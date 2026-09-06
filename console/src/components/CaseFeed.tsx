'use client';

import React, { useState, useMemo } from 'react';
import Link from 'next/link';
import { Dispute } from '@/lib/types';
import { StatusChip } from './StatusChip';
import { AlertTriangle, Search, X, ShieldAlert } from 'lucide-react';

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
      <div className="bg-surface border border-border rounded-lg p-12 text-center text-slate-400">
        <ShieldAlert className="h-9 w-9 text-slate-600 mx-auto mb-3" />
        <h3 className="text-sm font-semibold text-slate-200">No Dispute Cases Recorded</h3>
        <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
          Inject S1, S2, or S3 using the verification toolbar above to generate a live Stripe test case.
        </p>
      </div>
    );
  }

  const formatDueBy = (dateStr?: string) => {
    if (!dateStr) return { label: 'No deadline', days: null, urgent: false };
    const due = new Date(dateStr);
    const diffDays = Math.ceil((due.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
    if (diffDays > 0) {
      return {
        label: due.toLocaleDateString(),
        days: `${diffDays} days left`,
        urgent: diffDays <= 7,
      };
    }
    return {
      label: due.toLocaleDateString(),
      days: 'Deadline passed',
      urgent: true,
    };
  };

  return (
    <div className="bg-surface border border-border rounded-lg overflow-hidden shadow-sm">
      {/* Header with Title, Search and Tabs */}
      <div className="p-4 border-b border-border bg-[#0f1523] flex flex-col lg:flex-row lg:items-center justify-between gap-3">
        <div className="flex items-center space-x-3">
          <h3 className="text-sm font-bold tracking-tight text-white">
            Evidentiary Docket Ledger
          </h3>
          <span className="font-mono text-[11px] font-semibold text-slate-400 bg-border px-2 py-0.5 rounded">
            {disputes.length} Records
          </span>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          {/* Filter Tabs */}
          <div className="flex items-center bg-[#0b0f17] p-1 rounded-md border border-border text-xs">
            <button
              type="button"
              onClick={() => setActiveTab('all')}
              className={`px-2.5 py-1 rounded font-medium transition-colors ${
                activeTab === 'all'
                  ? 'bg-border text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              All ({counts.all})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('needs_response')}
              className={`px-2.5 py-1 rounded font-medium transition-colors ${
                activeTab === 'needs_response'
                  ? 'bg-amber-950/80 text-amber-200 border border-amber-800/60'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Action Req ({counts.needs_response})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('under_review')}
              className={`px-2.5 py-1 rounded font-medium transition-colors ${
                activeTab === 'under_review'
                  ? 'bg-blue-950/80 text-blue-200 border border-blue-800/60'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Under Review ({counts.under_review})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('won')}
              className={`px-2.5 py-1 rounded font-medium transition-colors ${
                activeTab === 'won'
                  ? 'bg-emerald-950/80 text-emerald-200 border border-emerald-800/60'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Won ({counts.won})
            </button>
          </div>

          {/* Search Bar */}
          <div className="relative max-w-xs w-full">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search ID, reason, order..."
              aria-label="Search disputes"
              className="w-full bg-[#0b0f17] border border-border rounded-md pl-8 pr-7 py-1 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-brand focus:border-brand"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                aria-label="Clear search query"
                className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
              >
                <X className="h-3 w-3" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Empty Filter State */}
      {filteredDisputes.length === 0 ? (
        <div className="p-12 text-center text-slate-400">
          <p className="text-sm font-medium text-slate-200">No disputes match your current filter</p>
          <p className="text-xs text-slate-400 mt-1">
            Try resetting your search query or selecting another status tab.
          </p>
          <button
            type="button"
            onClick={() => {
              setActiveTab('all');
              setSearchQuery('');
            }}
            className="mt-3 px-3 py-1.5 rounded-md text-xs font-medium bg-surface-elevated hover:bg-surface-hover text-slate-200 border border-border transition-colors"
          >
            Reset Filters
          </button>
        </div>
      ) : (
        <div className="overflow-x-auto">
          {/* Desktop Table View */}
          <table className="w-full border-collapse text-left text-xs">
            <thead>
              <tr className="border-b border-border bg-[#0d131f] text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                <th className="py-3 px-4">Dispute ID & Order</th>
                <th className="py-3 px-4">Reason & Evidentiary Dossier</th>
                <th className="py-3 px-4">Docket Status</th>
                <th className="py-3 px-4">Evidence Deadline</th>
                <th className="py-3 px-4 text-right">Contested Amount</th>
                <th className="py-3 px-4 text-right">Docket Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {filteredDisputes.map((d) => {
                const amountFormatted = `$${(d.amount_cents / 100).toFixed(2)}`;
                const isPending = d.status === 'needs_response' || (d.decision && d.decision.status === 'pending');
                const isReplying = isReplyingId === d.id;
                const dueInfo = formatDueBy(d.evidence_due_by);
                const isConcedePrompt = confirmingConcedeId === d.id;

                return (
                  <tr
                    key={d.id}
                    className={`transition-colors hover:bg-surface-elevated/70 ${
                      isPending ? 'bg-[#171113] border-l-2 border-l-rose-500' : ''
                    }`}
                  >
                    {/* Dispute ID & Order */}
                    <td className="py-3.5 px-4 align-middle">
                      <Link
                        href={`/case/${d.id}`}
                        className={`font-mono font-semibold hover:underline block ${
                          isPending ? 'text-rose-200' : 'text-slate-100'
                        }`}
                      >
                        {d.id}
                      </Link>
                      <div className="font-mono text-[11px] text-slate-400 mt-0.5">
                        {d.order_id ? `Ref: ${d.order_id}` : 'No linked order'}
                      </div>
                    </td>

                    {/* Reason & Evidentiary Dossier */}
                    <td className="py-3.5 px-4 align-middle max-w-xs">
                      <div className="font-semibold text-slate-200 capitalize">
                        {d.reason.replace(/_/g, ' ')}
                      </div>
                      <div className="text-[11px] text-slate-400 mt-0.5 truncate">
                        {d.decision?.owner_summary || (
                          d.reason === 'product_not_received'
                            ? 'Carrier signature verified · Proof ready'
                            : d.reason === 'fraudulent'
                            ? 'VIP account · ApprovalGate interrupt'
                            : 'Pre-dispute inquiry notification'
                        )}
                      </div>
                    </td>

                    {/* Status */}
                    <td className="py-3.5 px-4 align-middle">
                      <StatusChip status={d.status} size="sm" />
                    </td>

                    {/* Deadline */}
                    <td className="py-3.5 px-4 align-middle font-mono">
                      <div className={`text-[11px] font-semibold ${dueInfo.urgent ? 'text-amber-400' : 'text-slate-300'}`}>
                        {dueInfo.label}
                      </div>
                      {dueInfo.days && (
                        <div className="text-[10px] text-slate-400">
                          {dueInfo.days}
                        </div>
                      )}
                    </td>

                    {/* Contested Amount */}
                    <td className="py-3.5 px-4 align-middle text-right font-mono">
                      <div className={`text-sm font-bold tabular-nums ${isPending ? 'text-rose-200' : 'text-white'}`}>
                        {amountFormatted}
                      </div>
                      <div className="text-[10px] text-slate-400">USD</div>
                    </td>

                    {/* Actions */}
                    <td className="py-3.5 px-4 align-middle text-right">
                      {isPending && onQuickReply ? (
                        isConcedePrompt ? (
                          <div className="inline-flex items-center gap-1.5 bg-rose-950 p-1 px-2 rounded border border-rose-700 text-xs">
                            <span className="text-rose-200 text-[11px] font-medium">Concede?</span>
                            <button
                              type="button"
                              disabled={isReplying}
                              onClick={() => {
                                setConfirmingConcedeId(null);
                                onQuickReply(d.id, '2');
                              }}
                              className="px-2 py-0.5 text-[11px] font-bold rounded bg-rose-700 hover:bg-rose-600 text-white disabled:opacity-50"
                            >
                              Yes
                            </button>
                            <button
                              type="button"
                              disabled={isReplying}
                              onClick={() => setConfirmingConcedeId(null)}
                              className="px-1.5 py-0.5 text-[11px] rounded bg-slate-800 text-slate-300"
                            >
                              Cancel
                            </button>
                          </div>
                        ) : (
                          <div className="inline-flex items-center gap-1">
                            <button
                              type="button"
                              disabled={isReplying}
                              onClick={() => onQuickReply(d.id, '1')}
                              title="Fight dispute"
                              className="px-2 py-1 rounded text-[11px] font-bold bg-emerald-900/80 hover:bg-emerald-800 text-emerald-200 border border-emerald-700 transition-colors"
                            >
                              1 Fight
                            </button>
                            <button
                              type="button"
                              disabled={isReplying}
                              onClick={() => setConfirmingConcedeId(d.id)}
                              title="Concede dispute"
                              className="px-2 py-1 rounded text-[11px] font-bold bg-rose-950 hover:bg-rose-900 text-rose-200 border border-rose-800 transition-colors"
                            >
                              2 Concede
                            </button>
                            <Link
                              href={`/case/${d.id}`}
                              className="px-2.5 py-1 rounded text-[11px] font-medium bg-surface-elevated hover:bg-surface-hover text-slate-200 border border-border transition-colors ml-1"
                            >
                              Review
                            </Link>
                          </div>
                        )
                      ) : (
                        <Link
                          href={`/case/${d.id}`}
                          className="inline-flex items-center px-3 py-1 rounded text-[11px] font-semibold bg-brand/20 hover:bg-brand text-blue-200 hover:text-white border border-brand/50 transition-colors"
                        >
                          Review Docket
                        </Link>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
