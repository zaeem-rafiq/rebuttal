'use client';

import React, { useMemo } from 'react';
import Link from 'next/link';
import { Dispute } from '@/lib/types';
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
      return <Stamp text="FOUGHT · WON" variant="won" size="sm" />;
    }
    if (d.status === 'lost') {
      return <Stamp text="LOST" variant="lost" size="sm" />;
    }
    if (d.status === 'refunded_inquiry' || d.decision?.action === 'refund_inquiry') {
      return <Stamp text="INQUIRY CLOSED · $15 FEE AVOIDED" variant="inquiry_closed" size="sm" />;
    }
    if (d.status === 'charge_refunded') {
      return <Stamp text="CONCEDED" variant="conceded" size="sm" />;
    }

    if (d.decision?.action === 'fight' || d.decision?.status === 'approved' || d.status === 'under_review') {
      return <Stamp text="FOUGHT" variant="won" size="sm" />;
    }
    if (d.decision?.action === 'concede') {
      return <Stamp text="CONCEDED" variant="conceded" size="sm" />;
    }
    return (
      <span className="font-mono text-secondary-ink text-xs">
        Awaiting reply
      </span>
    );
  };

  if (rosterDisputes.length === 0) {
    return (
      <div className="mt-8 pt-4 border-t border-rule">
        <h2 className="text-sm font-sans font-medium text-ink border-b border-rule-strong pb-2 mb-3">
          Dispute roster
        </h2>
        <p className="text-xs font-mono text-secondary-ink py-4">
          No other open disputes on docket.
        </p>
      </div>
    );
  }

  return (
    <div className="mt-8 pt-4 border-t border-rule">
      <div className="flex items-baseline justify-between border-b border-rule-strong pb-2 mb-0">
        <h2 className="text-sm font-sans font-medium text-ink">
          Dispute roster
        </h2>
        <span className="text-xs font-mono text-secondary-ink">
          {rosterDisputes.length} {rosterDisputes.length === 1 ? 'case' : 'cases'}
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left text-xs">
          <thead>
            <tr className="border-b border-rule text-secondary-ink font-mono text-xs">
              <th className="py-2.5 px-3 font-normal">Case ID</th>
              <th className="py-2.5 px-3 font-normal">Reason</th>
              <th className="py-2.5 px-3 font-normal">Agent action</th>
              <th className="py-2.5 px-3 font-normal">Outcome</th>
              <th className="py-2.5 px-3 font-normal">Respond by</th>
              <th className="py-2.5 px-3 font-normal text-right">Amount</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-rule font-sans">
            {rosterDisputes.map((d) => {
              const dueInfo = formatRespondBy(d.evidence_due_by);
              const amountFormatted = `$${(d.amount_cents / 100).toFixed(2)}`;
              const reasonClean = d.reason.replace(/_/g, ' ');

              return (
                <tr
                  key={d.id}
                  className="h-10 hover:bg-sheet/60 transition-colors"
                >
                  {/* Case ID */}
                  <td className="py-2.5 px-3 align-middle font-mono">
                    <button
                      type="button"
                      onClick={() => onSelectDispute ? onSelectDispute(d.id) : undefined}
                      className="underline text-ink hover:text-ink font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ink"
                    >
                      {d.id}
                    </button>
                  </td>

                  {/* Reason (sentence case) */}
                  <td className="py-2.5 px-3 align-middle text-ink capitalize">
                    {reasonClean}
                  </td>

                  {/* Agent action (sentence case) */}
                  <td className="py-2.5 px-3 align-middle text-secondary-ink">
                    {getAgentAction(d)}
                  </td>

                  {/* Outcome (small stamp or status) */}
                  <td className="py-2.5 px-3 align-middle">
                    {renderOutcomeStamp(d)}
                  </td>

                  {/* Respond by */}
                  <td className="py-2.5 px-3 align-middle font-mono">
                    <span className={dueInfo.passed ? 'text-decision-red' : 'text-secondary-ink'}>
                      {dueInfo.text}
                    </span>
                  </td>

                  {/* Amount (right-aligned, mono, tabular numbers) */}
                  <td className="py-2.5 px-3 align-middle text-right font-mono tabular-nums text-ink font-medium">
                    {amountFormatted}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

