# Rebuttal: chargeback-defense prototype for Stripe merchants

Rebuttal is an AWS Agents for Humans hackathon prototype for small Stripe merchants. A Strands graph gathers evidence, proposes a fight, concession, or inquiry refund, and drafts an evidence packet. An approval hook requests human input for high-value, uncertain, and non-fight actions.

**Judge console:** https://main.dtrewze9hbzeb.amplifyapp.com

**Local demo video:** [rebuttal_demo_video.mp4](docs/media/rebuttal_demo_video.mp4)

**Submission draft:** [docs/submission.md](docs/submission.md)

These links identify the intended judging surfaces; their current availability and the final submission state are not established by this README.

## Implemented flow and evidence boundaries

1. Stripe test-mode webhook ingestion invokes the AgentCore application.
2. The Strands graph runs intake, evidence investigation, strategy, and drafting nodes. Order, shipment, and communication evidence comes from seeded records through local SQLite tools or configured Gateway tools. Direct UPS/FedEx and Gmail adapters are not present in this checkout.
3. Model-generated structured outputs contain a proposed action, win-probability estimate, rationale, and evidence narrative. These estimates are not calibrated probabilities of real dispute outcomes.
4. The executor's `ApprovalGate` requests an interrupt when amount is at least $200, probability is in the inclusive 0.35–0.65 band, or the action is not `fight`.
5. Telegram alerts and inline replies are implemented. The legacy Twilio path remains and may also send SMS when configured. The helper's returned message identifier alone does not establish delivery. The webhook passes an owner reply to the runtime; current delivery and session resume require a separate live rehearsal.
6. Execution tools submit evidence, concede, or refund an inquiry using Stripe test keys. A test-mode `won` result does not demonstrate recovery of real merchant funds.
7. Case and audit records support the console. Memory and observability integrations are implemented; configuration and historical proof files are not fresh runtime verification.

![Architecture](docs/architecture.png)

The existing diagram/video may depict the earlier SMS-centered flow. The current channel description above is authoritative for this checkout; media refresh is separate work.

| Responsibility | Source |
|---|---|
| Evidence graph and model prompts | `agent/graph.py` |
| Seeded order, shipment, and communication tools | `agent/tools/evidence_tools.py` |
| Optional Gateway client | `agent/tools/gateway_client.py` |
| Approval policy and Telegram/Twilio alerts | `agent/hooks.py` |
| Executor and session handling | `agent/executor.py`, `agent/app.py` |
| Telegram and legacy SMS ingress | `infra/lambdas/twilio_webhook/app.py` |
| Stripe test-mode actions | `agent/tools/stripe_tools.py` |
| Outcome memory | `agent/tools/memory_tools.py` |

## Scripted scenarios

All three scenarios use synthetic merchant evidence and Stripe test-mode behavior.

| Scenario | Intended demonstration | Boundary |
|---|---|---|
| S1: $48 delivery dispute | Strong evidence leads to a fight without owner interruption | Test-mode outcome; no measured real win rate |
| S2: $340 dispute | Gate requests an owner decision before execution | Current Telegram delivery/resume needs live verification |
| S3: $129 inquiry | Proposed inquiry refund | Refund is a non-fight action and requires approval; fee savings are not measured |

The deadline sweep contains a silence-policy path. Therefore, this project does not claim that every high-value action always waits indefinitely for positive owner confirmation. See `agent/sweep.py` for that separate behavior.

## Evaluations

[evals/run.py](evals/run.py) evaluates 20 synthetic cases. It checks action agreement, the production hook's interrupt request with external effects mocked, a Bedrock narrative verdict, and EV sign. The gate metric does not exercise SDK suspension, Telegram delivery, session rehydration, or Stripe execution.

The revised `grounded-v2` narrative rubric requires support for every factual assertion. Judge errors, malformed responses, missing fields, and non-boolean verdicts fail. Required-citation failures cannot be overridden by keyword matches. An LLM verdict remains fallible and is not a guarantee of zero hallucinations.

The [September 7 report](evals/results/2026-09-07.md) is historical evidence from the earlier rubric, not a benchmark for the revised evaluator. Current grounded-v2 model results: **BLOCKED**. The September 14 run exited 1 because AWS denied `bedrock:InvokeModelWithResponseStream` for the configured Haiku inference profile. See [docs/evals.md](docs/evals.md) for checks and limitations.

## Local setup

Use Python 3.12+ and the repository's `requirements.txt`. The console has its own npm dependencies.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Use `.env.example` as the configuration reference and keep local values out of Git. Configured graph runs call Bedrock and can incur usage charges.

### Seed synthetic data locally

```bash
python scripts/seed_supabase.py --local-only --verify
```

### Run the evidence graph

```bash
USE_GATEWAY_MCP=false python scripts/run_local.py --scenario S1 --dry-run
```

This runs the evidence graph with Bedrock; it is not an offline acceptance test of the executor or approval delivery.

### Offline checks

```bash
PYTHON_DOTENV_DISABLED=1 python -m pytest -q tests/test_evals.py tests/test_gate.py tests/test_hooks.py
```

### Console

```bash
cd console
npm ci
npm run dev
```

Open http://localhost:3000. Data availability depends on console configuration; a rendered page alone does not prove the agent loop.

## Deployment and safety

Deployment entry points are `infra/template.yaml`, `agent/app.py`, and `scripts/deploy_amplify.py`. Deployment and webhook setup change external resources and are separate from local checks.

Stripe tools enforce test keys. Synthetic fixtures, model estimates, historical proof notes, live integrations, and actual merchant outcomes must remain labeled separately. This prototype has no demonstrated production win rate or measured merchant time savings.

## License

[MIT](LICENSE)
