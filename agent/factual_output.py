"""Render factual text from linked source records; retain model assessments."""
from datetime import datetime
from decimal import Decimal
import json

from agent.models import DisputeStrategy, EvidencePacket


def _identifier(value):
    if isinstance(value, dict):
        value = value.get('id')
    return value.strip() if isinstance(value, str) and value.strip() else None


def _linked_sources(records):
    """Validate the actual tool results and lookup arguments before combining facts."""
    arguments = {}

    def record(tool):
        entries = [entry for entry in records if entry.get('tool') == tool]
        values = []
        arguments[tool] = []
        for entry in entries:
            content, args = entry.get('content'), entry.get('arguments')
            if (entry.get('status') != 'success' or not isinstance(args, dict)
                    or not isinstance(content, list) or not content
                    or any(not isinstance(value, dict) or value.get('error') for value in content)):
                raise ValueError(f'Failed or malformed source records for {tool}')
            values.extend(content)
            arguments[tool].append(args)
        if not values or any(value != values[0] for value in values):
            raise ValueError(f'Missing or conflicting source records for {tool}')
        return values[0]

    dispute, charge, order, shipment, comms, history = [record(tool) for tool in (
        'get_dispute', 'get_charge_context', 'get_order_evidence',
        'get_shipping_evidence', 'get_customer_comms', 'get_merchant_history_and_policy')]
    dispute_id, order_id, customer_id = map(_identifier, (dispute.get('id'), order.get('id'), order.get('customer_id')))
    if not all((dispute_id, order_id, customer_id)):
        raise ValueError('Dispute, order, and customer identifiers are required')

    def match(value, expected, label, required=False):
        if value is None or value == '':
            if required:
                raise ValueError(f'Missing {label}')
        elif _identifier(value) != expected:
            raise ValueError(f'Conflicting {label}')

    def metadata(value):
        meta = value.get('metadata') or {}
        if not isinstance(meta, dict):
            raise ValueError('Source metadata must be an object')
        return meta

    dispute_charge = dispute.get('charge')
    dispute_pi = dispute.get('payment_intent')
    charge_id = _identifier(dispute_charge)
    pi_id = _identifier(dispute_pi)
    if isinstance(dispute_charge, dict):
        nested_pi = _identifier(dispute_charge.get('payment_intent'))
        if pi_id and nested_pi and pi_id != nested_pi:
            raise ValueError('Conflicting payment intent in dispute charge')
        pi_id = pi_id or nested_pi
    payment_ids = {value for value in (charge_id, pi_id) if value}
    if not payment_ids:
        raise ValueError('Dispute source has no charge or payment intent linkage')

    for args in arguments['get_dispute']:
        requested = _identifier(args.get('dispute_id'))
        if not requested:
            raise ValueError('Missing dispute lookup identifier')
        # The Stripe tool resolves internal aliases; do not equate their spelling
        # with the returned ID. Native Stripe IDs bypass that alias resolution.
        native_id = requested.startswith('du_') or (requested.startswith('dp_') and len(requested) > 10 and requested[3].isalnum())
        if native_id and requested != dispute_id:
            raise ValueError('Dispute lookup returned a different Stripe dispute')
    for args in arguments['get_charge_context']:
        if _identifier(args.get('charge_id_or_payment_intent')) not in payment_ids:
            raise ValueError('Charge lookup is not linked to the dispute')
    # The anchored charge/PI lookup can enrich the other payment identifier.
    # Validate its known reference before using that enrichment to link the order.
    if charge_id:
        match(charge.get('charge_id'), charge_id, 'charge identifier')
    if pi_id:
        match(charge.get('payment_intent_id'), pi_id, 'payment intent identifier')
    charge_id = charge_id or _identifier(charge.get('charge_id'))
    pi_id = pi_id or _identifier(charge.get('payment_intent_id'))
    payment_ids.update(value for value in (charge_id, pi_id) if value)
    for payload in (charge, order):
        match(payload.get('charge_id'), charge_id, 'charge identifier')
        match(payload.get('payment_intent_id'), pi_id, 'payment intent identifier')
    if charge.get('id') is not None and _identifier(charge['id']) not in payment_ids:
        raise ValueError('Charge context identifies a different payment')

    payment_sources = [dispute, charge]
    payment_sources.extend(value for value in (dispute_charge, dispute_pi) if isinstance(value, dict))
    order_links = []
    stripe_customers = []
    for value in payment_sources:
        meta = metadata(value)
        for link in (value.get('order_id'), meta.get('order_id')):
            if link is not None:
                match(link, order_id, 'payment order linkage')
                order_links.append(link)
        for link in (value.get('customer_id'), meta.get('customer_id')):
            match(link, customer_id, 'merchant customer linkage')
        # Stripe customer IDs and merchant customer IDs are separate namespaces.
        customer = _identifier(value.get('customer'))
        if customer:
            if customer.startswith('cus_'):
                stripe_customers.append(customer)
            else:
                match(customer, customer_id, 'merchant customer linkage')
    if not order_links:
        raise ValueError('Payment sources do not identify the evidence order')
    if order.get('stripe_customer_id'):
        stripe_customers.append(_identifier(order['stripe_customer_id']))
    if len(set(stripe_customers)) > 1:
        raise ValueError('Conflicting Stripe customer identifiers')

    for tool in ('get_order_evidence', 'get_shipping_evidence', 'get_customer_comms'):
        for args in arguments[tool]:
            match(args.get('order_id'), order_id, f'{tool} order argument', required=True)
    for tool in ('get_customer_comms', 'get_merchant_history_and_policy'):
        for args in arguments[tool]:
            match(args.get('customer_id'), customer_id, f'{tool} customer argument', required=True)
    for payload in (shipment, comms):
        match(payload.get('order_id'), order_id, 'evidence order identifier', required=True)
    match(comms.get('customer_id'), customer_id, 'communications customer identifier', required=True)
    match(shipment.get('customer_id'), customer_id, 'shipment customer identifier')
    match(history.get('customer_id'), customer_id, 'history customer identifier')

    messages = comms.get('messages')
    if not isinstance(messages, list) or any(not isinstance(message, dict) for message in messages):
        raise ValueError('Communications source must contain message objects')
    for message in messages:
        match(message.get('customer_id'), customer_id, 'message customer identifier')
        # The adapter also retrieves this customer's messages about other orders.
        # Keep that supported history, but label the other order when rendering it.
        if message.get('order_id') not in (None, '', order_id) and _identifier(message.get('customer_id')) != customer_id:
            raise ValueError('Message for another order lacks the customer linkage')
    return dispute, charge, order, shipment, comms, history


