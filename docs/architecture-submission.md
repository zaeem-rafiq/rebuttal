# Submission architecture

[PNG attachment](architecture-submission.png) · [SVG vector export](architecture-submission.svg) · [Mermaid source](architecture-submission.mmd)

The diagram follows the current source and the [published 2:57 product demonstration](https://www.youtube.com/watch?v=ZlGc15UzTbU). It shows local investigation and recommendation, a real Telegram owner choice, the existing cloud callback, and the verified Stripe test-mode closure. It is a logical architecture, not a claim that every arrow was captured as a network trace.

## Read the diagram

The green section is the seven-node **AWS Strands Agents SDK** graph. Intake starts order and shipping lookup; the completed order lookup unlocks communications and customer history. Four completed evidence results are a logical fan-in, not an eighth agent. Strategy requires every investigator. Drafting requires both strategy and direct evidence context.

The orange section is the separate execution agent and its **ApprovalGate** hook. It requests an owner decision before guarded Stripe actions when the default amount, uncertainty, or non-fight conditions apply. The recorded $340 case generated a real Telegram alert, and the owner selected Concede on their physical phone. The source video captures the synchronized Telegram conversation, not a recording of the physical phone screen.

The blue section is the existing **Lambda / AgentCore reply path**, Stripe test API, and case-store/console result. On September 14 at 20:08 UTC, a fresh readback showed the same Stripe test dispute and Supabase dispute were `lost`, with an owner `concede_dispute` audit at 20:07 UTC. The local console displayed **CONCEDED · CLOSED** from the recorded terminal state and owner audit.

## Scope of the demonstrated run

- The console and generation pipeline ran locally. Generation used **Claude Sonnet 4.5 on Amazon Bedrock**, an isolated copy of synthetic merchant records, and real Stripe test reads.
- The test case was recovered into the case store before generation. Automatic cloud ingestion was not established by this take. The latest local graph and console repairs were not deployed.
- The real owner reply used the existing cloud integration. No simulated phone interface, fabricated reply, or synthetic success message was used.
- The separate Supabase decision row remained `pending`, and closure-memory metadata incorrectly labeled the action `fight`. These fields still need reconciliation; the Stripe terminal state and owner audit establish the recorded concession.
- The separate deadline sweep has silence-policy behavior. This diagram does not promise that every case waits indefinitely for an affirmative reply.

Other implemented components include Stripe webhook ingress, AgentCore Gateway and Memory, EventBridge scheduling, and Amplify hosting. Their existence does not establish a new verified full-cloud run. Direct carrier and Gmail adapters are not implemented.

## Source relationships

| Relationship | Source |
|---|---|
| Seven agents, order/customer dependency, guarded fan-in, direct evidence to drafter | `agent/graph.py`, `build_evidence_graph` |
| Structured strategy and evidence packet | `agent/models.py` |
| Isolated merchant evidence and policy tools | `agent/tools/evidence_tools.py`, `data/merchant_policy.yaml` |
| Separate executor and session handling | `agent/executor.py` |
| Approval conditions and real Telegram alert | `agent/hooks.py`, `ApprovalGate.before_tool_call` |
| Telegram reply ingress and runtime dispatch | `infra/lambdas/twilio_webhook/app.py`, `agent/app.py` |
| Concession handling and Stripe action | `scripts/reply.py`, `agent/tools/stripe_tools.py` |
| Case state and audit persistence | `agent/tools/case_tools.py` |
| Actual-record console and terminal-state handling | `console/src/lib/disputes.ts`, `console/src/components/ExhibitInspector.tsx` |
| Local run, owner action, fresh provider readback, published video | [submission verification](proofs/submission-verification.md) |

Source commits for the final runtime and console repairs are `02986f2` and `9cf06e3`. Public repository publication and Devpost submission are tracked separately.

## Render and verification

Uses installed Mermaid CLI 11.15.0 with local Google Chrome. Create `/tmp/rebuttal-mermaid-browser.json` containing:

```json
{"executablePath":"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"}
```

Then run from the repository root:

```sh
mmdc -p /tmp/rebuttal-mermaid-browser.json -i docs/architecture-submission.mmd -o docs/architecture-submission.svg -w 2400 -H 2600 -b white
mmdc -p /tmp/rebuttal-mermaid-browser.json -i docs/architecture-submission.mmd -o docs/architecture-submission.png -w 2400 -H 2600 -s 1.5 -b white
```

Both final exports exited 0 on September 14, 2026. SVG XML parsing passed. The final PNG was opened and visually inspected for complete labels, graph dependencies, approval conditions, local/cloud boundaries, and the outcome. This document-only change did not rerun the application suite or invoke cloud, messaging, or payment operations. Original `docs/architecture.*` assets were preserved.
