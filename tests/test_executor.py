"""tests/test_executor.py

Unit tests for agent/executor.py and agent/tools/case_tools.py:
- Executor agent instantiation and tool configuration.
- Record case and audit logging.
- Customer email dispatch recording.
- Evidence mapping logic: narrative -> uncategorized_file and DEMO_MODE winning_evidence token.
- Deterministic execute_strategy for fight, concede, and refund_inquiry.
"""

import json
import sqlite3
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from agent.models import DisputeStrategy, EvidencePacket
from agent.tools.case_tools import record_case, send_customer_email
from agent.executor import build_executor_agent, execute_strategy, LOCAL_DB_PATH


@pytest.fixture
def mock_db(tmp_path, monkeypatch):
    """Set up temporary SQLite database with required tables for tests."""
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
        CREATE TABLE audit_log (
            id TEXT PRIMARY KEY,
            dispute_id TEXT,
            action TEXT NOT NULL,
            actor TEXT NOT NULL,
            details JSON NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE customer_messages (
            id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            order_id TEXT,
            direction TEXT NOT NULL,
            channel TEXT NOT NULL,
            subject TEXT,
            body TEXT NOT NULL,
            has_shipping_change INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE orders (
            id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            amount_cents INTEGER NOT NULL,
            currency TEXT NOT NULL DEFAULT 'usd',
            status TEXT NOT NULL
        )
    """)
    cur.execute("""
        INSERT INTO disputes (id, order_id, amount_cents, currency, reason, status, metadata, created_at, updated_at)
        VALUES ('dp_test_1', 'ORD-TEST-1', 4800, 'usd', 'product_not_received', 'needs_response', '{"scenario": "S1"}', '2026-09-01T00:00:00Z', '2026-09-01T00:00:00Z')
    """)
    cur.execute("""
        INSERT INTO orders (id, customer_id, amount_cents, currency, status)
        VALUES ('ORD-TEST-1', 'CUST-TEST-1', 4800, 'usd', 'delivered')
    """)
    conn.commit()
    conn.close()

    # Monkeypatch paths in modules
    monkeypatch.setattr("agent.tools.case_tools.LOCAL_DB_PATH", db_file)
    monkeypatch.setattr("agent.executor.LOCAL_DB_PATH", db_file)
    return db_file


def test_build_executor_agent():
    mock_model = MagicMock()
    agent = build_executor_agent(model=mock_model)
    assert agent is not None
    assert agent.name == "executor"
    assert "submit_evidence" in agent.tool_names
    assert "concede_dispute" in agent.tool_names
    assert "refund_inquiry" in agent.tool_names
    assert "upload_evidence_file" in agent.tool_names
    assert "record_case" in agent.tool_names
    assert "send_customer_email" in agent.tool_names


def test_record_case_and_audit_log(mock_db):
    res = record_case(
        dispute_id="dp_test_1",
        action="test_action",
        actor="tester",
        status="under_review",
        details={"key": "value"},
    )
    assert res["status"] == "recorded"
    assert res["action"] == "test_action"

    conn = sqlite3.connect(mock_db)
    cur = conn.cursor()
    audit_rows = cur.execute("SELECT * FROM audit_log WHERE dispute_id = 'dp_test_1'").fetchall()
    assert len(audit_rows) == 1

    disp = cur.execute("SELECT status FROM disputes WHERE id = 'dp_test_1'").fetchone()
    assert disp[0] == "under_review"
    conn.close()


def test_send_customer_email(mock_db):
    res = send_customer_email(
        customer_id="CUST-TEST-1",
        subject="Dispute Notice",
        body="We received your dispute notice.",
        order_id="ORD-TEST-1",
    )
    assert res["status"] == "sent"

    conn = sqlite3.connect(mock_db)
    cur = conn.cursor()
    msgs = cur.execute("SELECT * FROM customer_messages WHERE customer_id = 'CUST-TEST-1'").fetchall()
    assert len(msgs) == 1
    conn.close()


@patch("agent.executor.verify_live_key_guard")
@patch("agent.executor.upload_evidence_file")
@patch("agent.executor.submit_evidence")
@patch("agent.executor.get_dispute")
def test_execute_strategy_fight(mock_get_disp, mock_submit, mock_upload, mock_guard, mock_db):
    mock_guard.return_value = "sk_test_mock"
    mock_upload.return_value = {"id": "file_test_999", "filename": "narrative.pdf"}
    mock_submit.return_value = {"id": "dp_test_1", "status": "under_review"}
    mock_get_disp.return_value = {"id": "dp_test_1", "status": "won"}

    strat = DisputeStrategy(
        action="fight",
        win_probability=0.85,
        expected_value_cents=4000,
        customer_value="new",
        evidence_strength="strong",
        rationale="Clear proof of delivery with carrier signature.",
        owner_summary="Fighting $48 dispute with signed delivery proof.",
    )
    packet = EvidencePacket(
        customer_name="Michael Okafor",
        shipping_tracking_number="1Z9999999999999991",
        shipping_carrier="UPS",
        narrative="Package was delivered and signed by Okafor.",
    )

    result = execute_strategy(
        dispute_id="dp_test_1",
        strategy=strat,
        evidence_packet=packet,
        is_demo_mode=True,
    )

    assert result["action"] == "fight"
    assert result["uploaded_file_id"] == "file_test_999"
    assert result["audit_rows_count"] >= 5

    # Check evidence payload passed to submit_evidence
    mock_submit.assert_called_once()
    call_args = mock_submit.call_args
    evidence_sent = call_args.kwargs.get("evidence") or call_args[1].get("evidence")
    assert evidence_sent["uncategorized_file"] == "file_test_999"
    # DEMO_MODE + win_prob >= 0.70 sets winning_evidence
    assert evidence_sent["uncategorized_text"] == "winning_evidence"
    assert evidence_sent["shipping_tracking_number"] == "1Z9999999999999991"
    assert evidence_sent["customer_name"] == "Michael Okafor"


@patch("agent.executor.verify_live_key_guard")
@patch("agent.executor.concede_dispute")
def test_execute_strategy_concede(mock_concede, mock_guard, mock_db):
    mock_guard.return_value = "sk_test_mock"
    mock_concede.return_value = {"id": "dp_test_1", "status": "lost"}

    strat = DisputeStrategy(
        action="concede",
        win_probability=0.20,
        expected_value_cents=0,
        customer_value="vip",
        evidence_strength="weak",
        rationale="Conceding to preserve relationship with VIP customer.",
        owner_summary="Conceding dispute to protect repeat VIP customer.",
    )

    result = execute_strategy(
        dispute_id="dp_test_1",
        strategy=strat,
        evidence_packet=None,
    )

    assert result["action"] == "concede"
    assert result["final_status"] == "lost"
    assert result["audit_rows_count"] >= 3
    mock_concede.assert_called_once()
