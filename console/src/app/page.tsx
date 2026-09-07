'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { supabase } from '@/lib/supabase';
import { Dispute } from '@/lib/types';
import { Header } from '@/components/Header';
import { CaseFeed } from '@/components/CaseFeed';
import { Stamp } from '@/components/Stamp';
import { TWILIO_WEBHOOK_URL, INJECT_URL, CONSOLE_KEY } from '@/lib/config';

interface ExhibitItem {
  letter: string;
  title: string;
  field: string;
  source: string;
  summary: string;
  status: 'attached' | 'missing';
}

interface CaseFileMemo {
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
}

function getCaseFileMemo(dispute: Dispute): CaseFileMemo {
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

  // Subscription canceled or inquiry scenario (S3)
  return {
    customerName: 'Roberto Alvarez',
    orderRef: 'Order #ORD-1003',
    headlineAmount: `$${(dispute.amount_cents / 100).toFixed(2)}`,
    respondByDate: '25 Sep 2026',
    respondByDays: 19,
    briefNarrative:
      'Pre-chargeback inquiry for $129.00 coffee subscription renewal. Support inbox shows customer Roberto Alvarez submitted cancellation request prior to billing cycle renewal. Contesting this claim violates card brand rules and risks a statutory $15.00 chargeback loss fee. Rebuttal recommends issuing an immediate inquiry refund to close the case with $15 fee avoided.',
    recommendation: 'Recommend: refund inquiry ($15 fee avoided)',
    exhibits: [
      {
        letter: 'A',
        title: 'Customer cancellation request',
        field: 'customer_communication',
        source: 'Email inbox MSG-005',
        summary: 'Customer requested cancellation prior to renewal charge',
        status: 'attached',
      },
      {
        letter: 'B',
        title: 'Merchant subscription terms',
        field: 'cancellation_policy',
        source: 'Merchant TOS § 4.2',
        summary: 'Terms permit cancellation prior to recurring billing date',
        status: 'attached',
      },
      {
        letter: 'C',
        title: 'Pre-chargeback inquiry disclosure',
        field: 'uncategorized_text',
        source: 'Stripe warning_needs_response',
        summary: 'Card scheme inquiry; full refund resolves claim with zero chargeback fee',
        status: 'attached',
      },
    ],
    smsText:
      'Pre-chargeback inquiry: Roberto Alvarez ($129.00). Customer emailed to cancel before renewal. Reply 1 Fight, 2 Refund ($15 fee avoided), 3 Hold.',
    smsRecipient: '+1 ••• 4471',
    smsTime: '14:04',
  };
}

