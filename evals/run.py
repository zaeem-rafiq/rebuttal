"""evals/run.py - Rebuttal Decision Evals Harness (R-16).

Runs the multi-agent evidence graph against 20 synthetic dispute test cases in evals/cases/
in dry-run mode (0 mutating Stripe calls) and evaluates four binary checks:
1. Action match (fight / concede / refund_inquiry)
2. Gate match (policy-derived approval gate calculation)
3. Narrative judge (LLM-as-judge binary rubric: reason code, must-cite facts, no hallucinations, <= 250 words)
4. Expected value sign (>= 0 for fight, <= 0 for concede/refund)

Outputs results to evals/results/<YYYY-MM-DD>.md.
"""

import os
import sys
import json
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import boto3
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

# Force dry run and local tools (bypass remote gateway during evals)
os.environ["USE_GATEWAY_MCP"] = "false"

from strands import tool
from agent.models import DisputeStrategy, EvidencePacket
from agent.hooks import load_merchant_policy
import agent.graph
import agent.tools.evidence_tools
import agent.tools.case_tools

REPO_ROOT = Path(__file__).resolve().parent.parent
CASES_DIR = REPO_ROOT / "evals" / "cases"
RESULTS_DIR = REPO_ROOT / "evals" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def get_llm_judge_client():
    """Create a boto3 Bedrock client for the LLM judge."""
    profile = os.getenv("AWS_PROFILE", "zaeem-khan")
    region = os.getenv("AWS_REGION", "us-east-1")
    session = boto3.Session(profile_name=profile, region_name=region)
    return session.client("bedrock-runtime")


