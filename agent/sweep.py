"""agent/sweep.py

Pure function deadline sweep and silence policy enforcement for Rebuttal.
Evaluates pending owner decisions:
- If now >= sent_at + 48h OR now >= due_by - 24h:
    Applies the merchant policy default ('fight') through the same resume path.
- For open Stripe disputes without an existing case file in the database:
    Opens a new case file and registers it in the disputes table and audit log.
"""

import os
import sys
import json
import sqlite3
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCAL_DB_PATH = REPO_ROOT / "data" / "local_supabase.db"

from agent.hooks import load_merchant_policy, send_owner_sms
from agent.tools.case_tools import record_case


def _parse_iso(val: Any) -> Optional[datetime]:
    """Parse ISO timestamp or datetime object into a timezone-aware UTC datetime."""
    if not val:
        return None
    if isinstance(val, datetime):
        return val if val.tzinfo else val.replace(tzinfo=timezone.utc)
    try:
        clean_str = str(val).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_str)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def run_sweep(
    now: datetime,
    db_path: Optional[Union[str, Path]] = None,
    policy: Optional[Dict[str, Any]] = None,
    storage_dir: Union[str, Path] = ".sessions",
    check_stripe: bool = True,
) -> Dict[str, Any]:
    """Execute the deadline sweep and silence policy evaluation.

    Parameters:
        now: Current time injected as a datetime object (pure function requirement).
        db_path: Optional path to SQLite database (defaults to LOCAL_DB_PATH).
        policy: Optional merchant policy dict (defaults to load_merchant_policy()).
        storage_dir: Directory where agent sessions are stored (default: .sessions).
        check_stripe: Whether to inspect Stripe for new open disputes without case files.

    Returns:
        Summary dict containing counts and IDs of defaulted decisions and opened disputes.
    """
    if not isinstance(now, datetime):
        raise TypeError(f"Expected datetime for 'now', got {type(now)}")
    now_utc = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
    now_iso = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    target_db = Path(db_path) if db_path else LOCAL_DB_PATH
    active_policy = policy or load_merchant_policy()
    silence_action = active_policy.get("silence_action", "fight")

    defaulted_decisions: List[Dict[str, Any]] = []
    untouched_decisions: List[Dict[str, Any]] = []
    opened_disputes: List[str] = []

    if not target_db.exists():
        return {
            "now": now_iso,
            "defaulted_decisions": [],
            "untouched_decisions": [],
            "opened_disputes": [],
            "error": f"Database not found at {target_db}",
        }

    conn = sqlite3.connect(target_db)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()

        # ---------------------------------------------------------------------
        # 1. Evaluate pending decisions against silence and deadline thresholds
        # ---------------------------------------------------------------------
        cur.execute(
            """SELECT dec.*, disp.evidence_due_by, disp.id AS linked_disp_id
               FROM decisions dec
               LEFT JOIN disputes disp ON dec.dispute_id = disp.id OR disp.order_id = dec.dispute_id
               WHERE dec.status = 'pending'"""
        )
        pending_rows = cur.fetchall()

        for row in pending_rows:
            dec_id = row["id"]
            dispute_id = row["dispute_id"]
            row_keys = row.keys()

            sent_raw = row["sent_at"] if "sent_at" in row_keys and row["sent_at"] else row["created_at"]
            sent_dt = _parse_iso(sent_raw)

            due_raw = row["evidence_due_by"]
            due_dt = _parse_iso(due_raw)

            aged_out = False
            if sent_dt and now_utc >= sent_dt + timedelta(hours=48):
                aged_out = True

            deadline_approaching = False
            if due_dt and now_utc >= due_dt - timedelta(hours=24):
                deadline_approaching = True

            if aged_out or deadline_approaching:
                reason = "aged_out" if aged_out else "deadline_approaching"

                # Resume Strands executor agent if an interrupt is pending in session
                try:
                    from agent.executor import build_executor_agent
                    executor = build_executor_agent(session_id=dispute_id, storage_dir=str(storage_dir))
                    if hasattr(executor, "_interrupt_state") and executor._interrupt_state:
                        pending_interrupts = [
                            intr for intr in executor._interrupt_state.interrupts.values()
                            if intr.response is None
                        ]
                        if pending_interrupts:
                            intr = pending_interrupts[0]
                            resp_val = "1" if silence_action == "fight" else ("2" if silence_action == "concede" else silence_action)
                            response_payload = [{"interruptResponse": {"interruptId": intr.id, "response": resp_val}}]
                            executor(response_payload)
                except Exception:
                    pass

                # Update decision record in database
                has_approved_at = "approved_at" in row_keys
                has_answered_at = "answered_at" in row_keys

                update_fields = ["status = 'approved'", "action = ?"]
                params: List[Any] = [silence_action]

                if has_answered_at:
                    update_fields.append("answered_at = ?")
                    params.append(now_iso)
                if has_approved_at:
                    update_fields.append("approved_at = ?")
                    params.append(now_iso)

                params.append(dec_id)
                cur.execute(
                    f"UPDATE decisions SET {', '.join(update_fields)} WHERE id = ?",
                    tuple(params),
                )
                conn.commit()

                # Record audit log event
                try:
                    record_case(
                        dispute_id=dispute_id,
                        status="under_review" if silence_action == "fight" else "lost",
                        action="silence_policy_default",
                        actor="sweep",
                        details={
                            "decision_id": dec_id,
                            "silence_action": silence_action,
                            "trigger": reason,
                            "sent_at": sent_raw,
                            "evidence_due_by": due_raw,
                            "applied_at": now_iso,
                        },
                    )
                except Exception:
                    pass

                # Notify owner via SMS
                try:
                    sms_body = (
                        f"Rebuttal Sweep: Silence policy applied default '{silence_action}' "
                        f"for dispute {dispute_id} ({reason})."
                    )
                    send_owner_sms(sms_body)
                except Exception:
                    pass

                defaulted_decisions.append({
                    "decision_id": dec_id,
                    "dispute_id": dispute_id,
                    "action": silence_action,
                    "status": "approved",
                    "reason": reason,
                })
            else:
                untouched_decisions.append({
                    "decision_id": dec_id,
                    "dispute_id": dispute_id,
                    "status": "pending",
                })

        # ---------------------------------------------------------------------
        # 2. Check for open Stripe disputes without a case file
        # ---------------------------------------------------------------------
        if check_stripe:
            try:
                from agent.tools.stripe_tools import list_open_disputes, verify_live_key_guard
                verify_live_key_guard()
                open_disputes = list_open_disputes(limit=25)
                for disp in open_disputes:
                    disp_id = disp.get("id")
                    if not disp_id:
                        continue

                    existing = cur.execute(
                        "SELECT id FROM disputes WHERE id = ? OR instr(metadata, ?) > 0",
                        (disp_id, disp_id),
                    ).fetchone()

                    if not existing:
                        meta = disp.get("metadata") or {}
                        order_id = meta.get("order_id") if isinstance(meta, dict) else None
                        pi_id = disp.get("payment_intent")
                        ch_id = disp.get("charge")
                        amount = disp.get("amount", 0)
                        currency = disp.get("currency", "usd")
                        disp_reason = disp.get("reason", "general")
                        disp_status = disp.get("status", "needs_response")

                        ev_due_raw = None
                        ev_details = disp.get("evidence_details")
                        if isinstance(ev_details, dict):
                            ev_due_raw = ev_details.get("due_by")
                        if isinstance(ev_due_raw, int):
                            ev_due_iso = datetime.fromtimestamp(ev_due_raw, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                        elif isinstance(ev_due_raw, str):
                            ev_due_iso = ev_due_raw
                        else:
                            ev_due_iso = None

                        cur.execute(
                            """INSERT INTO disputes
                               (id, order_id, payment_intent_id, charge_id, amount_cents, currency, reason, status, evidence_due_by, metadata, created_at, updated_at)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (
                                disp_id,
                                order_id,
                                pi_id,
                                ch_id,
                                amount,
                                currency,
                                disp_reason,
                                disp_status,
                                ev_due_iso,
                                json.dumps(meta),
                                now_iso,
                                now_iso,
                            ),
                        )
                        conn.commit()
                        opened_disputes.append(disp_id)

                        try:
                            record_case(
                                dispute_id=disp_id,
                                status=disp_status,
                                action="open_case_file",
                                actor="sweep",
                                details={"source": "stripe_sweep", "opened_at": now_iso},
                            )
                        except Exception:
                            pass
            except Exception:
                pass

    finally:
        conn.close()

    return {
        "now": now_iso,
        "defaulted_decisions": defaulted_decisions,
        "untouched_decisions": untouched_decisions,
        "opened_disputes": opened_disputes,
    }


def main():
    parser = argparse.ArgumentParser(description="Rebuttal Deadline and Silence Policy Sweep")
    parser.add_argument("--now", type=str, help="Injected current ISO timestamp (e.g. 2026-09-05T12:00:00Z)")
    parser.add_argument("--no-stripe", action="store_true", help="Skip Stripe open dispute synchronization")
    args = parser.parse_args()

    if args.now:
        now_dt = _parse_iso(args.now)
        if not now_dt:
            print(f"Invalid ISO timestamp: {args.now}", file=sys.stderr)
            sys.exit(1)
    else:
        now_dt = datetime.now(timezone.utc)

    result = run_sweep(now=now_dt, check_stripe=not args.no_stripe)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
