import React from 'react';
import { ArrowRight, Sparkles, Brain, ShieldAlert, Target, Info } from 'lucide-react';
import { WhatHappensNext } from '../../types';
import { StateBadge } from '../common/Badge';

interface WhatHappensNextBannerProps {
  data?: WhatHappensNext;
}

export const WhatHappensNextBanner: React.FC<WhatHappensNextBannerProps> = ({
  data = {
    headline: 'High probability of full exploitation within the next 2 forecast steps',
    current_state: 'SUSPICIOUS',
    predicted_next_state: 'ATTACK',
    next_stage: 'Initial Access & Credential Brute Force',
    next_mitre_technique: 'T1110',
    next_probability: 0.78,
    next_confidence: 0.91,
    rationale:
      'High packet rate + abnormal SYN/ACK ratio + repeated connection frequency increased the predicted attack progression probability.',
  },
}) => {
  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-[#0e172e] to-slate-900 border border-blue-500/30 p-6 shadow-2xl">
      {/* Background Accent Glow */}
      <div className="absolute top-0 right-1/4 w-96 h-32 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-1/3 w-96 h-32 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Top Banner Tag */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2">
          <span className="flex items-center justify-center p-1.5 rounded-md bg-blue-500/20 text-blue-400 border border-blue-500/30">
            <Brain className="w-4 h-4" />
          </span>
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-blue-400">
            CORE INNOVATION: TEMPORAL WORLD MODEL FORECASTING
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
          <span className="text-slate-500">Traditional IDS: "Is it bad now?"</span>
          <span className="text-slate-600">→</span>
          <span className="text-emerald-400 font-semibold">NetScope: "What happens next?"</span>
        </div>
      </div>

      {/* Main Headline */}
      <h2 className="text-lg md:text-xl font-bold text-slate-100 tracking-tight mb-6">
        {data.headline}
      </h2>

      {/* Transition Grid: Current -> Latent Dynamic -> Predicted State */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {/* Step 1: Current Observed State */}
        <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
          <div>
            <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-1 flex items-center justify-between">
              <span>Current Network State</span>
              <span className="text-[10px] text-slate-500 font-mono">T=0</span>
            </div>
            <div className="mt-2 flex items-center gap-2">
              <StateBadge state={data.current_state} />
              <span className="text-xs text-slate-300 font-medium">Observed Telemetry</span>
            </div>
          </div>
          <p className="text-xs text-slate-400 mt-3 pt-3 border-t border-slate-800/80">
            Persistent scanning activity and asymmetric connection requests identified.
          </p>
        </div>

        {/* Step 2: Temporal Prediction */}
        <div className="bg-blue-950/30 border border-blue-500/40 rounded-xl p-4 flex flex-col justify-between relative">
          <div className="absolute -left-2.5 top-1/2 -translate-y-1/2 hidden md:flex items-center justify-center w-5 h-5 rounded-full bg-blue-600 text-white z-10 shadow">
            <ArrowRight className="w-3 h-3" />
          </div>
          <div>
            <div className="text-[11px] font-mono text-blue-400 uppercase tracking-wider mb-1 flex items-center justify-between">
              <span>Predicted Next State</span>
              <span className="text-[10px] bg-blue-500/20 text-blue-300 px-1.5 py-0.2 rounded font-mono">
                P(S_t+1 | S_t)
              </span>
            </div>
            <div className="mt-2 flex items-center gap-2">
              <StateBadge state={data.predicted_next_state} />
              <span className="text-xs text-rose-300 font-bold">Escalation Impending</span>
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-blue-500/20 flex items-center justify-between text-xs font-mono">
            <div>
              <span className="text-slate-400 text-[11px]">Probability: </span>
              <span className="text-blue-400 font-bold">{Math.round(data.next_probability * 100)}%</span>
            </div>
            <div>
              <span className="text-slate-400 text-[11px]">Confidence: </span>
              <span className="text-emerald-400 font-bold">{Math.round(data.next_confidence * 100)}%</span>
            </div>
          </div>
        </div>

        {/* Step 3: MITRE ATT&CK Stage */}
        <div className="bg-purple-950/20 border border-purple-500/30 rounded-xl p-4 flex flex-col justify-between relative">
          <div className="absolute -left-2.5 top-1/2 -translate-y-1/2 hidden md:flex items-center justify-center w-5 h-5 rounded-full bg-purple-600 text-white z-10 shadow">
            <ArrowRight className="w-3 h-3" />
          </div>
          <div>
            <div className="text-[11px] font-mono text-purple-400 uppercase tracking-wider mb-1 flex items-center justify-between">
              <span>MITRE ATT&CK Forecast</span>
              <span className="text-[10px] text-purple-300 font-mono bg-purple-500/20 px-1.5 py-0.5 rounded">
                {data.next_mitre_technique}
              </span>
            </div>
            <div className="mt-2 font-semibold text-sm text-slate-100 flex items-center gap-1.5">
              <Target className="w-4 h-4 text-purple-400" />
              <span>{data.next_stage}</span>
            </div>
          </div>
          <p className="text-xs text-purple-200/80 mt-3 pt-3 border-t border-purple-500/20">
            Adversary transitioning from passive reconnaissance to active credential exploitation.
          </p>
        </div>
      </div>

      {/* Explainable AI Rationale footer */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-xs text-slate-300">
        <div className="flex items-center gap-1.5 text-amber-400 font-mono font-semibold shrink-0">
          <Sparkles className="w-4 h-4" />
          <span>AI Explanation:</span>
        </div>
        <p className="text-slate-400 italic">"{data.rationale}"</p>
      </div>
    </div>
  );
};
