import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts';
import { ExplainabilityFeature } from '../../types';
import { Sparkles, HelpCircle } from 'lucide-react';

interface FeatureImportanceChartProps {
  features: ExplainabilityFeature[];
  rationale?: string;
}

export const FeatureImportanceChart: React.FC<FeatureImportanceChartProps> = ({
  features,
  rationale = 'High packet rate + abnormal SYN/ACK ratio + repeated connection frequency increased the predicted attack progression probability to 91%.',
}) => {
  const chartData = features.map((f) => ({
    name: f.feature,
    importance: f.importance,
    importancePct: Math.round(f.importance * 100),
    direction: f.direction,
    description: f.description,
  }));

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div>
          <h3 className="text-sm font-semibold tracking-wider text-slate-100 uppercase flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-400" />
            Explainable AI: Feature Attribution (SHAP / Sensitivity)
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Local & global marginal contributions to attack state prediction
          </p>
        </div>
        <span className="text-xs font-mono text-amber-400 bg-amber-500/10 px-2.5 py-1 rounded border border-amber-500/20">
          Attribution: Shapley Values
        </span>
      </div>

      {/* Bar Chart */}
      <div className="w-full h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 50, bottom: 5 }}>
            <XAxis
              type="number"
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
            />
            <YAxis
              type="category"
              dataKey="name"
              stroke="#94a3b8"
              fontSize={11}
              tickLine={false}
              axisLine={false}
              width={130}
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
              formatter={(val: any) => [`${(val * 100).toFixed(1)}%`, 'Attribution Weight']}
              labelFormatter={(lbl) => `Feature: ${lbl}`}
            />
            <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.direction === 'Positive' ? '#3b82f6' : '#10b981'}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Feature Descriptions Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-slate-800 text-xs font-mono">
        {features.slice(0, 4).map((f) => (
          <div key={f.feature} className="p-2.5 bg-slate-950/60 rounded border border-slate-800/80">
            <div className="flex items-center justify-between mb-1">
              <span className="font-bold text-slate-200">{f.feature}</span>
              <span
                className={`text-[10px] px-1.5 py-0.2 rounded ${
                  f.direction === 'Positive'
                    ? 'text-blue-400 bg-blue-500/10'
                    : 'text-emerald-400 bg-emerald-500/10'
                }`}
              >
                {f.direction} Impact ({(f.importance * 100).toFixed(0)}%)
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-sans">{f.description}</p>
          </div>
        ))}
      </div>

      {/* Rationale Quote */}
      <div className="p-3 bg-amber-950/20 border border-amber-600/30 rounded-lg text-xs font-sans italic text-amber-200/90">
        <strong>Analyst Decision Summary:</strong> "{rationale}"
      </div>
    </div>
  );
};
