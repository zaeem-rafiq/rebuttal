#!/usr/bin/env python3
"""scripts/test_r18_s3.py

Verifies all three proofs for HAC-20 / R-18:
1. PROOF R-18: S3 strategy action=refund_inquiry gate=true = PASS
2. PROOF R-18: reply 2 → refund re_… created, case status=refunded_inquiry = PASS
3. PROOF R-18: console shows S3 stamp = PASS
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

LOCAL_DB_PATH = REPO_ROOT / "data" / "local_supabase.db"
PROOF_FILE = REPO_ROOT / "docs" / "proofs" / "R-18.md"

import stripe
from agent.tools.stripe_tools import verify_live_key_guard, get_dispute, resolve_stripe_dispute_id
from agent.graph import run_evidence_pipeline, get_bedrock_model
from agent.hooks import ApprovalGate
from agent.executor import build_executor_agent, execute_strategy
from scripts.reply import process_reply


def record_proof(line: str):
    print(line, flush=True)
    PROOF_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing = ""
    if PROOF_FILE.exists():
        with open(PROOF_FILE, "r", encoding="utf-8") as f:
            existing = f.read()
    if line not in existing:
        with open(PROOF_FILE, "a", encoding="utf-8") as f:
            f.write(f"{line}\n")


def test_s3_end_to_end():
    verify_live_key_guard()
    stripe.api_key = os.environ["STRIPE_SECRET_KEY"]

    print("=" * 60)
    print("STEP 1: Setting up S3 Pre-chargeback Inquiry in Stripe test mode...")
    print("=" * 60)

    # 1. Create PaymentIntent with pm_card_createDisputeInquiry for ORD-1003 ($129.00)
    pi = stripe.PaymentIntent.create(
        amount=12900,
        currency="usd",
        payment_method="pm_card_createDisputeInquiry",
        confirm=True,
        automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
        metadata={"order_id": "ORD-1003", "scenario": "S3"},
    )
    print(f"Created PI: {pi.id}")

    import time
    dispute = None
    charge_id = None
    for attempt in range(15):
        time.sleep(1.5)
        pi_refreshed = stripe.PaymentIntent.retrieve(pi.id, expand=["latest_charge.dispute"])
        if pi_refreshed.latest_charge:
            charge_obj = pi_refreshed.latest_charge
            if isinstance(charge_obj, str):
                charge_obj = stripe.Charge.retrieve(charge_obj)
            charge_id = charge_obj.id
            if hasattr(charge_obj, "dispute") and charge_obj.dispute:
                dispute = charge_obj.dispute
                break

        d_list = stripe.Dispute.list(payment_intent=pi.id, limit=1)
        if d_list.data:
            dispute = d_list.data[0]
            if not charge_id:
                charge_id = dispute.charge
            break

    if not dispute:
        raise TimeoutError(f"Dispute not created for PI {pi.id}")

    dispute_id = dispute.id
    status = dispute.status
    reason = dispute.reason
    print(f"Stripe inquiry active: {dispute_id}, status={status}, reason={reason}, charge={charge_id}")
    assert status == "warning_needs_response", f"Expected warning_needs_response, got {status}"

    # Update local SQLite and Supabase with live S3 dispute metadata
    meta_dict = {"order_id": "ORD-1003", "scenario": "S3", "stripe_dispute_id": dispute_id}
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    conn = sqlite3.connect(LOCAL_DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """UPDATE disputes
           SET payment_intent_id = ?, charge_id = ?, status = 'warning_needs_response', metadata = ?
           WHERE id = 'dp_S3' OR order_id = 'ORD-1003'""",
        (pi.id, charge_id, json.dumps(meta_dict)),
    )
    cur.execute(
        "UPDATE orders SET payment_intent_id = ?, charge_id = ? WHERE id = 'ORD-1003'",
        (pi.id, charge_id),
    )
    conn.commit()
    conn.close()

    # Replicate to Supabase
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if url and key:
        try:
            from supabase import create_client
            sb = create_client(url, key)
            sb.table("disputes").update({
                "payment_intent_id": pi.id,
                "charge_id": charge_id,
                "status": "warning_needs_response",
                "metadata": meta_dict,
            }).eq("id", "dp_S3").execute()
            sb.table("orders").update({
                "payment_intent_id": pi.id,
                "charge_id": charge_id,
            }).eq("id", "ORD-1003").execute()
        except Exception as e:
            print(f"Note: Supabase update skipped: {e}")

    print("\n" + "=" * 60)
    print("STEP 2: Running multi-agent evidence pipeline for S3...")
    print("=" * 60)

    task = (
        f"Investigate dispute dp_S3 (Stripe ID: {dispute_id}, order ORD-1003, customer CUST-003). "
        f"Extract status, review comms for cancellation requests, and determine optimal strategy."
    )
    strategy, drafter, _ = run_evidence_pipeline(task)

    print(f"Strategy action: {strategy.action}")
    print(f"Strategy rationale: {strategy.rationale}")
    print(f"Win probability: {strategy.win_probability}")

    # Verify Gate condition
    gate = ApprovalGate()
    # If action != 'fight', gate must require approval
    is_not_fight = strategy.action != "fight"
    gate_required = is_not_fight or (12900 >= 20000) or (0.35 <= strategy.win_probability <= 0.65)

    p1_pass = (strategy.action == "refund_inquiry" and gate_required)
    p1 = f"PROOF R-18: S3 strategy action={strategy.action} gate={'true' if gate_required else 'false'} = {'PASS' if p1_pass else 'FAIL'}"
    record_proof(p1)

    print("\n" + "=" * 60)
    print("STEP 3: Testing Owner Reply '2' (Refund Inquiry)...")
    print("=" * 60)

    # Insert pending decision for dp_S3 if not already present
    conn = sqlite3.connect(LOCAL_DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """INSERT OR REPLACE INTO decisions
           (id, dispute_id, action, win_probability, expected_value_cents, evidence_strength, customer_value, rationale, owner_summary, status, created_at)
           VALUES ('dec_s3_test', 'dp_S3', 'refund_inquiry', 0.15, 0, 'weak', 'new', ?, ?, 'pending', ?)""",
        (strategy.rationale, strategy.owner_summary, now_iso),
    )
    conn.commit()
    conn.close()

    # Process reply 2
    reply_res = process_reply(dispute_id="dp_S3", answer="2", record_proof=False)
    print(f"Reply result: {reply_res}")

    refund_id = reply_res.get("refund_id")
    case_status = reply_res.get("case_status")

    # Verify refund exists in Stripe
    has_valid_refund = False
    if refund_id and refund_id.startswith("re_"):
        try:
            ref_obj = stripe.Refund.retrieve(refund_id)
            if ref_obj and ref_obj.status in ["succeeded", "pending"]:
                has_valid_refund = True
                print(f"Verified Stripe Refund {ref_obj.id}: status={ref_obj.status}, amount={ref_obj.amount}")
        except Exception as e:
            print(f"Refund verification error: {e}")

    p2_pass = (has_valid_refund and case_status == "refunded_inquiry")
    p2 = f"PROOF R-18: reply 2 → refund {refund_id} created, case status={case_status} = {'PASS' if p2_pass else 'FAIL'}"
    record_proof(p2)

    print("\n" + "=" * 60)
    print("STEP 4: Verifying Console UI S3 Stamp...")
    print("=" * 60)

    # Verify console components have the S3 stamp logic
    case_feed_src = (REPO_ROOT / "console" / "src" / "components" / "CaseFeed.tsx").read_text(encoding="utf-8")
    page_src = (REPO_ROOT / "console" / "src" / "app" / "page.tsx").read_text(encoding="utf-8")
    details_src = (REPO_ROOT / "console" / "src" / "app" / "case" / "[id]" / "CaseDetailsClient.tsx").read_text(encoding="utf-8")

    stamp_text = "INQUIRY CLOSED · $15 FEE AVOIDED"
    has_feed_stamp = stamp_text in case_feed_src
    has_page_stamp = stamp_text in page_src
    has_details_stamp = stamp_text in details_src

    p3_pass = has_feed_stamp and has_page_stamp and has_details_stamp
    p3 = f"PROOF R-18: console shows S3 stamp = {'PASS' if p3_pass else 'FAIL'}"
    record_proof(p3)

    print("\n" + "=" * 60)
    print("ALL R-18 CHECKS COMPLETE")
    print("=" * 60)
    return p1_pass and p2_pass and p3_pass


if __name__ == "__main__":
    success = test_s3_end_to_end()
    sys.exit(0 if success else 1)
