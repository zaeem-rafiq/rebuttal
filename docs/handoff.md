# Rebuttal Build Queue Handoff

## Current Status
- **Active Issue:** HAC-22 (R-17 · Amplify console case file styling + demo switcher)
- **Linear State:** Ready to pick
- **Queue Progress:** Core M5 Complete (R-00 through R-11 Done). HAC-19 (R-15) Done. HAC-20 (R-18) Done. HAC-17 (S-A) Skipped. HAC-18 (S-B) Done. HAC-21 (R-16) Done.
- **Queue Order:** HAC-19 (Done) → HAC-20 (Done) → HAC-17 (Skipped) → HAC-18 (Done) → HAC-21 (Done) → HAC-22.

## What Was Done
1. Completed HAC-19 (R-15 · Dress rehearsal runbook + demo reset script).
2. Completed HAC-20 (R-18 · Scenario S3: refund an inquiry before chargeback).
3. Evaluated HAC-17 (S-A · Stretch: Gmail comms tool): User explicitly chose to skip S-A, keeping direct Supabase customer communications.
4. Completed HAC-18 (S-B · Stretch: AgentCore Gateway exposes order and tracking tools as MCP).
5. Completed HAC-21 (R-16 · Decision evals harness):
   - Implemented 6 deterministic unit tests in `tests/test_gate.py` covering approval gate boundaries (amount $\ge \$200$, uncertainty band $0.35-0.65$, non-fight actions, hold re-ping).
   - Created 20 synthetic cases in `evals/cases/case_01.json` – `case_20.json` spanning reason codes $\times$ evidence strength $\times$ customer value.
   - Built runner `evals/run.py` evaluating action match, policy gate match, Bedrock LLM narrative judge, and expected value sign.
   - Reached 20/20 Action Match (100%), 20/20 Gate Match (100%), 18/20 Narrative Judge Pass (90%), and 20/20 EV Sign Pass (100%).
   - Documented failure modes in `docs/evals.md`, updated `README.md` with evals summary table, recorded proofs in `docs/proofs/R-16.md`, committed (`ad4e968`), pushed, commented, and marked HAC-21 Done in Linear.

## Next Issue
- **HAC-22 (R-17 · Amplify console case file styling + demo switcher):**
  - Verify pre-conditions (HAC-21 Done, design case file specification in `.agents/rules/design-case-file.md`).
  - Style Amplify console to strict Case File design system: desk `#EDECE6`, sheet `#FFFFFF`, ink `#111418`, secondary ink `#5C6370`, rules `#D4D4D8`, highlighter `#FFE96B`, decision green `#14713A`, decision red `#B91C1C`.
  - Zero rounded corners except stamp at 2px; no blue anywhere; Space Grotesk + IBM Plex Mono; open file ~65% viewport + dense roster below.
  - Scenario switcher: plain text "Scenario: S1 · S2 · S3" in header.
  - Stamp landing transition (250ms ease-out) and quiet state ("Nothing needs you.").

