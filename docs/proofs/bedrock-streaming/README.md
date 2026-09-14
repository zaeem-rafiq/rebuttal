# Bedrock streaming access repair - September 14, 2026

Owner authorized inspection, the minimum IAM permission change, and a 20-case evaluation rerun.

## Observed change

IAM user `rebuttal-local`, account `292341338711`, inline policy `RebuttalPreflight` already allowed `bedrock:InvokeModel`. Added only `bedrock:InvokeModelWithResponseStream` to `InvokeConfiguredProfile` and `InvokeProfileDestinations`. The profile ARN, three destination model ARNs, and `bedrock:InferenceProfileArn` condition remain unchanged. No attached policy or other identity was modified.

The existing administrative CLI profile applied the change. The evaluation uses the existing `zaeem-khan` profile, whose STS identity was verified as `rebuttal-local`.

`policy-before.json` and `policy-after.json` preserve the exact policy documents. `aws iam put-user-policy` exited 0; a subsequent `get-user-policy` readback matched the expected document exactly. The first SDK inspection stalled and was interrupted before any mutation; the successful mutation used AWS CLI.

AWS documentation requires authorization on the inference profile and its source/destination foundation models: https://docs.aws.amazon.com/bedrock/latest/userguide/geographic-cross-region-inference.html (retrieved September 14, 2026).

## Recovery

Restore the prior policy only if removing streaming access is intended:

```bash
aws --profile default iam put-user-policy --user-name rebuttal-local --policy-name RebuttalPreflight --policy-document file://docs/proofs/bedrock-streaming/policy-before.json
```

Rollback has not been executed. Re-read the policy and preserve any subsequent owner changes before restoring.

## Evaluation

Command: `PYTHON_DOTENV_DISABLED=1 PYTHONUNBUFFERED=1 .venv/bin/python evals/run.py`.

Run started September 14, 2026 at 06:06 UTC using the grounded-v2 rubric and completed all 20 cases. Exit status: **1**, because the narrative threshold was not met.

- Action match: **20/20** (threshold at least 18).
- Approval-hook match: **20/20** (threshold 20).
- Narrative judge: **4/20** (threshold at least 18).
- EV-sign match: **20/20** (threshold 20).

[Full report](../../../evals/results/2026-09-14.md). This establishes that streaming inference now works under the restricted user. It does not establish live Telegram delivery or Stripe action execution.

The narrative report contains unsupported fee and completed-action claims, along with evaluator limitations. For example, the case_06 judge explanation incorrectly treats $450 and 45,000 cents as contradictory; case_04 misinterprets a Z timestamp. These are fallible model verdicts, not 16 independently confirmed hallucinations. The fixture-to-database transformation and the judge's case-facts summary also need reconciliation before relying on the score as a calibrated quality metric. No rubric, case labels, or thresholds were changed during this run.

Model estimates and synthetic test outcomes do not establish real merchant outcomes.
