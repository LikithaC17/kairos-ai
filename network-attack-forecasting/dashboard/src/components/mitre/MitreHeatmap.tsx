import React, { useState } from 'react';
import { MitreItem } from '../../types';
import { SeverityBadge } from '../common/Badge';
import { Crosshair, ShieldCheck, AlertTriangle, Search, Filter } from 'lucide-react';

interface MitreHeatmapProps {
  matrix: MitreItem[];
}

export const MitreHeatmap: React.FC<MitreHeatmapProps> = ({ matrix }) => {
  const [filterRisk, setFilterRisk] = useState<string>('ALL');

  const filtered = matrix.filter((item) => {
    return filterRisk === 'ALL' || item.risk === filterRisk;
  });

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden">
      {/* Header with Risk Filter */}
      <div className="p-4 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3 bg-slate-950/40">
        <div>
          <h3 className="text-sm font-semibold tracking-wider text-slate-100 uppercase flex items-center gap-2">
            <Crosshair className="w-4 h-4 text-purple-400" />
            MITRE ATT&CK Enterprise Matrix & Threat Heatmap
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Adversary TTPs aligned with temporal forecasting predictions
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="text-slate-400">Risk Filter:</span>
          <select
            value={filterRisk}
            onChange={(e) => setFilterRisk(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1 text-slate-200 focus:outline-none focus:border-blue-500"
          >
            <option value="ALL">All Risk Levels</option>
            <option value="CRITICAL">Critical Only</option>
            <option value="HIGH">High Only</option>
            <option value="MEDIUM">Medium Only</option>
            <option value="LOW">Low Only</option>
          </select>
        </div>
      </div>

      {/* Heatmap Matrix Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-slate-950 text-slate-400 border-b border-slate-800 uppercase tracking-wider">
            <tr>
              <th className="py-3 px-4">Technique ID</th>
              <th className="py-3 px-4">Technique Name</th>
              <th className="py-3 px-4">Enterprise Tactic</th>
              <th className="py-3 px-4">Current Evidence</th>
              <th className="py-3 px-4">Forecast Probability</th>
              <th className="py-3 px-4">Risk Level</th>
              <th className="py-3 px-4">Operational Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {filtered.map((item) => {
              const probPercent = Math.round(item.predicted_probability * 100);
              let probColor = 'text-slate-400';
              if (probPercent >= 80) probColor = 'text-rose-400 font-bold';
              else if (probPercent >= 60) probColor = 'text-orange-400 font-bold';
              else if (probPercent >= 40) probColor = 'text-amber-400';

              return (
                <tr key={item.technique_id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3.5 px-4 font-bold text-purple-400">
                    <span className="bg-purple-950/40 border border-purple-500/30 px-2 py-0.5 rounded">
                      {item.technique_id}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 font-semibold text-slate-200 font-sans">
                    {item.technique_name}
                  </td>
                  <td className="py-3.5 px-4 text-slate-400">{item.tactic}</td>
                  <td className="py-3.5 px-4 text-slate-300">
                    <span className="text-blue-400 font-bold">{item.evidence_count}</span> flows recorded
                  </td>
                  <td className="py-3.5 px-4">
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-slate-800 h-1.5 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${
                            probPercent >= 80
                              ? 'bg-rose-500'
                              : probPercent >= 60
                              ? 'bg-orange-500'
                              : 'bg-blue-500'
                          }`}
                          style={{ width: `${probPercent}%` }}
                        />
                      </div>
                      <span className={probColor}>{probPercent}%</span>
                    </div>
                  </td>
                  <td className="py-3.5 px-4">
                    <SeverityBadge severity={item.risk} size="sm" />
                  </td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${
                        item.current_status.includes('Active') || item.current_status.includes('High Risk')
                          ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                          : item.current_status.includes('Detected')
                          ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                          : 'bg-slate-800 text-slate-400 border-slate-700'
                      }`}
                    >
                      {item.current_status}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="p-4 border-t border-slate-800 bg-slate-950/40 text-xs text-slate-400 font-mono flex items-center justify-between">
        <span>MITRE ATT&CK Matrix version: Enterprise v14.1</span>
        <span className="text-emerald-400">Technique Correlation Engine: Synchronized</span>
      </div>
    </div>
  );
};
