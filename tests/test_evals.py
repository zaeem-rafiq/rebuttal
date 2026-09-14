"""Offline regression checks for evidence scoring and production gate selection."""
import json
from unittest.mock import MagicMock

import pytest
from evals.run import judge_narrative, observe_gate, normalize_currency_text


def judge_response(payload, usage=None):
    return {'usage': usage or {}, 'output': {'message': {'content': [{'text': json.dumps(payload)}]}}}


@pytest.mark.parametrize('response', [None, 'not json', '[]', '{}', json.dumps({
    'reason_code_pass': 'false', 'must_cite_pass': True, 'no_hallucination_pass': True, 'support_assertions': [], 'event_absence_pass': True, 'event_order_pass': True, 'policy_disclosure_pass': True,
}), json.dumps({
    'reason_code_pass': True, 'must_cite_pass': False, 'no_hallucination_pass': True, 'support_assertions': [], 'event_absence_pass': True, 'event_order_pass': True, 'policy_disclosure_pass': True,
}), json.dumps({
    'reason_code_pass': True, 'must_cite_pass': True, 'no_hallucination_pass': False, 'support_assertions': [], 'event_absence_pass': True, 'event_order_pass': True, 'policy_disclosure_pass': True,
})])
def test_judge_cannot_turn_failure_into_pass(response):
    client = MagicMock()
    if response is None:
        client.converse.side_effect = RuntimeError('unavailable')
    else:
        client.converse.return_value = {'output': {'message': {'content': [{'text': response}]}}}
    result = judge_narrative(client, 'product_not_received tracking A123', 'product_not_received', ['A123'], '{}')
    assert result['overall_pass'] is False
    if response is None:
        assert result['judge_valid'] is False


def test_judge_accepts_grounded_verdict_and_rejects_empty_or_long_text(monkeypatch):
    monkeypatch.setenv('BEDROCK_MODEL_ID', 'generator-model')
    monkeypatch.setenv('BEDROCK_JUDGE_MODEL_ID', 'judge-model')
    client = MagicMock()
    client.converse.return_value = {'usage': {'inputTokens': 100, 'outputTokens': 25}, 'output': {'message': {'content': [{'text': json.dumps({
        'reason_code_pass': True, 'must_cite_pass': True, 'no_hallucination_pass': True, 'support_assertions': [], 'event_absence_pass': True, 'event_order_pass': True, 'policy_disclosure_pass': True,
    })}]}}}
    for narrative, expected in [('Delivery recorded.', True), ('', False), ('word ' * 251, False)]:
        result = judge_narrative(client, narrative, 'product_not_received', [], '{}')
        assert result['overall_pass'] is expected
        assert result['model_id'] == client.converse.call_args.kwargs['modelId'] == 'judge-model'
        assert result['usage'] == {'inputTokens': 400, 'outputTokens': 100}


@pytest.mark.parametrize('amount,probability,action,expected', [
    (19999, .9, 'fight', False), (20000, .9, 'fight', True),
    (4800, .35, 'fight', True), (4800, .65, 'fight', True),
    (4800, .349, 'fight', False), (4800, .651, 'fight', False),
    (4800, .9, 'concede', True), (4800, .9, 'refund_inquiry', True),
])
def test_eval_observes_production_gate(amount, probability, action, expected):
    assert observe_gate(amount, {'action': action, 'win_probability': probability}) is expected


