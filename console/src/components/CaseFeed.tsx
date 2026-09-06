'use client';

import React, { useState, useMemo } from 'react';
import Link from 'next/link';
import { Dispute } from '@/lib/types';
import { StatusChip } from './StatusChip';
import { ArrowRight, Clock, AlertTriangle, Search, X, TrendingUp } from 'lucide-react';

interface CaseFeedProps {
  disputes: Dispute[];
  onQuickReply?: (disputeId: string, replyCode: '1' | '2' | '3') => void;
  isReplyingId?: string | null;
}

type FilterTab = 'all' | 'needs_response' | 'under_review' | 'won' | 'lost';

export const CaseFeed: React.FC<CaseFeedProps> = ({ disputes, onQuickReply, isReplyingId }) => {
  const [confirmingConcedeId, setConfirmingConcedeId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<FilterTab>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const counts = useMemo(() => {
    return {
      all: disputes.length,
      needs_response: disputes.filter(
        (d) => ['needs_response', 'warning_needs_response'].includes(d.status) || (d.decision && d.decision.status === 'pending')
      ).length,
      under_review: disputes.filter(
        (d) => d.status === 'under_review' || (d.decision && (d.decision.status === 'approved' || d.decision.status === 'executed'))
      ).length,
      won: disputes.filter((d) => d.status === 'won').length,
      lost: disputes.filter((d) => ['lost', 'charge_refunded'].includes(d.status)).length,
    };
  }, [disputes]);

  const filteredDisputes = useMemo(() => {
    return disputes.filter((d) => {
      // Tab filter
      if (activeTab === 'needs_response') {
        const isPending = ['needs_response', 'warning_needs_response'].includes(d.status) || (d.decision && d.decision.status === 'pending');
        if (!isPending) return false;
      } else if (activeTab === 'under_review') {
        const isUnderReview = d.status === 'under_review' || (d.decision && (d.decision.status === 'approved' || d.decision.status === 'executed'));
        if (!isUnderReview) return false;
      } else if (activeTab === 'won') {
        if (d.status !== 'won') return false;
      } else if (activeTab === 'lost') {
        if (!['lost', 'charge_refunded'].includes(d.status)) return false;
      }

      // Search query filter
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const matchesId = d.id.toLowerCase().includes(q);
        const matchesReason = d.reason.toLowerCase().includes(q);
        const matchesOrder = d.order_id ? d.order_id.toLowerCase().includes(q) : false;
        if (!matchesId && !matchesReason && !matchesOrder) return false;
      }

      return true;
    });
  }, [disputes, activeTab, searchQuery]);

  if (!disputes || disputes.length === 0) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-12 text-center text-slate-400">
        <Clock className="h-10 w-10 text-slate-600 mx-auto mb-3" />
        <h3 className="text-base font-semibold text-slate-200">No Disputes Recorded Yet</h3>
        <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
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
      {/* Header with Title, Search and Auto-refresh note */}
      <div className="p-4 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-3">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-200">
            Dispute Cases ({disputes.length})
          </h3>
          <span className="text-xs text-slate-400">Auto-refreshing every 5s</span>
        </div>

        {/* Search Bar */}
        <div className="relative max-w-xs w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search ID, reason, or order..."
            aria-label="Search disputes"
            className="w-full bg-slate-950 border border-slate-700/80 rounded-xl pl-8 pr-8 py-1.5 text-xs text-slate-200 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => setSearchQuery('')}
              aria-label="Clear search query"
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
            >
              <X className="h-3 w-3" />
            </button>
          )}
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="px-4 py-2 bg-slate-950/60 border-b border-slate-800 flex flex-wrap items-center gap-1.5 text-xs">
        <button
          type="button"
          onClick={() => setActiveTab('all')}
          className={`px-3 py-1 rounded-lg font-medium transition-colors ${
            activeTab === 'all'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
          }`}
        >
          All ({counts.all})
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('needs_response')}
          className={`px-3 py-1 rounded-lg font-medium transition-colors flex items-center space-x-1.5 ${
            activeTab === 'needs_response'
              ? 'bg-amber-600 text-white shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
          }`}
        >
          <span>Needs Response</span>
          <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-slate-900/60 font-mono">
            {counts.needs_response}
          </span>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('under_review')}
          className={`px-3 py-1 rounded-lg font-medium transition-colors flex items-center space-x-1.5 ${
            activeTab === 'under_review'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
          }`}
        >
          <span>Under Review</span>
          <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-slate-900/60 font-mono">
            {counts.under_review}
          </span>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('won')}
          className={`px-3 py-1 rounded-lg font-medium transition-colors flex items-center space-x-1.5 ${
            activeTab === 'won'
              ? 'bg-emerald-600 text-white shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
          }`}
        >
          <span>Won</span>
          <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-slate-900/60 font-mono">
            {counts.won}
          </span>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('lost')}
          className={`px-3 py-1 rounded-lg font-medium transition-colors flex items-center space-x-1.5 ${
            activeTab === 'lost'
              ? 'bg-rose-600 text-white shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
          }`}
        >
          <span>Lost / Conceded</span>
          <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-slate-900/60 font-mono">
            {counts.lost}
          </span>
        </button>
      </div>

      {/* Disputes List */}
      {filteredDisputes.length === 0 ? (
        <div className="p-10 text-center text-slate-400">
          <p className="text-sm font-medium text-slate-300">No disputes match your current filter</p>
          <p className="text-xs text-slate-400 mt-1">
            Try resetting your search query or selecting another status tab.
          </p>
          <button
            type="button"
            onClick={() => {
              setActiveTab('all');
              setSearchQuery('');
            }}
            className="mt-3 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
          >
            Reset Filters
          </button>
        </div>
      ) : (
        <div className="divide-y divide-slate-800/80">
          {filteredDisputes.map((d) => {
            const amountFormatted = `$${(d.amount_cents / 100).toFixed(2)}`;
            const isPending = d.status === 'needs_response' || (d.decision && d.decision.status === 'pending');
            const isReplying = isReplyingId === d.id;
            const evFormatted = d.decision?.expected_value_cents
              ? `$${(d.decision.expected_value_cents / 100).toFixed(2)}`
              : null;

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

                    {evFormatted && (
                      <span
                        title={`Expected Net Value: (Win Prob × ${amountFormatted}) - $15.00 dispute fee`}
                        className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-emerald-500/10 text-emerald-300 border border-emerald-500/20"
                      >
                        <TrendingUp className="h-3 w-3 text-emerald-400" />
                        <span>EV: +{evFormatted}</span>
                      </span>
                    )}
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
                        <span className="font-mono text-slate-400">Order: {d.order_id}</span>
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
                          className="px-2.5 py-1 text-xs font-bold rounded-lg bg-rose-700 hover:bg-rose-600 text-white disabled:opacity-50 transition-colors shadow-sm"
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
                          className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-emerald-700 hover:bg-emerald-600 text-white disabled:opacity-50 transition-colors"
                        >
                          1 Fight
                        </button>
                        <button
                          type="button"
                          disabled={isReplying}
                          onClick={() => setConfirmingConcedeId(d.id)}
                          aria-label={`Initiate concession for dispute ${d.id}`}
                          className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-rose-700 hover:bg-rose-600 text-white disabled:opacity-50 transition-colors"
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
      )}
    </div>
  );
};
