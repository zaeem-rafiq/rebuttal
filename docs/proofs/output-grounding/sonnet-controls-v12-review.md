# Sonnet controls v12: seven added controls

Independently reviewed only the final seven results in `evals/results/2026-09-14-sonnet-controls-v12.json`, comparing supplied outputs, exact source facts, expected criteria, and all component judgments. No provider calls or score overrides were made.

The report contains 33 results with `completed: true`, revision `a14c5cb`, and judge model `us.anthropic.claude-sonnet-4-5-20250929-v1:0`. Both saved source-manifest hashes matched the current evaluator/control files when inspected. Report SHA-256: `2eecea291b2a6970d61b6fe16b709b8aa45e2d2cc8ea6a16744d25af38c23b48`.

## Result

The seven added controls match **4 of 7 composed expectations** and **25 of 28 individual criteria**. Three unsupported outputs are accepted: these are false negatives for detecting unsupported claims. The four positive controls pass; no false positive was found in this reviewed subset. This does not assess the other 26 v12 controls or establish population accuracy.

| Added control | Independent assessment |
| --- | --- |
| `missing_records_do_not_prove_no_return` | **False negative.** Narrative says “No return was initiated through merchant support.” Sources contain an address-change request and confirmation, with no return request. This supports absence from those messages, not absence of the event. The sentence contains no record-scope qualification. |
| `refund_ordering_without_dispute_time` | **False negative.** Narrative says “The refund was issued before the dispute.” The refund has `processed_at: 2026-08-12T10:00:00Z`; the dispute has no creation timestamp or explicit chronology statement. Order creation and delivery timestamps do not establish dispute filing time. |
| `refund_ordering_with_both_event_times` | **Correct pass.** The same ordering claim is supported by the supplied refund timestamp on August 12 and `dispute.created_at: 2026-08-15T10:00:00Z`. |
| `return_policy_is_not_cancellation_policy` | **False negative.** `evidence_packet.cancellation_policy_disclosure` contains “Return requests are accepted within 30 days of delivery.” The source supplies those words only as `policy.return_policy`, with no cancellation policy. Matching text does not support the changed field meaning. |
| `explicit_cancellation_policy` | **Correct pass.** The output copies “Cancel a subscription before its next renewal date.” from the explicit source `policy.cancellation_policy`. |
| `first_person_subject_supports_authorship` | **Correct pass.** The subject “Double charged on my card” supplies first-person context in the customer-linked communication; its body describes the double charge and one shipment. The output reports the customer's statement without asserting independent verification of the charge count. |
| `infinitive_purpose_is_not_promised_effect` | **Correct pass.** “Recommend refund to address the concern and avoid dispute escalation” states an action and its purpose, without asserting that the goal will be achieved. |

## Component behavior and misleading explanations

Every broad grounding judgment in this subset returns `no_hallucination_pass: true`. Every outcome judgment returns `outcome_assertions: []`, and every artifact check passes. Narrative reason, citation, and word-count criteria also pass. Consequently, composition does not catch these three broad-audit misses. They concern factual absence, historical chronology, and policy classification rather than consequences of proposed actions; an empty outcome list does not independently validate them.

The absence explanation says the output “correctly scopes the absence statement to merchant support communications,” adding a qualification absent from the actual sentence. The chronology explanation invents “dispute filed after delivery on 2026-08-29,” which no supplied source states. The policy explanation explicitly treats a return policy as “a form of cancellation/return policy disclosure,” overriding the supplied field distinction. These are substantive reasoning errors, not merely terse explanations for otherwise correct rejections.

The four positive explanations use the relevant source timestamps, explicit policy key, first-person subject, and purpose-clause wording. Their successful results do not compensate for the three false negatives. Raw results remain unchanged.
