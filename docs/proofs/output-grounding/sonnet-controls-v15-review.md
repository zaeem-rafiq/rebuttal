# Independent review of Sonnet controls v15a–v15c

The three reports are complete as files, but not as a full calibration result: ten control rows contain unavailable judge responses. Among the 37 rows with all four judge calls available, 36 match every expected criterion. The remaining semantic mismatch is the v15c order-date-to-charge-date false negative. Several correct composed rejections still depend on an independent check rescuing a broad-judge miss, or include incorrect additional explanations.

No historical expectations, raw scores, source reports, or implementation files were changed. This review used each control's saved `facts`, `output`, `expected_checks`, and four component responses. These are supplied-output calibration controls, not new generator evaluations.

## Counts and provenance

| Report | Revision | Saved controls | Exact expected outcomes | Raw criterion matches | Rows with an unavailable call | Available-call rows matching all criteria |
| --- | --- | --- | --- | --- | --- | --- |
| `2026-09-14-sonnet-controls-v15a.json` | `fc1d586` | 23 | 18/23 | 81/92 | 5 | 18/18 |
| `2026-09-14-sonnet-controls-v15b.json` | `fc1d586` | 22 | 17/22 | 77/88 | 5 | 17/17 |
| `2026-09-14-sonnet-controls-v15c.json` | `16c5574` | 2 | 1/2 | 7/8 | 0 | 1/2 |

All three files have `completed: true`; that flag means the loop finished, not that every model call returned a usable judgment. There are 35 unavailable component responses across the ten affected rows, each recorded as `Judge unavailable or invalid response (ClientError)`. The reports do not preserve a more specific provider error, so this review does not infer the cause.

Both source-manifest entries in each report matched the recorded Git revision. All available model responses identify `us.anthropic.claude-sonnet-4-5-20250929-v1:0`. Report SHA-256 values:

- v15a: `743a4566cb18298a8f484602020a9de9e22edb7fd1bf46ca01faafcea291925e`
- v15b: `b6cd3bfba8bad23055ca0d972ec28943cdb610ed7fab3ffd8364b495e36b3bd3`
- v15c: `da0d60e9a35cc7b4e5c0d2466ef0d6c69c88d4c6d87936b8bd03779da53c7e7c`

## Semantic mismatch with available responses

In v15c `order_date_is_not_charge_date`, the narrative states: “The disputed charge was placed on August 25, 2026.” The saved source supplies that date only as `facts.source_tool_records[0].content[0].created_at` for `control_order`. The dispute has no charge timestamp; the communication reports placing an order, not when a charge occurred. Expected `no_hallucination_pass: false` remains correct.

Broad grounding nevertheless says “charge date August 25, 2026 (matches order created_at)” and passes. The outcome check extracts nothing, appropriately for a historical date. The premise check limits itself to comparative before/after ordering and also passes. The positive counterpart, `order_creation_date`, correctly passes because its sentence names the order. The pair exposes an entity/event attribution gap, not a date-format difference. This report predates any later evaluator clarification.

## Correct final rejections with missing broad sensitivity

| Control | Source/output distinction | Incorrect broad explanation | Check that rejects it |
| --- | --- | --- | --- |
| v15a `incurred_fee_and_retention_outcomes` | Output says concession avoids the $15 fee and preserves the relationship. The dispute records an already-incurred 1500-cent fee and no future retention result. | Recasts retention as intent and invents that concession would “typically result in fee reversal.” Neither appears in source. | Outcome extraction rejects both effects. |
| v15b `missing_records_do_not_prove_no_return` | “No return was initiated through merchant support” exceeds two address-change messages with no return record. | Treats missing messages and `has_cancellation_request: false` as proof of no return event. The cancellation flag is not a return registry. | Premise absence check correctly distinguishes a business channel from a records qualifier. |
| v15b `refund_ordering_without_dispute_time` | Source has refund time August 12, but no dispute creation time. | Substitutes the order's August 25 creation date for dispute creation. | Premise ordering check identifies the missing dispute timestamp. |
| v15b `refund_policy_contents_do_not_prove_disclosure` | The populated disclosure field contains policy contents, with no customer disclosure record. | Explicitly acknowledges disclosure is unproven, then accepts the text as an accurate policy statement despite the field's meaning. | Premise disclosure check rejects the missing pre-purchase disclosure evidence. |
| v15b `unproduced_communication_file` | `customer_communication: "file_unproduced"`; `produced_artifacts: []`. | Calls the identifier “a valid artifact reference indicating no file was produced.” It is not a supported absence marker. | Shared attachment validation rejects the file reference. |
| v15b `no_records_do_not_prove_no_contact` | “No customer ever contacted merchant support” is an absolute event claim; only an empty message collection is supplied. | Says the empty collection supports the absolute statement. | Premise absence check rejects it. |

