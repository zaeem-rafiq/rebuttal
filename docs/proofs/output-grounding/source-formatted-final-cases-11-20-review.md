# Final source review: formatter 4371ebf

Status: COMPLETE for this bounded source review. All final replay cases 11–20 and fresh whole-graph cases 03/18 are reviewed. No concrete factual defect or required-citation omission was observed in these final outputs.

Scope: independently compare all final factual strategy/evidence-packet fields and required narrative citations with the exact captured source records. Active replay reports are `evals/results/2026-09-14-source-formatted-final-v2-{a,b,c}.json`; fresh graph report is `evals/results/2026-09-14-source-formatted-final-v2-live.json`. The initial `source-formatted-final-*` attempt could not connect through the sandbox and is preserved separately as unavailable partial evidence. No provider calls, code changes, raw-report edits, or score overrides are performed by this review.

The replay applies formatter `4371ebffbb2467317477d6093e96d9f24dde9fcf` to generation captured at `ccd5616`, then obtains new judgments. It is not fresh twenty-case model generation. The separate fresh graph report exercises cases 03 and 18 at `4371ebf`.

Provenance verified against Git blobs for all three completed v2 replay reports: formatter SHA-256 `f9af3cf8510fe9ccb4693fde049ceb8bf6aff16af5931058ac04114973a8c602`; evaluator SHA-256 `eb236bd729e2609d5802ec723b90994235babc9bd7335988393b4f7c7bce18db`, unchanged from the previous formatted replay; rubric `grounded-v17`. Both original `ccd5616` source-report hashes match their preserved files. The completed v2 fresh graph source manifest matches revision `4371ebf` and records `source_dirty: false`, snapshot `3e9950a98db89479e22204b1a40b88cbfbe98443a6b671c82f7c37ba020c22d1`.

Observed saved outcomes for the reviewed replay subset: 10/10 valid judge passes, 10/10 action matches, 10/10 gate matches, and 10/10 EV-sign matches. Fresh cases 03/18: 2/2 on those same checks with valid judgments. These are subset totals; this review does not relabel any other case's failure or aggregate the full twenty-case result. Independent word counts are 68–100 for reviewed replay narratives and 84/80 for fresh cases 03/18, below the 250-word ceiling. Earlier failures remain preserved.

Final report SHA-256 values:

- Replay v2 a: `dc6c6e896409f0da60e0c304e218dd1cb05de782104b2bd9473772e93b51e4a9`.
- Replay v2 b: `8efff9e91244c99f39d76c4f744ad2348f163a59c1080b8789f479fbc9368297`.
- Replay v2 c: `9f93f975995e56dded2e8acffb3cd9b0399ff168ac09cc29c0f065b66898cd23`.
- Fresh graph v2: `7ab6da6e7e8d005c462e63274df4293282acf45c1e999ccd0e7bef86397ac2e8`.

The bounded formatter change replaces the mixed legacy `signed_by` label with `signature or delivery notation`. New customers omit the irrelevant VIP limit; repeat/VIP customers receive the recorded limit with the explicit qualification that the limit alone does not establish eligibility. Results from the earlier formatter remain separately reviewed in `source-formatted-cases-11-20-review.md`.

## Reviewed final replay cases

Cases 11–20 have exact `case_facts` equality with the preserved original snapshots. Every strategy rationale/owner summary and populated evidence field was reviewed. Identity/email, formatted addresses, status, amount, tier, order count/LTV, and communication count match the captured records. Physical shipping dates are YYYY-MM-DD; digital physical-shipping fields are null. All file-reference and policy-disclosure fields are null; `files` is empty. No unsupported completed action, policy disclosure, event date substitution, identity proof, or outcome prediction is observed.

