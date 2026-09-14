# Sonnet controls v11 independent review

Reviewed the saved outputs, source facts, criterion expectations, and three judge responses in `evals/results/2026-09-14-sonnet-controls-v11.json`. This review made no provider calls and changed no scores. The report SHA-256 is `a368470bb3fe21928da3c81937389096b8cc24353a1d12f13750b457ced933a4`.

The saved model identifier is `us.anthropic.claude-sonnet-4-5-20250929-v1:0`. The current evaluator was inspected at repository revision `25bfc30`. The control JSON itself stores model IDs, supplied facts, outputs, verdicts, and usage, but does not embed a source-revision manifest.

## Observed result

All **26 composed controls** match their expected results across **104 of 104 individual criteria**: reason code, required narrative references, factual grounding, and word count. Ten controls expect every criterion to pass; sixteen expect one criterion to fail. The comparison used strict boolean identity, as the control runner does.

The composed grounding result requires the broad factual verdict, the shared deterministic attachment validator, and the separately extracted outcome assertions to pass. Narrative citation checks remain isolated from supporting fields. No unexpected criterion failure or acceptance was found in this saved control set.

## Limitations visible in the raw responses

| Control | Observed response | Assessment |
| --- | --- | --- |
| `retention_outcome_alone` | The broad judge accepts “Concession preserves the customer relationship” as an expected benefit. The outcome call extracts that exact claim with `support: null`. | Correct composed rejection. The records contain customer history, not evidence that concession preserves the relationship. The broad judge alone misses this unsupported effect. |
| `inquiry_resolution_is_not_guaranteed` | The broad judge accepts “The proposed refund resolves the inquiry and prevents escalation” as a goal. The outcome call extracts it with `support: null`. | Correct composed rejection. “Resolves” and “prevents” assert effects absent from the records; “proposed” does not qualify their certainty. |
| `unproduced_attachment` | The broad judge treats `unproduced-evidence.pdf` as a filename outside factual grounding. The deterministic attachment validator rejects it. | Correct composed rejection. The source envelope records `produced_artifacts: []`. |
| `incurred_fee_and_retention_outcomes` | The outcome call returns an empty list for “Concession avoids the $15 dispute fee and preserves the customer relationship.” The broad judge rejects both claims. | Correct composed rejection, but outcome extraction alone misses these effects. The recorded balance transaction already has `fee: 1500` and `net: -35500`; it does not establish fee avoidance or retention. |

The broad judge alone therefore remains insufficient for the targeted grounding contract. Composition caught the targeted defects in this execution, with different checks covering different misses.

## Correct verdict with an unreliable explanation

`unseen_terms_authorization` correctly fails, but its broad explanation says the added “Renewal question” message “lacks direction metadata.” The saved source actually contains `communications.content[0].messages[2].direction: "inbound"` and the first-person body “I agreed to subscription terms previously and requested cancellation four days after renewal.”

The explanation also infers that the ceramic-item order is a one-time purchase rather than a subscription. The supplied item description alone does not establish that billing distinction. These are errors in the evaluator explanation, not additional defects in the generated control text.

The defensible rejection is narrower: the output asserts that “this charge was authorized under the accepted subscription terms,” while the records contain neither the terms nor evidence authorizing that specific charge. A reported earlier agreement and cancellation timing do not supply those missing facts. The raw verdict and explanation remain preserved without an override.

## Scope of the evidence

This is a bounded control result, not a claim of zero false positives or false negatives across real disputes. Several instructions explicitly target previously observed error classes, and these controls are not an independent population sample. The successful composite score does not establish that every component judge is accurate, nor that every explanation is reliable. The new full benchmark requires a separate review of its generated outputs against the exact tool records visible to the agents.
