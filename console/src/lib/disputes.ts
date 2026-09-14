import type { Dispute, Decision, CaseFileMemo, ExhibitItem } from './types';

/** The exported /case page can load any stored ID without per-ID HTML generation. */
export function getCaseHref(disputeId: string): string {
  return `/case?id=${encodeURIComponent(disputeId)}`;
}

export function formatSentenceCase(str: string): string {
  if (!str) return '';
  const clean = str.replace(/_/g, ' ').trim();
  return clean.charAt(0).toUpperCase() + clean.slice(1).toLowerCase();
}

export function getDecision(dispute?: Dispute | null): Decision | null {
  const value = dispute?.decision;
  const decisions = Array.isArray(value) ? value : value ? [value] : [];
  return [...decisions].filter((item) => item.dispute_id === dispute?.id)
    .sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at))[0] || null;
}

export function formatMoney(cents: number, currency = 'usd'): string {
  if (!Number.isFinite(cents)) return 'Amount not recorded';
  try {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: currency.toUpperCase() }).format(cents / 100);
  } catch {
    return `${cents} minor units (${currency})`;
  }
}

/** Static hosting has no Next API server. An opaque response is only a request,
 * never evidence that the owner decision or Stripe action has completed. */
export async function sendOwnerReply(webhookUrl: string, disputeId: string, code: '1' | '2', fetcher: typeof fetch = fetch): Promise<void> {
  const body = new URLSearchParams({ Body: code, From: '+18129551686', dispute_id: disputeId });
  const response = await fetcher(webhookUrl, {
    method: 'POST', mode: 'no-cors',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: body.toString(),
  });
  if (response.type !== 'opaque' && !response.ok) throw new Error('The reply could not be sent.');
}

export function getCaseState(dispute: Dispute) {
  const decision = getDecision(dispute);
  const conceded = dispute.audit_logs?.some((log) => log.dispute_id === dispute.id && log.action === 'concede_dispute'
    && (!decision || Date.parse(log.created_at) >= Date.parse(decision.created_at)));
  if (dispute.status === 'won') return { label: 'WON', variant: 'won', awaitingReply: false };
  if (dispute.status === 'lost') return { label: conceded ? 'CONCEDED · CLOSED' : 'LOST', variant: conceded ? 'conceded' : 'lost', awaitingReply: false };
  if (dispute.status === 'refunded_inquiry') return { label: 'INQUIRY CLOSED', variant: 'inquiry_closed', awaitingReply: false };
  if (dispute.status === 'charge_refunded') return { label: 'CHARGE REFUNDED', variant: 'refunded', awaitingReply: false };
  if (dispute.status === 'under_review') return { label: 'UNDER REVIEW', variant: 'under_review', awaitingReply: false };
  if (decision?.status === 'pending') return { label: 'AWAITING OWNER REPLY', variant: 'pending', awaitingReply: true };
  if (decision?.status === 'approved' || decision?.status === 'overridden') return { label: 'OWNER RESPONSE RECORDED', variant: 'approved', awaitingReply: false };
  if (decision?.status === 'executed') return { label: 'EXECUTION RECORDED', variant: 'approved', awaitingReply: false };
  return { label: 'NEEDS RESPONSE', variant: 'pending', awaitingReply: false };
}

function address(value?: Record<string, unknown>): string {
  if (!value) return 'Not recorded';
  return ['line1', 'line2', 'city', 'state', 'postal_code', 'country']
    .map((key) => value[key]).filter((item) => typeof item === 'string' && item).join(', ') || 'Not recorded';
}

