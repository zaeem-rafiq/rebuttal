# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Primary User:** Independent e-commerce merchants, digital creators, and boutique subscription operators using Stripe who manage their business without a dedicated in-house risk, fraud, or legal operations team.
- **User Situation & Job:** Under constant threat of margin erosion from illegitimate credit card chargebacks and time-consuming dispute administration. They need an autonomous advocate that defends legitimate revenue, compiles carrier/order proof without manual toil, and preserves high-value customer relationships.
- **Secondary Audience:** Hackathon evaluators and technical judges inspecting autonomous multi-agent reasoning, human-in-the-loop SMS interrupts, and distributed Bedrock AgentCore execution.

## Product Purpose

Rebuttal exists to level the playing field for independent merchants against unfair chargebacks. It continuously monitors Stripe disputes, launches parallel AI investigator agents across fragmented commerce systems (orders, carrier tracking and signatures, customer emails, and dispute history), computes win probability and expected value, compiles comprehensive evidence dossiers, and submits them directly to Stripe—all while keeping the merchant in control via single-tap SMS approvals when high-stakes judgment calls are required.

Success means eliminating hours of dispute paperwork, reversing wrongful chargebacks, preventing penalty fees, and protecting merchant lifetime customer relationships.

## Positioning

Unlike generic dispute alert services or passive form-fillers, Rebuttal is an autonomous, multi-agent defense system powered by the AWS Strands Agents SDK and Amazon Bedrock AgentCore:
- **Parallel Evidence Synthesis:** Coordinates dedicated investigator agents to discover proof across disconnected commerce silos simultaneously.
- **CLV-Aware Strategy:** Intelligently balances dispute win probability against Customer Lifetime Value (CLV), preventing costly disputes with VIP buyers.
- **Human-in-the-Loop SMS Interrupts:** Uses Strands `BeforeToolCallEvent` hooks (`agent.interrupt()`) to request merchant approval on high-value or ambiguous disputes via instant, single-digit SMS replies (`1 Fight | 2 Concede | 3 Hold`).

## Operating Context

- **Merchant Command Center:** Real-time Next.js 14 web console with 5-second polling against Supabase Cloud behind Row-Level Security (RLS).
- **Mobile Action Channel:** Out-of-band SMS dispatch via Twilio for immediate notification and two-way decision overrides on the go.
- **Commerce & Risk Backends:** Direct integration with Stripe Disputes API, AWS Bedrock AgentCore Runtime & Memory, AWS Lambda webhooks, and AWS CloudWatch GenAI Observability.

## Capabilities and Constraints

- **Capabilities:**
  - Real-time webhook ingestion (`charge.dispute.created`) with cryptographic signature validation.
  - Multi-agent graph coordination (Intake, Orders, Shipping, Comms, History, Strategy, Drafter, Executor).
  - Structured Pydantic strategy synthesis outputting win probability (0.00–1.00), expected value, customer tier (`new`, `repeat`, `vip`), and action recommendations.
  - Selective SMS interrupts for disputes > $200 or win probability between 35%–70%.
  - Pure-function automated deadline sweep applying protective silence defaults before hard deadlines expire.
  - Full OpenTelemetry span streaming to AWS CloudWatch GenAI Observability.
- **Constraints:**
  - **Live-Key Guard:** All Stripe operations must assert test key mode (`sk_test_`) and refuse live keys.
  - **Protected Fixtures:** The interactive scenario injection toolbar (S1/S2/S3), real-time Supabase dispute cards, and the Simulated Merchant Phone widget must remain prominent, fully functional, and preserved in the UI.
  - **Secret Safety:** Credentials sourced strictly from `.env` locally or AWS Secrets Manager in cloud; no secrets printed or leaked.

## Brand Commitments

- **Name:** Rebuttal
- **Voice:** High-conviction, professional financial advocate. Assertive against illegitimate chargebacks, protective of merchant margins, and clear-eyed about long-term customer relationships.
- **Tone:** Decisive, authoritative, transparent, and respectful of the merchant's time. Zero generic AI hype, apologetic fluff, or opaque "black box" decisions.

## Evidence on Hand

- **Synthetic Seed Data:** 12 realistic orders, customers, carrier scans, tracking numbers, customer communications, and dispute records in local SQLite and Supabase Cloud (`data/fixtures/`).
- **Three End-to-End Scenarios:**
  - **S1 ($48.00):** `product_not_received`, new customer, 88% win probability -> Autonomous Fight & Win with carrier signature.
  - **S2 ($340.00):** `fraudulent`, repeat VIP customer, 22% win probability -> SMS ApprovalGate -> Merchant reply `2` (Concede to protect VIP relationship).
  - **S3 ($129.00):** `subscription_canceled`, active subscriber -> Pre-dispute inquiry auto-refund, saving $15 dispute fee.
- **Telemetry & Architecture:** 92+ span execution trace waterfall in `docs/media/trace-S1.png` and architecture diagrams in `docs/architecture.svg` / `docs/architecture.png`.

## Product Principles

1. **Protect Margin and Peace of Mind:** Automate the repetitive evidentiary burden so small business owners never forfeit hard-earned money simply due to lack of time or administrative friction.
2. **Prioritize Long-Term Customer Value Over Short-Term Wins:** Winning a $50 dispute is a net loss if it destroys a $2,000 customer relationship; defense strategy must account for customer loyalty.
3. **Preserve Human Sovereignty in High-Stakes Moments:** The agent acts autonomously on routine, clear-cut cases, but must pause and yield control to the merchant whenever financial stakes or ambiguity are high.
4. **Radical Auditability and Transparency:** Every evidence item, carrier scan, win probability calculation, and decision step must be clearly visible and verifiable in the audit trail.

## Accessibility & Inclusion

- **Target Standard:** WCAG AA compliance across the web console.
- **Visuals:** High-contrast text on colored cards, avoiding washed-out gray-on-color or low-contrast status badges.
- **Structure:** Clear semantic HTML, accessible touch targets (minimum 44x44px for mobile and interactive phone controls), logical tab order, and full respect for `prefers-reduced-motion`.
