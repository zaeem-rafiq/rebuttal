"""Exercise runtime dispatch after a model result without providers or DB writes."""

import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


@pytest.mark.parametrize("scenario,gate_status,stop_reason,should_dispatch", [
    ("S1", "required", "interrupt", False),
    ("S1", "required", "end_turn", False),
    ("S1", None, "end_turn", False),
    ("S1", "skipped", "interrupt", False),
    ("S1", "skipped", "end_turn", True),
    ("S2", "skipped", "end_turn", True),
])
def test_runtime_dispatch_respects_gate_even_for_s1(monkeypatch, tmp_path, scenario, gate_status, stop_reason, should_dispatch):
    import agent.app as runtime
    from agent import executor, graph, ingress
    from agent.tools import case_tools, memory_tools, stripe_tools

    monkeypatch.setattr(runtime, "load_secrets", lambda: None)
    monkeypatch.setattr(runtime, "ensure_db", lambda: None)
    monkeypatch.setattr(runtime, "LOCAL_DB_PATH", tmp_path / "unused.db")
    monkeypatch.setattr(runtime, "get_runtime_bedrock_model", lambda: object())
    monkeypatch.setattr(memory_tools, "patch_history_tool_with_memory", lambda: None)
    monkeypatch.setattr(case_tools, "_get_supabase_client", lambda: object())
    monkeypatch.setattr(stripe_tools, "get_dispute", lambda case_id: {"id": case_id, "status": "under_review"})
    monkeypatch.setattr(ingress, "ingest_stripe_dispute", lambda *args, **kwargs: {
        "dispute_id": "du_runtime_gate", "amount_cents": 34000, "scenario": scenario,
    })
    strategy = SimpleNamespace(action="fight", rationale="Test proposal")
    pipeline = MagicMock(return_value=(strategy, object(), object()))
    monkeypatch.setattr(graph, "run_evidence_pipeline", pipeline)
    agent = MagicMock(return_value=SimpleNamespace(stop_reason=stop_reason))
    agent.state = {"gate_status": gate_status}
    builder = MagicMock(return_value=agent)
    monkeypatch.setattr(executor, "build_executor_agent", builder)
    dispatch = MagicMock()
    monkeypatch.setattr(executor, "execute_strategy", dispatch)

    asyncio.run(runtime.process_case_async("du_runtime_gate", scenario=scenario))

    pipeline.assert_called_once()
    builder.assert_called_once()
    agent.assert_called_once()
    if should_dispatch:
        dispatch.assert_called_once()
        assert dispatch.call_args.kwargs["dispute_id"] == "du_runtime_gate"
    else:
        dispatch.assert_not_called()