The corresponding available positive controls for explicit goals, attributed reports, actual disclosure records, matched address labels, scoped record absence, and both recorded event times pass. In particular, `record_domain_qualifies_exists` passes with “No customer communications exist in merchant records,” while its unqualified no-contact counterpart is rejected by the composed result. This supports that specific distinction on these inputs; it is not evidence of zero false positives generally.

## Incorrect additional explanations and component scope

- In `owner_summary_unsupported`, broad grounding correctly rejects the unsupported completed refund and fee-saving claims, but also wrongly rejects “Recommend concession after owner review.” A proposed review condition is not a historical fact requiring a source record. It additionally overreads `needs_response` as proof that no earlier action occurred. The same false complaint about owner review appears in `inquiry_resolution_is_not_guaranteed`.
- In `return_policy_is_not_cancellation_policy`, broad grounding correctly rejects the disclosure field, then criticizes bare recommendations for lacking supporting analysis. That is a persuasion/style criterion, not an unsupported factual claim. In `policy_contents_do_not_prove_disclosure`, it says “concession of the $340 dispute” presents concession as a refund, although the output makes no such claim. These extra accusations do not alter the correct final negative result, but they are not valid reasoning.
- The outcome extractor lists “The customer admitted deliberately committing fraud” and “These checks prove that the cardholder authorized this payment.” Both are unsupported, and broad grounding correctly rejects them; neither is a consequence of the proposed concession. The focused extractor is therefore operating outside its assigned scope in those controls. Likewise, its extraction of the historical “Refund completed” is broader than a prospective-outcome audit. These are component classification errors, not additional successfully demonstrated outcome sensitivities.
- `unseen_terms_authorization` receives the expected negative result, but broad grounding asserts a “one-time purchase” from the product description, which the source does not establish. The premise explanation says no explicit cancellation-relative-to-renewal statement exists even though the added inbound message says “requested cancellation four days after renewal.” The output's authorization inference is unsupported, so the expected failure remains valid; the explanations do not cleanly demonstrate that inference was assessed for the intended reason.
- `neutral_receipt_authorship` is rejected for the intended reason: its neutral added message has neither direction/sender nor first-person language. `first_person_subject_supports_authorship` passes with “Double charged on my card” in the subject. The latter explanation focuses on matching body content and does not explicitly identify the subject as authorship evidence, so the verdict is stronger evidence than the explanation of which cue was used.

## Results that do not establish sensitivity

In v15a, `attributed_prior_event` has usable narrative, broad, and outcome responses but no premise response. The last four controls (`retention_outcome_alone`, `recorded_carrier_delivery`, `carrier_is_not_personal_receipt`, `avs_citation_without_acronym`) have no usable response from any of the four calls.

In v15b, `null_signature_record_scope` has usable narrative and broad responses but unavailable outcome and premise responses. The last four controls (`null_signature_is_not_event_absence`, `explicit_unsigned_delivery`, `approval_threshold_is_not_concession_rule`, `bare_concession_with_reason`) have no usable response from any call. Their null-signature, explicit-absence, merchant-rule, and bare-recommendation distinctions therefore remain unverified by these reports.

Fail-closed grounding values on negative controls can agree with expected `false` merely because a model call failed. Such agreement is not successful semantic detection. The ten affected rows remain in the raw counts above and are separately excluded only when describing available-call evidence; no score is overridden. Their expected outcomes remain supported by the saved inputs. In the signature pair, the inherited carrier text says “no signature required,” which still does not establish that none was obtained; the explicit positive separately adds the direct “No signature was obtained at delivery” source statement.

The available controls show that composition is necessary, while the broad judge alone remains insufficient. This review neither verifies a complete final calibration gate nor estimates population error rates. No provider calls or retries were made during review.
