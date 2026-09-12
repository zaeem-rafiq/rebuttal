'use client';

import React, { useMemo, useState, useRef, useEffect } from 'react';
import { Dispute } from '@/lib/types';
import { formatSentenceCase } from '@/lib/disputes';
import { Stamp } from './Stamp';

interface CaseFeedProps {
  disputes: Dispute[];
  openDisputeId?: string | null;
  onSelectDispute?: (disputeId: string) => void;
}

export const CaseFeed: React.FC<CaseFeedProps> = ({
  disputes,
  openDisputeId,
  onSelectDispute,
}) => {
  const [focusedIndex, setFocusedIndex] = useState<number>(-1);
  const rowRefs = useRef<(HTMLTableRowElement | null)[]>([]);

  // Exclude the currently open case from the roster
  const rosterDisputes = useMemo(() => {
    const filtered = disputes.filter((d) => d.id !== openDisputeId);

    // Sort by respond-by (evidence_due_by) ascending
    return filtered.sort((a, b) => {
      const dateA = a.evidence_due_by ? new Date(a.evidence_due_by).getTime() : Infinity;
      const dateB = b.evidence_due_by ? new Date(b.evidence_due_by).getTime() : Infinity;
      return dateA - dateB;
    });
  }, [disputes, openDisputeId]);

  // Keep rowRefs array in sync
  useEffect(() => {
    rowRefs.current = rowRefs.current.slice(0, rosterDisputes.length);
  }, [rosterDisputes.length]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTableSectionElement>) => {
    if (rosterDisputes.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      const nextIndex = focusedIndex < rosterDisputes.length - 1 ? focusedIndex + 1 : 0;
      setFocusedIndex(nextIndex);
      rowRefs.current[nextIndex]?.focus();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      const prevIndex = focusedIndex > 0 ? focusedIndex - 1 : rosterDisputes.length - 1;
      setFocusedIndex(prevIndex);
      rowRefs.current[prevIndex]?.focus();
    } else if (e.key === 'Enter' || e.key === ' ') {
      if (focusedIndex >= 0 && focusedIndex < rosterDisputes.length) {
        e.preventDefault();
        onSelectDispute?.(rosterDisputes[focusedIndex].id);
        requestAnimationFrame(() => {
          document.getElementById('open-case-file')?.focus();
        });
      }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      if (focusedIndex >= 0 && rowRefs.current[focusedIndex]) {
        rowRefs.current[focusedIndex]?.blur();
      }
      setFocusedIndex(-1);
    }
  };

  const formatRespondBy = (dateStr?: string) => {
    if (!dateStr) return { text: 'No deadline', passed: false };
    const due = new Date(dateStr);
    const diffDays = Math.ceil((due.getTime() - Date.now()) / (1000 * 60 * 60 * 24));

    const day = due.getUTCDate().toString().padStart(2, '0');
    const month = due.toLocaleString('en-US', { month: 'short', timeZone: 'UTC' });
    const year = due.getUTCFullYear();
    const formattedDate = `${day} ${month} ${year}`;

    if (diffDays > 0) {
      return {
        text: `${formattedDate} (${diffDays} days)`,
        passed: false,
      };
    }
    return {
      text: `${formattedDate} (Deadline passed)`,
      passed: true,
    };
  };

  const getAgentAction = (d: Dispute) => {
    if (d.reason === 'fraudulent') return 'Drafted VIP fraud rebuttal memo';
    if (d.reason === 'product_not_received') return 'Compiled carrier delivery proof & signature';
    if (d.reason === 'subscription_canceled') return 'Recommended concession under policy § 4.2';
    if (d.decision?.owner_summary) return d.decision.owner_summary;
    return 'Compiled counter-evidence brief';
  };

  const renderOutcomeStamp = (d: Dispute) => {
    if (d.status === 'won') {
      return <Stamp text="WON" variant="won" size="sm" />;
    }
    if (d.status === 'lost') {
      return <Stamp text="LOST" variant="lost" size="sm" />;
    }
    if (d.status === 'refunded_inquiry' || d.decision?.action === 'refund_inquiry') {
      return <Stamp text="INQUIRY CLOSED" variant="inquiry_closed" size="sm" />;
    }
    if (d.status === 'charge_refunded' || d.decision?.action === 'concede') {
      return <Stamp text="CONCEDED" variant="conceded" size="sm" />;
    }
    if (d.status === 'under_review') {
      return <Stamp text="UNDER REVIEW" variant="under_review" size="sm" />;
    }
    if (d.decision?.action === 'fight' || d.decision?.status === 'approved') {
      return <Stamp text="WON" variant="won" size="sm" />;
    }
    return <Stamp text="PENDING" variant="pending" size="sm" />;
  };

  if (rosterDisputes.length === 0) {
    return (
      <section className="mt-8 pt-4 border-t border-rule" aria-label="Dispute roster">
        <h2 className="text-sm font-sans font-medium text-ink border-b border-rule-strong pb-2 mb-3">
          Dispute roster
        </h2>
        <p className="text-xs font-mono text-secondary-ink py-4">
          No other open disputes on docket.
        </p>
      </section>
    );
  }

  return (
    <section className="mt-8 pt-4 border-t border-rule" aria-label="Dispute roster">
      <div className="flex items-baseline justify-between border-b border-rule-strong pb-2 mb-0">
        <h2 className="text-sm font-sans font-medium text-ink">
          Dispute roster
        </h2>
        <span className="text-xs font-mono text-secondary-ink">
          {rosterDisputes.length} {rosterDisputes.length === 1 ? 'case' : 'cases'}
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left text-xs" aria-label="Dispute roster table">
          <thead>
            <tr className="border-b border-rule text-secondary-ink font-mono text-xs whitespace-nowrap">
              <th scope="col" className="py-2.5 px-3 font-normal whitespace-nowrap">Case ID</th>
              <th scope="col" className="py-2.5 px-3 font-normal whitespace-nowrap">Reason</th>
              <th scope="col" className="py-2.5 px-3 font-normal whitespace-nowrap hidden md:table-cell">Agent action</th>
              <th scope="col" className="py-2.5 px-3 font-normal whitespace-nowrap">Outcome</th>
              <th scope="col" className="py-2.5 px-3 font-normal whitespace-nowrap hidden sm:table-cell">Respond by</th>
              <th scope="col" className="py-2.5 px-3 font-normal text-right whitespace-nowrap">Amount</th>
            </tr>
          </thead>
          <tbody
            className="divide-y divide-rule font-sans"
            onKeyDown={handleKeyDown}
          >
            {rosterDisputes.map((d, index) => {
              const dueInfo = formatRespondBy(d.evidence_due_by);
              const amountFormatted = `$${(d.amount_cents / 100).toFixed(2)}`;
              const reasonClean = formatSentenceCase(d.reason);
              const isFocused = focusedIndex === index;

              return (
                <tr
                  key={d.id}
                  ref={(el) => {
                    rowRefs.current[index] = el;
                  }}
                  role="row"
                  aria-selected={isFocused}
                  tabIndex={index === 0 && focusedIndex === -1 ? 0 : isFocused ? 0 : -1}
                  onFocus={() => setFocusedIndex(index)}
                  onClick={() => {
                    onSelectDispute?.(d.id);
                    requestAnimationFrame(() => {
                      document.getElementById('open-case-file')?.focus();
                    });
                  }}
                  aria-label={`Case ${d.id}, ${reasonClean}, amount ${amountFormatted}`}
                  className={`h-10 min-h-[40px] cursor-pointer hover:bg-sheet/60 transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-ink focus-visible:outline-offset-2 ${
                    isFocused ? 'bg-sheet/70' : ''
                  }`}
                >
                  {/* Case ID */}
                  <td className="py-2.5 px-3 align-middle font-mono whitespace-nowrap">
                    <span className="underline text-ink font-medium">
                      {d.id}
                    </span>
                  </td>

                  {/* Reason (strict sentence case) */}
                  <td className="py-2.5 px-3 align-middle text-ink whitespace-nowrap">
                    {reasonClean}
                  </td>

                  {/* Agent action (hidden on mobile to prevent overflow) */}
                  <td className="py-2.5 px-3 align-middle text-secondary-ink whitespace-nowrap hidden md:table-cell">
                    {getAgentAction(d)}
                  </td>

                  {/* Outcome (small stamp or status) */}
                  <td className="py-2.5 px-3 align-middle whitespace-nowrap">
                    {renderOutcomeStamp(d)}
                  </td>

                  {/* Respond by (hidden on narrow mobile <640px) */}
                  <td className="py-2.5 px-3 align-middle font-mono whitespace-nowrap hidden sm:table-cell">
                    <span className={dueInfo.passed ? 'text-decision-red' : 'text-secondary-ink'}>
                      {dueInfo.text}
                    </span>
                  </td>

                  {/* Amount (right-aligned, mono, tabular numbers) */}
                  <td className="py-2.5 px-3 align-middle text-right font-mono tabular-nums text-ink font-medium whitespace-nowrap">
                    {amountFormatted}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
};
