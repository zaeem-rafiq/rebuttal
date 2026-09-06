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
        color: 'bg-docket-gold/15 text-docket-gold border-docket-gold/30',
      };
    }
    if (act.includes('stripe')) {
      return {
        label: 'Stripe API',
        icon: CreditCard,
        color: 'bg-status-won/15 text-status-won border-status-won/30',
      };
    }
    if (act.includes('twilio') || act.includes('sms')) {
      return {
        label: 'Twilio Gateway',
        icon: MessageSquare,
        color: 'bg-status-review/15 text-status-review border-status-review/30',
      };
    }
    return {
      label: actor || 'System Engine',
      icon: Terminal,
      color: 'bg-surface-elevated text-docket-text-muted border-border',
    };
  };

  if (!entries || entries.length === 0) {
    return (
      <div className="bg-surface border border-border rounded-xs p-6 text-center text-docket-text-muted">
        <Clock className="h-6 w-6 mx-auto mb-2 text-docket-gold/60" />
        <p className="text-xs font-serif font-medium text-docket-text">No Evidentiary Telemetry Recorded</p>
        <p className="text-[11px] text-docket-text-muted mt-1 font-mono">
          Audit telemetry registers synchronously as AWS Bedrock AgentCore compiles evidence packets.
        </p>
      </div>
    );
  }

  return (
    <div className="relative pl-5 space-y-3 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-px before:bg-border">
      {entries.map((entry, index) => {
        const { label, icon: Icon, color } = getActorBadge(entry.actor);
        const isExpanded = expandedId === entry.id || (index === 0 && expandedId === null);
        const hasDetails = entry.details && Object.keys(entry.details).length > 0;

        return (
          <div key={entry.id || index} className="relative">
            {/* Timeline node */}
            <div className="absolute -left-[21px] top-2 h-2.5 w-2.5 rounded-full bg-canvas border-2 border-docket-gold" />

            <div className="bg-surface border border-border rounded-xs p-3 text-xs transition-colors hover:border-docket-gold/40">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center space-x-2">
                  <span className={`inline-flex items-center space-x-1 px-1.5 py-0.5 rounded-xs border text-[10px] font-mono font-medium ${color}`}>
                    <Icon className="h-2.5 w-2.5" />
                    <span>{label}</span>
                  </span>
                  <span className="font-mono text-xs font-semibold text-docket-text">{entry.action}</span>
                </div>
                <span className="text-docket-text-muted font-mono text-[11px] tabular-nums">
                  {new Date(entry.created_at).toLocaleTimeString()}
                </span>
              </div>

              {hasDetails && (
                <div className="mt-2.5 pt-2 border-t border-border/80">
                  <button
                    type="button"
                    onClick={() => setExpandedId(isExpanded ? '' : entry.id)}
                    className="flex items-center space-x-1 text-[11px] text-docket-gold hover:text-docket-gold-light font-mono transition-colors"
                  >
                    <span>{isExpanded ? 'Hide Payload' : 'Inspect Payload'}</span>
                    {isExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                  </button>

                  {isExpanded && (
                    <pre className="mt-2 p-2.5 rounded-xs bg-canvas text-docket-text-secondary font-mono text-[11px] overflow-x-auto border border-border leading-relaxed">
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
