'use client';

import React from 'react';
import Link from 'next/link';
import { RefreshCw } from 'lucide-react';

interface HeaderProps {
  lastUpdated?: Date | null;
  isRefreshing?: boolean;
  onRefresh?: () => void;
  secondsRemaining?: number;
}

export const Header: React.FC<HeaderProps> = ({
  lastUpdated,
  isRefreshing = false,
  onRefresh,
  secondsRemaining = 5,
}) => {
  return (
    <header className="border-b border-border pb-5 mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div className="flex items-center space-x-3.5">
        <Link
          href="/"
          className="h-8 w-8 rounded-md bg-[#1e3a8a] border border-[#2563eb] flex items-center justify-center font-mono font-bold text-sm text-[#93c5fd] shadow-sm hover:brightness-110 transition-all"
        >
          R
        </Link>
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <Link
              href="/"
              className="text-lg font-bold tracking-tight text-white hover:text-blue-400 transition-colors"
            >
              Rebuttal
            </Link>
            <span className="px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded bg-[#161e2e] text-slate-300 border border-[#283548]">
              Dispute Docket
            </span>
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 text-[10px] font-semibold rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800/60">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_#34d399]" />
              <span>Bedrock AgentCore Active</span>
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Autonomous chargeback defense & carrier evidentiary synthesis
          </p>
        </div>
      </div>

      <div className="flex items-center space-x-3 text-xs text-slate-400">
        <div className="font-mono text-[11px] text-slate-400">
          Polling in <span className="tabular-nums font-semibold text-slate-200">{secondsRemaining}s</span>
          {lastUpdated && (
            <span className="hidden md:inline text-slate-500 ml-1.5">
              · Sync: {lastUpdated.toLocaleTimeString()}
            </span>
          )}
        </div>

        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            title="Sync Ledger"
            aria-label="Sync Ledger"
            className="inline-flex items-center gap-1.5 bg-surface border border-border hover:bg-surface-elevated active:bg-surface-highlight disabled:opacity-50 text-slate-200 px-3 py-1.5 rounded-md font-medium text-xs transition-colors focus-visible:ring-2 focus-visible:ring-brand"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? 'animate-spin text-blue-400' : 'text-slate-400'}`} />
            <span>{isRefreshing ? 'Syncing...' : 'Sync Ledger'}</span>
          </button>
        )}
      </div>
    </header>
  );
};
