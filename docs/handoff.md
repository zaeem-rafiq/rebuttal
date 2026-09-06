# Rebuttal Build Queue Handoff

## Current Status
- **Last Completed Issue:** HAC-11 (R-09 · Observability on, one trace captured)
- **Active Issue:** HAC-12 (R-10 · Judge console (live demo link))
- **Milestone:** M4 Judge console
- **Branch:** `zaeem/hac-12-r-10-judge-console-live-demo-link` (pushed to origin)
- **Linear Status:** In Progress

## Completed Work on HAC-12 (R-10)
1. **Inject Lambda (`infra/lambdas/inject/app.py` & SAM Template):**
   - Implemented with `X-Console-Key` header authentication, 60-second rate limiting, Stripe test-mode PaymentIntent creation, and live-key guard assertion.
   - Added to SAM template `infra/template.yaml`.
   - Deployed to AWS stack `rebuttal-webhooks` via SAM CLI.
   - Deployed Function URL: `https://aovwsnanmseqfc753yan52g3be0nqnem.lambda-url.us-east-1.on.aws/` (Verified live: returns 401 on missing auth, 400 on invalid scenario, 429 on rate limit).
2. **Judge Console Next.js Application (`console/`):**
   - Built full Next.js 14 App Router application with Tailwind CSS, TypeScript, and Lucide icons.
   - Implemented `/` route: summary metrics, scenario injection toolbar (S1/S2/S3) with 60s cooldown timer, live 5s auto-polling dispute feed, and inline "Reply as owner: 1 Fight | 2 Concede | 3 Hold" action buttons for pending decisions.
   - Implemented `/case/[id]` route featuring the 4 core cards:
     1. Strategy Card (Win probability visual gauge, expected value, evidence strength, customer value tier, model rationale)
     2. Evidence Packet (Order items, customer details, tracking details, delivery proof, customer emails/messages)
     3. Audit Timeline (Chronological events with actor tags: Bedrock Agent, Stripe, Twilio, timestamps, and expandable JSON payloads)
     4. Decision Card with Simulated Smartphone (Interactive iPhone frame showing Rebuttal SMS alerts and interactive reply buttons 1, 2, 3 directly sending to Twilio webhook)
   - Tested and verified locally: `npm run build` completed with 0 errors; both routes return HTTP 200 OK on `localhost:3000`.
   - Committed and pushed to `origin/zaeem/hac-12-r-10-judge-console-live-demo-link`.
3. **Supabase Anon Key & RLS Schema:**
   - Appended `SUPABASE_ANON_KEY` to `.env` and `console/.env.local`.
   - Updated `schema/supabase_schema.sql` with full Row Level Security policies (read-only for `anon` role, full access for `service_role`).

## Action Required from User to Finalize R-10 Proofs
1. **Supabase Cloud Schema Execution (1 minute):**
   - Open Supabase SQL Editor: `https://supabase.com/dashboard/project/ygcmdhmoqvafxrqyqnqv/sql/new`
   - Paste the contents of `schema/supabase_schema.sql` and click **Run**.
   - (This activates the tables and RLS in the cloud so `PROOF R-10: anon key INSERT into disputes rejected by RLS = PASS`).
2. **Vercel Deployment (1 minute):**
   - Run `npx vercel login` in terminal, OR import `https://github.com/zaeem-rafiq/rebuttal` into Vercel with Root Directory set to `console`.
   - Share the deployment URL or token so we can verify:
     - `PROOF R-10: vercel url <url> HTTP 200 = PASS`
     - `PROOF R-10: Inject S1 → new case visible within 90s (docs/media/console-inject.png) = PASS`

