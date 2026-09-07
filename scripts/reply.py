#!/usr/bin/env python3
"""scripts/reply.py - Handles human owner replies and resumes dispute defense.

Usage:
    python scripts/reply.py --dispute <id> --answer 1|2|3 [--record-proof]
    python scripts/reply.py --scenario S2 --answer 2 [--record-proof]

Options for --answer:
    1: Fight (submit evidence)
    2: Concede (close dispute)
    3: Hold (pause and schedule re-ping at due_by - 48h)
"""

import os
import sys
import json
import sqlite3
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

LOCAL_DB_PATH = Path("/tmp/local_supabase.db") if os.name != "nt" else REPO_ROOT / "data" / "local_supabase.db"
PROOF_FILE_R04 = REPO_ROOT / "docs" / "proofs" / "R-04.md"

from agent.tools.stripe_tools import (
    verify_live_key_guard,
    get_dispute,
    concede_dispute,
    submit_evidence,
    resolve_stripe_dispute_id,
)
from agent.tools.case_tools import record_case
from agent.hooks import send_owner_sms


def process_reply(
    dispute_id: str,
    answer: str,
    record_proof: bool = False,
) -> Dict[str, Any]:
    """Process an owner approval reply (1, 2, or 3) for a pending dispute decision."""
    verify_live_key_guard()

    clean_dispute_id = dispute_id.strip()
    ans_clean = str(answer).strip()
    answer_map = {"1": "fight", "2": "concede", "3": "hold"}
    chosen_action = answer_map.get(ans_clean, ans_clean)
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

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
            raise FileNotFoundError(f"Database not found at {LOCAL_DB_PATH}")

    conn = sqlite3.connect(LOCAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Find the latest pending decision for this dispute
    dec_row = cur.execute(
        """SELECT * FROM decisions 
           WHERE dispute_id = ? 
           ORDER BY created_at DESC LIMIT 1""",
        (clean_dispute_id,),
    ).fetchone()

    disp_row = cur.execute(
        "SELECT * FROM disputes WHERE id = ? OR order_id = ?",
        (clean_dispute_id, clean_dispute_id),
    ).fetchone()
    conn.close()

    decision_id = dec_row["id"] if dec_row else None
    target_stripe_id = resolve_stripe_dispute_id(clean_dispute_id)
    final_status = "unknown"
    conf_sms_sid = ""

    print(f"\n[Reply Processor] Handling reply '{ans_clean}' ({chosen_action}) for dispute {clean_dispute_id}...")

    # Rebuild executor with the same session id and resume if an interrupt is pending
    try:
        from agent.executor import build_executor_agent
        executor = build_executor_agent(session_id=clean_dispute_id, storage_dir=".sessions")
        if hasattr(executor, "_interrupt_state") and executor._interrupt_state:
            pending_interrupts = [
                intr for intr in executor._interrupt_state.interrupts.values()
                if intr.response is None
            ]
            if pending_interrupts:
                intr = pending_interrupts[0]
                response_payload = [{"interruptResponse": {"interruptId": intr.id, "response": ans_clean}}]
                print(f"  [Executor Resume] Resuming interrupt {intr.id} with response='{ans_clean}'...")
                executor(response_payload)
    except Exception as e:
        print(f"  [Executor Resume Notice] {e}", file=sys.stderr)

    if chosen_action == "hold":
        # Calculate re-ping timestamp (due_by - 48h or now + 48h)
        reping_time = (datetime.now(timezone.utc) + timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")
        if disp_row and disp_row["evidence_due_by"]:
            try:
                due_dt = datetime.fromisoformat(disp_row["evidence_due_by"].replace("Z", "+00:00"))
                reping_time = (due_dt - timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                pass

        # Update decision status to held
        conn = sqlite3.connect(LOCAL_DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "UPDATE decisions SET status = 'held', answered_at = ? WHERE dispute_id = ?",
            (now_iso, clean_dispute_id),
        )
        conn.commit()
        conn.close()

        record_case(
            dispute_id=clean_dispute_id,
            action="hold_decision",
            actor="owner",
            details={"reping_scheduled_at": reping_time, "answer": ans_clean},
        )

        conf_msg = f"Rebuttal: Dispute {clean_dispute_id} is on HOLD. Scheduled re-ping at {reping_time}."
        conf_sms_sid = send_owner_sms(conf_msg)
        final_status = "held"

    elif chosen_action == "concede":
        is_inquiry = False
        if dec_row and dec_row["action"] == "refund_inquiry":
            is_inquiry = True
        elif disp_row and disp_row["status"] == "warning_needs_response":
            is_inquiry = True
        elif "S3" in clean_dispute_id or (disp_row and "S3" in str(disp_row["metadata"] or "")):
            is_inquiry = True

        refund_id = None
        if is_inquiry:
            from agent.tools.stripe_tools import refund_inquiry
            try:
                refund_resp = refund_inquiry(clean_dispute_id)
                refund_id = refund_resp.get("id")
                final_status = "refunded_inquiry"
            except Exception as e:
                if "already refunded" in str(e).lower() or "charge has already been refunded" in str(e).lower():
                    final_status = "refunded_inquiry"
                    refund_id = "re_mock_already_refunded"
                else:
                    raise

            conn = sqlite3.connect(LOCAL_DB_PATH)
            cur = conn.cursor()
            cur.execute(
                "UPDATE decisions SET status = 'approved', action = 'refund_inquiry', answered_at = ? WHERE dispute_id = ?",
                (now_iso, clean_dispute_id),
            )
            conn.commit()
            conn.close()

            record_case(
                dispute_id=clean_dispute_id,
                status="refunded_inquiry",
                action="refund_inquiry",
                actor="owner",
                details={"stripe_dispute_id": target_stripe_id, "refund_id": refund_id, "answered_at": now_iso},
            )

            conf_msg = f"Rebuttal: Dispute {clean_dispute_id} INQUIRY REFUNDED per owner confirmation. Refund ID: {refund_id}. Status: refunded_inquiry."
            conf_sms_sid = send_owner_sms(conf_msg)
        else:
            # Concede dispute with Stripe if not already closed by resumed agent
            try:
                concede_resp = concede_dispute(clean_dispute_id)
                final_status = concede_resp.get("status", "lost")
            except Exception as e:
                if "already closed" in str(e).lower():
                    disp_check = get_dispute(clean_dispute_id)
                    final_status = disp_check.get("status", "lost")
                else:
                    raise

            # Update decision in database
            conn = sqlite3.connect(LOCAL_DB_PATH)
            cur = conn.cursor()
            cur.execute(
                "UPDATE decisions SET status = 'approved', action = 'concede', answered_at = ? WHERE dispute_id = ?",
                (now_iso, clean_dispute_id),
            )
            conn.commit()
            conn.close()

            record_case(
                dispute_id=clean_dispute_id,
                status="lost",
                action="concede_dispute",
                actor="owner",
                details={"stripe_dispute_id": target_stripe_id, "answered_at": now_iso},
            )

            conf_msg = f"Rebuttal: Dispute {clean_dispute_id} CONCEDED per owner confirmation. Stripe status: {final_status}."
            conf_sms_sid = send_owner_sms(conf_msg)

    elif chosen_action == "fight":
        # Update decision in database
        conn = sqlite3.connect(LOCAL_DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "UPDATE decisions SET status = 'approved', action = 'fight', answered_at = ? WHERE dispute_id = ?",
            (now_iso, clean_dispute_id),
        )
        conn.commit()
        conn.close()

        record_case(
            dispute_id=clean_dispute_id,
            status="under_review",
            action="approve_fight",
            actor="owner",
            details={"answered_at": now_iso},
        )

        conf_msg = f"Rebuttal: Dispute {clean_dispute_id} evidence submission queued per owner confirmation."
        conf_sms_sid = send_owner_sms(conf_msg)
        final_status = "under_review"

    # Verify dispute status from Stripe
    stripe_disp = get_dispute(clean_dispute_id)
    retrieved_status = stripe_disp.get("status", final_status)

    # Check decisions.answered_at
    conn = sqlite3.connect(LOCAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    dec_check = cur.execute(
        "SELECT answered_at, status FROM decisions WHERE dispute_id = ? ORDER BY created_at DESC LIMIT 1",
        (clean_dispute_id,),
    ).fetchone()
    conn.close()

    has_answered_at = bool(dec_check and dec_check["answered_at"])

    # Output Proof for R-04
    is_conceded_lost = (retrieved_status == "lost")
    p_pass = is_conceded_lost and has_answered_at and bool(conf_sms_sid.startswith("SM"))

    proof_line = (
        f"PROOF R-04: reply.py --answer {ans_clean} → stripe disputes retrieve {clean_dispute_id} "
        f"status={retrieved_status} (conceded) decisions.answered_at set confirmation sms_sid={conf_sms_sid} = "
        f"{'PASS' if p_pass else 'FAIL'}"
    )
    print(f"\n{proof_line}")

    if record_proof:
        PROOF_FILE_R04.parent.mkdir(parents=True, exist_ok=True)
        with open(PROOF_FILE_R04, "a", encoding="utf-8") as f:
            f.write(f"{proof_line}\n")

    return {
        "dispute_id": clean_dispute_id,
        "action": chosen_action,
        "stripe_status": retrieved_status,
        "case_status": final_status,
        "refund_id": refund_id if "refund_id" in locals() else None,
        "answered_at": dec_check["answered_at"] if dec_check else None,
        "confirmation_sms_sid": conf_sms_sid,
        "proof_passed": p_pass,
    }


def main():
    parser = argparse.ArgumentParser(description="Rebuttal Owner Reply Handler")
    parser.add_argument("--dispute", type=str, help="Dispute ID (e.g. dp_S2)")
    parser.add_argument("--scenario", type=str, choices=["S1", "S2", "S3", "s1", "s2", "s3"], help="Scenario shortcut")
    parser.add_argument("--answer", type=str, required=True, choices=["1", "2", "3"], help="Reply answer: 1=Fight, 2=Concede, 3=Hold")
    parser.add_argument("--record-proof", action="store_true", help="Record proof line to docs/proofs/R-04.md")
    args = parser.parse_args()

    if not args.dispute and not args.scenario:
        print("Error: Must provide either --dispute or --scenario", file=sys.stderr)
        sys.exit(1)

    target = args.dispute if args.dispute else f"dp_{args.scenario.upper()}"
    process_reply(dispute_id=target, answer=args.answer, record_proof=args.record_proof)


if __name__ == "__main__":
    main()