| Case | Saved judge | Source/citation review |
| --- | --- | --- |
| 11 | Valid PASS | Kelly Zhang/$130, FedEx `794911`, August 2 shipment and August 5 delivery, `K. Zhang` notation, and August 7 support quote match sources. `MSG-11` and promised refund are cited. Unsupported disclosure remains absent. |
| 12 | Valid PASS | Thomas Evans/$49, new tier, two orders/$98 LTV, September 1 digital access, and September 5 message match sources. Subscription terms and reported after-renewal timing remain in the intact quote; no independent renewal claim. |
| 13 | Valid PASS | Lisa Montgomery/$89, September 1 access data, and August 28 cancellation message match sources. The before-renewal report stays attributed; no delivery timestamp is reclassified as renewal. All three required references are present. |
| 14 | Valid PASS | Marcus Reid/$120, two orders/$240 LTV, UPS `1Z99914`, dates and `M. Reid` notation match sources. Neutral receipt quote retains `ORD-14A`, `ORD-14B`, and distinct items. Irrelevant VIP parameter is omitted; prior applicability false positive does not recur. |
| 15 | Valid PASS | Hannah Abbott/$60, USPS `940015`, dates, and source-scoped null-signature statement match records. The message supplies double charge, identical items, and single shipment as attributed content, without independently proving a second charge. |
| 16 | Valid PASS | Roberto Alvarez/$129, new tier, one order/$129 LTV, August 1 order and digital-access dates match sources. The message retains inquiry, cancellation, and $15 fee references without independently asserting an earlier cancellation or guaranteed fee saving. Digital physical-shipping fields are null. |
| 17 | Valid PASS | Patricia Hall/$75, repeat tier, four orders/$320 LTV, USPS `940017`, dates, and source-scoped null-signature statement match records. Pause and $15 fee statements remain an intact message quote. The recorded $500 parameter explicitly does not alone establish eligibility. |
| 18 | Valid PASS | Jessica Lee/$450, repeat tier, five orders/$1,200 LTV, FedEx `794918`, dates, and `J. Lee` notation match sources. Repeat/LTV/`vip_concede_max_cents` citations remain present with the eligibility qualification. Prior policy-applicability false positive does not recur. |
| 19 | Valid PASS | Samuel Jenkins/$550, new tier, one order/$550 LTV, UPS `1Z99919`, August 15 shipment/August 18 delivery, and `S. Jenkins` notation match records. Required tracking/signature/AVS references are present without claiming verified identity or authorization. |
| 20 | Valid PASS | Olivia Moore/$45, new tier, one order/$45 LTV, USPS `940020`, and August 16 shipment/August 19 delivery match sources. `Delivered in Mailbox` is neutrally labeled as a signature or delivery notation; required tracking, delivered, and USPS references are present. |

The `signature or delivery notation` label accurately accommodates both named carrier entries and the digital-delivery marker; it no longer labels every non-null legacy value exclusively as a signature.

## Fresh whole-graph case 03

Saved judge: valid PASS. Independent review: no concrete factual defect or citation omission observed.

Sarah Connor's identity/email, Phoenix billing and shipping address, $65 amount/LTV, new tier, one order, order creation on August 1, order status shipped, USPS tracking `940003`, carrier status delayed, and August 10 shipment timestamp match the fresh records. Null signature becomes only `No signature is recorded in the supplied delivery record`. No delivery timestamp is invented. The August 25 message and its `Where is my order?` subject are accurately quoted; required `940003`, delayed, and never delivered references are present. The non-delivery report stays attributed to that message.

The recommendation is prospective and does not invent merchant operational parameters or concession eligibility. An irrelevant VIP parameter is absent. Physical shipping fields have source support and date-only `shipping_date`; file-reference and policy-disclosure fields are null, and `files` is empty.

## Fresh whole-graph case 18

Saved judge: valid PASS. Independent review: no concrete factual defect or citation omission observed.

Jessica Lee's identity/email, San Francisco addresses, $450 disputed amount, repeat tier, five total orders, $1,200 LTV, FedEx tracking `794918`, August 10 shipment, August 13 delivery at 13:00 UTC, `J. Lee` notation, and all three card checks match the fresh source records. Empty communication records support the explicitly record-scoped absence statement. The recorded policy limit is correctly converted from 50000 cents to $500 and explicitly says that the limit alone does not establish eligibility. It does not turn the recommendation into a claim of policy authorization. Required repeat, LTV, and `vip_concede_max_cents` references are present. All optional file/disclosure fields are null and `files` is empty.

These are two observed fresh graph runs, including new model generation and final formatting; they do not establish a fresh twenty-case generation or live Stripe execution.

## Evidence limits

All reviewed reports retain raw model output separately. Final text is derived from records; this does not establish that unformatted model drafts are grounded or that retained model probabilities are calibrated. The factual source review and hash/readback checks were performed locally without new provider calls. Only this review document was written. No reviewed raw failure was edited or overridden, and this document does not claim universal evaluator accuracy from the passing subset.
