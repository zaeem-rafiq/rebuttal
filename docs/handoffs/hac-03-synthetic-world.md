---
artifact_contract: "ce-handoff/v1"
created_at: "2026-09-05T18:37:30Z"
title: "Kick off HAC-3 (R-01 Synthetic World)"
summary: "Handoff to execute HAC-3: Supabase schema, fixtures, Stripe tools, and dispute simulator"
keywords: ["HAC-3", "R-01", "Supabase", "fixtures", "Stripe", "dispute-simulator"]
cwd: "C:/Users/zaeem/Documents/Rebuttal"
resume_focus: "Implement HAC-3: Supabase schema, synthetic fixtures, Stripe tools, dispute simulator"
repository: "Rebuttal"
repo_root_sha: "e320fa5"
branch: "zaeem/hac-3-r-01-synthetic-world-supabase-schema-fixtures-stripe-tools"
head: "e69306e"
---

# HAC-3 / R-01: Synthetic World Handoff

## 1. Issue Overview
- **Linear Issue:** `HAC-3` (UUID: `d8a98ffb-6b21-4f8e-851d-d79f4182a5e8`)
- **Title:** `R-01 · Synthetic world: Supabase schema, fixtures, Stripe tools, dispute simulator`
- **Milestone:** M1 Core agent, local
- **Branch:** `zaeem/hac-3-r-01-synthetic-world-supabase-schema-fixtures-stripe-tools`
- **Linear Status:** In Progress

## 2. Deliverables & Acceptance Criteria
1. **Supabase Schema & Seed Script (`scripts/seed_supabase.py --reset`):**
   - Tables: `customers`, `orders`, `order_items`, `shipments`, `shipment_events`, `customer_messages`, `disputes`, `decisions`, `audit_log`, `merchant_policy`.
   - Seed data with 12 orders including scenarios S1, S2, S3:
     - **S1 (`ORD-1001`):** \$48.00 trail-mix sampler, customer M. Okafor, UPS delivered + signed "OKAFOR", AVS/CVC match, inquiry/tracking thread.
     - **S2 (`ORD-1002`):** \$340.00 ceramic pour-over set, customer J. Lee (4 prior orders, LTV \$1,120), shipped to alternate address per emailed customer request, no signature.
     - **S3 (`ORD-1003`):** \$129.00 coffee subscription, customer R. Alvarez, inquiry stage, emailed to cancel.
   - Idempotent seeding and schema migration SQL in `schema/supabase_schema.sql` or `migrations/`.

2. **Stripe Tools (`agent/tools/stripe_tools.py`):**
   - Exposes Strands `@tool` decorators:
     - `get_dispute(dispute_id: str)`
     - `get_charge_context(charge_id_or_payment_intent: str)` -> returns amount, card checks, billing details, `metadata.order_id`, customer email
     - `list_open_disputes(limit: int = 10)`
     - `upload_evidence_file(file_path: str, purpose: str = "dispute_evidence")`
     - `submit_evidence(dispute_id: str, evidence: dict, submit: bool = False)`
     - `concede_dispute(dispute_id: str)` -> calls `Dispute.close`
     - `refund_inquiry(dispute_id_or_charge: str)` -> only valid when dispute status is `warning_needs_response`
   - Strict adherence to Live-key guard: asserts `STRIPE_SECRET_KEY.startswith("sk_test_")`.

3. **Dispute Simulator (`scripts/simulate_dispute.py --scenario S1|S2|S3`):**
   - Creates a confirmed PaymentIntent with matching test PaymentMethod:
     - S1: `pm_card_createDisputeProductNotReceived`
     - S2: `pm_card_createDispute`
     - S3: `pm_card_createDisputeInquiry`
   - Sets `metadata.order_id` on the PaymentIntent.
   - Polls until dispute exists in Stripe test mode.
   - Prints `dispute.id`, `reason`, `amount`, `due_by`.
   - Writes the `PaymentIntent.id` back to the order in Supabase/fixtures.

4. **Proof of Success:**
   Append to `docs/proofs/R-01.md`:
   - `PROOF R-01: rows customers=10 orders=12 shipments=11 messages>=8 policy=1 = PASS`
   - `PROOF R-01: S1 dispute reason=product_not_received order=ORD-1001 due_by=<iso> = PASS`
   - `PROOF R-01: S2 dispute reason=fraudulent order=ORD-1002 = PASS`
   - `PROOF R-01: get_charge_context(S2).metadata.order_id=ORD-1002 = PASS`

## 3. Environment Context
- Virtual environment: `.venv/` (Python 3.12.14) with all packages installed.
- Stripe CLI installed (`stripe version 1.50.10`).
- Base git commits on `main` and `zaeem/hac-3-r-01-synthetic-world-supabase-schema-fixtures-stripe-tools`:
  `e69306e feat(preflight): implement R-00 preflight checks script and env template`
