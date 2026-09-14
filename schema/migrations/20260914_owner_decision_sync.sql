-- Apply before deploying owner-decision synchronization. No existing rows are removed.
BEGIN;
ALTER TABLE decisions ADD COLUMN IF NOT EXISTS answered_at TIMESTAMPTZ;
ALTER TABLE decisions DROP CONSTRAINT IF EXISTS decisions_status_check;
ALTER TABLE decisions ADD CONSTRAINT decisions_status_check
    CHECK (status IN ('pending', 'approved', 'executed', 'overridden', 'held'));
COMMIT;
