import React from 'react';
import { Decision } from '@/lib/types';
import { Target, TrendingUp, DollarSign, Award, FileText, Info } from 'lucide-react';
import { StatusChip } from './StatusChip';

interface StrategyCardProps {
  decision?: Decision;
  amountCents: number;
}

export const StrategyCard: React.FC<StrategyCardProps> = ({ decision, amountCents }) => {
  if (!decision) {
    return (
      <div className="bg-surface-card border border-surface-border rounded-lg p-6 text-center text-text-muted">
        <Target className="h-5 w-5 mx-auto mb-2 text-text-muted" />
        <p className="text-xs font-semibold text-text-primary">Evaluation In Progress</p>
        <p className="text-[11px] text-text-muted mt-1">Bedrock AgentCore Evidence Graph is analyzing carrier dockets & computing win probability.</p>
      </div>
    );
  }

  const winProbPercent = Math.round(decision.win_probability * 100);
  const expectedValueFormatted = `$${(decision.expected_value_cents / 100).toFixed(2)}`;
  const disputeAmountFormatted = `$${(amountCents / 100).toFixed(2)}`;

  return (
    <div className="bg-surface-card border border-surface-border rounded-lg p-5 space-y-4 shadow-xs">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-surface-border pb-3.5">
        <div>
          <span className="text-xs font-medium text-text-muted">
            Recommended Action
          </span>
          <h3 className="text-base font-bold text-text-primary flex items-center space-x-2 mt-0.5 capitalize">
            <span>{decision.action.replace('_', ' ')}</span>
            <StatusChip status={decision.status} size="sm" />
          </h3>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-[11px] text-text-muted">Customer Tier:</span>
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-surface-subtle text-text-secondary border border-surface-border uppercase">
            {decision.customer_value}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="bg-canvas-base border border-surface-border rounded-md p-3 flex flex-col justify-between">
          <div className="flex items-center justify-between text-[11px] text-text-muted mb-1 font-mono">
            <span>Win Probability</span>
            <TrendingUp className="h-3 w-3 text-status-won-text" />
          </div>
          <div className="text-xl font-bold text-text-primary font-mono tabular-nums">{winProbPercent}%</div>
          <div className="w-full bg-surface-subtle h-1.5 rounded-full mt-2 overflow-hidden border border-surface-border">
            <div
              className={`h-full rounded-full ${
                winProbPercent >= 70 ? 'bg-status-won-text' : winProbPercent >= 40 ? 'bg-status-review-text' : 'bg-status-lost-text'
              }`}
              style={{ width: `${winProbPercent}%` }}
            />
          </div>
        </div>

        <div className="bg-canvas-base border border-surface-border rounded-md p-3 flex flex-col justify-between">
          <div className="flex items-center justify-between text-[11px] text-text-muted mb-1 font-mono">
            <span className="flex items-center space-x-1">
              <span>Expected Value</span>
              <span
                title={`EV Model: (${winProbPercent}% × ${disputeAmountFormatted}) − $15.00 dispute fee = ${expectedValueFormatted}`}
                className="cursor-help text-text-muted hover:text-brand-primary transition-colors"
                aria-label={`Expected value calculation: ${winProbPercent}% times ${disputeAmountFormatted} minus $15 dispute fee`}
              >
                <Info className="h-3 w-3 inline" />
              </span>
            </span>
            <DollarSign className="h-3 w-3 text-brand-primary" />
          </div>
          <div className="text-xl font-bold text-brand-primary font-mono tabular-nums">{expectedValueFormatted}</div>
          <p className="text-[10px] text-text-muted mt-1 font-mono">Dispute: {disputeAmountFormatted}</p>
        </div>

        <div className="bg-canvas-base border border-surface-border rounded-md p-3 flex flex-col justify-between">
          <div className="flex items-center justify-between text-[11px] text-text-muted mb-1 font-mono">
            <span>Evidence Strength</span>
            <Award className="h-3 w-3 text-brand-primary" />
          </div>
          <div className="text-sm font-semibold text-text-primary capitalize">{decision.evidence_strength}</div>
          <p className="text-[10px] text-text-muted mt-1 font-mono">Verified Artifacts</p>
        </div>
      </div>

      <div className="space-y-2.5 pt-1">
        {decision.owner_summary && (
          <div className="bg-surface-subtle border border-surface-border rounded-md p-3">
            <p className="text-xs font-semibold text-brand-primary mb-1 flex items-center space-x-1.5 font-mono">
              <FileText className="h-3 w-3" />
              <span>Executive Summary</span>
            </p>
            <p className="text-xs text-text-primary leading-relaxed max-w-prose">{decision.owner_summary}</p>
          </div>
        )}

        {decision.rationale && (
          <div className="bg-canvas-base border border-surface-border rounded-md p-3">
            <p className="text-xs font-medium text-text-muted mb-1 font-mono">
              Agent Decision Rationale
            </p>
            <p className="text-xs text-text-secondary leading-relaxed max-w-prose font-mono text-[11px]">{decision.rationale}</p>
          </div>
        )}
      </div>
    </div>
  );
};