def test_currency_and_timestamp_normalization():
    """Verify directly checkable currency and UTC timestamp derivations."""
    from evals.run import format_currency_cents, format_utc_timestamp

    # Currency equivalence
    c450 = format_currency_cents(45000)
    assert c450["cents"] == 45000
    assert c450["dollars"] == "$450.00"
    assert c450["dollars_short"] == "$450"

    c3400 = format_currency_cents(340000)
    assert c3400["dollars_formatted"] == "$3,400.00"
    assert c3400["dollars_short"] == "$3400"
    assert normalize_currency_text({'text': ['$340', '$340.00', '$340.01', '$1,120', '$1.005']}) == {
        'text': ['$340.00', '$340.00', '$340.01', '$1,120.00', '$1.005']}

    c240 = format_currency_cents(24000)
    assert c240["dollars"] == "$240.00"
    assert c240["dollars_short"] == "$240"

    # Timestamp normalization for ISO-8601 UTC
    ts_z = format_utc_timestamp("2026-08-18T16:20:00Z")
    assert ts_z["iso"] == "2026-08-18T16:20:00Z"
    assert ts_z["utc_formatted"] == "August 18, 2026 at 4:20 PM UTC"
    assert ts_z["time_utc"] == "4:20 PM UTC"
    assert ts_z["date_long"] == "August 18, 2026"
    assert ts_z["date_short"] == "Aug 18, 2026"

    # Empty inputs
    assert format_currency_cents(None) == {}
    assert format_utc_timestamp(None) == {}


def test_seeded_database_and_policy_consistency(tmp_path):
    """Verify SQLite database seeded facts and policy defaults align with judge expectations."""
    import sqlite3
    from evals.run import setup_case_database

    sample_case = {
        "id": "case_test",
        "dispute_id": "dp_test",
        "order_id": "ORD-TEST-001",
        "customer_id": "CUST-TEST-001",
        "amount_cents": 22000,
        "currency": "usd",
        "reason": "fraudulent",
        "status": "needs_response",
        "customer": {
            "id": "CUST-TEST-001",
            "name": "Test User",
            "customer_value": "repeat",
            "order_count": 3,
            "lifetime_value_cents": 45000,
        },
        "order": {
            "id": "ORD-TEST-001",
            "amount_cents": 22000,
            "currency": "usd",
            "status": "fulfilled",
            "created_at": "2026-08-10T00:00:00Z",
        },
        "shipment": {
            "id": "shp_test",
            "carrier": "FedEx",
            "tracking_number": "794900",
            "status": "delivered",
            "shipped_at": "2026-08-14T10:00:00Z",
            "delivered_at": "2026-08-17T15:00:00Z",
        },
        "comms": [],
        "charge": {"amount": 22000},
    }

    db_path = tmp_path / "test_case.db"
    setup_case_database(sample_case, db_path)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Verify merchant policy table has return_policy
    policy = cur.execute("SELECT * FROM merchant_policy LIMIT 1").fetchone()
    assert policy is not None
    # id, approval_amount_cents, min_win_probability_to_fight, always_concede_under_cents, vip_concede_max_cents, silence_action, return_policy
    assert policy[4] == 50000  # vip_concede_max_cents
    assert "return policy" in policy[6].lower()

    # Verify orders table preserves created_at
    order = cur.execute("SELECT * FROM orders WHERE id = 'ORD-TEST-001'").fetchone()
    assert order is not None
    assert order[7] == "2026-08-10T00:00:00Z"

    # Verify customer table preserves lifetime_value_cents
    customer = cur.execute("SELECT * FROM customers WHERE id = 'CUST-TEST-001'").fetchone()
    assert customer is not None
    assert customer[6] == 45000

    conn.close()


def test_judge_prompt_contains_equivalence_and_grounding_rules():
    """Verify prompt passed to Bedrock judge enforces strict factual grounding and equivalence rules."""
    client = MagicMock()
    client.converse.return_value = {'output': {'message': {'content': [{'text': json.dumps({
        'reason_code_pass': True, 'must_cite_pass': True, 'no_hallucination_pass': True, 'support_assertions': [], 'event_absence_pass': True, 'event_order_pass': True, 'policy_disclosure_pass': True,
    })}]}}}

    judge_narrative(
        judge_client=client,
        narrative="Test narrative",
        reason="fraudulent",
        must_cite=["AVS", "442004"],
        case_summary='{"test": "facts"}',
    )

    call_args = client.converse.call_args_list[1].kwargs
    prompt_text = call_args["system"][0]["text"]
    assert json.loads(call_args['messages'][0]['content'][0]['text'])['source_records'] == {'test': 'facts'}

    assert "100 cents equals $1" in prompt_text
    assert "UTC/ISO date reformattings are equivalent" in prompt_text
    assert "A quoted report establishes what was reported, not its independent truth" in prompt_text
    assert "No X documented/in merchant records" in prompt_text
    assert "Proposed actions must not be presented as completed" in prompt_text
    assert "Audit every truth-assessable assertion in past, present, future, or conditional tense" in prompt_text


