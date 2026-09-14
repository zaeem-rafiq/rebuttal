# Rebuttal Decision Evals Results — 2026-09-14

**Execution Timestamp:** 2026-09-14T08:31:33.053066+00:00
**Code Revision:** `ae68a80`
**Bedrock Model ID:** `us.anthropic.claude-haiku-4-5-20251001-v1:0`
**Dataset:** `evals/cases/` (20 synthetic cases)
**Total Cases:** 20

**Rubric:** grounded-v2 (reconciled evidence flow, currency & timestamp equivalence, prospective action framing). Gate measures hook interrupt request only.

## Summary Metrics

- **Action Match:** 20/20 (Target: $\ge 18$)
- **Gate Match:** 20/20 (Target: $20/20$)
- **Narrative Judge Pass:** 19/20 (Target: $\ge 18$)
- **EV Sign Match:** 20/20 (Target: $20/20$)

## Per-Case Results Table

| Case | Reason Code | Amount | Expected Action | Actual Action | Gate (Exp / Got) | Judge | EV Sign | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| case_01 | `product_not_received` | $75.00 | `fight` | `fight` | `False` / `False` | PASS | PASS | PASS |
| case_02 | `product_not_received` | $280.00 | `fight` | `fight` | `True` / `True` | PASS | PASS | PASS |
| case_03 | `product_not_received` | $65.00 | `concede` | `concede` | `True` / `True` | PASS | PASS | PASS |
| case_04 | `fraudulent` | $140.00 | `fight` | `fight` | `False` / `False` | PASS | PASS | PASS |
| case_05 | `fraudulent` | $350.00 | `fight` | `fight` | `True` / `True` | PASS | PASS | PASS |
| case_06 | `fraudulent` | $220.00 | `concede` | `concede` | `True` / `True` | PASS | PASS | PASS |
| case_07 | `product_unacceptable` | $89.00 | `fight` | `fight` | `False` / `False` | PASS | PASS | PASS |
| case_08 | `product_unacceptable` | $115.00 | `concede` | `concede` | `True` / `True` | PASS | PASS | PASS |
| case_09 | `product_unacceptable` | $195.00 | `concede` | `concede` | `True` / `True` | PASS | PASS | PASS |
| case_10 | `credit_not_processed` | $99.00 | `fight` | `fight` | `False` / `False` | PASS | PASS | PASS |
| case_11 | `credit_not_processed` | $130.00 | `concede` | `concede` | `True` / `True` | PASS | PASS | PASS |
| case_12 | `subscription_canceled` | $49.00 | `fight` | `fight` | `False` / `False` | PASS | PASS | PASS |
| case_13 | `subscription_canceled` | $89.00 | `concede` | `concede` | `True` / `True` | PASS | PASS | PASS |
| case_14 | `duplicate` | $120.00 | `fight` | `fight` | `False` / `False` | PASS | PASS | PASS |
| case_15 | `duplicate` | $60.00 | `concede` | `concede` | `True` / `True` | PASS | PASS | PASS |
| case_16 | `inquiry` | $129.00 | `refund_inquiry` | `refund_inquiry` | `True` / `True` | PASS | PASS | PASS |
| case_17 | `inquiry` | $75.00 | `refund_inquiry` | `refund_inquiry` | `True` / `True` | PASS | PASS | PASS |
| case_18 | `product_not_received` | $450.00 | `concede` | `concede` | `True` / `True` | PASS | PASS | PASS |
| case_19 | `fraudulent` | $550.00 | `fight` | `fight` | `True` / `True` | PASS | PASS | PASS |
| case_20 | `product_not_received` | $45.00 | `fight` | `fight` | `False` / `False` | FAIL | PASS | **FAIL** |

## Failure Traces (Error Analysis)

### Case `case_20` (`product_not_received`)
- **Amount:** $45.00
- **Expected Action:** `fight` | **Actual:** `fight` (Match: True)
- **Expected Gate:** `False` | **Computed:** `False` (Match: True)
- **Win Probability:** `0.85` | **EV:** `3825¢` (EV Sign: True)
- **Judge Status:** FAIL
  - Reason Code Pass: True
  - Must-Cite Pass: True (Missing: [])
  - No Hallucination Pass: False
  - Word Count Pass: True (74 words)
  - Judge Explanation: The narrative explicitly names 'product_not_received' and cites all required evidence items (940020, delivered, USPS). However, it contains an unsupported factual claim: 'The merchant disputes this claim' is not grounded in case facts, which show no merchant communication or dispute response in the communications array.
- **Rationale:** USPS tracking #940020 confirms delivery to customer's verified address on August 19, 2026. Delivery confirmation shows package delivered to mailbox at 210 Beech St, Minneapolis—matching billing address with passed AVS/CVC verification. Strong carrier evidence directly rebuts product-not-received claim.
- **Narrative:**
```
Dispute Reason: product_not_received

Carrier records confirm USPS tracking 940020 delivered to mailbox on August 19, 2026. The merchant disputes this claim. Order ORD-EVAL-020 was shipped on August 16, 2026 and delivered on August 19, 2026 to the customer's verified address (210 Beech St, Minneapolis, MN 55401). All card security checks passed: AVS address line 1 match, postal code match, and CVC verification confirmed. Tracking shows delivery confirmed in mailbox. Evidence submitted to contest dispute.
```

