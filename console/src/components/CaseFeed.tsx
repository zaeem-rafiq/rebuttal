'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Dispute } from '@/lib/types';
import { StatusChip } from './StatusChip';
import { ArrowRight, Clock, AlertTriangle } from 'lucide-react';

interface CaseFeedProps {
  disputes: Dispute[];
  onQuickReply?: (disputeId: string, replyCode: '1' | '2' | '3') => void;
  isReplyingId?: string | null;
}

export const CaseFeed: React.FC<CaseFeedProps> = ({ disputes, onQuickReply, isReplyingId }) => {
  const [confirmingConcedeId, setConfirmingConcedeId] = useState<string | null>(null);
  if (!disputes || disputes.length === 0) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-12 text-center text-slate-400">
        <Clock className="h-10 w-10 text-slate-600 mx-auto mb-3" />
        <h3 className="text-base font-semibold text-slate-200">No Disputes Recorded Yet</h3>
        <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
          Use the Scenario Injector above to inject S1, S2, or S3 into Stripe test mode. The dispute will appear here within 5 seconds.
        </p>
      </div>
    );
  }

  const formatDueBy = (dateStr?: string) => {
    if (!dateStr) return 'No deadline';
    const due = new Date(dateStr);
    const diffDays = Math.ceil((due.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
    if (diffDays > 0) {
      return `Due in ${diffDays} days (${due.toLocaleDateString()})`;
    }
    return `Passed (${due.toLocaleDateString()})`;
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl shadow-black/20">
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
          Dispute Cases ({disputes.length})
        </h3>
        <span className="text-xs text-slate-500">Auto-refreshing every 5s</span>
      </div>

      <div className="divide-y divide-slate-800/80">
        {disputes.map((d) => {
          const amountFormatted = `$${(d.amount_cents / 100).toFixed(2)}`;
          const isPending = d.status === 'needs_response' || (d.decision && d.decision.status === 'pending');
          const isReplying = isReplyingId === d.id;

          return (
            <div
              key={d.id}
              className="p-5 hover:bg-slate-800/40 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="space-y-1.5">
                <div className="flex flex-wrap items-center space-x-2.5">
                  <Link
                    href={`/case/${d.id}`}
                    className="font-mono font-bold text-slate-100 hover:text-indigo-400 text-sm transition-colors flex items-center space-x-1"
                  >
                    <span>{d.id}</span>
                  </Link>
                  <StatusChip status={d.status} size="sm" />
                  <span className="text-xs font-mono font-semibold text-indigo-300">
                    {amountFormatted}
                  </span>
                </div>

                <div className="flex flex-wrap items-center space-x-3 text-xs text-slate-400">
                  <span className="capitalize text-slate-300 font-medium">
                    Reason: {d.reason.replace(/_/g, ' ')}
                  </span>
                  <span>•</span>
                  <span className="flex items-center space-x-1 text-slate-400">
                    <Clock className="h-3 w-3" />
                    <span>{formatDueBy(d.evidence_due_by)}</span>
                  </span>
                  {d.order_id && (
                    <>
                      <span>•</span>
                      <span className="font-mono text-slate-500">Order: {d.order_id}</span>
                    </>
                  )}
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                {isPending && onQuickReply && (
                  confirmingConcedeId === d.id ? (
                    <div className="flex items-center space-x-2 bg-rose-950/90 p-1.5 px-3 rounded-xl border border-rose-600 text-xs shadow-lg animate-in fade-in duration-200">
                      <AlertTriangle className="h-4 w-4 text-rose-400 shrink-0" />
                      <span className="text-rose-200 font-medium">
                        Concede {amountFormatted}? Forfeits dispute to Stripe.
                      </span>
                      <button
                        type="button"
                        disabled={isReplying}
                        onClick={() => {
                          setConfirmingConcedeId(null);
                          onQuickReply(d.id, '2');
                        }}
                        aria-label={`Confirm permanent concession of dispute ${d.id}`}
                        className="px-2.5 py-1 text-xs font-bold rounded-lg bg-rose-600 hover:bg-rose-500 text-white disabled:opacity-50 transition-colors shadow-sm"
                      >
                        Yes, Concede
                      </button>
                      <button
                        type="button"
                        disabled={isReplying}
                        onClick={() => setConfirmingConcedeId(null)}
                        aria-label="Cancel concession"
                        className="px-2.5 py-1 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center space-x-1.5 bg-slate-950/80 p-1.5 rounded-xl border border-amber-500/30">
                      <span className="text-[11px] font-semibold text-amber-300 px-2 uppercase">
                        Owner Action:
                      </span>
                      <button
                        type="button"
                        disabled={isReplying}
                        onClick={() => onQuickReply(d.id, '1')}
                        aria-label={`Fight dispute ${d.id} and submit evidence`}
                        className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white disabled:opacity-50 transition-colors"
                      >
                        1 Fight
                      </button>
                      <button
                        type="button"
                        disabled={isReplying}
                        onClick={() => setConfirmingConcedeId(d.id)}
                        aria-label={`Initiate concession for dispute ${d.id}`}
                        className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-rose-600 hover:bg-rose-500 text-white disabled:opacity-50 transition-colors"
                      >
                        2 Concede
                      </button>
                      <button
                        type="button"
                        disabled={isReplying}
                        onClick={() => onQuickReply(d.id, '3')}
                        aria-label={`Hold dispute ${d.id} for manual review`}
                        className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-slate-700 hover:bg-slate-600 text-white disabled:opacity-50 transition-colors"
                      >
                        3 Hold
                      </button>
                    </div>
                  )
                )}

                <Link
                  href={`/case/${d.id}`}
                  className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
                >
                  <span>Review Case</span>
                  <ArrowRight className="h-3.5 w-3.5 text-indigo-400" />
                </Link>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
