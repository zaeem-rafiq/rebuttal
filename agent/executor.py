"""agent/executor.py

Executor Agent for Rebuttal autonomous chargeback defense.
Executes the approved strategy exactly without re-evaluating or altering decisions.

Tools:
    - submit_evidence
    - concede_dispute
    - refund_inquiry
    - upload_evidence_file
    - record_case (writes disputes + audit_log)
    - send_customer_email (stub -> customer_messages outbound)
"""

import os
import sys
import time
import json
import tempfile
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from dotenv import load_dotenv
from strands import Agent
from strands.models import BedrockModel

from agent.models import DisputeStrategy, EvidencePacket
from agent.tools.stripe_tools import (
    verify_live_key_guard,
    get_dispute,
    upload_evidence_file,
    submit_evidence,
    concede_dispute,
    refund_inquiry,
    resolve_stripe_dispute_id,
)
from agent.tools.case_tools import record_case, send_customer_email

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCAL_DB_PATH = REPO_ROOT / "data" / "local_supabase.db"

EXECUTOR_SYSTEM_PROMPT = (
    "You are the Rebuttal Dispute Execution Agent.\n"
    "Your solemn duty is to execute the approved dispute strategy exactly as formulated. "
    "NEVER re-decide, re-evaluate, or question the approved strategy.\n\n"
    "Available tools:\n"
    "- `upload_evidence_file(file_path)`: Upload narrative document or receipt to Stripe Files API.\n"
    "- `submit_evidence(dispute_id, evidence, submit=True)`: Submit evidence packet to Stripe.\n"
    "- `concede_dispute(dispute_id)`: Close and concede the dispute without evidence.\n"
    "- `refund_inquiry(dispute_id_or_charge)`: Issue full refund for pre-chargeback inquiry.\n"
    "- `record_case(dispute_id, action, actor='executor', status=None, details=None)`: Record audit log entries and state updates.\n"
    "- `send_customer_email(customer_id, subject, body, order_id=None)`: Record outbound email notification.\n\n"
    "Execution rules:\n"
    "1. When action is 'fight':\n"
    "   - Log strategy acceptance with `record_case`.\n"
    "   - Upload the evidence narrative using `upload_evidence_file` to obtain a file ID.\n"
    "   - Log file upload with `record_case`.\n"
    "   - Prepare evidence dictionary: set uncategorized_file to the file ID; in DEMO_MODE with win_probability >= 0.70 set uncategorized_text='winning_evidence', else narrative; attach tracking and shipping details.\n"
    "   - Call `submit_evidence(dispute_id, evidence=evidence, submit=True)`.\n"
    "   - Record submission and status updates with `record_case`.\n"
    "   - If needed, record outbound email to customer via `send_customer_email`.\n"
    "   - Record completion with `record_case`.\n"
    "2. When action is 'concede':\n"
    "   - Log strategy acceptance with `record_case`.\n"
    "   - Concede dispute via `concede_dispute(dispute_id)`.\n"
    "   - Record concession and status='lost' with `record_case`.\n"
    "   - Send courteous email via `send_customer_email`.\n"
    "   - Record completion with `record_case`.\n"
    "3. When action is 'refund_inquiry':\n"
    "   - Log strategy acceptance with `record_case`.\n"
    "   - Issue refund via `refund_inquiry(dispute_id)`.\n"
    "   - Record refund and status='charge_refunded' with `record_case`.\n"
    "   - Send confirmation email via `send_customer_email`.\n"
    "   - Record completion with `record_case`."
)


from strands.session import FileSessionManager
from agent.hooks import ApprovalGate, AuditHook, send_owner_sms


