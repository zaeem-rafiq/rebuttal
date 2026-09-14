"""Reject artifacts the evidence collectors cannot produce, before execution."""
from unittest.mock import MagicMock

import pytest

import agent.graph as graph_module
from agent.models import EvidencePacket


@pytest.mark.parametrize("fallback", [False, True])
@pytest.mark.parametrize("field", ["files", "shipping_documentation", "service_documentation", "uncategorized_file"])
def test_pipeline_rejects_unproduced_attachments(monkeypatch, tmp_path, fallback, field):
    # Even an existing local file is not evidence authorized by a collector.
    unrelated = tmp_path / "not-case-evidence.pdf"
    unrelated.write_text("unrelated file")
    value = [str(unrelated)] if field == "files" else str(unrelated)
    packet = EvidencePacket(narrative="Recommendation: Concede dispute.", **{field: value})
    graph = MagicMock()
    drafter = MagicMock()
    drafter.structured_output.return_value = packet
    monkeypatch.setattr(graph_module, "build_evidence_graph", lambda **kwargs: (graph, {"drafter": drafter}))
    outputs = iter([None, None if fallback else packet])
    monkeypatch.setattr(graph_module, "_extract_structured_output", lambda *args: next(outputs))

    with pytest.raises(ValueError, match="unproduced attachment references: " + field):
        graph_module.run_evidence_pipeline("Investigate this case")


@pytest.mark.parametrize("fallback", [False, True])
def test_pipeline_returns_text_packet_with_no_artifacts(monkeypatch, fallback):
    packet = EvidencePacket(narrative="Recommendation: Concede dispute.", files=[])
    graph = MagicMock()
    drafter = MagicMock()
    drafter.structured_output.return_value = packet
    monkeypatch.setattr(graph_module, "build_evidence_graph", lambda **kwargs: (graph, {"drafter": drafter}))
    outputs = iter([None, None if fallback else packet])
    monkeypatch.setattr(graph_module, "_extract_structured_output", lambda *args: next(outputs))

    _, result, _ = graph_module.run_evidence_pipeline("Investigate this case")
    assert result is packet
    assert result.files == []
