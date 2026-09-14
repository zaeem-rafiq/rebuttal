# Source review: final formatted cases 11–20

Status: COMPLETE for this source review. All ten formatted replay outputs and fresh whole-graph cases 11 and 13 are reviewed. This is not a claim that evaluator calibration or the overall project is complete.

This review is separate from `ccd5616-cases-11-20-review.md`, which documents the original model drafts and their defects. The replay in `evals/results/2026-09-14-source-formatted-{a,b,c}.json` applies final formatting at revision `ab240e1d50e08eae0b7d0e9f2c46c709f169c036` to captured generation from `ccd5616`, then obtains new judgments using rubric `grounded-v17`. It is not a new twenty-case model generation. The separate `evals/results/2026-09-14-source-formatted-live.json` exercises fresh whole-graph generation, final formatting, and judgment at `ab240e1`.

The processor hash (`2caff55c5947e80e955af8ec869c94d5594e23ad211cf0891e940f715d687b01`) and evaluator hash (`eb236bd729e2609d5802ec723b90994235babc9bd7335988393b4f7c7bce18db`) match their Git blobs at the processing revision. Both recorded source-report hashes match the preserved `ccd5616` source reports. Every replay case 11–20 has `case_facts` exactly equal to its original captured source snapshot. The live report's complete recorded source manifest matches `ab240e1`; it records `source_dirty: false`.

All four reports are now `completed: true`. Final SHA-256 values:

- Replay a: `d36986301d671b99ace9718a817e82f4aeac4be4a29f8a9e9fd8b10dd1c10160`.
- Replay b: `c7ec93bbfe77426b6467e0f7d6c978ed7fff06610c31f1c4565019110bb82c88`.
- Replay c: `7c22c0fbd9b985c32a554bbd585b49c5e035703e02e93b80471d18f51cde0431`.
- Fresh whole graph: `10ce04fe9807e8ac365a7e20057f0d43c2da92c15f96d58946918dd167fdfbad`.

Every factual strategy and evidence-packet field is compared with captured `case_facts.source_tool_records`. Required narrative citations are checked separately. Internal numeric assessments and selected actions remain model assessments; this source review does not validate probability calibration, customer outcomes, or live Stripe submission. Raw model drafts, earlier judgments, and current raw judgments are preserved.

## Replay results and common checks

For reviewed cases 11–20, saved judge outcomes are 8/10 pass with 10/10 valid judgments. Cases 14 and 18 are evaluator false positives detailed below. All ten required-citation sets are present in final narratives. Their observed word counts are 72–98, matching an independent `len(narrative.split())` check and below the 250-word ceiling. No source value fabrication or unsupported event chronology is observed. A mixed signature/delivery-notation label remains an output clarity issue detailed below.

Across every final packet, identity/email and billing address match the order record. Physical shipment fields match carrier records, shipping dates use YYYY-MM-DD, digital products leave those physical fields null, and all file-reference/policy-disclosure fields are null with empty `files`. Every strategy summary uses the recorded status, amount, tier, order/LTV values, and message count. Recommendations remain prospective. Record-domain absence statements do not claim unobserved events never happened. Every communication appears as an intact source quote with its own timestamp and subject; no new sender identity, guaranteed consequence, or pre-purchase disclosure is inferred. Raw model drafts and original judgments remain separately available in each replay result.

## Replay case 11

Saved judge: PASS. The final output matches the separately reviewed fresh whole-graph case 11 below. Policy disclosures are null, and the August 7 support promise with `MSG-11` is quoted accurately. The earlier unsupported refund-policy disclosure is absent. Both required narrative citations are present. No further factual defect observed.

## Replay case 12

Saved judge: PASS. Thomas Evans, new tier, two total orders, $98 LTV, $49 disputed amount, order creation on August 1, and all three passing card checks match the captured sources. Digital access dispatch/delivery remains September 1 access data. The September 5 message is quoted intact, including its reported four-day interval after renewal and prior agreement to subscription terms. All three narrative citations are present. Physical shipping and policy-disclosure fields remain null. The renewal chronology is not promoted from a message report into independently recorded fact. See the common signature-label clarification below.

