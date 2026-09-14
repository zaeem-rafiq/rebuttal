# Rebuttal — Devpost Hackathon Submission Copy

*Prepared for the AWS "Agents for Humans" Hackathon (Track: **Professional Agents**)*

---

### Project Title
**Rebuttal**

### Tagline (≤ 200 characters)
Autonomous chargeback defense agent for Stripe merchants on AWS Strands Agents SDK and Bedrock AgentCore with human-in-the-loop mobile Telegram approvals.

---

### Key Links
* **Judge Console:** [https://main.dtrewze9hbzeb.amplifyapp.com](https://main.dtrewze9hbzeb.amplifyapp.com)
* **GitHub Repository:** [https://github.com/zaeem-rafiq/rebuttal](https://github.com/zaeem-rafiq/rebuttal)
* **Demo Video (1080p, 02:32):** *(Insert unlisted YouTube link from `docs/media/rebuttal_demo_video.mp4`)*
* **Technical Articles (builder.aws):**
  1. *Human-in-the-Loop over Telegram with AWS Strands Interrupts* (`docs/posts/post-1-telegram-hil.md`)
  2. *Evals for an Agent That Decides: Binary Checks for Fight, Concede, or Refund* (`docs/posts/post-2-evals.md`)
  3. *Simulating Stripe Disputes End-to-End for Autonomous Agent Demos* (`docs/posts/post-3-stripe-simulation.md`)

---

### Built With
* **AWS Strands Agents SDK** (Multi-agent Evidence Graph, `@tool`s, hooks, session interrupts)
* **Amazon Bedrock AgentCore Runtime & Memory** (`rebuttal-pASUe6CVmu`, long-term `/merchant/{actorId}/outcomes`)
* **Amazon Bedrock Foundation Models** (Claude 3.5 Sonnet / Haiku inference)
* **AWS Lambda & Function URLs** (Stripe & Telegram dual-mode webhooks, scenario injector)
* **Amazon EventBridge** (Scheduled dispute deadline sweeps & daily demo resets)
* **AWS CloudWatch GenAI Observability** (OpenTelemetry distributed trace spans)
* **AWS Amplify Hosting** (Next.js 14 Case File console)
* **Stripe API** (Live webhook ingestion, dispute evidence submission, inquiry refunds)
* **Telegram Bot API** (Interactive mobile push alerts with inline action buttons via `@rebuttal_defense_bot`)
* **Supabase Cloud PostgreSQL** (Order, tracking, customer message fixtures with RLS)

---

### Devpost Description (Markdown)

Evidence boundary: this is a Stripe test-mode prototype with synthetic order, shipment, and communication records. Current runtime health, Telegram delivery/resume, and merchant outcomes are not verified by this draft.

#### 1. Inspiration
Chargebacks are an existential friction for small Stripe e-commerce merchants. Filing a dispute defense requires navigating complex card brand legal rules, digging up shipment scans, cross-referencing order records, and writing persuasive evidence before the applicable evidence deadline.

Our target is merchants who struggle to assemble dispute evidence before deadlines; merchant time savings and win-rate improvements have not been measured. Conversely, merchants often blindly fight disputes against repeat VIP customers, destroying customer goodwill over an inadvertent billing misunderstanding. We built **Rebuttal** to act as an autonomous paralegal: investigating cases overnight, making model-assisted recommendations, drafting audit-ready legal dossiers, and seeking merchant authorization only when it matters most.

#### 2. What It Does
Rebuttal implements a Stripe test-mode dispute workflow:
1. **Multi-Agent Evidence Discovery:** A parallel Strands graph deploys specialized agents to investigate seeded order records, shipment scans, customer messages, and configured dispute history. Direct carrier and Gmail adapters are not implemented in this checkout.
2. **Model-Assisted Strategic Decisions:** The Strategy node synthesizes evidence strength, customer lifetime value (LTV), and dispute win probability to choose one of three strategic actions:
   - **Fight:** Compiles and submits evidence directly to Stripe when winning evidence exists.
   - **Concede:** Gracefully closes the dispute to preserve VIP relationships when win probability is low.
   - **Refund Inquiry:** Proposes a refund for pre-chargeback inquiries (`warning_needs_response`). This non-fight action requires approval; fee savings are not demonstrated.
3. **Human-in-the-Loop over Telegram:** Disputes of at least $200, estimates in the inclusive 0.35–0.65 uncertainty band, or any non-fight action trigger a Strands `BeforeToolCallEvent` interrupt. Rebuttal dispatches an interactive push alert to the merchant’s phone via Telegram (`@rebuttal_defense_bot`) with inline buttons: `[1 ⚔️ Fight]`, `[2 🤝 Concede]`, `[3 ⏸️ Hold]`. The callback handler forwards the decision to the runtime. Current delivery and session resume need a fresh live rehearsal. Legacy Twilio support remains and may also send SMS when configured.
4. **The Case File Console:** A clean, paper-waybill-inspired judge dashboard hosted on AWS Amplify that displays live dispute dockets, evidence exhibits, and real-time status stamps.

#### 3. How We Built It
* **Agent Architecture:** Built on the **AWS Strands Agents SDK** orchestrating parallel evidence nodes (`Orders`, `Shipping`, `Comms`, `History`) into a central `StrategySynthesizer` and `EvidenceDrafter`.
* **Serverless Ingestion:** The AWS SAM template defines webhook and scenario-injection functions. Stripe signature handling and Telegram callback parsing are separate paths; this draft does not establish authenticated Telegram owner authorization.
* **AgentCore Runtime & Memory:** Deployed on Amazon Bedrock AgentCore (`rebuttal-pASUe6CVmu`), leveraging persistent short-term event memory and long-term semantic memory to learn merchant preferences over time.
* **Observability:** Instrumenting OTel spans with AWS CloudWatch GenAI Observability to track execution waterfalls, latency, and token consumption across all parallel agents.

#### 4. Challenges We Overcame
* **Carrier A2P 10DLC Delivery Filtering:** Standard out-of-band carrier SMS was repeatedly blocked by US carrier spam filters (Twilio Error 30034). Rather than waiting weeks for brand campaign verification, we engineered a dual-handling webhook supporting the Telegram Bot API. The replacement supports inline keyboard responses; no current delivery-latency benchmark is established.
* **Non-Blocking Interrupts:** The executor includes interrupt and session-rehydration code. Offline hook checks establish gate selection with simulated answers; a fresh live rehearsal is still needed to establish delivery and resume behavior.

#### 5. What We Learned & What's Next
* **Binary Evals Over LLM Vibes:** The evaluator separates action agreement, approval-hook selection, a fallible LLM grounding verdict, and EV sign. The revised rubric fails judge errors and unsupported factual claims. The old benchmark does not validate this revised rubric, and the gate metric does not establish live delivery or resume.
* **Roadmap:** Adding multi-tenant Slack app integration for enterprise teams, and automated carrier API connectors (FedEx, DHL, UPS) via the Bedrock AgentCore Gateway MCP tool server.
