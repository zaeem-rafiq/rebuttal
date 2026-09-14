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

Current state: implementation and verification in progress.
