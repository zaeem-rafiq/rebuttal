"""
scripts/test_s_b.py

Verification script for HAC-18 (S-B · Stretch: AgentCore Gateway exposes order and tracking tools as MCP).
Evaluates:
1. agent.tool_names includes lookup_order,get_tracking
2. S1 via Gateway → action=fight
"""

import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

load_dotenv()

from agent.graph import build_evidence_graph, run_evidence_pipeline
from agent.tools.gateway_client import get_gateway_tools


def test_s_b():
    print("\n=== Testing HAC-18 (S-B): AgentCore Gateway MCP ===", flush=True)

    # 1. Verify Gateway tools availability & agent.tool_names
    graph, agents = build_evidence_graph()
    orders_agent = agents.get("orders")
    shipping_agent = agents.get("shipping")

    all_tool_names = set(orders_agent.tool_names) | set(shipping_agent.tool_names)
    print(f"Orders agent tool_names:   {orders_agent.tool_names}", flush=True)
    print(f"Shipping agent tool_names: {shipping_agent.tool_names}", flush=True)

    has_lookup = "lookup_order" in all_tool_names or "lookup_order" in orders_agent.tool_names
    has_tracking = "get_tracking" in all_tool_names or "get_tracking" in shipping_agent.tool_names

    if not (has_lookup and has_tracking):
        print(f"FAILED: Expected lookup_order and get_tracking in tool_names. Found: {all_tool_names}", flush=True)
        sys.exit(1)

    proof_1 = "PROOF S-B: agent.tool_names includes lookup_order,get_tracking = PASS"
    print(proof_1, flush=True)

    # 2. Run Scenario S1 via Gateway
    print("\nExecuting S1 pipeline via Gateway tools...", flush=True)
    s1_task = (
        "Process dispute dp_S1 for order ORD-1001 ($48.00 USD). "
        "Customer claim: product_not_received. Reason: product_not_received. "
        "Investigate order and shipping delivery evidence via AgentCore Gateway and synthesize strategy."
    )

    strategy, evidence_packet, _ = run_evidence_pipeline(s1_task)

    if not strategy:
        print("FAILED: Strategy node did not return a valid DisputeStrategy.", flush=True)
        sys.exit(1)

    print(f"S1 Strategy Action: {strategy.action} (win_probability: {strategy.win_probability})", flush=True)
    print(f"S1 Strategy Rationale: {strategy.rationale}", flush=True)

    if strategy.action != "fight":
        print(f"FAILED: Expected action='fight', got '{strategy.action}'", flush=True)
        sys.exit(1)

    proof_2 = "PROOF S-B: S1 via Gateway → action=fight = PASS"
    print(proof_2, flush=True)

    # Write proof lines to docs/proofs/S-B.md
    proof_file = Path("docs/proofs/S-B.md")
    proof_file.parent.mkdir(parents=True, exist_ok=True)
    with open(proof_file, "w", encoding="utf-8") as f:
        f.write(f"{proof_1}\n{proof_2}\n")

    print(f"\nSuccessfully wrote proofs to {proof_file}", flush=True)
    print("\nALL S-B PROOFS PASSED!")


if __name__ == "__main__":
    test_s_b()
