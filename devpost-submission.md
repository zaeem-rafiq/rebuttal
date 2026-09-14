# Rebuttal

Submission copy prepared September 14, 2026. Publishing this file does not establish that the Devpost entry has been submitted.

## Tagline

A chargeback investigator that gathers the evidence, recommends a response, and puts consequential decisions on the merchant's phone.

## Inspiration

A chargeback turns a small merchant into an investigator. The answer may be buried in an order, a delivery event, a customer's address-change message, or the merchant's relationship with that buyer. The deadline keeps moving while the owner is running the business.

We wanted to give that owner a prepared decision: the relevant facts, a reasoned recommendation, and a way to act from their phone. Sometimes the right answer is to concede. Rebuttal is designed to make that choice deliberate, rather than treating every dispute as something to fight.

## What it does

Rebuttal assembles a case file from order details, shipping records, customer communications, and merchant history and policy. Its agents recommend fighting, conceding, or refunding an inquiry, and prepare the supporting evidence narrative. The console lets the merchant inspect the underlying records and the recorded recommendation.

Before a consequential Stripe action, a separate approval hook checks the merchant's policy. Under the default policy, amounts of at least $200, estimates in the 0.35–0.65 uncertainty band, and any non-fight action request an owner decision. Telegram presents **Fight, Concede, or Hold**, so the owner can respond away from the desk.

