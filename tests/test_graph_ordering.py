"""Exercise the installed Strands scheduler without model or service calls."""
import asyncio
from unittest.mock import MagicMock

import pytest
from strands.agent.agent_result import AgentResult
from strands.agent.base import AgentBase
from strands.telemetry.metrics import EventLoopMetrics

import agent.graph as graph_module


def run_graph(monkeypatch, *, remove_conditions=False):
    completed = set()
    calls = []

    def make_agent(**kwargs):
        name = kwargs['name']
        executor = MagicMock(spec=AgentBase)

        async def stream(prompt, **_):
            text = '\n'.join(block.get('text', '') for block in prompt)
            calls.append((name, completed.copy(), text))
            # Yield the event loop so concurrently scheduled nodes really overlap.
            await asyncio.sleep(0)
            completed.add(name)
            yield {'result': AgentResult(
                stop_reason='end_turn',
                message={'role': 'assistant', 'content': [{'text': f'{name}-result'}]},
                metrics=EventLoopMetrics(),
                state={},
            )}

        executor.stream_async = stream
        return executor

    monkeypatch.setenv('USE_GATEWAY_MCP', 'false')
    monkeypatch.setattr(graph_module, 'Agent', make_agent)
    graph, _ = graph_module.build_evidence_graph(model=MagicMock())
    if remove_conditions:
        for edge in graph.edges:
            edge.condition = None
    graph('Investigate this dispute using all collected records.')
    return calls


def assert_complete_flow(calls):
    collectors = {'orders', 'shipping', 'comms', 'history'}
    for node, predecessors in [('strategy', collectors), ('drafter', collectors | {'strategy'})]:
        invocations = [call for call in calls if call[0] == node]
        assert len(invocations) == 1, f'{node} must execute exactly once'
        _, completed, prompt = invocations[0]
        assert predecessors <= completed, f'{node} started before every predecessor completed'
        for predecessor in predecessors:
            assert f'From {predecessor}:' in prompt
            assert f'{predecessor}-result' in prompt


def test_scheduler_waits_for_complete_inputs_and_drafts_once(monkeypatch):
    assert_complete_flow(run_graph(monkeypatch))


def test_unguarded_edges_reproduce_premature_repeated_drafting(monkeypatch):
    # Reproduce the old topology on an isolated graph, preserving production source.
    calls = run_graph(monkeypatch, remove_conditions=True)
    drafts = [call for call in calls if call[0] == 'drafter']
    assert len(drafts) == 2
    assert 'strategy' not in drafts[0][1]
    assert 'From strategy:' not in drafts[0][2]
    with pytest.raises(AssertionError, match='drafter must execute exactly once'):
        assert_complete_flow(calls)
