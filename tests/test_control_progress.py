"""Interrupted paid controls retain completed evidence and usage."""
import json
import runpy
from unittest.mock import MagicMock

import pytest


@pytest.mark.parametrize('provider_valid', [True, False])
@pytest.mark.parametrize('selected', ['', 'grounded_control,retention_outcome_alone', 'grounded_control,attributed_prior_event'])
def test_control_interruption_preserves_completed_results(monkeypatch, tmp_path, selected, provider_valid):
    import evals.run as runner
    import agent.tools.evidence_tools as evidence

    monkeypatch.setattr(evidence, 'get_order_evidence', lambda _: {'billing_address': {}})
    monkeypatch.setattr(evidence, 'get_shipping_evidence', lambda _: {'shipping_address': {}})
    monkeypatch.setattr(evidence, 'get_customer_comms', lambda *args: {'messages': []})
    monkeypatch.setattr(evidence, 'get_merchant_history_and_policy', lambda _: {
        'policy': {}})
    monkeypatch.setattr(runner, 'get_llm_judge_client', lambda: object())
    first = {'judge_valid': provider_valid, 'overall_pass': True, 'reason_code_pass': True, 'must_cite_pass': True,
             'no_hallucination_pass': True, 'word_count_pass': True,
             'explanation': 'Grounded control.', 'usage': {'inputTokens': 123, 'outputTokens': 45}}
    judge = MagicMock(side_effect=[first, RuntimeError('provider interrupted')])
    monkeypatch.setattr(runner, 'judge_narrative', judge)
    report = tmp_path / 'controls.json'
    monkeypatch.setenv('CONTROL_REPORT_PATH', str(report))
    monkeypatch.setenv('CONTROL_CASES', selected)

    expected_error = 'provider interrupted' if provider_valid else 'control validity cannot be assessed'
    with pytest.raises(RuntimeError, match=expected_error):
        runpy.run_path(str(runner.REPO_ROOT / 'evals/check_output_grounding.py'))

    saved = json.loads(report.read_text())
    assert saved['completed'] is False
    if selected:
        assert saved['selected_controls'] == selected.split(',')
    assert len(saved['results']) == 1
    assert saved['results'][0]['name'] == 'grounded_control'
    assert saved['results'][0]['result']['usage'] == first['usage']
    assert saved['results'][0]['facts']['source_tool_records']
    assert saved['code_revision'] and set(saved['source_manifest']) == {
        'evals/run.py', 'evals/check_output_grounding.py'}

    for call in judge.call_args_list:
        records = json.loads(call.args[4])['source_tool_records']
        comms = next(record['content'][0] for record in records if record['collector'] == 'communications')
        assert comms['message_count'] == len(comms['messages'])
        assert comms['has_cancellation_request'] == any(
            'cancel' in (message.get('subject', '') + message.get('body', '')).lower()
            for message in comms['messages'])
