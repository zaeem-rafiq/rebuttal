---
trigger: always_on
---

# Rebuttal — Global Operating Rules

You are working on **Rebuttal**, an autonomous chargeback-defense agent for small Stripe merchants built on the AWS Strands Agents SDK and Amazon Bedrock AgentCore for the AWS "Agents for Humans" hackathon.

## Global Rules — Every Issue Inherits These

1. **Secret Safety:**
   - Secrets only from `.env` (gitignored) locally and AWS Secrets Manager in the cloud.
   - Never print a secret value to stdout, stderr, logs, or chat. Print only sanitized checks (e.g. `sk_test_` prefix check).

2. **Live-Key Guard:**
   - Every Stripe client initialization MUST assert `STRIPE_SECRET_KEY.startswith("sk_test_")` and exit immediately otherwise.
   - `DEMO_MODE=true` only controls the Stripe test-outcome token; it NEVER alters decision logic.

3. **Proof Lines:**
   - Output `PROOF R-xx: <check> = PASS|FAIL` to the transcript AND append the same lines to `docs/proofs/R-xx.md`.
   - An issue is complete ONLY when every listed proof line evaluates to `PASS`.

4. **Turn Bound Hard Stop:**
   - The turn bound and time budget are hard stops.
   - If the turn or time bound is reached, immediately write the blocker document even if close to finishing.

5. **Protected Paths (All Issues):**
   - `LICENSE`, `.env*`, `docs/proofs/**`, `docs/blockers/**`, `docs/decisions/**` (append-only).
   - `data/fixtures/**` is protected after R-01 completion.
   - `agent/models.py` is protected after R-02 completion (changes require an ADR in `docs/decisions/`).

6. **Fast-Moving SDK Verification:**
   - Verify Strands and Bedrock AgentCore APIs against the installed package documentation and introspection before using them.

7. **Cost and Resource Safeguards:**
   - Ask the user before running anything that costs money beyond trivial cents or provisions long-running cloud infrastructure.

---

## Six-Field Issue Format

Every issue in the Rebuttal project follows this six-field structure:

1. **End-state:** A single, measurable, verifiable end condition.
2. **Proof-of-success:** Exact proof lines printed to transcript and recorded in `docs/proofs/R-xx.md`.
3. **Turn/time bound:** Explicit budget in wall-clock time and LLM turns.
4. **Protected paths:** Explicit list of files/directories that cannot be modified.
5. **Pre-conditions:** Prerequisites and predecessor proofs that must be PASS.
6. **Failure handoff:** After 2 failed attempts or 30 minutes without a passing proof: write `docs/blockers/R-xx.md` (what was tried, exact error, hypothesis, smallest next step), print `BLOCKED R-xx`, and stop.
