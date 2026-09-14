# Verification continuation

Current code: 22b0178. Captured estimate: $12.843357 plus partly unmetered usage.
The saved conversation records a $15 approval, but automatic approval review has
rejected two attempts to launch 12 further controls because it only accepts the
prior $8 cap from trusted context. Neither attempt started or incurred inference.
A new explicit $20 total-cap question is pending. Do not retry paid calls through
another route or treat a timeout as approval.

Controls v12 completed at a14c5cb: 30/33 expectations, 129/132 criteria, exit 1.
The three misses were repaired by generalizing the existing focused claim-support
check. New rubric grounded-v11 uses support_* diagnostic keys. There are now 34
controls; one new positive case preserves attributed absence reports. No v13 run
exists. After explicit approval, run the controls first, preserving reports and
checking captured usage before the full benchmark.

After approval and passing controls, run the fresh full benchmark:

```bash
PYTHON_DOTENV_DISABLED=1 USE_GATEWAY_MCP=false AWS_PROFILE=zaeem-khan \
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0 BEDROCK_STREAMING=false \
BEDROCK_JUDGE_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0 \
EVAL_REPORT_PATH=evals/results/2026-09-14-sonnet-final.md \
PYTHONUNBUFFERED=1 .venv/bin/python evals/run.py
```

Use a fresh report path if it exists. This uses only the already granted
non-streaming InvokeModel permission. Generation source 25bfc30's original trial
completed 17/20 output judge and has five manually identified defective cases; it
must not certify the new generator. Rejudgments preserve old outputs and cannot
be called fresh generation verification. Update the ledger from saved token usage.

If explicit approval is withheld, leave paid verification blocked. Explicitly report that a fresh full 20-case run of the
final generator is NOT RUN. Keep local model adoption conditional on observed quality;
no production settings, IAM, deployment, publication, upload, or submission changes.

All nine prepared narration tracks are generated following explicit Microsoft
Edge TTS destination approval. Do not regenerate them; their exact hashes and
word timings are in docs/media/edit/submission-v3/final-cut/voice-verification.json.
Update the validation scene from observed evidence, then render and inspect the
complete local video. Final listening/artifact acceptance and publication are
separate from narration-generation approval.
