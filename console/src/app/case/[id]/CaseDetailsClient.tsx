'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import { Dispute, Decision, AuditLogEntry, Order } from '@/lib/types';
import { Header } from '@/components/Header';
import { Stamp } from '@/components/Stamp';
import { TWILIO_WEBHOOK_URL } from '@/lib/config';

interface ExhibitItem {
  letter: string;
  title: string;
  field: string;
  source: string;
  summary: string;
  status: 'attached' | 'missing';
}

function getCaseMemo(dispute: Dispute): {
  customerName: string;
  orderRef: string;
  headlineAmount: string;
  respondByDate: string;
  respondByDays: number;
  briefNarrative: string;
  recommendation: string;
  exhibits: ExhibitItem[];
  smsText: string | null;
  smsRecipient: string | null;
  smsTime: string | null;
} {
  const isFraud = dispute.reason === 'fraudulent' || dispute.id.includes('S2');
  const isPNR = dispute.reason === 'product_not_received' || dispute.id.includes('S1');

  if (isFraud) {
    return {
      customerName: 'Sarah Jenkins',
      orderRef: 'Order #8841',
      headlineAmount: `$${(dispute.amount_cents / 100).toFixed(2)}`,
      respondByDate: '22 Sep 2026',
      respondByDays: 16,
      briefNarrative:
        'Cardholder Sarah Jenkins disputes transaction of $340.00 citing unauthorized fraud. Internal ledger verification demonstrates an established commercial relationship spanning 14 prior completed orders totaling $4,820.00 lifetime spend, all delivered to the identical verified cardholder address with zero historical disputes. Stripe Radar score was 12/100 (low risk) and AVS postal code returned a full match. Rebuttal recommends defending this claim with high confidence, subject to owner authorization to confirm customer relationship preservation.',
      recommendation: 'Recommend: fight (confidence 92%)',
      exhibits: [
        {
          letter: 'A',
          title: 'Prior order ledger and customer history',
          field: 'prior_undisputed_transaction_description',
          source: 'Shopify customer ledger',
          summary: '14 prior orders ($4,820 lifetime spend) delivered to verified address',
          status: 'attached',
        },
        {
          letter: 'B',
          title: 'Proof of delivery and cardholder signature',
          field: 'shipping_documentation',
          source: 'UPS tracking #1Z9999999999999999',
          summary: 'Delivered to 880 Harrison St, San Francisco, CA; signed by cardholder',
          status: 'attached',
        },
        {
          letter: 'C',
          title: 'Stripe Radar risk evaluation',
          field: 'customer_communication',
          source: 'Stripe Radar',
          summary: 'Risk score 12/100, 3D Secure authenticated, CVC & AVS postal match',
          status: 'attached',
        },
        {
          letter: 'D',
          title: 'Merchant checkout terms of service',
          field: 'cancellation_policy',
          source: 'Store checkout policy v2.4',
          summary: 'Accepted by cardholder at checkout with timestamp and IP log',
          status: 'attached',
        },
        {
          letter: 'E',
          title: 'Cardholder signature on file',
          field: 'signature',
          source: 'Stripe charge object',
          summary: 'Missing from Stripe charge object',
          status: 'missing',
        },
      ],
      smsText:
        'Alert: Dispute #8841 ($340.00) flagged for VIP Sarah Jenkins ($4,820 spend). Reply 1 to authorize evidence submission, or 2 to refund.',
      smsRecipient: '+1 ••• 4471',
      smsTime: '14:02',
    };
  }

  if (isPNR) {
    return {
      customerName: 'Michael Okafor',
      orderRef: 'Order #8840',
      headlineAmount: `$${(dispute.amount_cents / 100).toFixed(2)}`,
      respondByDate: '20 Sep 2026',
      respondByDays: 14,
      briefNarrative:
        'Cardholder claims goods were not received. Carrier tracking scan from UPS confirms physical delivery directly to cardholder documented shipping address in Austin, TX, with direct signature confirmation matching claimant name. Counter-evidence packet assembled and submitted to card scheme automatically under merchant rule threshold (< $100).',
      recommendation: 'Recommend: fight (confidence 98%)',
      exhibits: [
        {
          letter: 'A',
          title: 'Carrier proof of delivery and signature',
          field: 'shipping_documentation',
          source: 'UPS tracking #1Z88400019283746',
          summary: 'Physical delivery confirmed to 1424 Elm St with recipient signature',
          status: 'attached',
        },
        {
          letter: 'B',
          title: 'Order fulfillment and dispatch record',
          field: 'receipt',
          source: 'Shopify fulfillment service',
          summary: 'Order ORD-1001 fulfilled within 24 hours of checkout',
          status: 'attached',
        },
        {
          letter: 'C',
          title: 'Customer delivery notification log',
          field: 'customer_communication',
          source: 'Gmail support thread',
          summary: 'Delivery notice emailed to m.okafor@example.com with carrier tracking link',
          status: 'attached',
        },
        {
          letter: 'D',
          title: 'Cardholder non-receipt declaration',
          field: 'customer_communication',
          source: 'Stripe charge object',
          summary: 'Missing from Stripe charge object',
          status: 'missing',
        },
      ],
      smsText: null,
      smsRecipient: null,
      smsTime: null,
    };
  }

  return {
    customerName: 'David Miller',
    orderRef: 'Order #8842',
    headlineAmount: `$${(dispute.amount_cents / 100).toFixed(2)}`,
    respondByDate: '25 Sep 2026',
    respondByDays: 19,
    briefNarrative:
      'Cardholder disputes recurring billing charge claiming account was canceled prior to renewal. Support inbox records indicate formal cancellation request was received 48 hours prior to billing cycle renewal. Contesting this claim would violate card brand rules and incur a statutory $15.00 arbitration fee with negligible win probability.',
    recommendation: 'Recommend: concede (confidence 96%)',
    exhibits: [
      {
        letter: 'A',
        title: 'Inbound cancellation notice',
        field: 'customer_communication',
        source: 'Zendesk ticket #48102',
        summary: 'Customer requested cancellation on Aug 22 prior to Aug 24 renewal',
        status: 'attached',
      },
      {
        letter: 'B',
        title: 'Merchant subscription terms',
        field: 'cancellation_policy',
        source: 'Merchant TOS § 4.2',
        summary: 'Terms permit cancellation up to 24 hours prior to billing date',
        status: 'attached',
      },
      {
        letter: 'C',
        title: 'Billing timeline audit',
        field: 'refund_policy',
        source: 'Stripe billing schedule',
        summary: 'Inadvertent renewal processed following valid cancellation window',
        status: 'attached',
      },
    ],
    smsText: null,
    smsRecipient: null,
    smsTime: null,
  };
}