def build_executor_agent(
    model: Optional[BedrockModel] = None,
    session_id: Optional[str] = None,
    storage_dir: str = ".sessions",
    hooks: Optional[list] = None,
    session_manager: Optional[Any] = None,
    merchant_id: str = "default",
    memory_id: Optional[str] = None,
) -> Agent:
    """Build and return a Strands Agent instance configured for dispute execution."""
    if model is None:
        from agent.graph import get_bedrock_model
        model = get_bedrock_model()

    if session_manager is not None:
        active_session_manager = session_manager
    elif session_id:
        target_memory_id = memory_id or os.getenv("AGENTCORE_MEMORY_ID", "rebuttal_mem-Idf0xfCGuL")
        use_agentcore_memory = os.getenv("USE_AGENTCORE_MEMORY_SESSION", "true").lower() == "true"
        if use_agentcore_memory and target_memory_id:
            try:
                from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
                from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig
                import boto3

                region = os.getenv("AWS_REGION", "us-east-1")
                is_cloud = bool(os.environ.get("DOCKER_CONTAINER") or not os.path.exists(os.path.expanduser("~/.aws/credentials")))
                profile = None if is_cloud else os.getenv("AWS_PROFILE")
                b_sess = boto3.Session(profile_name=profile, region_name=region) if profile else boto3.Session(region_name=region)

                cfg = AgentCoreMemoryConfig(
                    memory_id=target_memory_id,
                    session_id=session_id,
                    actor_id=merchant_id,
                )
                active_session_manager = AgentCoreMemorySessionManager(
                    agentcore_memory_config=cfg,
                    region_name=region,
                    boto_session=b_sess,
                )
            except Exception as e:
                import logging
                logging.getLogger("rebuttal.executor").warning("Falling back to FileSessionManager: %s", e)
                active_session_manager = FileSessionManager(session_id=session_id, storage_dir=storage_dir)
        else:
            active_session_manager = FileSessionManager(session_id=session_id, storage_dir=storage_dir)
    else:
        active_session_manager = None

    active_hooks = hooks if hooks is not None else [ApprovalGate(), AuditHook()]

    return Agent(
        model=model,
        tools=[
            submit_evidence,
            concede_dispute,
            refund_inquiry,
            upload_evidence_file,
            record_case,
            send_customer_email,
        ],
        hooks=active_hooks,
        session_manager=active_session_manager,
        system_prompt=EXECUTOR_SYSTEM_PROMPT,
        name="executor",
    )


