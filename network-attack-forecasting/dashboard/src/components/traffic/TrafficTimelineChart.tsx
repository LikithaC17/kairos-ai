import React, { useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  AreaChart,
  Area,
} from 'recharts';
import { TimelinePoint } from '../../types';
import { formatNumber, formatBytes } from '../../utils';

interface TrafficTimelineChartProps {
  timeline: TimelinePoint[];
  selectedWindow: string;
  onWindowChange: (w: string) => void;
}

export const TrafficTimelineChart: React.FC<TrafficTimelineChartProps> = ({
  timeline,
  selectedWindow,
  onWindowChange,
}) => {
  const [metric, setMetric] = useState<'packets' | 'bytes' | 'flows' | 'rate' | 'suspicious'>('packets');

  const windows = ['1m', '5m', '15m', '1h', '24h'];

  const getMetricKey = () => {
    switch (metric) {
      case 'bytes':
        return 'bytes';
      case 'flows':
        return 'flows';
      case 'rate':
        return 'packet_rate';
      case 'suspicious':
        return 'is_suspicious';
      default:
        return 'packets';
    }
  };

  const getMetricColor = () => {
    switch (metric) {
      case 'bytes':
        return '#8b5cf6';
      case 'flows':
        return '#06b6d4';
      case 'rate':
        return '#f59e0b';
      case 'suspicious':
        return '#ef4444';
      default:
        return '#3b82f6';
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Chart Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        {/* Metric Selector Tabs */}
        <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs font-mono">
          {(
            [
              { id: 'packets', label: 'Packets' },
              { id: 'bytes', label: 'Bytes' },
              { id: 'flows', label: 'Flows' },
              { id: 'rate', label: 'Packet Rate' },
              { id: 'suspicious', label: 'Threat Activity' },
            ] as const
          ).map((m) => (
            <button
              key={m.id}
              onClick={() => setMetric(m.id)}
              className={`px-2.5 py-1 rounded transition-colors ${
                metric === m.id
                  ? 'bg-blue-600 text-white font-semibold shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>

        {/* Time Window Buttons */}
        <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs font-mono">
          {windows.map((w) => (
            <button
              key={w}
              onClick={() => onWindowChange(w)}
              className={`px-2 py-0.5 rounded transition-colors ${
                selectedWindow === w
                  ? 'bg-slate-800 text-blue-400 font-bold border border-blue-500/30'
                  : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              {w}
            </button>
          ))}
        </div>
      </div>

      {/* Recharts Line/Area Graph */}
      <div className="w-full h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={timeline} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="metricGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={getMetricColor()} stopOpacity={0.4} />
                <stop offset="95%" stopColor={getMetricColor()} stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis
              dataKey="time"
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: '#1e293b' }}
            />
            <YAxis
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: '#1e293b' }}
              tickFormatter={(v) => (metric === 'bytes' ? formatBytes(v, 0) : formatNumber(v))}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '0.5rem',
                fontSize: '12px',
                color: '#f8fafc',
                fontFamily: 'monospace',
              }}
              formatter={(value: any) => [
                metric === 'bytes' ? formatBytes(value) : formatNumber(value),
                metric.toUpperCase(),
              ]}
              labelFormatter={(lbl) => `Timestamp: ${lbl}`}
            />
            <Area
              type="monotone"
              dataKey={getMetricKey()}
              stroke={getMetricColor()}
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#metricGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
