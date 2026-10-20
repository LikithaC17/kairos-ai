import React from 'react';

interface CardProps {
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  glow?: 'none' | 'blue' | 'rose' | 'amber' | 'purple';
}

export const Card: React.FC<CardProps> = ({
  title,
  subtitle,
  action,
  children,
  className = '',
  glow = 'none',
}) => {
  const glowClasses = {
    none: '',
    blue: 'border-blue-500/30 shadow-[0_0_15px_rgba(59,130,246,0.1)]',
    rose: 'border-rose-500/30 shadow-[0_0_15px_rgba(239,68,68,0.1)]',
    amber: 'border-amber-500/30 shadow-[0_0_15px_rgba(245,158,11,0.1)]',
    purple: 'border-purple-500/30 shadow-[0_0_15px_rgba(139,92,246,0.1)]',
  }[glow];

  return (
    <div
      className={`bg-slate-900/90 border border-slate-800 rounded-xl p-5 backdrop-blur-md transition-all duration-200 hover:border-slate-700 ${glowClasses} ${className}`}
    >
      {(title || action) && (
        <div className="flex items-start justify-between gap-4 mb-4 pb-3 border-b border-slate-800/80">
          <div>
            {title && <h3 className="text-sm font-semibold text-slate-100 tracking-wide uppercase">{title}</h3>}
            {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
          </div>
          {action && <div className="flex items-center gap-2">{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
};
