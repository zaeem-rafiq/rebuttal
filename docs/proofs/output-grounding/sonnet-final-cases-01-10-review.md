# Independent source review: initial final-candidate Sonnet cases 01–10

The first ten captured cases contain three factual defects: unsupported merchant-policy attribution in case 03, an inference of no signature from a null value in case 06, and an order date assigned to a charge in case 10. No required narrative reason or citation omission was found. The composed evaluator also has four false-positive case failures, two false-negative passes, and one failure for the wrong reason. Raw results have not been changed.

This is a review of the initial final-candidate generation, not verification of a later repaired generator or the complete benchmark. The report was still running (`completed: false`) when all ten reviewed cases were available.

## Evidence and method

- Source report: `evals/results/2026-09-14-sonnet-final.json`, cases `case_01` through `case_10` only.
- Generation revision: `45772c9`; generation and judge model: `us.anthropic.claude-sonnet-4-5-20250929-v1:0`; generation streaming: `false`; recorded rubric: `grounded-v12`.
- All 35 recorded source-manifest hashes matched file contents at revision `45772c9`, checked using `git show` and SHA-256. This comparison used the captured revision, not concurrent working-tree edits.
- SHA-256 of the ten reviewed result objects, in report order, serialized with `json.dumps(rows, sort_keys=True, separators=(',', ':'))`: `8308f9c1078c5bbe7775b9f82a1f04bd21e5401e9212a2f1dee2743b14f1d159`. This is a subset digest, not a hash of the still-growing report.
- Each factual strategy field and every populated evidence-packet field was compared with its case's exact `case_facts.source_tool_records`. Fixture expectations supplied narrative citation requirements only; `fixture_context` was not treated as model-visible evidence. Model explanations were checked against the output and sources, rather than accepted as factual authority. Internal numeric estimates were not treated as empirical claims.
- Raw subset results: action match 10/10, gate match 10/10, EV sign 10/10, composed judge 5/10. Narrative reason, required citations, and word-count checks each passed 10/10. These are the recorded scores, not adjusted manual scores.

All ten packets have null file and policy-disclosure fields, null `uncategorized_text`, and `files: []`. No unproduced attachment or unsupported policy-disclosure claim was found in this subset. Customer names, email addresses, billing/shipping addresses, carrier names, tracking identifiers, and shipping dates match their respective source records. The defects below concern claims within narrative or strategy text.

## Per-case adjudication

| Case | Generated-output finding | Raw composed judge and independent assessment | Narrative references checked |
| --- | --- | --- | --- |
| 01 | No definite factual defect found. Delivery, signature, addresses, card checks, order and shipment dates are supported. Communication absence is explicitly restricted to merchant records. | Fail: false positive from the premise check discarding the records qualifier. | `1Z99901`, `M. Taylor`, delivered |
| 02 | No definite factual defect found. Carrier, delivery date/time, signature, addresses, checks, and scoped record absence are supported. | Fail: same records-qualifier false positive. The premise explanation also says the narrative mentions a return-policy requirement that appears only in the source. | `794902`, `D. Vance`, delivered |
| 03 | Unsupported merchant-policy attribution in the last narrative sentence; details below. Other factual fields are supported. | Fail for the wrong reason: broad grounding misses the policy claim; the outcome extractor rejects a bare recommendation instead. | `940003`, delayed, never delivered |
| 04 | No definite factual defect found. The output compares recorded `D. Kim` with billing name `David Kim`; this is conservatively read as name consistency, not a statement of authenticated identity or personal receipt. | Pass agrees with that reading. The premise explanation incorrectly argues that an empty message array proves absolute event absence; the actual sentence passes because it says “in merchant records.” | AVS, CVC, `442004` |
| 05 | No definite factual defect found. Delivery and signature match; absence of alternate-address requests and failed checks is scoped to supplied records. | Fail: same records-qualifier false positive. | `1Z99905`, `R. Martinez`, AVS |
| 06 | Narrative and strategy turn a null signature field into an assertion that no signature was obtained; details below. | Pass: false negative. Broad grounding explicitly treats null as affirmative absence, and the premise check says there is no event-absence assertion. | alternate address, unverified |
| 07 | No definite factual defect found. The return policy is quoted without a disclosure claim. Missing return requests are explicitly scoped to supplied communications. | Fail: same records-qualifier false positive in the narrative. | return policy; no pre-dispute customer communications in merchant records |
| 08 | No definite factual defect found. “No signature confirmation was recorded” correctly describes missing signature data. Return tracking, reported warehouse delivery, and outstanding refund remain attributed to the first-person communication. The “reported-return rule” is not called a merchant policy. | Pass agrees. | `RET-88008`, warehouse, return delivered |
| 09 | No definite factual defect found. The output uses 12 total orders, $3,400 LTV, and the actual $500 VIP threshold. “No return request appears in the supplied communications” has the necessary scope. | Pass agrees. The message's “Disappointed” is read as the linked customer's expressed dissatisfaction, not a claim of authenticated cardholder identity. | VIP, LTV, policy |
| 10 | The narrative assigns an order creation date to a charge; details below. Refund references, quoted communication, current refunded status, and other factual fields are supported. | Pass: false negative. Both broad and premise explanations accept the substituted event date. The earlier unsupported refund-before-dispute claim is absent. | `re_prior10`, refund already issued |

