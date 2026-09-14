# Final source review: formatted cases 01–10

Reviewed the final-v2 outputs processed by `4371ebffbb2467317477d6093e96d9f24dde9fcf`, against their exact saved tool records. No unsupported final factual claim or required-citation omission was identified in these ten cases. The saved evaluator passes 9/10; case 09 is a residual evaluator false positive. Its raw failed score remains unchanged.

This is a source review of deterministic formatting and new judgments of captured `ccd5616` drafts, not ten fresh graph generations. Original drafts, `fixture_context`, and judge explanations were not used as evidence for final factual claims. The separate fresh graph integration runs are outside this review.

| Case | Source assessment | Saved judge |
| --- | --- | --- |
| 01 | Customer/payment facts, UPS delivery, recorded signature value, dates, card checks, and scoped empty communications match sources. | Pass |
| 02 | FedEx tracking and signature value, addresses, exact event dates, customer metrics, and communication count match sources. | Pass |
| 03 | Carrier delay is recorded; “never delivered” remains an exact communications quote. No merchant concession rule or VIP limit is asserted. | Pass |
| 04 | DHL tracking and signature value are reported without adding authenticated cardholder identity. | Pass |
| 05 | UPS facts, billing/shipping addresses, payment checks, dates, and customer metrics match sources. | Pass |
| 06 | Alternate and billing addresses remain distinct. Null signature is scoped to the supplied record. The request is quoted neutrally; the policy parameter carries an explicit eligibility limitation. | Pass |
| 07 | Recorded return policy is quoted, disclosure fields remain null, and empty communications remain record-scoped. | Pass |
| 08 | Carrier shipment and quoted return/warehouse report remain distinct; RET-88008 and outstanding-refund report retain their communications basis. | Pass |
| 09 | VIP status, 12 total orders, $3,400 LTV, $195 amount, $500 policy parameter, FedEx facts, and complaint text match sources. | **Fail: false positive** |
| 10 | Order creation, current refunded status, shipment dates, and quoted re_prior10 refund confirmation retain their event and source meanings. No before-dispute claim is added. | Pass |

## Case 09 adjudication

The broad grounding component calls `strategy.rationale`'s “Recommend concede the dispute” unsupported because the source records do not explain why that action was selected over fighting. This is a proposed action, not a statement that merchant policy grants an entitlement or that concession has occurred. The output explicitly says: “Recorded policy parameter: vip_concede_max_cents=$500.00. This limit alone does not establish eligibility.” The successful `get_merchant_history_and_policy` result supplies `vip_concede_max_cents: 50000`.

The same explanation labels the policy-value line unsupported, immediately acknowledges the conversion is correct, and states that all other factual claims match. Its objection is to the justification for the selected strategy, not to an unsupported factual premise actually asserted. The independent premise component correctly passes the parameter, its eligibility limitation, and the recommendation. Reason, required citations, word limit, artifacts, and physical fields also pass. This is a residual broad-judge false positive; no score override or further tuning is part of this review.

## Verified change and assessment boundaries

The small formatter diff removes the VIP parameter for new customers, retains its literal identifier for repeat/VIP customers with an explicit limitation, and labels the mixed `signed_by` field “signature or delivery notation.” The associated test preserves the literal delivery notation while rejecting its presentation as a recorded signature. No actionable correctness regression was identified in that diff.

An offline comparison confirmed all ten saved final outputs equal the current formatter's result for their exact original source records. Relative to the previous independently reviewed formatted outputs, only `evidence_packet.narrative` changes, exactly by the policy and notation wording above. Every other final field is unchanged. Action, win probability, expected value, and evidence-strength assessments remain exactly as captured; they are model decisions/estimates, not newly verified empirical facts. Source-record lists and raw drafts also remain identical in all ten cases.

Local verification returned exit 0. Saved counts are 10/10 action, gate, EV-sign, valid-judge, reason, required-citation, word-limit, artifact, and physical-field checks; 9/10 composed passes. Narrative lengths are 68–107 words. This does not establish probability calibration, production behavior, or population-wide error rates.

## Provenance

- Reviewed reports: `evals/results/2026-09-14-source-formatted-final-v2-{a,b,c}.json`, interleaved cases, rubric `grounded-v17`. All ten reviewed rows were present while remaining cases continued.
- Sorted ten-row subset SHA-256: `5ce4c29d6bfeaece382fbcad798993649d9ce9a1f8091201158d44be642e85c6`, using UTF-8 JSON with sorted keys, `ensure_ascii=False`, and separators `(',', ':')`.
- Generation revision `ccd5616`; processing revision `4371ebffbb2467317477d6093e96d9f24dde9fcf`. Processor SHA-256 `f9af3cf8510fe9ccb4693fde049ceb8bf6aff16af5931058ac04114973a8c602`; unchanged evaluator SHA-256 `eb236bd729e2609d5802ec723b90994235babc9bd7335988393b4f7c7bce18db`. Both hashes match the processing commit; referenced source-report hashes also match.
- Earlier `source-formatted-final-{a,b,c}.json` partials contain unavailable `EndpointConnectionError` judgments. They are preserved infrastructure failures, not factual rejections. This review's scores come exclusively from final-v2.

No provider calls, code edits, raw-report edits, or Git mutations were performed by this review. Earlier reviews remain preserved separately.
