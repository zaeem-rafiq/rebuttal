'use client';

import React from 'react';
import Link from 'next/link';
import { ShieldAlert, RefreshCw, Activity } from 'lucide-react';

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
    <header className="border-b border-slate-800/80 pb-5 mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div className="flex items-center space-x-3.5">
        <div className="h-10 w-10 rounded-xl bg-slate-900 border border-slate-700/80 flex items-center justify-center shadow-md shadow-black/40 ring-1 ring-white/5">
          <ShieldAlert className="h-5 w-5 text-indigo-400" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <Link href="/" className="text-xl font-bold tracking-tight text-white hover:text-indigo-400 transition-colors">
              Rebuttal
            </Link>
            <span className="px-2 py-0.5 text-xs font-semibold uppercase tracking-wider rounded-full bg-slate-800 text-slate-300 border border-slate-700">
              Risk Operations Console
            </span>
            <span className="flex items-center space-x-1 px-2 py-0.5 text-xs font-medium rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>AgentCore Live</span>
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Autonomous Chargeback Defense · AWS Bedrock AgentCore & Strands SDK
          </p>
        </div>
      </div>

      <div className="flex items-center space-x-3 text-xs text-slate-400">
        <div className="flex items-center space-x-1.5 bg-slate-900/80 border border-slate-800 px-3 py-1.5 rounded-lg">
          <Activity className="h-3.5 w-3.5 text-indigo-400" />
          <span>Polling: <strong className="text-slate-200">{secondsRemaining}s</strong></span>
        </div>

        {lastUpdated && (
          <span className="hidden md:inline-block text-slate-500">
            Updated {lastUpdated.toLocaleTimeString()}
          </span>
        )}

        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            title="Refresh disputes now"
            aria-label="Refresh disputes now"
            className="flex items-center space-x-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 px-3 py-1.5 rounded-lg border border-slate-700/60 transition-colors"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? 'animate-spin text-indigo-400' : ''}`} />
            <span>{isRefreshing ? 'Refreshing...' : 'Refresh'}</span>
          </button>
        )}
      </div>
    </header>
  );
};
