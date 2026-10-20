import React from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';
import { ProtocolDistribution } from '../../types';

interface ProtocolDonutChartProps {
  protocols: ProtocolDistribution[];
}

export const ProtocolDonutChart: React.FC<ProtocolDonutChartProps> = ({ protocols }) => {
  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-4 h-full">
      {/* Donut Chart */}
      <div className="w-full sm:w-1/2 h-48 relative">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={protocols}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={80}
              paddingAngle={3}
              dataKey="value"
            >
              {protocols.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} stroke="#0f172a" strokeWidth={2} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '0.5rem',
                fontSize: '12px',
                color: '#f8fafc',
                fontFamily: 'monospace',
              }}
              formatter={(value: any, name: any) => [`${value} packets`, name]}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <span className="text-[10px] text-slate-400 font-mono uppercase">Protocols</span>
          <span className="text-sm font-bold font-mono text-slate-200">Total</span>
        </div>
      </div>

      {/* Legend & Percentages List */}
      <div className="w-full sm:w-1/2 space-y-2">
        {protocols.map((p) => (
          <div key={p.name} className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: p.color }} />
              <span className="text-slate-300 font-medium">{p.name}</span>
            </div>
            <div className="flex items-center gap-2 font-mono">
              <span className="text-slate-400">{p.value.toLocaleString()}</span>
              <span className="text-slate-200 font-semibold w-12 text-right">{p.percentage}%</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