def execute_strategy(
    dispute_id: str,
    strategy: DisputeStrategy,
    evidence_packet: Optional[EvidencePacket] = None,
    context: Optional[Dict[str, Any]] = None,
    is_demo_mode: Optional[bool] = None,
) -> Dict[str, Any]:
    """Deterministically execute an approved strategy and evidence packet.

    Parameters:
        dispute_id: Internal dispute ID (e.g. 'dp_S1') or live Stripe dispute ID.
        strategy: Approved DisputeStrategy instance.
        evidence_packet: Compiled EvidencePacket instance (required for 'fight').
        context: Optional dictionary with order_id, customer_id, etc.
        is_demo_mode: If True, uses Stripe test outcome token 'winning_evidence' when win_prob >= 0.70.

    Returns:
        Summary dictionary containing execution outcome, file_id, audit rows count, and final status.
    """
    verify_live_key_guard()

    demo_mode = (
        is_demo_mode
        if is_demo_mode is not None
        else os.getenv("DEMO_MODE", "true").lower() == "true"
    )

    clean_dispute_id = dispute_id.strip()
    target_stripe_id = resolve_stripe_dispute_id(clean_dispute_id)
    ctx = context or {}

    # Extract customer_id and order_id if not in context
    customer_id = ctx.get("customer_id")
    order_id = ctx.get("order_id")

    if not customer_id or not order_id:
        if LOCAL_DB_PATH.exists():
            try:
                conn = sqlite3.connect(LOCAL_DB_PATH)
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                disp_row = cur.execute(
                    "SELECT * FROM disputes WHERE id = ? OR order_id = ? OR instr(metadata, ?) > 0",
                    (clean_dispute_id, clean_dispute_id, clean_dispute_id),
                ).fetchone()
                if disp_row:
                    order_id = order_id or disp_row["order_id"]
                    if order_id:
                        ord_row = cur.execute("SELECT customer_id FROM orders WHERE id = ?", (order_id,)).fetchone()
                        if ord_row:
                            customer_id = customer_id or ord_row["customer_id"]
                conn.close()
            except Exception:
                pass

    customer_id = customer_id or "CUST-001"
    order_id = order_id or "ORD-1001"

    uploaded_file_id = None
    action = strategy.action

    # Step 1: Accept strategy audit event
    record_case(
        dispute_id=clean_dispute_id,
        action="accept_strategy",
        actor="executor",
        details={
            "action": action,
            "win_probability": strategy.win_probability,
            "expected_value_cents": strategy.expected_value_cents,
            "rationale": strategy.rationale,
        },
    )

    if action == "fight":
        narrative = evidence_packet.narrative if evidence_packet else "Evidence proving valid transaction and fulfillment."

        # Step 2: Upload narrative file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt", encoding="utf-8") as tf:
            tf.write(f"REBUTTAL DISPUTE EVIDENCE DOSSIER\n")
            tf.write(f"Dispute ID: {clean_dispute_id}\n")
            tf.write(f"Order ID: {order_id}\n")
            tf.write(f"Customer ID: {customer_id}\n\n")
            tf.write(f"NARRATIVE & TIMELINE:\n{narrative}\n")
            narrative_file_path = tf.name

        try:
            upload_resp = upload_evidence_file(narrative_file_path, purpose="dispute_evidence")
            uploaded_file_id = upload_resp.get("id")
        finally:
            try:
                os.unlink(narrative_file_path)
            except Exception:
                pass

        # Step 3: Log file upload audit event
        record_case(
            dispute_id=clean_dispute_id,
            action="upload_evidence",
            actor="executor",
            details={
                "file_id": uploaded_file_id,
                "purpose": "dispute_evidence",
                "filename": "narrative.pdf",
            },
        )

        # Step 4: Construct evidence payload
        evidence_dict: Dict[str, Any] = {}
        if uploaded_file_id:
            evidence_dict["uncategorized_file"] = uploaded_file_id

        # DEMO_MODE rule: winning_evidence token triggers automatic won status in Stripe test mode
        if demo_mode and strategy.win_probability >= 0.70:
            evidence_dict["uncategorized_text"] = "winning_evidence"
        else:
            evidence_dict["uncategorized_text"] = narrative

        # Map structured fields from EvidencePacket
        if evidence_packet:
            for field, key in [
                ("shipping_tracking_number", "shipping_tracking_number"),
                ("shipping_carrier", "shipping_carrier"),
                ("shipping_date", "shipping_date"),
                ("customer_name", "customer_name"),
                ("customer_email_address", "customer_email_address"),
                ("billing_address", "billing_address"),
                ("shipping_address", "shipping_address"),
                ("customer_communication", "customer_communication"),
                ("refund_policy_disclosure", "refund_policy_disclosure"),
                ("cancellation_policy_disclosure", "cancellation_policy_disclosure"),
            ]:
                val = getattr(evidence_packet, field, None)
                if val:
                    evidence_dict[key] = str(val)

        # Step 5: Submit evidence to Stripe
        submit_resp = submit_evidence(target_stripe_id, evidence=evidence_dict, submit=True)
        stripe_status = submit_resp.get("status", "under_review")

        # Step 6: Log evidence submission audit event
        record_case(
            dispute_id=clean_dispute_id,
            status=stripe_status,
            action="submit_evidence",
            actor="executor",
            details={
                "stripe_dispute_id": target_stripe_id,
                "submitted_fields": list(evidence_dict.keys()),
                "status": stripe_status,
            },
        )

        # Step 7: Send customer email notice
        send_customer_email(
            customer_id=customer_id,
            order_id=order_id,
            subject=f"Update regarding dispute on order {order_id}",
            body=f"We have submitted fulfillment and tracking verification for order {order_id} to the payment processor.",
        )
        record_case(
            dispute_id=clean_dispute_id,
            action="send_customer_email",
            actor="executor",
            details={"recipient": customer_id, "channel": "email"},
        )

        # In DEMO_MODE with winning_evidence, poll Stripe briefly to confirm won status
        final_status = stripe_status
        if demo_mode and strategy.win_probability >= 0.70:
            for _ in range(6):
                time.sleep(1.5)
                disp_check = get_dispute(target_stripe_id)
                final_status = disp_check.get("status", final_status)
                if final_status == "won":
                    break

            if final_status == "won":
                record_case(
                    dispute_id=clean_dispute_id,
                    status="won",
                    action="dispute_won",
                    actor="stripe_webhook",
                    details={"final_status": "won", "stripe_dispute_id": target_stripe_id},
                )

        # Step 8: Final completion audit event
        record_case(
            dispute_id=clean_dispute_id,
            action="complete_execution",
            actor="executor",
            details={"final_status": final_status, "action": action},
        )

    elif action == "concede":
        concede_resp = concede_dispute(target_stripe_id)
        final_status = concede_resp.get("status", "lost")

        record_case(
            dispute_id=clean_dispute_id,
            status="lost",
            action="concede_dispute",
            actor="executor",
            details={"stripe_dispute_id": target_stripe_id, "rationale": strategy.rationale},
        )

        send_customer_email(
            customer_id=customer_id,
            order_id=order_id,
            subject=f"Notice regarding dispute on order {order_id}",
            body=f"We have accepted your dispute claim on order {order_id} as a valued repeat customer.",
        )
        record_case(
            dispute_id=clean_dispute_id,
            action="send_customer_email",
            actor="executor",
            details={"recipient": customer_id, "channel": "email"},
        )

        record_case(
            dispute_id=clean_dispute_id,
            action="complete_execution",
            actor="executor",
            details={"final_status": "lost", "action": action},
        )

    elif action == "refund_inquiry":
        refund_resp = refund_inquiry(target_stripe_id)
        final_status = "charge_refunded"

        record_case(
            dispute_id=clean_dispute_id,
            status="charge_refunded",
            action="refund_inquiry",
            actor="executor",
            details={"refund_id": refund_resp.get("id"), "rationale": strategy.rationale},
        )

        send_customer_email(
            customer_id=customer_id,
            order_id=order_id,
            subject=f"Refund confirmation for inquiry on order {order_id}",
            body=f"Your order inquiry has been processed and a full refund has been issued.",
        )
        record_case(
            dispute_id=clean_dispute_id,
            action="send_customer_email",
            actor="executor",
            details={"recipient": customer_id, "channel": "email"},
        )

        record_case(
            dispute_id=clean_dispute_id,
            action="complete_execution",
            actor="executor",
            details={"final_status": "charge_refunded", "action": action},
        )

    else:
        raise ValueError(f"Unknown strategy action '{action}'")

    # Count audit log rows for this dispute
    audit_rows_count = 0
    if LOCAL_DB_PATH.exists():
        try:
            conn = sqlite3.connect(LOCAL_DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM audit_log WHERE dispute_id = ?", (clean_dispute_id,))
            audit_rows_count = cur.fetchone()[0]
            conn.close()
        except Exception:
            pass

    # Dispatch confirmation SMS per R-04 requirement
    conf_sms_sid = send_owner_sms(
        f"Rebuttal: Action '{action}' executed for dispute {clean_dispute_id}. Status: {final_status}."
    )

    return {
        "dispute_id": clean_dispute_id,
        "stripe_dispute_id": target_stripe_id,
        "action": action,
        "final_status": final_status,
        "uploaded_file_id": uploaded_file_id,
        "audit_rows_count": audit_rows_count,
        "confirmation_sms_sid": conf_sms_sid,
    }
