# Rebuttal Decision Evals Results — 2026-09-14

**Execution Timestamp:** 2026-09-14T09:35:14.012108+00:00
**Code Revision:** `4dbb5e1`
**Bedrock Model ID:** `us.anthropic.claude-haiku-4-5-20251001-v1:0`
**Dataset:** `evals/cases/` (20 synthetic cases)
**Total Cases:** 20

**Rubric:** grounded-v2 (reconciled evidence flow, currency & timestamp equivalence, prospective action framing). Gate measures hook interrupt request only.

## Summary Metrics

- **Action Match:** 20/20 (Target: $\ge 18$)
- **Gate Match:** 20/20 (Target: $20/20$)
- **Narrative Judge Pass:** 17/20 (Target: $\ge 18$)
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
| case_08 | `product_unacceptable` | $115.00 | `concede` | `concede` | `True` / `True` | FAIL | PASS | **FAIL** |
| case_09 | `product_unacceptable` | $195.00 | `concede` | `concede` | `True` / `True` | PASS | PASS | PASS |
| case_10 | `credit_not_processed` | $99.00 | `fight` | `fight` | `False` / `False` | PASS | PASS | PASS |
| case_11 | `credit_not_processed` | $130.00 | `concede` | `concede` | `True` / `True` | PASS | PASS | PASS |
| case_12 | `subscription_canceled` | $49.00 | `fight` | `fight` | `False` / `False` | PASS | PASS | PASS |
| case_13 | `subscription_canceled` | $89.00 | `concede` | `concede` | `True` / `True` | PASS | PASS | PASS |
| case_14 | `duplicate` | $120.00 | `fight` | `fight` | `False` / `False` | PASS | PASS | PASS |
| case_15 | `duplicate` | $60.00 | `concede` | `concede` | `True` / `True` | FAIL | PASS | **FAIL** |
| case_16 | `inquiry` | $129.00 | `refund_inquiry` | `refund_inquiry` | `True` / `True` | PASS | PASS | PASS |
| case_17 | `inquiry` | $75.00 | `refund_inquiry` | `refund_inquiry` | `True` / `True` | PASS | PASS | PASS |
| case_18 | `product_not_received` | $450.00 | `concede` | `concede` | `True` / `True` | PASS | PASS | PASS |
| case_19 | `fraudulent` | $550.00 | `fight` | `fight` | `True` / `True` | FAIL | PASS | **FAIL** |
| case_20 | `product_not_received` | $45.00 | `fight` | `fight` | `False` / `False` | PASS | PASS | PASS |

## Failure Traces (Error Analysis)

### Case `case_08` (`product_unacceptable`)
- **Amount:** $115.00
- **Expected Action:** `concede` | **Actual:** `concede` (Match: True)
- **Expected Gate:** `True` | **Computed:** `True` (Match: True)
- **Win Probability:** `0.15` | **EV:** `0¢` (EV Sign: True)
- **Judge Status:** FAIL
  - Reason Code Pass: True
  - Must-Cite Pass: True (Missing: ['return delivered'])
  - No Hallucination Pass: False
  - Word Count Pass: True (70 words)
  - Judge Explanation: The narrative explicitly names 'product_unacceptable' and cites all required evidence items (RET-88008, warehouse, return delivered). However, it contains an unsupported factual claim: 'Merchant return policy requires refund processing upon return delivery to warehouse' is not stated in the case facts. The actual policy states '30-day return policy; customer must initiate return through merchant support prior to dispute'—it does not specify automatic refund timing upon warehouse receipt. This is a hallucination of policy terms not present in CASE FACTS SUMMARY.
