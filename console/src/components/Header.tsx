'use client';

import React from 'react';
import Link from 'next/link';
import { RefreshCw, Scale } from 'lucide-react';

interface HeaderProps {
  lastUpdated?: Date | null;
  isRefreshing?: boolean;
  onRefresh?: () => void;
  secondsRemaining?: number;
  activeCount?: number;
  volumeWonFormatted?: string;
  winRateFormatted?: string;
}

export const Header: React.FC<HeaderProps> = ({
  lastUpdated,
  isRefreshing = false,
  onRefresh,
  secondsRemaining = 5,
  activeCount = 3,
  volumeWonFormatted = '$388.00',
  winRateFormatted = '88.5%',
}) => {
  return (
    <header className="border-b border-border pb-5 mb-6 flex flex-col lg:flex-row lg:items-end justify-between gap-4">
      {/* Title & Folio Identity */}
      <div className="flex items-start space-x-3.5">
        <Link
          href="/"
          className="h-10 w-10 min-w-[44px] min-h-[44px] rounded-xs bg-surface-elevated border border-docket-gold/40 flex items-center justify-center font-mono font-bold text-sm text-docket-gold hover:border-docket-gold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-docket-gold"
          title="Return to Magistrate Docket"
          aria-label="Return to Magistrate Docket"
        >
          <Scale className="h-5 w-5" />
        </Link>
        <div>
          <div className="text-[10px] font-mono font-bold uppercase tracking-[0.16em] text-docket-gold">
            Magistrate Record // Rebuttal Arbitration Core
          </div>
          <h1 className="text-2xl sm:text-3xl font-serif font-medium tracking-tight text-docket-text mt-0.5">
            <Link href="/" className="hover:text-docket-gold transition-colors">
              Dispute Docket &amp; <em className="italic text-docket-gold font-serif">Evidence Triage</em>
            </Link>
          </h1>
          <p className="text-xs text-docket-text-muted mt-1 font-sans">
            Autonomous chargeback defense, scheme arbitration, &amp; carrier evidentiary synthesis
          </p>
        </div>
      </div>

      {/* Meta Stream & Live Sync Controls */}
      <div className="flex flex-wrap items-center gap-3 text-xs font-mono">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xs bg-surface-subtle border border-border text-docket-text-secondary text-[11px]">
          <span className="h-2 w-2 rounded-full bg-status-won shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
          <span>BEDROCK AGENTCORE ACTIVE</span>
        </div>

        <div className="text-[11px] text-docket-text-muted">
          Auto-sync in <span className="tabular-nums font-semibold text-docket-text font-mono">{secondsRemaining}s</span>
          {lastUpdated && (
            <span className="hidden sm:inline text-docket-text-subtle ml-1">
              ({lastUpdated.toLocaleTimeString()})
            </span>
          )}
        </div>

        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            title="Synchronize Docket Ledger"
            aria-label="Synchronize Docket Ledger"
            className="inline-flex items-center gap-1.5 bg-surface-elevated border border-border hover:border-docket-gold/60 active:bg-surface-subtle disabled:opacity-50 text-docket-text px-3 py-1.5 min-h-[44px] sm:min-h-0 rounded-xs font-mono text-xs transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-docket-gold"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? 'animate-spin text-docket-gold' : 'text-docket-text-muted'}`} />
            <span>{isRefreshing ? 'Syncing...' : 'Sync Docket'}</span>
          </button>
        )}
      </div>
    </header>
  );
};
