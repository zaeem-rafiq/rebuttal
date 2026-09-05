# Rebuttal Observability & Tracing Documentation (R-09)

Amazon Bedrock AgentCore GenAI Observability and OpenTelemetry instrumentation for autonomous dispute defense.

## S1 Dispute Case Run (Captured Trace)

- **Trace ID:** `6a9c9b885cc07bc474321c9a4c03153b`
- **Total Spans:** `92`
- **Scenario:** S1 (Product Not Received — $48.00)
- **Session ID:** `rebuttal-dp_S1-2748d5a8a8454332bd219f14d6d91e96`
- **Agent Runtime ARN:** `arn:aws:bedrock-agentcore:us-east-1:292341338711:runtime/rebuttal-pASUe6CVmu`
- **Endpoint:** `DEFAULT`
- **AWS Region:** `us-east-1`
- **AWS Account:** `292341338711`

## Where to Find in AWS Console

1. **CloudWatch GenAI Observability Dashboard:**
   [AWS CloudWatch GenAI Observability (us-east-1)](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#gen-ai-observability/agent-core)
   Navigate to **Agents** > **rebuttal** > **Traces** and search for Trace ID `6a9c9b885cc07bc474321c9a4c03153b`.

2. **CloudWatch Logs:**
   - Log Group: `/aws/bedrock-agentcore/runtimes/rebuttal-pASUe6CVmu-DEFAULT`
   - OTel Logs Stream: `otel-rt-logs`
   - Application Logs: `--log-stream-name-prefix "2026/09/05/[runtime-logs]"`

3. **CLI Inspection:**
   ```bash
   # Show full trace visualization
   agentcore obs show --trace-id 6a9c9b885cc07bc474321c9a4c03153b

   # List traces for session
   agentcore obs list --session-id rebuttal-dp_S1-2748d5a8a8454332bd219f14d6d91e96
   ```

## Visual Trace Screenshot

The full hierarchical waterfall visualization with 92 spans (including multi-agent graph nodes, LLM calls, tool executions, and runtime API events) is captured at:
`docs/media/trace-S1.png`

## Key Spans in the Trace

| Span Name | Type | Duration | Details |
|---|---|---|---|
| `process_case_async (S1)` | Root Task | 4,285 ms | Asynchronous dispute processing lifecycle |
| `intake` | Agent Node | 142 ms | Dispute context and order discovery |
| `orders` | Agent Node | 620 ms | Order history extraction (`get_order`, `list_customer_orders`) |
| `shipping` | Agent Node | 580 ms | Carrier tracking extraction (`get_shipment`) |
| `comms` | Agent Node | 490 ms | Customer email and message context (`get_customer_messages`) |
| `history` | Agent Node | 510 ms | Long-term memory semantic search (`get_past_dispute_outcomes`) |
| `strategy` | Agent Node | 840 ms | Bedrock Claude 3.5 Haiku structured strategy formulation |
| `drafter` | Agent Node | 620 ms | Evidence packet compilation |
| `executor` | Agent Run | 1,220 ms | Execution of approved strategy |
| `execute_tool record_case` | Tool Call | 494 ms | Local SQLite + Supabase case log update |
| `execute_tool submit_evidence` | Tool Call | 420 ms | Stripe Disputes API evidence submission |
| `Bedrock AgentCore.CreateEvent` | Runtime API | 82 ms | AgentCore Short-Term Memory event emission |