def test_keyword_presence_cannot_override_negative_judge_verdict():
    """Verify keyword match in narrative cannot force must_cite_pass when judge says False."""
    client = MagicMock()
    # Judge finds must_cite semantically invalid despite exact keywords appearing
    client.converse.return_value = {'output': {'message': {'content': [{'text': json.dumps({
        'reason_code_pass': True,
        'must_cite_pass': False,
        'no_hallucination_pass': True, 'support_assertions': [], 'event_absence_pass': True, 'event_order_pass': True, 'policy_disclosure_pass': True,
        'explanation': 'Required evidence items were mentioned out of context.',
    })}]}}}

    narrative = "The reason is product_not_received. Carrier tracking 1Z99901 was delivered and signed by M. Taylor."
    result = judge_narrative(client, narrative, "product_not_received", ["1Z99901", "M. Taylor", "delivered"], "{}")

    assert result["overall_pass"] is False
    assert result["must_cite_pass"] is False
    assert result["missing_items"] == []  # Keywords were present, but judge verdict is authoritative


def test_judge_fails_on_unsupported_facts():
    """Verify fail verdicts for unsupported fees, completed actions, or ungrounded accusations."""
    client = MagicMock()

    # Case A: Unsupported $15 statutory fee
    client.converse.return_value = {'output': {'message': {'content': [{'text': json.dumps({
        'reason_code_pass': True,
        'must_cite_pass': True,
        'no_hallucination_pass': False, 'support_assertions': [], 'event_absence_pass': True, 'event_order_pass': True, 'policy_disclosure_pass': True,
        'explanation': 'Unsupported $15 statutory loss fee not in case facts.',
    })}]}}}
    res_fee = judge_narrative(client, "Conceding dispute to avoid $15 fee", "product_not_received", [], "{}")
    assert res_fee["overall_pass"] is False
    assert res_fee["no_hallucination_pass"] is False
    assert res_fee["judge_valid"] is True

    # Case B: Prospective action claimed as already executed
    client.converse.return_value = {'output': {'message': {'content': [{'text': json.dumps({
        'reason_code_pass': True,
        'must_cite_pass': True,
        'no_hallucination_pass': False, 'support_assertions': [], 'event_absence_pass': True, 'event_order_pass': True, 'policy_disclosure_pass': True,
        'explanation': 'Action presented as completed when status is needs_response.',
    })}]}}}
    res_action = judge_narrative(client, "Merchant concedes dispute and refund is processed", "product_not_received", [], "{}")
    assert res_action["overall_pass"] is False
    assert res_action["no_hallucination_pass"] is False

    # Case C: Fully grounded prospective recommendation passes
    client.converse.return_value = {'output': {'message': {'content': [{'text': json.dumps({
        'reason_code_pass': True,
        'must_cite_pass': True,
        'no_hallucination_pass': True, 'support_assertions': [], 'event_absence_pass': True, 'event_order_pass': True, 'policy_disclosure_pass': True,
        'explanation': 'Fully grounded prospective recommendation.',
    })}]}}}
    res_good = judge_narrative(client, "Recommendation: Concede dispute based on delayed tracking.", "product_not_received", [], "{}")
    assert res_good["overall_pass"] is True
    assert res_good["no_hallucination_pass"] is True


