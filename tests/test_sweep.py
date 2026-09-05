"""tests/test_sweep.py

Tests for agent/sweep.py deadline sweep and silence policy enforcement:
1. aged-49h -> defaults to fight, status=approved
2. due_by - 20h -> defaults to fight, status=approved
3. fresh -> untouched, status=pending
"""

import json
import sqlite3
import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

from agent.sweep import run_sweep


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Set up temporary database schema for sweep tests."""
    db_file = tmp_path / "test_sweep.db"
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE disputes (
            id TEXT PRIMARY KEY,
            order_id TEXT,
            payment_intent_id TEXT,
            charge_id TEXT,
            amount_cents INTEGER NOT NULL,
            currency TEXT NOT NULL DEFAULT 'usd',
            reason TEXT NOT NULL,
            status TEXT NOT NULL,
            evidence_due_by TEXT,
            metadata JSON NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE decisions (
            id TEXT PRIMARY KEY,
            dispute_id TEXT REFERENCES disputes(id),
            action TEXT NOT NULL,
            win_probability REAL NOT NULL DEFAULT 0.5,
            expected_value_cents INTEGER NOT NULL DEFAULT 0,
            evidence_strength TEXT NOT NULL DEFAULT 'mixed',
            customer_value TEXT NOT NULL DEFAULT 'new',
            rationale TEXT,
            owner_summary TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            approved_at TEXT,
            executed_at TEXT,
            answered_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE audit_log (
            id TEXT PRIMARY KEY,
            dispute_id TEXT,
            action TEXT NOT NULL,
            actor TEXT NOT NULL,
            details JSON NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

    import agent.tools.case_tools
    monkeypatch.setattr(agent.tools.case_tools, "LOCAL_DB_PATH", db_file)
    return db_file


def test_sweep_aged_49h_defaults_to_fight(test_db):
    """Decision aged 49h (> 48h) defaults to fight with status=approved."""
    conn = sqlite3.connect(test_db)
    cur = conn.cursor()

    # Dispute evidence due in 20 days (deadline is not approaching)
    cur.execute(
        """INSERT INTO disputes (id, amount_cents, reason, status, evidence_due_by, created_at, updated_at)
           VALUES ('dp_aged', 25000, 'fraudulent', 'needs_response', '2026-09-30T00:00:00Z', '2026-09-01T00:00:00Z', '2026-09-01T00:00:00Z')"""
    )
    # Decision created on Sept 1 at 10:00 UTC
    cur.execute(
        """INSERT INTO decisions (id, dispute_id, action, status, created_at)
           VALUES ('dec_aged', 'dp_aged', 'concede', 'pending', '2026-09-01T10:00:00Z')"""
    )
    conn.commit()
    conn.close()

    # Injected clock: Sept 3 at 11:00 UTC (49 hours after created_at)
    now = datetime(2026, 9, 3, 11, 0, 0, tzinfo=timezone.utc)

    result = run_sweep(now=now, db_path=test_db, check_stripe=False)

    assert len(result["defaulted_decisions"]) == 1
    assert result["defaulted_decisions"][0]["decision_id"] == "dec_aged"
    assert result["defaulted_decisions"][0]["action"] == "fight"
    assert result["defaulted_decisions"][0]["status"] == "approved"
    assert result["defaulted_decisions"][0]["reason"] == "aged_out"

    # Verify database state
    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM decisions WHERE id = 'dec_aged'").fetchone()
    audit_rows = conn.execute("SELECT * FROM audit_log WHERE dispute_id = 'dp_aged'").fetchall()
    conn.close()

    assert row["status"] == "approved"
    assert row["action"] == "fight"
    assert row["answered_at"] is not None
    assert len(audit_rows) >= 1


def test_sweep_due_by_minus_20h_defaults_to_fight(test_db):
    """Decision with due_by - 20h remaining (< 24h) defaults to fight with status=approved."""
    conn = sqlite3.connect(test_db)
    cur = conn.cursor()

    # Dispute evidence due on Sept 5 at 20:00 UTC
    cur.execute(
        """INSERT INTO disputes (id, amount_cents, reason, status, evidence_due_by, created_at, updated_at)
           VALUES ('dp_urgent', 15000, 'product_not_received', 'needs_response', '2026-09-05T20:00:00Z', '2026-09-04T18:00:00Z', '2026-09-04T18:00:00Z')"""
    )
    # Decision created recently (only 6 hours before now, far less than 48h)
    cur.execute(
        """INSERT INTO decisions (id, dispute_id, action, status, created_at)
           VALUES ('dec_urgent', 'dp_urgent', 'hold', 'pending', '2026-09-04T18:00:00Z')"""
    )
    conn.commit()
    conn.close()

    # Injected clock: Sept 5 at 00:00 UTC (due_by - 20h, exactly 20 hours remaining until deadline)
    now = datetime(2026, 9, 5, 0, 0, 0, tzinfo=timezone.utc)

    result = run_sweep(now=now, db_path=test_db, check_stripe=False)

    assert len(result["defaulted_decisions"]) == 1
    assert result["defaulted_decisions"][0]["decision_id"] == "dec_urgent"
    assert result["defaulted_decisions"][0]["action"] == "fight"
    assert result["defaulted_decisions"][0]["status"] == "approved"
    assert result["defaulted_decisions"][0]["reason"] == "deadline_approaching"

    # Verify database state
    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM decisions WHERE id = 'dec_urgent'").fetchone()
    conn.close()

    assert row["status"] == "approved"
    assert row["action"] == "fight"
    assert row["answered_at"] is not None


def test_sweep_fresh_remains_pending(test_db):
    """Decision that is fresh (<48h aged, >24h until deadline) remains pending."""
    conn = sqlite3.connect(test_db)
    cur = conn.cursor()

    # Dispute evidence due in 50 hours
    cur.execute(
        """INSERT INTO disputes (id, amount_cents, reason, status, evidence_due_by, created_at, updated_at)
           VALUES ('dp_fresh', 18000, 'unrecognized', 'needs_response', '2026-09-07T12:00:00Z', '2026-09-05T00:00:00Z', '2026-09-05T00:00:00Z')"""
    )
    # Decision created 10 hours ago (< 48h)
    cur.execute(
        """INSERT INTO decisions (id, dispute_id, action, status, created_at)
           VALUES ('dec_fresh', 'dp_fresh', 'fight', 'pending', '2026-09-05T00:00:00Z')"""
    )
    conn.commit()
    conn.close()

    # Injected clock: Sept 5 at 10:00 UTC (aged 10h, due in 50h)
    now = datetime(2026, 9, 5, 10, 0, 0, tzinfo=timezone.utc)

    # Also test that open Stripe dispute without case file is registered
    mock_stripe_dispute = {
        "id": "dp_stripe_new_99",
        "amount": 35000,
        "currency": "usd",
        "reason": "fraudulent",
        "status": "needs_response",
        "evidence_details": {"due_by": "2026-09-25T00:00:00Z"},
        "metadata": {"order_id": "ORD-9999"},
        "payment_intent": "pi_mock_99",
        "charge": "ch_mock_99",
    }

    with patch("agent.tools.stripe_tools.list_open_disputes", return_value=[mock_stripe_dispute]), \
         patch("agent.tools.stripe_tools.verify_live_key_guard"):
        result = run_sweep(now=now, db_path=test_db, check_stripe=True)

    # dec_fresh must remain untouched
    assert len(result["defaulted_decisions"]) == 0
    assert len(result["untouched_decisions"]) == 1
    assert result["untouched_decisions"][0]["decision_id"] == "dec_fresh"
    assert result["untouched_decisions"][0]["status"] == "pending"

    # Stripe dispute was registered as a new case file
    assert "dp_stripe_new_99" in result["opened_disputes"]

    # Verify database state
    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row
    dec_row = conn.execute("SELECT * FROM decisions WHERE id = 'dec_fresh'").fetchone()
    new_disp_row = conn.execute("SELECT * FROM disputes WHERE id = 'dp_stripe_new_99'").fetchone()
    conn.close()

    assert dec_row["status"] == "pending"
    assert dec_row["answered_at"] is None
    assert new_disp_row is not None
    assert new_disp_row["order_id"] == "ORD-9999"
    assert new_disp_row["status"] == "needs_response"
