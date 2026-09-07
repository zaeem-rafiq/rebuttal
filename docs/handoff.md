# Rebuttal Build Queue Handoff

## Current Status
- **Active Issue:** HAC-21 (R-16 · Full evaluation run against the 10-dispute golden set)
- **Linear State:** Ready to pick
- **Queue Progress:** Core M5 Complete (R-00 through R-11 Done). HAC-19 (R-15) Done. HAC-20 (R-18) Done. HAC-17 (S-A) Skipped. HAC-18 (S-B) Done.
- **Queue Order:** HAC-19 (Done) → HAC-20 (Done) → HAC-17 (Skipped) → HAC-18 (Done) → HAC-21 → HAC-22.

## What Was Done
1. Completed HAC-19 (R-15 · Dress rehearsal runbook + demo reset script).
2. Completed HAC-20 (R-18 · Scenario S3: refund an inquiry before chargeback).
3. Evaluated HAC-17 (S-A · Stretch: Gmail comms tool): User explicitly chose to skip S-A, keeping direct Supabase customer communications.
4. Completed HAC-18 (S-B · Stretch: AgentCore Gateway exposes order and tracking tools as MCP):
   - Provisioned Bedrock AgentCore Gateway `rebuttal-mcp-gateway` (ID: `rebuttal-mcp-gateway-oamgt4bt21`) in `us-east-1` with Cognito OAuth JWT authentication.
   - Deployed Lambda target `rebuttal-gateway-tools` and attached target `rebuttal-evidence-tools` exposing `lookup_order` and `get_tracking` backed by Supabase.
   - Integrated Strands `MCPClient` over streamable HTTP into `agent/graph.py` and `agent/tools/gateway_client.py` with automatic name adaptation and fallback.
   - Updated `docs/architecture.mmd` architecture diagram.
   - Verified proofs (`PROOF S-B: agent.tool_names includes lookup_order,get_tracking = PASS`, `PROOF S-B: S1 via Gateway → action=fight = PASS`), committed (`7698589`), pushed, posted comment, and closed HAC-18 in Linear.

## Next Issue
- **HAC-21 (R-16 · Full evaluation run against the 10-dispute golden set):**
  - Verify pre-conditions (HAC-18 Done or skipped).
  - Execute full golden set evaluation across 10 disputes (100% agreement on action, evidence pack valid, win probability within tolerance).
  - STOP CONDITION: Stop after first full eval run and hand FAIL traces in `evals/results/<date>.md` before tuning any prompt.

