# Source review: ccd5616 cases 11–20

Status: COMPLETE for this source review. All ten outputs, cases 11–20, are reviewed. This review does not certify the overall grounding work as complete.

Raw report: `evals/results/2026-09-14-ccd5616-b.json`. The report records revision `ccd5616`, `source_dirty: false`, generation and judge model `us.anthropic.claude-sonnet-4-5-20250929-v1:0`, rubric `grounded-v15`, and source snapshot SHA-256 `fb6c7607596830a59e6e979faeacc4554fcd52b133db84fcbf82818e05502114`. Every recorded source-manifest hash was independently compared against its Git blob at `ccd5616`; all matched. The report is now `completed: true` with ten cases. Preserved report SHA-256: `79c2bfa90606e0aca0d700fafac8eded41c5e9bb09a70994d3ccb3318dc93ae5`.

This review compares all factual fields in `supporting_output.strategy` and `supporting_output.evidence_packet` with the exact captured `case_facts.source_tool_records`. The fixture's descriptive story and expected action are not factual evidence. Required narrative citations are checked separately. Internal numeric assessments and action selection are outside factual-prose review. Raw judge outcomes are preserved; review findings do not change recorded scores.

Observed raw shard totals: action match 10/10, gate match 10/10, EV sign 10/10, judge pass 8/10, valid judge response 9/10. Genuine factual defects are present in cases 11, 13, and 17. The judge correctly fails case 11, misses the defects in 13 and 17, and fails case 20 because its premise response could not be parsed. No required narrative citation omission was observed. Raw verdicts remain unchanged.

## Case 11: credit_not_processed

Raw judge: FAIL. Independent review: a genuine unsupported policy-disclosure field, correctly rejected by both broad grounding and premise judges.

- `evidence_packet.refund_policy_disclosure` contains `30-day return policy; customer must initiate return through merchant support prior to dispute`. Source record 5, `get_merchant_history_and_policy`, supplies this as `policy.return_policy`; no captured record establishes that Kelly Zhang was shown the policy before purchase. Correct policy content does not establish the fact asserted by this Stripe field. This field must be null without disclosure evidence; relevant policy text may appear in narrative or supplementary text.
- Other populated identity, billing, physical shipping, carrier, tracking, and shipping-date fields match source records. Narrative amount $130, delivery on August 5 at 15:00 UTC, FedEx tracking `794911`, signature `K. Zhang`, and address match records 0–3. The August 7 communication quotes the support refund promise accurately. Claims of no processed refund are limited to the supplied order status, charge metadata, and communications records; no universal nonpayment or invented processing failure is asserted.
- Narrative contains required `MSG-11` and the promised refund. All file-reference fields are null and `files` is empty. The proposal is prospective. No further factual defect observed in inspected fields.
- Unscored format deviation: narrative is 101 words, exceeding the generator's under-60-word concession instruction while remaining below the evaluator's 250-word ceiling. This is not counted here as a factual grounding failure.

## Case 12: subscription_canceled

Raw judge: PASS. Independent review: no concrete factual defect or required-citation omission observed.

Thomas Evans, email, billing address, order creation on August 1, Monthly Pro Software License amount $49, all three passing card checks, and digital delivery on September 1 match records 0–3. The narrative names the order when citing its creation date. Record 4 contains the first-person cancellation message dated September 5, including the reported four-day interval after renewal and prior agreement to subscription terms. Narrative and owner summary preserve that attribution. The rationale's final sentence summarizes the chronology immediately following the attributed quote; this is not treated as an independent new source claim. No specific-payment authorization or policy-compliance conclusion is asserted. Customer tier `new`, 2 total orders, $98 lifetime value, and zero prior disputes match record 5.

All physical shipping fields are null for this digital product, repairing the prior run's field-semantic defect. File-reference and policy-disclosure fields are null, and `files` is empty. Narrative contains all required references: subscription terms, September 5, and after renewal.

## Case 13: subscription_canceled

Raw judge: PASS. Independent review: a genuine event-type/source-attribution defect missed by the broad grounding and premise judges.

