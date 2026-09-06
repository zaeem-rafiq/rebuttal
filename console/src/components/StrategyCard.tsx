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
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 text-center text-slate-400">
        <Target className="h-6 w-6 mx-auto mb-2 text-slate-600" />
        <p className="text-sm font-medium text-slate-200">Evaluation In Progress</p>
        <p className="text-xs text-slate-400 mt-1">Bedrock AgentCore Evidence Graph is currently analyzing evidence and computing win probability.</p>
      </div>
    );
  }

  const winProbPercent = Math.round(decision.win_probability * 100);
  const expectedValueFormatted = `$${(decision.expected_value_cents / 100).toFixed(2)}`;
  const disputeAmountFormatted = `$${(amountCents / 100).toFixed(2)}`;

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl shadow-black/20 space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <span className="text-[11px] uppercase font-semibold tracking-wider text-slate-400">
            Recommended Action
          </span>
          <h3 className="text-lg font-bold text-white uppercase tracking-tight flex items-center space-x-2 mt-0.5">
            <span>{decision.action.replace('_', ' ')}</span>
            <StatusChip status={decision.status} size="sm" />
          </h3>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-400">Customer Tier:</span>
          <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 uppercase">
            {decision.customer_value}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3.5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Win Probability</span>
            <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
          </div>
          <div className="text-xl font-bold text-white font-mono">{winProbPercent}%</div>
          <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
            <div
              className={`h-full rounded-full ${
                winProbPercent >= 70 ? 'bg-emerald-500' : winProbPercent >= 40 ? 'bg-amber-500' : 'bg-rose-500'
              }`}
              style={{ width: `${winProbPercent}%` }}
            />
          </div>
        </div>

        <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3.5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span className="flex items-center space-x-1">
              <span>Expected Value</span>
              <span
                title={`EV Model: (${winProbPercent}% × ${disputeAmountFormatted}) − $15.00 dispute fee = ${expectedValueFormatted}`}
                className="cursor-help text-slate-400 hover:text-indigo-300 transition-colors"
                aria-label={`Expected value calculation: ${winProbPercent}% times ${disputeAmountFormatted} minus $15 dispute fee`}
              >
                <Info className="h-3 w-3 inline" />
              </span>
            </span>
            <DollarSign className="h-3.5 w-3.5 text-indigo-400" />
          </div>
          <div className="text-xl font-bold text-indigo-300 font-mono">{expectedValueFormatted}</div>
          <p className="text-[10px] text-slate-400 mt-1">Dispute: {disputeAmountFormatted}</p>
        </div>

        <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3.5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Evidence Strength</span>
            <Award className="h-3.5 w-3.5 text-purple-400" />
          </div>
          <div className="text-base font-bold text-purple-300 capitalize">{decision.evidence_strength}</div>
          <p className="text-[10px] text-slate-400 mt-1">Proof grade: production</p>
        </div>
      </div>

      <div className="space-y-3 pt-2">
        {decision.owner_summary && (
          <div className="bg-indigo-950/30 border border-indigo-900/40 rounded-xl p-3.5">
            <p className="text-[11px] font-semibold text-indigo-300 uppercase tracking-wider mb-1 flex items-center space-x-1.5">
              <FileText className="h-3 w-3" />
              <span>Executive Summary</span>
            </p>
            <p className="text-xs text-slate-200 leading-relaxed">{decision.owner_summary}</p>
          </div>
        )}

        {decision.rationale && (
          <div className="bg-slate-950/50 border border-slate-800 rounded-xl p-3.5">
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
              Model Rationale
            </p>
            <p className="text-xs text-slate-300 leading-relaxed">{decision.rationale}</p>
          </div>
        )}
      </div>
    </div>
  );
};