## Replay case 13

Saved judge: PASS. Lisa Montgomery, new tier, one order, $89 LTV/amount, order creation, access reference `DIGITAL-13`, access dispatch/delivery on September 1, and the August 28 cancellation message all match their exact sources. The earlier assertion that a digital delivery record proved renewal at midnight is absent. Renewal appears only in the accurately quoted message, so August 28, before renewal, and cancellation request remain cited without invented event timing. Physical shipping and disclosure fields are null. See the common signature-label clarification below.

## Replay case 14

Saved judge: FAIL. Independent review: evaluator false positive; no unsupported policy applicability is asserted.

The broad judge fails `Recorded VIP concession limit (vip_concede_max_cents): $500.00` because the customer is new. This sentence reports a value from source record 5 (`policy.vip_concede_max_cents: 50000`), and the final recommendation is to submit evidence, not to concede under that rule. The output neither says this customer is VIP nor claims that the parameter authorizes a concession. The premise judge correctly passes the same sentence as factual reporting. The broad judge's invented applicability implication is the sole saved substantive failure.

Marcus Reid's identity, new tier, two total orders, $240 LTV, $120 disputed amount, UPS `1Z99914`, August 10 shipping, August 13 delivery, `M. Reid` signature, and card-check values match records. The neutral receipt comparison is quoted as a communications record, preserving required `ORD-14A`, `ORD-14B`, and distinct-items references without inventing customer authorship. Raw failure is preserved.

## Replay case 15

Saved judge: PASS. Hannah Abbott's identity, new tier, one order, $60 LTV/amount, USPS `940015`, August 8 shipping, August 11 delivery, and card checks match sources. Null `signed_by` becomes only `No signature is recorded in the supplied delivery record`, not an assertion that no signature was obtained. The August 8 message supplies the required double-charge, identical-items, and single-shipment references as an intact attributed report. No independent second-charge or total-shipment claim is introduced.

## Replay case 16

Saved judge: PASS. Roberto Alvarez's identity, new tier, one order, $129 amount/LTV, inquiry status, and August 1 order/access dates match sources. The communication's reported earlier cancellation and proposed $15 fee avoidance stay inside its exact quote; no independent cancellation event or guaranteed saving is asserted. Required inquiry, cancellation, and $15 fee references are present. Physical shipping fields are null. See the common signature-label clarification below.

## Replay case 17

Saved judge: PASS. Patricia Hall's identity, repeat tier, four orders, $320 LTV, $75 inquiry amount, USPS `940017`, August 5 shipping, and August 8 delivery match records. The earlier owner-summary claim of delivery `without signature` is gone. The final narrative says only that no signature is recorded in the supplied delivery record, accurately reflecting null `signed_by`. The August 9 pause/fee message is quoted without treating either its pause report or expected fee saving as independently verified. Required inquiry and $15 fee citations remain present.

## Replay case 18

Saved judge: FAIL. Independent review: evaluator false positive; the narrative does not assert a policy-based authorization.

The premise judge interprets the separately reported `Recorded VIP concession limit (vip_concede_max_cents): $500.00` as a claim that policy permits this concession, then says the parameter cannot apply to repeat customers. The final output merely states the configured value and a recommendation; it does not assert that this rule applies. The action itself is excluded from factual-prose judgment. Broad grounding correctly passes all factual claims. The failure therefore rests on a policy applicability claim the final output never makes, irrespective of the system's business decision rule for repeat customers.

Jessica Lee's repeat tier, five total orders, $1,200 LTV, $450 disputed amount, $500 recorded threshold, FedEx `794918`, August 10 shipping, August 13 delivery at 13:00 UTC, `J. Lee` signature, and card checks match sources. Empty communications support the explicitly record-scoped absence statement. Required repeat, LTV, and `vip_concede_max_cents` citations are present. Raw failure is preserved.

## Replay case 19