## Exact defects and evaluator distinctions

### Case 03: an agent decision rule presented as merchant parameters

Field: `supporting_output.evidence_packet.narrative`.

> The disputed amount of $65.00 falls within merchant operational parameters for concession when delivery cannot be confirmed.

The captured `get_merchant_history_and_policy` result at `case_facts.source_tool_records[5].content[0].policy` contains `approval_amount_cents: 20000`, `min_win_probability_to_fight: 0.5`, `always_concede_under_cents: 1500`, `vip_concede_max_cents: 50000`, `silence_action: "fight"`, and a 30-day return-policy statement. It does not contain a merchant rule to concede an unconfirmed delivery at $65. The reason-specific agent instruction supports choosing concession, but it is not evidence that the merchant supplied that rule.

The support extractor instead rejected “Concede dispute dp_eval_03 based on carrier non-delivery.” That sentence is an action recommendation citing the recorded delayed/non-delivery basis, not an assertion that choosing concession causes a future outcome. Its extraction is a component false positive. The composed failure does not demonstrate that the actual unsupported policy claim was detected.

### Case 06: null signature data converted to a negative event

Field: `supporting_output.evidence_packet.narrative`.

> No signature was obtained at delivery.

Related claims occur in `strategy.rationale` (“FedEx delivered to that address on 2026-08-17 without signature”) and `strategy.owner_summary` (“delivery confirmed to that address without signature”).

The captured shipping result at `case_facts.source_tool_records[3].content[0]` has `signed_by: null`. Its two events record shipment and delivery; neither says no signature was obtained. There is no affirmative signature-obtained boolean or explicit no-signature event. The tool returns a nullable signature-name field from the shipment record; its contract does not define null as proof that no signature was collected. “No signature recorded” is supported, as demonstrated by the correctly scoped wording in case 08. The stronger claim in case 06 is not.

### Case 10: order creation time substituted for charge time

Field: `supporting_output.evidence_packet.narrative`.

> The disputed charge for $99.00 (Wireless Gaming Mouse, order ORD-EVAL-010) was placed August 1, 2026.

The source supplying August 1 is `get_order_evidence`, at `case_facts.source_tool_records[2].content[0].created_at`. Neither `get_charge_context` nor `get_dispute` supplies a charge creation timestamp. The sentence's subject is the disputed charge, so the parenthetical order identifier does not make the order date evidence of that charge event. Describing the order as created on August 1 would stay within the source evidence. The premise explanation explicitly cites `order.created_at` as support for the disputed-charge sentence, showing the missed distinction.

### Cases 01, 02, 05, and 07: qualified absence wrongly rejected

All four narratives state:

> No pre-dispute customer communications exist in merchant records.

Their `get_customer_comms` results have `messages: []` and `message_count: 0` at `case_facts.source_tool_records[4].content[0]`. The phrase “in merchant records” restricts the claim to that record collection. It does not assert that the customer never communicated through any channel. The premise check labels the sentence unqualified and demands a qualifier already present in the actual words. Broad grounding accepts these records-scoped claims, and the outcome extractor returns an empty assertion list. These four composed failures are evaluator false positives, not evidence of a generation defect.

This finite review does not establish population false-positive or false-negative rates. It also does not establish production Stripe submissions, live SMS behavior, or a later repaired generator's output quality. No provider calls, score overrides, code changes, or raw-report edits were performed for this review.
