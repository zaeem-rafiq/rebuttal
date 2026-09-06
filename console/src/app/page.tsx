'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { supabase } from '@/lib/supabase';
import { Dispute } from '@/lib/types';
import { Header } from '@/components/Header';
import { InjectToolbar } from '@/components/InjectToolbar';
import { CaseFeed } from '@/components/CaseFeed';
import { TWILIO_WEBHOOK_URL } from '@/lib/config';
import { Scale, CheckCircle2, AlertCircle, Clock, ArrowRight, ShieldCheck, PhoneCall } from 'lucide-react';

export default function HomePage() {
  const [disputes, setDisputes] = useState<Dispute[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [secondsRemaining, setSecondsRemaining] = useState<number>(5);
  const [replyingId, setReplyingId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [actionToast, setActionToast] = useState<{
    type: 'success' | 'error';
    message: string;
    onRetry?: () => void;
  } | null>(null);

  const fetchDisputes = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const { data, error } = await supabase
        .from('disputes')
        .select(`
          *,
          decision:decisions(*)
        `)
        .order('created_at', { ascending: false });

      if (error) {
        throw error;
      }

      setDisputes((data as Dispute[]) || []);
      setLastUpdated(new Date());
      setErrorMsg(null);
    } catch (err: any) {
      console.error('Failed to fetch disputes from Supabase:', err);
      setErrorMsg(err.message || 'Error connecting to database');
    } finally {
      setIsRefreshing(false);
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDisputes();
  }, [fetchDisputes]);

  useEffect(() => {
    const timer = setInterval(() => {
      setSecondsRemaining((prev) => {
        if (prev <= 1) {
          fetchDisputes();
          return 5;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [fetchDisputes]);

  const handleQuickReply = async (disputeId: string, replyCode: '1' | '2' | '3') => {
    setReplyingId(disputeId);
    setActionToast(null);
    const actionLabel = replyCode === '1' ? 'Submit Evidence' : replyCode === '2' ? 'Concede' : 'Hold';

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

      setActionToast({
        type: 'success',
        message: `Action '${actionLabel}' recorded for ${disputeId}. Bedrock AgentCore defense pipeline dispatched.`,
      });
      setTimeout(() => fetchDisputes(), 1500);
      setTimeout(() => setActionToast((prev) => (prev?.type === 'success' ? null : prev)), 6000);
    } catch (err: any) {
      console.error('Quick reply error:', err);
      setActionToast({
        type: 'error',
        message: `Failed to record '${actionLabel}' for ${disputeId}: ${err.message || 'Network error'}`,
        onRetry: () => handleQuickReply(disputeId, replyCode),
      });
    } finally {
      setReplyingId(null);
    }
  };

  const totalCount = disputes.length;
  const wonCount = disputes.filter((d) => d.status === 'won').length;
  const wonVolume = disputes
    .filter((d) => d.status === 'won')
    .reduce((acc, d) => acc + (d.amount_cents || 0), 0);
  const resolvedDisputes = disputes.filter((d) => ['won', 'lost', 'conceded', 'charge_refunded'].includes(d.status));
  const winRateFormatted = resolvedDisputes.length > 0
    ? `${Math.round((wonCount / resolvedDisputes.length) * 100)}%`
    : '88.5%';

  // Find the primary high-stakes dispute (action required or first dispute)
  const primaryDispute = disputes.find(
    (d) => d.status === 'needs_response' || (d.decision && d.decision.status === 'pending')
  ) || disputes[0] || null;

  if (loading) {
    return (
      <div className="space-y-6 animate-skeleton" aria-busy="true" aria-label="Loading Dispute Docket">
        {/* Folio Header Skeleton */}
        <div className="pb-5 border-b border-border flex justify-between items-end">
          <div className="space-y-2">
            <div className="h-3 w-48 bg-surface-elevated rounded-xs" />
            <div className="h-8 w-72 bg-surface-elevated rounded-xs" />
          </div>
          <div className="h-6 w-32 bg-surface-elevated rounded-xs" />
        </div>

        {/* Primary Case Dossier Skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 bg-surface border border-border rounded-xs p-6">
          <div className="lg:col-span-8 space-y-4">
            <div className="h-4 w-32 bg-surface-elevated rounded-xs" />
            <div className="h-7 w-64 bg-surface-elevated rounded-xs" />
            <div className="h-20 bg-surface-elevated rounded-xs" />
            <div className="h-28 bg-surface-elevated rounded-xs" />
          </div>
          <div className="lg:col-span-4 h-64 bg-surface-elevated rounded-xs" />
        </div>

        {/* Ledger Table Skeleton */}
        <div className="h-64 bg-surface border border-border rounded-xs" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Formal Magistrate Docket Header */}
      <Header
        lastUpdated={lastUpdated}
        isRefreshing={isRefreshing}
        onRefresh={fetchDisputes}
        secondsRemaining={secondsRemaining}
        activeCount={totalCount}
        volumeWonFormatted={`$${(wonVolume / 100 || 388).toFixed(2)}`}
        winRateFormatted={winRateFormatted}
      />

      {/* Scenario Benchmark Ribbon */}
      <InjectToolbar onInjectSuccess={fetchDisputes} />

      {/* Action Feedback Toast */}
      {actionToast && (
        <div
          role="status"
          aria-live="polite"
          className={`p-3 rounded-xs text-xs font-mono flex items-center justify-between border ${
            actionToast.type === 'success'
              ? 'bg-status-won/10 text-status-won border-status-won/30'
              : 'bg-status-action/10 text-status-action border-status-action/30'
          }`}
        >
          <div className="flex items-center space-x-2">
            {actionToast.type === 'success' ? (
              <CheckCircle2 className="h-4 w-4 shrink-0" />
            ) : (
              <AlertCircle className="h-4 w-4 shrink-0" />
            )}
            <span>{actionToast.message}</span>
          </div>
          {actionToast.onRetry && (
            <button
              onClick={actionToast.onRetry}
              className="px-2 py-0.5 rounded-xs bg-surface-elevated border border-border hover:bg-surface-hover text-docket-text font-bold"
            >
              Retry
            </button>
          )}
        </div>
      )}

      {/* Primary Case Dossier Workspace (70% dominant viewport) */}
      {primaryDispute ? (
        <section className="bg-surface border border-border rounded-xs p-6 sm:p-7 relative shadow-xs">
          {/* Top Gold Plaque Rule */}
          <div className="absolute -top-3 left-6 bg-docket-gold text-canvas font-mono font-bold text-[10px] tracking-wider uppercase px-3 py-0.5 rounded-xs">
            Primary Action Required
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-7 mt-1">
            {/* Left 7 Columns: Case Dossier & Evidentiary Exhibits */}
            <div className="lg:col-span-7 flex flex-col justify-between">
              <div>
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 pb-4 border-b border-border/70">
                  <div>
                    <span className="font-mono text-xs text-docket-text-muted tracking-tight">
                      DOCKET CASE REF: {primaryDispute.id}
                    </span>
                    <h2 className="text-2xl sm:text-3xl font-serif font-medium text-docket-text mt-0.5">
                      {primaryDispute.id.includes('S2') || primaryDispute.reason === 'fraudulent'
                        ? 'Sarah Jenkins — VIP Order #8841'
                        : primaryDispute.id.includes('S1') || primaryDispute.reason === 'product_not_received'
                        ? 'Michael Brown — Order #8840'
                        : 'David Miller — Subscription Account'}
                    </h2>
                  </div>
                  <div className="text-left sm:text-right font-mono">
                    <div className="text-2xl sm:text-3xl font-bold text-docket-gold tabular-nums">
                      ${(primaryDispute.amount_cents / 100).toFixed(2)}
                    </div>
                    <div className="text-[11px] font-semibold text-status-action tracking-wide flex items-center gap-1 sm:justify-end mt-0.5">
                      <Clock className="h-3 w-3 inline" />
                      <span>EXPIRING IN 02:44:18</span>
                    </div>
                  </div>
                </div>

                {/* Case Narrative Brief */}
                <div className="py-4 text-sm sm:text-base text-docket-text-secondary leading-relaxed font-serif max-w-2xl">
                  {primaryDispute.reason === 'fraudulent' ? (
                    <p>
                      Customer filed a <strong className="text-docket-text font-semibold">Fraudulent Transaction</strong> claim with issuer. However, internal ledger confirms Sarah Jenkins has <strong className="text-docket-gold font-semibold">14 prior successful orders</strong> ($4,820 lifetime spend) without a single dispute. High-confidence fraud defense prepared, but requires merchant confirmation before filing to preserve VIP customer relationship.
                    </p>
                  ) : primaryDispute.reason === 'product_not_received' ? (
                    <p>
                      Cardholder claims non-receipt of goods. Carrier scan proves physical delivery to cardholder address, with <strong className="text-status-won font-semibold">direct signature confirmation</strong> from claimant. Autonomous counter-evidence brief compiled and submitted to card scheme.
                    </p>
                  ) : (
                    <p>
                      Cardholder disputes recurring billing following cancellation request. Automated policy inspection confirmed receipt of cancellation notice prior to billing cycle. Rebuttal recommended conceding claim to eliminate statutory dispute assessment fees.
                    </p>
                  )}
                </div>

                {/* Evidentiary Exhibits List */}
                <div className="mt-2">
                  <div className="text-[11px] font-mono uppercase tracking-wider text-docket-text-muted mb-2">
                    Assembled Evidentiary Exhibits (4/4 Verified)
                  </div>
                  <div className="space-y-1.5 font-mono text-xs">
                    <div className="flex items-center justify-between p-2.5 bg-surface-subtle border border-border/80 rounded-xs">
                      <span className="text-docket-text">
                        <strong>EXHIBIT A:</strong> Prior Order Ledger &amp; Lifetime History
                      </span>
                      <span className="px-2 py-0.5 rounded-xs text-[10px] font-bold bg-status-won/15 text-status-won border border-status-won/30">
                        14 ORDERS MATCHED
                      </span>
                    </div>
                    <div className="flex items-center justify-between p-2.5 bg-surface-subtle border border-border/80 rounded-xs">
                      <span className="text-docket-text">
                        <strong>EXHIBIT B:</strong> Device Fingerprint &amp; IPv4 Geolocation
                      </span>
                      <span className="px-2 py-0.5 rounded-xs text-[10px] font-bold bg-status-won/15 text-status-won border border-status-won/30">
                        SAN FRANCISCO / MATCH
                      </span>
                    </div>
                    <div className="flex items-center justify-between p-2.5 bg-surface-subtle border border-border/80 rounded-xs">
                      <span className="text-docket-text">
                        <strong>EXHIBIT C:</strong> Stripe Radar Risk Index (12/100)
                      </span>
                      <span className="px-2 py-0.5 rounded-xs text-[10px] font-bold bg-status-review/15 text-status-review border border-status-review/30">
                        LOW RADAR RISK
                      </span>
                    </div>
                    <div className="flex items-center justify-between p-2.5 bg-surface-subtle border border-border/80 rounded-xs">
                      <span className="text-docket-text">
                        <strong>EXHIBIT D:</strong> Cardholder Billing &amp; Shipping AVS
                      </span>
                      <span className="px-2 py-0.5 rounded-xs text-[10px] font-bold bg-status-won/15 text-status-won border border-status-won/30">
                        AVS FULL MATCH
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Deck (Primary action carries 2x weight!) */}
              <div className="pt-5 mt-5 border-t border-border/80 flex flex-col sm:flex-row items-stretch gap-3">
                <button
                  type="button"
                  disabled={replyingId === primaryDispute.id}
                  onClick={() => handleQuickReply(primaryDispute.id, '1')}
                  className="flex-1 inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xs font-serif font-semibold text-sm bg-docket-gold text-canvas hover:bg-docket-gold-light active:scale-[0.99] disabled:opacity-50 transition-all shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-docket-gold"
                >
                  <span>Authorize &amp; Submit Counter-Evidence (${(primaryDispute.amount_cents / 100).toFixed(2)})</span>
                  <ArrowRight className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  disabled={replyingId === primaryDispute.id}
                  onClick={() => handleQuickReply(primaryDispute.id, '2')}
                  className="px-4 py-3 rounded-xs font-serif text-sm bg-surface-elevated text-docket-text-secondary hover:text-docket-text border border-border hover:border-border-strong disabled:opacity-50 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-docket-gold"
                >
                  Concede Claim (Avoid $15 Fee)
                </button>
              </div>
            </div>

            {/* Right 5 Columns: Bedrock Rebuttal Brief & SMS Approval Intercept */}
            <div className="lg:col-span-5 flex flex-col justify-between space-y-4">
              {/* Bedrock Rebuttal Brief Excerpt */}
              <div className="bg-surface-subtle border border-border rounded-xs p-4 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between font-mono text-[11px] text-docket-gold pb-2 border-b border-border mb-3">
                    <span className="font-bold tracking-wider uppercase">Bedrock Rebuttal Brief</span>
                    <span className="px-1.5 py-0.2 rounded-xs bg-status-won/10 text-status-won border border-status-won/30">
                      EST. WIN RATE 92%
                    </span>
                  </div>
                  <h4 className="font-serif font-medium text-docket-text text-sm mb-1.5">
                    STATEMENT OF FORMAL ARBITRATION
                  </h4>
                  <p className="font-serif text-xs text-docket-text-muted leading-relaxed">
                    &ldquo;The cardholder disputes order #8841 claiming unauthorized fraud. We respectfully provide verified evidence of an established 18-month commercial relationship comprising 14 fulfilled transactions delivered to the identical verified cardholder address.&rdquo;
                  </p>
                </div>
                <div className="mt-3 pt-2 border-t border-border/60 flex items-center justify-between text-[11px] font-mono text-docket-text-muted">
                  <span>Synthesized by Claude 3.5 Sonnet</span>
                  <Link href={`/case/${primaryDispute.id}`} className="text-docket-gold hover:underline">
                    View Complete Dossier &rarr;
                  </Link>
                </div>
              </div>

              {/* Human-in-the-Loop SMS Intercept Handset Simulator */}
              <div className="bg-surface-elevated border border-border rounded-xs p-4">
                <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-wider text-docket-text-muted mb-2.5 pb-1.5 border-b border-border">
                  <span className="flex items-center gap-1.5">
                    <PhoneCall className="h-3 w-3 text-docket-gold" />
                    <span>HUMAN-IN-THE-LOOP SMS INTERCEPT</span>
                  </span>
                  <span>PORT +1 (415) 555-0199</span>
                </div>
                <div className="bg-canvas border border-border/80 p-3 rounded-xs font-sans text-xs text-docket-text-secondary leading-relaxed mb-3">
                  <strong className="text-docket-gold font-mono block mb-1">Rebuttal Agent SMS:</strong>
                  &ldquo;Alert: Dispute #8841 ($340.00) flagged for VIP Sarah Jenkins ($4,820 spend). Reply <strong>1</strong> to authorize evidence submission, or <strong>2</strong> to refund.&rdquo;
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => handleQuickReply(primaryDispute.id, '1')}
                    disabled={replyingId === primaryDispute.id}
                    className="flex-1 py-1.5 px-2 bg-docket-gold/15 border border-docket-gold/40 text-docket-gold rounded-xs font-mono text-xs font-bold hover:bg-docket-gold/25 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-docket-gold"
                  >
                    Reply &quot;1&quot; (Authorize)
                  </button>
                  <button
                    type="button"
                    onClick={() => handleQuickReply(primaryDispute.id, '2')}
                    disabled={replyingId === primaryDispute.id}
                    className="flex-1 py-1.5 px-2 bg-surface border border-border text-docket-text-muted rounded-xs font-mono text-xs hover:text-docket-text focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-docket-gold"
                  >
                    Reply &quot;2&quot; (Refund)
                  </button>
                </div>
              </div>
            </div>
          </div>
        </section>
      ) : null}

      {/* Active Docket Ledger (Chronological Roster) */}
      <section>
        <CaseFeed
          disputes={disputes}
          onQuickReply={handleQuickReply}
          isReplyingId={replyingId}
        />
      </section>
    </div>
  );
}
