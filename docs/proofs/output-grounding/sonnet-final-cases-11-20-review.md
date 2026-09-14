# Independent source review: final Sonnet cases 11–20

Status: source review complete for the captured cases 11–16. Cases 17–20: NOT RUN to a completed evaluation; no captured outputs are available. The root runner reported `ExpiredTokenException` after case 16, and the preserved report remains `completed=false` with 16 results. This is a partial run, not a passing fixed-20 benchmark.

Run: `evals/results/2026-09-14-sonnet-final.json`, generation revision `45772c9`, rubric `grounded-v12`, Sonnet 4.5 for generation and judgment. The source report records a clean source snapshot. Preserved report SHA-256: `3e69bd3e5636e8997862c69088121226a605f77e13f5bfe2c2f80441678f582c`. The model's per-case verdicts remain recorded evidence, not a claim of evaluator accuracy.

This review compares every factual strategy/evidence field against the exact captured `source_tool_records`, and separately checks the narrative's required citations. Fixture descriptions and expected actions are not factual evidence. Reported events remain distinct from independently established events; policy contents remain distinct from evidence of pre-purchase disclosure. Model verdicts are retained unchanged.

## Case 11: credit_not_processed

Observed judge result: pass. Independent finding: no factual output defect or narrative citation omission observed.

All populated identity/address/shipping fields match the orders, charge-context, and shipment records. The narrative's Espresso Grinder, $130 amount, August 1 order creation, August 2 shipment, August 5 delivery, signature `K. Zhang`, and tracking `794911` are recorded. The August 7 support message explicitly promises a refund within three days; its merchant-perspective wording supports describing a merchant communication without claiming independently authenticated identity. `MSG-11` and `promised refund` both appear in the narrative. Rationale, owner summary, and narrative limit missing-refund findings to supplied records, rather than asserting a payment failure. Proposed concession remains prospective. File fields and disclosure fields are null, with `files=[]`.

Primary evidence: `results[10].case_facts.source_tool_records`, especially the orders record at index 2, shipment at index 3, and support communication at index 4. All factual fields in `results[10].supporting_output` were inspected; internal action/probability/EV assessments were not treated as external factual claims.

## Cases 12–13: subscription_canceled

Observed judge results: both pass. The narratives contain all fixed citation requirements. Case 12 quotes `Sep 5`, `4 days after renewal`, and `subscription terms`; case 13 quotes `Aug 28`, `before renewal`, and `cancellation request`. The communications records contain those exact first-person requests and their recorded message dates. The narratives preserve reported chronology and do not infer specific-charge authorization or compliance with unseen terms. Customer names, emails, tiers, card checks, and digital delivery dates match captured records. File/disclosure fields remain null and `files=[]`.

Field-contract defect: both packets populate physical `shipping_address`, `shipping_carrier`, `shipping_tracking_number`, and `shipping_date` fields for digital products. Case 12's item is `Monthly Pro Software License`; case 13's is `Quarterly Membership`. Each shipment record has `carrier="Digital"`, a `DIGITAL-12/13` reference, and `shipping_address={}`. The packet copies the street address from the order's shipping-address field. These values are present in source records, but the installed Stripe contract describes the populated fields as physical-product shipping/carrier evidence. This is a fixture/tool representation and field-semantics defect, not an invented source quotation. The fixed benchmark currently passes these fields and has no citation requirement for their digital reference IDs. The root reviewer independently confirmed the physical-only contract. No score was changed.

Primary evidence: `results[11]` and `results[12]`, each `case_facts.source_tool_records[2]` (order/product/address), `[3]` (digital delivery), and `[4]` (cancellation message). All factual fields in both `supporting_output` objects were inspected. Stripe contract reference: installed `stripe/params/_dispute_modify_params.py`, physical shipping definitions at lines 117–135.

## Case 14: duplicate

Observed judge result: fail, due to alleged customer-authorship claims. Independent finding: judge false positive under the run's stated rubric; no factual output defect or fixed citation omission observed.

The narrative quotes `A communication dated August 10, 2026 states...`; the rationale/owner summary use `customer communication ... reports`. No field says the customer wrote, sent, or admitted the comparison. The rubric explicitly allows `customer communication` as a generic communication-with-customer label without asserting authorship. The broad judge acknowledges that rule and then contradicts it by treating the same label as an authorship assertion. Its first numbered finding also labels the neutral narrative as unsupported while immediately describing it as neutral. `ORD-14A`, `ORD-14B`, and `distinct items` all appear in the narrative and the captured message. Product, $120 amount, order creation, card checks, metadata, shipment/address, signature `M. Reid`, and tracking `1Z99914` match the retrieved records. File/disclosure fields are null and `files=[]`.

Primary evidence: `results[13].supporting_output`, `case_facts.source_tool_records[4].content[0].messages[0]`, and `judge_details.grounding_judge`. The saved failure remains unchanged.

## Case 15: duplicate

Observed judge result: pass. Independent finding: no factual output defect or fixed citation omission observed. The double charge, two-second interval, identical items, and single shipment are attributed to the communication; its first-person subject `Double charged on my card` supports describing a customer report. The narrative and strategy distinguish that report from the single order/delivery present in retrieved records. No null-signature-to-no-signature inference is made. All populated shipping/identity fields, $60 amount, Fitness Resistance Bands item, dates, and card checks match records. `double charge`, `identical`, and `single shipment` occur in the narrative quote. File/disclosure fields are null and `files=[]`.

Separate unscored prompt deviation: narrative word count is 104. The fixed evaluator enforces 250 words, so it passes; the generator's duplicate-concession instruction asks for under 60 words. This is a brevity deviation, not a grounding failure or a reason to alter the saved score.

Primary evidence: `results[14].supporting_output`, especially its explicit record-scoped count statements, and `case_facts.source_tool_records[2:5]` for order, shipment, and attributed communication.

## Case 16: inquiry

Observed judge result: pass. Independent finding: the same physical-shipping-field contract defect as cases 12–13. The item is `Annual Analytics SaaS Plan`; the source shipment uses `Digital`, `DIGITAL-16`, and an empty delivery address, but the output fills physical shipping fields and the order's street address.

Narrative and strategy prose otherwise remain grounded: they preserve the customer's report of a prior cancellation and the quoted `$15 fee` statement, without claiming independently verified cancellation, fee savings, resolved inquiry, or prevented escalation. The $129 amount, plan name, customer identity/tier, August 1 message timestamp, inquiry reason, and `warning_needs_response` status are recorded. All three required citations (`inquiry`, `cancellation`, `$15 fee`) appear in the narrative. File/disclosure fields are null and `files=[]`.

Primary evidence: `results[15].case_facts.source_tool_records[2]` (SaaS product and order address), `[3]` (digital delivery), `[4]` (customer report/fee quote), and all factual fields of `supporting_output`.

## Cases 17–20

NOT RUN to a completed evaluation in this report. Their fixture citation requirements were inspected in preparation only; no runtime finding or passing result is inferred from them. A fresh run requires separate source verification and a separate review artifact.

## Consolidated findings

- Cases 12, 13, and 16: source-present digital delivery values were placed into Stripe's physical shipping fields; the judge missed this field-contract defect.
- Case 14: false-positive authorship failure under the run's own rubric; saved verdict left unchanged.
- Case 15: 104-word narrative exceeds the reason-specific under-60 prompt instruction, while passing the fixed 250-word evaluator limit. This is an unscored brevity deviation.
- Case 11 and case 15: no factual output defect or fixed citation omission observed. All six captured narratives contain their fixed required references.

Only this review document was edited during the source review. No provider calls, code changes, or raw-report edits were performed.