def test_support_assertion_overrides_a_passing_model_verdict():
    """Independent effect extraction can reject a passing broad factual verdict."""
    quote = 'Concession preserves the customer relationship.'
    client = MagicMock()
    narrative_verdict = {'reason_code_pass': True, 'must_cite_pass': True}
    broad_verdict = {'no_hallucination_pass': True, 'explanation': 'The prediction seems reasonable.'}
    outcome_verdict = {'support_assertions': [
        {'field': 'strategy.owner_summary', 'quote': quote, 'support': None},
    ]}
    client.converse.side_effect = [
        judge_response(narrative_verdict, {'inputTokens': 2, 'outputTokens': 1}),
        judge_response(broad_verdict, {'inputTokens': 8, 'outputTokens': 3}),
        judge_response(outcome_verdict, {'inputTokens': 5, 'outputTokens': 2}),
        judge_response({'event_absence_pass': True, 'event_order_pass': True, 'policy_disclosure_pass': True}),
    ]
    result = judge_narrative(client, 'Dispute Reason: fraudulent.', 'fraudulent', [], '{}', {
        'strategy': {'owner_summary': 'Recommend concession. ' + quote},
    })
    assert result['raw_no_hallucination_pass'] is True
    assert result['grounding_judge']['no_hallucination_pass'] is True
    assert result['support_assertions_pass'] is False
    assert result['no_hallucination_pass'] is False
    assert result['overall_pass'] is False
    assert quote in result['support_assertion_errors'][0]
    assert result['narrative_judge'] == narrative_verdict
    assert result['grounding_judge'] == broad_verdict
    assert result['support_judge'] == outcome_verdict
    assert client.converse.call_count == 4
    assert result['usage'] == {'inputTokens': 15, 'outputTokens': 6}
    broad_call, outcome_call = client.converse.call_args_list[1:3]
    assert 'support_assertions' not in broad_call.kwargs['system'][0]['text']
    assert 'support_assertions' in outcome_call.kwargs['system'][0]['text']
    assert broad_call.kwargs['messages'] == outcome_call.kwargs['messages']


@pytest.mark.parametrize('assertions', [
    [],
    [{'field': 'strategy.rationale', 'quote': 'The proposed credit reduces the balance by $25.00.',
      'support': {'path': ['records', 0, 'credit_effect'],
                  'quote': 'The proposed credit reduces the balance by $25.00.'}}],
])
def test_valid_goal_or_source_supported_outcome_preserves_pass(assertions):
    client = MagicMock()
    client.converse.side_effect = [
        judge_response({'reason_code_pass': True, 'must_cite_pass': True}),
        judge_response({'no_hallucination_pass': True}),
        judge_response({'support_assertions': assertions}),
        judge_response({'event_absence_pass': True, 'event_order_pass': True, 'policy_disclosure_pass': True}),
    ]
    facts = {'records': [{'credit_effect': 'The proposed credit reduces the balance by $25.'}]}
    text = 'The proposed credit reduces the balance by $25.' if assertions else 'Aim to retain the customer.'
    result = judge_narrative(client, 'Dispute Reason: fraudulent.', 'fraudulent', [], json.dumps(facts), {
        'strategy': {'rationale': text},
    })
    assert result['support_assertions_pass'] is True
    assert result['overall_pass'] is True


@pytest.mark.parametrize('support,valid', [
    ([{'path': ['refund_at'], 'quote': '2026-08-12'},
      {'path': ['dispute_at'], 'quote': '2026-08-15'}], True),
    ([{'path': ['refund_at'], 'quote': '2026-08-12'},
      {'path': ['missing_event_time'], 'quote': '2026-08-15'}], False),
    ([], False),
])
def test_relationship_citations_require_every_reference_to_exist(support, valid):
    from evals.run import validate_support_assertions

    claim = 'The refund was issued before the dispute.'
    errors = validate_support_assertions(
        [{'field': 'narrative', 'quote': claim, 'support': support}],
        {'narrative': claim}, {'refund_at': '2026-08-12', 'dispute_at': '2026-08-15'},
    )
    assert (not errors) is valid


