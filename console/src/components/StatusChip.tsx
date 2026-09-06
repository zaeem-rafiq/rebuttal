import React from 'react';

interface StatusChipProps {
  status: string;
  size?: 'sm' | 'md';
}

export const StatusChip: React.FC<StatusChipProps> = ({ status, size = 'md' }) => {
  const normalized = (status || '').toLowerCase().trim();

  let label = status;
  let badgeStyle = 'bg-surface-subtle text-text-secondary border-surface-border';

  switch (normalized) {
    case 'won':
      label = 'Won';
      badgeStyle = 'bg-status-won-bg text-status-won-text border-status-won-border';
      break;
    case 'conceded':
    case 'charge_refunded':
      label = normalized === 'conceded' ? 'Conceded' : 'Refunded';
      badgeStyle = 'bg-status-lost-bg text-status-lost-text border-status-lost-border';
      break;
    case 'lost':
      label = 'Lost';
      badgeStyle = 'bg-status-lost-bg text-status-lost-text border-status-lost-border';
      break;
    case 'needs_response':
      label = 'Approval Needed';
      badgeStyle = 'bg-status-review-bg text-status-review-text border-status-review-border';
      break;
    case 'warning_needs_response':
      label = 'Inquiry (Pre-dispute)';
      badgeStyle = 'bg-status-review-bg text-status-review-text border-status-review-border';
      break;
    case 'under_review':
      label = 'Under Review';
      badgeStyle = 'bg-status-submitted-bg text-status-submitted-text border-status-submitted-border';
      break;
    case 'approved':
      label = 'Approved';
      badgeStyle = 'bg-status-submitted-bg text-status-submitted-text border-status-submitted-border';
      break;
    case 'executed':
      label = 'Executed';
      badgeStyle = 'bg-brand-primary/15 text-brand-primary border-brand-primary/30';
      break;
    default:
      label = status;
  }

  const px = size === 'sm' ? 'px-1.5 py-0.5 text-[10px]' : 'px-2 py-0.5 text-[11px]';

  return (
    <span
      className={`inline-flex items-center font-mono font-medium rounded border whitespace-nowrap ${badgeStyle} ${px}`}
    >
      <span>{label}</span>
    </span>
  );
};
