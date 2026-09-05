"""tests/test_memory.py

Unit tests for agent/tools/memory_tools.py:
- retrieve_past_outcomes querying Bedrock AgentCore semantic memory.
- store_dispute_outcome recording short-term events and indexed records.
- get_past_dispute_outcomes strands tool.
- patch_history_tool_with_memory integration with get_merchant_history_and_policy.
"""

from unittest.mock import MagicMock, patch
import pytest

from agent.tools.memory_tools import (
    retrieve_past_outcomes,
    store_dispute_outcome,
    get_past_dispute_outcomes,
    patch_history_tool_with_memory,
)


def test_store_dispute_outcome_mocked():
    mock_client = MagicMock()
    mock_client.create_event.return_value = {"eventId": "ev_test_123"}
    mock_dp = MagicMock()
    mock_dp.batch_create_memory_records.return_value = {
        "successfulRecords": [{"memoryRecordId": "rec_test_123"}]
    }
    mock_client.gmdp_client = mock_dp

    with patch("agent.tools.memory_tools.get_memory_client", return_value=mock_client):
        res = store_dispute_outcome(
            dispute_id="dp_test_1",
            reason="product_not_received",
            action="fight",
            outcome="won",
            amount=4800,
            merchant_id="default",
        )
        assert res["status"] == "stored"
        assert res["event_id"] == "ev_test_123"
        assert res["record_id"] == "rec_test_123"
        assert res["action"] == "fight"
        assert res["outcome"] == "won"


def test_retrieve_past_outcomes_mocked():
    mock_client = MagicMock()
    mock_client.retrieve_memories.return_value = [
        {"memoryRecordId": "mem_1", "content": {"text": "dispute won for product_not_received"}}
    ]

    with patch("agent.tools.memory_tools.get_memory_client", return_value=mock_client):
        recs = retrieve_past_outcomes("product_not_received", merchant_id="default")
        assert len(recs) == 1
        assert "won" in recs[0]["content"]["text"]


def test_get_past_dispute_outcomes_tool():
    with patch(
        "agent.tools.memory_tools.retrieve_past_outcomes",
        return_value=[{"memoryRecordId": "mem_1", "content": {"text": "outcome won"}}],
    ):
        tool_res = get_past_dispute_outcomes("product_not_received")
        assert len(tool_res) == 1
        assert tool_res[0]["memoryRecordId"] == "mem_1"


def test_patch_history_tool():
    with patch(
        "agent.tools.memory_tools.retrieve_past_outcomes",
        return_value=[{"memoryRecordId": "mem_1", "content": {"text": "precedent record"}}],
    ):
        patch_history_tool_with_memory()
        from agent.tools.evidence_tools import get_merchant_history_and_policy
        # Mock database connection inside get_merchant_history_and_policy
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.execute.return_value.fetchone.return_value = None
        mock_cur.execute.return_value.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cur
        with patch("agent.tools.evidence_tools._get_db_connection", return_value=mock_conn):
            res = get_merchant_history_and_policy("CUST-001")
            assert "memory_past_outcomes" in res
            assert res["memory_outcomes_count"] == 1
