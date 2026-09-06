'use client';

import React from 'react';

export type StampDecision = 'won' | 'lost' | 'approved' | 'fought' | 'conceded' | 'refunded';

interface StampProps {
  decision?: StampDecision | string;
  variant?: StampDecision | string;
  text?: string;
  actor?: 'agent' | 'owner' | 'issuer';
  timestamp?: string | Date;
  channel?: string;
  animate?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const Stamp: React.FC<StampProps> = ({
  decision,
  variant,
  text,
  actor = 'agent',
  timestamp,
  channel,
  animate = false,
  size = 'md',
  className = '',
}) => {
  const normDecision = (decision || variant || '').toLowerCase().trim();
  const rawText = (text || '').toLowerCase().trim();

  const isGreen =
    ['won', 'approved', 'fought'].includes(normDecision) ||
    rawText.includes('won') ||
    rawText.includes('approved') ||
    rawText.includes('fought');

  const colorClass = isGreen
    ? 'border-decision-green text-decision-green'
    : 'border-decision-red text-decision-red';

  let label = text || '';
  if (!label) {
    let timeStr = '';
    if (timestamp) {
      const d = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
      if (!isNaN(d.getTime())) {
        const day = String(d.getDate()).padStart(2, '0');
        const month = d.toLocaleString('en-US', { month: 'short' }).toUpperCase();
        const hours = String(d.getHours()).padStart(2, '0');
        const mins = String(d.getMinutes()).padStart(2, '0');
        timeStr = ` · ${day} ${month} ${hours}:${mins}`;
      }
    }

    const byStr =
      actor === 'owner'
        ? channel
          ? ` · BY OWNER (${channel.toUpperCase()})`
          : ' · BY OWNER (SMS)'
        : actor === 'issuer'
        ? ' · BY ISSUER'
        : ' · BY AGENT';

    const actionStr = normDecision.toUpperCase();
    label = `${actionStr}${timeStr}${byStr}`;
  }


  const sizeClasses = {
    sm: 'text-[11px] px-1.5 py-0.5 border-[1.5px]',
    md: 'text-xs px-2.5 py-1 border-2',
    lg: 'text-sm px-3.5 py-1.5 border-2',
  }[size];

  return (
    <div
      role="status"
      aria-label={`Outcome: ${label}`}
      className={`inline-block font-mono font-bold tracking-wider uppercase rounded-stamp select-none transform -rotate-[2deg] ${colorClass} ${sizeClasses} ${
        animate ? 'animate-stamp' : ''
      } ${className}`}
      style={{
        boxShadow: 'none',
      }}
    >
      {label}
    </div>
  );
};
