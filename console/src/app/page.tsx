'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { supabase } from '@/lib/supabase';
import { Dispute } from '@/lib/types';
import { Header } from '@/components/Header';
import { InjectToolbar } from '@/components/InjectToolbar';
import { CaseFeed } from '@/components/CaseFeed';
import { TWILIO_WEBHOOK_URL } from '@/lib/config';
import { ShieldAlert, TrendingUp, DollarSign, Clock, AlertCircle, CheckCircle2, RotateCcw, X } from 'lucide-react';

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
    const actionLabel = replyCode === '1' ? 'Fight' : replyCode === '2' ? 'Concede' : 'Hold';

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
        message: `Action '${actionLabel}' recorded for ${disputeId}. Bedrock AgentCore defense pipeline notified.`,
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
  const resolvedDisputes = disputes.filter((d) => ['won', 'lost', 'conceded', 'charge_refunded'].includes(d.status));
  const wonCount = disputes.filter((d) => d.status === 'won').length;
  const wonVolume = disputes
    .filter((d) => d.status === 'won')
    .reduce((acc, d) => acc + (d.amount_cents || 0), 0);
  const pendingCount = disputes.filter(
    (d) => d.status === 'needs_response' || (d.decision && d.decision.status === 'pending')
  ).length;
  const winRateFormatted = resolvedDisputes.length > 0
    ? `${Math.round((wonCount / resolvedDisputes.length) * 100)}%`
    : '—%';

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse" aria-busy="true" aria-label="Loading Evidentiary Docket">
        {/* Header Skeleton */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-surface-border">
          <div className="flex items-center space-x-3">
            <div className="h-9 w-9 rounded-lg bg-surface-subtle" />
            <div className="space-y-1.5">
              <div className="h-4 w-40 bg-surface-subtle rounded" />
              <div className="h-3 w-56 bg-surface-subtle rounded" />
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <div className="h-8 w-24 bg-surface-subtle rounded-md" />
            <div className="h-8 w-8 bg-surface-subtle rounded-md" />
          </div>
        </div>

        {/* Metric Ledger Skeleton */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 bg-surface-card border border-surface-border rounded-lg divide-y sm:divide-y-0 sm:divide-x divide-surface-border overflow-hidden">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="p-5 space-y-3">
              <div className="h-3 w-28 bg-surface-subtle rounded" />
              <div className="h-7 w-20 bg-surface-subtle rounded" />
              <div className="h-2.5 w-36 bg-surface-subtle rounded" />
            </div>
          ))}
        </div>

        {/* Inject Toolbar Skeleton */}
        <div className="h-14 bg-surface-card border border-surface-border rounded-lg" />

        {/* Docket Table Skeleton */}
        <div className="bg-surface-card border border-surface-border rounded-lg overflow-hidden">
          <div className="p-4 border-b border-surface-border flex justify-between items-center">
            <div className="h-4 w-36 bg-surface-subtle rounded" />
            <div className="h-7 w-48 bg-surface-subtle rounded" />
          </div>
          <div className="divide-y divide-surface-border">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="p-4 flex items-center justify-between">
                <div className="space-y-1">
                  <div className="h-3.5 w-32 bg-surface-subtle rounded" />
                  <div className="h-2.5 w-24 bg-surface-subtle rounded" />
                </div>
                <div className="h-3.5 w-40 bg-surface-subtle rounded hidden sm:block" />
                <div className="h-5 w-20 bg-surface-subtle rounded" />
                <div className="h-3.5 w-16 bg-surface-subtle rounded" />
                <div className="h-7 w-20 bg-surface-subtle rounded" />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Header
        lastUpdated={lastUpdated}
        isRefreshing={isRefreshing}
        onRefresh={fetchDisputes}
        secondsRemaining={secondsRemaining}
      />

      {/* Master Evidentiary Ledger Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 bg-surface-card border border-surface-border rounded-lg divide-y sm:divide-y-0 sm:divide-x divide-surface-border overflow-hidden shadow-xs">
        <div className="p-5 flex flex-col justify-between">
          <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider font-mono">
            Protected Net Volume
          </span>
          <div className="mt-2">
            <p className="text-3xl font-bold font-mono text-status-won-text tabular-nums tracking-tight">
              ${(wonVolume / 100).toFixed(2)}
            </p>
            <span className="text-[11px] text-text-muted mt-1 block">
              {wonCount > 0 ? `${wonCount} carrier receipts signed & locked` : 'Recovered automatically via carrier POD'}
            </span>
          </div>
        </div>

        <div className="p-5 flex flex-col justify-between">
          <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider font-mono">
            Evidentiary Win Rate
          </span>
          <div className="mt-2">
            <p className="text-2xl font-bold font-mono text-text-primary tabular-nums">
              {winRateFormatted}
            </p>
            <span className="text-[11px] text-text-muted mt-1 block">
              {resolvedDisputes.length > 0 ? `${wonCount} won of ${resolvedDisputes.length} resolved` : 'Awaiting initial dispute resolution'}
            </span>
          </div>
        </div>

        <div className="p-5 flex flex-col justify-between">
          <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider font-mono">
            Active Docket Load
          </span>
          <div className="mt-2">
            <p className="text-2xl font-bold font-mono text-text-primary tabular-nums">
              {totalCount}
            </p>
            <span className="text-[11px] text-text-muted mt-1 block">
              Stripe cases currently on record
            </span>
          </div>
        </div>

        <div className="p-5 flex flex-col justify-between">
          <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider font-mono">
            ApprovalGate Intercepts
          </span>
          <div className="mt-2">
            <p className={`text-2xl font-bold font-mono tabular-nums ${pendingCount > 0 ? 'text-status-review-text' : 'text-text-secondary'}`}>
              {pendingCount}
            </p>
            <span className="text-[11px] text-text-muted mt-1 block">
              {pendingCount > 0 ? 'Merchant SMS action required' : 'All dossiers running on autopilot'}
            </span>
          </div>
        </div>
      </div>

      {actionToast && (
        <div
          role="status"
          aria-live="polite"
          className={`p-3.5 rounded-lg text-xs flex items-center justify-between gap-3 border shadow-sm font-mono ${
            actionToast.type === 'success'
              ? 'bg-status-won-bg border-status-won-border text-status-won-text'
              : 'bg-status-lost-bg border-status-lost-border text-status-lost-text'
          }`}
        >
          <div className="flex items-center space-x-2.5">
            {actionToast.type === 'success' ? (
              <CheckCircle2 className="h-4 w-4 shrink-0" />
            ) : (
              <AlertCircle className="h-4 w-4 shrink-0" />
            )}
            <span className="font-medium">{actionToast.message}</span>
          </div>
          <div className="flex items-center space-x-2 shrink-0">
            {actionToast.onRetry && (
              <button
                type="button"
                onClick={actionToast.onRetry}
                className="px-2 py-0.5 rounded bg-surface-subtle hover:bg-surface-hover text-text-primary font-medium flex items-center space-x-1 border border-surface-border transition-colors"
              >
                <RotateCcw className="h-3 w-3" />
                <span>Retry</span>
              </button>
            )}
            <button
              type="button"
              onClick={() => setActionToast(null)}
              aria-label="Dismiss notification"
              className="text-text-muted hover:text-text-primary p-1"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      )}

      {errorMsg && (
        <div className="p-3.5 rounded-lg bg-status-lost-bg border border-status-lost-border text-xs text-status-lost-text flex items-center justify-between gap-3 font-mono">
          <div className="flex items-center space-x-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <p>Database telemetry error: {errorMsg}</p>
          </div>
          <button
            type="button"
            onClick={() => fetchDisputes()}
            className="px-2.5 py-1 rounded bg-surface-subtle hover:bg-surface-hover text-text-primary text-[11px] font-medium border border-surface-border flex items-center space-x-1 transition-colors shrink-0"
          >
            <RotateCcw className="h-3 w-3" />
            <span>Reconnect</span>
          </button>
        </div>
      )}

      <InjectToolbar onInjectSuccess={fetchDisputes} />

      <CaseFeed
        disputes={disputes}
        onQuickReply={handleQuickReply}
        isReplyingId={replyingId}
      />
    </div>
  );
}
