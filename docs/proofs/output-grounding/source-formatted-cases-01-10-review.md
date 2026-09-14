# Independent source review: formatted cases 01–10

Reviewed the final `supporting_output.strategy` and `supporting_output.evidence_packet` fields against each case's exact `case_facts.source_tool_records`, including narrative reason and required citations. No unsupported final factual claim or required-citation omission was identified in these ten outputs. The saved composed evaluator passes 8/10; its failures in cases 03 and 07 are false positives described below. Raw scores remain unchanged.

These are deterministic formatting and new judgments of captured `ccd5616` model drafts, processed by `ab240e1d50e08eae0b7d0e9f2c46c709f169c036`. They are not ten fresh graph generations. This review excludes the separate fresh graph integration report and does not treat `fixture_context`, original drafts, or judge explanations as authoritative source evidence.

| Case | Independent factual assessment | Saved judge |
| --- | --- | --- |
| 01 | Names, addresses, amount, UPS tracking/signature, event labels, card checks, customer metrics, and scoped empty-record statement match sources. | Pass |
| 02 | Same supported field mapping for FedEx delivery. Exact timestamps remain in narrative; physical shipping date is date-only. | Pass |
| 03 | Delayed shipment is reported as recorded; “never delivered” remains an exact communications quote. Recommendation asserts no merchant-policy requirement. | **Fail: false positive** |
| 04 | DHL tracking and recorded signature match sources; no authenticated-cardholder assertion is added. | Pass |
| 05 | UPS signature, dates, billing/shipping addresses, and card checks match sources. | Pass |
| 06 | Distinct billing and shipping addresses are preserved. Null signature is correctly described as missing from the supplied record; the alternate-address request is quoted neutrally. | Pass |
| 07 | Return policy is quoted as policy contents. Both disclosure fields remain null, and the empty communications statement is record-scoped. | **Fail: false positive** |
| 08 | Original shipment is separate from the quoted return/warehouse/refund report, including RET-88008. No independent return-delivery proof is asserted. | Pass |
| 09 | VIP status, 12 total orders, $3,400 LTV, and $500 recorded policy value match sources. Complaint is quoted; no unqualified no-return assertion or unsupported disclosure field. | Pass |
| 10 | Order creation and current refunded status are separately labeled. Refund confirmation, date, and re_prior10 reference remain a communications quote; no before-dispute ordering is invented. | Pass |

## Evaluator false positives

**Case 03, premise component:** The final narrative says “Recommendation: concede the dispute for dp_eval_03 ($65.00)” and separately reports “Recorded VIP concession limit (vip_concede_max_cents): $500.00.” The successful policy result contains `vip_concede_max_cents: 50000`; the output does not say this parameter authorizes concession for a new customer. Nevertheless, the premise explanation rejects the recommendation because “No stated policy rule supports conceding for a new customer at this amount based on non-delivery.” This evaluates whether a recommendation is mandated by merchant policy, rather than whether the output falsely attributes such a rule. The broad grounding component correctly passes.

**Case 07, broad grounding component:** The same recorded policy line is rejected as a purported customer-specific limit. The explanation acknowledges both the literal field and conversion are correct, then infers applicability to the new customer from the parameter's inclusion. The final output makes no customer-specific applicability assertion and recommends fighting. The premise component correctly states that the line “merely reports the recorded parameter value” and passes. This is an explanatory and verdict disagreement between components, not a demonstrated unsupported output claim.

## Assessment boundary and observed checks

All ten final action, `win_probability`, `expected_value_cents`, and `evidence_strength` values exactly match the original captured strategy. These remain model decisions or estimates, not newly established empirical facts. The formatter replaces factual prose while preserving those assessments; this review does not establish probability calibration or numerical-estimate accuracy. Customer tier, monetary facts, order totals, and communication counts in the final prose were checked against raw records.

Read-only local checks returned exit 0 and confirmed:

- 10/10 action, gate, EV-sign, reason, required-citation, word-count, artifact, and physical-field checks in the saved reports; 10 valid judge responses; 8 composed passes.
- All ten original source-record lists and raw generated outputs are preserved exactly. The action/assessment comparison also matches 10/10.
- Narratives contain 72–112 words. No file attachments are invented; disclosure and uploaded-file fields are null.
- Both referenced source-report hashes match. Processor and evaluator hashes match the saved processing commit.

## Provenance

Inputs are the interleaved `evals/results/2026-09-14-source-formatted-a.json`, `-b.json`, and `-c.json` reports, rubric `grounded-v17`. All ten reviewed rows were available while the larger reports continued. The SHA-256 of the ten case rows sorted by case ID and serialized as UTF-8 JSON with sorted keys, `ensure_ascii=False`, and separators `(',', ':')` is `b9ec256857799fda959c190a8e18f019f22bff9eba2727d9ce0edc0e36516a9c`; this fixes the reviewed subset independently of later appended cases.

Processor SHA-256: `2caff55c5947e80e955af8ec869c94d5594e23ad211cf0891e940f715d687b01`. Evaluator SHA-256: `eb236bd729e2609d5802ec723b90994235babc9bd7335988393b4f7c7bce18db`. Source generation reports retain their original `ccd5616` provenance and provider usage.

No provider calls, code edits, raw-report mutations, or score overrides were performed for this review. Ten source-backed outputs do not establish population-wide error rates or production behavior.
