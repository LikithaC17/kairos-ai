import React from 'react';
import { Activity, ShieldAlert, TrendingUp, AlertTriangle, Cpu, CheckCircle } from 'lucide-react';
import { SecurityState, SeverityLevel, TrafficSummary } from '../../types';
import { formatNumber, formatBytes } from '../../utils';

interface KpiCardsProps {
  summary?: TrafficSummary;
  threatLevel?: SeverityLevel;
  activeThreatCount?: number;
  forecastRisk?: SeverityLevel;
  attackProbability?: number;
  modelConfidence?: number;
}

export const KpiCards: React.FC<KpiCardsProps> = ({
  summary = {
    packets_per_sec: 1420,
    bytes_per_sec: 985400,
    flows_per_sec: 42.6,
    active_connections: 1845,
    total_bytes: 886860000,
    total_packets: 1278450,
    unique_src_ips: 48,
    unique_dst_ips: 112,
    avg_duration: 3.45,
    avg_packet_size: 692.5,
    tcp_udp_ratio: '78.4% / 21.6%',
    syn_ack_ratio: 2.14,
  },
  threatLevel = 'HIGH',
  activeThreatCount = 3,
  forecastRisk = 'CRITICAL',
  attackProbability = 0.78,
  modelConfidence = 0.914,
}) => {
  const getThreatColor = (lvl: SeverityLevel) => {
    switch (lvl) {
      case 'CRITICAL':
        return 'text-rose-400 border-rose-500/30 bg-rose-500/10';
      case 'HIGH':
        return 'text-orange-400 border-orange-500/30 bg-orange-500/10';
      case 'MEDIUM':
        return 'text-amber-400 border-amber-500/30 bg-amber-500/10';
      default:
        return 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10';
    }
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      {/* 1. Network Traffic Volume */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition-colors">
        <div className="flex items-center justify-between text-slate-400 text-xs">
          <span className="font-mono uppercase tracking-wider">Network Traffic</span>
          <Activity className="w-4 h-4 text-blue-400" />
        </div>
        <div className="mt-2">
          <div className="text-xl font-bold font-mono text-slate-100">
            {formatNumber(summary.packets_per_sec)} <span className="text-xs font-normal text-slate-400">pkts/s</span>
          </div>
          <div className="text-[11px] text-slate-400 font-mono mt-0.5">
            {summary.flows_per_sec} flows/s · {summary.active_connections} active
          </div>
        </div>
        <div className="mt-2 pt-2 border-t border-slate-800 text-[10px] text-slate-500 flex justify-between">
          <span>Throughput:</span>
          <span className="text-slate-300 font-mono">{formatBytes(summary.bytes_per_sec)}/s</span>
        </div>
      </div>

      {/* 2. Current Threat Level */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition-colors">
        <div className="flex items-center justify-between text-slate-400 text-xs">
          <span className="font-mono uppercase tracking-wider">Current Threat Level</span>
          <ShieldAlert className="w-4 h-4 text-orange-400" />
        </div>
        <div className="mt-2">
          <div className="flex items-center gap-2">
            <span
              className={`text-xl font-black font-mono tracking-wider px-2 py-0.5 rounded border ${getThreatColor(
                threatLevel
              )}`}
            >
              {threatLevel}
            </span>
          </div>
          <p className="text-[11px] text-slate-400 font-mono mt-1">Real-time state classification</p>
        </div>
        <div className="mt-2 pt-2 border-t border-slate-800 text-[10px] text-slate-500 flex justify-between">
          <span>SYN/ACK Ratio:</span>
          <span className="text-slate-300 font-mono">{summary.syn_ack_ratio}x</span>
        </div>
      </div>

      {/* 3. Active Detected Threats */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition-colors">
        <div className="flex items-center justify-between text-slate-400 text-xs">
          <span className="font-mono uppercase tracking-wider">Active Threats</span>
          <AlertTriangle className="w-4 h-4 text-rose-400" />
        </div>
        <div className="mt-2">
          <div className="text-xl font-bold font-mono text-rose-400">
            {activeThreatCount}{' '}
            <span className="text-xs font-normal text-slate-400">threat vectors</span>
          </div>
          <p className="text-[11px] text-slate-400 font-mono mt-0.5">Under active containment</p>
        </div>
        <div className="mt-2 pt-2 border-t border-slate-800 text-[10px] text-slate-500 flex justify-between">
          <span>Priority Triage:</span>
          <span className="text-rose-400 font-mono">Immediate SOC Action</span>
        </div>
      </div>

      {/* 4. Forecast Risk */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition-colors">
        <div className="flex items-center justify-between text-slate-400 text-xs">
          <span className="font-mono uppercase tracking-wider">Forecast Risk</span>
          <TrendingUp className="w-4 h-4 text-purple-400" />
        </div>
        <div className="mt-2">
          <div className="flex items-center gap-2">
            <span
              className={`text-xl font-black font-mono tracking-wider px-2 py-0.5 rounded border ${getThreatColor(
                forecastRisk
              )}`}
            >
              {forecastRisk}
            </span>
          </div>
          <p className="text-[11px] text-slate-400 font-mono mt-1">Multi-step future state trajectory</p>
        </div>
        <div className="mt-2 pt-2 border-t border-slate-800 text-[10px] text-slate-500 flex justify-between">
          <span>Look-ahead Horizon:</span>
          <span className="text-purple-400 font-mono">+5 Steps (2.5m)</span>
        </div>
      </div>

      {/* 5. Attack Progression Probability */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition-colors">
        <div className="flex items-center justify-between text-slate-400 text-xs">
          <span className="font-mono uppercase tracking-wider">Attack Probability</span>
          <TrendingUp className="w-4 h-4 text-blue-400" />
        </div>
        <div className="mt-2">
          <div className="text-xl font-bold font-mono text-blue-400">
            {Math.round(attackProbability * 100)}%
          </div>
          <div className="w-full bg-slate-800 h-1.5 rounded-full mt-1.5 overflow-hidden">
            <div
              className="bg-blue-500 h-full rounded-full transition-all duration-500"
              style={{ width: `${Math.round(attackProbability * 100)}%` }}
            />
          </div>
        </div>
        <div className="mt-2 pt-2 border-t border-slate-800 text-[10px] text-slate-500 flex justify-between">
          <span>Next Transition:</span>
          <span className="text-blue-300 font-mono">P(S_t+1 | S_t)</span>
        </div>
      </div>

      {/* 6. ML Model Confidence */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition-colors">
        <div className="flex items-center justify-between text-slate-400 text-xs">
          <span className="font-mono uppercase tracking-wider">Model Confidence</span>
          <Cpu className="w-4 h-4 text-emerald-400" />
        </div>
        <div className="mt-2">
          <div className="text-xl font-bold font-mono text-emerald-400">
            {(modelConfidence * 100).toFixed(1)}%
          </div>
          <div className="w-full bg-slate-800 h-1.5 rounded-full mt-1.5 overflow-hidden">
            <div
              className="bg-emerald-500 h-full rounded-full transition-all duration-500"
              style={{ width: `${modelConfidence * 100}%` }}
            />
          </div>
        </div>
        <div className="mt-2 pt-2 border-t border-slate-800 text-[10px] text-slate-500 flex justify-between">
          <span>Holdout Test Acc:</span>
          <span className="text-emerald-300 font-mono">91.37%</span>
        </div>
      </div>
    </div>
  );
};
