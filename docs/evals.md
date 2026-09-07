# Decision Evals Harness (`evals/`)

The Rebuttal decision evals suite tests the autonomous multi-agent evidence and decision pipeline against a comprehensive 20-dispute synthetic golden set (`evals/cases/case_01.json` – `case_20.json`).

The suite evaluates four deterministic and LLM-assisted binary checks with zero mutating calls to Stripe:
1. **Action Match (`action_match`):** Agent selects the correct strategic action (`fight`, `concede`, or `refund_inquiry`).
2. **Gate Match (`gate_match`):** Code assertion verifying whether the dispute triggers the human-in-the-loop approval gate per `merchant_policy.yaml` thresholds (amount $\ge \$200$, uncertain win probability $0.35 \le p \le 0.65$, or non-fight actions).
3. **Narrative Judge (`judge_pass`):** LLM-as-judge binary evaluation verifying the generated Stripe evidence narrative:
   - Names or directly addresses the dispute reason code.
   - Cites every required `must_cite` evidence item (e.g., carrier tracking number, signature confirmation, customer admission/quote).
   - Hallucination check: Claims nothing absent from the fixture data (no invented signatures, tracking numbers, or quotes).
   - Word count constraint: $\le 250$ words.
4. **Expected Value Sign (`ev_sign`):** Verifies that `expected_value_cents` has the correct mathematical sign ($\ge 0$ for `fight`, $\le 0$ for `concede` and `refund_inquiry`).

---

## Failure Modes Caught by the Suite

The harness is explicitly designed to detect and prevent five core failure modes:

### 1. Fabricated Evidence (Hallucination)
- **Failure description:** The drafter agent invents recipient signatures, nonexistent carrier tracking numbers, or fake customer admissions when evidence is actually missing or weak.
- **Caught by:** Check (c) Narrative Judge rubric (`no_hallucination_pass`). The judge verifies that any claimed signature or delivery proof matches the shipment records in the case fixture.

### 2. Wrong-Reason-Code Narrative
- **Failure description:** The drafter generates generic defense text (e.g., arguing delivery proof) for a dispute filed under a different reason code (such as `credit_not_processed`, `subscription_canceled`, or `duplicate`).
- **Caught by:** Check (c) Narrative Judge rubric (`reason_code_pass`). The narrative must specifically address the legal and technical elements of the disputed reason code.

### 3. Gate Bypass
- **Failure description:** A high-value dispute ($\ge \$200$), an uncertain dispute ($0.35 \le p \le 0.65$), or a concession executes autonomously without pausing for owner approval via SMS interrupt.
- **Caught by:** Check (b) Gate Match and `tests/test_gate.py`. Evaluates deterministic policy assertions against the agent's strategy output.

### 4. Over-Conceding to New Customers
- **Failure description:** The agent concedes a dispute for a first-time or one-off customer with strong delivery proof simply because the dispute amount is low, forfeiting merchant revenue without customer lifetime value justification.
- **Caught by:** Check (a) Action Match on cases like `case_01`, `case_04`, `case_07`, `case_12`, `case_14`, and `case_20`.

### 5. Under-Fighting Strong Evidence
- **Failure description:** The agent fails to fight when clear delivery proof with recipient signature and full AVS/CVC card match exists, improperly discounting win probability.
- **Caught by:** Check (a) Action Match and win probability thresholds across strong evidence cases (`case_01`, `case_02`, `case_04`, `case_05`, `case_19`).

---

## Running the Evals

To run the full evaluation suite:
```bash
uv run python evals/run.py
```

Results and failure traces are recorded to `evals/results/<YYYY-MM-DD>.md`.