- Both `strategy.rationale` and `evidence_packet.narrative` assert: `The digital delivery record shows the renewal occurred on 2026-09-01T00:00:00Z.` Source record 3 contains only digital delivery (`shipped_at` and `delivered_at`) timestamps. It does not record a renewal event. Record 4 reports a September 1 renewal date but supplies no precise midnight renewal timestamp and does not make the digital delivery record evidence of that event. The output improperly changes a delivery timestamp into a renewal timestamp and misattributes its evidentiary source. The owner summary also says the renewal date is documented in both communications and digital delivery records.
- The judge explanations repeat the same error. Broad grounding says the digital delivery timestamps support the renewal date, while the premise judge calls delivery time `renewal delivery` and treats both event times as recorded. This is a false negative, not an ambiguous currency/date formatting issue.
- Smallest factual correction: report digital access delivery on September 1 separately, then state that the communication reports a cancellation request before the stated September 1 renewal. Do not claim the exact renewal time or independent renewal proof from the delivery record.
- Lisa Montgomery, email, billing address, new tier, and the August 28 cancellation message otherwise match captured records. Its first-person request supports customer attribution. Narrative includes required August 28, before renewal, and cancellation request. Physical shipping fields, policy-disclosure fields, and file-reference fields are null; `files` is empty.

## Case 14: duplicate

Raw judge: PASS. Independent review: no concrete factual defect or required-citation omission observed.

Narrative, rationale, and owner summary attribute the distinct-items comparison to the communications record without inventing a customer admission. The August 10 `Order receipt` message explicitly says `ORD-14A` and `ORD-14B` contained distinct items ordered separately, while charge metadata separately supplies those related-order IDs. The output does not infer contents or order timing from the IDs alone and does not invent separate payment intents or a total shipment count. All three required narrative references (`ORD-14A`, `ORD-14B`, distinct items) are present.

Marcus Reid's name/email, billing and shipping address, passing card checks, UPS tracking `1Z99914`, August 10 shipping date, August 13 delivery date, and signature `M. Reid` match records 1–3. Billing and carrier delivery addresses are identical, supporting that comparison. The signature is reported as recorded without asserting verified cardholder identity or authorization. Customer tier is `new`. All file-reference and policy-disclosure fields are null, and `files` is empty. The previous run's authorship false positive does not recur in this saved verdict.

## Case 15: duplicate

Raw judge: PASS. Independent review: no concrete factual defect or required-citation omission observed.

The August 8 communication reports two charges two seconds apart, identical items, and a single fulfilled shipment. All three factual text fields retain communication attribution for this report. The output accurately states that the retrieved records show one order lookup and one USPS delivery; it does not convert one retrieved shipment into an independently proven global shipment count. Its absence claim is limited to what communications/charge metadata report, with the owner summary continuing that records context. Narrative includes all required references: double charge, identical, and single shipment.

Order `ORD-EVAL-015`, creation on August 1, $60 amount, fulfilled status, USPS tracking `940015`, August 8 shipping date, August 11 delivery, Columbus address, and passing card checks match source records. Hannah Abbott's name/email, addresses, and new tier match their sources. `signed_by` is null and the output makes no unsupported claim that no signature was obtained. File-reference and policy-disclosure fields are null; `files` is empty.

## Case 16: inquiry

Raw judge: PASS. Independent review: no concrete factual defect or required-citation omission observed.

The raw dispute has `reason: inquiry` and `status: warning_needs_response`. Narrative labels it as a pre-chargeback inquiry, quotes the August 1 communication, and proposes an inquiry refund. The reported cancellation before renewal and requested avoidance of a $15 fee remain attributed to that communication in narrative, rationale, and owner summary. The output does not independently assert the earlier cancellation happened, that a fee is applicable, or that the proposed refund guarantees resolution or savings. All required references (inquiry, cancellation, $15 fee) are present in narrative.

Roberto Alvarez's identity, email, Memphis billing address, new tier, $129 charge, Annual Analytics SaaS Plan, order creation on August 1, and digital delivery on August 1 match the corresponding records. Order creation and digital delivery remain distinct event types. Physical shipping fields, disclosure fields, and file-reference fields are null; `files` is empty. The previous digital-to-physical field defect does not recur in this output.

## Case 17: inquiry

Raw judge: PASS. Independent review: a genuine unsupported null-signature inference missed by the broad grounding and premise judges.

