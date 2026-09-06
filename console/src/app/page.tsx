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

  return (
    <div className="space-y-6">
      <Header
        lastUpdated={lastUpdated}
        isRefreshing={isRefreshing}
        onRefresh={fetchDisputes}
        secondsRemaining={secondsRemaining}
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Total Disputes</span>
            <ShieldAlert className="h-4 w-4 text-indigo-400" />
          </div>
          <p className="text-2xl font-bold font-mono text-white mt-2">{totalCount}</p>
          <span className="text-[11px] text-slate-400 mt-1">Synthetic & live Stripe events</span>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Win Rate</span>
            <TrendingUp className="h-4 w-4 text-emerald-400" />
          </div>
          <p className="text-2xl font-bold font-mono text-emerald-300 mt-2">{winRateFormatted}</p>
          <span className="text-[11px] text-slate-400 mt-1">
            {resolvedDisputes.length > 0
              ? `${wonCount} of ${resolvedDisputes.length} resolved cases`
              : 'Awaiting dispute resolutions'}
          </span>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Protected Revenue</span>
            <DollarSign className="h-4 w-4 text-emerald-400" />
          </div>
          <p className="text-2xl font-bold font-mono text-white mt-2">
            ${(wonVolume / 100).toFixed(2)}
          </p>
          <span className="text-[11px] text-slate-400 mt-1">Recovered automatically</span>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Pending Action</span>
            <Clock className="h-4 w-4 text-amber-400" />
          </div>
          <p className="text-2xl font-bold font-mono text-amber-300 mt-2">{pendingCount}</p>
          <span className="text-[11px] text-slate-400 mt-1">Awaiting owner confirmation</span>
        </div>
      </div>

      {actionToast && (
        <div
          role="status"
          aria-live="polite"
          className={`p-4 rounded-xl text-xs flex items-center justify-between gap-3 border shadow-lg animate-in fade-in duration-200 ${
            actionToast.type === 'success'
              ? 'bg-emerald-950/70 border-emerald-800 text-emerald-200'
              : 'bg-rose-950/80 border-rose-700 text-rose-200'
          }`}
        >
          <div className="flex items-center space-x-2.5">
            {actionToast.type === 'success' ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
            ) : (
              <AlertCircle className="h-4 w-4 text-rose-400 shrink-0" />
            )}
            <span className="font-medium">{actionToast.message}</span>
          </div>
          <div className="flex items-center space-x-2 shrink-0">
            {actionToast.onRetry && (
              <button
                type="button"
                onClick={actionToast.onRetry}
                className="px-2.5 py-1 rounded-lg bg-rose-800 hover:bg-rose-700 text-white font-medium flex items-center space-x-1 transition-colors"
              >
                <RotateCcw className="h-3 w-3" />
                <span>Retry</span>
              </button>
            )}
            <button
              type="button"
              onClick={() => setActionToast(null)}
              aria-label="Dismiss notification"
              className="text-slate-400 hover:text-white p-1"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      )}

      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800/60 text-xs text-rose-300 flex items-center space-x-2">
          <AlertCircle className="h-4 w-4 text-rose-400 shrink-0" />
          <p>Database notice: {errorMsg}</p>
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
