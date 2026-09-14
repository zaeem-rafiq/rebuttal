# Rebuttal Decision Evals Results — 2026-09-14

**Execution Timestamp:** 2026-09-14T17:47:59.061006+00:00
**Code Revision:** `ab240e1`
**Source Snapshot SHA256:** `e0afc8daae48af59cace0569f41e480049232e59817fa088e96d791a883a09bc` (uncommitted source changes: False)
**Bedrock Model ID:** `us.anthropic.claude-sonnet-4-5-20250929-v1:0`
**Dataset:** `evals/cases/` (20 synthetic cases)
**Total Cases:** 2

**Rubric:** grounded-v17 (grounding across all strategy and evidence fields; reason, must-cite, and word count apply to narrative only). Gate measures hook interrupt request only.

## Summary Metrics

- **Action Match:** 2/2 (Target: $\ge 18$)
- **Gate Match:** 2/2 (Target: $20/20$)
- **Output Judge Pass:** 2/2 (Target: $\ge 18$)
- **EV Sign Match:** 2/2 (Target: $20/20$)

## Per-Case Results Table

| Case | Reason Code | Amount | Expected Action | Actual Action | Gate (Exp / Got) | Judge | EV Sign | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| case_11 | `credit_not_processed` | $130.00 | `concede` | `concede` | `True` / `True` | PASS | PASS | PASS |
| case_13 | `subscription_canceled` | $89.00 | `concede` | `concede` | `True` / `True` | PASS | PASS | PASS |

## Failure Traces (Error Analysis)

All 2 cases passed all 4 binary checks on this run.
