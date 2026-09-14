'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import { Dispute, Decision, AuditLogEntry, Order } from '@/lib/types';
import { Header } from '@/components/Header';
import { Stamp } from '@/components/Stamp';
import { ExhibitInspector } from '@/components/ExhibitInspector';
import { getCaseFileMemo, getCaseState, sendOwnerReply } from '@/lib/disputes';
import { TWILIO_WEBHOOK_URL } from '@/lib/config';

export default function CaseDetailsPage({ disputeId: suppliedDisputeId }: { disputeId?: string } = {}) {
  const params = useParams();
  const disputeId = suppliedDisputeId ?? params?.id as string;

  const [dispute, setDispute] = useState<Dispute | null>(null);
  const [decision, setDecision] = useState<Decision | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [replyingId, setReplyingId] = useState<string | null>(null);
  const [replyMessage, setReplyMessage] = useState<string | null>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const fetchCaseDetails = useCallback(async () => {
    if (!disputeId) return;

    try {
      const { data: dData, error: disputeError } = await supabase
        .from('disputes')
        .select('*')
        .eq('id', disputeId)
        .single();
      if (disputeError) throw disputeError;

      if (dData) {
        setDispute(dData as Dispute);

        const { data: decData, error: decisionError } = await supabase
          .from('decisions')
          .select('*')
          .eq('dispute_id', disputeId)
          .order('created_at', { ascending: false })
          .limit(1)
          .maybeSingle();
        if (decisionError) throw decisionError;

        setDecision(decData as Decision | null);

        const { data: logsData, error: logsError } = await supabase
          .from('audit_log')
          .select('*')
          .eq('dispute_id', disputeId)
          .order('created_at', { ascending: false });
        if (logsError) throw logsError;

        setAuditLogs((logsData || []) as AuditLogEntry[]);

        if (dData.order_id) {
          const { data: oData, error: orderError } = await supabase
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
          if (orderError) throw orderError;

          setOrder(oData as Order | null);
        } else {
          setOrder(null);
        }
      } else {
        setDispute(null);
        setDecision(null);
        setOrder(null);
        setAuditLogs([]);
      }
      setFetchError(null);
    } catch (err) {
      console.error('Failed to load case details:', err);
      setFetchError('Case synchronization failed. Displayed records may be out of date.');
    } finally {
      setLoading(false);
    }
  }, [disputeId]);

  useEffect(() => {
    fetchCaseDetails();
    const timer = setInterval(fetchCaseDetails, 5000);
    return () => clearInterval(timer);
  }, [fetchCaseDetails]);

  const handleQuickReply = async (code: '1' | '2') => {
    if (!dispute) return;
    setReplyingId(dispute.id);
    try {
      await sendOwnerReply(TWILIO_WEBHOOK_URL, dispute.id, code);
      setReplyMessage('Reply requested. Waiting for the recorded backend outcome.');
      await fetchCaseDetails();
    } catch (err) {
      setReplyMessage(err instanceof Error ? err.message : 'The reply could not be sent.');
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
            {fetchError ? 'Case file unavailable' : 'Case file not found'}
          </h1>
          <p className="text-xs font-mono text-secondary-ink mb-4">
            {fetchError || `Dispute ${disputeId} was not located in the docket database.`}
          </p>
          <Link href="/" className="underline text-ink font-mono text-xs hover:text-ink">
            Return to docket
          </Link>
        </div>
      </div>
    );
  }

  const caseRecord = { ...dispute, decision, order: order || undefined, audit_logs: auditLogs };
  const memo = getCaseFileMemo(caseRecord);
  const caseState = getCaseState(caseRecord);
  const isAwaitingReply = caseState.awaitingReply;

  return (
    <div className="space-y-6">
      <Header />
      {fetchError && <p className="text-xs font-mono text-decision-red" role="alert">{fetchError}</p>}

      {/* Nav breadcrumb */}
      <div className="mb-2">
        <Link href="/" className="underline text-ink font-mono text-xs hover:text-ink">
          Return to docket
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
              <span>{memo.customerName}</span>
              <span className="mx-2">·</span>
              <span>{memo.orderRef}</span>
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
              {memo.respondByDays === null ? 'Response deadline not recorded' : `Respond by ${memo.respondByDate}${memo.respondByDays < 0 ? ' (deadline passed)' : ` (${memo.respondByDays} days left)`}`}
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
                Agent estimate — win probability: {Math.round(decision.win_probability * 100)}% · Expected value: ${(decision.expected_value_cents / 100).toFixed(2)} · Evidence strength: {decision.evidence_strength}
              </p>
            )}
          </div>
        </div>

        {/* Section 2: Evidentiary Exhibits */}
        <div className="border-b border-rule pb-5">
          <div className="text-xs font-mono text-secondary-ink mb-3">
            Evidentiary exhibits
          </div>
          <ExhibitInspector exhibits={memo.exhibits} />

          {/* Fulfillment details if order exists */}
          {order && (
            <div className="mt-4 pt-4 border-t border-rule font-mono text-xs">
              <div className="text-secondary-ink mb-2">Stored fulfillment records:</div>
              <div className="text-ink space-y-1">
                <div>Customer: {order.customer?.name} ({order.customer?.email})</div>
                {order.shipments && order.shipments[0] && (
                  <div>
                    Shipment: {order.shipments[0].carrier} #{order.shipments[0].tracking_number} · Status: {order.shipments[0].status}
                    {order.shipments[0].signed_by && ` · Signature or delivery notation: ${order.shipments[0].signed_by}`}
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
                Awaiting owner reply
              </div>

              <div className="text-xs text-secondary-ink font-sans max-w-[75ch]">
                A pending approval decision is recorded. Use the owner notification to respond; delivery details are not stored in this case file.
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
                  {decision?.action === 'refund_inquiry'
                    ? 'Reply "2" to refund'
                    : 'Reply "2" to concede'}
                </button>
              </div>
            </div>
          ) : null}

          {replyMessage && <p className="text-xs font-mono text-secondary-ink mt-3">{replyMessage}</p>}
          {!isAwaitingReply && (
            <div className="space-y-1">
              <div className="text-xs font-sans text-secondary-ink">Recorded state:</div>
              <Stamp text={caseState.label} variant={caseState.variant} />
            </div>
          )}
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
                    <th scope="col" className="py-2 px-3 font-normal">Timestamp</th>
                    <th scope="col" className="py-2 px-3 font-normal">Actor</th>
                    <th scope="col" className="py-2 px-3 font-normal">Action</th>
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
