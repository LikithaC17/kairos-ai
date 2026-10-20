import React from 'react';
import { TrafficSummary, PortStat } from '../../types';
import { formatNumber, formatBytes } from '../../utils';
import { Network, Server, ArrowDownUp, Timer, Shield } from 'lucide-react';

interface CurrentNetworkStatePanelProps {
  summary: TrafficSummary;
  topPorts: PortStat[];
}

export const CurrentNetworkStatePanel: React.FC<CurrentNetworkStatePanelProps> = ({
  summary,
  topPorts,
}) => {
  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5">
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Network className="w-4 h-4 text-blue-400" />
          <h3 className="text-sm font-semibold tracking-wider text-slate-100 uppercase">
            Current Network State Telemetry
          </h3>
        </div>
        <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
          ● Latent State Synchronized
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 mb-4">
        {/* Source IPs */}
        <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
          <span className="text-[10px] font-mono uppercase text-slate-400">Source Host Count</span>
          <div className="text-lg font-bold font-mono text-slate-200 mt-1">
            {formatNumber(summary.unique_src_ips)} <span className="text-xs text-slate-500 font-normal">unique</span>
          </div>
          <span className="text-[10px] text-slate-500 font-mono">Internal LAN Hosts</span>
        </div>

        {/* Destination IPs */}
        <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
          <span className="text-[10px] font-mono uppercase text-slate-400">Destination Endpoints</span>
          <div className="text-lg font-bold font-mono text-slate-200 mt-1">
            {formatNumber(summary.unique_dst_ips)} <span className="text-xs text-slate-500 font-normal">endpoints</span>
          </div>
          <span className="text-[10px] text-slate-500 font-mono">External + DMZ</span>
        </div>

        {/* TCP/UDP Ratio */}
        <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
          <span className="text-[10px] font-mono uppercase text-slate-400">TCP / UDP Ratio</span>
          <div className="text-lg font-bold font-mono text-blue-400 mt-1">
            {summary.tcp_udp_ratio}
          </div>
          <span className="text-[10px] text-slate-500 font-mono">Transport distribution</span>
        </div>

        {/* SYN/ACK Ratio */}
        <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
          <span className="text-[10px] font-mono uppercase text-slate-400">SYN / ACK Flag Ratio</span>
          <div
            className={`text-lg font-bold font-mono mt-1 ${
              summary.syn_ack_ratio > 1.8 ? 'text-rose-400' : 'text-emerald-400'
            }`}
          >
            {summary.syn_ack_ratio}x
          </div>
          <span className="text-[10px] text-slate-500 font-mono">
            {summary.syn_ack_ratio > 1.8 ? 'Abnormal Half-Open Burst' : 'Baseline Healthy'}
          </span>
        </div>

        {/* Packet Size Stats */}
        <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
          <span className="text-[10px] font-mono uppercase text-slate-400">Mean Packet Size</span>
          <div className="text-lg font-bold font-mono text-slate-200 mt-1">
            {summary.avg_packet_size} <span className="text-xs text-slate-500 font-normal">Bytes</span>
          </div>
          <span className="text-[10px] text-slate-500 font-mono">MTU nominal 1500B</span>
        </div>

        {/* Connection Duration */}
        <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
          <span className="text-[10px] font-mono uppercase text-slate-400">Avg Flow Duration</span>
          <div className="text-lg font-bold font-mono text-slate-200 mt-1">
            {summary.avg_duration} <span className="text-xs text-slate-500 font-normal">sec</span>
          </div>
          <span className="text-[10px] text-slate-500 font-mono">Connection longevity</span>
        </div>

        {/* Cumulative Bytes */}
        <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
          <span className="text-[10px] font-mono uppercase text-slate-400">Cumulative Volume</span>
          <div className="text-lg font-bold font-mono text-purple-400 mt-1">
            {formatBytes(summary.total_bytes)}
          </div>
          <span className="text-[10px] text-slate-500 font-mono">{formatNumber(summary.total_packets)} frames</span>
        </div>

        {/* Flow Rate */}
        <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
          <span className="text-[10px] font-mono uppercase text-slate-400">Flow Arrival Rate</span>
          <div className="text-lg font-bold font-mono text-cyan-400 mt-1">
            {summary.flows_per_sec} <span className="text-xs text-slate-500 font-normal">flows/s</span>
          </div>
          <span className="text-[10px] text-slate-500 font-mono">Sliding 1m window</span>
        </div>
      </div>

      {/* Port Activity Horizontal Bar */}
      <div>
        <div className="text-xs font-mono text-slate-400 mb-2 flex items-center justify-between">
          <span>Target Port Activity Ranking</span>
          <span>Sampled flows</span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
          {topPorts.map((item) => (
            <div
              key={item.port}
              className="bg-slate-950/80 border border-slate-800 px-3 py-2 rounded flex flex-col justify-between"
            >
              <span className="text-xs font-mono font-bold text-slate-200">{item.port}</span>
              <span className="text-[11px] font-mono text-blue-400">{formatNumber(item.count)} hits</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