@pytest.mark.parametrize('bad_assertions', [
    None, {}, 'none', [None], [{}],
    [{'field': 'missing.field', 'quote': 'A credit reduces the balance.', 'support': None}],
    [{'field': 'strategy.rationale', 'quote': '', 'support': None}],
    [{'field': 'strategy.rationale', 'quote': 'Invented output quote', 'support': None}],
    [{'field': 'strategy.rationale', 'quote': 'A credit reduces the balance.', 'support': {}}],
    [{'field': 'strategy.rationale', 'quote': 'A credit reduces the balance.',
      'support': {'path': 'records.0.effect', 'quote': 'A credit reduces the balance.'}}],
])
def test_missing_or_malformed_support_assertions_fail_closed(bad_assertions):
    client = MagicMock()
    verdict = {}
    if bad_assertions is not None:
        verdict['support_assertions'] = bad_assertions
    client.converse.side_effect = [
        judge_response({'reason_code_pass': True, 'must_cite_pass': True}),
        judge_response({'no_hallucination_pass': True}),
        judge_response(verdict),
        judge_response({'event_absence_pass': True, 'event_order_pass': True, 'policy_disclosure_pass': True}),
    ]
    result = judge_narrative(client, 'Dispute Reason: fraudulent.', 'fraudulent', [], '{}', {
        'strategy': {'rationale': 'A credit reduces the balance.'},
    })
    assert result['raw_no_hallucination_pass'] is True
    assert result['support_assertions_pass'] is False
    assert result['overall_pass'] is False
    assert result['support_judge'] == verdict


@pytest.mark.parametrize('path,quote', [
    ([], 'A credit reduces the balance.'),
    (['records', 2, 'effect'], 'A credit reduces the balance.'),
    (['records', -1, 'effect'], 'A credit reduces the balance.'),
    (['records', True, 'effect'], 'A credit reduces the balance.'),
    (['records', 0, 'missing'], 'A credit reduces the balance.'),
    (['records', 0, 'effect'], ''),
    (['records', 0, 'effect'], 'Invented source quote'),
    (['records', 0], 'A credit reduces the balance.'),
    (['records', 0, 'absent'], 'null'),
])
def test_invalid_outcome_source_citation_fails_closed(path, quote):
    client = MagicMock()
    effect = 'A credit reduces the balance.'
    client.converse.side_effect = [
        judge_response({'reason_code_pass': True, 'must_cite_pass': True}),
        judge_response({'no_hallucination_pass': True}),
        judge_response({'support_assertions': [{'field': 'strategy.rationale', 'quote': effect,
                                               'support': {'path': path, 'quote': quote}}]}),
        judge_response({'event_absence_pass': True, 'event_order_pass': True, 'policy_disclosure_pass': True}),
    ]
    result = judge_narrative(client, 'Dispute Reason: fraudulent.', 'fraudulent', [],
                             json.dumps({'records': [{'effect': effect, 'absent': None}]}), {
                                 'strategy': {'rationale': effect},
                             })
    assert result['support_assertions_pass'] is False
    assert result['overall_pass'] is False


@pytest.mark.parametrize('claim,facts', [
    ('This customer has 5 prior orders.', {'order_count': 5}),
    ('The dispute amount is $340.01.', {'amount_cents': 34000}),
])
def test_empty_outcomes_cannot_override_a_broad_factual_failure(claim, facts):
    client = MagicMock()
    client.converse.side_effect = [
        judge_response({'reason_code_pass': True, 'must_cite_pass': True}),
        judge_response({'no_hallucination_pass': False, 'explanation': 'The stated value is unsupported.'}),
        judge_response({'support_assertions': []}),
        judge_response({'event_absence_pass': True, 'event_order_pass': True, 'policy_disclosure_pass': True}),
    ]
    result = judge_narrative(client, 'Dispute Reason: fraudulent.', 'fraudulent', [], json.dumps(facts), {
        'strategy': {'rationale': claim},
    })
    assert result['raw_no_hallucination_pass'] is False
    assert result['support_assertions_pass'] is True
    assert result['no_hallucination_pass'] is False
    assert result['overall_pass'] is False
    broad = client.converse.call_args_list[1].kwargs
    payload = json.loads(broad['messages'][0]['content'][0]['text'])
    assert payload['source_records'] == facts
    assert payload['factual_output_fields']['strategy.rationale'] == claim