Saved judge: PASS. Samuel Jenkins's identity, new tier, one order, $550 LTV/amount, UPS `1Z99919`, August 15 shipping, August 18 delivery at 14:30 UTC, recorded `S. Jenkins` signature, and AVS/CVC values match sources. The narrative does not equate a recorded signature or passing checks with verified cardholder identity or payment authorization. Required tracking, signature, and AVS citations are present. Communication absence remains limited to merchant records.

## Replay case 20

Saved judge: PASS with a valid response, unlike the previous draft run's invalid premise response. Olivia Moore's identity, new tier, one order, $45 LTV/amount, USPS `940020`, August 16 shipping, August 19 delivery at 11:00 UTC, and card checks match sources. All required USPS, tracking, and delivered references are present. Communication absence remains record-scoped. The source's `Delivered in Mailbox` value is preserved; the signature-label clarification below applies.

The saved premise explanation contains self-contradictory arithmetic about 50000 cents even though its final verdict passes. The actual conversion is correct: 50000 cents equals $500. This explanation defect is evidence that a passing verdict alone does not make judge reasoning reliable.

## Signature/delivery-notation label clarification

The formatter renders every non-null legacy `signed_by` value as `recorded signature`. This produces `recorded signature: Digital Delivery` in cases 12/13, `recorded signature: Digital` in case 16, and `recorded signature: Delivered in Mailbox` in case 20. The values are accurately copied and are not represented as a named person's verified identity, but the label can suggest signature evidence when the source contains only a delivery notation. A neutral label such as `recorded signature or delivery notation` preserves this mixed field's semantics without classifying its contents. This bounded wording concern was reported to the root agent; it is distinct from the eliminated invented values/chronology and from the policy-related judge false positives.

## Fresh whole-graph case 11

Saved judge: PASS with `judge_valid: true`. Independent review: no concrete factual defect or required-citation omission observed in final `supporting_output`.

The final policy-disclosure fields are null, fixing the original model draft's unsupported disclosure claim. The narrative directly quotes the August 7 support promise and its subject `Support Ticket MSG-11`; both required citations, `MSG-11` and promised refund, are present. It attributes that text to a communications record without inventing sender identity, refund completion, or pre-purchase policy disclosure.

Kelly Zhang's name/email, Atlanta billing and carrier address, order `ORD-EVAL-011`, order creation on August 1, fulfilled status, $130 amount, FedEx tracking `794911`, shipping on August 2, delivery on August 5 at 15:00 UTC, and recorded signature `K. Zhang` match the fresh captured records. The physical `shipping_date` is correctly formatted as `2026-08-02`. Card-check values, new customer tier, one total order, $130 LTV, one communications record, and recorded $500 VIP concession limit match their sources. The displayed limit is a recorded policy value, not a claim that this customer is VIP or that the limit authorizes the proposed action. Rationale and owner summary give a prospective recommendation and directly recorded status/customer facts. All file-reference fields are null and `files` is empty.

The live report separately retains `raw_generated_output`. This review concerns the final source-derived output actually returned by the graph; it does not relabel raw model prose as grounded.

## Fresh whole-graph case 13

Saved judge: PASS with `judge_valid: true`. Its final `supporting_output` is identical to replay case 13. Fresh source records were independently inspected: Lisa Montgomery, the $89 amount, August 1 order creation, September 1 digital access records, and August 28 cancellation message all agree with the final text. This observed graph run confirms that final formatting executes after new model generation and removes the earlier delivery-to-renewal assertion. Digital physical-shipping fields and policy disclosures remain null. Required citations are present. The same mixed signature/delivery-notation label clarification applies.

The fresh report is complete with both selected cases passing valid judgments, and separately retains each `raw_generated_output`. It proves two selected fresh graph flows, not a new twenty-case generation or live financial submission.

## Review evidence and limits

This review used local read-only report/record comparison and Git-blob/hash verification; no provider calls, code modifications, score overrides, or raw-report changes were performed. Only this review document was written. The replay's two saved failures remain failures in raw accounting. Recommendations, model probabilities, and expected values were retained from prior generation and are not independently calibrated by deterministic formatting. Evaluator false-positive controls and any subsequent wording revision require their own recorded evidence.
