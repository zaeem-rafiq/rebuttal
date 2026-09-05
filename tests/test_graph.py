"""tests/test_graph.py

Unit tests for Strands Evidence Graph topology, node configuration, and scenario resolution.
Enforces requirements for HAC-4 / R-02.
"""

import pytest
from unittest.mock import MagicMock
from agent.graph import build_evidence_graph, _extract_structured_output
from agent.models import DisputeStrategy, EvidencePacket
from scripts.run_local import resolve_scenario_context


def test_resolve_scenario_context_s1():
    """Verify S1 scenario resolves to ORD-1001 with expected dispute parameters."""
    ctx = resolve_scenario_context("S1")
    assert ctx["scenario"] == "S1"
    assert ctx["order_id"] == "ORD-1001"
    assert ctx["reason"] == "product_not_received"
    assert ctx["customer_id"] == "CUST-001"
    assert ctx["amount_cents"] == 4800


def test_resolve_scenario_context_s2():
    """Verify S2 scenario resolves to ORD-1002 with expected dispute parameters."""
    ctx = resolve_scenario_context("S2")
    assert ctx["scenario"] == "S2"
    assert ctx["order_id"] == "ORD-1002"
    assert ctx["reason"] == "fraudulent"
    assert ctx["customer_id"] == "CUST-002"
    assert ctx["amount_cents"] == 34000


def test_resolve_scenario_context_s3():
    """Verify S3 scenario resolves to ORD-1003 with expected dispute parameters."""
    ctx = resolve_scenario_context("S3")
    assert ctx["scenario"] == "S3"
    assert ctx["order_id"] == "ORD-1003"
    assert ctx["customer_id"] == "CUST-003"


def test_graph_topology_nodes_and_edges():
    """Verify graph builder constructs all nodes and required fan-out/fan-in edges."""
    mock_model = MagicMock()
    graph, agents = build_evidence_graph(model=mock_model)

    expected_nodes = {"intake", "orders", "shipping", "comms", "history", "strategy", "drafter"}
    assert set(graph.nodes.keys()) == expected_nodes
    assert set(agents.keys()) == expected_nodes

    # Check node models & structured output models
    assert agents["strategy"]._default_structured_output_model == DisputeStrategy
    assert agents["drafter"]._default_structured_output_model == EvidencePacket


    # Check edges
    edge_pairs = {(e.from_node.node_id, e.to_node.node_id) for e in graph.edges}
    
    # Fan-out from intake
    assert ("intake", "orders") in edge_pairs
    assert ("intake", "shipping") in edge_pairs
    assert ("intake", "comms") in edge_pairs
    assert ("intake", "history") in edge_pairs

    # Fan-in to strategy
    assert ("orders", "strategy") in edge_pairs
    assert ("shipping", "strategy") in edge_pairs
    assert ("comms", "strategy") in edge_pairs
    assert ("history", "strategy") in edge_pairs

    # Final edge to drafter
    assert ("strategy", "drafter") in edge_pairs


def test_extract_structured_output_direct():
    """Verify _extract_structured_output extracts from AgentResult.structured_output."""
    strategy_mock = DisputeStrategy(
        action="fight",
        win_probability=0.85,
        expected_value_cents=3855,
        customer_value="new",
        evidence_strength="strong",
        rationale="Delivered and signed.",
        owner_summary="Fighting $48 claim.",
    )

    mock_agent_res = MagicMock()
    mock_agent_res.structured_output = strategy_mock
    mock_node_res = MagicMock()
    mock_node_res.get_agent_results.return_value = [mock_agent_res]

    extracted = _extract_structured_output(mock_node_res, DisputeStrategy)
    assert extracted == strategy_mock


def test_extract_structured_output_json_fallback():
    """Verify _extract_structured_output extracts from JSON string representation."""
    json_str = '''```json
    {
        "action": "concede",
        "win_probability": 0.20,
        "expected_value_cents": -1500,
        "customer_value": "repeat",
        "evidence_strength": "weak",
        "rationale": "High value repeat customer; concession preserves relationship.",
        "owner_summary": "Conceding $350 claim for VIP."
    }
    ```'''

    mock_agent_res = MagicMock()
    mock_agent_res.structured_output = None
    mock_agent_res.__str__.return_value = json_str
    mock_node_res = MagicMock()
    mock_node_res.get_agent_results.return_value = [mock_agent_res]

    extracted = _extract_structured_output(mock_node_res, DisputeStrategy)
    assert extracted is not None
    assert extracted.action == "concede"
    assert extracted.customer_value == "repeat"
