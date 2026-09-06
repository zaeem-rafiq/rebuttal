'use client';

import React from 'react';
import Link from 'next/link';

interface HeaderProps {
  activeScenario?: 'S1' | 'S2' | 'S3' | null;
  onSelectScenario?: (scenario: 'S1' | 'S2' | 'S3') => void;
  loadingScenario?: string | null;
  cooldown?: number;
  lastUpdated?: Date | null;
  isRefreshing?: boolean;
  onRefresh?: () => void;
  secondsRemaining?: number;
}


export const Header: React.FC<HeaderProps> = ({
  activeScenario = 'S2',
  onSelectScenario,
  loadingScenario = null,
  cooldown = 0,
}) => {
  return (
    <header className="border-b border-rule pb-3 mb-8 flex flex-col sm:flex-row sm:items-baseline justify-between gap-3">
      <div className="flex items-baseline gap-4">
        <Link href="/" className="text-lg font-medium text-ink tracking-tight underline">
          Rebuttal
        </Link>
        <span className="text-xs font-mono text-secondary-ink">
          Autonomous chargeback defense
        </span>
      </div>

      <div className="text-xs font-mono flex items-center gap-2 text-secondary-ink">
        <span>Scenario:</span>
        {(['S1', 'S2', 'S3'] as const).map((sc, idx) => (
          <React.Fragment key={sc}>
            {idx > 0 && <span>·</span>}
            <button
              type="button"
              onClick={() => onSelectScenario?.(sc)}
              disabled={loadingScenario !== null || cooldown > 0}
              className={`hover:text-ink disabled:opacity-50 transition-colors ${
                activeScenario === sc ? 'underline font-semibold text-ink' : ''
              }`}
            >
              {sc}
            </button>
          </React.Fragment>
        ))}
        {loadingScenario && (
          <span className="text-xs font-mono text-secondary-ink ml-1 italic">
            injecting {loadingScenario}…
          </span>
        )}
        {cooldown > 0 && !loadingScenario && (
          <span className="text-xs font-mono text-secondary-ink ml-1 tabular-nums">
            ({cooldown}s)
          </span>
        )}
      </div>
    </header>
  );
};

