# Prepared verification, pending owner budget/model approval

Current authorization cap: $8 total additional verification inference. Recorded
usage estimate: $6.945951, excluding some interrupted-run and executor usage.
A $1 planning reserve is an estimate, not an invoice or verified upper bound.
The owner has been asked to approve a Sonnet generation trial and a $15 total cap.
No Sonnet generation trial has run. No new model call follows from this document.

After that approval, use the existing configuration in the original checkout:

```bash
PYTHON_DOTENV_DISABLED=1 USE_GATEWAY_MCP=false AWS_PROFILE=zaeem-khan \
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0 \
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
scoped to the US Sonnet profile; only the newly proposed generation purpose and
budget require the pending decision.

The original video remains intact. Final edited video creation separately awaits
Microsoft Edge TTS approval for the exact narration at
`docs/media/edit/submission-v3/final-cut/narration-for-approval.md`. Only that text
would be sent. Seven voice tracks remain missing; no destination approval or final
listening approval is inferred from the approved edit direction.
