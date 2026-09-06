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
      <div className="bg-surface-card border border-surface-border rounded-lg p-12 text-center text-text-muted">
        <ShieldAlert className="h-9 w-9 text-text-muted mx-auto mb-3" />
        <h3 className="text-sm font-semibold text-text-primary">Evidentiary Docket Awaiting Cases</h3>
        <p className="text-xs text-text-muted mt-1 max-w-sm mx-auto leading-relaxed">
          No dispute cases are currently recorded. Inject S1, S2, or S3 using the verification toolbar above to launch Bedrock AgentCore defense pipelines.
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
    <div className="bg-surface-card border border-surface-border rounded-lg overflow-hidden shadow-xs">
      {/* Header with Title, Search and Tabs */}
      <div className="p-4 border-b border-surface-border bg-surface-subtle/50 flex flex-col lg:flex-row lg:items-center justify-between gap-3">
        <div className="flex items-center space-x-3">
          <h3 className="text-sm font-semibold tracking-tight text-text-primary">
            Evidentiary Docket Ledger
          </h3>
          <span className="font-mono text-[11px] font-semibold text-text-muted bg-surface-card border border-surface-border px-2 py-0.5 rounded">
            {disputes.length} Records
          </span>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          {/* Filter Tabs */}
          <div className="flex items-center bg-canvas-base p-1 rounded-md border border-surface-border text-xs">
            <button
              type="button"
              onClick={() => setActiveTab('all')}
              className={`px-2.5 py-1 rounded font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary ${
                activeTab === 'all'
                  ? 'bg-surface-card text-text-primary border border-surface-border shadow-xs'
                  : 'text-text-muted hover:text-text-secondary'
              }`}
            >
              All ({counts.all})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('needs_response')}
              className={`px-2.5 py-1 rounded font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary ${
                activeTab === 'needs_response'
                  ? 'bg-status-review-bg text-status-review-text border border-status-review-border'
                  : 'text-text-muted hover:text-text-secondary'
              }`}
            >
              Action Req ({counts.needs_response})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('under_review')}
              className={`px-2.5 py-1 rounded font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary ${
                activeTab === 'under_review'
                  ? 'bg-status-submitted-bg text-status-submitted-text border border-status-submitted-border'
                  : 'text-text-muted hover:text-text-secondary'
              }`}
            >
              Under Review ({counts.under_review})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('won')}
              className={`px-2.5 py-1 rounded font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary ${
                activeTab === 'won'
                  ? 'bg-status-won-bg text-status-won-text border border-status-won-border'
                  : 'text-text-muted hover:text-text-secondary'
              }`}
            >
              Won ({counts.won})
            </button>
          </div>

          {/* Search Bar */}
          <div className="relative max-w-xs w-full">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-text-muted" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search ID, reason, order..."
              aria-label="Search disputes"
              className="w-full bg-canvas-base border border-surface-border rounded-md pl-8 pr-7 py-1 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-brand-primary focus:border-brand-primary font-mono"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                aria-label="Clear search query"
                className="absolute right-2 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary"
              >
                <X className="h-3 w-3" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Empty Filter State */}
      {filteredDisputes.length === 0 ? (
        <div className="p-12 text-center text-text-muted">
          <p className="text-sm font-medium text-text-secondary">No disputes match your current filter</p>
          <p className="text-xs text-text-muted mt-1">
            Try resetting your search query or selecting another status tab.
          </p>
          <button
            type="button"
            onClick={() => {
              setActiveTab('all');
              setSearchQuery('');
            }}
            className="mt-3 px-3 py-1.5 rounded-md text-xs font-medium bg-surface-subtle hover:bg-surface-hover text-text-primary border border-surface-border transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary"
          >
            Reset Filters
          </button>
        </div>
      ) : (
        <div className="overflow-x-auto">
          {/* Desktop Table View */}
          <table className="w-full border-collapse text-left text-xs">
            <thead>
              <tr className="border-b border-surface-border bg-surface-subtle/40 text-[10px] font-mono font-semibold text-text-muted uppercase tracking-wider">
                <th className="py-3 px-4">Dispute ID & Order</th>
                <th className="py-3 px-4">Reason & Evidentiary Dossier</th>
                <th className="py-3 px-4">Docket Status</th>
                <th className="py-3 px-4">Evidence Deadline</th>
                <th className="py-3 px-4 text-right">Contested Amount</th>
                <th className="py-3 px-4 text-right">Docket Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-border">
              {filteredDisputes.map((d) => {
                const amountFormatted = `$${(d.amount_cents / 100).toFixed(2)}`;
                const isPending = d.status === 'needs_response' || (d.decision && d.decision.status === 'pending');
                const isReplying = isReplyingId === d.id;
                const dueInfo = formatDueBy(d.evidence_due_by);
                const isConcedePrompt = confirmingConcedeId === d.id;

                return (
                  <tr
                    key={d.id}
                    className={`transition-colors hover:bg-surface-hover/60 ${
                      isPending ? 'bg-status-review-bg/20 border-l-2 border-l-status-review-border' : ''
                    }`}
                  >
                    {/* Dispute ID & Order */}
                    <td className="py-3.5 px-4 align-middle">
                      <Link
                        href={`/case/${d.id}`}
                        className={`font-mono font-semibold hover:underline block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary rounded ${
                          isPending ? 'text-text-primary' : 'text-text-primary'
                        }`}
                      >
                        {d.id}
                      </Link>
                      <div className="font-mono text-[11px] text-text-muted mt-0.5">
                        {d.order_id ? `Ref: ${d.order_id}` : 'No linked order'}
                      </div>
                    </td>

                    {/* Reason & Evidentiary Dossier */}
                    <td className="py-3.5 px-4 align-middle max-w-xs">
                      <div className="font-medium text-text-primary capitalize">
                        {d.reason.replace(/_/g, ' ')}
                      </div>
                      <div className="text-[11px] text-text-muted mt-0.5 truncate">
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
                      <div className={`text-[11px] font-semibold ${dueInfo.urgent ? 'text-status-review-text' : 'text-text-secondary'}`}>
                        {dueInfo.label}
                      </div>
                      {dueInfo.days && (
                        <div className="text-[10px] text-text-muted">
                          {dueInfo.days}
                        </div>
                      )}
                    </td>

                    {/* Contested Amount */}
                    <td className="py-3.5 px-4 align-middle text-right font-mono">
                      <div className="text-sm font-bold tabular-nums text-text-primary">
                        {amountFormatted}
                      </div>
                      <div className="text-[10px] text-text-muted">USD</div>
                    </td>

                    {/* Actions */}
                    <td className="py-3.5 px-4 align-middle text-right">
                      {isPending && onQuickReply ? (
                        isConcedePrompt ? (
                          <div className="inline-flex items-center gap-1.5 bg-status-lost-bg p-1 px-2 rounded border border-status-lost-border text-xs font-mono">
                            <span className="text-status-lost-text text-[11px] font-medium">Concede?</span>
                            <button
                              type="button"
                              disabled={isReplying}
                              onClick={() => {
                                setConfirmingConcedeId(null);
                                onQuickReply(d.id, '2');
                              }}
                              className="px-2 py-0.5 text-[11px] font-bold rounded bg-status-lost-text text-canvas-base hover:opacity-90 disabled:opacity-50 transition-opacity focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-status-lost-border"
                            >
                              Yes
                            </button>
                            <button
                              type="button"
                              disabled={isReplying}
                              onClick={() => setConfirmingConcedeId(null)}
                              className="px-1.5 py-0.5 text-[11px] rounded bg-surface-subtle text-text-muted hover:text-text-primary border border-surface-border transition-colors"
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
                              className="px-2 py-1 rounded text-[11px] font-mono font-semibold bg-status-won-bg text-status-won-text border border-status-won-border hover:bg-status-won-border/30 active:scale-95 disabled:opacity-50 transition-all focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-brand-primary"
                            >
                              1 Fight
                            </button>
                            <button
                              type="button"
                              disabled={isReplying}
                              onClick={() => setConfirmingConcedeId(d.id)}
                              title="Concede dispute"
                              className="px-2 py-1 rounded text-[11px] font-mono font-semibold bg-status-lost-bg text-status-lost-text border border-status-lost-border hover:bg-status-lost-border/30 active:scale-95 disabled:opacity-50 transition-all focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-brand-primary"
                            >
                              2 Concede
                            </button>
                            <Link
                              href={`/case/${d.id}`}
                              className="px-2.5 py-1 rounded text-[11px] font-medium bg-surface-subtle hover:bg-surface-hover text-text-secondary hover:text-text-primary border border-surface-border active:scale-95 transition-all ml-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary"
                            >
                              Review
                            </Link>
                          </div>
                        )
                      ) : (
                        <Link
                          href={`/case/${d.id}`}
                          className="inline-flex items-center px-3 py-1 rounded text-[11px] font-medium bg-surface-subtle hover:bg-surface-hover text-text-secondary hover:text-text-primary border border-surface-border active:scale-95 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary"
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
