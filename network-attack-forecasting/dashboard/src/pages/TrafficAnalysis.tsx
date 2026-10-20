import React, { useState } from 'react';
import { usePolling } from '../hooks/usePolling';
import { trafficApi } from '../services/trafficApi';
import { TrafficTimelineChart } from '../components/traffic/TrafficTimelineChart';
import { ProtocolDonutChart } from '../components/traffic/ProtocolDonutChart';
import { CurrentNetworkStatePanel } from '../components/dashboard/CurrentNetworkStatePanel';
import { Card } from '../components/common/Card';
import { StateBadge, SeverityBadge } from '../components/common/Badge';
import { CardSkeleton, ChartSkeleton } from '../components/common/Skeleton';
import { formatTime, formatBytes, formatNumber } from '../utils';
import { Activity, ArrowUpDown, Filter } from 'lucide-react';

export const TrafficAnalysis: React.FC = () => {
  const [selectedWindow, setSelectedWindow] = useState('15m');
  const [protocolFilter, setProtocolFilter] = useState('ALL');

  const { data: stats, isLoading: loadingStats } = usePolling(
    () => trafficApi.getTrafficStats(selectedWindow),
    8000
  );

  const { data: flows, isLoading: loadingFlows } = usePolling(
    () => trafficApi.getTraffic(50),
    8000
  );

  const filteredFlows = flows?.filter((f) => {
    return protocolFilter === 'ALL' || f.protocol === protocolFilter;
  }) || [];

  return (
    <div className="space-y-6">
      {/* Network State Summary Grid */}
      {stats && (
        <CurrentNetworkStatePanel
          summary={stats.summary}
          topPorts={stats.top_ports}
        />
      )}

      {/* Main Charts: Timeline + Protocol */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card
            title="Real-Time Network Telemetry Ingestion"
            subtitle="Flow metrics aggregated over sliding observation intervals"
          >
            {loadingStats || !stats ? (
              <ChartSkeleton />
            ) : (
              <TrafficTimelineChart
                timeline={stats.timeline}
                selectedWindow={selectedWindow}
                onWindowChange={setSelectedWindow}
              />
            )}
          </Card>
        </div>

        <div className="lg:col-span-1">
          <Card
            title="Protocol Distribution Breakdown"
            subtitle="Transport & application layer volume"
          >
            {loadingStats || !stats ? (
              <ChartSkeleton />
            ) : (
              <ProtocolDonutChart protocols={stats.protocols} />
            )}
          </Card>
        </div>
      </div>

      {/* Recent Ingested Flows Table */}
      <Card
        title="Live Network Flow Telemetry Stream"
        subtitle="Raw preprocessed 7-feature sequence records"
        action={
          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="text-slate-400">Filter Protocol:</span>
            <select
              value={protocolFilter}
              onChange={(e) => setProtocolFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200 focus:outline-none"
            >
              <option value="ALL">All Protocols</option>
              <option value="TCP">TCP</option>
              <option value="UDP">UDP</option>
              <option value="ICMP">ICMP</option>
            </select>
          </div>
        }
      >
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950 text-slate-400 border-b border-slate-800 uppercase tracking-wider">
              <tr>
                <th className="py-2.5 px-3">Flow ID</th>
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">Source Socket</th>
                <th className="py-2.5 px-3">Destination Socket</th>
                <th className="py-2.5 px-3">Proto</th>
                <th className="py-2.5 px-3">Duration</th>
                <th className="py-2.5 px-3">Rate (pkts/s)</th>
                <th className="py-2.5 px-3">Volume</th>
                <th className="py-2.5 px-3">Classified State</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredFlows.slice(0, 15).map((flow) => (
                <tr key={flow.flow_id} className="hover:bg-slate-800/30">
                  <td className="py-2.5 px-3 text-blue-400 font-bold">{flow.flow_id}</td>
                  <td className="py-2.5 px-3 text-slate-400">{formatTime(flow.timestamp)}</td>
                  <td className="py-2.5 px-3 text-slate-200">
                    {flow.src_ip}:{flow.src_port}
                  </td>
                  <td className="py-2.5 px-3 text-slate-200">
                    {flow.dst_ip}:{flow.dst_port}
                  </td>
                  <td className="py-2.5 px-3 text-cyan-400">{flow.protocol}</td>
                  <td className="py-2.5 px-3 text-slate-400">{flow.flow_duration}s</td>
                  <td className="py-2.5 px-3 text-emerald-400 font-bold">
                    {formatNumber(flow.packet_rate)}
                  </td>
                  <td className="py-2.5 px-3 text-purple-400">{formatBytes(flow.byte_count)}</td>
                  <td className="py-2.5 px-3">
                    <StateBadge state={flow.state} size="sm" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
