"""Offline acceptance checks for source-derived final evidence and identity links."""
from copy import deepcopy

import pytest

from agent.factual_output import render_factual_output
from agent.models import DisputeStrategy


def source_records(tag='A'):
    order_id, customer_id = f'ORDER-{tag}', f'CUSTOMER-{tag}'
    metadata = {'order_id': order_id, 'customer_id': customer_id}
    values = [
        ('get_dispute', {'dispute_id': f'dp_{tag}'}, {
            'id': f'dp_{tag}', 'reason': 'product_unacceptable', 'amount': 4000, 'currency': 'usd',
            'status': 'needs_response', 'charge': f'ch_{tag}', 'payment_intent': f'pi_{tag}', 'metadata': metadata}),
        ('get_charge_context', {'charge_id_or_payment_intent': f'ch_{tag}'}, {
            'charge_id': f'ch_{tag}', 'payment_intent_id': f'pi_{tag}', 'metadata': metadata,
            'card_checks': {'address_line1_check': 'pass', 'cvc_check': 'pass'}}),
        ('get_order_evidence', {'order_id': order_id}, {
            'id': order_id, 'customer_id': customer_id, 'customer_name': 'Alex Morgan',
            'customer_email': 'alex@example.test', 'created_at': '2026-08-01T09:00:00Z', 'status': 'fulfilled',
            'billing_address': {'line1': '10 Main St', 'city': 'Boston', 'country': 'US'}}),
        ('get_shipping_evidence', {'order_id': order_id}, {
            'order_id': order_id, 'carrier': 'UPS', 'tracking_number': f'TRACK-{tag}',
            'status': 'delivered', 'shipped_at': '2026-08-03T10:15:00Z', 'delivered_at': '2026-08-05T13:00:00Z',
            'signed_by': None, 'shipping_address': {'line1': '20 Office St', 'city': 'Boston', 'country': 'US'}}),
        ('get_customer_comms', {'order_id': order_id, 'customer_id': customer_id}, {
            'order_id': order_id, 'customer_id': customer_id, 'messages': []}),
        ('get_merchant_history_and_policy', {'customer_id': customer_id}, {
            'customer_tier': 'repeat', 'order_count': 3, 'lifetime_value_cents': 10000,
            'policy': {'vip_concede_max_cents': 50000, 'return_policy': 'Returns accepted within 30 days.'}}),
    ]
    return deepcopy([{'tool': tool, 'arguments': args, 'status': 'success', 'content': [value]}
                     for tool, args, value in values])


@pytest.fixture
def raw_strategy():
    return DisputeStrategy(action='concede', win_probability=.2, expected_value_cents=0,
                           customer_value='new', evidence_strength='weak',
                           rationale='Concession guarantees loyalty and saves a fee. Delivery was without signature.',
                           owner_summary='Refund completed; no signature was obtained.')


def test_final_text_uses_sources_and_preserves_assessments(raw_strategy):
    records = source_records()
    original = deepcopy(records)
    strategy, packet = render_factual_output(raw_strategy, records)
    assert records == original
    assert strategy.action == raw_strategy.action
    assert strategy.win_probability == raw_strategy.win_probability
    assert strategy.expected_value_cents == raw_strategy.expected_value_cents
    assert strategy.evidence_strength == raw_strategy.evidence_strength
    assert strategy.customer_value == 'repeat'
    assert '3 total orders' in strategy.rationale
    assert '$100.00' in strategy.rationale
    for output in (strategy.rationale, strategy.owner_summary, packet.narrative):
        assert 'guarantees loyalty' not in output
        assert 'without signature' not in output
        assert 'no signature was obtained' not in output
        assert 'Refund completed' not in output
    assert 'No signature is recorded in the supplied delivery record.' in packet.narrative
    assert 'Order ORDER-A; created 2026-08-01T09:00:00Z' in packet.narrative
    assert 'shipped: 2026-08-03T10:15:00Z' in packet.narrative
    assert 'delivered: 2026-08-05T13:00:00Z' in packet.narrative
    assert 'created_at=' not in packet.narrative
    assert 'pending approval/execution' not in packet.narrative
    assert packet.shipping_date == '2026-08-03'
    assert packet.shipping_address == '20 Office St, Boston, US'
    assert packet.billing_address == '10 Main St, Boston, US'
    assert packet.refund_policy_disclosure is None
    assert packet.cancellation_policy_disclosure is None
    assert packet.customer_communication is None
    assert packet.files == []
    assert 'Returns accepted within 30 days.' in packet.narrative
    assert 'Recorded VIP concession limit (vip_concede_max_cents): $500.00.' in packet.narrative


def test_rejects_other_cases_evidence_under_dispute(raw_strategy):
    records = source_records('B')
    records[0] = source_records('A')[0]
    with pytest.raises(ValueError, match='linked to the dispute|linkage'):
        render_factual_output(raw_strategy, records)


@pytest.mark.parametrize('index,section,key,value', [
    (1, 'arguments', 'charge_id_or_payment_intent', 'ch_OTHER'),
    (1, 'content', 'charge_id', 'ch_OTHER'),
    (1, 'content', 'payment_intent_id', 'pi_OTHER'),
    (2, 'arguments', 'order_id', 'ORDER-OTHER'),
    (3, 'arguments', 'order_id', 'ORDER-OTHER'),
    (3, 'content', 'order_id', 'ORDER-OTHER'),
    (4, 'arguments', 'customer_id', 'CUSTOMER-OTHER'),
    (4, 'content', 'customer_id', 'CUSTOMER-OTHER'),
    (5, 'arguments', 'customer_id', 'CUSTOMER-OTHER'),
    (5, 'content', 'customer_id', 'CUSTOMER-OTHER'),
])
def test_rejects_conflicting_source_identifiers(raw_strategy, index, section, key, value):
    records = source_records()
    target = records[index]['arguments'] if section == 'arguments' else records[index]['content'][0]
    target[key] = value
    with pytest.raises(ValueError):
        render_factual_output(raw_strategy, records)