export default function HomePage() {
  const [disputes, setDisputes] = useState<Dispute[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedDisputeId, setSelectedDisputeId] = useState<string | null>(null);
  const [activeScenario, setActiveScenario] = useState<'S1' | 'S2' | 'S3' | null>('S2');
  const [loadingScenario, setLoadingScenario] = useState<string | null>(null);
  const [forcedState, setForcedState] = useState<'empty' | 'loading' | 'error' | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cooldown, setCooldown] = useState<number>(0);
  const [replyingId, setReplyingId] = useState<string | null>(null);
  const [localDecisions, setLocalDecisions] = useState<Record<string, {
    action: 'approved' | 'conceded';
    timestamp: string;
    actor: 'SMS' | 'AGENT';
  }>>({});
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const s = params.get('state');
      if (s === 'empty' || s === 'loading' || s === 'error') {
        setForcedState(s);
      }
    }
  }, []);

  const fetchDisputes = useCallback(async () => {
    try {
      const { data, error: sbError } = await supabase
        .from('disputes')
        .select(`
          *,
          decision:decisions(*)
        `)
        .order('created_at', { ascending: false });

      if (sbError) throw sbError;
      setDisputes((data as Dispute[]) || []);
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch disputes:', err);
      setError(err?.message || 'Stripe API communication timeout (ECONNRESET).');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDisputes();
  }, [fetchDisputes]);

  // Polling every 5s
  useEffect(() => {
    const timer = setInterval(() => {
      fetchDisputes();
    }, 5000);
    return () => clearInterval(timer);
  }, [fetchDisputes]);

  // Cooldown timer
  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setInterval(() => {
      setCooldown((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(timer);
  }, [cooldown]);

  const handleSelectScenario = async (scenario: 'S1' | 'S2' | 'S3') => {
    if (cooldown > 0 || loadingScenario) return;
    setLoadingScenario(scenario);
    setActiveScenario(scenario);

    try {
      const resp = await fetch(INJECT_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Console-Key': CONSOLE_KEY,
        },
        body: JSON.stringify({ scenario }),
      });

      const data = await resp.json().catch(() => ({}));
      if (resp.ok) {
        setCooldown(10);
        setToastMessage(`Scenario ${scenario} injected.`);
        setTimeout(() => setToastMessage(null), 4000);
        await fetchDisputes();
        if (data.dispute_id) {
          setSelectedDisputeId(data.dispute_id);
        }
      }
    } catch (err: any) {
      console.error('Injection failed:', err);
    } finally {
      setLoadingScenario(null);
    }
  };

  const handleQuickReply = async (disputeId: string, replyCode: '1' | '2') => {
    setReplyingId(disputeId);
    const now = new Date();
    const day = now.getUTCDate().toString().padStart(2, '0');
    const month = now.toLocaleString('en-US', { month: 'short', timeZone: 'UTC' }).toUpperCase();
    const hours = now.getUTCHours().toString().padStart(2, '0');
    const mins = now.getUTCMinutes().toString().padStart(2, '0');
    const timeStr = `${day} ${month} ${hours}:${mins}`;

    // Optimistically update local decision state for instant gate stamp landing
    setLocalDecisions((prev) => ({
      ...prev,
      [disputeId]: {
        action: replyCode === '1' ? 'approved' : 'conceded',
        timestamp: timeStr,
        actor: 'SMS',
      },
    }));

    try {
      const formData = new URLSearchParams();
      formData.append('Body', replyCode);
      formData.append('From', '+18129551686');
      formData.append('dispute_id', disputeId);

      await fetch(TWILIO_WEBHOOK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData.toString(),
        mode: 'no-cors',
      });

      setTimeout(() => fetchDisputes(), 1200);
    } catch (err: any) {
      console.error('Quick reply error:', err);
    } finally {
      setReplyingId(null);
    }
  };

  // Helper to normalize decision from array or object
  const getDecision = (d?: Dispute | null) => {
    if (!d || !d.decision) return null;
    if (Array.isArray(d.decision)) return d.decision[0] || null;
    return d.decision;
  };

  // Determine currently open dispute based on selection or active scenario
  const openDispute = (() => {
    if (selectedDisputeId) {
      const found = disputes.find((d) => d.id === selectedDisputeId);
      if (found) return found;
    }
    if (activeScenario === 'S1') {
      const found = disputes.find((d) => d.id === 'dp_S1' || d.metadata?.scenario === 'S1' || d.reason === 'product_not_received');
      if (found) return found;
    }
    if (activeScenario === 'S2') {
      const found = disputes.find((d) => d.id === 'dp_S2' || d.metadata?.scenario === 'S2' || d.reason === 'fraudulent');
      if (found) return found;
    }
    if (activeScenario === 'S3') {
      const found = disputes.find((d) => d.id === 'dp_S3' || d.metadata?.scenario === 'S3' || d.reason === 'subscription_canceled');
      if (found) return found;
    }
    return (
      disputes.find(
        (d) =>
          d.status === 'needs_response' ||
          (getDecision(d) && getDecision(d)?.status === 'pending')
      ) ||
      disputes[0] ||
      null
    );
  })();

  // Resolved disputes statistics for quiet state
  const resolvedCount = disputes.filter((d) =>
    ['won', 'lost', 'charge_refunded'].includes(d.status)
  ).length;
  const foughtCount = disputes.filter((d) => d.status === 'won').length;
  const concededCount = disputes.filter((d) => d.status === 'charge_refunded').length;

  if (loading || forcedState === 'loading') {
    return (
      <div className="space-y-6">
        <Header activeScenario={activeScenario} />
        {/* Loading: skeleton rows in the roster, never spinners */}
        <div className="bg-sheet border-t-2 border-rule-strong p-6 sm:p-8 space-y-4">
          <div className="h-4 bg-rule/50 w-32" />
          <div className="h-10 bg-rule/50 w-48" />
          <div className="h-5 bg-rule/50 w-64" />
          <div className="h-16 bg-rule/30 w-full" />
        </div>
        <div className="mt-8 pt-4 border-t border-rule">
          <div className="text-xs font-mono text-secondary-ink mb-3">All disputes · Loading docket</div>
          <div className="border-t border-rule divide-y divide-rule">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="h-[40px] flex items-center justify-between px-2">
                <div className="h-3.5 bg-rule/40 w-28" />
                <div className="h-3.5 bg-rule/40 w-16" />
                <div className="h-3.5 bg-rule/40 w-36" />
                <div className="h-3.5 bg-rule/40 w-24" />
                <div className="h-3.5 bg-rule/40 w-20" />
                <div className="h-3.5 bg-rule/40 w-20" />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Quiet State: when nothing is gated
  const isQuietState = forcedState === 'empty' || !openDispute;

  if (isQuietState) {
    return (
      <div className="space-y-6">
        <Header
          activeScenario={activeScenario}
          onSelectScenario={handleSelectScenario}
          loadingScenario={loadingScenario}
          cooldown={cooldown}
        />
        <div className="py-12">
          <h1 className="text-xl font-sans text-ink tracking-tight font-normal mb-2">
            Nothing needs you.
          </h1>
          <p className="text-sm text-secondary-ink font-sans">
            {resolvedCount > 0 && forcedState !== 'empty'
              ? `${resolvedCount} disputes handled since Sep 1 — ${foughtCount} fought, ${concededCount} conceded.`
              : '12 disputes handled since Sep 1 — 9 fought, 3 conceded.'}
          </p>
        </div>
        <CaseFeed
          disputes={disputes}
          openDisputeId={null}
          onSelectDispute={(id) => setSelectedDisputeId(id)}
        />
      </div>
    );
  }

  const memo = getCaseFileMemo(openDispute);
  const localDecision = localDecisions[openDispute.id];
  const disputeDecision = getDecision(openDispute);

  // Determine gate state: is this dispute awaiting SMS reply?
  const isAwaitingReply =
    !localDecision &&
    openDispute.status !== 'won' &&
    openDispute.status !== 'lost' &&
    openDispute.status !== 'refunded_inquiry' &&
    openDispute.status !== 'charge_refunded' &&
    ((openDispute.reason === 'fraudulent' || openDispute.id.includes('S2')) &&
      (openDispute.status === 'needs_response' ||
        openDispute.status === 'under_review' ||
        (disputeDecision && disputeDecision.status === 'pending')) ||
      ((openDispute.reason === 'subscription_canceled' || openDispute.id.includes('S3') || openDispute.status === 'warning_needs_response') &&
        (disputeDecision?.status === 'pending' || openDispute.status === 'warning_needs_response')));

  // Has a decision been recorded?
  const hasRecordedOutcome =
    localDecision ||
    openDispute.status === 'won' ||
    openDispute.status === 'lost' ||
    openDispute.status === 'refunded_inquiry' ||
    openDispute.status === 'charge_refunded' ||
    (disputeDecision &&
      (disputeDecision.status === 'approved' ||
        disputeDecision.status === 'executed' ||
        disputeDecision.action === 'fight' ||
        disputeDecision.action === 'concede' ||
        disputeDecision.action === 'refund_inquiry')) ||
    (!isAwaitingReply && (openDispute.reason === 'product_not_received' || openDispute.reason === 'subscription_canceled'));

  return (
    <div className="space-y-6">
      <Header
        activeScenario={activeScenario}
        onSelectScenario={handleSelectScenario}
        loadingScenario={loadingScenario}
        cooldown={cooldown}
      />

      {/* Error State: 1px rule #B91C1C above error line, secondary ink, retry as ink link */}
      {(error || forcedState === 'error') && (
        <div className="border-t border-decision-red pt-3 pb-2 flex flex-col sm:flex-row sm:items-baseline justify-between gap-2 text-xs font-mono">
          <span className="text-secondary-ink">
            Failed to synchronize dispute docket: {error || 'Stripe API communication timeout (ECONNRESET).'}
          </span>
          <button
            type="button"
            onClick={() => {
              setError(null);
              setForcedState(null);
              fetchDisputes();
            }}
            className="underline text-ink hover:text-ink cursor-pointer shrink-0"
          >
            Retry
          </button>
        </div>
      )}

      {toastMessage && (
        <div className="border border-rule p-2.5 text-xs font-mono text-ink bg-sheet">
          {toastMessage}
        </div>
      )}

      {/* OPEN FILE: ~65% of the viewport */}
      <section className="bg-sheet border-t-2 border-rule-strong p-6 sm:p-8">
        {/* Case Header */}
        <div className="border-b border-rule pb-5 mb-5">
          <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2 text-xs font-mono text-secondary-ink mb-2">
            <div>
              <span>{openDispute.reason}</span>
              <span className="mx-2">·</span>
              <span>{memo.customerName}</span>
              <span className="mx-2">·</span>
              <span>{memo.orderRef}</span>
              <span className="mx-2">·</span>
              <Link
                href={`/case/${openDispute.id}`}
                className="underline text-ink hover:text-ink font-mono"
              >
                {openDispute.id}
              </Link>
            </div>
            <div className="text-secondary-ink font-mono text-xs">
              Stripe chargeback file
            </div>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-4 mt-1">
            {/* Amount as the headline: mono, 43px */}
            <div className="text-2xl font-mono tabular-nums text-ink font-bold tracking-tight">
              {memo.headlineAmount}
            </div>

            {/* Respond by <date> (<n> days): second-heaviest element */}
            <div className="text-base sm:text-lg font-sans font-medium text-ink tracking-tight">
              Respond by {memo.respondByDate} ({memo.respondByDays} days left)
            </div>
          </div>
        </div>

        {/* The Brief: written as a paralegal's memo */}
        <div className="border-b border-rule pb-5 mb-5">
          <div className="text-xs font-mono text-secondary-ink mb-2">
            Paralegal memo
          </div>
          <div className="max-w-[75ch] text-sm text-ink leading-[1.55] font-sans">
            <p className="mb-3">{memo.briefNarrative}</p>
            <p className="font-mono text-xs font-medium text-ink">
              {memo.recommendation}
            </p>
          </div>
        </div>

        {/* Exhibits: lettered A, B, C... */}
        <div className="border-b border-rule pb-5 mb-5">
          <div className="text-xs font-mono text-secondary-ink mb-3">
            Exhibits
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
        </div>

        {/* Decision Block */}
        <div>
          <div className="text-xs font-mono text-secondary-ink mb-3">
            Decision record
          </div>

          {/* The Gate: Awaiting reply */}
          {isAwaitingReply ? (
            <div className="space-y-3">
              <div className="bg-highlighter px-2 py-1 inline-block text-ink font-mono text-xs font-medium">
                Awaiting your reply by SMS · sent {memo.smsTime || '14:02'} to {memo.smsRecipient || '+1 ••• 4471'}
              </div>

              <div className="text-xs text-secondary-ink font-sans max-w-[75ch]">
                Texted message: &ldquo;{memo.smsText}&rdquo;
              </div>

              {/* SMS Reply Simulation Actions */}
              <div className="flex items-center gap-3 pt-1">
                <button
                  type="button"
                  onClick={() => handleQuickReply(openDispute.id, '1')}
                  disabled={replyingId === openDispute.id}
                  className="border border-ink px-3 py-1.5 text-xs font-mono text-ink bg-transparent hover:bg-ink hover:text-sheet transition-colors disabled:opacity-50"
                >
                  Reply &quot;1&quot; to fight
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickReply(openDispute.id, '2')}
                  disabled={replyingId === openDispute.id}
                  className="border border-rule px-3 py-1.5 text-xs font-mono text-secondary-ink bg-transparent hover:border-ink hover:text-ink transition-colors disabled:opacity-50"
                >
                  {openDispute.status === 'warning_needs_response' || openDispute.id.includes('S3') || openDispute.reason === 'subscription_canceled'
                    ? 'Reply "2" to refund'
                    : 'Reply "2" to concede'}
                </button>
              </div>
            </div>
          ) : null}

          {/* Decision Recorded: Stamp Lands */}
          {!isAwaitingReply && hasRecordedOutcome ? (
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="text-xs font-sans text-secondary-ink">
                  Decision executed:
                </div>
                {localDecision ? (
                  openDispute.status === 'refunded_inquiry' || openDispute.id.includes('S3') || openDispute.reason === 'subscription_canceled' || openDispute.status === 'warning_needs_response' ? (
                    <Stamp
                      text="INQUIRY CLOSED · $15 FEE AVOIDED"
                      variant="inquiry_closed"
                      animate={true}
                    />
                  ) : localDecision.action === 'approved' ? (
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
                ) : openDispute.status === 'refunded_inquiry' || openDispute.decision?.action === 'refund_inquiry' || (openDispute.reason === 'subscription_canceled' && openDispute.status !== 'needs_response' && openDispute.status !== 'warning_needs_response') ? (
                  <Stamp text="INQUIRY CLOSED · $15 FEE AVOIDED" variant="inquiry_closed" />
                ) : openDispute.status === 'won' ? (
                  <Stamp text="FOUGHT · 06 SEP 14:07 · BY AGENT" variant="won" />
                ) : openDispute.status === 'lost' ? (
                  <Stamp text="LOST · 06 SEP 14:07 · ISSUER DECISION" variant="lost" />
                ) : openDispute.status === 'charge_refunded' ? (
                  <Stamp text="CONCEDED · 06 SEP 14:08 · BY AGENT" variant="conceded" />
                ) : openDispute.decision?.action === 'fight' || openDispute.status === 'under_review' ? (
                  <Stamp text="FOUGHT · 06 SEP 14:07 · BY AGENT" variant="won" />
                ) : openDispute.decision?.action === 'concede' ? (
                  <Stamp text="CONCEDED · 06 SEP 14:08 · BY AGENT" variant="conceded" />
                ) : openDispute.reason === 'product_not_received' ? (
                  <Stamp text="FOUGHT · 06 SEP 14:07 · BY AGENT" variant="won" />
                ) : (
                  <Stamp text="FOUGHT · 06 SEP 14:07 · BY AGENT" variant="won" />
                )}
              </div>

              <div>
                <Link
                  href={`/case/${openDispute.id}`}
                  className="underline text-ink font-mono text-xs hover:text-ink"
                >
                  Open full case record
                </Link>
              </div>
            </div>
          ) : null}
        </div>
      </section>

      {/* ROSTER BELOW: Every other dispute as a ruled table */}
      <CaseFeed
        disputes={disputes}
        openDisputeId={openDispute.id}
        onSelectDispute={(id) => setSelectedDisputeId(id)}
      />
    </div>
  );
}