- `strategy.owner_summary` says `USPS tracking shows delivery 2026-08-08 to billing address without signature.` Source record 3 has `signed_by: null`; this supports no signature recorded in the supplied record, not the claim that delivery occurred without a signature. The output's reference to tracking does not make an affirmative no-signature claim present in that source. Smallest correction: `USPS tracking records delivery on 2026-08-08 to the billing address; no signature is recorded in the supplied record`, or omit the signature clause.
- The broad judge explains that the output `correctly notes no signature was recorded`, silently changing the actual wording `without signature`. The premise judge says no relevant absence claim is present. Both pass the unsupported inference, making this a false negative.
- Other reviewed facts match: Patricia Hall's identity/email/billing address, repeat tier, four orders, $320 lifetime value, $75 inquiry amount, USPS tracking `940017`, August 8 delivery, and August 9 message. Billing and shipping addresses match, so the delivery-address comparison is valid. The pause claim and $15 fee remain attributed to the first-person customer message; no independent delivery-pause event or guaranteed fee saving is asserted. Narrative contains both required references, inquiry and $15 fee. Optional shipping fields, policy-disclosure fields, and file-reference fields are null; `files` is empty.

## Case 18: product_not_received

Raw judge: PASS. Independent review: no concrete factual defect or required-citation omission observed.

Jessica Lee's repeat tier, 5 total orders, $1,200 lifetime value, $450 disputed amount, and the configured `vip_concede_max_cents` value of 50000 cents ($500) match source records. The output recommends a concession using those facts without relabeling this repeat customer as VIP, promising retention, or asserting the action is complete. Required narrative references repeat, LTV (spelled out as lifetime value), and `vip_concede_max_cents` are present. The raw `missing_items` list contains literal `LTV`, but the narrative judge correctly accepts its spelled-out equivalent; this diagnostic list does not represent a final citation failure.

Name/email, addresses, FedEx tracking `794918`, August 10 shipping date, August 13 delivery at 13:00 UTC, and `J. Lee` signature match records. The card-check summary matches all three pass results. The absence of communications is expressly restricted to merchant records and matches an empty messages array; it does not claim the customer never contacted support. All file-reference and policy-disclosure fields are null, and `files` is empty.

## Case 19: fraudulent

Raw judge: PASS. Independent review: no concrete factual defect or required-citation omission observed.

Order `ORD-EVAL-019`, Professional Drone 4K, $550, creation on August 1, Samuel Jenkins, email, and Dallas addresses match source records. The narrative correctly labels the August 1 date as order creation. UPS tracking `1Z99919`, August 15 shipping date, August 18 delivery at 14:30 UTC, and recorded signature `S. Jenkins` match the carrier record. Billing and delivery addresses match, supporting the comparison. Passing AVS line1/postal and CVC checks are reported without claiming they independently prove payment authorization; rationale expressly notes that name consistency does not verify recipient identity. Required narrative tracking, signature, and AVS references are present.

The communication absence statement is restricted to merchant records and supported by the empty array. Customer tier is correctly `new`. All file-reference and policy-disclosure fields are null; `files` is empty. The proposed fight action is not described as already submitted.

## Case 20: product_not_received

Raw judge: FAIL, `judge_valid: false`, because the premise judge returned an invalid response (`JSONDecodeError`). This is an unavailable evaluation, not evidence that a specific factual claim failed. Broad grounding passes. Independent review: no concrete factual defect or required-citation omission observed.

Olivia Moore's identity/email, Minneapolis billing and shipping addresses, new tier, order `ORD-EVAL-020`, Aroma Oil Diffuser, $45 amount, USPS tracking `940020`, August 16 shipping date, and August 19 delivery at 11:00 match the source records. The narrative's St Paul origin is explicitly supplied by the shipping event. It describes `Delivered in Mailbox` as a carrier delivery confirmation, not a person's signature or verified receipt by the cardholder. Rationale and owner summary preserve that meaning. The equal billing/delivery address and passing AVS line1/postal/CVC checks are directly supported. Communication absence remains limited to merchant records. Required narrative tracking number, delivered status, and USPS references are present.

File-reference and policy-disclosure fields are null; `files` is empty. The proposed fight action is prospective. The invalid premise response must remain a failure in raw benchmark accounting unless a separately recorded evaluation is performed; source review does not substitute a model verdict.

## Evidence limits

This is a read-only review of saved model outputs and their captured source records. No provider calls, code edits, score overrides, or raw-report edits were performed. The model drafts still contain the documented defects. Any subsequent deterministic formatting and re-evaluation must be recorded separately from this generation run.
