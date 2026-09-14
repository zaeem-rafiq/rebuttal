# Independent review: ccd5616 raw cases 01–10

Reviewed every generated factual field in `supporting_output.strategy` and `supporting_output.evidence_packet`, plus each narrative's reason and required citations, against the corresponding `case_facts.source_tool_records`. `fixture_context` and judge explanations were not treated as evidence. This review covers original model drafts, before the subsequent deterministic factual formatter; it does not establish the formatter's final judged result.

The saved run has 10/10 action matches, gate matches, EV-sign matches, valid judge responses, reason checks, citation checks, and word-count checks. Its composed judge passes 8/10. Manual review identifies factual defects in cases 06, 07, and 09: case 06 is a false-negative pass, while the failures in 07 and 09 are supported. No required-citation omission or false-positive case rejection was identified in this subset.

| Case | Independent factual assessment | Saved judge |
| --- | --- | --- |
| 01 | No discrepancy identified; carrier details and record-scoped absence statement are supported. | Pass |
| 02 | No discrepancy identified; payment reference, delivery, and recorded signature are supported. | Pass |
| 03 | No discrepancy identified; delayed/never-delivered wording has an explicit carrier-event basis. No invented merchant concession policy. | Pass |
| 04 | No discrepancy identified; recorded signature is not presented as authenticated cardholder identity. | Pass |
| 05 | No discrepancy identified; billing/shipping addresses, card checks, and event dates are supported. | Pass |
| 06 | Unsupported absence-of-signature claim in both strategy text fields. Narrative correctly scopes the missing record. | **Pass: false negative** |
| 07 | Policy text placed in a disclosure-evidence field without evidence of customer exposure. | Fail: correct |
| 08 | No discrepancy identified; return/warehouse assertions retain their communications-record basis. | Pass |
| 09 | Same unsupported disclosure-field population as 07. VIP status, 12 total orders, $3,400 LTV, and recorded threshold are supported. | Fail: correct |
| 10 | No discrepancy identified; refund reference and communication date are supported, with no invented ordering relative to dispute creation. | Pass |

## Concrete defects and component behavior

**Case 06:** `strategy.rationale` says, “FedEx tracking confirms delivery to the alternate address on 2026-08-17 without signature.” `strategy.owner_summary` says, “Delivery confirmed to alternate address without signature.” The successful `get_shipping_evidence` result has `signed_by: null`; its events record shipment and delivery, without an explicit statement that no signature was obtained. This supports the narrative's “No signature recorded (signed_by: null),” not the two unqualified strategy claims. Both the broad grounding judgment and premise judgment pass, overlooking the stronger claims outside the narrative.

**Cases 07 and 09:** `evidence_packet.refund_policy_disclosure` contains “30-day return policy; customer must initiate return through merchant support prior to dispute”. The successful `get_merchant_history_and_policy` result supplies exactly this policy text, but no record of how or when it was disclosed to the customer. Copying the text into a field whose contract requires disclosure evidence is unsupported. The premise component rejects both cases. The broad grounding component misses case 07 and correctly rejects case 09.

Some passing explanations contain inaccurate evidence pointers: case 05's broad explanation locates its billing address in charge context, although it is supplied by order evidence. Premise explanations for cases 02 and 04 discuss an order date absent from their generated output. Those explanation defects did not change the supported verdicts; they limit how much explanatory accuracy can be inferred from a passing score.

## Provenance and limits

- Input: `evals/results/2026-09-14-ccd5616-a.json`, completed, 10 cases; SHA-256 `3a8176fc40d7c9273d26d33ec7640bddb1dce7ee190a9c5a9feab533a2972c83`.
- Generation revision `ccd5616`, clean source snapshot `fb6c7607596830a59e6e979faeacc4554fcd52b133db84fcbf82818e05502114`; all 35 saved manifest entries matched that Git revision in a read-only hash check.
- Generation and judge: `us.anthropic.claude-sonnet-4-5-20250929-v1:0`; generation streaming disabled; saved rubric `grounded-v15`.
- Review used local saved records only, with no provider calls and no modifications to raw scores or reports. No claim about population-wide false-positive or false-negative rates follows from this subset.
