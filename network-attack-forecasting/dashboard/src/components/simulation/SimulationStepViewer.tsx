import React from 'react';
import { SimulationStep } from '../../types';
import { StateBadge, SeverityBadge } from '../common/Badge';
import { formatTime, formatBytes } from '../../utils';
import { ShieldAlert, ArrowRight, Activity, Clock, CheckCircle2 } from 'lucide-react';

interface SimulationStepViewerProps {
  currentStepIndex: number;
  steps: SimulationStep[];
}

export const SimulationStepViewer: React.FC<SimulationStepViewerProps> = ({
  currentStepIndex,
  steps,
}) => {
  const currentStep = steps[currentStepIndex] || steps[0];
  if (!currentStep) return null;

  // Select key milestone stages: T0, T1, T2, T3, T4 relative to current step
  const visibleSteps = steps.slice(0, currentStepIndex + 1).slice(-6);

  return (
    <div className="space-y-5">
      {/* Active Step Real-Time Inspector */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5">
        <div className="flex flex-wrap items-center justify-between gap-3 pb-3 mb-4 border-b border-slate-800">
          <div className="flex items-center gap-2 font-mono">
            <span className="text-sm font-bold text-blue-400 bg-blue-500/10 px-2.5 py-1 rounded border border-blue-500/20">
              STEP {currentStep.step_label} / {steps.length > 0 ? steps.length - 1 : 0}
            </span>
            <span className="text-xs text-slate-400">Flow: {currentStep.flow_id}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-slate-400">State:</span>
            <StateBadge state={currentStep.ground_truth_state} />
            <SeverityBadge severity={currentStep.severity} size="sm" />
          </div>
        </div>

        {/* Dynamic Telemetry at this Step */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono mb-4">
          <div className="p-3 bg-slate-950/70 rounded-lg border border-slate-800">
            <span className="text-slate-500 text-[10px] block">SOURCE SOCKET</span>
            <span className="font-bold text-slate-200">{currentStep.src_ip}</span>
          </div>
          <div className="p-3 bg-slate-950/70 rounded-lg border border-slate-800">
            <span className="text-slate-500 text-[10px] block">DESTINATION SOCKET</span>
            <span className="font-bold text-slate-200">{currentStep.dst_ip}</span>
          </div>
          <div className="p-3 bg-slate-950/70 rounded-lg border border-slate-800">
            <span className="text-slate-500 text-[10px] block">PACKET RATE</span>
            <span className="font-bold text-blue-400">{currentStep.packet_rate} pkts/s</span>
          </div>
          <div className="p-3 bg-slate-950/70 rounded-lg border border-slate-800">
            <span className="text-slate-500 text-[10px] block">PREDICTED NEXT STATE</span>
            <span className="font-bold text-rose-400">{currentStep.inferred_next_state}</span>
          </div>
        </div>

        {/* Model's Inferred Probabilities at This Step */}
        <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800">
          <div className="text-xs font-mono text-slate-400 mb-2 flex items-center justify-between">
            <span>Model Softmax Probability Distribution</span>
            <span className="text-emerald-400 font-bold">
              Confidence: {Math.round(currentStep.prediction_confidence * 100)}%
            </span>
          </div>
          <div className="grid grid-cols-4 gap-2 text-xs font-mono">
            {Object.entries(currentStep.current_probabilities).map(([stateKey, prob]) => (
              <div key={stateKey} className="p-2 rounded bg-slate-900 border border-slate-800/80">
                <div className="flex justify-between text-[11px] mb-1">
                  <span className="text-slate-400">{stateKey}</span>
                  <span className="text-slate-200 font-bold">{Math.round((prob as number) * 100)}%</span>
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 rounded-full"
                    style={{ width: `${Math.round((prob as number) * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Historical Simulation Step Feed */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5">
        <h3 className="text-sm font-semibold tracking-wider text-slate-100 uppercase mb-4">
          Simulation Evolution Timeline
        </h3>
        <div className="space-y-3 font-mono text-xs">
          {visibleSteps.map((st) => (
            <div
              key={st.step_index}
              className={`p-3 rounded-lg border flex flex-wrap items-center justify-between gap-3 transition-colors ${
                st.step_index === currentStepIndex
                  ? 'bg-blue-950/20 border-blue-500/40 text-slate-100'
                  : 'bg-slate-950/40 border-slate-800 text-slate-400'
              }`}
            >
              <div className="flex items-center gap-3">
                <span className="px-2 py-0.5 rounded bg-slate-800 text-blue-400 font-bold">
                  {st.step_label}
                </span>
                <span>{st.src_ip} → {st.dst_ip}</span>
              </div>
              <div className="flex items-center gap-4">
                <StateBadge state={st.ground_truth_state} size="sm" />
                <span className="text-slate-500">→ Forecast Next:</span>
                <span className="text-rose-400 font-bold">{st.inferred_next_state}</span>
                <span className="text-emerald-400">{Math.round(st.prediction_confidence * 100)}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
