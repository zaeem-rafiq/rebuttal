# Rebuttal Demo Take Runbook

This runbook specifies the exact command and click sequence for recording a demo take of **Rebuttal**, along with a triage table for any potential failure modes.

---

## 1. Take Sequence (Chronological)

### Step 0: Stack Reset & Clean State
Run the automated demo reset script to archive past test dispute rows, reset database fixtures, and verify all cloud infrastructure:
```bash
uv run python scripts/reset_demo.py
```
**Expected verification output:**
```
PROOF R-15: reset_demo ok runtime=READY lambdas=3/3 console=200 = PASS
Stack is CLEAN and TAKE-READY.
```

---

### Step 1: Open Judge Console
Open the live deployed Judge Console:
- URL: `https://main.dtrewze9hbzeb.amplifyapp.com`
- Verify clean state: 12 seeded orders, 3 baseline disputes (`dp_S1`, `dp_S2`, `dp_S3`), decisions cleared.

---

### Step 2: Inject Scenario S1 (Autonomous Defense)
- **Customer & Order:** M. Okafor · ORD-1001 · Trail-mix sampler ($48.00)
- **Dispute Reason:** `product_not_received`
- **Action:**
  - Click **Inject S1** in the console toolbar (or run `uv run python scripts/simulate_dispute.py --scenario S1`).
- **Autonomous Agent Behavior:**
  1. Stripe test mode creates confirmed PaymentIntent and raises dispute.
  2. Stripe webhook invokes Bedrock AgentCore runtime (`rebuttal-pASUe6CVmu`).
  3. Strands GraphBuilder pipeline gathers evidence: UPS tracking delivered, recipient signature matched.
  4. Decision engine recommends **Fight** with high win probability (0.90).
  5. Since amount ($48) < approval threshold ($200), the agent autonomously submits evidence directly to Stripe.
  6. Dispute outcome resolves to **Won** (`status=won`).
  7. **No SMS is sent** to the owner (`no_sms=true`).
- **Console Feedback:**
  - Open file updates showing submitted evidence exhibits and green **WON** stamp.

---

### Step 3: Inject Scenario S2 (High-Stakes Human Gate)
- **Customer & Order:** J. Lee · ORD-1002 · Ceramic pour-over set ($340.00)
- **Dispute Reason:** `fraudulent`
- **Action:**
  - Click **Inject S2** in the console toolbar (or run `uv run python scripts/simulate_dispute.py --scenario S2`).
- **Autonomous Agent Behavior:**
  1. Stripe creates $340 chargeback.
  2. Bedrock AgentCore executes intake, orders, shipping, comms, and strategy nodes.
  3. Strategy finds mixed evidence (billing address mismatch, delivery to mailroom).
  4. Gate check triggers because dispute amount ($340.00) exceeds the merchant's $200.00 auto-fight threshold (`amount >= 20000 cents`).
  5. Execution pauses on Bedrock AgentCore session interrupt.
  6. Rebuttal dispatches SMS via Twilio to owner phone (`+18129551686`).
- **Merchant Experience:**
  - Owner phone buzzes with alert:
    ```text
    Rebuttal Alert: Dispute dp_S2 ($340.00 - fraudulent).
    Mixed evidence. Recommending concede or review.
    Reply:
    1 Fight
    2 Concede
    3 Hold
    ```
  - Console displays yellow highlighter band: `Awaiting your reply by SMS · sent to +1 ••• 1686`.

---

### Step 4: Merchant Real Phone Reply
- **Action on Phone:**
  - On your mobile device, reply directly to the SMS with:
    ```text
    2
    ```
- **Autonomous Agent Behavior:**
  1. Twilio forwards inbound SMS to `rebuttal-twilio-webhook` Lambda Function URL.
  2. Lambda validates HMAC signature, parses answer `2` (concede), and invokes AgentCore approval endpoint.
  3. Bedrock AgentCore resumes interrupted session and executes `concede_dispute`.
  4. Stripe dispute transitions to `status=lost`.
  5. Confirmation SMS sent back to owner:
     `Rebuttal: Dispute conceded per owner confirmation.`
- **Console Feedback:**
  - Console transitions gate to **CONCEDED** / **LOST** decision stamp.

---

### Step 5: AgentCore Long-Term Memory & Observability
- Bedrock AgentCore stores dispute outcome in long-term memory (`/merchant/default/outcomes`) for future dispute context.
- CloudWatch GenAI Observability records the complete execution waterfall trace.

---

## 2. Contingency Triage Table ("If X Fails, Do Y")

| Failure Symptom | Underlying Cause | Immediate Remediation (Do Y) |
|---|---|---|
| `reset_demo.py` fails on `runtime=ERROR` | Bedrock AgentCore endpoint scaling up or AWS credential expired | Check `aws sts get-caller-identity --profile zaeem-khan`. Re-authenticate via `aws login --profile zaeem-khan` if needed. |
| Injected scenario does not appear in console | Stripe webhook not delivered to Function URL within 15s | Check `/aws/lambda/rebuttal-stripe-webhook` CloudWatch logs. Manually dispatch event via `uv run python scripts/test_r08_e2e.py` fallback dispatch. |
| Console rate limits injection (HTTP 429) | Multiple injections triggered within 60s cooldown | Wait 60 seconds between clicks, or trigger directly via `uv run python scripts/simulate_dispute.py --scenario S1`. |
| S2 SMS does not buzz on phone | Twilio carrier delay or blocked number | Check Twilio Console SMS logs. Verify `TWILIO_FROM` number in `.env`. Ensure phone has cellular signal. |
| Reply "2" sent from phone, but dispute stays open | Twilio webhook signature failed or wrong dispute mapping | Run `uv run python scripts/reply.py --scenario S2 --answer 2` to resume and close immediately via command line. |
| Console shows stale case data | Browser cached previous Supabase query | Hard refresh browser tab (`Ctrl+Shift+R` / `Cmd+Shift+R`). The console auto-polls every 5s. |
| Stripe API error `live-key-guard` | Secret key does not start with `sk_test_` | Stop immediately. Verify `STRIPE_SECRET_KEY` in `.env` starts with `sk_test_`. Never use live keys. |
| CloudWatch trace missing in GenAI Observability | OpenTelemetry buffering delay | CloudWatch GenAI Observability spans can take up to 2–5 minutes to index in the console dashboard. |
