import React from 'react';

interface StatusChipProps {
  status: string;
  size?: 'sm' | 'md';
}

export const StatusChip: React.FC<StatusChipProps> = ({ status, size = 'md' }) => {
  const normalized = (status || '').toLowerCase().trim();

  let label = status;
  let badgeStyle = 'bg-surface-subtle text-docket-text-secondary border-border';

  switch (normalized) {
    case 'won':
      label = '✓ Won';
      badgeStyle = 'bg-status-won/15 text-status-won border-status-won/30 font-semibold';
      break;
    case 'conceded':
    case 'charge_refunded':
      label = normalized === 'conceded' ? '⊘ Conceded' : 'Refunded';
      badgeStyle = 'bg-surface-subtle text-docket-text-muted border-border';
      break;
    case 'lost':
      label = 'Lost';
      badgeStyle = 'bg-status-action/15 text-status-action border-status-action/30 font-semibold';
      break;
    case 'needs_response':
      label = '⚠ Action Required';
      badgeStyle = 'bg-docket-gold/15 text-docket-gold border-docket-gold/40 font-semibold';
      break;
    case 'warning_needs_response':
      label = 'Inquiry (Pre-dispute)';
      badgeStyle = 'bg-status-inquiry/15 text-status-inquiry border-status-inquiry/30 font-semibold';
      break;
    case 'under_review':
      label = 'Under Review';
      badgeStyle = 'bg-status-review/15 text-status-review border-status-review/30';
      break;
    case 'approved':
      label = 'Approved';
      badgeStyle = 'bg-status-won/15 text-status-won border-status-won/30 font-semibold';
      break;
    case 'executed':
      label = 'Executed';
      badgeStyle = 'bg-docket-gold/15 text-docket-gold border-docket-gold/30 font-semibold';
      break;
    default:
      label = status;
  }

  const px = size === 'sm' ? 'px-1.5 py-0.5 text-[10px]' : 'px-2 py-0.5 text-[11px]';

  return (
    <span
      className={`inline-flex items-center font-mono rounded-xs border whitespace-nowrap tracking-tight ${badgeStyle} ${px}`}
    >
      <span>{label}</span>
    </span>
  );
};
