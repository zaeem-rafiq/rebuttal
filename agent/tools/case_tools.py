"""agent/tools/case_tools.py

Case management, audit logging, and customer messaging tools for Rebuttal.
Exposes Strands @tool functions:
    - record_case
    - send_customer_email
"""

import os
import json
import uuid
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from strands import tool

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOCAL_DB_PATH = Path("/tmp/local_supabase.db") if os.name != "nt" else REPO_ROOT / "data" / "local_supabase.db"


def _get_db_connection() -> sqlite3.Connection:
    """Obtain a SQLite connection to the local database with row factory."""
    if not LOCAL_DB_PATH.exists():
        if os.name != "nt":
            orig = REPO_ROOT / "data" / "local_supabase.db"
            if orig.exists():
                import shutil
                LOCAL_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(orig, LOCAL_DB_PATH)
                try:
                    os.chmod(LOCAL_DB_PATH, 0o666)
                except Exception:
                    pass
        if not LOCAL_DB_PATH.exists():
            raise FileNotFoundError(f"Database file not found at {LOCAL_DB_PATH}")
    conn = sqlite3.connect(LOCAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _get_supabase_client():
    """Attempt to initialize Supabase cloud client if configured."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if url and key:
        try:
            from supabase import create_client
            return create_client(url, key)
        except Exception:
            return None
    return None


@tool
def record_case(
    dispute_id: str,
    action: str,
    actor: str = "executor",
    status: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Record case events, state transitions, and audit log entries in the database.

    Parameters:
        dispute_id: The ID of the dispute (e.g. 'dp_S1' or Stripe ID).
        action: Audit action name (e.g. 'accept_strategy', 'upload_evidence', 'submit_evidence', 'concede_dispute', 'refund_inquiry', 'complete_execution').
        actor: Identity or agent executing the action (default: 'executor').
        status: Optional updated dispute status (e.g. 'needs_response', 'under_review', 'won', 'lost', 'charge_refunded').
        details: Optional dictionary containing additional structured metadata.

    Returns:
        Dictionary confirming the recorded audit event and updated case status.
    """
    clean_dispute_id = dispute_id.strip()
    audit_id = f"aud_{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    details_dict = details or {}
    details_json = json.dumps(details_dict)

    conn = _get_db_connection()
    try:
        cur = conn.cursor()

        # Update dispute status in local database if provided
        if status:
            cur.execute(
                "UPDATE disputes SET status = ?, updated_at = ? WHERE id = ?",
                (status, now_iso, clean_dispute_id),
            )
            # Also update if dispute_id matches a metadata order/scenario or payment intent
            if cur.rowcount == 0:
                cur.execute(
                    """UPDATE disputes SET status = ?, updated_at = ? 
                       WHERE id = ? 
                          OR order_id = ? 
                          OR instr(metadata, ?) > 0""",
                    (status, now_iso, clean_dispute_id, clean_dispute_id, clean_dispute_id),
                )

        # Insert audit log entry
        cur.execute(
            """INSERT INTO audit_log (id, dispute_id, action, actor, details, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (audit_id, clean_dispute_id, action, actor, details_json, now_iso),
        )
        conn.commit()
    finally:
        conn.close()

    # Replicate to Supabase Cloud if available (non-fatal if offline/unreachable)
    sb = _get_supabase_client()
    if sb:
        try:
            if status:
                sb.table("disputes").update({"status": status, "updated_at": now_iso}).eq("id", clean_dispute_id).execute()
            sb.table("audit_log").insert({
                "id": audit_id,
                "dispute_id": clean_dispute_id,
                "action": action,
                "actor": actor,
                "details": details_dict,
                "created_at": now_iso,
            }).execute()
        except Exception:
            pass

    return {
        "status": "recorded",
        "audit_id": audit_id,
        "dispute_id": clean_dispute_id,
        "action": action,
        "actor": actor,
        "case_status": status,
        "created_at": now_iso,
    }


@tool
def send_customer_email(
    customer_id: str,
    subject: str,
    body: str,
    order_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Record and queue an outbound customer notification email in the customer messages database.

    Parameters:
        customer_id: Customer ID (e.g. 'CUST-001').
        subject: Subject line of the email.
        body: Body text of the customer message.
        order_id: Optional order ID reference (e.g. 'ORD-1001').

    Returns:
        Dictionary confirming message creation.
    """
    clean_cust_id = customer_id.strip()
    clean_order_id = order_id.strip() if order_id else None
    msg_id = f"msg_out_{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    conn = _get_db_connection()
    try:
        cur = conn.cursor()
        if clean_order_id:
            cur.execute(
                """SELECT id FROM customer_messages
                   WHERE order_id = ? AND direction = 'outbound' AND subject = ?""",
                (clean_order_id, subject),
            )
            existing = cur.fetchone()
            if existing:
                return {
                    "status": "already_sent",
                    "message_id": existing[0],
                    "customer_id": clean_cust_id,
                    "order_id": clean_order_id,
                    "subject": subject,
                }

        cur.execute(
            """INSERT INTO customer_messages (id, customer_id, order_id, direction, channel, subject, body, has_shipping_change, created_at)
               VALUES (?, ?, ?, 'outbound', 'email', ?, ?, 0, ?)""",
            (msg_id, clean_cust_id, clean_order_id, subject, body, now_iso),
        )
        conn.commit()
    finally:
        conn.close()

    # Replicate to Supabase Cloud if available
    sb = _get_supabase_client()
    if sb:
        if clean_order_id:
            try:
                existing_sb = (
                    sb.table("customer_messages")
                    .select("id")
                    .eq("order_id", clean_order_id)
                    .eq("direction", "outbound")
                    .eq("subject", subject)
                    .execute()
                )
                if existing_sb.data:
                    return {
                        "status": "already_sent",
                        "message_id": existing_sb.data[0]["id"],
                        "customer_id": clean_cust_id,
                        "order_id": clean_order_id,
                        "subject": subject,
                    }
            except Exception:
                pass
        try:
            sb.table("customer_messages").insert({
                "id": msg_id,
                "customer_id": clean_cust_id,
                "order_id": clean_order_id,
                "direction": "outbound",
                "channel": "email",
                "subject": subject,
                "body": body,
                "has_shipping_change": False,
                "created_at": now_iso,
            }).execute()
        except Exception:
            pass

    return {
        "status": "sent",
        "message_id": msg_id,
        "customer_id": clean_cust_id,
        "order_id": clean_order_id,
        "subject": subject,
        "created_at": now_iso,
    }