export default function CaseDetailsPage() {
  const params = useParams();
  const disputeId = params?.id as string;

  const [dispute, setDispute] = useState<Dispute | null>(null);
  const [decision, setDecision] = useState<Decision | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [replyingId, setReplyingId] = useState<string | null>(null);
  const [localDecision, setLocalDecision] = useState<{
    action: 'approved' | 'conceded';
    timestamp: string;
  } | null>(null);

  const fetchCaseDetails = useCallback(async () => {
    if (!disputeId) return;

    try {
      const { data: dData } = await supabase
        .from('disputes')
        .select('*')
        .eq('id', disputeId)
        .single();

      if (dData) {
        setDispute(dData as Dispute);

        const { data: decData } = await supabase
          .from('decisions')
          .select('*')
          .eq('dispute_id', disputeId)
          .maybeSingle();

        if (decData) setDecision(decData as Decision);

        const { data: logsData } = await supabase
          .from('audit_log')
          .select('*')
          .eq('dispute_id', disputeId)
          .order('created_at', { ascending: false });

        if (logsData) setAuditLogs(logsData as AuditLogEntry[]);

        if (dData.order_id) {
          const { data: oData } = await supabase
            .from('orders')
            .select(`
              *,
              customer:customers(*),
              items:order_items(*),
              shipments:shipments(*, events:shipment_events(*)),
              messages:customer_messages(*)
            `)
            .eq('id', dData.order_id)
            .maybeSingle();

          if (oData) setOrder(oData as Order);
        }
      }
    } catch (err) {
      console.error('Failed to load case details:', err);
    } finally {
      setLoading(false);
    }
  }, [disputeId]);

  useEffect(() => {
    fetchCaseDetails();
  }, [fetchCaseDetails]);

  const handleQuickReply = async (code: '1' | '2') => {
    if (!dispute) return;
    setReplyingId(dispute.id);

    const now = new Date();
    const day = now.getUTCDate().toString().padStart(2, '0');
    const month = now.toLocaleString('en-US', { month: 'short', timeZone: 'UTC' }).toUpperCase();
    const hours = now.getUTCHours().toString().padStart(2, '0');
    const mins = now.getUTCMinutes().toString().padStart(2, '0');
    const timeStr = `${day} ${month} ${hours}:${mins}`;

    setLocalDecision({
      action: code === '1' ? 'approved' : 'conceded',
      timestamp: timeStr,
    });

    try {
      const formData = new URLSearchParams();
      formData.append('Body', code);
      formData.append('From', '+18129551686');
      formData.append('dispute_id', dispute.id);

      await fetch(TWILIO_WEBHOOK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData.toString(),
        mode: 'no-cors',
      });

      setTimeout(() => fetchCaseDetails(), 1200);
    } catch (err) {
      console.error('Failed to send SMS reply:', err);
    } finally {
      setReplyingId(null);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Header />
        <div className="bg-sheet border-t-2 border-rule-strong p-6 sm:p-8 space-y-4">
          <div className="h-4 bg-rule/50 w-32" />
          <div className="h-10 bg-rule/50 w-48" />
          <div className="h-5 bg-rule/50 w-64" />
          <div className="h-24 bg-rule/40 w-full" />
        </div>
      </div>
    );
  }

  if (!dispute) {
    return (
      <div className="space-y-6">
        <Header />
        <div className="bg-sheet border-t-2 border-rule-strong p-8">
          <h1 className="text-xl font-sans text-ink tracking-tight font-normal mb-2">
            Case file not found
          </h1>
          <p className="text-xs font-mono text-secondary-ink mb-4">
            Dispute &ldquo;{disputeId}&rdquo; was not located in the docket database.
          </p>
          <Link href="/" className="underline text-ink font-mono text-xs hover:text-ink">
            Return to docket
          </Link>
        </div>
      </div>
    );
  }

  const memo = getCaseMemo(dispute);
  const isAwaitingReply =
    !localDecision &&
    (dispute.reason === 'fraudulent' || dispute.id.includes('S2')) &&
    (dispute.status === 'needs_response' ||
      dispute.status === 'under_review' ||
      (decision && decision.status === 'pending'));

  const hasRecordedOutcome =
    localDecision ||
    dispute.status === 'won' ||
    dispute.status === 'lost' ||
    dispute.status === 'charge_refunded' ||
    (decision &&
      (decision.status === 'approved' ||
        decision.status === 'executed' ||
        decision.action === 'fight' ||
        decision.action === 'concede')) ||
    (!isAwaitingReply && (dispute.reason === 'product_not_received' || dispute.reason === 'subscription_canceled'));

  return (
    <div className="space-y-6">
      <Header />

      {/* Nav breadcrumb */}
      <div className="mb-2">
        <Link href="/" className="underline text-ink font-mono text-xs hover:text-ink">
          ← Return to docket
        </Link>
      </div>

      {/* OPEN CASE FILE SHEET */}
      <article className="bg-sheet border-t-2 border-rule-strong p-6 sm:p-8 space-y-6">
        {/* Case Header */}
        <div className="border-b border-rule pb-5">
          <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2 text-xs font-mono text-secondary-ink mb-2">
            <div>
              <span>{dispute.reason}</span>
              <span className="mx-2">·</span>
              <span>{order?.customer?.name || memo.customerName}</span>
              <span className="mx-2">·</span>
              <span>{order?.id || memo.orderRef}</span>
              <span className="mx-2">·</span>
              <span className="text-ink font-semibold">{dispute.id}</span>
            </div>
            <div>Stripe chargeback dossier</div>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-4 mt-1">
            {/* Amount: mono, 43px */}
            <div className="text-2xl font-mono tabular-nums text-ink font-bold tracking-tight">
              {memo.headlineAmount}
            </div>

            {/* Respond by: second-heaviest element */}
            <div className="text-base sm:text-lg font-sans font-medium text-ink tracking-tight">
              Respond by {memo.respondByDate} ({memo.respondByDays} days left)
            </div>
          </div>
        </div>

        {/* Section 1: Paralegal Memo Brief */}
        <div className="border-b border-rule pb-5">
          <div className="text-xs font-mono text-secondary-ink mb-2">
            Paralegal brief
          </div>
          <div className="max-w-[75ch] text-sm text-ink leading-[1.55] font-sans">
            <p className="mb-3">{memo.briefNarrative}</p>
            <p className="font-mono text-xs font-medium text-ink">
              {memo.recommendation}
            </p>
            {decision && (
              <p className="font-mono text-xs text-secondary-ink mt-2">
                Win probability: {Math.round(decision.win_probability * 100)}% · Expected value: ${(decision.expected_value_cents / 100).toFixed(2)} · Evidence strength: {decision.evidence_strength}
              </p>
            )}
          </div>
        </div>

        {/* Section 2: Evidentiary Exhibits */}
        <div className="border-b border-rule pb-5">
          <div className="text-xs font-mono text-secondary-ink mb-3">
            Evidentiary exhibits
          </div>
          <div className="divide-y divide-rule border-t border-b border-rule font-sans">
            {memo.exhibits.map((ex) => (
              <div
                key={ex.letter}
                className="py-2.5 flex flex-col sm:flex-row sm:items-baseline justify-between gap-2 text-xs"
              >
                <div className="flex-1 max-w-[65ch]">
                  <span className="font-medium text-ink mr-2">
                    Exhibit {ex.letter}: {ex.title}
                  </span>
                  <span className="font-mono text-secondary-ink mr-2">
                    [{ex.field}]
                  </span>
                  <span className="text-secondary-ink">
                    — {ex.source}: {ex.summary}
                  </span>
                </div>
                <div className="font-mono text-right shrink-0">
                  {ex.status === 'attached' ? (
                    <span className="text-secondary-ink">attached</span>
                  ) : (
                    <span className="text-decision-red font-medium">missing</span>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Fulfillment details if order exists */}
          {order && (
            <div className="mt-4 pt-4 border-t border-rule font-mono text-xs">
              <div className="text-secondary-ink mb-2">Fulfillment verification:</div>
              <div className="text-ink space-y-1">
                <div>Customer: {order.customer?.name} ({order.customer?.email})</div>
                {order.shipments && order.shipments[0] && (
                  <div>
                    Shipment: {order.shipments[0].carrier} #{order.shipments[0].tracking_number} · Status: {order.shipments[0].status}
                    {order.shipments[0].signed_by && ` · Signed by: ${order.shipments[0].signed_by}`}
                  </div>
                )}
                {order.items && order.items.length > 0 && (
                  <div>
                    Line items: {order.items.map((it) => `${it.quantity}x ${it.product_name}`).join(', ')}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Section 3: Decision Record */}
        <div className="border-b border-rule pb-5">
          <div className="text-xs font-mono text-secondary-ink mb-3">
            Decision record
          </div>

          {isAwaitingReply ? (
            <div className="space-y-3">
              <div className="bg-highlighter px-2 py-1 inline-block text-ink font-mono text-xs font-medium">
                Awaiting your reply by SMS · sent {memo.smsTime || '14:02'} to {memo.smsRecipient || '+1 ••• 4471'}
              </div>

              <div className="text-xs text-secondary-ink font-sans max-w-[75ch]">
                Texted message: &ldquo;{memo.smsText}&rdquo;
              </div>

              <div className="flex items-center gap-3 pt-1">
                <button
                  type="button"
                  onClick={() => handleQuickReply('1')}
                  disabled={replyingId === dispute.id}
                  className="border border-ink px-3 py-1.5 text-xs font-mono text-ink bg-transparent hover:bg-ink hover:text-sheet transition-colors disabled:opacity-50"
                >
                  Reply &quot;1&quot; to fight
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickReply('2')}
                  disabled={replyingId === dispute.id}
                  className="border border-rule px-3 py-1.5 text-xs font-mono text-secondary-ink bg-transparent hover:border-ink hover:text-ink transition-colors disabled:opacity-50"
                >
                  Reply &quot;2&quot; to concede
                </button>
              </div>
            </div>
          ) : null}

          {!isAwaitingReply && hasRecordedOutcome ? (
            <div className="space-y-1">
              <div className="text-xs font-sans text-secondary-ink">
                Decision executed:
              </div>
              {localDecision ? (
                localDecision.action === 'approved' ? (
                  <Stamp
                    text={`APPROVED · ${localDecision.timestamp} · BY OWNER (SMS)`}
                    variant="approved"
                    animate={true}
                  />
                ) : (
                  <Stamp
                    text={`CONCEDED · ${localDecision.timestamp} · BY OWNER (SMS)`}
                    variant="conceded"
                    animate={true}
                  />
                )
              ) : dispute.status === 'won' ? (
                <Stamp text="FOUGHT · 06 SEP 14:07 · BY AGENT" variant="won" />
              ) : dispute.status === 'lost' ? (
                <Stamp text="LOST · 06 SEP 14:07 · ISSUER DECISION" variant="lost" />
              ) : dispute.status === 'charge_refunded' ? (
                <Stamp text="CONCEDED · 06 SEP 14:08 · BY AGENT" variant="conceded" />
              ) : decision?.action === 'fight' || dispute.status === 'under_review' ? (
                <Stamp text="FOUGHT · 06 SEP 14:07 · BY AGENT" variant="won" />
              ) : decision?.action === 'concede' ? (
                <Stamp text="CONCEDED · 06 SEP 14:08 · BY AGENT" variant="conceded" />
              ) : dispute.reason === 'product_not_received' ? (
                <Stamp text="FOUGHT · 06 SEP 14:07 · BY AGENT" variant="won" />
              ) : dispute.reason === 'subscription_canceled' ? (
                <Stamp text="CONCEDED · 06 SEP 14:08 · BY AGENT" variant="conceded" />
              ) : (
                <Stamp text="FOUGHT · 06 SEP 14:07 · BY AGENT" variant="won" />
              )}
            </div>
          ) : null}
        </div>

        {/* Section 4: Chronological Audit Trail */}
        <div>
          <div className="text-xs font-mono text-secondary-ink mb-3">
            Chronological audit log
          </div>
          {auditLogs.length === 0 ? (
            <p className="text-xs font-mono text-secondary-ink">
              No audit entries recorded.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-left text-xs">
                <thead>
                  <tr className="border-b border-rule text-secondary-ink font-mono text-xs">
                    <th className="py-2 px-3 font-normal">Timestamp</th>
                    <th className="py-2 px-3 font-normal">Actor</th>
                    <th className="py-2 px-3 font-normal">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-rule font-sans">
                  {auditLogs.map((log) => {
                    const d = new Date(log.created_at);
                    const day = d.getUTCDate().toString().padStart(2, '0');
                    const month = d.toLocaleString('en-US', { month: 'short', timeZone: 'UTC' });
                    const time = `${d.getUTCHours().toString().padStart(2, '0')}:${d.getUTCMinutes().toString().padStart(2, '0')}`;
                    const timeStr = `${day} ${month} ${time}`;

                    return (
                      <tr key={log.id} className="h-9 hover:bg-sheet/60">
                        <td className="py-2 px-3 align-middle font-mono text-secondary-ink">
                          {timeStr}
                        </td>
                        <td className="py-2 px-3 align-middle font-mono text-ink">
                          {log.actor}
                        </td>
                        <td className="py-2 px-3 align-middle text-ink">
                          {log.action.replace(/_/g, ' ')}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </article>
    </div>
  );
}

