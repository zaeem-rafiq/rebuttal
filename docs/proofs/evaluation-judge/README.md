# Sonnet verification access and usage

The owner explicitly approved up to **$50 total paid verification** on September
14, 2026 and asked to finish. Earlier budget approval-review blocks are resolved.
The current captured token estimate and incomplete-usage caveats are recorded in
[usage-ledger.json](usage-ledger.json); this is not a billing readback.

The previously approved RebuttalEvaluationJudge IAM policy permits non-streaming
bedrock:InvokeModel for the US Sonnet 4.5 inference profile and verified US model
ARNs. Its applied policy/readback evidence is preserved here. The verification
uses BEDROCK_STREAMING=false and requires no later IAM expansion. The ignored local `.env` now selects Sonnet 4.5 with streaming disabled after
final acceptance. Code fallback defaults and cloud configuration remain unchanged.

Sanitized Stripe TEST records are authorized for verification and the video;
client_secret and receipt_url are excluded. No deployment, publication, upload,
production financial action, or submission is authorized by the verification cap.

Current implementation and acceptance evidence are tracked in
[output-grounding verification](../../output-grounding-verification.md).
Preserve failed raw judgments separately from source-review adjudications.
Controls assess known distinctions; they do not establish a population error rate.
