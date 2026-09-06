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
    <header className="border-b border-surface-border pb-5 mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div className="flex items-center space-x-3.5">
        <Link
          href="/"
          className="h-9 w-9 min-w-[44px] min-h-[44px] sm:h-8 sm:w-8 sm:min-w-0 sm:min-h-0 rounded-md bg-brand-primary/15 border border-brand-primary/40 flex items-center justify-center font-mono font-bold text-sm text-brand-primary shadow-xs hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary transition-all"
        >
          R
        </Link>
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <Link
              href="/"
              className="text-lg font-bold tracking-tight text-text-primary hover:text-brand-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary rounded min-h-[44px] sm:min-h-0 inline-flex items-center"
            >
              Rebuttal
            </Link>
            <span className="px-2 py-0.5 text-[11px] font-mono font-medium rounded bg-surface-subtle text-text-secondary border border-surface-border">
              Dispute Docket
            </span>
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 text-[11px] font-mono font-medium rounded bg-status-won-bg text-status-won-text border border-status-won-border">
              <span className="h-1.5 w-1.5 rounded-full bg-status-won-text shadow-xs" />
              <span>AgentCore Active</span>
            </span>
          </div>
          <p className="text-xs text-text-muted mt-0.5">
            Autonomous chargeback defense & carrier evidentiary synthesis
          </p>
        </div>
      </div>

      <div className="flex items-center space-x-3 text-xs text-text-muted">
        <div className="font-mono text-[11px] text-text-muted">
          Polling in <span className="tabular-nums font-semibold text-text-secondary">{secondsRemaining}s</span>
          {lastUpdated && (
            <span className="hidden md:inline text-text-muted ml-1.5">
              (Synced {lastUpdated.toLocaleTimeString()})
            </span>
          )}
        </div>

        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            title="Sync Ledger"
            aria-label="Sync Ledger"
            className="inline-flex items-center gap-1.5 bg-surface-subtle border border-surface-border hover:bg-surface-hover active:bg-surface-subtle disabled:opacity-50 text-text-primary px-3 py-2 sm:py-1.5 min-h-[44px] sm:min-h-0 rounded-md font-medium text-xs transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? 'animate-spin text-brand-primary' : 'text-text-muted'}`} />
            <span>{isRefreshing ? 'Syncing...' : 'Sync Ledger'}</span>
          </button>
        )}
      </div>
    </header>
  );
};
