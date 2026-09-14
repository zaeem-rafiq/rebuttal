# Rebuttal Decision Evals Results — 2026-09-14

**Execution Timestamp:** 2026-09-14T13:27:31.432548+00:00
**Code Revision:** `eb83ad5`
**Source Snapshot SHA256:** `bba841de8d7c3e5dbe126d9a96e7aee02fa3f6151743bfc3bce37fa374af8875` (uncommitted source changes: True)
**Bedrock Model ID:** `us.anthropic.claude-haiku-4-5-20251001-v1:0`
**Dataset:** `evals/cases/` (20 synthetic cases)
**Total Cases:** 3

**Rubric:** grounded-v3 (grounding across all strategy and evidence fields; reason, must-cite, and word count apply to narrative only). Gate measures hook interrupt request only.

## Summary Metrics

- **Action Match:** 3/3 (Target: $\ge 18$)
- **Gate Match:** 3/3 (Target: $20/20$)
- **Output Judge Pass:** 1/3 (Target: $\ge 18$)
- **EV Sign Match:** 3/3 (Target: $20/20$)

## Per-Case Results Table

| Case | Reason Code | Amount | Expected Action | Actual Action | Gate (Exp / Got) | Judge | EV Sign | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| case_08 | `product_unacceptable` | $115.00 | `concede` | `concede` | `True` / `True` | FAIL | PASS | **FAIL** |
| case_09 | `product_unacceptable` | $195.00 | `concede` | `concede` | `True` / `True` | PASS | PASS | PASS |
| case_14 | `duplicate` | $120.00 | `fight` | `fight` | `False` / `False` | FAIL | PASS | **FAIL** |

## Failure Traces (Error Analysis)

### Case `case_08` (`product_unacceptable`)
- **Amount:** $115.00
- **Expected Action:** `concede` | **Actual:** `concede` (Match: True)
- **Expected Gate:** `True` | **Computed:** `True` (Match: True)
- **Win Probability:** `0.15` | **EV:** `0¢` (EV Sign: True)
- **Judge Status:** FAIL
  - Reason Code Pass: True
  - Must-Cite Pass: True (Missing: [])
  - No Hallucination Pass: False
  - Word Count Pass: True (148 words)
  - Judge Explanation: reason_code_pass: NARRATIVE explicitly names 'product_unacceptable' as the dispute reason and recommends concession. must_cite_pass: NARRATIVE meaningfully references all three required items: 'RET-88008' (return tracking), 'warehouse' (delivery destination), and 'return delivered' (delivery status). no_hallucination_pass: FAILED. The NARRATIVE states 'Per merchant product_unacceptable policy, customer return reports and refund claims are prioritized to resolve disputes and prevent escalation.' This claim is unsupported. The supplied merchant_policy contains no rule prioritizing product_unacceptable returns or refund claims. The policy_rules address human_approval_threshold, low_value_auto_concede, vip_repeat_concession, pre_chargeback_inquiry, silence_action, and return_policy_rule—none of which establish a prioritization rule for product_unacceptable disputes. This is an invented policy justification.
- **Rationale:** Customer reported item returned via tracking RET-88008 to warehouse on August 15, 2026, with outstanding refund complaint. Per product_unacceptable policy, customer return reports and refund claims take precedence to resolve dispute and prevent escalation.
- **Narrative:**
```
Dispute Reason: product_unacceptable

Customer James Wilson reported via message dated August 16, 2026, that he returned the Thermal Travel Mug Set using return tracking RET-88008, with the return delivered to the merchant's warehouse on August 15, 2026. The customer states that no refund has been issued as of the dispute date.

The original order (ORD-EVAL-008) was fulfilled and delivered via USPS tracking 940008 to the customer's billing address (808 Spruce Ct, Chicago, IL 60601) on August 4, 2026. All card verification checks (AVS line 1, postal code, and CVC) passed at transaction time.

The customer's communication documents a reported return delivery to the warehouse and an outstanding refund expectation. Per merchant product_unacceptable policy, customer return reports and refund claims are prioritized to resolve disputes and prevent escalation.

Recommendation: Concede dispute dp_eval_08 based on customer reported return delivery (RET-88008) to warehouse on August 15, 2026, with outstanding refund complaint.
```

- **Complete Generated Output:**
```json
{
  "strategy": {
    "action": "concede",
    "win_probability": 0.15,
    "expected_value_cents": 0,
    "customer_value": "new",
    "evidence_strength": "weak",
    "rationale": "Customer reported item returned via tracking RET-88008 to warehouse on August 15, 2026, with outstanding refund complaint. Per product_unacceptable policy, customer return reports and refund claims take precedence to resolve dispute and prevent escalation.",
    "owner_summary": "Recommend concede: Customer reported return delivery (RET-88008) to warehouse with outstanding refund. Resolves product_unacceptable dispute and addresses customer concern."
  },
  "evidence_packet": {
    "customer_name": "James Wilson",
    "customer_email_address": "j.wilson@example.com",
    "billing_address": "808 Spruce Ct, Chicago, IL 60601, United States",
    "shipping_address": "808 Spruce Ct, Chicago, IL 60601, United States",
    "shipping_carrier": "USPS",
    "shipping_tracking_number": "940008",
    "shipping_date": "2026-08-01",
    "shipping_documentation": null,
    "service_documentation": null,
    "customer_communication": null,
    "refund_policy_disclosure": null,
    "cancellation_policy_disclosure": null,
    "uncategorized_text": null,
    "uncategorized_file": null,
    "narrative": "Dispute Reason: product_unacceptable\n\nCustomer James Wilson reported via message dated August 16, 2026, that he returned the Thermal Travel Mug Set using return tracking RET-88008, with the return delivered to the merchant's warehouse on August 15, 2026. The customer states that no refund has been issued as of the dispute date.\n\nThe original order (ORD-EVAL-008) was fulfilled and delivered via USPS tracking 940008 to the customer's billing address (808 Spruce Ct, Chicago, IL 60601) on August 4, 2026. All card verification checks (AVS line 1, postal code, and CVC) passed at transaction time.\n\nThe customer's communication documents a reported return delivery to the warehouse and an outstanding refund expectation. Per merchant product_unacceptable policy, customer return reports and refund claims are prioritized to resolve disputes and prevent escalation.\n\nRecommendation: Concede dispute dp_eval_08 based on customer reported return delivery (RET-88008) to warehouse on August 15, 2026, with outstanding refund complaint.",
    "files": []
  }
}
```

