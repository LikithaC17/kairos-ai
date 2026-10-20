import React from 'react';
import { SecurityState, SeverityLevel } from '../../types';
import { getStateBadge, getSeverityBadge } from '../../utils';

interface StateBadgeProps {
  state: SecurityState;
  size?: 'sm' | 'md';
}

export const StateBadge: React.FC<StateBadgeProps> = ({ state, size = 'md' }) => {
  const meta = getStateBadge(state);
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs font-semibold';
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border font-mono tracking-wider ${meta.bg} ${meta.text} ${meta.border} ${sizeClasses}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
      {meta.label}
    </span>
  );
};

interface SeverityBadgeProps {
  severity: SeverityLevel;
  size?: 'sm' | 'md';
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({ severity, size = 'md' }) => {
  const meta = getSeverityBadge(severity);
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs font-semibold';
  return (
    <span
      className={`inline-flex items-center rounded-md border font-mono uppercase tracking-wider ${meta.bg} ${meta.text} ${meta.border} ${sizeClasses}`}
    >
      {meta.label}
    </span>
  );
};