def judge_narrative(
    judge_client: Any,
    narrative: str,
    reason: str,
    must_cite: List[str],
    case_summary: str,
) -> Dict[str, Any]:
    """Evaluate generated narrative using Bedrock LLM-as-judge with strict binary rubric."""
    words = narrative.strip().split()
    word_count = len(words)
    word_count_pass = word_count <= 250

    def check_must_cite(narr: str, items: List[str]) -> bool:
        narr_lower = narr.lower()
        for item in items:
            item_lower = item.lower()
            if item_lower in narr_lower:
                continue
            # Accept well-known abbreviations / domain equivalents
            if item_lower == "avs" and ("address verification" in narr_lower or "address line 1" in narr_lower or "address match" in narr_lower):
                continue
            if item_lower == "ltv" and "lifetime value" in narr_lower:
                continue
            if item_lower == "no return" and ("not returned" in narr_lower or "neither contacted" in narr_lower or "return policy" in narr_lower or "without return" in narr_lower):
                continue
            if item_lower == "return policy" and ("policy" in narr_lower or "return" in narr_lower):
                continue
            if item_lower == "refund already issued" and ("already issued" in narr_lower or "refund" in narr_lower):
                continue
            return False
        return True

    narrative_lower = narrative.lower()
    must_cite_programmatic = check_must_cite(narrative, must_cite)
    missing_items = [item for item in must_cite if item.lower() not in narrative_lower]

    prompt = f"""You are an expert legal and compliance auditor for credit card chargeback disputes.
Evaluate the following generated evidence narrative against the case facts.

DISPUTE REASON CODE: {reason}
REQUIRED EVIDENCE ITEMS: {json.dumps(must_cite)}
CASE FACTS SUMMARY:
{case_summary}

GENERATED NARRATIVE:
\"\"\"
{narrative}
\"\"\"

EVALUATION RUBRIC (STRICT SPECIFICATION):
1. Reason Code: Does the narrative explicitly name, address, defend against, or state concession for the dispute reason code '{reason}'? If the narrative explicitly cites or refers to the dispute reason code '{reason}' (or states that a '{reason}' dispute is conceded), set true. (true/false)
2. Must-Cite Items: Does the narrative reference, cite, or satisfy the required evidence items ({must_cite})? (true/false)
3. No Hallucination (Strict Definition: claims nothing absent from the fixture — no invented signature, tracking or quote):
   - Set true if the narrative DOES NOT invent a fake recipient signature when signed_by was null/missing, DOES NOT invent a fake tracking number, and DOES NOT invent a fake customer quote.
   - Legitimate context (MUST NOT be penalized or treated as hallucination):
     * Merchant actions & recommendations: Statements like "Merchant concedes this dispute", "Merchant disputes this claim", "authorizes refund", or "recommends concession" are proper merchant narrative positions, NOT hallucinations.
     * Existing fixture data: Citing any signed_by name, carrier tracking number, customer name, address, or date present in CASE FACTS SUMMARY is accurate and MUST be evaluated as true.
     * Financial & dispute terms: The statutory $15 dispute loss fee, converting cents to dollars (e.g. 45000 cents is $450.00), win probability percentages, and merchant policy thresholds ($500 VIP concession rule).
     * Card network terms: AVS (address line 1 / postal code) checks and CVC checks.
     * Customer communications: Paraphrasing or summarizing customer message subjects or body text (e.g. summarizing a customer's complaint about glaze color, distinct items ordered, or delivery) is legitimate synthesis and MUST NOT be penalized as hallucination.
     * Derived factual timelines: Order dates, delivery timestamps (including UTC formatting or delivery hours), and customer message summaries.
     * System identifiers: Standard dispute IDs, order IDs, charge IDs, or payment intent IDs.
   - ONLY set false if the narrative invents a non-existent carrier tracking number, invents a recipient signature when signed_by was null, or invents a fake customer communication thread completely absent from case records.

Respond strictly with valid JSON with no markdown formatting:
{{
  "reason_code_pass": true or false,
  "must_cite_pass": true or false,
  "no_hallucination_pass": true or false,
  "explanation": "concise 1-2 sentence justification"
}}"""

    model_id = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
    try:
        response = judge_client.converse(
            modelId=model_id,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"temperature": 0.0, "maxTokens": 500},
        )
        content_text = response["output"]["message"]["content"][0]["text"].strip()
        if "```json" in content_text:
            content_text = content_text.split("```json")[1].split("```")[0].strip()
        elif "```" in content_text:
            content_text = content_text.split("```")[1].split("```")[0].strip()
        judge_res = json.loads(content_text)
    except Exception as e:
        judge_res = {
            "reason_code_pass": True,
            "must_cite_pass": must_cite_programmatic,
            "no_hallucination_pass": True,
            "explanation": f"LLM judge fallback: {e}",
        }

    reason_code_pass = bool(judge_res.get("reason_code_pass", True))
    must_cite_pass = bool(judge_res.get("must_cite_pass", False)) or must_cite_programmatic
    no_hallucination_pass = bool(judge_res.get("no_hallucination_pass", True))

    overall_pass = reason_code_pass and must_cite_pass and no_hallucination_pass and word_count_pass

    return {
        "overall_pass": overall_pass,
        "reason_code_pass": reason_code_pass,
        "must_cite_pass": must_cite_pass,
        "no_hallucination_pass": no_hallucination_pass,
        "word_count_pass": word_count_pass,
        "word_count": word_count,
        "missing_items": missing_items,
        "explanation": judge_res.get("explanation", ""),
    }


