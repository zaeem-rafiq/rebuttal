"""tests/test_hooks.py

Unit tests for agent/hooks.py and ApprovalGate interrupt mechanism:
- ApprovalGate skips when under threshold, action is fight, and prob is high.
- ApprovalGate triggers when amount >= approval_amount_cents.
- ApprovalGate triggers when action != fight.
- ApprovalGate triggers when 0.35 <= win_prob <= 0.65.
- AuditHook records tool execution to audit_log.
- Answer mapping and decision status updates.
"""

import json
import sqlite3
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from strands.hooks import BeforeToolCallEvent, AfterToolCallEvent
from agent.hooks import (
    ApprovalGate,
    AuditHook,
    load_merchant_policy,
    get_agent_state,
    set_agent_state,
)


@pytest.fixture
def mock_db(tmp_path, monkeypatch):
    """Set up temporary SQLite database with required tables for hooks testing."""
    db_file = tmp_path / "test_supabase.db"
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


def test_merchant_policy_loading():
    """Verify default and file merchant policy loading."""
    policy = load_merchant_policy()
    assert "approval_amount_cents" in policy
    assert policy["approval_amount_cents"] == 20000
    assert policy["silence_action"] == "fight"


def test_approval_gate_skips_s1(mock_db):
    """Test that S1 profile (amount < 20000, fight, high win prob) skips the gate."""
    gate = ApprovalGate(policy={"approval_amount_cents": 20000})

    mock_agent = MagicMock()
    mock_agent.state = {}

    event = BeforeToolCallEvent(
        agent=mock_agent,
        selected_tool=MagicMock(),
        tool_use={"name": "submit_evidence", "toolUseId": "tu_123"},
        invocation_state={
            "dispute_id": "dp_S1",
            "amount_cents": 4800,
            "strategy": {
                "action": "fight",
                "win_probability": 0.85,
                "owner_summary": "Dispute S1 fight",
            },
        },
    )

    with patch("agent.hooks.send_owner_sms") as mock_sms:
        gate.before_tool_call(event)
        mock_sms.assert_not_called()

    assert mock_agent.state.get("gate_status") == "skipped"
    assert event.cancel_tool is False


def test_approval_gate_triggers_amount_threshold(mock_db):
    """Test that amount >= 20000 triggers interrupt even if action is fight."""
    gate = ApprovalGate(policy={"approval_amount_cents": 20000})

    mock_agent = MagicMock()
    mock_agent.state = {}

    event = BeforeToolCallEvent(
        agent=mock_agent,
        selected_tool=MagicMock(),
        tool_use={"name": "submit_evidence", "toolUseId": "tu_456"},
        invocation_state={
            "dispute_id": "dp_high",
            "amount_cents": 25000,
            "strategy": {
                "action": "fight",
                "win_probability": 0.80,
                "owner_summary": "High amount dispute",
            },
        },
    )

    with patch("agent.hooks.send_owner_sms", return_value="SM_mock123") as mock_sms, \
         patch.object(BeforeToolCallEvent, "interrupt", return_value="1") as mock_interrupt:
        gate.before_tool_call(event)
        mock_sms.assert_called_once()
        mock_interrupt.assert_called_once_with(
            "owner-approval",
            reason={
                "dispute_id": "dp_high",
                "decision_id": mock_agent.state.get("decision_id"),
                "proposed_tool": "submit_evidence",
                "proposed_action": "fight",
                "amount_cents": 25000,
                "sms_sid": "SM_mock123",
            },
        )

    assert mock_agent.state.get("gate_status") == "required"
    assert mock_agent.state.get("approval") == "fight"


def test_approval_gate_triggers_non_fight_action(mock_db):
    """Test that action != 'fight' (e.g. concede in S2) triggers interrupt."""
    gate = ApprovalGate(policy={"approval_amount_cents": 20000})

    mock_agent = MagicMock()
    mock_agent.state = {}

    event = BeforeToolCallEvent(
        agent=mock_agent,
        selected_tool=MagicMock(),
        tool_use={"name": "concede_dispute", "toolUseId": "tu_789"},
        invocation_state={
            "dispute_id": "dp_S2",
            "amount_cents": 34000,
            "strategy": {
                "action": "concede",
                "win_probability": 0.20,
                "owner_summary": "S2 VIP concede",
            },
        },
    )

    with patch("agent.hooks.send_owner_sms", return_value="SM_mock_s2") as mock_sms, \
         patch.object(BeforeToolCallEvent, "interrupt", return_value="2") as mock_interrupt:
        gate.before_tool_call(event)
        mock_sms.assert_called_once()
        mock_interrupt.assert_called_once()

    assert mock_agent.state.get("gate_status") == "required"
    assert mock_agent.state.get("approval") == "concede"

    conn = sqlite3.connect(mock_db)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM decisions WHERE dispute_id = 'dp_S2'").fetchone()
    conn.close()
    assert row is not None
    assert row["status"] == "approved"
    assert row["answered_at"] is not None


def test_approval_gate_hold_action(mock_db):
    """Test that reply 3 (hold) cancels the tool and updates status to held."""
    gate = ApprovalGate(policy={"approval_amount_cents": 20000})

    mock_agent = MagicMock()
    mock_agent.state = {}

    event = BeforeToolCallEvent(
        agent=mock_agent,
        selected_tool=MagicMock(),
        tool_use={"name": "concede_dispute", "toolUseId": "tu_hold"},
        invocation_state={
            "dispute_id": "dp_hold",
            "amount_cents": 30000,
            "strategy": {
                "action": "concede",
                "win_probability": 0.40,
                "owner_summary": "Hold dispute",
            },
        },
    )

    with patch("agent.hooks.send_owner_sms", return_value="SM_mock_hold"), \
         patch.object(BeforeToolCallEvent, "interrupt", return_value="3"):
        gate.before_tool_call(event)

    assert "Owner chose hold" in str(event.cancel_tool)

    conn = sqlite3.connect(mock_db)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM decisions WHERE dispute_id = 'dp_hold'").fetchone()
    conn.close()
    assert row["status"] == "held"
    assert row["answered_at"] is not None


def test_audit_hook_records_tool_call(mock_db):
    """Test that AuditHook records tool execution to audit_log table."""
    audit_hook = AuditHook()
    mock_agent = MagicMock()
    mock_agent.state = {}
    event = AfterToolCallEvent(
        agent=mock_agent,
        selected_tool=MagicMock(),
        tool_use={"name": "concede_dispute", "input": {"dispute_id": "dp_audit"}},
        result={"status": "lost"},
        invocation_state={"dispute_id": "dp_audit"},
        duration=0.25,
        exception=None,
    )

    audit_hook.after_tool_call(event)

    conn = sqlite3.connect(mock_db)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM audit_log WHERE dispute_id = 'dp_audit'").fetchone()
    conn.close()

    assert row is not None
    assert row["action"] == "tool_executed:concede_dispute"
    assert row["actor"] == "executor"
    details = json.loads(row["details"])
    assert details["tool"] == "concede_dispute"
    assert details["duration"] == 0.25
