import React from 'react';
import { usePolling } from '../hooks/usePolling';
import { modelApi } from '../services/modelApi';
import { Card } from '../components/common/Card';
import { CardSkeleton } from '../components/common/Skeleton';
import { formatTime } from '../utils';
import { Server, Activity, Cpu, HardDrive, CheckCircle2, ShieldCheck, Zap } from 'lucide-react';

export const SystemStatus: React.FC = () => {
  const { data: statusData, isLoading } = usePolling(
    () => modelApi.getSystemStatus(),
    10000
  );

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="p-1.5 rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                <ShieldCheck className="w-5 h-5" />
              </span>
              <h2 className="text-xl font-bold text-white tracking-wide">
                System Infrastructure & Node Telemetry
              </h2>
            </div>
            <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
              Monitoring runtime health, RPC response latency, ML inference dispatch pipelines, and telemetry ingestion sockets.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-mono text-xs flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4" />
              All Services Operational
            </span>
          </div>
        </div>
      </div>

      {/* Host Metrics */}
      {statusData && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 font-mono text-xs">
          <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
            <span className="text-slate-500 block mb-1">CPU LOAD</span>
            <div className="text-xl font-bold text-slate-100">
              {statusData.system_metrics.cpu_usage_pct}%
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
              <div
                className="bg-blue-500 h-full rounded-full"
                style={{ width: `${statusData.system_metrics.cpu_usage_pct}%` }}
              />
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
            <span className="text-slate-500 block mb-1">RAM UTILIZATION</span>
            <div className="text-xl font-bold text-slate-100">
              {statusData.system_metrics.memory_usage_pct}%
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
              <div
                className="bg-purple-500 h-full rounded-full"
                style={{ width: `${statusData.system_metrics.memory_usage_pct}%` }}
              />
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
            <span className="text-slate-500 block mb-1">UPTIME</span>
            <div className="text-xl font-bold text-emerald-400">
              {Math.floor(statusData.system_metrics.uptime_seconds / 3600)}h{' '}
              {Math.floor((statusData.system_metrics.uptime_seconds % 3600) / 60)}m
            </div>
            <span className="text-[10px] text-slate-500">Continuous Service</span>
          </div>

          <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
            <span className="text-slate-500 block mb-1">INFERRED SEQUENCES</span>
            <div className="text-xl font-bold text-cyan-400">
              {statusData.system_metrics.total_inferred_sequences.toLocaleString()}
            </div>
            <span className="text-[10px] text-slate-500">Dual-Head Passes</span>
          </div>
        </div>
      )}

      {/* Services Table */}
      <Card title="Operational Node Status" subtitle="Health check heartbeats & REST response latencies">
        {isLoading || !statusData ? (
          <CardSkeleton />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-950 text-slate-400 border-b border-slate-800 uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Subsystem Node</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Latency (ms)</th>
                  <th className="py-3 px-4">Version</th>
                  <th className="py-3 px-4">Last Heartbeat</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {statusData.services.map((svc) => (
                  <tr key={svc.name} className="hover:bg-slate-800/30">
                    <td className="py-3.5 px-4 font-bold text-slate-200 flex items-center gap-2">
                      <Server className="w-4 h-4 text-blue-400" />
                      <span>{svc.name}</span>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[11px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                        ONLINE
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-300">
                      <span className="text-cyan-400 font-bold">{svc.latency_ms}</span> ms
                    </td>
                    <td className="py-3.5 px-4 text-slate-400">{svc.version}</td>
                    <td className="py-3.5 px-4 text-slate-500">{formatTime(svc.last_heartbeat)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
};