@pytest.mark.parametrize('key,value', [('order_id', 'ORDER-OTHER'), ('customer_id', 'CUSTOMER-OTHER')])
def test_payment_metadata_must_match_merchant_evidence(raw_strategy, key, value):
    records = source_records()
    records[1]['content'][0]['metadata'][key] = value
    with pytest.raises(ValueError, match='linkage'):
        render_factual_output(raw_strategy, records)


def test_missing_payment_order_link_requires_review(raw_strategy):
    records = source_records()
    for index in (0, 1):
        records[index]['content'][0]['metadata'] = {}
    with pytest.raises(ValueError, match='do not identify the evidence order'):
        render_factual_output(raw_strategy, records)


@pytest.mark.parametrize('failure', ['failed', 'error_payload', 'conflicting', 'missing'])
def test_failed_or_ambiguous_sources_require_review(raw_strategy, failure):
    records = source_records()
    if failure == 'failed':
        records[3]['status'] = 'error'
    elif failure == 'error_payload':
        records[3]['content'] = [{'error': 'No shipment found'}]
    elif failure == 'conflicting':
        other = deepcopy(records[3])
        other['content'][0]['tracking_number'] = 'OTHER'
        records.append(other)
    else:
        records.pop(3)
    with pytest.raises(ValueError, match='source records'):
        render_factual_output(raw_strategy, records)


def test_expanded_stripe_links_aliases_and_identical_retrievals_are_supported(raw_strategy):
    records = source_records()
    dispute = records[0]['content'][0]
    dispute['id'] = 'du_resolved'
    records[0]['arguments']['dispute_id'] = 'internal-alias'
    dispute['charge'] = {'id': 'ch_A', 'payment_intent': 'pi_A', 'customer': 'cus_STRIPE',
                         'metadata': {'order_id': 'ORDER-A'}}
    dispute['payment_intent'] = {'id': 'pi_A', 'customer': 'cus_STRIPE'}
    records[1]['arguments']['charge_id_or_payment_intent'] = 'pi_A'
    records[1]['content'][0]['customer'] = 'cus_STRIPE'
    records.append(deepcopy(records[3]))
    _, packet = render_factual_output(raw_strategy, records)
    assert 'du_resolved' in packet.narrative
    assert packet.customer_name == 'Alex Morgan'
    records[1]['content'][0]['customer'] = 'cus_OTHER'
    with pytest.raises(ValueError, match='Stripe customer'):
        render_factual_output(raw_strategy, records)


@pytest.mark.parametrize('only', ['charge', 'payment_intent'])
def test_anchored_payment_lookup_can_enrich_the_other_identifier(raw_strategy, only):
    records = source_records()
    dispute = records[0]['content'][0]
    if only == 'charge':
        dispute.pop('payment_intent')
    else:
        dispute.pop('charge')
        records[1]['arguments']['charge_id_or_payment_intent'] = 'pi_A'
    records[2]['content'][0].update(charge_id='ch_A', payment_intent_id='pi_A')
    _, packet = render_factual_output(raw_strategy, records)
    assert packet.customer_name == 'Alex Morgan'


def test_digital_access_stays_out_of_physical_shipping_fields(raw_strategy):
    records = source_records()
    records[3]['content'][0]['carrier'] = 'Digital'
    records[3]['content'][0]['tracking_number'] = 'ACCESS-REF'
    _, packet = render_factual_output(raw_strategy, records)
    assert 'Digital access record' in packet.narrative
    assert 'access reference: ACCESS-REF' in packet.narrative
    assert 'access delivery recorded: 2026-08-05T13:00:00Z' in packet.narrative
    for field in ('shipping_address', 'shipping_carrier', 'shipping_tracking_number', 'shipping_date'):
        assert getattr(packet, field) is None


def test_messages_are_quoted_as_records_and_other_orders_are_labeled(raw_strategy):
    records = source_records()
    records[4]['content'][0]['messages'] = [{
        'customer_id': 'CUSTOMER-A', 'order_id': 'ORDER-EARLIER', 'created_at': '2026-07-01T10:00:00Z',
        'subject': 'Receipt comparison REF-77', 'body': 'Two distinct items were ordered separately.'}]
    _, packet = render_factual_output(raw_strategy, records)
    assert 'order ORDER-EARLIER; subject "Receipt comparison REF-77"' in packet.narrative
    assert 'states: "Two distinct items were ordered separately."' in packet.narrative
    assert 'customer wrote' not in packet.narrative
    assert packet.customer_communication is None
    records[4]['content'][0]['messages'][0]['customer_id'] = 'CUSTOMER-OTHER'
    with pytest.raises(ValueError, match='message customer'):
        render_factual_output(raw_strategy, records)


def test_long_source_messages_fail_for_review_without_truncation(raw_strategy):
    records = source_records()
    records[4]['content'][0]['messages'] = [{'subject': 'Long message', 'body': 'detail ' * 300}]
    with pytest.raises(ValueError, match='word budget; review required'):
        render_factual_output(raw_strategy, records)


def test_invalid_physical_shipping_date_requires_review(raw_strategy):
    records = source_records()
    records[3]['content'][0]['shipped_at'] = 'yesterday'
    with pytest.raises(ValueError, match='shipment date is invalid'):
        render_factual_output(raw_strategy, records)
