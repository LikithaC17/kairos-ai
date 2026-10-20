import React from 'react';
import { ArrowRight, Cpu, Layers, Database, Activity, GitCommit } from 'lucide-react';
import { ForecastResponse } from '../../types';

interface WorldModelFlowProps {
  forecast?: ForecastResponse;
}

export const WorldModelFlow: React.FC<WorldModelFlowProps> = ({ forecast }) => {
  const currentState = forecast?.current_state || 'SUSPICIOUS';
  const nextState = forecast?.predicted_next_state || 'ATTACK';
  const nextProb = forecast?.what_happens_next?.next_probability || 0.78;
  const nextStage = forecast?.what_happens_next?.next_stage || 'Credential Brute Force';

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5">
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
        <div>
          <h3 className="text-sm font-semibold tracking-wider text-slate-100 uppercase flex items-center gap-2">
            <Cpu className="w-4 h-4 text-purple-400" />
            AI Network Security World Model Architecture
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Sequential State Transition: $S_t \rightarrow h_t \in \mathbb&#123;R&#125;^{'{128}'} \rightarrow P(S_{'{t+k}'} \mid S_t)$
          </p>
        </div>
        <span className="text-xs font-mono text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20">
          Dual-Head GRU Active
        </span>
      </div>

      {/* Model Flow Nodes */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3 items-center">
        {/* Node 1: Current Network State */}
        <div className="bg-slate-950/80 border border-slate-800 p-4 rounded-xl flex flex-col justify-between h-36">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span>Input $S_t$</span>
            <Activity className="w-4 h-4 text-blue-400" />
          </div>
          <div>
            <div className="text-xs font-mono font-bold text-slate-100">Observed State</div>
            <div className="text-sm font-extrabold font-mono text-amber-400 mt-1">{currentState}</div>
          </div>
          <div className="text-[10px] font-mono text-slate-500">7 Continuous Features (T=20)</div>
        </div>

        {/* Node 2: Latent Representation */}
        <div className="bg-purple-950/20 border border-purple-500/30 p-4 rounded-xl flex flex-col justify-between h-36 relative">
          <div className="flex items-center justify-between text-xs font-mono text-purple-400">
            <span>Latent $h_t$</span>
            <Layers className="w-4 h-4 text-purple-400" />
          </div>
          <div>
            <div className="text-xs font-mono font-bold text-purple-200">World Model Latent</div>
            <div className="text-xs font-mono text-purple-300 mt-1">128-Dim GRU State</div>
          </div>
          <div className="text-[10px] font-mono text-purple-400/80">Learned Dynamics Manifold</div>
        </div>

        {/* Node 3: Head Decoders */}
        <div className="bg-blue-950/20 border border-blue-500/30 p-4 rounded-xl flex flex-col justify-between h-36">
          <div className="flex items-center justify-between text-xs font-mono text-blue-400">
            <span>Dual Heads</span>
            <Cpu className="w-4 h-4 text-blue-400" />
          </div>
          <div>
            <div className="text-xs font-mono font-bold text-blue-200">Decoders A & B</div>
            <div className="text-[11px] font-mono text-slate-300 mt-1">Head A: Current (80.6%)</div>
            <div className="text-[11px] font-mono text-blue-300">Head B: Forecast (91.4%)</div>
          </div>
          <div className="text-[10px] font-mono text-blue-400/80">Log-Softmax Projection</div>
        </div>

        {/* Node 4: Predicted Future State */}
        <div className="bg-slate-950/80 border border-rose-500/30 p-4 rounded-xl flex flex-col justify-between h-36">
          <div className="flex items-center justify-between text-xs font-mono text-rose-400">
            <span>Forecast S_(t+1)</span>
            <GitCommit className="w-4 h-4 text-rose-400" />
          </div>
          <div>
            <div className="text-xs font-mono font-bold text-slate-100">Projected State</div>
            <div className="text-sm font-extrabold font-mono text-rose-400 mt-1">{nextState}</div>
          </div>
          <div className="text-[10px] font-mono text-rose-300">Risk Prob: {Math.round(nextProb * 100)}%</div>
        </div>

        {/* Node 5: Attack Progression */}
        <div className="bg-slate-950/80 border border-slate-800 p-4 rounded-xl flex flex-col justify-between h-36">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span>Adversary Phase</span>
            <Database className="w-4 h-4 text-purple-400" />
          </div>
          <div>
            <div className="text-xs font-mono font-bold text-slate-100">MITRE Kill Chain</div>
            <div className="text-xs font-mono text-slate-300 mt-1 line-clamp-2">{nextStage}</div>
          </div>
          <div className="text-[10px] font-mono text-emerald-400">Proactive Early Warning</div>
        </div>
      </div>
    </div>
  );
};
