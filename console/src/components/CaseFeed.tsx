'use client';

import React, { useState, useMemo } from 'react';
import Link from 'next/link';
import { Dispute } from '@/lib/types';
import { StatusChip } from './StatusChip';
import { Scale, Search, X } from 'lucide-react';

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
      <div className="bg-surface border border-border rounded-xs p-12 text-center text-docket-text-muted">
        <Scale className="h-10 w-10 text-docket-gold/60 mx-auto mb-3" />
        <h3 className="text-base font-serif font-medium text-docket-text">DOCKET CLEAR // AWAITING CLAIMS</h3>
        <p className="text-xs text-docket-text-muted mt-1 max-w-sm mx-auto leading-relaxed">
          No chargeback claims currently filed in jurisdiction. Inject S1, S2, or S3 using the scenario ribbon above to activate the Bedrock evidentiary compiler.
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
    <div className="bg-surface border border-border rounded-xs overflow-hidden shadow-xs">
      {/* Header with Title, Search and Tabs */}
      <div className="p-4 border-b border-border bg-surface-subtle flex flex-col lg:flex-row lg:items-center justify-between gap-3">
        <div className="flex items-center space-x-3">
          <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-docket-text">
            Active Docket Ledger — Chronological Stream
          </h3>
          <span className="font-mono text-[11px] font-semibold text-docket-gold bg-surface-elevated border border-border px-2 py-0.5 rounded-xs">
            {disputes.length} Records
          </span>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          {/* Filter Tabs */}
          <div className="flex flex-wrap items-center bg-canvas p-1 rounded-xs border border-border text-xs gap-1 sm:gap-0 font-mono">
            <button
              type="button"
              onClick={() => setActiveTab('all')}
              className={`px-3 py-1.5 sm:py-1 min-h-[44px] sm:min-h-0 rounded-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-docket-gold ${
                activeTab === 'all'
                  ? 'bg-surface-elevated text-docket-text border border-docket-gold/40 shadow-xs'
                  : 'text-docket-text-muted hover:text-docket-text-secondary'
              }`}
            >
              All ({counts.all})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('needs_response')}
              className={`px-3 py-1.5 sm:py-1 min-h-[44px] sm:min-h-0 rounded-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-docket-gold ${
                activeTab === 'needs_response'
                  ? 'bg-docket-gold/15 text-docket-gold border border-docket-gold/50'
                  : 'text-docket-text-muted hover:text-docket-text-secondary'
              }`}
            >
              Action Req ({counts.needs_response})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('under_review')}
              className={`px-3 py-1.5 sm:py-1 min-h-[44px] sm:min-h-0 rounded-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-docket-gold ${
                activeTab === 'under_review'
                  ? 'bg-status-review/15 text-status-review border border-status-review/40'
                  : 'text-docket-text-muted hover:text-docket-text-secondary'
              }`}
            >
              Under Review ({counts.under_review})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('won')}
              className={`px-3 py-1.5 sm:py-1 min-h-[44px] sm:min-h-0 rounded-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-docket-gold ${
                activeTab === 'won'
                  ? 'bg-status-won/15 text-status-won border border-status-won/40'
                  : 'text-docket-text-muted hover:text-docket-text-secondary'
              }`}
            >
              Won ({counts.won})
            </button>
          </div>

          {/* Search Bar */}
          <div className="relative max-w-xs w-full">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-docket-text-muted" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search ID, reason, order..."
              aria-label="Search docket records"
              className="w-full bg-canvas border border-border rounded-xs pl-8 pr-7 py-1.5 sm:py-1 min-h-[44px] sm:min-h-0 text-xs text-docket-text placeholder:text-docket-text-subtle focus:outline-none focus:ring-1 focus:ring-docket-gold focus:border-docket-gold font-mono"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                aria-label="Clear search query"
                className="absolute right-2 top-1/2 -translate-y-1/2 text-docket-text-muted hover:text-docket-text"
              >
                <X className="h-3 w-3" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Empty Filter State */}
      {filteredDisputes.length === 0 ? (
        <div className="p-12 text-center text-docket-text-muted">
          <p className="text-sm font-serif text-docket-text-secondary">No claims match the specified filter query</p>
          <p className="text-xs text-docket-text-muted mt-1">
            Reset filter selection or search terms to inspect full docket.
          </p>
          <button
            type="button"
            onClick={() => {
              setActiveTab('all');
              setSearchQuery('');
            }}
            className="mt-3 px-3 py-1.5 rounded-xs text-xs font-mono bg-surface-elevated hover:bg-surface-hover text-docket-text border border-border transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-docket-gold"
          >
            Reset Filters
          </button>
        </div>
      ) : (
        <div className="overflow-x-auto">
          {/* Desktop Table View */}
          <table className="w-full border-collapse text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-border bg-surface-subtle text-[11px] font-mono uppercase tracking-wider text-docket-text-muted">
                <th className="py-3 px-4">Docket ID</th>
                <th className="py-3 px-4">Claimant / Reason</th>
                <th className="py-3 px-4">Docket Status</th>
                <th className="py-3 px-4">Filing Deadline</th>
                <th className="py-3 px-4 text-right">Contested Amount</th>
                <th className="py-3 px-4 text-right">Action</th>
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
                    className={`transition-colors hover:bg-surface-hover/50 ${
                      isPending ? 'bg-docket-gold/5 border-l-2 border-l-docket-gold' : ''
                    }`}
                  >
                    {/* Docket ID & Order */}
                    <td className="py-3.5 px-4 align-middle">
                      <Link
                        href={`/case/${d.id}`}
                        className="font-mono font-semibold text-docket-text hover:text-docket-gold hover:underline block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-docket-gold rounded-xs"
                      >
                        {d.id}
                      </Link>
                      <div className="font-mono text-[11px] text-docket-text-muted mt-0.5">
                        {d.order_id ? `Ref: ${d.order_id}` : 'Direct claim'}
                      </div>
                    </td>

                    {/* Reason & Evidentiary Summary */}
                    <td className="py-3.5 px-4 align-middle max-w-xs font-sans">
                      <div className="font-medium text-docket-text capitalize font-mono text-xs">
                        {d.reason.replace(/_/g, ' ')}
                      </div>
                      <div className="text-[11px] text-docket-text-muted mt-0.5 truncate">
                        {d.decision?.owner_summary || (
                          d.reason === 'product_not_received'
                            ? 'UPS carrier signature matched (M. Brown)'
                            : d.reason === 'fraudulent'
                            ? 'VIP Account ($4.8k LTV) — ApprovalGate Intercept'
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
                      <div className={`text-[11px] font-semibold ${dueInfo.urgent ? 'text-docket-gold' : 'text-docket-text-secondary'}`}>
                        {dueInfo.label}
                      </div>
                      {dueInfo.days && (
                        <div className="text-[10px] text-docket-text-muted">
                          {dueInfo.days}
                        </div>
                      )}
                    </td>

                    {/* Contested Amount */}
                    <td className="py-3.5 px-4 align-middle text-right font-mono">
                      <div className="text-sm font-bold tabular-nums text-docket-gold">
                        {amountFormatted}
                      </div>
                      <div className="text-[10px] text-docket-text-muted">USD</div>
                    </td>

                    {/* Actions */}
                    <td className="py-3.5 px-4 align-middle text-right">
                      {isPending && onQuickReply ? (
                        isConcedePrompt ? (
                          <div className="inline-flex items-center gap-1.5 bg-surface-elevated p-1 px-2 rounded-xs border border-border text-xs font-mono">
                            <span className="text-docket-text-secondary text-[11px]">Concede?</span>
                            <button
                              type="button"
                              disabled={isReplying}
                              onClick={() => {
                                setConfirmingConcedeId(null);
                                onQuickReply(d.id, '2');
                              }}
                              className="px-2 py-0.5 text-[11px] font-bold rounded-xs bg-status-action text-white hover:opacity-90 disabled:opacity-50 transition-opacity focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-docket-gold"
                            >
                              Yes
                            </button>
                            <button
                              type="button"
                              disabled={isReplying}
                              onClick={() => setConfirmingConcedeId(null)}
                              className="px-1.5 py-0.5 text-[11px] rounded-xs bg-surface text-docket-text-muted hover:text-docket-text border border-border transition-colors"
                            >
                              Cancel
                            </button>
                          </div>
                        ) : (
                          <div className="inline-flex items-center gap-1 font-mono">
                            <button
                              type="button"
                              disabled={isReplying}
                              onClick={() => onQuickReply(d.id, '1')}
                              title="Authorize Evidence Submission"
                              className="px-2.5 py-1 min-h-[44px] sm:min-h-0 rounded-xs text-[11px] font-mono font-semibold bg-docket-gold text-canvas hover:bg-docket-gold-light active:scale-95 disabled:opacity-50 transition-all focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-docket-gold"
                            >
                              1 Submit Proof
                            </button>
                            <button
                              type="button"
                              disabled={isReplying}
                              onClick={() => setConfirmingConcedeId(d.id)}
                              title="Concede dispute"
                              className="px-2 py-1 min-h-[44px] sm:min-h-0 rounded-xs text-[11px] font-mono bg-surface-elevated text-docket-text-muted border border-border hover:text-docket-text active:scale-95 disabled:opacity-50 transition-all focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-docket-gold"
                            >
                              2 Concede
                            </button>
                            <Link
                              href={`/case/${d.id}`}
                              className="px-2 py-1 min-h-[44px] sm:min-h-0 rounded-xs text-[11px] font-mono bg-surface-elevated hover:bg-surface-hover text-docket-text-secondary hover:text-docket-text border border-border active:scale-95 transition-all ml-1 inline-flex items-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-docket-gold"
                            >
                              Dossier &rarr;
                            </Link>
                          </div>
                        )
                      ) : (
                        <Link
                          href={`/case/${d.id}`}
                          className="inline-flex items-center px-3 py-1 min-h-[44px] sm:min-h-0 rounded-xs text-[11px] font-mono bg-surface-elevated hover:bg-surface-hover text-docket-text-secondary hover:text-docket-text border border-border active:scale-95 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-docket-gold"
                        >
                          Review Case &rarr;
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
