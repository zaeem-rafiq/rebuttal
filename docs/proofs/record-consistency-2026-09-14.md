# Owner decision and closure attribution fixes

Implemented and verified locally on branch `codex/record-consistency-20260914`, based on `14ad4eaf8bcb17b6ded0b0865fa25453003d4b9b`. No cloud migration, deployment, historical data repair, or submission edit was performed for this change.

## Behavior and scope

- Owner reply -> select one latest decision across local/cloud stores -> resume/fallback action -> update that exact decision in both stores. Fight, concession, inquiry refund, and Hold share the writer. Older decisions remain unchanged; a cloud-only decision works when the local database exists.
- ApprovalGate uses the same writer and caches approval only after persistence succeeds. Configured cloud failures and missing cloud update rows are surfaced. Writes are not a distributed transaction; a local update or Stripe action can precede a synchronization failure, so read back the provider outcome before retrying a failed reply.
- Closure webhook -> query local/cloud execution audits -> store a confirmed action, or record a skip reason. Approval, an arbitrary payload action, and Stripe `lost` do not establish an executed action. Missing, conflicting, or unavailable audit evidence does not create outcome memory. Terminal case status and the closure audit are still recorded.
- Fresh SQLite databases include `answered_at`; initialization upgrades older SQLite databases without removing rows. The canonical PostgreSQL schema now permits decision status `held`. The separate SQL migration is prepared and **not applied**.

## Verification

Verification ran from an isolated worktree using the existing Python environment. Cloud configuration was explicitly cleared for offline tests. To repeat it from a Git clone after creating its `.venv` and installing `requirements.txt`, use these portable commands:

```sh
PYTHON_DOTENV_DISABLED=1 AWS_EC2_METADATA_DISABLED=true SUPABASE_URL= SUPABASE_SERVICE_KEY= .venv/bin/python scripts/seed_supabase.py --local-only --verify
PYTHON_DOTENV_DISABLED=1 AWS_EC2_METADATA_DISABLED=true SUPABASE_URL= SUPABASE_SERVICE_KEY= STRIPE_SECRET_KEY=sk_test_mock_for_unit_tests .venv/bin/python -m pytest -q
git diff --check
```

Observed: fixture seed exit 0; final full suite **256 passed**, 20 dependency deprecation warnings; diff check exit 0. The new real-schema upgrade test first reproduced `sqlite3.OperationalError: no such column: answered_at`, then passed after the initializer correction. New tests cover exact-row preservation, cloud-only decision selection and all four reply branches, optional values, surfaced cloud failures, actual schema upgrades, confirmed execution attribution, absent/conflicting evidence, and preserved terminal state. Independent read-only review found no blocking issue in the scoped diff.

These tests use temporary SQLite databases and offline provider doubles. They do not establish live Supabase writes, PostgreSQL migration execution, Stripe actions, Telegram delivery, or a new full-cloud run. The console is unchanged; its suite was not rerun.

## Required release steps

1. Review and apply `schema/migrations/20260914_owner_decision_sync.sql` to the intended nonproduction cloud database. Verify that existing decisions are preserved and Hold is accepted. This requires separate authorization.
2. Deploy this source and initialize any existing SQLite database with `scripts.seed_supabase.init_local_db` before processing replies.
3. Exercise an owner decision in Stripe test mode and read back the exact decision ID, action, status, timestamp, execution audit, and closure-memory result from the providers.
4. Only then revise the submission's cloud-verification claims. Do not alter the submitted project after its deadline.

An early closure event can skip memory before an execution audit arrives; no retry/backfill is added. Existing historical memory is not repaired. The separate inquiry case-status spelling mismatch (`refunded_inquiry` versus the cloud schema's `charge_refunded`) and the deadline-sweep write path remain outside this owner-decision fix. Do not claim the entire inquiry or sweep flow is repaired. Roll back application behavior by reverting this commit; retain the additive schema changes until stored `held` rows have been assessed.
