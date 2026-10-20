import React from 'react';
import { ArrowRight, CheckCircle2, AlertTriangle, ShieldAlert, Crosshair } from 'lucide-react';
import { KILL_CHAIN_STAGES } from '../../constants';

interface AttackProgressionFlowProps {
  currentStageId?: string; // e.g. RECONNAISSANCE
  predictedNextStageId?: string; // e.g. INITIAL_ACCESS
  highRiskStageIds?: string[]; // e.g. ['COMMAND_AND_CONTROL', 'EXFILTRATION']
}

export const AttackProgressionFlow: React.FC<AttackProgressionFlowProps> = ({
  currentStageId = 'RECONNAISSANCE',
  predictedNextStageId = 'INITIAL_ACCESS',
  highRiskStageIds = ['COMMAND_AND_CONTROL', 'EXFILTRATION', 'IMPACT'],
}) => {
  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5">
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
        <div>
          <h3 className="text-sm font-semibold tracking-wider text-slate-100 uppercase flex items-center gap-2">
            <Crosshair className="w-4 h-4 text-purple-400" />
            Adversary Kill Chain Stage Progression
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Sequential progression mapped to MITRE Enterprise Tactics
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs font-mono">
          <span className="flex items-center gap-1.5 text-amber-400">
            <span className="w-2 h-2 rounded-full bg-amber-400" />
            Current Stage
          </span>
          <span className="flex items-center gap-1.5 text-blue-400">
            <span className="w-2 h-2 rounded-full bg-blue-400" />
            Predicted Next
          </span>
          <span className="flex items-center gap-1.5 text-rose-400">
            <span className="w-2 h-2 rounded-full bg-rose-400" />
            High-Risk Future
          </span>
        </div>
      </div>

      {/* Progression Flow Horizontal Timeline */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3">
        {KILL_CHAIN_STAGES.map((stage, idx) => {
          const isCurrent = stage.id === currentStageId;
          const isPredictedNext = stage.id === predictedNextStageId;
          const isHighRisk = highRiskStageIds.includes(stage.id);

          let borderClass = 'border-slate-800';
          let bgClass = 'bg-slate-950/60';
          let badgeText = 'Normal Monitoring';
          let badgeColor = 'text-slate-500 bg-slate-900 border-slate-800';

          if (isCurrent) {
            borderClass = 'border-amber-500/50 shadow-[0_0_15px_rgba(245,158,11,0.15)]';
            bgClass = 'bg-amber-950/20';
            badgeText = 'CURRENT OBSERVED';
            badgeColor = 'text-amber-400 bg-amber-500/10 border-amber-500/30';
          } else if (isPredictedNext) {
            borderClass = 'border-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.15)]';
            bgClass = 'bg-blue-950/20';
            badgeText = 'PREDICTED NEXT (+1)';
            badgeColor = 'text-blue-400 bg-blue-500/10 border-blue-500/30';
          } else if (isHighRisk) {
            borderClass = 'border-rose-500/30';
            bgClass = 'bg-rose-950/10';
            badgeText = 'HIGH RISK HORIZON';
            badgeColor = 'text-rose-400 bg-rose-500/10 border-rose-500/30';
          }

          return (
            <div
              key={stage.id}
              className={`p-4 rounded-xl border flex flex-col justify-between transition-all duration-200 ${borderClass} ${bgClass}`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-mono text-slate-500 font-bold">STAGE 0{idx + 1}</span>
                  <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded border uppercase ${badgeColor}`}>
                    {badgeText}
                  </span>
                </div>
                <h4 className="text-xs font-bold text-slate-100">{stage.name}</h4>
                <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">{stage.description}</p>
              </div>

              <div className="mt-4 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px] font-mono">
                <span className="text-slate-400">MITRE Technique:</span>
                <span className="text-purple-400 font-bold">{stage.mitre}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
