"""Offline regression checks for evidence scoring and production gate selection."""
import json
from unittest.mock import MagicMock

import pytest
from evals.run import judge_narrative, observe_gate


@pytest.mark.parametrize('response', [None, 'not json', '[]', '{}', json.dumps({
    'reason_code_pass': 'false', 'must_cite_pass': True, 'no_hallucination_pass': True,
}), json.dumps({
    'reason_code_pass': True, 'must_cite_pass': False, 'no_hallucination_pass': True,
}), json.dumps({
    'reason_code_pass': True, 'must_cite_pass': True, 'no_hallucination_pass': False,
})])
def test_judge_cannot_turn_failure_into_pass(response):
    client = MagicMock()
    if response is None:
        client.converse.side_effect = RuntimeError('unavailable')
    else:
        client.converse.return_value = {'output': {'message': {'content': [{'text': response}]}}}
    result = judge_narrative(client, 'product_not_received tracking A123', 'product_not_received', ['A123'], '{}')
    assert result['overall_pass'] is False


def test_judge_accepts_grounded_verdict_and_rejects_empty_or_long_text():
    client = MagicMock()
    client.converse.return_value = {'output': {'message': {'content': [{'text': json.dumps({
        'reason_code_pass': True, 'must_cite_pass': True, 'no_hallucination_pass': True,
    })}]}}}
    for narrative, expected in [('Delivery recorded.', True), ('', False), ('word ' * 251, False)]:
        assert judge_narrative(client, narrative, 'product_not_received', [], '{}')['overall_pass'] is expected


@pytest.mark.parametrize('amount,probability,action,expected', [
    (19999, .9, 'fight', False), (20000, .9, 'fight', True),
    (4800, .35, 'fight', True), (4800, .65, 'fight', True),
    (4800, .349, 'fight', False), (4800, .651, 'fight', False),
    (4800, .9, 'concede', True), (4800, .9, 'refund_inquiry', True),
])
def test_eval_observes_production_gate(amount, probability, action, expected):
    assert observe_gate(amount, {'action': action, 'win_probability': probability}) is expected
