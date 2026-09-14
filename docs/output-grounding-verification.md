# Output grounding repair

The e54a489 benchmark rerun passed its original thresholds (19/20 narrative,
20/20 action, gate selection, and EV sign), but a separate Stripe-test input
produced unsupported owner instructions and nonexistent attachment filenames.
The original evaluator only scored narrative prose.

Impact: evidence collectors -> strategy/rationale/owner summary -> drafter packet
-> approval notification and executor -> Stripe. The repair applies grounding
instructions at every agent, rejects attachment references the collectors did
not produce, and expands the evaluator to all consumer-facing generated text.
The narrative-only length/reason/citation checks and original thresholds stay.

Verification sequence: offline regressions; replay the captured bad output
against the expanded judge; full 20-case Bedrock benchmark; isolated real
Strands pause/resume with a Stripe test dispute. Record the current revision,
report names, and observed results below. Preserve the original recording and
all older evaluation reports. No deployment or publication is part of this fix.

Recovery: changes are isolated on codex/output-grounding, based on e54a489.
Shared uncommitted preflight work is untouched. Test-mode provider objects are
retained as evidence. A failed check prevents a completion or demo-success claim.

Current state: implementation and verification in progress. Do not label the
expanded evaluator accurate yet: its live controls currently expose false
positives. No new Stripe payload disclosure or Sonnet access is assumed.

## Observed verification

- e54a489 original rubric rerun: action 20/20, gate 20/20, narrative 19/20,
  EV sign 20/20, exit 0. This scored narrative, not complete output.
- eb83ad5 complete-output run: action 19/20, gate 19/20, judge 16/20,
  EV sign 20/20, exit 1. Full inputs and outputs are preserved in
  evals/results/2026-09-14-eb83ad5-full.json and its Markdown companion.
- Return rule follow-up: targeted cases 08/09/14 produced correct actions and
  gates (3/3). Only 1/3 judge checks passed; the report is preserved as
  2026-09-14-output-targeted-v4. The returned-item case incorrectly attributed
  application decision logic to merchant policy. The duplicate case was a
  judge false positive: its required IDs appeared in an attributed quote.
- Offline suite: PYTHON_DOTENV_DISABLED=1 USE_GATEWAY_MCP=false
  .venv/bin/python -m pytest -q -> 107 passed, 2 deprecation warnings, exit 0.
  The final evaluator model override and metadata changes were separately
  checked with tests/test_evals.py -> 29 passed, exit 0.
- Live local eb83ad5 test reached a Strands interrupt with all seven graph nodes
  executing once and zero guarded financial tool calls. Developer chose hold;
  Stripe readback remained needs_response, livemode=false, zero guarded calls.
  Phone delivery and deployment were not exercised.

## Adjudication corrections

Case 08 had a real action defect: a returned-item report and no earlier return
request could activate conflicting rules. Reported returns now take precedence.
Case 09's judge cited a false positive about scoped absence, but the actual
rationale also said 12 prior orders instead of the supplied 12 total orders.
Case 14's first output assigned customer authorship without a sender field;
its later quoted-ID citation failure was an evaluator false positive.
Case 18's judge incorrectly treated a repeat/VIP policy field name as a VIP-only
rule, while the output also used insufficiently prospective concession wording.
Original report verdicts remain intact; these observations do not overwrite scores.

The live Stripe test dispute actually supplied a $15 fee and $355 net debit in
balance_transactions. The compact recorder omitted those fields, so the initial
unsupported-fee diagnosis was wrong. Full capture now retains the dispute and
model-visible messages. Historical replay with abbreviated current facts cannot
establish fee grounding; controls now use explicit synthetic mutations and assert
each expected criterion, rather than accepting a failure for any reason.

Current Haiku judge controls still reject simple dollar/cents equivalence and
misread quoted citations. A separate, narrowly scoped Sonnet judge access proposal
is prepared in the main checkout under docs/proofs/evaluation-judge; it has not
been applied. BEDROCK_JUDGE_MODEL_ID can select a judge independently of the
application model, and reports retain judge model ID and token usage. The latest
implementation still needs a complete run with a judge that passes these controls.


## Latest checkpoint

Revision 5552395 completed the 20-case benchmark: action 20/20, gate 20/20,
EV sign 20/20, Haiku judge 13/20, exit 1. Results and complete source/output
records are preserved in evals/results/2026-09-14-5552395-full.{md,json}.
The action regression is repaired. The grounding work is not complete.

Independent review found false-positive explanations alongside actual errors:
prior-versus-total counts, unsupported receipt/authorization implications,
undocumented agreement compliance, and invented fulfillment/payment processing
claims. Passing Haiku verdicts also missed authorization implications in owner
summaries. No manually adjusted passing score is claimed. The saved scenario
description is broader than agent-visible tool records and must not be used to
justify claims the agent could not ground in retrieved evidence.

The shared Stripe serialization boundary now excludes client_secret and
receipt_url recursively. Expanded test responses included these unused fields;
they are unnecessary for dispute evidence. Fee and balance-transaction evidence
is retained. Regression checks cover nested objects/lists and preserve the input
object. Full offline suite after this repair: 107 passed, 2 warnings, exit 0.
The local response capture was sanitized and restricted to mode 0600. Eight
JSON files in this task's recorded executor sessions were checked by field-name
search; none contained client_secret or receipt_url. Earlier model invocations
used the old unfiltered tool response; no provider-side deletion or credential
rotation is claimed. The recording harness refuses an unsanitized revision.

Pending owner decisions in the current task: (1) narrowly scoped Sonnet evaluator
access and a $5 verification budget; (2) sanitized Stripe test-record use in the
Bedrock verification/final demo. Automatic approval review rejected the additional
full-payload disclosure; it was not retried. No new permission was applied.

Next: qualify the evaluator on all per-criterion positive/negative controls;
adjudicate saved outputs and repair remaining actual generation defects; repeat
required checks; record the sanitized test flow; integrate the isolated commits
without disturbing main's unrelated preflight work; finish the video and verify
it against the official rules. The 49.954-second opening prototype is in the main
checkout at docs/media/edit/submission-v3/opening-proof/. It is not a final demo.
