import React from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';
import { ProbabilityCurvePoint } from '../../types';

interface AttackProbabilityGraphProps {
  data: ProbabilityCurvePoint[];
}

export const AttackProbabilityGraph: React.FC<AttackProbabilityGraphProps> = ({ data }) => {
  const chartData = data.map((d) => ({
    ...d,
    probPercent: Math.round(d.probability * 100),
    confLowerPercent: Math.round(d.confidence_lower * 100),
    confUpperPercent: Math.round(d.confidence_upper * 100),
    // For area shading
    band: [Math.round(d.confidence_lower * 100), Math.round(d.confidence_upper * 100)],
  }));

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5">
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
        <div>
          <h3 className="text-sm font-semibold tracking-wider text-slate-100 uppercase">
            Attack Probability Trajectory & Confidence Envelope
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Statistical projection $P(\text&#123;Attack&#125; \mid S_{'{t+k}'})$ with 90% Bayesian Credible Interval
          </p>
        </div>
        <span className="text-xs font-mono text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20">
          Uncertainty Calibrated
        </span>
      </div>

      <div className="w-full h-72">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis
              dataKey="step"
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: '#1e293b' }}
            />
            <YAxis
              domain={[0, 100]}
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: '#1e293b' }}
              tickFormatter={(v) => `${v}%`}
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
              formatter={(value: any, name: any) => [`${value}%`, name]}
              labelFormatter={(lbl) => `Forecast Horizon: ${lbl}`}
            />
            <Legend
              wrapperStyle={{ fontSize: '11px', fontFamily: 'monospace', paddingTop: '10px' }}
            />
            {/* Shaded Upper/Lower Envelope */}
            <Area
              name="Confidence Interval (90%)"
              type="monotone"
              dataKey="confUpperPercent"
              stroke="transparent"
              fill="url(#areaGradient)"
            />
            {/* Main Probability Line */}
            <Line
              name="Attack Escalation Probability"
              type="monotone"
              dataKey="probPercent"
              stroke="#3b82f6"
              strokeWidth={3}
              dot={{ fill: '#3b82f6', stroke: '#1e293b', strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, fill: '#60a5fa' }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between text-[11px] font-mono text-slate-400 gap-2">
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block" />
          Point Estimate ($K$-step recurrent forward step)
        </span>
        <span className="text-slate-500">Early Warning Threshold: 70% reached at step +2</span>
      </div>
    </div>
  );
};
