# Output grounding verification

Complete locally against the defined acceptance thresholds at code revision
**4371ebf**. No deployment, upload, publication, or submission occurred.

## Observed results

| Verification | Result |
|---|---|
| Full offline regression | 217 passed, 2 warnings; exit 0 |
| Fixed 20-case action / gate / EV checks | 20 / 20 / 20 |
| Final factual-output model judge | 19/20, all 20 responses valid; threshold >=18 |
| Explicit evaluator controls | 52/52 matched; 24 positive and 28 negative controls |
| Fresh complete-graph integration | Cases 03 and 18 both pass; exit 0 |
| Independent source review | All 20 final outputs reviewed; no unsupported factual claim identified |

The 20-case result applies the final formatter to the exact captured source records
and raw model drafts from ccd5616, then requests new judgments and observes the
approval hook again. It is **not fresh generation of 20 model drafts**. No model
prompt or provider request changed between that generation and the final formatter.
Separate fresh complete-graph cases exercise the final integration. Stripe action
tools are isolated from these evaluations.

[Machine-readable acceptance](proofs/output-grounding/final-acceptance.json) records
report hashes, criteria and counts. `python3 docs/proofs/output-grounding/aggregate-final.py`
returned exit 0 after validating complete unique coverage, source/control/test
hashes and thresholds. Replay shards a/b returned 0; shard c returned 1 because
it requires every case in that shard to pass. The combined fixed benchmark passes
its unchanged >=18/20 judge threshold. All three calibration processes returned 0.

Regression command:
`PYTHON_DOTENV_DISABLED=1 USE_GATEWAY_MCP=false .venv/bin/python -m pytest -q`
returned 0: 217 passed, 2 warnings in 21.89 seconds.
[Exact command, source hashes and log](proofs/output-grounding/4371ebf-tests.json).

## What changed

Intake -> four evidence collectors -> model strategy and draft -> source-link
validation and factual formatting -> owner approval -> executor/Stripe. Raw model
drafts remain available for diagnosis. Final narrative, owner summary and rationale
come from linked source records. Model action, probability, expected value and
evidence-strength estimates remain model assessments, not measured outcomes.

The formatter rejects missing, failed, conflicting or mismatched evidence records.
It preserves event identity when reporting dates, scopes missing-signature statements
to the records, distinguishes digital access from physical shipping, and quotes
communications without inventing customer authorship. Policy parameters do not
establish customer eligibility or pre-purchase policy disclosure. Current collectors
produce no uploaded artifacts or disclosure events, so those fields stay empty.
Oversized source text requires review instead of truncating into an unsupported claim.

The evaluator checks all final factual fields through four separate judgments:
reason/citations, broad grounding, claimed action effects, and absence/date/policy
premises. It validates typed responses, exact assertion/citation structure, word
limits, physical shipping fields and uploaded-file references. Provider and malformed
response errors fail closed. Currency/date equivalence does not change raw evidence.
See [evaluation commands](evals.md) and [Stripe evidence contract](decisions/0006-stripe-evidence-contract.md).

## Remaining evaluator error

Case 09 is a **raw evaluator failure**, retained in the 19/20 score. The broad judge
rejects a proposed concession for lacking a source rule explaining the decision.
That is an action recommendation, not an assertion of policy entitlement; the
narrative explicitly says the quoted parameter alone does not establish eligibility.
The judge also labels the $500 parameter unsupported while acknowledging that its
conversion from 50000 cents is correct. The separate premise judgment passes.

Independent reviews:
[cases 01–10](proofs/output-grounding/source-formatted-final-cases-01-10-review.md),
[cases 11–20 and fresh integrations](proofs/output-grounding/source-formatted-final-cases-11-20-review.md).
This is a documented residual false positive, not a score silently changed to pass.
The 52 controls cover known distinctions; they do not establish zero population error.

Earlier raw generation defects, false positives, ambiguous control inputs, expired
AWS login failures and sandbox connection failures remain in their original reports.
They are not represented as successful runs. Source-derived finalization replaced
repeated prompt-only tuning after the latter still produced factual defects.

## Local configuration and cost

The previously authorized local adoption now sets Sonnet 4.5 and non-streaming
inference in the ignored `.env`, including the same judge model. An isolated
constructor check observed the intended settings, exit 0, without a provider call.
Code fallback defaults and cloud configuration were not changed. The final provider
runs used those same explicit model/streaming values.

Captured verification token usage estimates **$36.058822** against the owner's
**$50 total cap**. [Usage ledger](proofs/evaluation-judge/usage-ledger.json) preserves
per-run usage. Some earlier interrupted/executor usage was not fully metered; the
captured estimate is not an AWS invoice or an exact total. Paid inference is stopped.

## Video and evidence boundaries

The [corrected local video](media/edit/submission-v3/final-cut/final-verification-prep/rebuttal-final-candidate.mp4)
is 3:32.688, 1080p30 H.264/AAC. Rendering and full decode returned 0. All seven
validation reveals and eight cuts passed sampled encoded-frame inspection.
[Media QA](media/edit/submission-v3/final-cut/final-verification-prep/qa/verification.json)
records hash `1cea12875e9d544d502b7a559faa374fa4873cafc64a2b7a0f62333429464a6c`.
The nine approved narration recordings remain unchanged.
The preserved 616db5e runtime demonstration uses synthetic merchant records,
sanitized Stripe TEST objects, local sessions and isolated SQLite. Seven graph
nodes ran once; owner approval interrupted with zero guarded calls. CLI choice 2
conceded, resume made one guarded call, and fresh Stripe readback returned `lost`
with `livemode=false`. This is a test concession, not a recovery or separate refund.
That recorded runtime is distinct from the final source-formatting verification.

[Official rules](https://agentsforhumans.devpost.com/rules), checked September 14,
allow up to five minutes and accept slides, screen recordings and voiceover. They
require a working demonstration, the problem/audience/why pitch, English or a
translation, and public YouTube/Vimeo hosting. Local media preparation does not
establish hosting or submission. Independent listening and owner acceptance of the
exact final movie remain separate from technical media QA.

Phone delivery, production Stripe submission, cloud deployment, real merchant
outcomes and submitted state are not established by this work. Original video
SHA256 remains `9c18864f3e1748d26891b13eb9f7a42a0ab4924b17353dd46112b7a54e271768`.
Unrelated README/preflight/Devpost/architecture work and the orders fixture are preserved.
