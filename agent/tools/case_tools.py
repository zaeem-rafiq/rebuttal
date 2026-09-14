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
from contextlib import closing
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


def _decision_cloud_client():
    client = _get_supabase_client()
    if client is None and (os.getenv("SUPABASE_URL") or os.getenv("SUPABASE_SERVICE_KEY")):
        raise RuntimeError("Configured cloud decision store is unavailable")
    return client


def get_latest_decision(dispute_id: str, db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Select one current decision across stores before processing an owner reply."""
    rows = []
    path = Path(db_path) if db_path is not None else LOCAL_DB_PATH
    if path.exists():
        with closing(sqlite3.connect(path)) as conn, conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM decisions WHERE dispute_id = ? ORDER BY created_at DESC, id DESC LIMIT 1",
                (dispute_id.strip(),),
            ).fetchone()
            if row:
                rows.append(dict(row))
    sb = _decision_cloud_client()
    if sb is not None:
        rows.extend(sb.table("decisions").select("*").eq("dispute_id", dispute_id.strip())
                    .order("created_at", desc=True).order("id", desc=True).limit(1).execute().data or [])
    if not rows:
        return None

    def ordering(row):
        created = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        return created, row["id"]

    return max(rows, key=ordering)


def update_decision_status(
    decision_id: str,
    status: str,
    action: Optional[str] = None,
    answered_at: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Update exactly one decision in both stores; surface incomplete replication."""
    if not decision_id or status not in {"approved", "overridden", "held"}:
        raise ValueError("A decision ID and valid owner decision status are required")
    if action is not None and action not in {"fight", "concede", "refund_inquiry"}:
        raise ValueError("Invalid owner decision action")
    values = {"status": status}
    if action is not None:
        values["action"] = action
    if answered_at is not None:
        values["answered_at"] = answered_at
    sb = _decision_cloud_client()
    path = Path(db_path) if db_path is not None else LOCAL_DB_PATH
    local_row = None
    if path.exists():
        with closing(sqlite3.connect(path)) as conn, conn:
            conn.row_factory = sqlite3.Row
            conn.execute(
                "UPDATE decisions SET " + ", ".join(f"{key} = ?" for key in values) + " WHERE id = ?",
                (*values.values(), decision_id),
            )
            row = conn.execute("SELECT * FROM decisions WHERE id = ?", (decision_id,)).fetchone()
            local_row = dict(row) if row else None
    cloud_row = None
    if sb is not None:
        try:
            rows = sb.table("decisions").update(values).eq("id", decision_id).execute().data or []
            cloud_row = next((row for row in rows if row.get("id") == decision_id), None)
            if cloud_row is None or any(cloud_row.get(key) != value for key, value in values.items() if key != "answered_at"):
                raise RuntimeError("Cloud decision row was not updated")
            if answered_at is not None:
                actual = datetime.fromisoformat((cloud_row.get("answered_at") or "").replace("Z", "+00:00"))
                expected = datetime.fromisoformat(answered_at.replace("Z", "+00:00"))
                if actual != expected:
                    raise RuntimeError("Cloud decision answer timestamp was not updated")
        except Exception as exc:
            raise RuntimeError("Decision cloud synchronization failed; a local update or Stripe action may already have completed") from exc
    result = cloud_row or local_row
    if result is None:
        raise LookupError(f"Decision not found: {decision_id}")
    return result


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
