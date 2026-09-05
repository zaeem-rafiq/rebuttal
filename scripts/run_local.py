#!/usr/bin/env python3
"""scripts/run_local.py - Local execution runner for Rebuttal Evidence Graph.

Usage:
    python scripts/run_local.py --dispute <id> --dry-run
    python scripts/run_local.py --scenario S1|S2|S3 --dry-run [--record-proof]
"""

import os
import sys
import time
import json
import argparse
import sqlite3
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

LOCAL_DB_PATH = REPO_ROOT / "data" / "local_supabase.db"
PROOF_FILE = REPO_ROOT / "docs" / "proofs" / "R-02.md"

# Mutating Stripe call tracking counter
MUTATING_CALLS_COUNT = 0


def track_mutating_call(tool_name: str):
    """Callback triggered if any mutating Stripe tool is invoked."""
    global MUTATING_CALLS_COUNT
    MUTATING_CALLS_COUNT += 1
    print(f"  [MUTATION DETECTED] Tool called: {tool_name}", file=sys.stderr)


# Instrument mutating Stripe tools
import agent.tools.stripe_tools as st

_orig_submit = st.submit_evidence
_orig_concede = st.concede_dispute
_orig_refund = st.refund_inquiry

def _guarded_submit(*args, **kwargs):
    track_mutating_call("submit_evidence")
    return _orig_submit(*args, **kwargs)

def _guarded_concede(*args, **kwargs):
    track_mutating_call("concede_dispute")
    return _orig_concede(*args, **kwargs)

def _guarded_refund(*args, **kwargs):
    track_mutating_call("refund_inquiry")
    return _orig_refund(*args, **kwargs)

st.submit_evidence = _guarded_submit
st.concede_dispute = _guarded_concede
st.refund_inquiry = _guarded_refund

from agent.graph import run_evidence_pipeline
from agent.models import DisputeStrategy, EvidencePacket


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
        reason = dispute["reason"] if dispute else ("product_not_received" if scenario.upper() == "S1" else "fraudulent")
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


def run_local(
    dispute_identifier: str,
    scenario: Optional[str] = None,
    dry_run: bool = True,
    record_proof: bool = False,
) -> Dict[str, Any]:
    """Execute the Evidence Graph for a dispute in local/dry-run mode."""
    global MUTATING_CALLS_COUNT
    MUTATING_CALLS_COUNT = 0

    print("\n" + "=" * 60)
    print(f"Rebuttal Evidence Graph - Local Execution (R-02)")
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

    print(f"[Graph] Launching Strands multi-agent pipeline...")
    strategy, drafter, graph = run_evidence_pipeline(task)
    wall_time = time.time() - start_time

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

    print("\n" + "-" * 60)
    print("RUN METRICS & SAFEGUARDS:")
    print("-" * 60)
    print(f"  Wall Time:              {wall_time:.2f}s (< 120s target)")
    print(f"  Mutating Stripe Calls:  {MUTATING_CALLS_COUNT} (0 required in dry-run)")
    print(f"  Graph Nodes Completed:  {len(graph.state.completed_nodes)}")

    if dry_run:
        assert MUTATING_CALLS_COUNT == 0, f"Dry-run violation: {MUTATING_CALLS_COUNT} mutating calls made!"

    return {
        "context": ctx,
        "strategy": strategy,
        "evidence_packet": drafter,
        "wall_time": wall_time,
        "mutating_calls": MUTATING_CALLS_COUNT,
    }


def main():
    parser = argparse.ArgumentParser(description="Rebuttal Local Evidence Graph Runner")
    parser.add_argument("--dispute", type=str, help="Dispute ID or scenario (S1, S2, S3)")
    parser.add_argument("--scenario", type=str, choices=["S1", "S2", "S3", "s1", "s2", "s3"], help="Target scenario")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Enforce dry-run mode (default: True)")
    parser.add_argument("--record-proof", action="store_true", help="Record proof lines to docs/proofs/R-02.md")
    args = parser.parse_args()

    if not args.dispute and not args.scenario:
        print("Error: Must provide either --dispute or --scenario", file=sys.stderr)
        sys.exit(1)

    target = args.scenario.upper() if args.scenario else args.dispute
    result = run_local(
        dispute_identifier=target,
        scenario=args.scenario.upper() if args.scenario else None,
        dry_run=args.dry_run,
        record_proof=args.record_proof,
    )

    strategy: Optional[DisputeStrategy] = result["strategy"]
    drafter: Optional[EvidencePacket] = result["evidence_packet"]
    wall_time = result["wall_time"]
    mutating_calls = result["mutating_calls"]

    # Check proofs for scenario
    scen = result["context"].get("scenario")
    if scen == "S1" and strategy and drafter:
        action_pass = strategy.action == "fight"
        prob_pass = strategy.win_probability >= 0.70
        strength_pass = strategy.evidence_strength == "strong"
        tracking_pass = bool(drafter.shipping_tracking_number)
        s1_pass = action_pass and prob_pass and strength_pass and tracking_pass
        proof_line = f"PROOF R-02: S1 action={strategy.action} win_probability>=0.70 evidence_strength={strategy.evidence_strength} shipping_tracking_number set = {'PASS' if s1_pass else 'FAIL'}"
        print(f"\n{proof_line}")
        if args.record_proof:
            PROOF_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(PROOF_FILE, "a", encoding="utf-8") as f:
                f.write(f"{proof_line}\n")

    elif scen == "S2" and strategy:
        action_pass = strategy.action == "concede"
        cust_val_pass = strategy.customer_value in ["repeat", "vip"]
        s2_pass = action_pass and cust_val_pass
        proof_line = f"PROOF R-02: S2 action={strategy.action} customer_value in {{repeat,vip}} = {'PASS' if s2_pass else 'FAIL'}"
        print(f"\n{proof_line}")
        if args.record_proof:
            PROOF_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(PROOF_FILE, "a", encoding="utf-8") as f:
                f.write(f"{proof_line}\n")

    # Dry-run proof
    dry_run_pass = mutating_calls == 0 and wall_time < 120.0
    proof_dry_run = f"PROOF R-02: dry-run made {mutating_calls} mutating Stripe calls, wall time <120s = {'PASS' if dry_run_pass else 'FAIL'}"
    print(f"{proof_dry_run}")
    if args.record_proof:
        PROOF_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PROOF_FILE, "a", encoding="utf-8") as f:
            f.write(f"{proof_dry_run}\n")


if __name__ == "__main__":
    main()