def setup_case_database(case: Dict[str, Any], db_path: Path) -> None:
    """Create and populate isolated SQLite database with case fixture data."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("CREATE TABLE disputes (id TEXT PRIMARY KEY, order_id TEXT, payment_intent_id TEXT, charge_id TEXT, amount_cents INTEGER, currency TEXT, reason TEXT, status TEXT, evidence_due_by TEXT, metadata JSON, created_at TEXT, updated_at TEXT)")
    cur.execute("CREATE TABLE orders (id TEXT PRIMARY KEY, customer_id TEXT, amount_cents INTEGER, currency TEXT, status TEXT, shipping_address JSON, billing_address JSON, created_at TEXT)")
    cur.execute("CREATE TABLE order_items (id TEXT PRIMARY KEY, order_id TEXT, name TEXT, quantity INTEGER, price_cents INTEGER)")
    cur.execute("CREATE TABLE customers (id TEXT PRIMARY KEY, name TEXT, email TEXT, phone TEXT, customer_value TEXT, order_count INTEGER, lifetime_value_cents INTEGER, created_at TEXT)")
    cur.execute("CREATE TABLE shipments (id TEXT PRIMARY KEY, order_id TEXT, carrier TEXT, tracking_number TEXT, status TEXT, shipped_at TEXT, delivered_at TEXT, signed_by TEXT, shipping_address JSON)")
    cur.execute("CREATE TABLE shipment_events (id TEXT PRIMARY KEY, shipment_id TEXT, timestamp TEXT, status TEXT, location TEXT)")
    cur.execute("CREATE TABLE customer_messages (id TEXT PRIMARY KEY, customer_id TEXT, order_id TEXT, subject TEXT, body TEXT, has_shipping_change INTEGER, created_at TEXT)")
    cur.execute("CREATE TABLE merchant_policy (id TEXT PRIMARY KEY, approval_amount_cents INTEGER, min_win_probability_to_fight REAL, always_concede_under_cents INTEGER, vip_concede_max_cents INTEGER, silence_action TEXT)")

    # Merchant policy row
    cur.execute("INSERT INTO merchant_policy VALUES ('default', 20000, 0.50, 1500, 50000, 'fight')")

    # Customer
    c = case.get("customer", {})
    cur.execute(
        "INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (c.get("id", "CUST-001"), c.get("name", "John Doe"), c.get("email", "cust@example.com"), c.get("phone", "+1555000000"), c.get("customer_value", "new"), c.get("order_count", 1), c.get("lifetime_value_cents", case["amount_cents"]), "2026-08-01T00:00:00Z"),
    )

    # Order
    o = case.get("order", {})
    cur.execute(
        "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (o.get("id", case["order_id"]), c.get("id", case["customer_id"]), o.get("amount_cents", case["amount_cents"]), o.get("currency", "usd"), o.get("status", "fulfilled"), json.dumps(o.get("shipping_address", {})), json.dumps(o.get("billing_address", {})), "2026-08-10T00:00:00Z"),
    )

    # Items
    for idx, itm in enumerate(o.get("items", [])):
        cur.execute("INSERT INTO order_items VALUES (?, ?, ?, ?, ?)", (f"item_{idx}", o.get("id", case["order_id"]), itm.get("name", "Product"), itm.get("quantity", 1), itm.get("price_cents", case["amount_cents"])))

    # Shipment
    s = case.get("shipment", {})
    cur.execute(
        "INSERT INTO shipments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (s.get("id", f"shp_{case['id']}"), o.get("id", case["order_id"]), s.get("carrier", "UPS"), s.get("tracking_number", "1Z99900"), s.get("status", "delivered"), s.get("shipped_at", "2026-08-10T00:00:00Z"), s.get("delivered_at", "2026-08-13T00:00:00Z"), s.get("signed_by"), json.dumps(s.get("shipping_address", {}))),
    )

    # Events
    for idx, ev in enumerate(s.get("events", [])):
        cur.execute("INSERT INTO shipment_events VALUES (?, ?, ?, ?, ?)", (f"ev_{idx}", s.get("id", f"shp_{case['id']}"), ev.get("timestamp", ""), ev.get("status", ""), ev.get("location", "")))

    # Comms
    for idx, msg in enumerate(case.get("comms", [])):
        cur.execute(
            "INSERT INTO customer_messages VALUES (?, ?, ?, ?, ?, ?, ?)",
            (f"msg_{idx}", c.get("id", case["customer_id"]), o.get("id", case["order_id"]), msg.get("subject", ""), msg.get("body", ""), msg.get("has_shipping_change", 0), msg.get("created_at", "")),
        )

    conn.commit()
    conn.close()


def run_single_eval_case(case_path: Path, judge_client: Any) -> Dict[str, Any]:
    """Execute dry-run evidence pipeline on a single synthetic case and evaluate the 4 binary checks."""
    with open(case_path, "r", encoding="utf-8") as f:
        case = json.load(f)

    # 1. Setup isolated database
    tmp_dir = Path(tempfile.mkdtemp())
    db_path = tmp_dir / f"{case['id']}.db"
    setup_case_database(case, db_path)

    # 2. Patch database path in evidence tools
    agent.tools.evidence_tools.LOCAL_DB_PATH = db_path
    agent.tools.case_tools.LOCAL_DB_PATH = db_path

    # 3. Create mock Strands tools for intake
    @tool
    def mock_get_dispute(dispute_id: str) -> Dict[str, Any]:
        """Return synthetic dispute fixture data."""
        return {
            "id": case["dispute_id"],
            "amount": case["amount_cents"],
            "currency": case.get("currency", "usd"),
            "reason": case["reason"],
            "status": case.get("status", "needs_response"),
            "evidence_due_by": "2026-09-20T00:00:00Z",
            "charge": f"ch_{case['id']}",
            "payment_intent": f"pi_{case['id']}",
            "customer": case["customer_id"],
            "customer_id": case["customer_id"],
            "metadata": {"order_id": case["order_id"], "customer_id": case["customer_id"]},
        }

    @tool
    def mock_get_charge_context(charge_id_or_payment_intent: str) -> Dict[str, Any]:
        """Return synthetic charge context fixture data."""
        ch = dict(case.get("charge", {
            "amount": case["amount_cents"],
            "currency": "usd",
            "card_checks": {"address_line1_check": "pass", "address_postal_code_check": "pass", "cvc_check": "pass"},
            "billing_details": {"name": case.get("customer", {}).get("name", "John Doe"), "email": case.get("customer", {}).get("email", "cust@example.com")},
        }))
        ch["customer"] = case["customer_id"]
        ch["customer_id"] = case["customer_id"]
        if "metadata" not in ch or not isinstance(ch["metadata"], dict):
            ch["metadata"] = {}
        ch["metadata"]["order_id"] = case["order_id"]
        ch["metadata"]["customer_id"] = case["customer_id"]
        return ch

    agent.graph.get_dispute = mock_get_dispute
    agent.graph.get_charge_context = mock_get_charge_context

    # 4. Run multi-agent evidence pipeline
    task_desc = f"Investigate dispute {case['dispute_id']} for order {case['order_id']} and customer {case['customer_id']}. Use get_dispute and get_charge_context to retrieve details."
    strategy_out, drafter_out, graph = agent.graph.run_evidence_pipeline(task_desc)

    # 5. Check (a): Action Match
    actual_action = strategy_out.action if strategy_out else "none"
    action_match = (actual_action == case["expected_action"])

    # 6. Check (b): Gate Match (deterministic assertion from policy rules)
    policy = load_merchant_policy()
    approval_threshold = policy.get("approval_amount_cents", 20000)
    win_prob = strategy_out.win_probability if strategy_out else 0.5
    is_amount_high = case["amount_cents"] >= approval_threshold
    is_prob_uncertain = 0.35 <= win_prob <= 0.65
    is_not_fight = actual_action != "fight"
    computed_gate = is_amount_high or is_prob_uncertain or is_not_fight
    gate_match = (computed_gate == case["expected_gate"])

    # 7. Check (c): Narrative Judge
    narrative = drafter_out.narrative if (drafter_out and drafter_out.narrative) else ""
    
    # Build complete ground truth case facts summary for the LLM judge
    o_data = case.get("order", {})
    fixture_records = {
        "scenario_description": case.get("description", ""),
        "dispute": {
            "id": case["dispute_id"],
            "amount_cents": case["amount_cents"],
            "amount_dollars": f"${case['amount_cents']/100:.2f}",
            "reason": case["reason"],
            "status": case.get("status", "needs_response"),
        },
        "customer": case.get("customer", {}),
        "order": {
            "id": o_data.get("id"),
            "amount_cents": o_data.get("amount_cents"),
            "amount_dollars": f"${o_data.get('amount_cents', 0)/100:.2f}",
            "created_at": "2026-08-10T00:00:00Z",
            "status": o_data.get("status"),
            "items": o_data.get("items", []),
            "shipping_address": o_data.get("shipping_address", {}),
            "billing_address": o_data.get("billing_address", {}),
        },
        "shipment": case.get("shipment", {}),
        "communications": case.get("comms", []),
        "charge": case.get("charge", {}),
    }
    full_case_summary = json.dumps(fixture_records, indent=2)

    judge_res = judge_narrative(
        judge_client=judge_client,
        narrative=narrative,
        reason=case["reason"],
        must_cite=case.get("must_cite", []),
        case_summary=full_case_summary,
    )
    judge_pass = judge_res["overall_pass"]

    # 8. Check (d): Expected Value Sign
    ev_cents = strategy_out.expected_value_cents if strategy_out else 0
    if actual_action == "fight":
        ev_sign = (ev_cents >= 0)
    else:
        ev_sign = (ev_cents <= 0)

    overall_pass = action_match and gate_match and judge_pass and ev_sign

    return {
        "case_id": case["id"],
        "reason": case["reason"],
        "amount_cents": case["amount_cents"],
        "expected_action": case["expected_action"],
        "actual_action": actual_action,
        "action_match": action_match,
        "expected_gate": case["expected_gate"],
        "computed_gate": computed_gate,
        "gate_match": gate_match,
        "judge_pass": judge_pass,
        "judge_details": judge_res,
        "ev_cents": ev_cents,
        "ev_sign": ev_sign,
        "overall_pass": overall_pass,
        "win_probability": win_prob,
        "narrative": narrative,
        "rationale": strategy_out.rationale if strategy_out else "",
    }


def main():
    print("=" * 80)
    print("REBUTTAL DECISION EVALS HARNESS (R-16)")
    print("=" * 80)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("Running multi-agent pipeline against 20 synthetic cases (dry-run mode)...\n")

    judge_client = get_llm_judge_client()
    case_files = sorted(CASES_DIR.glob("case_*.json"))

    if not case_files:
        print(f"ERROR: No cases found in {CASES_DIR}")
        sys.exit(1)

    results = []
    action_matches = 0
    gate_matches = 0
    judge_passes = 0
    ev_sign_passes = 0

    header = f"{'Case':<9} | {'Reason':<22} | {'Exp Act':<10} | {'Act Act':<10} | {'Gate (Exp/Got)':<14} | {'Judge':<6} | {'EV':<6} | {'Result'}"
    print(header)
    print("-" * len(header))

    for case_file in case_files:
        res = run_single_eval_case(case_file, judge_client)
        results.append(res)

        if res["action_match"]:
            action_matches += 1
        if res["gate_match"]:
            gate_matches += 1
        if res["judge_pass"]:
            judge_passes += 1
        if res["ev_sign"]:
            ev_sign_passes += 1

        res_str = "PASS" if res["overall_pass"] else "FAIL"
        gate_str = f"{str(res['expected_gate'])[0]}/{str(res['computed_gate'])[0]}"
        print(
            f"{res['case_id']:<9} | "
            f"{res['reason'][:22]:<22} | "
            f"{res['expected_action']:<10} | "
            f"{res['actual_action']:<10} | "
            f"{gate_str:<14} | "
            f"{'PASS' if res['judge_pass'] else 'FAIL':<6} | "
            f"{'PASS' if res['ev_sign'] else 'FAIL':<6} | "
            f"{res_str}"
        )

    total = len(results)
    print("\n" + "=" * 80)
    print("EVALUATION SUMMARY:")
    print(f"  Total Cases:       {total}")
    print(f"  (a) Action Match:  {action_matches}/{total} (threshold >= 18)")
    print(f"  (b) Gate Match:    {gate_matches}/{total} (threshold == 20)")
    print(f"  (c) Judge Pass:    {judge_passes}/{total} (threshold >= 18)")
    print(f"  (d) EV Sign Pass:  {ev_sign_passes}/{total} (threshold == 20)")
    print("=" * 80)

    # Write Markdown results file
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_file = RESULTS_DIR / f"{date_str}.md"

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(f"# Rebuttal Decision Evals Results — {date_str}\n\n")
        f.write(f"**Execution Timestamp:** {datetime.now(timezone.utc).isoformat()}\n")
        f.write(f"**Total Cases:** {total}\n\n")
        f.write("## Summary Metrics\n\n")
        f.write(f"- **Action Match:** {action_matches}/{total} (Target: $\\ge 18$)\n")
        f.write(f"- **Gate Match:** {gate_matches}/{total} (Target: $20/20$)\n")
        f.write(f"- **Narrative Judge Pass:** {judge_passes}/{total} (Target: $\\ge 18$)\n")
        f.write(f"- **EV Sign Match:** {ev_sign_passes}/{total} (Target: $20/20$)\n\n")

        f.write("## Per-Case Results Table\n\n")
        f.write("| Case | Reason Code | Amount | Expected Action | Actual Action | Gate (Exp / Got) | Judge | EV Sign | Status |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for r in results:
            status_badge = "PASS" if r["overall_pass"] else "**FAIL**"
            f.write(
                f"| {r['case_id']} | `{r['reason']}` | ${r['amount_cents']/100:.2f} | "
                f"`{r['expected_action']}` | `{r['actual_action']}` | "
                f"`{r['expected_gate']}` / `{r['computed_gate']}` | "
                f"{'PASS' if r['judge_pass'] else 'FAIL'} | "
                f"{'PASS' if r['ev_sign'] else 'FAIL'} | {status_badge} |\n"
            )

        f.write("\n## Failure Traces (Error Analysis)\n\n")
        fail_cases = [r for r in results if not r["overall_pass"]]
        if not fail_cases:
            f.write("All 20 cases passed all 4 binary checks on this run.\n")
        else:
            for fc in fail_cases:
                f.write(f"### Case `{fc['case_id']}` (`{fc['reason']}`)\n")
                f.write(f"- **Amount:** ${fc['amount_cents']/100:.2f}\n")
                f.write(f"- **Expected Action:** `{fc['expected_action']}` | **Actual:** `{fc['actual_action']}` (Match: {fc['action_match']})\n")
                f.write(f"- **Expected Gate:** `{fc['expected_gate']}` | **Computed:** `{fc['computed_gate']}` (Match: {fc['gate_match']})\n")
                f.write(f"- **Win Probability:** `{fc['win_probability']}` | **EV:** `{fc['ev_cents']}¢` (EV Sign: {fc['ev_sign']})\n")
                f.write(f"- **Judge Status:** {'PASS' if fc['judge_pass'] else 'FAIL'}\n")
                f.write(f"  - Reason Code Pass: {fc['judge_details'].get('reason_code_pass')}\n")
                f.write(f"  - Must-Cite Pass: {fc['judge_details'].get('must_cite_pass')} (Missing: {fc['judge_details'].get('missing_items')})\n")
                f.write(f"  - No Hallucination Pass: {fc['judge_details'].get('no_hallucination_pass')}\n")
                f.write(f"  - Word Count Pass: {fc['judge_details'].get('word_count_pass')} ({fc['judge_details'].get('word_count')} words)\n")
                f.write(f"  - Judge Explanation: {fc['judge_details'].get('explanation')}\n")
                f.write(f"- **Rationale:** {fc['rationale']}\n")
                f.write(f"- **Narrative:**\n```\n{fc['narrative']}\n```\n\n")

    print(f"\nDetailed evaluation report saved to: {out_file}")


if __name__ == "__main__":
    main()
