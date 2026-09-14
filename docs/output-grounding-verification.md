# Output grounding verification

Status: implemented locally; final model verification is pending. No deployment,
publication, video upload, or submission is claimed. The owner approved the
limited Sonnet evaluator policy and raised the total verification inference cap
to $8. Sanitized Stripe TEST records are authorized for verification and the demo.

## Current stopping point after the authorized $8 verification

The fbaf06f full run completed: action 20/20, gate 20/20, EV 20/20, output judge 9/20
(exit 1). Its overly restrictive authorship rubric caused false positives. The same
unchanged outputs were rejudged with d494d4e/grounded-v8: output judge 16/20,
other metrics 20/20, exit 1. Both raw reports and source hashes remain preserved.
The latest control run matched 21/23 expected results, exit 1. It missed a prior-order
count error and misclassified a bare recommendation as an unsupported outcome.

Manual review still finds a missing return-policy citation (case07), a 100x
lifetime-value error in rationale (case09), and promised inquiry-resolution/
escalation-prevention effects (cases16/17). Case09's latest grounding verdict
missed the monetary error, while the overall case failed citation scoring.
No manual score override is applied. The output-grounding gap remains open.

The prepared follow-up separates outcome extraction from the broad factual audit
in a third call, adds controls for cents/dollars and inquiry promises, and reinforces
the generation contract. It has not received paid model verification. A Sonnet
generation trial uses the existing BEDROCK_MODEL_ID setting; adoption is conditional
on observed results. Approval to raise the total inference cap from $8 to $15 is pending.
The current recorded token estimate is $6.945951; an interrupted run and executor
usage are not fully metered. A $1 planning reserve is not a verified upper bound.
No more model calls are authorized under this checkpoint without that decision.

Original-checkout integration through f48000c passed 143 offline tests, exit 0.
The final prepared follow-up will receive its own combined-suite result before
commit/integration. The Stripe test runtime proof remains the recorded 616db5e run.
Final video voice generation still awaits explicit Microsoft Edge TTS destination
approval; automatic approval review rejected that upload before execution.

## Impact and acceptance

Intake -> four evidence collectors -> strategy and owner summary -> evidence
packet -> approval notification and executor -> Stripe. All consumer-facing
factual fields require grounding. Raw sanitized tool records now reach strategy
and drafter and supply the evaluator's facts. Collector summaries and fixture-only
interpretations cannot establish facts. The graph waits for all prerequisites;
attachments the tools never produced are rejected before execution.

Acceptance: offline regressions; explicit positive/negative evaluator controls;
20 fixed synthetic cases (action >=18, gate 20, output judge >=18, EV sign 20);
separate local Strands suspension/resume and Stripe test readback. Scores must
come from executed checks. Manual adjudication never overwrites raw verdicts.
Small synthetic controls do not establish a population error rate.

Recovery: isolated branch codex/output-grounding starts at e54a489. Main's dirty
preflight work is preserved. Local commits provide recovery history; nothing is
pushed or deployed. Failed candidates and original recordings remain available.

## Latest observed results

| Revision/check | Action | Gate | Output judge | EV sign | Result |
|---|---:|---:|---:|---:|---|
| e54a489, original narrative-only rubric | 20/20 | 20/20 | 19/20 | 20/20 | Exit 0; does not cover sibling fields |
| eb83ad5, expanded output audit | 19/20 | 19/20 | 16/20 | 20/20 | Exit 1 |
| 5552395, Haiku judge | 20/20 | 20/20 | 13/20 | 20/20 | Exit 1 |
| 616db5e, Sonnet exact-source audit | 20/20 | 20/20 | 14/20 | 20/20 | Exit 1 |

Reports are retained under evals/results with those revision names. The 98a7313
run was stopped when review found fixture-only policy statements in judge inputs
(exit 130). The 970ff0a run encountered a Bedrock internalServerException after
one case (exit 1). Their logs/partial JSON are not complete benchmarks.

Offline suite after the latest implementation:
`PYTHON_DOTENV_DISABLED=1 USE_GATEWAY_MCP=false .venv/bin/python -m pytest -q`
-> 112 passed, two deprecation warnings, exit 0. A runtime-model factory check
also observed temperature=0.0 with a mocked model/session; no cloud runtime call.
The final source manifest and model results remain pending.

## Review of all 20 outputs from 616db5e

Reviewed against source_tool_records, not fixture_context:

