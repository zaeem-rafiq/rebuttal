# Rebuttal: Demo Video Script & Production Beat Sheet

**Total Duration:** 02:30 (Target: ≤ 5:00)  
**Master Audio Track:** `docs/media/demo_narration.mp3` (Generated via AWS Polly Neural `Matthew`)  
**Live Console:** [https://main.dtrewze9hbzeb.amplifyapp.com](https://main.dtrewze9hbzeb.amplifyapp.com)  
**Target Video Format:** 1080p (1920×1080), 30 or 60 FPS MP4  

---

## Screen Layout Recommendations

```
+---------------------------------------------+-----------------------+
|                                             |                       |
|   LEFT / MAIN (65% width)                   |  RIGHT (35% width)    |
|   - Rebuttal Case File Console              |  - Telegram Phone     |
|     (https://main.dtrewze9hbzeb.amplifyapp) |    Capture / Mirror   |
|   - Or Stripe Dashboard tab                 |  - Live CLI Trace     |
|                                             |    (run_local.py)     |
|                                             |                       |
+---------------------------------------------+-----------------------+
```

---

## Timed Beat Sheet & Word-for-Word Voiceover

### Act 1: The Problem — The $150 Billion Chargeback Trap (00:00 – 00:22)
* **What to Show on Screen:**
  - Start on Stripe Dashboard or Rebuttal Console home page (`https://main.dtrewze9hbzeb.amplifyapp.com`).
  - Highlight the harsh merchant realities: $15 dispute penalty, tight 7-day deadlines, complex evidence requirements.
* **Audio Voiceover (Word-for-Word):**
  > "For small, independent e-commerce merchants selling on Stripe, chargebacks are a silent, brutal bleed. Every single dispute comes with an immediate, non-refundable fifteen-dollar penalty fee from the card network. Merchants are given a narrow window, often just seven days, to assemble evidentiary packets across Shopify, shipping carriers, and customer support threads. Because gathering this evidence by hand is tedious and confusing, over eighty percent of merchants either forfeit by default or paste together weak, unformatted rebuttals that get denied. That is billions of dollars lost annually to friendly fraud. Meet Rebuttal: the autonomous chargeback defense agent built on the AWS Strands Agents SDK and Amazon Bedrock AgentCore."

---

### Act 2: Architecture & "The Case File" Interface (00:22 – 00:45)
* **What to Show on Screen:**
  - Showcase the Rebuttal Console desk (`#EDECE6`) and open sheet (`#FFFFFF`).
  - Emphasize the archival Case File design: 0px border radius, ink typography, absence of flashy SaaS gradients.
  - Hover or click on the evidence exhibits (Shopify, UPS tracking, customer chats).
* **Audio Voiceover (Word-for-Word):**
  > "Rebuttal acts as an autonomous legal paralegal working on the merchant's behalf overnight. When designing Rebuttal, we rejected generic SaaS dashboards and built The Case File. Inspired by judicial bench dockets, our interface is disciplined and distraction-free: genuine paper-and-ink contrast, strict monospace typography for financial identifiers, and a clear desk policy. Everything on screen is either verified evidence, an active decision, or a deadline. Under the hood, an event-driven ingestion pipeline powered by AWS SAM, Amazon API Gateway, and Lambda captures Stripe webhooks. A multi-agent state graph orchestrated by Bedrock AgentCore Runtime executes autonomous investigation routines against Shopify, UPS, and customer communication channels."

---

### Act 3: Scenario S1 — Autonomous Carrier Win (00:45 – 01:14)
* **What to Show on Screen:**
  - Click **Scenario S1** in the top-right scenario bar.
  - Case file loads: **$48.00** (`product_not_received`).
  - Show Exhibits A through E expanding: UPS carrier tracking, signed delivery receipt in Atlanta, GPS coordinates matching order billing address.
  - Show win probability (88%) and watch the stamp land: **`FOUGHT · BY AGENT`** / **`WON`**.
* **Audio Voiceover (Word-for-Word):**
  > "Let us watch Scenario One unfold in real time. A customer files a forty-eight-dollar dispute claiming product not received. Within milliseconds of receiving the Stripe webhook, Rebuttal's triage agent classifies the claim and initiates an evidence sweep. It queries the merchant's order system, retrieves carrier tracking from UPS, pulls the signed proof of delivery, and verifies the delivery coordinates match the customer's billing address. On the docket, you can see Rebuttal assembling Exhibits A through E: the original order, carrier tracking, signed delivery receipt, customer purchase history, and store refund policy. Rebuttal calculates an eighty-eight percent win probability. Because this exceeds the merchant's sixty percent policy threshold, the agent acts autonomously: it formats the evidence into Stripe's strict arbitration schema and submits the rebuttal directly to the Stripe API. The dispute is stamped WON, protecting forty-eight dollars without requiring a single second of merchant effort."

---

### Act 4: Scenario S2 — Human-in-the-Loop via Telegram & SMS Gate (01:14 – 01:46)
* **What to Show on Screen:**
  - Click **Scenario S2** (`dp_S2`, **$340.00** `fraudulent`, Repeat VIP customer).
  - Point out low win probability (22%) and yellow highlighter band: *Awaiting your reply by Telegram / SMS*.
  - Show phone screen on right (or inset camera): Telegram notification pops up from `@rebuttal_defense_bot` with inline buttons `[1 ⚔️ Fight]`, `[2 🤝 Concede]`, `[3 ⏸️ Hold]`.
  - Tap `2 Concede` (or `1 Fight`) on the phone.
  - Within ~2 seconds, watch the stamp slam onto the open case file: **`CONCEDED · BY OWNER (TELEGRAM)`**.
* **Audio Voiceover (Word-for-Word):**
  > "Autonomous systems must also know when not to fight. In Scenario Two, a three-hundred-forty-dollar chargeback arrives for a repeat VIP customer. With a low win probability and high customer lifetime value, fighting aggressively could destroy customer goodwill. Rebuttal's Approval Gate halts execution. It dispatches an interactive push notification directly to the store owner via Telegram and Twilio SMS. Notice the action buttons: Fight, Concede, or Hold. The merchant reviews the memo on their phone, recognizes the VIP customer, and taps Concede. Instantly, our AWS Lambda webhook captures the callback, securely verifies the origin, and routes the decision into the Amazon Bedrock AgentCore runtime. The dispute is conceded gracefully, preventing an adversarial dispute and retaining the customer."

---

### Act 5: Scenario S3 — Pre-Dispute Inquiry Prevention (01:46 – 02:11)
* **What to Show on Screen:**
  - Click **Scenario S3** (`dp_S3`, **$129.00** `subscription_canceled`).
  - Show the pre-dispute inquiry banner.
  - Show Rebuttal identifying cancellation confusion and issuing an immediate preventive refund.
  - Show the outcome stamp: **`INQUIRY CLOSED · REFUNDED · $15 FEE SAVED`**.
* **Audio Voiceover (Word-for-Word):**
  > "Scenario Three demonstrates proactive dispute prevention. Before a customer files a formal chargeback, payment networks issue a pre-dispute inquiry or early fraud warning. Most merchants miss these alerts because they arrive quietly in Stripe notifications. Rebuttal monitors inquiries in real time. Here, an active subscriber was confused about their annual renewal and initiated an inquiry for one hundred twenty-nine dollars. Rebuttal detects that the account is in good standing and that the customer simply requested cancellation. Instead of allowing this inquiry to escalate into a formal dispute, which would trigger a fifteen-dollar penalty fee, Rebuttal automatically issues a prompt refund and cancels the recurring billing. The dispute is prevented before it ever starts, saving the merchant fifteen dollars and safeguarding their Stripe dispute ratio."

---

### Act 6: Enterprise Hardening & Closing (02:11 – 02:30)
* **What to Show on Screen:**
  - Show terminal running evals benchmark (`python evals/run_evals.py`) with 100% pass rate.
  - Or show the system architecture diagram in README.
  - Conclude on the Rebuttal Console header.
* **Audio Voiceover (Word-for-Word):**
  > "Rebuttal is enterprise-hardened with continuous evaluation benchmarks, strict schema validation, and zero hallucinations. Every tool call enforces strict Pydantic schemas. All secrets resolve at runtime via AWS Secrets Manager with zero context leakage. Our automated decision evals harness tests forty-eight distinct dispute permutations, proving a one hundred percent policy compliance rate. And our web console achieved a perfect one hundred accessibility score on Google Lighthouse. Rebuttal gives small Stripe merchants the same sophisticated, data-driven legal defense that Fortune 500 retailers possess. Rebuttal: autonomous chargeback defense, with human oversight when it matters most. Thank you."

---

## 3 Easy Ways to Record

### Option A: Screen Record While Playing the Audio (Zero Editing)
1. Open your screen recorder (OBS, Loom, or Windows Game Bar: `Win + G`).
2. Play `docs/media/demo_narration.mp3` through your speakers or virtual audio cable.
3. Follow along and click the scenarios on `https://main.dtrewze9hbzeb.amplifyapp.com` in sync with the voice.
4. Stop recording. Done!

### Option B: Video Editor Overlay (CapCut, Clipchamp, Premiere, DaVinci)
1. Screen record yourself walking through the 6 acts on the console at your own pace (~2.5 minutes).
2. Drag your video file and `docs/media/demo_narration.mp3` into your video editor.
3. Align the video clips to the 6 audio acts.
4. Export as 1080p MP4!

### Option C: Read the Script Live Yourself
- If you prefer your own voice, use the word-for-word voiceover script above as your teleprompter while recording!
