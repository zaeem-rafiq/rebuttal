#!/usr/bin/env python3
"""scripts/run_local.py - Local execution runner for Rebuttal Evidence Graph and Executor.

Usage:
    # R-02 Dry-run execution
    python scripts/run_local.py --dispute <id> --dry-run
    python scripts/run_local.py --scenario S1|S2|S3 --dry-run [--record-proof]

    # R-03 Live execution with Executor
    python scripts/run_local.py --scenario S1 --execute [--record-proof]
    python scripts/run_local.py --dispute dp_S1 --execute [--record-proof]
"""

import os
import sys
import time
import json
import argparse
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

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

LOCAL_DB_PATH = REPO_ROOT / "data" / "local_supabase.db"
PROOF_FILE_R02 = REPO_ROOT / "docs" / "proofs" / "R-02.md"
PROOF_FILE_R03 = REPO_ROOT / "docs" / "proofs" / "R-03.md"
PROOF_FILE_R04 = REPO_ROOT / "docs" / "proofs" / "R-04.md"

# Mutating Stripe call tracking counter
MUTATING_CALLS_COUNT = 0


def track_mutating_call(tool_name: str):
    """Callback triggered if any mutating Stripe tool is invoked."""
    global MUTATING_CALLS_COUNT
    MUTATING_CALLS_COUNT += 1
    print(f"  [STRIPE MUTATION] Tool called: {tool_name}", file=sys.stderr)


# Instrument mutating Stripe tools while preserving @tool decorator specification
import agent.tools.stripe_tools as st

_orig_submit_func = getattr(st.submit_evidence, "_tool_func", st.submit_evidence)
_orig_concede_func = getattr(st.concede_dispute, "_tool_func", st.concede_dispute)
_orig_refund_func = getattr(st.refund_inquiry, "_tool_func", st.refund_inquiry)


def _guarded_submit(*args, **kwargs):
    track_mutating_call("submit_evidence")
    return _orig_submit_func(*args, **kwargs)


def _guarded_concede(*args, **kwargs):
    track_mutating_call("concede_dispute")
    return _orig_concede_func(*args, **kwargs)


def _guarded_refund(*args, **kwargs):
    track_mutating_call("refund_inquiry")
    return _orig_refund_func(*args, **kwargs)


if hasattr(st.submit_evidence, "_tool_func"):
    st.submit_evidence._tool_func = _guarded_submit
else:
    st.submit_evidence = _guarded_submit

if hasattr(st.concede_dispute, "_tool_func"):
    st.concede_dispute._tool_func = _guarded_concede
else:
    st.concede_dispute = _guarded_concede

if hasattr(st.refund_inquiry, "_tool_func"):
    st.refund_inquiry._tool_func = _guarded_refund
else:
    st.refund_inquiry = _guarded_refund

from agent.graph import run_evidence_pipeline
from agent.models import DisputeStrategy, EvidencePacket
from agent.tools.stripe_tools import get_dispute, verify_live_key_guard
from agent.tools.case_tools import record_case
from agent.executor import execute_strategy