def test_outcome_call_failure_cannot_be_hidden_by_passing_other_judges():
    client = MagicMock()
    client.converse.side_effect = [
        judge_response({'reason_code_pass': True, 'must_cite_pass': True}),
        judge_response({'no_hallucination_pass': True}),
        RuntimeError('outcome model unavailable'),
        judge_response({'event_absence_pass': True, 'event_order_pass': True, 'policy_disclosure_pass': True}),
    ]
    result = judge_narrative(client, 'Dispute Reason: fraudulent.', 'fraudulent', [], '{}')
    assert result['raw_no_hallucination_pass'] is True
    assert result['support_assertions_pass'] is False
    assert result['overall_pass'] is False
    assert 'RuntimeError' in result['support_judge']['explanation']
    assert client.converse.call_count == 4


@pytest.mark.parametrize('key,value', [
    ('event_absence_pass', False), ('event_order_pass', False),
    ('policy_disclosure_pass', False), ('event_absence_pass', None),
    ('event_order_pass', 'true'),
])
def test_missing_or_failed_premise_check_cannot_hide_behind_other_passes(key, value):
    verdict = {'event_absence_pass': True, 'event_order_pass': True, 'policy_disclosure_pass': True}
    if value is None:
        verdict.pop(key)
    else:
        verdict[key] = value
    client = MagicMock()
    client.converse.side_effect = [
        judge_response({'reason_code_pass': True, 'must_cite_pass': True}),
        judge_response({'no_hallucination_pass': True}),
        judge_response({'support_assertions': []}),
        judge_response(verdict),
    ]
    result = judge_narrative(client, 'Dispute Reason: fraudulent.', 'fraudulent', [], '{}')
    assert result['premise_judge'] == verdict
    assert result['premise_checks_pass'] is False
    assert result['no_hallucination_pass'] is False
    assert result['overall_pass'] is False


def test_build_evidence_graph_topology():
    """Verify build_evidence_graph constructs all 7 nodes with correct prompts."""
    from agent.graph import build_evidence_graph

    mock_model = MagicMock()
    graph, agents = build_evidence_graph(model=mock_model)

    assert set(agents.keys()) == {"intake", "orders", "shipping", "comms", "history", "strategy", "drafter"}
    assert "Orders Evidence Agent" in agents["orders"].system_prompt
    assert "Shipping & Fulfillment Evidence Agent" in agents["shipping"].system_prompt
    assert "Customer Communications Evidence Agent" in agents["comms"].system_prompt
    assert "Customer History & Merchant Policy Agent" in agents["history"].system_prompt
    assert "Senior Dispute Strategist" in agents["strategy"].system_prompt
    assert "Dispute Evidence Drafter" in agents["drafter"].system_prompt
    assert "PROSPECTIVE RECOMMENDATION" in agents["drafter"].system_prompt


def test_no_hardcoded_case_references_in_graph():
    """Verify agent/graph.py contains zero hardcoded case numbers, customer names, or canned case scripts."""
    import re
    from pathlib import Path

    graph_code = Path("agent/graph.py").read_text(encoding="utf-8")

    # Disallow golden set case IDs, evaluation customer IDs, and evaluation order IDs
    forbidden_patterns = [
        r"case_[0-9]+",
        r"case\s+[0-9]+",
        r"cases\s+[0-9]+",
        r"ORD-EVAL-[0-9]+",
        r"CUST-EVAL-[0-9]+",
        r"dp_eval_[0-9]+",
        r"ORD-14[AB]",
        r"MSG-11",
        r"RET-88008",
        r"re_prior10",
        r"Jessica Lee",
        r"Amanda Ross",
        r"Carlos Gomez",
        r"Michael Taylor",
    ]
    for pat in forbidden_patterns:
        match = re.search(pat, graph_code, re.IGNORECASE)
        assert match is None, f"Found prohibited hardcoded reference '{match.group(0)}' matching pattern '{pat}' in agent/graph.py"


