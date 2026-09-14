# Sonnet trial review

Status: complete for the original trial. Review generation source revision 25bfc30 against the exact
source_tool_records captured per case. Fixture-only descriptions and model verdicts
are not independent proof. Preserve original model scores without manual overrides.
Root reviews cases 01–10; the independent reviewer owns cases 11–20 and control
mismatches. Numeric probability calibration and EV magnitude are outside this audit;
the fixed benchmark checks only EV sign.

| Case | Exact-source review |
|---|---|
| 01 | No definite unsupported claim found. Addresses, dates, amount, signature, card checks, policy, and scoped empty communications match records. |
| 02 | No definite unsupported claim found. Carrier delivery is source-attributed; signature, origin, dates, addresses, card checks, and policy match records. |
| 03 | No definite unsupported claim found. Delayed/never-delivered wording is attributed to the carrier event and customer complaint; null delivery/signature and tier/threshold facts match records. |
| 04 | No definite unsupported claim found. Signature-name consistency is distinguished from recipient identity; addresses, delivery and shipment dates, checks, and policy match records. |
| 05 | No definite unsupported claim found. Name initials/surname align with billing record without asserting verified personal receipt; tracking, address, checks, and policy match. |
| 06 | No definite unsupported claim found. Postal check failure, alternate-address message, shipment timing, tier, amount, LTV, and policy threshold match retrieved records. |
| 07 | No definite unsupported claim found. Previously missing return policy now appears in the narrative; empty communications stay scoped to merchant records. |
| 08 | No definite unsupported claim found. Reported return and missing refund are attributed to the customer message, with return tracking and dates retained. |
| 09 | Unsupported absence claim: "No return was initiated through merchant support." Source contains a complaint, not an authoritative negative return record. Judge incorrectly adds a supplied-records scope; raw pass preserved. LTV is now correctly $3,400. Root and independent reviewer agree. |
| 10 | Unsupported ordering: "Records confirm refund already issued prior to the dispute." Refund is recorded but dispute creation/event time is absent. A due date and refund ID do not establish that ordering. Raw pass preserved. The drafter prompt itself instructs this ordering and needs repair. Root and independent reviewer agree. |
| 11 | Independent review found no definite unsupported claim or citation omission. Promised refund and MSG-11 are cited; missing refund is scoped to records. |
| 12 | Independent review found no definite defect. Agreement and cancellation timing remain attributed observations without a charge-authorization conclusion. |
| 13 | Unsupported field attribution: return_policy text is placed in cancellation_policy_disclosure with no cancellation policy supplied. Raw judge pass preserved. |
| 14 | Independent review found no definite defect. Neutral comparison record is attributed without inventing customer authorship. |
| 15 | Raw judge failure is an authorship false positive: first-person subject "Double charged on my card" was ignored while the body was inspected. No definite additional defect found. |
| 16 | Unsupported "Proposed refund resolves pre-chargeback inquiry" and return-policy text in cancellation_policy_disclosure. Raw failure preserved, but extracted goal fragments are not the defensible reason. |
| 17 | Unsupported "Proposed refund resolves pre-chargeback inquiry". Raw failure preserved; the extracted escalation purpose fragment is not the actual asserted-result clause. |
| 18 | Independent review found no definite defect. Empty communications explicitly scoped to merchant records; tier, LTV, tracking, signature, dates and threshold match. |
| 19 | Independent review found no definite defect. Recorded signature, tracking and AVS citations match sources. |
| 20 | Independent review found no definite defect. Carrier mailbox delivery is not strengthened into personal receipt; citations present. |

Original trial completed: action20/20, gate20/20, EVsign20/20, composedoutputjudge17/20,
exit1. Raw failures are15,16,17. Independent source review found concrete defects
in09,10,13,16,17 and a false-positive failure in15. These observations do not
replace raw scores. The prompt and evaluator follow-up is a separate source revision;
its model verification remains pending.
