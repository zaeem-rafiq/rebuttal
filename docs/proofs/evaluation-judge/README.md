# Sonnet verification access and usage

The owner-approved RebuttalEvaluationJudge inline policy was applied to IAM user
rebuttal-local on September 14, 2026. Its readback exactly matched the preserved
proposal; put-user-policy and get-user-policy both exited 0. It allows only
non-streaming bedrock:InvokeModel for the US Sonnet 4.5 inference profile and its
three verified US destination model ARNs. Existing Haiku permissions remained
unchanged. No later permission expansion has been made in this task.

The owner subsequently approved Sonnet generation for a bounded verification
trial and raised the total additional inference cap to $15. The installed Strands
SDK uses its non-streaming transport when BEDROCK_STREAMING=false, so the trial
required no streaming permission or new infrastructure. The full trial completed
at generation revision 25bfc30, with action/gate/EV 20/20 and output judge 17/20;
exit 1. It did not qualify the build for completion.

The captured token-derived total after controls v12 is $12.843357.
Some interrupted-run and executor usage remains unmetered. The $1 planning reserve
in usage-ledger.json is an estimate, not a billing readback or verified upper bound.
Expanded controls v12 completed 30/33, exit 1. Automatic approval review then
rejected two attempted 12-control follow-ups before launch, accepting only the
earlier $8 cap from trusted context despite the saved later approval. A new
explicit $20 total-cap question is pending. Do not retry paid calls until it is
answered and the approval gate resolves.

Sonnet as a single broad judge still misses some defects. The composed v11 controls
matched all 26 cases, but an independent review identified inaccurate component
explanations; see ../output-grounding/sonnet-controls-v11-review.md. Passing the
small control set is not a population accuracy guarantee.

Sanitized Stripe TEST records are authorized for verification and the video;
client_secret and receipt_url remain excluded. No deployment, publication, upload,
production financial action, or submission is authorized. Recovery for this policy
is deletion of this separate inline policy only, after confirming it still matches
the preserved proposal and obtaining any required authorization.
