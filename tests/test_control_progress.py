"""Interrupted paid controls retain completed evidence and usage."""
import json
import runpy
from unittest.mock import MagicMock

import pytest


def test_control_interruption_preserves_completed_results(monkeypatch, tmp_path):
    import evals.run as runner
    import agent.tools.evidence_tools as evidence

    monkeypatch.setattr(evidence, 'get_order_evidence', lambda _: {'billing_address': {}})
    monkeypatch.setattr(evidence, 'get_shipping_evidence', lambda _: {'shipping_address': {}})
    monkeypatch.setattr(evidence, 'get_customer_comms', lambda *args: {'messages': []})
    monkeypatch.setattr(evidence, 'get_merchant_history_and_policy', lambda _: {
        'policy': {'return_policy': 'Return within 30 days.'}})
    monkeypatch.setattr(runner, 'get_llm_judge_client', lambda: object())
    first = {'overall_pass': True, 'reason_code_pass': True, 'must_cite_pass': True,
             'no_hallucination_pass': True, 'word_count_pass': True,
             'explanation': 'Grounded control.', 'usage': {'inputTokens': 123, 'outputTokens': 45}}
    judge = MagicMock(side_effect=[first, RuntimeError('provider interrupted')])
    monkeypatch.setattr(runner, 'judge_narrative', judge)
    report = tmp_path / 'controls.json'
    monkeypatch.setenv('CONTROL_REPORT_PATH', str(report))

    with pytest.raises(RuntimeError, match='provider interrupted'):
        runpy.run_path(str(runner.REPO_ROOT / 'evals/check_output_grounding.py'))

    saved = json.loads(report.read_text())
    assert saved['completed'] is False
    assert len(saved['results']) == 1
    assert saved['results'][0]['name'] == 'grounded_control'
    assert saved['results'][0]['result']['usage'] == first['usage']
    assert saved['results'][0]['facts']['source_tool_records']
    assert saved['code_revision'] and set(saved['source_manifest']) == {
        'evals/run.py', 'evals/check_output_grounding.py'}
