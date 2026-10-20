import React from 'react';
import { NavLink } from 'react-router-dom';
import { Shield, Sparkles, Activity, Server, Cpu } from 'lucide-react';
import { NAV_ITEMS } from '../../constants';

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 flex flex-col justify-between bg-[#0b1222] border-r border-slate-800 shrink-0 h-screen sticky top-0">
      {/* Brand & Logo Header */}
      <div>
        <div className="h-16 flex items-center px-6 border-b border-slate-800 gap-3">
          <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-blue-600/20 border border-blue-500/40 text-blue-400">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-sm tracking-widest text-white uppercase">NETSCOPE AI</span>
              <span className="text-[9px] bg-blue-500/20 border border-blue-500/30 text-blue-400 font-mono px-1 py-0.2 rounded">
                SOC
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-medium">Attack Forecasting Model</p>
          </div>
        </div>

        {/* Navigation Section */}
        <nav className="p-3 space-y-1">
          <div className="px-3 py-2 text-[10px] font-mono font-semibold uppercase tracking-wider text-slate-400">
            Operations & Forecasting
          </div>
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30 font-semibold shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`
                }
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Bottom Telemetry Status Panel */}
      <div className="p-4 border-t border-slate-800 bg-[#080d1a]/80 text-xs font-mono space-y-2">
        <div className="flex items-center justify-between text-slate-400">
          <span className="flex items-center gap-1.5">
            <Server className="w-3.5 h-3.5 text-emerald-400" />
            Backend API:
          </span>
          <span className="text-emerald-400 font-medium flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block animate-pulse" />
            ONLINE
          </span>
        </div>

        <div className="flex items-center justify-between text-slate-400">
          <span className="flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-blue-400" />
            ML Engine:
          </span>
          <span className="text-blue-400 font-medium">GRU Dual-Head</span>
        </div>

        <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-400">
          <span>Engine v1.0.0</span>
          <span>FastAPI / PyTorch</span>
        </div>
      </div>
    </aside>
  );
};
