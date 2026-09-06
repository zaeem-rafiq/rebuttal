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
      <div className="bg-surface border border-border rounded-xs p-6 text-center text-docket-text-muted">
        <Target className="h-6 w-6 mx-auto mb-2 text-docket-gold/60" />
        <p className="text-xs font-serif font-medium text-docket-text">Evidentiary Evaluation in Progress</p>
        <p className="text-[11px] text-docket-text-muted mt-1 font-mono">Bedrock AgentCore Evidence Graph is compiling carrier dockets &amp; computing win probability.</p>
      </div>
    );
  }

  const winProbPercent = Math.round(decision.win_probability * 100);
  const expectedValueFormatted = `$${(decision.expected_value_cents / 100).toFixed(2)}`;
  const disputeAmountFormatted = `$${(amountCents / 100).toFixed(2)}`;

  return (
    <div className="bg-surface border border-border rounded-xs p-5 space-y-4 shadow-xs">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-3.5">
        <div>
          <span className="text-xs font-mono font-medium text-docket-text-muted uppercase tracking-wider">
            Magistrate Arbitration Strategy
          </span>
          <h3 className="text-lg font-serif font-medium text-docket-text flex items-center space-x-2 mt-0.5 capitalize">
            <span>{decision.action.replace('_', ' ')}</span>
            <StatusChip status={decision.status} size="sm" />
          </h3>
        </div>

        <div className="flex items-center space-x-2 font-mono">
          <span className="text-[11px] text-docket-text-muted">Customer Tier:</span>
          <span className="px-2 py-0.5 rounded-xs text-[10px] font-bold bg-surface-elevated text-docket-gold border border-docket-gold/30 uppercase">
            {decision.customer_value}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {/* Win Probability */}
        <div className="bg-surface-subtle border border-border rounded-xs p-3.5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-[11px] text-docket-text-muted mb-1 font-mono">
            <span>Win Probability</span>
            <TrendingUp className="h-3.5 w-3.5 text-status-won" />
          </div>
          <div className="text-2xl font-bold text-docket-text font-mono tabular-nums">{winProbPercent}%</div>
          <div className="w-full bg-surface-elevated h-1.5 rounded-xs mt-2 overflow-hidden border border-border">
            <div
              className={`h-full rounded-xs ${
                winProbPercent >= 70 ? 'bg-status-won' : winProbPercent >= 40 ? 'bg-docket-gold' : 'bg-status-action'
              }`}
              style={{ width: `${winProbPercent}%` }}
            />
          </div>
        </div>

        {/* Expected Value */}
        <div className="bg-surface-subtle border border-border rounded-xs p-3.5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-[11px] text-docket-text-muted mb-1 font-mono">
            <span className="flex items-center space-x-1">
              <span>Expected Value</span>
              <span
                title={`EV Model: (${winProbPercent}% × ${disputeAmountFormatted}) − $15.00 scheme fee = ${expectedValueFormatted}`}
                className="cursor-help text-docket-text-muted hover:text-docket-gold transition-colors"
                aria-label={`Expected value calculation: ${winProbPercent}% times ${disputeAmountFormatted} minus $15 fee`}
              >
                <Info className="h-3 w-3 inline" />
              </span>
            </span>
            <DollarSign className="h-3.5 w-3.5 text-docket-gold" />
          </div>
          <div className="text-2xl font-bold text-docket-gold font-mono tabular-nums">{expectedValueFormatted}</div>
          <p className="text-[10px] text-docket-text-muted mt-1 font-mono">At-risk claim: {disputeAmountFormatted}</p>
        </div>

        {/* Evidence Strength */}
        <div className="bg-surface-subtle border border-border rounded-xs p-3.5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-[11px] text-docket-text-muted mb-1 font-mono">
            <span>Evidence Strength</span>
            <Award className="h-3.5 w-3.5 text-status-won" />
          </div>
          <div className="text-base font-bold text-docket-text capitalize font-mono">{decision.evidence_strength}</div>
          <p className="text-[10px] text-docket-text-muted mt-1 font-mono">Verified Carrier Artifacts</p>
        </div>
      </div>

      <div className="space-y-2.5 pt-1">
        {decision.owner_summary && (
          <div className="bg-surface-elevated border border-border rounded-xs p-3.5">
            <p className="text-xs font-mono font-bold uppercase tracking-wider text-docket-gold mb-1.5 flex items-center space-x-1.5">
              <FileText className="h-3.5 w-3.5" />
              <span>Magistrate Executive Summary</span>
            </p>
            <p className="text-sm font-serif text-docket-text-secondary leading-relaxed max-w-prose">
              {decision.owner_summary}
            </p>
          </div>
        )}

        {decision.rationale && (
          <div className="bg-canvas border border-border rounded-xs p-3">
            <p className="text-[10px] font-mono font-bold uppercase tracking-wider text-docket-text-muted mb-1">
              Bedrock Agent Reasoning &amp; Policy Chain
            </p>
            <p className="text-xs text-docket-text-muted leading-relaxed font-mono">
              {decision.rationale}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
