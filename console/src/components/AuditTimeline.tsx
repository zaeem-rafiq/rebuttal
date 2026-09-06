'use client';

import React, { useState } from 'react';
import { AuditLogEntry } from '@/lib/types';
import { Terminal, Bot, CreditCard, MessageSquare, ChevronDown, ChevronUp, Clock } from 'lucide-react';

interface AuditTimelineProps {
  entries: AuditLogEntry[];
}

export const AuditTimeline: React.FC<AuditTimelineProps> = ({ entries }) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const getActorBadge = (actor: string) => {
    const act = (actor || '').toLowerCase();
    if (act.includes('agent') || act.includes('bedrock') || act.includes('strands')) {
      return {
        label: 'Bedrock Agent',
        icon: Bot,
        color: 'bg-purple-950/60 text-purple-300 border-purple-800/50',
      };
    }
    if (act.includes('stripe')) {
      return {
        label: 'Stripe Webhook',
        icon: CreditCard,
        color: 'bg-blue-950/60 text-blue-300 border-blue-800/50',
      };
    }
    if (act.includes('twilio') || act.includes('sms')) {
      return {
        label: 'Twilio SMS',
        icon: MessageSquare,
        color: 'bg-emerald-950/60 text-emerald-300 border-emerald-800/50',
      };
    }
    return {
      label: actor || 'System',
      icon: Terminal,
      color: 'bg-slate-800 text-slate-300 border-slate-700',
    };
  };

  if (!entries || entries.length === 0) {
    return (
      <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 text-center text-slate-400">
        <Clock className="h-6 w-6 mx-auto mb-2 text-slate-600" />
        <p className="text-sm font-medium text-slate-300">No audit logs recorded for this dispute yet.</p>
        <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
          Audit telemetry will populate automatically as AWS Bedrock AgentCore processes evidence and triggers defense tools.
        </p>
      </div>
    );
  }

  return (
    <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
      {entries.map((entry, index) => {
        const { label, icon: Icon, color } = getActorBadge(entry.actor);
        const isExpanded = expandedId === entry.id || (index === 0 && expandedId === null);
        const hasDetails = entry.details && Object.keys(entry.details).length > 0;

        return (
          <div key={entry.id || index} className="relative">
            <div className="absolute -left-[27px] top-1.5 h-3.5 w-3.5 rounded-full bg-slate-950 border-2 border-indigo-500 shadow-sm shadow-indigo-500/50" />

            <div className="bg-slate-900/80 border border-slate-800/90 rounded-xl p-3.5 text-xs transition-colors hover:border-slate-700">
              <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                <div className="flex items-center space-x-2">
                  <span className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded-md border text-[11px] font-medium ${color}`}>
                    <Icon className="h-3 w-3" />
                    <span>{label}</span>
                  </span>
                  <span className="font-semibold text-slate-200">{entry.action}</span>
                </div>
                <span className="text-slate-500 font-mono text-[11px]">
                  {new Date(entry.created_at).toLocaleTimeString()}
                </span>
              </div>

              {hasDetails && (
                <div className="mt-2">
                  <button
                    type="button"
                    onClick={() => setExpandedId(isExpanded ? '' : entry.id)}
                    className="flex items-center space-x-1 text-[11px] text-slate-400 hover:text-slate-200 font-mono"
                  >
                    <span>{isExpanded ? 'Hide Payload' : 'View Payload'}</span>
                    {isExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                  </button>

                  {isExpanded && (
                    <pre className="mt-2 p-2.5 rounded-lg bg-slate-950 text-slate-300 font-mono text-[11px] overflow-x-auto border border-slate-800/80 leading-relaxed">
                      {JSON.stringify(entry.details, null, 2)}
                    </pre>
                  )}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};
