import React from 'react';
import { Play, Pause, RotateCcw, FastForward, PlayCircle, Settings2 } from 'lucide-react';
import { SimulationScenario } from '../../types';

interface SimulationControlsProps {
  scenarios: SimulationScenario[];
  selectedScenario: string;
  onScenarioChange: (scenarioId: string) => void;
  isRunning: boolean;
  onStart: () => void;
  onPause: () => void;
  onReset: () => void;
  onStepForward: () => void;
  horizon: number;
  onHorizonChange: (h: number) => void;
  speed: number;
  onSpeedChange: (speed: number) => void;
}

export const SimulationControls: React.FC<SimulationControlsProps> = ({
  scenarios,
  selectedScenario,
  onScenarioChange,
  isRunning,
  onStart,
  onPause,
  onReset,
  onStepForward,
  horizon,
  onHorizonChange,
  speed,
  onSpeedChange,
}) => {
  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 space-y-5">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <PlayCircle className="w-4 h-4 text-blue-400" />
          <h3 className="text-sm font-semibold tracking-wider text-slate-100 uppercase">
            Attack Simulation & Demonstration Rig
          </h3>
        </div>
        <span className="text-xs font-mono text-slate-400">SOC Interactive Mode</span>
      </div>

      {/* Grid of parameters */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
        {/* Scenario Selection */}
        <div>
          <label className="block text-slate-400 mb-1.5 uppercase tracking-wider text-[11px]">
            Attack Scenario
          </label>
          <select
            value={selectedScenario}
            onChange={(e) => onScenarioChange(e.target.value)}
            disabled={isRunning}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 text-xs focus:outline-none focus:border-blue-500 disabled:opacity-50"
          >
            {scenarios.map((sc) => (
              <option key={sc.id} value={sc.id}>
                {sc.name}
              </option>
            ))}
          </select>
        </div>

        {/* Forecast Horizon (K-steps) */}
        <div>
          <label className="block text-slate-400 mb-1.5 uppercase tracking-wider text-[11px]">
            Look-Ahead Horizon ($K$-steps): {horizon}
          </label>
          <input
            type="range"
            min={1}
            max={10}
            value={horizon}
            onChange={(e) => onHorizonChange(Number(e.target.value))}
            className="w-full accent-blue-500 bg-slate-800 rounded-lg cursor-pointer h-2 mt-2"
          />
        </div>

        {/* Speed */}
        <div>
          <label className="block text-slate-400 mb-1.5 uppercase tracking-wider text-[11px]">
            Simulation Replay Speed
          </label>
          <div className="flex items-center gap-2">
            {[
              { label: '0.5x', val: 2000 },
              { label: '1.0x', val: 1000 },
              { label: '2.0x', val: 500 },
              { label: '4.0x', val: 250 },
            ].map((sp) => (
              <button
                key={sp.label}
                onClick={() => onSpeedChange(sp.val)}
                className={`flex-1 py-1.5 rounded border transition-colors ${
                  speed === sp.val
                    ? 'bg-blue-600 text-white border-blue-500 font-bold'
                    : 'bg-slate-950 text-slate-400 border-slate-800 hover:text-white'
                }`}
              >
                {sp.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Playback Control Buttons */}
      <div className="pt-3 border-t border-slate-800 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          {isRunning ? (
            <button
              onClick={onPause}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-amber-600 text-white font-semibold text-xs hover:bg-amber-500 transition-colors shadow"
            >
              <Pause className="w-4 h-4" />
              <span>Pause Simulation</span>
            </button>
          ) : (
            <button
              onClick={onStart}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white font-semibold text-xs hover:bg-blue-500 transition-colors shadow"
            >
              <Play className="w-4 h-4" />
              <span>Start Simulation</span>
            </button>
          )}

          <button
            onClick={onStepForward}
            disabled={isRunning}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-xs hover:bg-slate-700 transition-colors disabled:opacity-40"
          >
            <FastForward className="w-3.5 h-3.5" />
            <span>Step +1</span>
          </button>

          <button
            onClick={onReset}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 text-xs hover:text-white hover:border-slate-700 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset</span>
          </button>
        </div>

        <div className="text-xs font-mono text-slate-400">
          Status:{' '}
          <span className={isRunning ? 'text-emerald-400 font-bold' : 'text-slate-500'}>
            {isRunning ? '● Replaying Sequence Telemetry' : 'Paused / Ready'}
          </span>
        </div>
      </div>
    </div>
  );
};
