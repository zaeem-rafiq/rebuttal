# Approved verification in progress

Current authorization cap: $15 total additional verification inference. Recorded
usage estimate: $6.945951, excluding some interrupted-run and executor usage.
A $1 planning reserve is an estimate, not an invoice or verified upper bound.
The owner explicitly approved both the Sonnet generation trial under this total cap
and sending the prepared narration to Microsoft Edge TTS. The commands below are
authorized; their results must still be observed before any acceptance claim.

Use the existing model configuration in the original checkout. BEDROCK_STREAMING=false
selects the installed SDK non-streaming transport, covered by the existing InvokeModel
permission; no AWS permission expansion is needed. The default remains streaming:

```bash
PYTHON_DOTENV_DISABLED=1 USE_GATEWAY_MCP=false AWS_PROFILE=zaeem-khan \
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0 BEDROCK_STREAMING=false \
BEDROCK_JUDGE_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0 \
EVAL_REPORT_PATH=evals/results/2026-09-14-sonnet-generation-trial.md \
PYTHONUNBUFFERED=1 .venv/bin/python evals/run.py

PYTHON_DOTENV_DISABLED=1 USE_GATEWAY_MCP=false AWS_PROFILE=zaeem-khan \
BEDROCK_JUDGE_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0 \
CONTROL_REPORT_PATH=evals/results/2026-09-14-sonnet-controls-v11.json \
PYTHONUNBUFFERED=1 .venv/bin/python -m evals.check_output_grounding
```

Choose fresh filenames if these already exist. The fixed benchmark uses isolated
synthetic records and mocked Stripe intake with production-equivalent tool metadata
and ID validation. It does not execute Stripe action tools. The control suite now
contains 26 cases; the three-call evaluator is not yet model-verified. Compare each
control criterion, not only its overall boolean. Review all benchmark outputs
against actual tool records, including passing judgments. Preserve failures.

Keep the application model unchanged until the trial justifies adoption. Do not
change production IAM, deploy, publish, upload the video, or submit the hackathon
entry from this preparation. The existing applied evaluator permission is already
scoped to the US Sonnet profile; the owner has now approved the generation purpose and budget.

The original video remains intact. Microsoft Edge TTS is now approved for the exact narration at
`docs/media/edit/submission-v3/final-cut/narration-for-approval.md`. Only that text
is authorized for transmission. Final listening and artifact approval remain separate
from the approved narration-generation destination.