def test_missing_vs_affirmative_evidence_rules():
    """Verify prompts enforce principled handling of empty communications without affirmative accusations."""
    from agent.graph import build_evidence_graph

    mock_model = MagicMock()
    _, agents = build_evidence_graph(model=mock_model)

    drafter_prompt = agents["drafter"].system_prompt
    comms_prompt = agents["comms"].system_prompt

    # Drafter prompt must require standard empty comms sentence and prohibit affirmative bad-faith inferences
    assert "No pre-dispute customer communications exist in merchant records." in drafter_prompt
    assert "NEVER write 'No customer inquiry or fraud report was submitted'" in drafter_prompt
    assert "Zero Editorial Gloss" in drafter_prompt or "ZERO EDITORIAL GLOSS" in drafter_prompt

    # Comms prompt must instruct that absence of records does not imply bad faith
    assert "do NOT assume lack of records implies bad faith" in comms_prompt


@pytest.mark.parametrize('tainted_field', ['owner_summary', 'rationale', 'uncategorized_text'])
def test_supporting_output_failure_cannot_hide_behind_passing_narrative(tainted_field):
    """Verify sibling output reaches the judge and its failure is authoritative."""
    output = {"strategy": {"action": "concede"}, "evidence_packet": {}}
    group = "strategy" if tainted_field in {"owner_summary", "rationale"} else "evidence_packet"
    output[group][tainted_field] = "Issue a full refund and absorb the $15 fee."
    client = MagicMock()
    client.converse.return_value = {'output': {'message': {'content': [{'text': json.dumps({
        'reason_code_pass': True, 'must_cite_pass': True, 'no_hallucination_pass': False, 'support_assertions': [], 'event_absence_pass': True, 'event_order_pass': True, 'policy_disclosure_pass': True,
        'explanation': f'Unsupported refund and fee in {tainted_field}.',
    })}]}}}

    result = judge_narrative(client, 'Dispute Reason: fraudulent. Recommendation: Concede.',
                             'fraudulent', [], '{}', supporting_output=output)

    prompt = client.converse.call_args.kwargs['messages'][0]['content'][0]['text']
    assert json.loads(prompt)['factual_output_fields'][f'{group}.{tainted_field}'] == normalize_currency_text(output[group][tainted_field])
    assert 'strategy.action' not in json.loads(prompt)['factual_output_fields']
    assert result['reason_code_pass'] and result['must_cite_pass'] and result['word_count_pass']
    assert result['overall_pass'] is False
    assert client.converse.call_count == 4
    citation_input = json.loads(client.converse.call_args_list[0].kwargs["messages"][0]["content"][0]["text"])
    assert set(citation_input) == {"narrative", "required_reason", "required_narrative_references"}
    assert output[group][tainted_field] not in json.dumps(citation_input)


def test_supporting_text_does_not_change_narrative_word_count_or_missing_items():
    client = MagicMock()
    client.converse.return_value = {'output': {'message': {'content': [{'text': json.dumps({
        'reason_code_pass': True, 'must_cite_pass': False, 'no_hallucination_pass': True, 'support_assertions': [], 'event_absence_pass': True, 'event_order_pass': True, 'policy_disclosure_pass': True,
    })}]}}}
    result = judge_narrative(client, 'Dispute Reason: fraudulent.', 'fraudulent', ['tracking-123'], '{}', {
        'strategy': {'action': 'fight', 'win_probability': 0.85},
        'evidence_packet': {'uncategorized_text': 'tracking-123 ' * 300, 'files': []},
    })
    assert result['word_count'] == 3
    assert result['word_count_pass'] is True
    assert result['missing_items'] == ['tracking-123']
    assert result['overall_pass'] is False


def test_attachment_guard_overrides_a_false_positive_model_verdict():
    client = MagicMock()
    client.converse.return_value = {'output': {'message': {'content': [{'text': json.dumps({
        'reason_code_pass': True, 'must_cite_pass': True, 'no_hallucination_pass': True, 'support_assertions': [], 'event_absence_pass': True, 'event_order_pass': True, 'policy_disclosure_pass': True,
    })}]}}}
    result = judge_narrative(client, 'Dispute Reason: fraudulent.', 'fraudulent', [], '{}', {
        'evidence_packet': {'files': ['unproduced.pdf']},
    })
    assert result['grounding_judge']['no_hallucination_pass'] is True
    assert result['artifact_pass'] is False
    assert result['no_hallucination_pass'] is False
    assert result['overall_pass'] is False
    assert 'unproduced attachment' in result['explanation']