def render_factual_output(strategy: DisputeStrategy, records: list[dict]):
    dispute, charge, order, shipment, comms, history = _linked_sources(records)

    def money(cents, currency='usd'):
        if type(cents) is not int:
            raise ValueError('Monetary source value must be integer minor units')
        return f'${Decimal(cents) / 100:,.2f}' if currency == 'usd' else f'{cents} minor units ({currency})'

    def address(value):
        if not isinstance(value, dict):
            return value or None
        return ', '.join(str(value[key]) for key in ('line1', 'line2', 'city', 'state', 'postal_code', 'country') if value.get(key)) or None

    def status(value):
        return str(value).replace('_', ' ')

    reason, dispute_id = dispute.get('reason'), dispute['id']
    if not isinstance(reason, str) or not reason:
        raise ValueError('Dispute source is missing its reason')
    amount = money(dispute.get('amount'), dispute.get('currency'))
    action = {'fight': 'submit evidence', 'concede': 'concede the dispute', 'refund_inquiry': 'issue an inquiry refund'}[strategy.action]
    lines = [f'Dispute Reason: {reason}', f'Recommendation: {action} for {dispute_id} ({amount}).']
    order_parts = [f"Order {order['id']}"]
    if order.get('created_at'):
        order_parts.append(f"created {order['created_at']}")
    if order.get('status'):
        order_parts.append(f"recorded status: {status(order['status'])}")
    lines.append('; '.join(order_parts) + '.')
    digital = str(shipment.get('carrier', '')).casefold() == 'digital'
    labels = {'carrier': 'carrier', 'tracking_number': 'access reference' if digital else 'tracking',
              'status': 'recorded status', 'shipped_at': 'access dispatch recorded' if digital else 'shipped',
              'delivered_at': 'access delivery recorded' if digital else 'delivered', 'signed_by': 'signature or delivery notation'}
    parts = [f'{label}: {status(shipment[key]) if key == "status" else shipment[key]}'
             for key, label in labels.items() if shipment.get(key) is not None]
    lines.append(('Digital access record: ' if digital else 'Carrier shipment record: ') + '; '.join(parts) + '.')
    if shipment.get('signed_by') is None:
        lines.append('No signature is recorded in the supplied delivery record.')
    shipping_date = None
    if not digital and shipment.get('shipped_at') is not None:
        try:
            shipping_date = datetime.fromisoformat(shipment['shipped_at'].replace('Z', '+00:00')).date().isoformat()
        except (ValueError, TypeError, AttributeError) as exc:
            raise ValueError('Physical shipment date is invalid; review required') from exc
    checks = charge.get('card_checks') or {}
    names = {'address_line1_check': 'AVS address line 1', 'address_postal_code_check': 'AVS postal code', 'cvc_check': 'CVC'}
    checked = [f'{label}: {checks[key]}' for key, label in names.items() if checks.get(key) is not None]
    if checked:
        lines.append('Recorded card checks: ' + '; '.join(checked) + '.')
    tier = history.get('customer_tier')
    if tier not in ('new', 'repeat', 'vip'):
        raise ValueError('Source customer tier is missing or unsupported')
    customer_facts = [f'customer tier: {tier}']
    if history.get('order_count') is not None:
        customer_facts.append(f"{history['order_count']} total orders")
    if history.get('lifetime_value_cents') is not None:
        customer_facts.append(f"LTV: {money(history['lifetime_value_cents'])}")
    lines.append('Merchant records: ' + '; '.join(customer_facts) + '.')
    policy = history.get('policy') or {}
    if tier in ('repeat', 'vip') and policy.get('vip_concede_max_cents') is not None:
        lines.append(f"Recorded policy parameter: vip_concede_max_cents={money(policy['vip_concede_max_cents'])}. This limit alone does not establish eligibility.")
    if reason == 'product_unacceptable' and policy.get('return_policy'):
        lines.append('Recorded return policy: ' + json.dumps(policy['return_policy'], ensure_ascii=False))
    messages = comms['messages']
    if not messages:
        lines.append('No pre-dispute customer communications exist in merchant records.')
    for message in messages:
        context = []
        if message.get('created_at'):
            context.append(str(message['created_at']))
        if message.get('order_id') and message['order_id'] != order['id']:
            context.append(f"order {message['order_id']}")
        context.append('subject ' + json.dumps(message.get('subject', ''), ensure_ascii=False))
        lines.append(f"Communications record ({'; '.join(context)}) states: {json.dumps(message.get('body', ''), ensure_ascii=False)}")
    narrative = '\n'.join(lines)
    if len(narrative.split()) > 250:
        raise ValueError('Source evidence exceeds the narrative word budget; review required')

    # Current collectors return no policy-exposure events or uploaded artifacts.
    # Those fields stay null; raw model drafts remain separate diagnostics.
    packet = EvidencePacket(
        customer_name=order.get('customer_name'), customer_email_address=order.get('customer_email'),
        billing_address=address(order.get('billing_address')),
        shipping_address=None if digital else address(shipment.get('shipping_address')),
        shipping_carrier=None if digital else shipment.get('carrier'),
        shipping_tracking_number=None if digital else shipment.get('tracking_number'),
        shipping_date=shipping_date, narrative=narrative,
    )
    dispute_status = status(dispute.get('status'))
    rationale = f'Recommend {action}. Recorded dispute status: {dispute_status}; amount: {amount}. ' + '; '.join(customer_facts) + '.'
    summary = f'Recommend {action} for {amount}. Recorded status: {dispute_status}; customer tier: {tier}; {len(messages)} communications record(s).'
    grounded_strategy = DisputeStrategy(**{**strategy.model_dump(), 'customer_value': tier,
                                          'rationale': rationale, 'owner_summary': summary})
    return grounded_strategy, packet
