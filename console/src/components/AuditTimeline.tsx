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
        label: 'Bedrock AgentCore',
        icon: Bot,
        color: 'bg-status-submitted-bg text-status-submitted-text border-status-submitted-border',
      };
    }
    if (act.includes('stripe')) {
      return {
        label: 'Stripe API',
        icon: CreditCard,
        color: 'bg-status-won-bg text-status-won-text border-status-won-border',
      };
    }
    if (act.includes('twilio') || act.includes('sms')) {
      return {
        label: 'Twilio Gateway',
        icon: MessageSquare,
        color: 'bg-status-review-bg text-status-review-text border-status-review-border',
      };
    }
    return {
      label: actor || 'System Engine',
      icon: Terminal,
      color: 'bg-surface-subtle text-text-secondary border-surface-border',
    };
  };

  if (!entries || entries.length === 0) {
    return (
      <div className="bg-surface-card border border-surface-border rounded-lg p-6 text-center text-text-muted">
        <Clock className="h-5 w-5 mx-auto mb-2 text-text-muted" />
        <p className="text-xs font-medium text-text-secondary">No evidentiary actions recorded yet</p>
        <p className="text-[11px] text-text-muted mt-1 max-w-sm mx-auto">
          Audit telemetry registers synchronously as AWS Bedrock AgentCore processes evidence packets.
        </p>
      </div>
    );
  }

  return (
    <div className="relative pl-5 space-y-3 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-px before:bg-surface-border">
      {entries.map((entry, index) => {
        const { label, icon: Icon, color } = getActorBadge(entry.actor);
        const isExpanded = expandedId === entry.id || (index === 0 && expandedId === null);
        const hasDetails = entry.details && Object.keys(entry.details).length > 0;

        return (
          <div key={entry.id || index} className="relative">
            {/* Timeline node */}
            <div className="absolute -left-[21px] top-2 h-2.5 w-2.5 rounded-full bg-canvas-base border-2 border-brand-primary" />

            <div className="bg-surface-card border border-surface-border rounded-lg p-3 text-xs transition-colors hover:border-surface-border-strong">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center space-x-2">
                  <span className={`inline-flex items-center space-x-1 px-1.5 py-0.5 rounded border text-[10px] font-mono font-medium ${color}`}>
                    <Icon className="h-2.5 w-2.5" />
                    <span>{label}</span>
                  </span>
                  <span className="font-mono text-xs font-medium text-text-primary">{entry.action}</span>
                </div>
                <span className="text-text-muted font-mono text-[11px] tabular-nums">
                  {new Date(entry.created_at).toLocaleTimeString()}
                </span>
              </div>

              {hasDetails && (
                <div className="mt-2.5 pt-2 border-t border-surface-border">
                  <button
                    type="button"
                    onClick={() => setExpandedId(isExpanded ? '' : entry.id)}
                    className="flex items-center space-x-1 text-[11px] text-text-muted hover:text-text-primary font-mono transition-colors"
                  >
                    <span>{isExpanded ? 'Hide Payload' : 'Inspect Payload'}</span>
                    {isExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                  </button>

                  {isExpanded && (
                    <pre className="mt-2 p-2.5 rounded bg-canvas-base text-text-secondary font-mono text-[11px] overflow-x-auto border border-surface-border leading-relaxed">
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
