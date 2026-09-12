'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { supabase } from '@/lib/supabase';
import { Dispute } from '@/lib/types';
import { Header } from '@/components/Header';
import { CaseFeed } from '@/components/CaseFeed';
import { Stamp } from '@/components/Stamp';
import { ExhibitInspector } from '@/components/ExhibitInspector';
import { getCaseFileMemo } from '@/lib/disputes';
import { TWILIO_WEBHOOK_URL, INJECT_URL, CONSOLE_KEY } from '@/lib/config';

export default function HomePage() {
  const [disputes, setDisputes] = useState<Dispute[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedDisputeId, setSelectedDisputeId] = useState<string | null>(null);
  const [activeScenario, setActiveScenario] = useState<'S1' | 'S2' | 'S3' | null>('S2');
  const [loadingScenario, setLoadingScenario] = useState<string | null>(null);
  const [forcedState, setForcedState] = useState<'empty' | 'loading' | 'error' | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cooldown, setCooldown] = useState<number>(0);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'reconnecting' | 'offline'>('connected');
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
      if (navigator.onLine) {
        setConnectionStatus('connected');
      }
    } catch (err: unknown) {
      console.error('Failed to fetch disputes:', err);
      const message = err instanceof Error ? err.message : String(err);
      setError(message || 'Stripe API communication timeout (ECONNRESET).');
      setConnectionStatus('reconnecting');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDisputes();
  }, [fetchDisputes]);

  // Real-time Supabase channel + Network online/offline status
  useEffect(() => {
    const handleOnline = () => {
      setConnectionStatus('connected');
      fetchDisputes();
    };
    const handleOffline = () => {
      setConnectionStatus('offline');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    const channel = supabase
      .channel('public:disputes')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'disputes' },
        () => {
          fetchDisputes();
        }
      )
      .subscribe((status) => {
        if (status === 'SUBSCRIBED') {
          setConnectionStatus('connected');
        } else if (status === 'CLOSED' || status === 'CHANNEL_ERROR' || status === 'TIMED_OUT') {
          setConnectionStatus('reconnecting');
        }
      });

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      supabase.removeChannel(channel);
    };
  }, [fetchDisputes]);

  // Polling fallback every 5s with randomized jitter (5000ms ± 500ms: 4500ms - 5500ms)
  useEffect(() => {
    let timeoutId: NodeJS.Timeout;
    let isMounted = true;

    const schedulePoll = () => {
      const jitterMs = 5000 + Math.floor((Math.random() - 0.5) * 1000);
      timeoutId = setTimeout(async () => {
        if (!isMounted) return;
        try {
          await fetchDisputes();
        } catch {
          // Handled within fetchDisputes
        }
        if (isMounted) {
          schedulePoll();
        }
      }, jitterMs);
    };

    schedulePoll();

    return () => {
      isMounted = false;
      clearTimeout(timeoutId);
    };
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
    } catch (err: unknown) {
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
    } catch (err: unknown) {
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

  if (forcedState === 'loading' || (loading && disputes.length === 0)) {
    return (
      <div className="space-y-6">
        <Header activeScenario={activeScenario} connectionStatus={connectionStatus} />
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

  // Error State: network failure on cold start or forcedState === 'error'
  if (forcedState === 'error' || (error && disputes.length === 0 && forcedState !== 'empty')) {
    return (
      <div className="space-y-6">
        <Header
          activeScenario={activeScenario}
          onSelectScenario={handleSelectScenario}
          loadingScenario={loadingScenario}
          cooldown={cooldown}
          connectionStatus={connectionStatus}
        />
        {/* Error State: 1px rule #B91C1C above error line, secondary ink, retry as ink link */}
        <div className="border-t border-decision-red pt-3 pb-2 flex flex-col sm:flex-row sm:items-baseline justify-between gap-2 text-xs font-mono">
          <span className="text-secondary-ink">
            Failed to synchronize dispute docket: {error || 'Stripe API communication timeout (ECONNRESET).'}
          </span>
          <button
            type="button"
            onClick={() => {
              setError(null);
              setForcedState(null);
              setLoading(true);
              fetchDisputes();
            }}
            className="underline text-ink hover:text-ink cursor-pointer shrink-0"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Quiet State: when nothing is gated and no unhandled error
  const isQuietState = forcedState === 'empty' || (!openDispute && !error);

  if (isQuietState) {
    return (
      <div className="space-y-6">
        <Header
          activeScenario={activeScenario}
          onSelectScenario={handleSelectScenario}
          loadingScenario={loadingScenario}
          cooldown={cooldown}
          connectionStatus={connectionStatus}
        />
        {error && (
          <div className="border-t border-decision-red pt-3 pb-2 flex flex-col sm:flex-row sm:items-baseline justify-between gap-2 text-xs font-mono">
            <span className="text-secondary-ink">
              Failed to synchronize dispute docket: {error}
            </span>
            <button
              type="button"
              onClick={() => {
                setError(null);
                setForcedState(null);
                setLoading(true);
                fetchDisputes();
              }}
              className="underline text-ink hover:text-ink cursor-pointer shrink-0"
            >
              Retry
            </button>
          </div>
        )}
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
          onSelectDispute={(id) => {
            setSelectedDisputeId(id);
            requestAnimationFrame(() => {
              document.getElementById('open-case-file')?.focus();
            });
          }}
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
        connectionStatus={connectionStatus}
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
      <section
        id="open-case-file"
        tabIndex={-1}
        className="bg-sheet border-t-2 border-rule-strong p-6 sm:p-8 focus:outline-none"
      >
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
          <ExhibitInspector exhibits={memo.exhibits} />
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
                  className="border border-ink px-3 py-1.5 text-xs font-mono text-ink bg-transparent hover:bg-ink hover:text-sheet transition-colors disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-ink focus-visible:outline-offset-2"
                >
                  Reply &quot;1&quot; to fight
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickReply(openDispute.id, '2')}
                  disabled={replyingId === openDispute.id}
                  className="border border-rule px-3 py-1.5 text-xs font-mono text-secondary-ink bg-transparent hover:border-ink hover:text-ink transition-colors disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-ink focus-visible:outline-offset-2"
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
                  <Stamp text="INQUIRY CLOSED · $15 FEE AVOIDED" variant="inquiry_closed" animate={true} />
                ) : openDispute.status === 'won' ? (
                  <Stamp text="WON · 06 SEP 14:07 · BY AGENT" variant="won" animate={true} />
                ) : openDispute.status === 'lost' ? (
                  <Stamp text="LOST · 06 SEP 14:07 · ISSUER DECISION" variant="lost" animate={true} />
                ) : openDispute.status === 'charge_refunded' ? (
                  <Stamp text="CONCEDED · 06 SEP 14:08 · BY AGENT" variant="conceded" animate={true} />
                ) : openDispute.status === 'under_review' || openDispute.decision?.action === 'fight' ? (
                  <Stamp text="UNDER REVIEW · EVIDENCE SUBMITTED" variant="under_review" animate={true} />
                ) : openDispute.decision?.action === 'concede' ? (
                  <Stamp text="CONCEDED · 06 SEP 14:08 · BY AGENT" variant="conceded" animate={true} />
                ) : openDispute.reason === 'product_not_received' ? (
                  <Stamp text="WON · 06 SEP 14:07 · BY AGENT" variant="won" animate={true} />
                ) : (
                  <Stamp text="WON · 06 SEP 14:07 · BY AGENT" variant="won" animate={true} />
                )}
              </div>

              <div>
                <Link
                  href={`/case/${openDispute.id}`}
                  className="underline text-ink font-mono text-xs hover:text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-ink focus-visible:outline-offset-2"
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
        onSelectDispute={(id) => {
          setSelectedDisputeId(id);
          requestAnimationFrame(() => {
            document.getElementById('open-case-file')?.focus();
          });
        }}
      />
    </div>
  );
}