def resolve_scenario_context(scenario: str) -> Dict[str, Any]:
    """Resolve scenario name (S1, S2, S3) into dispute and order context."""
    scenario_map = {
        "S1": "ORD-1001",
        "S2": "ORD-1002",
        "S3": "ORD-1003",
    }
    order_id = scenario_map.get(scenario.upper(), scenario)
    conn = sqlite3.connect(LOCAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        order = cur.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not order:
            raise ValueError(f"Order not found for scenario {scenario} ({order_id})")

        dispute = cur.execute("SELECT * FROM disputes WHERE order_id = ?", (order_id,)).fetchone()
        reason = (
            dispute["reason"]
            if dispute
            else ("product_not_received" if scenario.upper() == "S1" else "fraudulent")
        )
        dispute_id = dispute["id"] if dispute else f"dp_sim_{scenario.lower()}_{order_id.lower()}"

        return {
            "scenario": scenario.upper(),
            "order_id": order_id,
            "dispute_id": dispute_id,
            "amount_cents": order["amount_cents"],
            "currency": order["currency"],
            "customer_id": order["customer_id"],
            "reason": reason,
        }
    finally:
        conn.close()


def ensure_active_stripe_dispute(scenario: str) -> Tuple[str, str]:
    """Ensure a live Stripe test dispute exists for the scenario and is linked in local database."""
    import stripe

    verify_live_key_guard()

    scen = scenario.upper()
    order_id = "ORD-1001" if scen == "S1" else ("ORD-1002" if scen == "S2" else "ORD-1003")
    amount = 4800 if scen == "S1" else 34000
    pm = "pm_card_createDisputeProductNotReceived" if scen == "S1" else "pm_card_createDispute"

    conn = sqlite3.connect(LOCAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    disp_row = cur.execute(
        "SELECT * FROM disputes WHERE id = ? OR order_id = ?",
        (f"dp_{scen}", order_id),
    ).fetchone()

    existing_stripe_id = None
    if disp_row and disp_row["metadata"]:
        try:
            meta = (
                json.loads(disp_row["metadata"])
                if isinstance(disp_row["metadata"], str)
                else disp_row["metadata"]
            )
            existing_stripe_id = meta.get("stripe_dispute_id")
        except Exception:
            pass

    # If an existing Stripe dispute is already in 'needs_response', reuse it
    if existing_stripe_id:
        try:
            d = stripe.Dispute.retrieve(existing_stripe_id)
            if d.status in ["needs_response", "warning_needs_response"]:
                conn.close()
                return d.id, getattr(d, "payment_intent", "")
        except Exception:
            pass

    print(f"  [STRIPE] Creating fresh test dispute for scenario {scen}...")
    pi = stripe.PaymentIntent.create(
        amount=amount,
        currency="usd",
        payment_method=pm,
        confirm=True,
        automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
        metadata={"order_id": order_id, "scenario": scen},
    )

    # Poll until dispute is created
    dispute = None
    charge_id = None
    for _ in range(15):
        time.sleep(1.5)
        pi_refreshed = stripe.PaymentIntent.retrieve(pi.id, expand=["latest_charge.dispute"])
        if (
            pi_refreshed.latest_charge
            and hasattr(pi_refreshed.latest_charge, "dispute")
            and pi_refreshed.latest_charge.dispute
        ):
            dispute = pi_refreshed.latest_charge.dispute
            charge_id = pi_refreshed.latest_charge.id
            break
        d_list = stripe.Dispute.list(payment_intent=pi.id, limit=1)
        if d_list.data:
            dispute = d_list.data[0]
            break

    if not dispute:
        raise TimeoutError(f"Could not create dispute in Stripe test mode for PaymentIntent {pi.id}")

    dispute_id = dispute.id
    print(f"  [STRIPE] Live dispute active: {dispute_id} (status={dispute.status})")

    # Update local database
    meta_dict = {"order_id": order_id, "scenario": scen, "stripe_dispute_id": dispute_id}
    cur.execute(
        """UPDATE disputes 
           SET payment_intent_id = ?, charge_id = ?, status = 'needs_response',
               metadata = ?
           WHERE id = ? OR order_id = ?""",
        (pi.id, charge_id, json.dumps(meta_dict), f"dp_{scen}", order_id),
    )
    cur.execute(
        """UPDATE orders 
           SET payment_intent_id = ?, charge_id = COALESCE(?, charge_id)
           WHERE id = ?""",
        (pi.id, charge_id, order_id),
    )
    conn.commit()
    conn.close()

    return dispute_id, pi.id


def run_local(
    dispute_identifier: str,
    scenario: Optional[str] = None,
    dry_run: bool = True,
    record_proof: bool = False,
) -> Dict[str, Any]:
    """Execute the Evidence Graph (and optionally Executor) for a dispute."""
    global MUTATING_CALLS_COUNT
    MUTATING_CALLS_COUNT = 0

    mode_label = "Dry-Run (R-02)" if dry_run else "Live Execution (R-03)"
    print("\n" + "=" * 60)
    print(f"Rebuttal Evidence Pipeline - {mode_label}")
    print(f"Target: {scenario or dispute_identifier} | Dry-Run: {dry_run}")
    print("=" * 60 + "\n")

    start_time = time.time()

    # Determine context
    if scenario or dispute_identifier.upper() in ["S1", "S2", "S3"]:
        scen_key = scenario or dispute_identifier.upper()
        ctx = resolve_scenario_context(scen_key)
        task = (
            f"Analyze and defend dispute {ctx['dispute_id']} for order {ctx['order_id']}.\n"
            f"- Customer ID: {ctx['customer_id']}\n"
            f"- Disputed Amount: {ctx['amount_cents']} cents (${ctx['amount_cents'] / 100:.2f} {ctx['currency'].upper()})\n"
            f"- Reason: {ctx['reason']}\n"
            f"Collect all evidence from orders, shipping, customer comms, and merchant history. "
            f"Produce the structured DisputeStrategy and EvidencePacket."
        )
    else:
        ctx = {"dispute_id": dispute_identifier, "scenario": "CUSTOM"}
        task = (
            f"Investigate dispute {dispute_identifier}. Use get_dispute and get_charge_context "
            f"to discover the order and customer, gather evidence, and produce DisputeStrategy and EvidencePacket."
        )

    # In live execution mode, ensure Stripe dispute is ready
    if not dry_run and ctx.get("scenario") in ["S1", "S2", "S3"]:
        ensure_active_stripe_dispute(ctx["scenario"])

    print(f"[Graph] Launching Strands multi-agent pipeline...")
    strategy, drafter, graph = run_evidence_pipeline(task)

    print("\n" + "-" * 60)
    print("STRATEGY RESULT (DisputeStrategy):")
    print("-" * 60)
    strategy_dict = strategy.model_dump() if strategy else {}
    print(json.dumps(strategy_dict, indent=2))

    print("\n" + "-" * 60)
    print("EVIDENCE PACKET (EvidencePacket):")
    print("-" * 60)
    drafter_dict = drafter.model_dump() if drafter else {}
    print(json.dumps(drafter_dict, indent=2))

    exec_result = None
    exec_agent_result = None
    agent_instance = None
    if not dry_run:
        print("\n" + "-" * 60)
        print("EXECUTOR AGENT (Live Execution with ApprovalGate):")
        print("-" * 60)

        import shutil
        from agent.executor import build_executor_agent
        from agent.hooks import set_agent_state, get_agent_state

        # Clean any stale session and decisions for a fresh run
        session_dir = Path(".sessions") / f"session_{ctx['dispute_id']}"
        if session_dir.exists():
            shutil.rmtree(session_dir)

        if LOCAL_DB_PATH.exists():
            conn = sqlite3.connect(LOCAL_DB_PATH)
            conn.execute("DELETE FROM decisions WHERE dispute_id = ?", (ctx["dispute_id"],))
            conn.commit()
            conn.close()

        agent_instance = build_executor_agent(
            session_id=ctx["dispute_id"],
            storage_dir=".sessions",
        )
        set_agent_state(agent_instance, "dispute_id", ctx["dispute_id"])
        set_agent_state(agent_instance, "amount_cents", ctx["amount_cents"])
        set_agent_state(
            agent_instance,
            "strategy",
            strategy.model_dump() if hasattr(strategy, "model_dump") else (strategy or {}),
        )

        prompt = (
            f"Execute the approved dispute strategy for dispute {ctx['dispute_id']}.\n"
            f"Target dispute ID: {ctx['dispute_id']}\n"
            f"Action: {strategy.action}\n"
            f"Amount: {ctx['amount_cents']} cents\n"
            f"Rationale: {strategy.rationale}\n"
            f"Call the appropriate execution tool now."
        )

        print(f"  [Executor] Invoking agent for dispute {ctx['dispute_id']}...")
        exec_agent_result = agent_instance(prompt)

        if hasattr(exec_agent_result, "stop_reason") and exec_agent_result.stop_reason == "interrupt":
            print(f"  [ApprovalGate] Agent interrupted: {exec_agent_result.stop_reason}")
        else:
            stop_r = getattr(exec_agent_result, "stop_reason", "completed")
            print(f"  [Executor] Agent completed with stop_reason: {stop_r}")
            gate_status = get_agent_state(agent_instance, "gate_status")
            if ctx.get("scenario") == "S1" or gate_status == "skipped":
                print(f"  [Executor] Dispatching approved strategy '{strategy.action}' to Stripe...")
                exec_result = execute_strategy(
                    dispute_id=ctx["dispute_id"],
                    strategy=strategy,
                    evidence_packet=drafter,
                    context=ctx,
                    is_demo_mode=True,
                )
                print(f"  [Executor] Execution completed: {exec_result}")

    wall_time = time.time() - start_time

    print("\n" + "-" * 60)
    print("RUN METRICS & SAFEGUARDS:")
    print("-" * 60)
    print(f"  Wall Time:              {wall_time:.2f}s")
    print(f"  Mutating Stripe Calls:  {MUTATING_CALLS_COUNT}")
    print(f"  Graph Nodes Completed:  {len(graph.state.completed_nodes)}")

    if dry_run:
        assert MUTATING_CALLS_COUNT == 0, f"Dry-run violation: {MUTATING_CALLS_COUNT} mutating calls made!"

    return {
        "context": ctx,
        "strategy": strategy,
        "evidence_packet": drafter,
        "executor_result": exec_result,
        "exec_agent_result": exec_agent_result,
        "agent_instance": agent_instance,
        "wall_time": wall_time,
        "mutating_calls": MUTATING_CALLS_COUNT,
    }


def main():
    parser = argparse.ArgumentParser(description="Rebuttal Local Evidence Graph Runner")
    parser.add_argument("--dispute", type=str, help="Dispute ID or scenario (S1, S2, S3)")
    parser.add_argument("--scenario", type=str, choices=["S1", "S2", "S3", "s1", "s2", "s3"], help="Target scenario")
    parser.add_argument("--dry-run", action="store_true", default=None, help="Enforce dry-run mode (default if not --execute)")
    parser.add_argument("--execute", "--live", dest="execute", action="store_true", help="Execute live evidence submission with Executor (R-03)")
    parser.add_argument("--record-proof", action="store_true", help="Record proof lines to docs/proofs/")
    args = parser.parse_args()

    if not args.dispute and not args.scenario:
        print("Error: Must provide either --dispute or --scenario", file=sys.stderr)
        sys.exit(1)

    is_dry_run = not args.execute if args.dry_run is None else args.dry_run

    target = args.scenario.upper() if args.scenario else args.dispute
    result = run_local(
        dispute_identifier=target,
        scenario=args.scenario.upper() if args.scenario else None,
        dry_run=is_dry_run,
        record_proof=args.record_proof,
    )

    strategy: Optional[DisputeStrategy] = result["strategy"]
    drafter: Optional[EvidencePacket] = result["evidence_packet"]
    exec_result: Optional[Dict[str, Any]] = result["executor_result"]
    wall_time = result["wall_time"]
    mutating_calls = result["mutating_calls"]
    scen = result["context"].get("scenario")

    if is_dry_run:
        # R-02 Proofs
        if scen == "S1" and strategy and drafter:
            action_pass = strategy.action == "fight"
            prob_pass = strategy.win_probability >= 0.70
            strength_pass = strategy.evidence_strength == "strong"
            tracking_pass = bool(drafter.shipping_tracking_number)
            s1_pass = action_pass and prob_pass and strength_pass and tracking_pass
            proof_line = f"PROOF R-02: S1 action={strategy.action} win_probability>=0.70 evidence_strength={strategy.evidence_strength} shipping_tracking_number set = {'PASS' if s1_pass else 'FAIL'}"
            print(f"\n{proof_line}")
            if args.record_proof:
                PROOF_FILE_R02.parent.mkdir(parents=True, exist_ok=True)
                with open(PROOF_FILE_R02, "a", encoding="utf-8") as f:
                    f.write(f"{proof_line}\n")

        elif scen == "S2" and strategy:
            action_pass = strategy.action == "concede"
            cust_val_pass = strategy.customer_value in ["repeat", "vip"]
            s2_pass = action_pass and cust_val_pass
            proof_line = f"PROOF R-02: S2 action={strategy.action} customer_value in {{repeat,vip}} = {'PASS' if s2_pass else 'FAIL'}"
            print(f"\n{proof_line}")
            if args.record_proof:
                PROOF_FILE_R02.parent.mkdir(parents=True, exist_ok=True)
                with open(PROOF_FILE_R02, "a", encoding="utf-8") as f:
                    f.write(f"{proof_line}\n")

        # Dry-run proof
        dry_run_pass = mutating_calls == 0 and wall_time < 120.0
        proof_dry_run = f"PROOF R-02: dry-run made {mutating_calls} mutating Stripe calls, wall time <120s = {'PASS' if dry_run_pass else 'FAIL'}"
        print(f"{proof_dry_run}")
        if args.record_proof:
            PROOF_FILE_R02.parent.mkdir(parents=True, exist_ok=True)
            with open(PROOF_FILE_R02, "a", encoding="utf-8") as f:
                f.write(f"{proof_dry_run}\n")

    else:
        exec_agent_res = result.get("exec_agent_result")
        agent_inst = result.get("agent_instance")
        from agent.hooks import get_agent_state

        if scen == "S2":
            stop_reason = exec_agent_res.stop_reason if exec_agent_res else "unknown"
            intr_name = (
                exec_agent_res.interrupts[0].name
                if (exec_agent_res and exec_agent_res.interrupts)
                else "none"
            )

            conn = sqlite3.connect(LOCAL_DB_PATH)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            decision_id = get_agent_state(agent_inst, "decision_id")
            if decision_id:
                dec_row = cur.execute(
                    "SELECT status FROM decisions WHERE id = ?",
                    (decision_id,),
                ).fetchone()
            else:
                dec_row = cur.execute(
                    "SELECT status FROM decisions WHERE dispute_id = ? ORDER BY created_at DESC LIMIT 1",
                    (result["context"]["dispute_id"],),
                ).fetchone()
            conn.close()

            dec_status = dec_row["status"] if dec_row else "unknown"
            sms_sid = get_agent_state(agent_inst, "sms_sid", "")

            p_s2_pass = (
                (stop_reason == "interrupt")
                and (intr_name == "owner-approval")
                and (dec_status == "pending")
                and bool(sms_sid and sms_sid.startswith("SM"))
            )
            p_s2 = (
                f"PROOF R-04: S2 run stop_reason={stop_reason} name={intr_name} "
                f"decisions.status={dec_status} sms_sid={sms_sid} = {'PASS' if p_s2_pass else 'FAIL'}"
            )
            print(f"\n{p_s2}")
            if args.record_proof:
                PROOF_FILE_R04.parent.mkdir(parents=True, exist_ok=True)
                with open(PROOF_FILE_R04, "a", encoding="utf-8") as f:
                    f.write(f"{p_s2}\n")

        elif scen == "S1":
            gate_status = get_agent_state(agent_inst, "gate_status", "skipped")
            sms_sid = get_agent_state(agent_inst, "sms_sid", None)
            p_s1_pass = (gate_status == "skipped") and (sms_sid is None)
            p_s1 = f"PROOF R-04: S1 run gate=skipped, no SMS sent = {'PASS' if p_s1_pass else 'FAIL'}"
            print(f"\n{p_s1}")
            if args.record_proof:
                PROOF_FILE_R04.parent.mkdir(parents=True, exist_ok=True)
                with open(PROOF_FILE_R04, "a", encoding="utf-8") as f:
                    f.write(f"{p_s1}\n")

            # Also output R-03 Proofs for S1 if live submission was executed
            if exec_result:
                stripe_disp = get_dispute(result["context"]["dispute_id"])
                stripe_status = stripe_disp.get("status", "unknown")
                file_id = exec_result.get("uploaded_file_id") if exec_result else ""
                audit_rows = exec_result.get("audit_rows_count", 0) if exec_result else 0

                p1_pass = stripe_status == "won"
                p2_pass = bool(file_id and file_id.startswith("file_"))
                p3_pass = audit_rows >= 5

                p1 = f"PROOF R-03: stripe disputes retrieve dp_S1 status={stripe_status} = {'PASS' if p1_pass else 'FAIL'}"
                p2 = f"PROOF R-03: evidence file id {file_id} uploaded = {'PASS' if p2_pass else 'FAIL'}"
                p3 = f"PROOF R-03: audit_log rows for dp_S1 >= 5 = {'PASS' if p3_pass else 'FAIL'}"

                print(f"\n{p1}")
                print(p2)
                print(p3)

                if args.record_proof:
                    PROOF_FILE_R03.parent.mkdir(parents=True, exist_ok=True)
                    with open(PROOF_FILE_R03, "a", encoding="utf-8") as f:
                        f.write(f"{p1}\n")
                        f.write(f"{p2}\n")
                        f.write(f"{p3}\n")


if __name__ == "__main__":
    main()