| Case | Finding | Classification |
|---|---|---|
| 03 | Billing/shipping addresses are identical; judge rejects the billing label for the same destination | False positive |
| 10 | Order created_at is used as refund-status date; concession is said to guarantee a double refund | Generation defects |
| 11 | MSG-11 appears in optional communication field, but not narrative | Citation omission |
| 12 | Prior subscription acknowledgment/timing is treated as specific-charge authorization under unseen terms | Generation defect missed by judge |
| 14 | Neutral receipt with no sender/direction is called customer-authored | Generation defect missed by judge |
| 16 | Correctly attributed "Customer reports" is rejected in favor of "claims" | False positive |
| 19 | Tracking identifier absent from narrative; equivalent address-check wording also rejected | Citation omission plus false-positive AVS explanation |
| 20 | Prospective recommendations are rejected; carrier-recorded delivery is strengthened into personal possession by the judge | False positive |

No additional definite unsupported claims were found in the remaining outputs.
This manual review is separate from the raw 14/20 model score.

All 20 intake mocks accepted an order ID as a charge lookup argument. Production
Stripe lookup would not. The corrected mocks copy production tool metadata and
reject wrong dispute/charge/payment-intent IDs; one focused regression exercises
valid and invalid calls inside the actual evaluation patch scope. Intake guidance
now requires the charge/payment-intent ID returned by the dispute lookup.

The final generation repair keeps the same output fields/types and records its
schema-description decision in docs/decisions/0005-output-schema-grounding.md.
It separates creation/status dates, observations/authorization, source text/author,
and proposed action/guaranteed effects, and requires narrative tracking/ticket IDs.

## Evaluator controls and provenance

Haiku controls and early Sonnet controls failed. All historical outputs remain.
Sonnet v7 controls matched 13/13 expected per-criterion results, but expanded v8
matched only 17/20: neutral receipt authorship and promised fee/retention effects
were missed. A passing verdict for the wrong criterion is not a passing control.
Final expanded controls and benchmark must be observed before an accuracy claim.

The evaluator separates narrative-only reason/citations from exact-source factual
fields. Canonical dollar formatting preserves value/precision. Word count and
unproduced-attachment failure are deterministic. Numeric probability/evidence-
strength assessments are not calibrated facts; action and EV have separate checks.
Every factual rationale, owner summary, customer tier, and packet field is audited.
Malformed/unavailable judge responses fail. There is no keyword success override.

Reports retain source hashes captured before inference, raw inputs/outputs,
generation/judge usage, rejected packets, model IDs, and completed markers. A
rejected packet cannot reach the normal executor. Existing report paths are refused.
Case07's ambiguous "no return" citation was corrected to absence of communications
in supplied merchant records; action/gate labels and thresholds did not change.

## Local runtime and media evidence

The final recorded 616db5e run is in the main checkout at
`docs/media/edit/submission-v3/final-verified-run/`. It uses synthetic merchant
records, sanitized Stripe TEST objects, local FileSessionManager, and an isolated
SQLite copy. Seven graph nodes executed once. Strands interrupted at owner approval
with zero guarded calls and Stripe needs_response. Developer CLI response 2 selected
concession; resume made exactly one guarded call. Fresh Stripe readback returned
lost and livemode=false; recorder assertions passed, exit 0. Lost here means the
test dispute was conceded, not won or recovered. No separate refund is claimed.
The recorded output passed the Sonnet exact-source judge and attachment check.

Earlier fee-avoidance/relationship-preservation candidates were held with zero
action calls and are retained under candidate-98a7313-held and candidate-970ff0a-held.
The original Stripe test record did include a $15 fee; an earlier abbreviated
capture omitted it. Claiming that fee was invented was incorrect. Claiming that
concession avoids an already-incurred fee remains unsupported.

Stripe serialization recursively removes client_secret and receipt_url while
preserving fee evidence. Regression checks preserve source objects and cover nested
lists/objects. Earlier model calls used the old unfiltered payload; no provider-side
deletion or rotation is claimed. The recorder refuses unsanitized source revisions.

Phone delivery, cloud deployment, real merchant outcomes, and production Stripe
submission remain unverified. The nine-scene storyboard preserves actual CLI/test
readback and labels edited playback. Final video export awaits final scores and
explicit Microsoft Edge TTS approval for the prepared narration. The original
video remains intact; local files are not a public hackathon submission.

## Next actions

Finish final controls and the stricter 20-case run within the approved cap;
review new failures against exact records; update this checkpoint and cost ledger;
integrate verified local commits while preserving main's unrelated dirty work;
run the combined suite; render and inspect the final video after narration approval.