- **Rationale:** Customer reported returning item to warehouse via RET-88008 with delivery confirmed Aug 15, 2026, but refund was not processed. Merchant operational failure to complete refund after return receipt warrants concession to resolve dispute and process pending refund.
- **Narrative:**
```
Dispute Reason: product_unacceptable

Customer James Wilson reports return RET-88008 delivered to merchant warehouse on August 15, 2026, with communication dated August 16, 2026 indicating no refund was processed. Customer communication documents the return delivery; however, refund processing was not completed following return receipt. Merchant return policy requires refund processing upon return delivery to warehouse.

Recommendation: Concede dispute dp_eval_08 based on customer's reported return delivery to warehouse without subsequent refund processing.
```

### Case `case_15` (`duplicate`)
- **Amount:** $60.00
- **Expected Action:** `concede` | **Actual:** `concede` (Match: True)
- **Expected Gate:** `True` | **Computed:** `True` (Match: True)
- **Win Probability:** `0.1` | **EV:** `0¢` (EV Sign: True)
- **Judge Status:** FAIL
  - Reason Code Pass: True
  - Must-Cite Pass: True (Missing: [])
  - No Hallucination Pass: False
  - Word Count Pass: True (78 words)
  - Judge Explanation: The narrative explicitly cites 'duplicate' reason and all three required evidence items ('double charge', 'identical', 'single shipment'). However, it contains a critical factual error: it states 'Transaction records confirm a single charge exists for this order,' which contradicts the case facts showing two charges occurred 2 seconds apart (as reported in customer communication). The narrative also recommends concession but falsely implies the merchant's payment records corroborate a second charge when the case facts do not provide merchant charge records showing two distinct transactions—only the customer's report of the double charge.
- **Rationale:** Customer reported double charge for identical items with single shipment fulfilled. Records confirm a single shipment was delivered. Payment processing error appears to have generated duplicate authorization/charge. Conceding resolves duplicate charge dispute and customer concern.
- **Narrative:**
```
Dispute Reason: duplicate

Customer communication dated August 8, 2026 reports a 'double charge' for 'identical items' with only a 'single shipment' fulfilled. Carrier records confirm USPS tracking #940015 shows a single shipment delivered to the confirmed address on August 11, 2026. Order records show one order (ORD-EVAL-015) created August 1, 2026 for $60.00. Transaction records confirm a single charge exists for this order. Recommendation: Concede dispute based on customer reported double charge for identical items with single shipment.
```

### Case `case_19` (`fraudulent`)
- **Amount:** $550.00
- **Expected Action:** `fight` | **Actual:** `fight` (Match: True)
- **Expected Gate:** `True` | **Computed:** `True` (Match: True)
- **Win Probability:** `0.85` | **EV:** `43950¢` (EV Sign: True)
- **Judge Status:** FAIL
  - Reason Code Pass: False
  - Must-Cite Pass: True (Missing: [])
  - No Hallucination Pass: True
  - Word Count Pass: True (91 words)
  - Judge Explanation: The narrative fails to explicitly name, address, defend against, or state concession for the dispute reason code 'fraudulent'—it only states 'Dispute Reason: fraudulent' as a header but provides no substantive defense or acknowledgment of the fraudulent claim itself. All three required evidence items (1Z99919, S. Jenkins, AVS) are properly cited and factually grounded.
- **Rationale:** Card verification passed (AVS address line 1, postal code, CVC all match). UPS tracking confirms delivery with recipient signature "S. Jenkins" matching cardholder name to billing address on August 18, 2026. No unverified alternate address. Strong evidence supports legitimate transaction and delivery.
- **Narrative:**
```
Dispute Reason: fraudulent

The merchant disputes this claim. Card verification checks confirm AVS address line 1 match, postal code match, and CVC check all passed at time of authorization. Order ORD-EVAL-019 for Professional Drone 4K ($550.00) was fulfilled and shipped via UPS tracking 1Z99919 on August 15, 2026. Carrier records confirm delivery on August 18, 2026 at 14:30:00 UTC to 200 Walnut Ave, Dallas, TX 75201. Recipient signature "S. Jenkins" matches cardholder Samuel Jenkins. Billing address on file matches delivery address and matches card verification records. Evidence submitted to contest dispute.
```

