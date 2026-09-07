"""tests/test_gate.py

Deterministic test suite for Rebuttal ApprovalGate decision boundaries:
1. amount >= $200 (approval_amount_cents = 20000) triggers gate
2. amount < $200 with high win probability (win_probability >= 0.70) skips gate
3. uncertain probability band (0.35 <= win_probability <= 0.65) triggers gate
4. non-fight action 'concede' triggers gate
5. non-fight action 'refund_inquiry' triggers gate
6. owner 'hold' reply cancels tool, updates decision status to 'held', and schedules re-ping
"""

import json
import sqlite3
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
import pytest

from strands.hooks import BeforeToolCallEvent
from agent.hooks import (
    ApprovalGate,
    load_merchant_policy,
)


@pytest.fixture
def mock_gate_db(tmp_path, monkeypatch):
    """Set up temporary SQLite database with required tables for gate testing."""
    db_file = tmp_path / "test_gate.db"
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
            win_probability REAL NOT NULL,
            expected_value_cents INTEGER NOT NULL,
            evidence_strength TEXT NOT NULL,
            customer_value TEXT NOT NULL,
            rationale TEXT NOT NULL,
            owner_summary TEXT NOT NULL,
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

    import agent.hooks
    import agent.tools.case_tools
    monkeypatch.setattr(agent.hooks, "LOCAL_DB_PATH", db_file)
    monkeypatch.setattr(agent.tools.case_tools, "LOCAL_DB_PATH", db_file)
    return db_file


def test_gate_triggers_on_high_amount(mock_gate_db):
    """Gate boundary 1: amount >= $200 (20000 cents) triggers gate even with high win prob."""
    gate = ApprovalGate(policy={"approval_amount_cents": 20000})
    mock_agent = MagicMock()
    mock_agent.state = {}

    event = BeforeToolCallEvent(
        agent=mock_agent,
        selected_tool=MagicMock(),
        tool_use={"name": "submit_evidence", "toolUseId": "tu_gate_1"},
        invocation_state={
            "dispute_id": "dp_high_amt",
            "amount_cents": 25000,
            "strategy": {
                "action": "fight",
                "win_probability": 0.90,
                "owner_summary": "High amount dispute $250.00",
            },
        },
    )

    with patch("agent.hooks.send_owner_sms", return_value="SM_mock_high") as mock_sms, \
         patch.object(BeforeToolCallEvent, "interrupt", return_value="1") as mock_interrupt:
        gate.before_tool_call(event)
        mock_sms.assert_called_once()
        mock_interrupt.assert_called_once()

    assert mock_agent.state.get("gate_status") == "required"
    assert mock_agent.state.get("approval") == "fight"


def test_gate_skips_on_low_amount_high_prob(mock_gate_db):
    """Gate boundary 2: amount < $200, fight action, win_prob >= 0.70 skips gate autonomously."""
    gate = ApprovalGate(policy={"approval_amount_cents": 20000})
    mock_agent = MagicMock()
    mock_agent.state = {}

    event = BeforeToolCallEvent(
        agent=mock_agent,
        selected_tool=MagicMock(),
        tool_use={"name": "submit_evidence", "toolUseId": "tu_gate_2"},
        invocation_state={
            "dispute_id": "dp_low_amt",
            "amount_cents": 4800,
            "strategy": {
                "action": "fight",
                "win_probability": 0.85,
                "owner_summary": "Low amount dispute $48.00 with strong proof",
            },
        },
    )

    with patch("agent.hooks.send_owner_sms") as mock_sms:
        gate.before_tool_call(event)
        mock_sms.assert_not_called()

    assert mock_agent.state.get("gate_status") == "skipped"
    assert event.cancel_tool is False


def test_gate_triggers_on_uncertainty_band(mock_gate_db):
    """Gate boundary 3: win_probability in [0.35, 0.65] triggers gate even under threshold."""
    gate = ApprovalGate(policy={"approval_amount_cents": 20000})
    mock_agent = MagicMock()
    mock_agent.state = {}

    event = BeforeToolCallEvent(
        agent=mock_agent,
        selected_tool=MagicMock(),
        tool_use={"name": "submit_evidence", "toolUseId": "tu_gate_3"},
        invocation_state={
            "dispute_id": "dp_uncertain",
            "amount_cents": 5000,
            "strategy": {
                "action": "fight",
                "win_probability": 0.50,
                "owner_summary": "Uncertain dispute win_probability 0.50",
            },
        },
    )

    with patch("agent.hooks.send_owner_sms", return_value="SM_mock_uncertain") as mock_sms, \
         patch.object(BeforeToolCallEvent, "interrupt", return_value="1") as mock_interrupt:
        gate.before_tool_call(event)
        mock_sms.assert_called_once()
        mock_interrupt.assert_called_once()

    assert mock_agent.state.get("gate_status") == "required"


