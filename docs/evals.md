# Decision evaluations

`evals/run.py` evaluates the evidence graph against the fixed 20 synthetic cases in `evals/cases/`. It uses model inference and mocked dispute intake. It does not run Stripe action tools.

The graph retains raw model drafts, then derives final factual text from linked source records. Model action, probability, expected value, and evidence-strength assessments remain separate. Identity mismatches, invalid attachments, and oversized final text fail before execution.

The evaluator checks the complete final output:

| Check | What is observed | What it does not establish |
|---|---|---|
| Action match | Proposed action equals the case label | Real dispute success or calibrated probabilities |
| Gate match | Production `ApprovalGate.before_tool_call` requests an interrupt; notification, cloud access, and local persistence are isolated | SDK suspension, phone delivery, session resume, or downstream execution |
| Output judge | Four separate Bedrock calls check narrative reason/citations, broad factual grounding in every strategy/evidence field, asserted outcomes, and absence/order/disclosure premises; code enforces 1–250 narrative words and rejects unproduced attachments | Infallible factual validation |
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
records the repair, raw verdicts, and source-review adjudication.

`BEDROCK_JUDGE_MODEL_ID` optionally selects a judge independently of the
application's `BEDROCK_MODEL_ID`. This setting grants no AWS permission.
Each saved judgment includes model ID and token usage. Complete inputs and
outputs are saved beside the Markdown report in JSON, with source hashes taken
before inference. `EVAL_REPORT_PATH` selects a fresh report filename.

Rubric grounded-v17 isolates citation scoring from supporting fields so an order
reference outside the narrative cannot satisfy it. The grounding judge receives
structured facts and identical canonical dollar formatting on both sides;
original output stays unchanged in reports. The production attachment validator
can force failure even when the model misses an invalid file reference. Raw
tool records forwarded to strategy/drafter are the judge's factual input.
Normalized fixture context is saved separately and cannot ground a model claim.
Numeric estimates remain assessments, not measured
win rates or permission to invent supporting facts.
Factual text fields are presented individually by path. Numeric estimates,
evidence-strength assessments, and the selected action are excluded from this
text audit. Action and EV sign retain their separate checks; probability and
evidence strength are internal assessments with no calibration claim. Customer
tier, rationale, owner summary, and every evidence field remain in the audit.

Run explicit positive and negative controls before trusting a judge:

```bash
PYTHON_DOTENV_DISABLED=1 CONTROL_REPORT_PATH=evals/results/output-controls-new.json \
  .venv/bin/python -m evals.check_output_grounding
```

Controls assert each expected criterion separately: dollar/cents equivalence,
quoted citations, narrative-only citation coverage, scoped record absence,
card-check equivalence versus authorization inference, invented action/fee and
fraud claims, and unproduced attachments. A false verdict for the wrong reason
cannot count as a successful control. Historical Haiku and early Sonnet controls
failed. Revised controls additionally check total versus prior orders and owner
summary authorization inferences. Review the latest saved control run and full
benchmark before making an accuracy claim; small controls do not establish a
population error rate.

JSON reports persist after each case with a `completed` marker, including rejected
packets and raw records when output validation fails. A partial report is not a
completed benchmark. Existing paths are refused before inference. Case 07's
ambiguous "no return" reference now asks for the absence of communications in
the supplied merchant records; its action/gate labels and thresholds are unchanged.

Before calling the approval path end-to-end verified, separately observe real alert delivery, owner response, runtime resume, and the resulting Stripe test-mode action. That verification is outside this evaluator.

Synthetic intake tools use production tool metadata and reject unknown dispute,
charge, or payment-intent IDs. An order ID cannot satisfy a charge lookup.

The outcome audit extracts an exact output field/quote and source path/quote (or
null). Unsupported or malformed assertions fail regardless of the broad verdict.
Source citation existence is checked in code; semantic support and extraction
remain model judgments. All four raw responses and summed usage are preserved. The premise check fails closed unless each independent absence, event-date/order, and policy-premise/disclosure verdict is a literal boolean true. Digital access records cannot populate physical shipping fields. Invalid response structure cannot count as a successful negative control. See the current verification report for live acceptance; offline tests alone do not validate a model rubric.

## Final source-formatting verification

The final formatter is verified against the exact source records and retained model drafts from all 20 ccd5616 cases. `docs/proofs/output-grounding/render-captured.py` applies the current formatter, observes the approval hook again, and requests new judgments. This is not new generation of 20 model drafts. Separate fresh complete-graph cases exercise the final integration. `docs/proofs/output-grounding/aggregate-final.py` checks complete, unique coverage, exact source hashes, the unchanged acceptance thresholds, 52 calibration controls, and the fresh graph results without changing any verdict. The authoritative result is `docs/proofs/output-grounding/final-acceptance.json`.
