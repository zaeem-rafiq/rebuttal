import React from 'react';

interface StatusChipProps {
  status: string;
  size?: 'sm' | 'md';
}

export const StatusChip: React.FC<StatusChipProps> = ({ status, size = 'md' }) => {
  const normalized = (status || '').toLowerCase().trim();

  let label = status;
  let badgeStyle = 'bg-surface-elevated text-slate-300 border-border';

  switch (normalized) {
    case 'won':
      label = 'Won';
      badgeStyle = 'bg-[#064e3b]/80 text-[#34d399] border-[#059669]/60';
      break;
    case 'conceded':
    case 'charge_refunded':
      label = normalized === 'conceded' ? 'Conceded' : 'Refunded';
      badgeStyle = 'bg-[#311317]/80 text-[#fca5a5] border-[#991b1b]/60';
      break;
    case 'lost':
      label = 'Lost';
      badgeStyle = 'bg-[#450a0a]/80 text-[#fca5a5] border-[#dc2626]/60';
      break;
    case 'needs_response':
      label = 'Approval Needed';
      badgeStyle = 'bg-[#311317] text-[#f87171] border-[#991b1b]';
      break;
    case 'warning_needs_response':
      label = 'Inquiry (Pre-dispute)';
      badgeStyle = 'bg-[#271c08] text-[#fbbf24] border-[#78350f]';
      break;
    case 'under_review':
      label = 'Under Review';
      badgeStyle = 'bg-[#161e2e] text-[#93c5fd] border-[#2563eb]/40';
      break;
    case 'approved':
      label = 'Approved';
      badgeStyle = 'bg-[#172554]/80 text-[#93c5fd] border-[#1d4ed8]/60';
      break;
    case 'executed':
      label = 'Executed';
      badgeStyle = 'bg-[#1e1b4b]/80 text-[#c7d2fe] border-[#4338ca]/60';
      break;
    default:
      label = status;
  }

  const px = size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-0.5 text-[11px]';

  return (
    <span
      className={`inline-flex items-center font-mono font-medium rounded border whitespace-nowrap ${badgeStyle} ${px}`}
    >
      <span>{label}</span>
    </span>
  );
};
