import React from 'react';
import { ForecastFutureState, SecurityState } from '../../types';
import { StateBadge, SeverityBadge } from '../common/Badge';
import { formatTime } from '../../utils';
import { ArrowRight, Clock, Target, ShieldAlert } from 'lucide-react';

interface ForecastTimelineProps {
  currentState: SecurityState;
  futureStates: ForecastFutureState[];
}

export const ForecastTimeline: React.FC<ForecastTimelineProps> = ({
  currentState,
  futureStates,
}) => {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold tracking-wider text-slate-100 uppercase">
            Multi-Horizon Future State Timeline
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Autoregressive sequence extrapolation: $S_t \rightarrow \hat&#123;S&#125;_{'{t+1}'} \dots \hat&#123;S&#125;_{'{t+K}'}$
          </p>
        </div>
        <span className="text-xs font-mono text-blue-400 bg-blue-500/10 px-2.5 py-1 rounded border border-blue-500/20">
          Horizon: K = {futureStates.length} Steps
        </span>
      </div>

      {/* Horizontal Scrollable Timeline */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {/* Node 0: Current State */}
        <div className="bg-slate-950/80 border-2 border-slate-700 rounded-xl p-4 flex flex-col justify-between shadow-lg">
          <div>
            <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-2">
              <span className="font-bold text-slate-200">Current (T0)</span>
              <span className="text-[10px] text-slate-500">NOW</span>
            </div>
            <div className="my-2">
              <StateBadge state={currentState} />
            </div>
            <div className="text-xs font-semibold text-slate-300 mt-2">Observed Ground Truth</div>
          </div>
          <div className="pt-3 mt-3 border-t border-slate-800 text-[11px] text-slate-400 font-mono">
            <span>Inference Base State</span>
          </div>
        </div>

        {/* Step Nodes: +1 to +K */}
        {futureStates.map((fs, idx) => {
          const isHighRisk = fs.risk_level === 'CRITICAL' || fs.risk_level === 'HIGH';
          return (
            <div
              key={fs.step}
              className={`rounded-xl p-4 flex flex-col justify-between transition-all duration-200 border ${
                isHighRisk
                  ? 'bg-rose-950/20 border-rose-500/40 shadow-[0_0_15px_rgba(239,68,68,0.08)]'
                  : 'bg-slate-900/90 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div>
                <div className="flex items-center justify-between text-xs font-mono mb-2">
                  <span className="font-bold text-blue-400">{fs.step} Step</span>
                  <div className="flex items-center gap-1 text-[10px] text-slate-400">
                    <Clock className="w-3 h-3" />
                    <span>{formatTime(fs.expected_time)}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2 mb-2">
                  <StateBadge state={fs.state} size="sm" />
                  <SeverityBadge severity={fs.risk_level} size="sm" />
                </div>

                <div className="font-semibold text-xs text-slate-100 line-clamp-1 mt-1">
                  {fs.attack_stage}
                </div>

                <div className="mt-2 text-[11px] font-mono flex items-center gap-1 text-purple-400">
                  <Target className="w-3 h-3" />
                  <span>MITRE {fs.mitre_technique}</span>
                </div>
              </div>

              {/* Metrics & Evidence */}
              <div className="pt-3 mt-3 border-t border-slate-800/80 space-y-1.5 font-mono text-[11px]">
                <div className="flex justify-between">
                  <span className="text-slate-400">Probability:</span>
                  <span className="text-blue-400 font-bold">{Math.round(fs.probability * 100)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Confidence:</span>
                  <span className="text-emerald-400 font-bold">{Math.round(fs.confidence * 100)}%</span>
                </div>
                <div className="pt-1 text-[10px] text-slate-500 italic line-clamp-1">
                  {fs.key_evidence[0]}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