Our [2:58 demonstration](https://www.youtube.com/watch?v=WRrAUpgRC90) follows a $340 Stripe test dispute. It shows the actual console, the order and delivery records, the customer's messages, the recommendation, the real Telegram alert, and the confirmation after the owner chooses Concede on their phone. A fresh Stripe readback and the recorded owner audit confirm that the same test dispute closed as `lost`, which is Stripe's status for the concession shown. The console displays **CONCEDED · CLOSED**.

## How we built it

**AWS Strands Agents SDK** runs a seven-node evidence graph and a separate execution agent. Intake reads the Stripe dispute and payment context. Orders and shipping can begin together; communications and history wait for the order lookup to resolve the merchant's customer ID. Strategy waits for all four evidence investigators. The drafter receives both the strategy and the underlying evidence directly, so it does not have to reconstruct facts from a recommendation alone.

**Amazon Bedrock** provides the model inference; the recorded generation used Claude Sonnet 4.5. Structured outputs, source checks, and the execution hook separate evidence interpretation from action. A recommendation is not permission to execute.

Codex and Google Antigravity assisted with implementation, review, and debugging; Codex also helped produce the edited demonstration. The runtime AI is the Strands/Bedrock pipeline described above. Narration is AI-generated.

The user interface is **Next.js, React, and TypeScript**. **Supabase** holds the case and audit records. The phone reply is handled by the existing **AWS Lambda and Amazon Bedrock AgentCore** integration, which applies the owner's decision through the Stripe test API. The repository also contains Gateway, Memory, deadline-sweep, and deployment components.

The recording combines a local console and local Strands pipeline with real Bedrock inference, a genuine Telegram exchange, and the existing cloud callback. The test case was recovered into the case store before generation. This recording does not establish automatic cloud ingestion or deployment of the latest local console and graph repairs.

## Challenges we ran into

The hardest problem was keeping every displayed claim tied to evidence. Early outputs confused planned actions with completed actions, inferred intent from missing messages, and sometimes relied on incomplete evaluator inputs. We tightened source handling, normalized money and timestamps, supplied complete policy context to evaluation, and added checks for unsupported assertions and evaluator false positives.

The graph also exposed a real dependency: communications and customer history cannot run correctly until the order lookup has identified the merchant's customer. We made that ordering explicit and guarded the fan-in before strategy and drafting.

Finally, a successful chat message is not enough to prove an action happened. We checked the resulting Stripe dispute, matching case status, and owner audit separately before using the completed outcome in the video.

Implementation revision `e2c1cd1` adds a shared writer for the selected owner decision across local/cloud stores. Closure memory now requires consistent execution audits; missing, conflicting, or unavailable evidence produces an explicit skip while preserving terminal case status. These fixes passed local tests, including cloud-only decision scenarios. See the [verification record](docs/proofs/record-consistency-2026-09-14.md).

## Accomplishments we're proud of

- The demo shows inspectable product evidence and an actual owner decision from their phone.
- The $340 test case closed through the existing phone callback, with matching Stripe and case-store readbacks.
- Implementation revision `e2c1cd1` passed 256 Python tests locally with seeded synthetic fixtures and offline provider doubles. The unchanged console previously passed 12 focused tests, type checking, and a production build; those checks were not rerun for this revision.
- The public video shows the full decision journey in under three minutes, with English captions and clearly disclosed synthetic records and Stripe test mode.

## What we learned

The agent's useful output is a decision someone can trust and act on. That requires more than plausible prose: correct data dependencies, visible source records, a separate execution boundary, and a check of the resulting state. We also learned to evaluate the evaluator; a false accusation of hallucination is still a testing defect.

## What's next

Apply the prepared SQL migration, deploy the locally tested decision and attribution fixes, and verify live synchronization and automatic ingestion with the current source. Deploy the updated console, add direct merchant-system adapters, and test with consenting merchants to measure review time and decision quality.

This is a prototype using synthetic merchant evidence and Stripe test mode. Direct carrier and Gmail adapters are not implemented. Win estimates are not calibrated against real merchant outcomes, and real recovery rates or time savings have not been measured. The recorded case's decision row and closure-memory label remain historically inconsistent; terminal dispute state and the owner audit establish the demonstrated concession. Revision `e2c1cd1` contains locally tested fixes, but no new deployment or historical cloud-record repair was performed. The [PostgreSQL migration](schema/migrations/20260914_owner_decision_sync.sql) is prepared and **not applied**; live synchronization remains unverified. The deadline sweep has a separate silence policy, so the approval flow is not an indefinite-wait guarantee.

## Built with

AWS Strands Agents SDK, Amazon Bedrock, Amazon Bedrock AgentCore, AWS Lambda, Amazon EventBridge, Amazon CloudWatch, AWS Amplify, Python, Next.js, React, TypeScript, Stripe, Telegram Bot API, Supabase, SQLite.

## Links and architecture

- Demo video: https://www.youtube.com/watch?v=WRrAUpgRC90
- Public source repository: https://github.com/zaeem-rafiq/rebuttal
- Required architecture upload: [architecture-submission.png](docs/architecture-submission.png)
- Architecture source and scope: [architecture-submission.md](docs/architecture-submission.md)
- Local decision/attribution verification: [record-consistency-2026-09-14.md](docs/proofs/record-consistency-2026-09-14.md)
- Optional live-demo field: leave blank; the hosted console has not been verified against this recorded build.

## Testing instructions for judges

Watch the public video for the recorded product and phone workflow. The repository provides the source and local setup instructions; use Python 3.12+ and install `requirements.txt` in a virtual environment. Clone the `codex/record-consistency-20260914` branch with Git (the evaluator reads Git provenance), then seed the local synthetic database before the offline Python checks:

```sh
PYTHON_DOTENV_DISABLED=1 AWS_EC2_METADATA_DISABLED=true SUPABASE_URL= SUPABASE_SERVICE_KEY= .venv/bin/python scripts/seed_supabase.py --local-only --verify
PYTHON_DOTENV_DISABLED=1 AWS_EC2_METADATA_DISABLED=true SUPABASE_URL= SUPABASE_SERVICE_KEY= STRIPE_SECRET_KEY=sk_test_mock_for_unit_tests .venv/bin/python -m pytest -q
```

For the console's focused checks after installing its locked dependencies:

```sh
cd console
npm ci
node --test tests/disputes.test.cjs
npx tsc --noEmit
```

The Python suite covers source validation, evaluator controls, graph scheduling, approval boundaries, and runtime guards. The console checks cover actual-record rendering and decision-state handling. These checks isolate external effects; they do not send phone messages or execute Stripe actions. Live inference and provider integration require the configuration in `.env.example`. Do not use production Stripe keys. The submitted video is an edited recording of the verified test case, not an unrestricted hosted test environment.

## Official form recap (not project-story copy)

Rules checked September 14, 2026: https://agentsforhumans.devpost.com/rules

| Official field | Prepared answer |
|---|---|
| Submitter Type | Individual; owner confirmed solo entry |
| Country of Residence | United States |
| Organization | Leave blank |
| Track | Professional Agents |
| Public code repository | https://github.com/zaeem-rafiq/rebuttal |
| Required architecture diagram | Attach `docs/architecture-submission.png` |
| AWS Builder ID | Enter the owner-supplied Builder ID separately; do not publish it in the project story |
| Optional live demo | Leave blank |
| Testing instructions | Use the section above |
| Optional bonus blog post | [Owner approval](https://builder.aws.com/content/3JKulzlCq3EKvf4v5JY56vQbRBu); [Evaluation lessons](https://builder.aws.com/content/3JKv5cydKUnsdDqFMx3fKDXEw3e); [Stripe test webhooks](https://builder.aws.com/content/3JKvYmtVerTCu01RjeNaKNpTn9a) |
| Demo video | https://www.youtube.com/watch?v=WRrAUpgRC90 |

The repository begins with its initial project commit on September 5, 2026, within the hackathon build period. It uses the standard frameworks and open-source dependencies listed above; no claim is made that these dependencies were created for the event.
