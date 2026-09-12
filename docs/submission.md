# Rebuttal — Devpost Hackathon Submission Copy

*Prepared for the AWS "Agents for Humans" Hackathon (Track: **Professional Agents**)*

---

### Project Title
**Rebuttal**

### Tagline (≤ 200 characters)
Autonomous chargeback defense agent for Stripe merchants on AWS Strands Agents SDK and Bedrock AgentCore with human-in-the-loop mobile Telegram approvals.

---

### Key Links
* **Live Webhook & Judge Console:** [https://main.dtrewze9hbzeb.amplifyapp.com](https://main.dtrewze9hbzeb.amplifyapp.com)
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

#### 1. Inspiration
Chargebacks are an existential friction for small Stripe e-commerce merchants. Filing a dispute defense requires navigating complex card brand legal rules, digging up shipment scans, cross-referencing order records, and writing persuasive evidence within unforgiving bank deadlines (typically 7–14 days).

Merchants lose 70% of winnable disputes simply due to lack of time or missing technical evidence. Conversely, merchants often blindly fight disputes against repeat VIP customers, destroying customer goodwill over an inadvertent billing misunderstanding. We built **Rebuttal** to act as an autonomous paralegal: investigating cases overnight, making mathematically grounded decisions, drafting audit-ready legal dossiers, and seeking merchant authorization only when it matters most.

#### 2. What It Does
Rebuttal listens to live Stripe dispute events and handles end-to-end chargeback resolution:
1. **Multi-Agent Evidence Discovery:** A parallel Strands graph deploys specialized agents to investigate the merchant's orders database, carrier tracking scans, customer support messages, and prior historical disputes.
2. **Deterministic Strategic Decisions:** The Strategy node synthesizes evidence strength, customer lifetime value (LTV), and dispute win probability to choose one of three strategic actions:
   - **Fight:** Compiles and submits evidence directly to Stripe when winning evidence exists.
   - **Concede:** Gracefully closes the dispute to preserve VIP relationships when win probability is low.
   - **Refund Inquiry:** Immediately refunds pre-chargeback customer inquiries (`warning_needs_response`) before they mature into official disputes, dodging non-refundable bank fees ($15).
3. **Human-in-the-Loop over Telegram:** High-value disputes ($\ge \$200$), uncertain cases, or concessions trigger a Strands `BeforeToolCallEvent` interrupt. Rebuttal dispatches an interactive push alert to the merchant’s phone via Telegram (`@rebuttal_defense_bot`) with inline buttons: `[1 ⚔️ Fight]`, `[2 🤝 Concede]`, `[3 ⏸️ Hold]`. A single tap securely resumes the Bedrock AgentCore runtime session.
4. **The Case File Console:** A clean, paper-waybill-inspired judge dashboard hosted on AWS Amplify that displays live dispute dockets, evidence exhibits, and real-time status stamps.

#### 3. How We Built It
* **Agent Architecture:** Built on the **AWS Strands Agents SDK** orchestrating parallel evidence nodes (`Orders`, `Shipping`, `Comms`, `History`) into a central `StrategySynthesizer` and `EvidenceDrafter`.
* **Serverless Ingestion:** An AWS SAM template deploys three Lambda Function URLs with IAM SigV4 / HMAC authentication handling incoming Stripe dispute webhooks, Telegram inline callback queries, and scenario injections.
* **AgentCore Runtime & Memory:** Deployed on Amazon Bedrock AgentCore (`rebuttal-pASUe6CVmu`), leveraging persistent short-term event memory and long-term semantic memory to learn merchant preferences over time.
* **Observability:** Instrumenting OTel spans with AWS CloudWatch GenAI Observability to track execution waterfalls, latency, and token consumption across all parallel agents.

#### 4. Challenges We Overcame
* **Carrier A2P 10DLC Delivery Filtering:** Standard out-of-band carrier SMS was repeatedly blocked by US carrier spam filters (Twilio Error 30034). Rather than waiting weeks for brand campaign verification, we engineered a dual-handling webhook supporting the Telegram Bot API. This provided instant sub-second push delivery and intuitive one-tap inline keyboard responses.
* **Non-Blocking Interrupts:** Traditional HITL patterns lock compute threads while awaiting human replies. By pairing Strands SDK session interrupts with Bedrock AgentCore session rehydration, the agent freezes its state in memory, frees compute resources, and seamlessly resumes when the webhook callback arrives.

#### 5. What We Learned & What's Next
* **Binary Evals Over LLM Vibes:** We proved that deterministic binary unit checks (`action_match`, `gate_match`, `judge_pass`, `ev_sign`) provide far more engineering reliability than subjective 1–5 LLM scores.
* **Roadmap:** Adding multi-tenant Slack app integration for enterprise teams, and automated carrier API connectors (FedEx, DHL, UPS) via the Bedrock AgentCore Gateway MCP tool server.
