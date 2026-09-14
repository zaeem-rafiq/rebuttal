"""Rejected packets remain reviewable without invoking the model judge."""
import json
import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock

import evals.run as runner
from agent.models import DisputeStrategy, EvidencePacket


@pytest.mark.parametrize("malformed", [False, True])
def test_pipeline_rejection_retains_outputs_and_source_records(monkeypatch, malformed):
    case_path = runner.CASES_DIR / "case_01.json"
    case = json.loads(case_path.read_text())
    strategy = DisputeStrategy(
        action=case["expected_action"], win_probability=.85, expected_value_cents=100,
        customer_value="new", evidence_strength="strong",
        rationale="Recommend fighting based on the supplied delivery record.",
        owner_summary="Recommend fighting this dispute.",
    )
    packet = EvidencePacket(
        narrative="Dispute Reason: fraudulent. Recommendation: Submit evidence.",
        uncategorized_text="Retain this sibling claim for review too.",
        files=["never-produced-evidence.pdf"],
    )
    packet_data = packet.model_dump()
    if malformed:
        packet = {"narrative": packet_data["narrative"],
                  "customer_communication": "Raw transcript text that is not a file ID."}
        packet_data = packet
    graph = MagicMock()
    graph.state = SimpleNamespace(
        results={
            "strategy": SimpleNamespace(get_agent_results=lambda: [SimpleNamespace(structured_output=strategy)]),
            "drafter": SimpleNamespace(get_agent_results=lambda: [SimpleNamespace(structured_output=packet)]),
        },
        accumulated_usage={"inputTokens": 120, "outputTokens": 30, "totalTokens": 150},
    )
    expected_records = []
    graph.nodes = {}
    for name in ("intake", "orders", "shipping", "comms", "history"):
        arguments = {"lookup_id": f"{name}-lookup"}
        payload = {"source_marker": f"{name}-raw-record"}
        source = SimpleNamespace(messages=[
            {"role": "assistant", "content": [{"toolUse": {
                "toolUseId": name, "name": f"get_{name}", "input": arguments,
            }}]},
            {"role": "user", "content": [{"toolResult": {
                "toolUseId": name, "status": "success", "content": [{"json": payload}],
            }}]},
        ])
        graph.nodes[name] = SimpleNamespace(executor=source)
        expected_records.append({
            "collector": name, "tool": f"get_{name}", "tool_use_id": name,
            "arguments": arguments, "status": "success", "content": [payload],
        })
    # Keep real structured extraction, attachment validation, exception handling,
    # source extraction, and scoring; replace only the model-producing graph.
    monkeypatch.setattr(runner.agent.graph, "build_evidence_graph", lambda **kwargs: (graph, {}))
    judge = MagicMock()

    result = runner.run_single_eval_case(case_path, judge)

    graph.assert_called_once()
    judge.converse.assert_not_called()
    if malformed:
        assert result["pipeline_error"].startswith("InvalidEvidencePacket:")
        assert "customer_communication must be an uploaded Stripe file ID" in result["pipeline_error"]
    else:
        assert result["pipeline_error"] == (
            "InvalidEvidencePacket: Evidence packet contains unproduced attachment references: files"
        )
    assert result["supporting_output"] == {
        "strategy": strategy.model_dump(), "evidence_packet": packet_data,
    }
    assert result["narrative"] == packet_data["narrative"]
    assert result["rationale"] == strategy.rationale
    assert result["case_facts"] == {
        "source_tool_records": expected_records, "produced_artifacts": [],
    }
    assert result["fixture_context"]["dispute"]["id"] == case["dispute_id"]
    assert result["generation_usage"] == graph.state.accumulated_usage
    assert result["action_match"] and result["gate_match"] and result["ev_sign"]
    assert result["judge_pass"] is False
    assert result["overall_pass"] is False