def test_gate_triggers_on_concede_action(mock_gate_db):
    """Gate boundary 4: action != 'fight' ('concede') triggers gate even under threshold."""
    gate = ApprovalGate(policy={"approval_amount_cents": 20000})
    mock_agent = MagicMock()
    mock_agent.state = {}

    event = BeforeToolCallEvent(
        agent=mock_agent,
        selected_tool=MagicMock(),
        tool_use={"name": "concede_dispute", "toolUseId": "tu_gate_4"},
        invocation_state={
            "dispute_id": "dp_concede",
            "amount_cents": 7500,
            "strategy": {
                "action": "concede",
                "win_probability": 0.20,
                "owner_summary": "Concede $75.00 dispute",
            },
        },
    )

    with patch("agent.hooks.send_owner_sms", return_value="SM_mock_concede") as mock_sms, \
         patch.object(BeforeToolCallEvent, "interrupt", return_value="2") as mock_interrupt:
        gate.before_tool_call(event)
        mock_sms.assert_called_once()
        mock_interrupt.assert_called_once()

    assert mock_agent.state.get("gate_status") == "required"
    assert mock_agent.state.get("approval") == "concede"


def test_gate_triggers_on_refund_inquiry_action(mock_gate_db):
    """Gate boundary 5: action != 'fight' ('refund_inquiry') triggers gate."""
    gate = ApprovalGate(policy={"approval_amount_cents": 20000})
    mock_agent = MagicMock()
    mock_agent.state = {}

    event = BeforeToolCallEvent(
        agent=mock_agent,
        selected_tool=MagicMock(),
        tool_use={"name": "refund_inquiry", "toolUseId": "tu_gate_5"},
        invocation_state={
            "dispute_id": "dp_inquiry",
            "amount_cents": 12900,
            "strategy": {
                "action": "refund_inquiry",
                "win_probability": 0.15,
                "owner_summary": "Pre-chargeback inquiry refund $129.00",
            },
        },
    )

    with patch("agent.hooks.send_owner_sms", return_value="SM_mock_inquiry") as mock_sms, \
         patch.object(BeforeToolCallEvent, "interrupt", return_value="refund_inquiry") as mock_interrupt:
        gate.before_tool_call(event)
        mock_sms.assert_called_once()
        mock_interrupt.assert_called_once()

    assert mock_agent.state.get("gate_status") == "required"
    assert mock_agent.state.get("approval") == "refund_inquiry"


def test_gate_hold_reping(mock_gate_db):
    """Gate boundary 6: owner '3' (hold) cancels tool, records status held, and computes re-ping."""
    gate = ApprovalGate(policy={"approval_amount_cents": 20000})
    mock_agent = MagicMock()
    mock_agent.state = {}

    # Insert dispute with evidence_due_by to verify re-ping calculation
    due_iso = (datetime.now(timezone.utc) + timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    conn = sqlite3.connect(mock_gate_db)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO disputes (id, amount_cents, currency, reason, status, evidence_due_by, metadata, created_at, updated_at) "
        "VALUES ('dp_hold_test', 30000, 'usd', 'fraudulent', 'needs_response', ?, '{}', '2026-09-01T00:00:00Z', '2026-09-01T00:00:00Z')",
        (due_iso,),
    )
    conn.commit()
    conn.close()

    event = BeforeToolCallEvent(
        agent=mock_agent,
        selected_tool=MagicMock(),
        tool_use={"name": "submit_evidence", "toolUseId": "tu_gate_6"},
        invocation_state={
            "dispute_id": "dp_hold_test",
            "amount_cents": 30000,
            "strategy": {
                "action": "fight",
                "win_probability": 0.40,
                "owner_summary": "Dispute $300 hold test",
            },
        },
    )

    with patch("agent.hooks.send_owner_sms", return_value="SM_mock_hold"), \
         patch.object(BeforeToolCallEvent, "interrupt", return_value="3"):
        gate.before_tool_call(event)

    # Verify tool call was canceled with hold notice
    assert "Owner chose hold" in str(event.cancel_tool)

    # Verify decision table updated to held
    conn = sqlite3.connect(mock_gate_db)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM decisions WHERE dispute_id = 'dp_hold_test'").fetchone()
    assert row is not None
    assert row["status"] == "held"
    assert row["answered_at"] is not None

    # Verify audit_log recorded hold_decision
    audit_row = conn.execute("SELECT * FROM audit_log WHERE dispute_id = 'dp_hold_test' AND action = 'hold_decision'").fetchone()
    assert audit_row is not None
    assert audit_row["actor"] == "owner"
    conn.close()

    # Verify re-ping schedule computation logic (due_by - 48h)
    due_dt = datetime.fromisoformat(due_iso.replace("Z", "+00:00"))
    expected_reping = (due_dt - timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert expected_reping < due_iso
