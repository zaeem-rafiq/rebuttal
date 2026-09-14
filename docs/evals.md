# Decision evaluations

`evals/run.py` evaluates the evidence graph against the fixed 20 synthetic cases in `evals/cases/`. It uses model inference and mocked dispute intake. It does not run Stripe action tools.

The current rubric is **grounded-v2**:

| Check | What is observed | What it does not establish |
|---|---|---|
| Action match | Proposed action equals the case label | Real dispute success or calibrated probabilities |
| Gate match | Production `ApprovalGate.before_tool_call` requests an interrupt; notification, cloud access, and local persistence are isolated | SDK suspension, phone delivery, session resume, or downstream execution |
| Narrative judge | Bedrock judges reason coverage, required citations, and all factual assertions against case facts; code enforces 1–250 words | Infallible factual validation |
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

The September 7 report remains unchanged as a historical artifact from the earlier rubric. Its results must not be attributed to grounded-v2. **Current grounded-v2 model evaluation: completed September 14, 2026; FAIL (exit 1).** After the owner-approved streaming permission repair, all 20 cases ran: 20 action matches, 20 gate matches, 4 narrative passes, and 20 EV-sign matches. See [results](../evals/results/2026-09-14.md) and [IAM repair evidence](proofs/bedrock-streaming/README.md).

The narrative failures include unsupported fee and execution claims. They also include judge mistakes: case_06 incorrectly treats $450 and 45,000 cents as contradictory, and case_04 misreads a Z timestamp. Adjudicate these verdicts and reconcile the agent's seeded facts with the judge's facts before treating the score as a calibrated measure. No labels or thresholds were changed to improve this result.

Before calling the approval path end-to-end verified, separately observe real alert delivery, owner response, runtime resume, and the resulting Stripe test-mode action. That verification is outside this evaluator.
