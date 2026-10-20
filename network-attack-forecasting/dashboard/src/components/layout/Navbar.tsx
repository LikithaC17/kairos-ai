import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  RotateCw,
  Bell,
  CheckCircle2,
  Cpu,
  Layers,
} from 'lucide-react';
import { POLLING_INTERVALS } from '../../constants';

interface NavbarProps {
  onRefresh?: () => void;
  isRefreshing?: boolean;
  lastUpdated?: Date;
  pollingInterval?: number;
  onPollingIntervalChange?: (ms: number) => void;
  unreadAlertCount?: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  onRefresh,
  isRefreshing = false,
  lastUpdated = new Date(),
  pollingInterval = 10000,
  onPollingIntervalChange,
  unreadAlertCount = 3,
}) => {
  const location = useLocation();
  const navigate = useNavigate();

  // Compute page title from path
  const getPageTitle = (path: string) => {
    if (path === '/' || path === '/dashboard') return 'SOC Overview & Forecasting';
    if (path === '/traffic') return 'Live Telemetry & Traffic Analysis';
    if (path === '/threats') return 'Intrusion Detection & Evidence';
    if (path === '/forecast') return 'Temporal World Model Attack Forecast';
    if (path === '/simulation') return 'Interactive Adversary Simulation';
    if (path === '/mitre') return 'MITRE ATT&CK Matrix & Heatmap';
    if (path === '/alerts') return 'Security Operations Center Alerts';
    if (path === '/model') return 'AI World Model Insights & Explainability';
    if (path === '/status') return 'System Infrastructure Status';
    if (path === '/settings') return 'Platform & Engine Configuration';
    return 'NETSCOPE AI';
  };

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between h-16 px-6 bg-[#080d1a]/90 backdrop-blur-md border-b border-slate-800">
      {/* Left: Page Title & Breadcrumb */}
      <div className="flex items-center gap-3">
        <div>
          <h1 className="text-base font-bold tracking-wide text-slate-100 flex items-center gap-2">
            {getPageTitle(location.pathname)}
          </h1>
          <p className="text-[11px] text-slate-400 font-mono">
            NETSCOPE // Autonomous Threat Forecasting System
          </p>
        </div>
      </div>

      {/* Right: SOC Status Telemetry + Controls */}
      <div className="flex items-center gap-4">
        {/* Status Pills */}
        <div className="hidden lg:flex items-center gap-2 text-xs font-mono">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-slate-300">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-slate-400">Network:</span>
            <span className="text-emerald-400 font-medium">Operational</span>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-slate-300">
            <Cpu className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-slate-400">Model:</span>
            <span className="text-blue-400 font-medium">GRU Dual-Head</span>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-slate-300">
            <Layers className="w-3.5 h-3.5 text-purple-400" />
            <span className="text-slate-400">World Model:</span>
            <span className="text-purple-400 font-medium">Online</span>
          </div>
        </div>

        {/* Live API Indicator */}
        <div className="flex items-center">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-mono bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>LIVE API</span>
          </div>
        </div>

        {/* Polling Interval Selector */}
        {onPollingIntervalChange && (
          <div className="hidden sm:flex items-center gap-1.5 text-xs text-slate-400 font-mono">
            <select
              value={pollingInterval}
              onChange={(e) => onPollingIntervalChange(Number(e.target.value))}
              className="bg-slate-900 border border-slate-800 rounded px-2 py-1 text-slate-200 text-xs focus:outline-none focus:border-blue-500"
            >
              {POLLING_INTERVALS.map((item) => (
                <option key={item.value} value={item.value}>
                  Sync: {item.label}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Refresh Button */}
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            title={`Last updated: ${lastUpdated.toLocaleTimeString()}`}
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700 transition-colors disabled:opacity-50"
          >
            <RotateCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-blue-400' : ''}`} />
          </button>
        )}

        {/* Alert Bell Button */}
        <button
          onClick={() => navigate('/alerts')}
          className="relative p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700 transition-colors"
        >
          <Bell className="w-4 h-4" />
          {unreadAlertCount > 0 && (
            <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-rose-500 text-[10px] font-bold text-white ring-2 ring-[#080d1a]">
              {unreadAlertCount}
            </span>
          )}
        </button>
      </div>
    </header>
  );
};