/** Build the case file from its joined stored records; scenario IDs never supply facts. */
export function getCaseFileMemo(dispute: Dispute, now = Date.now()): CaseFileMemo {
  const order = dispute.order?.id === dispute.order_id ? dispute.order : undefined;
  const customer = order?.customer?.id === order?.customer_id ? order?.customer : undefined;
  const decision = getDecision(dispute);
  const exhibits: ExhibitItem[] = [];
  const add = (title: string, field: string, source: string, summary: string,
    fields: Array<{ label: string; value: string }>, missing = false) => {
    exhibits.push({ letter: String.fromCharCode(65 + exhibits.length), title, field, source, summary,
      status: missing ? 'missing' : 'recorded', dossier: { type: 'recorded_evidence', fields } });
  };
  if (order) {
    add('Order and customer record', 'order', order.id, customer?.name || 'Customer name not recorded', [
      { label: 'Order status', value: formatSentenceCase(order.status) },
      { label: 'Order created', value: order.created_at || 'Not recorded' },
      { label: 'Customer', value: customer ? `${customer.name} (${customer.id})` : 'Not recorded' },
      { label: 'Customer tier', value: customer?.customer_value || 'Not recorded' },
      { label: 'Total orders', value: customer?.order_count == null ? 'Not recorded' : String(customer.order_count) },
      { label: 'Lifetime value', value: customer?.lifetime_value_cents == null ? 'Not recorded' : formatMoney(customer.lifetime_value_cents, order.currency) },
      { label: 'Billing address', value: address(order.billing_address) },
      { label: 'Order shipping address', value: address(order.shipping_address) },
      { label: 'Line items', value: order.items?.map((item) => `${item.quantity} × ${item.product_name}`).join('; ') || 'No line items in the supplied order record' },
    ]);
    const shipments = (order.shipments || []).filter((shipment) => !shipment.order_id || shipment.order_id === order.id);
    for (const shipment of shipments) {
      const digital = shipment.carrier?.toLowerCase() === 'digital';
      add(digital ? 'Digital access record' : 'Carrier shipment record', 'shipment', shipment.id,
        `${shipment.carrier} · ${shipment.tracking_number} · ${formatSentenceCase(shipment.status)}`, [
          { label: digital ? 'Access reference' : 'Tracking number', value: shipment.tracking_number },
          { label: 'Recorded status', value: formatSentenceCase(shipment.status) },
          { label: digital ? 'Access dispatch recorded' : 'Shipped', value: shipment.shipped_at || 'Not recorded' },
          { label: digital ? 'Access delivery recorded' : 'Delivered', value: shipment.delivered_at || 'Not recorded' },
          { label: 'Signature or delivery notation', value: shipment.signed_by || 'No signature or delivery notation in the supplied record' },
          ...(digital ? [] : [{ label: 'Shipment destination', value: address(shipment.shipping_address) }]),
          { label: 'Tracking events', value: shipment.events?.map((event) => [event.timestamp, event.status, event.location, event.details].filter(Boolean).join(' · ')).join('\n') || 'No event history in the supplied record' },
        ]);
    }
    if (!shipments.length) add('Shipment record', 'shipment', order.id, 'No shipment record supplied', [], true);
    const messages = (order.messages || []).filter((message) => (!message.order_id || message.order_id === order.id)
      && (!message.customer_id || message.customer_id === order.customer_id));
    add('Customer communications', 'customer_messages', order.id,
      `${messages.length} communications record${messages.length === 1 ? '' : 's'}`, messages.map((message) => ({
        label: [message.id, message.created_at, message.direction || 'Direction not recorded', message.subject].filter(Boolean).join(' · '),
        value: message.body,
      })), !messages.length);
    add('Recorded payment checks', 'payment_checks', order.charge_id || order.payment_intent_id || order.id,
      'Checks stored with the order', [
        { label: 'AVS postal', value: order.avs_postal_match || 'Not recorded' },
        { label: 'CVC', value: order.cvc_match || 'Not recorded' },
        { label: '3D Secure / Radar', value: 'No authentication or risk record supplied' },
      ]);
  } else {
    add('Order evidence', 'order', dispute.order_id || dispute.id, 'No linked order evidence supplied', [], true);
  }
  add('Policy disclosure evidence', 'policy_disclosure', 'Case records', 'No disclosure evidence supplied', [
    { label: 'Customer exposure', value: 'The supplied case records do not show how or when a policy was disclosed to this customer.' },
  ], true);
  if (decision?.rationale || decision?.owner_summary) {
    add('Stored agent assessment', 'decision', decision.id, `Recorded ${decision.created_at}`, [
      { label: 'Rationale', value: decision.rationale || 'No rationale stored' },
      { label: 'Owner summary', value: decision.owner_summary || 'No owner summary stored' },
    ]);
  }
  const due = dispute.evidence_due_by ? Date.parse(dispute.evidence_due_by) : NaN;
  const days = Number.isFinite(due) ? (due < now ? -Math.ceil((now - due) / 86400000) : Math.ceil((due - now) / 86400000)) : null;
  const facts = [`${formatSentenceCase(dispute.reason)} dispute for ${formatMoney(dispute.amount_cents, dispute.currency)}.`,
    `Recorded status: ${formatSentenceCase(dispute.status).toLowerCase()}.`];
  if (order) facts.push(`Order ${order.id}: ${formatSentenceCase(order.status).toLowerCase()}.`);
  if (customer) facts.push(`${customer.name}; recorded customer tier: ${customer.customer_value}; ${customer.order_count} total orders; lifetime value ${formatMoney(customer.lifetime_value_cents, order?.currency)}.`);
  if (!order) facts.push('Linked order evidence is not available in this case file.');
  const action = { fight: 'submit evidence', concede: 'concede the dispute', refund_inquiry: 'refund the inquiry' };
  return {
    customerName: customer?.name || 'Customer not recorded', orderRef: order?.id || dispute.order_id || 'Order not linked',
    headlineAmount: formatMoney(dispute.amount_cents, dispute.currency),
    respondByDate: Number.isFinite(due) ? new Date(due).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC' }) : 'Not recorded',
    respondByDays: days, briefNarrative: facts.join(' '),
    recommendation: decision ? `Recorded recommendation: ${action[decision.action]}.` : 'No agent recommendation recorded.',
    exhibits, smsText: null, smsRecipient: null, smsTime: null,
  };
}
