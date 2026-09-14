# Evaluation judge access proposal

Applied and read back on September 14, 2026 after explicit owner approval. The Haiku judge fails elementary positive controls,
including dollar/cents equivalence and quoted evidence citations. Those results
cannot substantiate evaluator accuracy.

Completed action: added a separate inline policy named RebuttalEvaluationJudge to IAM
user rebuttal-local. It permits only non-streaming InvokeModel for the US Sonnet
4.5 inference profile and its three verified US destination model ARNs. Existing
Haiku permissions remain untouched. The original $5 additional inference cap was
raised by the owner to $8 for bounded controls and the existing benchmark. Sonnet
has been used only as the evaluator. The captured token estimate is $6.945951;
some interrupted-run and executor usage is unmetered, so this is not a billing
total. Further inference is paused. A Sonnet generation trial and a $15 total cap
have been proposed and remain pending owner approval.
The owner separately approved sanitized Stripe test-record use for verification
and the demo; client_secret and receipt_url remain excluded. No deployment,
publication, or submission is authorized.

AWS get-inference-profile and get-user-policy both exited 0 on 2026-09-14.
Before application, list-user-policies showed only RebuttalPreflight. The
put-user-policy and get-user-policy commands both exited 0; the readback in
applied-policy-readback.json exactly equals proposed-policy.json. Existing
Haiku permissions were preserved. Controls remain under investigation: switching
to Sonnet alone did not eliminate false positives. Recovery is deletion of this
separate inline policy only, after confirming it still matches this proposal.