### Case `case_14` (`duplicate`)
- **Amount:** $120.00
- **Expected Action:** `fight` | **Actual:** `fight` (Match: True)
- **Expected Gate:** `False` | **Computed:** `False` (Match: True)
- **Win Probability:** `0.85` | **EV:** `10200¢` (EV Sign: True)
- **Judge Status:** FAIL
  - Reason Code Pass: True
  - Must-Cite Pass: False (Missing: [])
  - No Hallucination Pass: True
  - Word Count Pass: True (95 words)
  - Judge Explanation: reason_code_pass: TRUE. The narrative explicitly names 'duplicate' as the dispute reason in the opening sentence. must_cite_pass: FALSE. The required items are ['ORD-14A', 'ORD-14B', 'distinct items']. The narrative cites 'distinct items' and references 'ORD-14A' and 'ORD-14B' only indirectly through the quoted customer communication ('ORD-14A and ORD-14B contained distinct items ordered separately'), but does not independently name these order IDs outside the quotation. The facts show metadata 'related_orders: ORD-14A,ORD-14B' and the communication body states the comparison, but the narrative does not directly cite ORD-14A and ORD-14B as standalone factual references—only as part of the attributed message. This fails the requirement to 'meaningfully reference' these items. no_hallucination_pass: TRUE. All factual claims in the narrative are supported: card checks passed (charge.card_checks), order delivered (shipment.status, shipment.delivered_at), recipient signature from M. Reid (shipment.signed_by), billing address match (order.billing_address and shipment.shipping_address match), communication dated August 10, 2026 (communications[0].created_at), and the quoted message content (communications[0].body). Strategy assessments (win_probability 0.85, expected_value_cents 10200, evidence_strength 'strong') are labeled as assessments and not contradicted by facts.
- **Rationale:** Records confirm separate orders contained distinct items ordered separately. Customer communication documents that ORD-14A and ORD-14B were distinct transactions. Card verification passed all checks. Package delivered to verified billing address with recipient signature.
- **Narrative:**
```
Dispute Reason: duplicate

The merchant disputes this duplicate charge claim. Card verification checks (AVS address line 1, postal code, and CVC) all passed. Order ORD-EVAL-014 for a Leather Laptop Briefcase was delivered via UPS tracking 1Z99914 on August 13, 2026, to 150 Poplar Ave, Indianapolis, IN 46201, with recipient signature from M. Reid matching the cardholder. Customer communication dated August 10, 2026, documents an Order receipt message: "Comparison shows ORD-14A and ORD-14B contained distinct items ordered separately," confirming that the related orders were separate legitimate transactions with distinct items. Recommendation: Submit evidence to contest dispute.
```

- **Complete Generated Output:**
```json
{
  "strategy": {
    "action": "fight",
    "win_probability": 0.85,
    "expected_value_cents": 10200,
    "customer_value": "new",
    "evidence_strength": "strong",
    "rationale": "Records confirm separate orders contained distinct items ordered separately. Customer communication documents that ORD-14A and ORD-14B were distinct transactions. Card verification passed all checks. Package delivered to verified billing address with recipient signature.",
    "owner_summary": "Recommend fighting duplicate dispute. Records confirm ORD-14A and ORD-14B contained distinct items ordered separately per customer communication. Delivery confirmed to verified address with signature."
  },
  "evidence_packet": {
    "customer_name": "Marcus Reid",
    "customer_email_address": "m.reid@example.com",
    "billing_address": "150 Poplar Ave, Indianapolis, IN 46201, US",
    "shipping_address": "150 Poplar Ave, Indianapolis, IN 46201, US",
    "shipping_carrier": "UPS",
    "shipping_tracking_number": "1Z99914",
    "shipping_date": "2026-08-10",
    "shipping_documentation": null,
    "service_documentation": null,
    "customer_communication": null,
    "refund_policy_disclosure": null,
    "cancellation_policy_disclosure": null,
    "uncategorized_text": null,
    "uncategorized_file": null,
    "narrative": "Dispute Reason: duplicate\n\nThe merchant disputes this duplicate charge claim. Card verification checks (AVS address line 1, postal code, and CVC) all passed. Order ORD-EVAL-014 for a Leather Laptop Briefcase was delivered via UPS tracking 1Z99914 on August 13, 2026, to 150 Poplar Ave, Indianapolis, IN 46201, with recipient signature from M. Reid matching the cardholder. Customer communication dated August 10, 2026, documents an Order receipt message: \"Comparison shows ORD-14A and ORD-14B contained distinct items ordered separately,\" confirming that the related orders were separate legitimate transactions with distinct items. Recommendation: Submit evidence to contest dispute.",
    "files": []
  }
}
```
