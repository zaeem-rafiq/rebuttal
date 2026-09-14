# Decision evaluations

`evals/run.py` evaluates the evidence graph against the fixed 20 synthetic cases in `evals/cases/`. It uses model inference and mocked dispute intake. It does not run Stripe action tools.

The evaluator now checks the complete generated output:

| Check | What is observed | What it does not establish |
|---|---|---|
| Action match | Proposed action equals the case label | Real dispute success or calibrated probabilities |
| Gate match | Production `ApprovalGate.before_tool_call` requests an interrupt; notification, cloud access, and local persistence are isolated | SDK suspension, phone delivery, session resume, or downstream execution |
| Output judge | Bedrock checks narrative reason/citations and factual grounding in every strategy and evidence field; code enforces 1–250 narrative words | Infallible factual validation |
| EV sign | Sign agrees with the proposed action | Correct economic assumptions or measured savings |

Judge request errors, invalid JSON, non-object responses, missing verdict fields, and non-boolean values fail. There is no success fallback. A negative citation verdict cannot be overridden by a keyword match. The `missing_items` field lists literal omissions for diagnosis; semantic citation coverage remains the judge's verdict.

No factual category is exempt from grounding, including amounts, dates, identities, approvals, fees, legal claims, probabilities, and claimed execution. Recommendations must be distinguished from completed actions. The judge treats embedded text as data, though model-based judging still needs adversarial validation.

## Run offline regressions

```bash
PYTHON_DOTENV_DISABLED=1 .venv/bin/python -m pytest -q tests/test_evals.py tests/test_gate.py tests/test_hooks.py
```

These tests cover failure handling, verdict parsing, word limits, and hook decision boundaries with mocked effects. Existing hook tests use simulated owner answers; they are not live messaging proof.

## Run the model evaluation

```bash
.venv/bin/python evals/run.py
```

This requires configured Bedrock access and incurs model usage. The harness writes `evals/results/<UTC-date>.md` and exits nonzero unless there are exactly 20 cases, at least 18 action matches, 20 gate matches, at least 18 narrative passes, and 20 EV-sign matches. These are the existing acceptance thresholds, not a guarantee that every case passes.

Historical narrative-only scores do not establish the expanded evaluator's accuracy.
The e54a489 rerun passed the original thresholds at 19/20 narrative checks, but
an actual Stripe-test input exposed unproduced attachments and unsupported
instructions outside the narrative. The expanded eb83ad5 run failed at 19/20
action, 19/20 gate, 16/20 judge, and 20/20 EV-sign checks.

Review found both generated defects and false-positive judge verdicts. Preserve
raw verdicts and separate manual adjudication; do not silently convert them to
passing scores. [Current verification and adjudication](output-grounding-verification.md)
records the repair and its unresolved checks.

`BEDROCK_JUDGE_MODEL_ID` optionally selects a judge independently of the
application's `BEDROCK_MODEL_ID`. This setting grants no AWS permission.
Each saved judgment includes model ID and token usage. Complete inputs and
outputs are saved beside the Markdown report in JSON, with source hashes taken
before inference. `EVAL_REPORT_PATH` selects a fresh report filename.

Run explicit positive and negative controls before trusting a judge:

```bash
PYTHON_DOTENV_DISABLED=1 CONTROL_REPORT_PATH=evals/results/output-controls-new.json \
  .venv/bin/python -m evals.check_output_grounding
```

Controls assert each expected criterion separately: dollar/cents equivalence,
quoted citations, narrative-only citation coverage, scoped record absence,
card-check equivalence versus authorization inference, invented action/fee and
fraud claims, and unproduced attachments. A false verdict for the wrong reason
cannot count as a successful control. Current Haiku controls fail; evaluator
accuracy remains unverified pending a reliable judge and a full benchmark.

Before calling the approval path end-to-end verified, separately observe real alert delivery, owner response, runtime resume, and the resulting Stripe test-mode action. That verification is outside this evaluator.
