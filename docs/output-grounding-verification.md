# Output grounding verification

Status: implemented locally at 22b0178, not fully verified. No push, deployment,
publication, upload, or submission has occurred.

## Observed evidence

- Full Sonnet generation trial at 25bfc30: 20 fixed synthetic cases completed;
  action 20/20, approval gate 20/20, EV sign 20/20, output judge 17/20 (minimum 18).
  Exit 1. Raw report: evals/results/2026-09-14-sonnet-generation-trial.json.
- Every output field was reviewed against exact source_tool_records. Defects were
  found in cases 09, 10, 13, 16, 17; case 15 was a judge authorship false positive.
  See docs/proofs/output-grounding/sonnet-trial-review.md. Manual findings do not
  replace the preserved raw score.
- Controls v11: 26/26 expectations and 104/104 criteria matched, exit 0. Expanded
  controls v12 at a14c5cb: 30/33 expectations and 129/132 criteria matched, exit 1.
  Three false negatives remained: unqualified event absence, refund chronology
  without a dispute timestamp, and return terms mislabeled as cancellation policy.
  All four new positive counterparts passed. Independent reviews are preserved
  under docs/proofs/output-grounding/sonnet-controls-v11-review.md and
  sonnet-controls-v12-review.md.
- Fresh offline regression at 22b0178: 157 passed, 2 warnings, 21.20 seconds, exit 0.
  Command and source hashes: docs/proofs/output-grounding/22b0178-verification.json.
- The latest evaluator repair at 22b0178 has not made any provider calls. The
  attempted 12-control follow-up was rejected before launch by approval review.
  No v13 result or fresh full 20-case final-generation result exists.

## Repairs and affected flow

Intake -> four collectors -> strategy and owner summary -> evidence packet ->
approval hook -> executor and Stripe. Exact sanitized tool records reach the
strategy, drafter, and evaluator; summaries and fixture interpretations cannot
establish facts. The graph waits for every collector; unproduced attachments fail
before execution. Source sanitation removes client_secret and receipt_url.

Generator repairs remove contradictory mandates about inquiry resolution,
refund-before-dispute chronology, forced VIP labels, and policy-only concessions.
Negative findings require explicit record scope. Event order needs both event times
or an explicit source statement. Policy fields require the correct policy type.
Messages support attributed reports without independently proving reported events.

The evaluator retains separate narrative requirements and broad grounding checks.
Its existing third call now extracts supported and unsupported relationship claims:
action effects, event absence, event order, and policy-field meaning. Missing premises
use null support. Exact output quotes and every source citation are validated;
chronology can cite two timestamps. Citation existence does not prove semantic
entailment, which remains an evaluated model responsibility. Goals, scoped record
absence, and attributed reports have explicit positive treatment. There are now
34 controls, including an attributed refund-nonreceipt report. Named subsets are
recorded, unknown names fail, and completed usage persists if a later call fails.

The report rubric is grounded-v11. Diagnostic outcome_* keys became support_*
keys; Python consumers and tests were updated. Product types, field names, action
labels, and benchmark thresholds remain unchanged. Model defaults remain Haiku;
Sonnet was used only through explicit evaluation environment settings, with
non-streaming InvokeModel and no additional IAM expansion.

## Verification and budget gate

Required: offline regressions; all explicit controls; a fresh fixed 20-case final
build evaluation with action >=18, gate 20, output judge >=18, and EV sign 20.
Older outputs and rejudgments cannot certify the repaired generator.

Captured token-derived estimate is $12.843357. Some interrupted and executor usage
is unmetered; the $1 planning reserve is not an invoice or a verified upper bound.
The saved conversation records a $15 cap approval. Automatic approval review
nevertheless rejected further paid calls because it accepts only the earlier $8
cap from its trusted context. Two attempts were rejected before inference, the
second after checking the saved approval. Do not retry through another execution
path. A new explicit $20 total-cap question is pending for controls and one fresh
full run. No further inference is permitted until that approval resolves the gate.

## Runtime and video

The preserved 616db5e local runtime recording uses synthetic merchant records,
sanitized Stripe TEST objects, a local session manager, and isolated SQLite.
Seven graph nodes executed once. Owner approval interrupted with needs_response
and zero guarded calls. CLI choice 2 conceded; resume made one guarded call.
Fresh Stripe readback returned lost with livemode=false. Recorder assertions and
the source-based output judge passed. Lost means test concession, not recovery or
a win; no separate refund is claimed. This is distinct from later generator and
evaluator revisions.

All nine approved Microsoft Edge TTS tracks are generated, hashes verified, and
fully decoded. The padded cut is 212.667 seconds. Eight ready scenes rendered and
decoded successfully, with reveal/cut frames reviewed. A complete local REVIEW
CANDIDATE is being assembled using the observed failed trial, current offline
checks, and explicit final-model-verification-pending labels. It is not submission
ready; full decode, visual review, and owner listening remain to be recorded.

Original video remains intact with SHA-256
9c18864f3e1748d26891b13eb9f7a42a0ab4924b17353dd46112b7a54e271768.
Phone delivery, cloud deployment, production Stripe submission, real merchant
outcomes, and public video/submission remain unverified. Rules reread September 14:
https://agentsforhumans.devpost.com/rules requires a video <=5 minutes, a working
demonstration plus problem/audience/why pitch, English or translation, and public
YouTube/Vimeo hosting. Local preparation does not establish public submission.

## Preservation

Task commits are local on main. Unrelated preflight, README, Devpost, architecture,
and fixture work remains preserved. Failed, interrupted, and rejudged artifacts
remain in evals/results. The separate codex/output-grounding worktree retains the
original repair history. Never reset or discard unrelated working-tree changes.