def test_eval_rejection_continues_suite_and_persists_complete_output(monkeypatch, tmp_path):
    """Run the actual harness with offline model responses, including a rejected packet."""
    import evals.run as runner
    from agent.models import DisputeStrategy, EvidencePacket

    strategy = DisputeStrategy(action='fight', win_probability=.85, expected_value_cents=100,
                               customer_value='new', evidence_strength='strong',
                               rationale='Recommend fighting based on delivery records.',
                               owner_summary='Recommend fighting this dispute.')
    packet = EvidencePacket(narrative='Dispute Reason: product_not_received. Delivery recorded.')
    # Every field, not a manually maintained subset, must enter the judge and saved artifact.
    for name in type(packet).model_fields:
        if name != 'narrative':
            setattr(packet, name, [f'{name}-sentinel'] if name == 'files' else f'{name}-sentinel')
    pipeline = MagicMock(side_effect=[ValueError('Unverified attachment reference'), (strategy, packet, None)])
    monkeypatch.setattr(runner.agent.graph, 'run_evidence_pipeline', pipeline)
    judge = MagicMock()
    judge.converse.return_value = {'output': {'message': {'content': [{'text': json.dumps({
        'reason_code_pass': True, 'must_cite_pass': True, 'no_hallucination_pass': False, 'support_assertions': [], 'event_absence_pass': True, 'event_order_pass': True, 'policy_disclosure_pass': True,
        'explanation': 'Sentinel values are unsupported.',
    })}]}}}
    monkeypatch.setattr(runner, 'get_llm_judge_client', lambda: judge)
    cases_dir = tmp_path / 'cases'
    cases_dir.mkdir()
    case = json.loads((runner.CASES_DIR / 'case_01.json').read_text())
    for number in (1, 2):
        case['id'] = f'case_{number:02d}'
        (cases_dir / f"{case['id']}.json").write_text(json.dumps(case))
    monkeypatch.setattr(runner, 'CASES_DIR', cases_dir)
    monkeypatch.setattr(runner.sys, 'argv', ['evals/run.py'])
    report = tmp_path / 'evaluation.md'
    monkeypatch.setenv('EVAL_REPORT_PATH', str(report))
    original_tools = (runner.agent.graph.get_dispute, runner.agent.graph.get_charge_context)
    original_db = runner.agent.tools.evidence_tools.LOCAL_DB_PATH

    with pytest.raises(SystemExit) as exc:
        runner.main()

    assert exc.value.code == 1
    assert pipeline.call_count == 2
    assert judge.converse.call_count == 4  # Four isolated checks for accepted output; none for rejected output.
    rows = json.loads(report.with_suffix('.json').read_text())['results']
    assert rows[0]['pipeline_error'] == 'ValueError: Unverified attachment reference'
    assert not any(rows[0][key] for key in ('overall_pass', 'action_match', 'gate_match', 'judge_pass', 'ev_sign'))
    expected_output = {'strategy': strategy.model_dump(), 'evidence_packet': packet.model_dump()}
    assert rows[1]['supporting_output'] == expected_output
    assert rows[1]['case_facts']['dispute']['id'] == case['dispute_id']
    assert 'scenario_description' not in rows[1]['case_facts']
    assert rows[1]['case_facts']['merchant_policy']['vip_concede_max_cents'] == 50000
    prompt = judge.converse.call_args.kwargs['messages'][0]['content'][0]['text']
    fields = json.loads(prompt)['factual_output_fields']
    for name in type(packet).model_fields:
        if name != 'narrative':
            assert f'{name}-sentinel' in fields.values()
    assert fields['strategy.rationale'] == strategy.rationale
    assert fields['strategy.owner_summary'] == strategy.owner_summary
    assert fields['strategy.customer_value'] == strategy.customer_value
    assert json.dumps(expected_output, indent=2) in report.read_text()
    assert (runner.agent.graph.get_dispute, runner.agent.graph.get_charge_context) == original_tools
    assert runner.agent.tools.evidence_tools.LOCAL_DB_PATH == original_db
