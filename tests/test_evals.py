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


def test_judge_accepts_grounded_verdict_and_rejects_empty_or_long_text(monkeypatch):
    monkeypatch.setenv('BEDROCK_MODEL_ID', 'generator-model')
    monkeypatch.setenv('BEDROCK_JUDGE_MODEL_ID', 'judge-model')
    client = MagicMock()
    client.converse.return_value = {'usage': {'inputTokens': 100, 'outputTokens': 25}, 'output': {'message': {'content': [{'text': json.dumps({
        'reason_code_pass': True, 'must_cite_pass': True, 'no_hallucination_pass': True,
    })}]}}}
    for narrative, expected in [('Delivery recorded.', True), ('', False), ('word ' * 251, False)]:
        result = judge_narrative(client, narrative, 'product_not_received', [], '{}')
        assert result['overall_pass'] is expected
        assert result['model_id'] == client.converse.call_args.kwargs['modelId'] == 'judge-model'
        assert result['usage'] == {'inputTokens': 100, 'outputTokens': 25}


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
        'reason_code_pass': True, 'must_cite_pass': True, 'no_hallucination_pass': True,
    })}]}}}

    judge_narrative(
        judge_client=client,
        narrative="Test narrative",
        reason="fraudulent",
        must_cite=["AVS", "442004"],
        case_summary='{"test": "facts"}',
    )

    call_args = client.converse.call_args[1]
    prompt_text = call_args["system"][0]["text"]

    assert "100 cents equals $1" in prompt_text
    assert "UTC/ISO date reformattings are equivalent" in prompt_text
    assert "A quoted report establishes what was reported, not its independent truth" in prompt_text
    assert "No X documented/in merchant records" in prompt_text
    assert "Current recommendations must be prospective" in prompt_text


def test_keyword_presence_cannot_override_negative_judge_verdict():
    """Verify keyword match in narrative cannot force must_cite_pass when judge says False."""
    client = MagicMock()
    # Judge finds must_cite semantically invalid despite exact keywords appearing
    client.converse.return_value = {'output': {'message': {'content': [{'text': json.dumps({
        'reason_code_pass': True,
        'must_cite_pass': False,
        'no_hallucination_pass': True,
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
        'no_hallucination_pass': False,
        'explanation': 'Unsupported $15 statutory loss fee not in case facts.',
    })}]}}}
    res_fee = judge_narrative(client, "Conceding dispute to avoid $15 fee", "product_not_received", [], "{}")
    assert res_fee["overall_pass"] is False
    assert res_fee["no_hallucination_pass"] is False

    # Case B: Prospective action claimed as already executed
    client.converse.return_value = {'output': {'message': {'content': [{'text': json.dumps({
        'reason_code_pass': True,
        'must_cite_pass': True,
        'no_hallucination_pass': False,
        'explanation': 'Action presented as completed when status is needs_response.',
    })}]}}}
    res_action = judge_narrative(client, "Merchant concedes dispute and refund is processed", "product_not_received", [], "{}")
    assert res_action["overall_pass"] is False
    assert res_action["no_hallucination_pass"] is False

    # Case C: Fully grounded prospective recommendation passes
    client.converse.return_value = {'output': {'message': {'content': [{'text': json.dumps({
        'reason_code_pass': True,
        'must_cite_pass': True,
        'no_hallucination_pass': True,
        'explanation': 'Fully grounded prospective recommendation.',
    })}]}}}
    res_good = judge_narrative(client, "Recommendation: Concede dispute based on delayed tracking.", "product_not_received", [], "{}")
    assert res_good["overall_pass"] is True
    assert res_good["no_hallucination_pass"] is True


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
        'reason_code_pass': True, 'must_cite_pass': True, 'no_hallucination_pass': False,
        'explanation': f'Unsupported refund and fee in {tainted_field}.',
    })}]}}}

    result = judge_narrative(client, 'Dispute Reason: fraudulent. Recommendation: Concede.',
                             'fraudulent', [], '{}', supporting_output=output)

    prompt = client.converse.call_args.kwargs['messages'][0]['content'][0]['text']
    assert json.loads(prompt)['supporting_output'] == output
    assert result['reason_code_pass'] and result['must_cite_pass'] and result['word_count_pass']
    assert result['overall_pass'] is False
    client.converse.assert_called_once()


def test_supporting_text_does_not_change_narrative_word_count_or_missing_items():
    client = MagicMock()
    client.converse.return_value = {'output': {'message': {'content': [{'text': json.dumps({
        'reason_code_pass': True, 'must_cite_pass': False, 'no_hallucination_pass': True,
    })}]}}}
    result = judge_narrative(client, 'Dispute Reason: fraudulent.', 'fraudulent', ['tracking-123'], '{}', {
        'strategy': {'action': 'fight', 'win_probability': 0.85},
        'evidence_packet': {'uncategorized_text': 'tracking-123 ' * 300, 'files': []},
    })
    assert result['word_count'] == 3
    assert result['word_count_pass'] is True
    assert result['missing_items'] == ['tracking-123']
    assert result['overall_pass'] is False


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
        'reason_code_pass': True, 'must_cite_pass': True, 'no_hallucination_pass': False,
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
    judge.converse.assert_called_once()  # Rejected output needs no judge call.
    rows = json.loads(report.with_suffix('.json').read_text())['results']
    assert rows[0]['pipeline_error'] == 'ValueError: Unverified attachment reference'
    assert not any(rows[0][key] for key in ('overall_pass', 'action_match', 'gate_match', 'judge_pass', 'ev_sign'))
    expected_output = {'strategy': strategy.model_dump(), 'evidence_packet': packet.model_dump()}
    assert rows[1]['supporting_output'] == expected_output
    assert rows[1]['case_facts']['dispute']['id'] == case['dispute_id']
    prompt = judge.converse.call_args.kwargs['messages'][0]['content'][0]['text']
    assert json.loads(prompt)['supporting_output'] == expected_output
    assert json.dumps(expected_output, indent=2) in report.read_text()
    assert (runner.agent.graph.get_dispute, runner.agent.graph.get_charge_context) == original_tools
    assert runner.agent.tools.evidence_tools.LOCAL_DB_PATH == original_db
