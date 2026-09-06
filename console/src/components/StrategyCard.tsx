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
      <div className="bg-surface border border-border rounded-lg p-6 text-center text-slate-400">
        <Target className="h-5 w-5 mx-auto mb-2 text-slate-500" />
        <p className="text-xs font-semibold text-slate-200">Evaluation In Progress</p>
        <p className="text-[11px] text-slate-400 mt-1">Bedrock AgentCore Evidence Graph is analyzing carrier dockets & computing win probability.</p>
      </div>
    );
  }

  const winProbPercent = Math.round(decision.win_probability * 100);
  const expectedValueFormatted = `$${(decision.expected_value_cents / 100).toFixed(2)}`;
  const disputeAmountFormatted = `$${(amountCents / 100).toFixed(2)}`;

  return (
    <div className="bg-surface border border-border rounded-lg p-5 space-y-4 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-3.5">
        <div>
          <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
            Recommended Action
          </span>
          <h3 className="text-base font-bold text-white uppercase tracking-tight flex items-center space-x-2 mt-0.5">
            <span>{decision.action.replace('_', ' ')}</span>
            <StatusChip status={decision.status} size="sm" />
          </h3>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-[11px] text-slate-400">Customer Tier:</span>
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-surface-elevated text-slate-200 border border-border uppercase">
            {decision.customer_value}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="bg-[#0b0f17] border border-border rounded-md p-3 flex flex-col justify-between">
          <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
            <span>Win Probability</span>
            <TrendingUp className="h-3 w-3 text-emerald-400" />
          </div>
          <div className="text-xl font-bold text-white font-mono tabular-nums">{winProbPercent}%</div>
          <div className="w-full bg-[#1f2937] h-1.5 rounded-full mt-2 overflow-hidden">
            <div
              className={`h-full rounded-full ${
                winProbPercent >= 70 ? 'bg-emerald-500' : winProbPercent >= 40 ? 'bg-amber-500' : 'bg-rose-500'
              }`}
              style={{ width: `${winProbPercent}%` }}
            />
          </div>
        </div>

        <div className="bg-[#0b0f17] border border-border rounded-md p-3 flex flex-col justify-between">
          <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
            <span className="flex items-center space-x-1">
              <span>Expected Value</span>
              <span
                title={`EV Model: (${winProbPercent}% × ${disputeAmountFormatted}) − $15.00 dispute fee = ${expectedValueFormatted}`}
                className="cursor-help text-slate-400 hover:text-blue-400 transition-colors"
                aria-label={`Expected value calculation: ${winProbPercent}% times ${disputeAmountFormatted} minus $15 dispute fee`}
              >
                <Info className="h-3 w-3 inline" />
              </span>
            </span>
            <DollarSign className="h-3 w-3 text-blue-400" />
          </div>
          <div className="text-xl font-bold text-blue-300 font-mono tabular-nums">{expectedValueFormatted}</div>
          <p className="text-[10px] text-slate-400 mt-1 font-mono">Dispute: {disputeAmountFormatted}</p>
        </div>

        <div className="bg-[#0b0f17] border border-border rounded-md p-3 flex flex-col justify-between">
          <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
            <span>Evidence Strength</span>
            <Award className="h-3 w-3 text-blue-400" />
          </div>
          <div className="text-sm font-bold text-slate-200 capitalize">{decision.evidence_strength}</div>
          <p className="text-[10px] text-slate-400 mt-1">Proof grade: Production Verified</p>
        </div>
      </div>

      <div className="space-y-2.5 pt-1">
        {decision.owner_summary && (
          <div className="bg-surface-elevated border border-border rounded-md p-3">
            <p className="text-[10px] font-bold text-blue-300 uppercase tracking-wider mb-1 flex items-center space-x-1.5">
              <FileText className="h-3 w-3" />
              <span>Executive Summary</span>
            </p>
            <p className="text-xs text-slate-200 leading-relaxed max-w-prose">{decision.owner_summary}</p>
          </div>
        )}

        {decision.rationale && (
          <div className="bg-[#0b0f17] border border-border rounded-md p-3">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
              Agent Decision Rationale
            </p>
            <p className="text-xs text-slate-300 leading-relaxed max-w-prose">{decision.rationale}</p>
          </div>
        )}
      </div>
    </div>
  );
};
