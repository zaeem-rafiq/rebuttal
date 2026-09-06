import React from 'react';
import { CheckCircle2, XCircle, Clock, AlertTriangle, HelpCircle } from 'lucide-react';

interface StatusChipProps {
  status: string;
  size?: 'sm' | 'md';
}

export const StatusChip: React.FC<StatusChipProps> = ({ status, size = 'md' }) => {
  const normalized = (status || '').toLowerCase().trim();

  let label = status;
  let bgClass = 'bg-slate-800 text-slate-300 border-slate-700';
  let Icon = HelpCircle;

  switch (normalized) {
    case 'won':
      label = 'Won';
      bgClass = 'bg-emerald-950/80 text-emerald-300 border-emerald-700/50 shadow-sm shadow-emerald-900/30';
      Icon = CheckCircle2;
      break;
    case 'conceded':
    case 'charge_refunded':
      label = normalized === 'conceded' ? 'Conceded' : 'Refunded';
      bgClass = 'bg-rose-950/70 text-rose-300 border-rose-800/50';
      Icon = XCircle;
      break;
    case 'lost':
      label = 'Lost';
      bgClass = 'bg-red-950/80 text-red-300 border-red-800/50';
      Icon = XCircle;
      break;
    case 'needs_response':
      label = 'Pending Decision';
      bgClass = 'bg-amber-950/80 text-amber-300 border-amber-700/50 animate-pulse';
      Icon = AlertTriangle;
      break;
    case 'warning_needs_response':
      label = 'Inquiry (Pre-dispute)';
      bgClass = 'bg-yellow-950/80 text-yellow-300 border-yellow-700/50';
      Icon = AlertTriangle;
      break;
    case 'under_review':
      label = 'Under Review';
      bgClass = 'bg-sky-950/80 text-sky-300 border-sky-700/50';
      Icon = Clock;
      break;
    case 'approved':
      label = 'Approved';
      bgClass = 'bg-blue-950/80 text-blue-300 border-blue-700/50';
      Icon = CheckCircle2;
      break;
    case 'executed':
      label = 'Executed';
      bgClass = 'bg-indigo-950/80 text-indigo-300 border-indigo-700/50';
      Icon = CheckCircle2;
      break;
    default:
      label = status;
  }

  const px = size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs';

  return (
    <span className={`inline-flex items-center space-x-1.5 font-medium rounded-full border ${bgClass} ${px}`}>
      <Icon className={size === 'sm' ? 'h-3 w-3' : 'h-3.5 w-3.5'} />
      <span>{label}</span>
    </span>
  );
};
