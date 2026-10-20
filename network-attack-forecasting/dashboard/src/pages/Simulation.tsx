import React, { useState, useEffect, useRef } from 'react';
import { simulationApi } from '../services/simulationApi';
import { SimulationControls } from '../components/simulation/SimulationControls';
import { SimulationStepViewer } from '../components/simulation/SimulationStepViewer';
import { SimulationScenario, SimulationRunResult } from '../types';
import { Card } from '../components/common/Card';
import { CardSkeleton } from '../components/common/Skeleton';
import { PlayCircle, Sparkles, CheckCircle2 } from 'lucide-react';

export const Simulation: React.FC = () => {
  const [scenarios, setScenarios] = useState<SimulationScenario[]>([]);
  const [selectedScenario, setSelectedScenario] = useState('mixed');
  const [horizon, setHorizon] = useState(5);
  const [speed, setSpeed] = useState(1000);
  const [isRunning, setIsRunning] = useState(false);
  const [simResult, setSimResult] = useState<SimulationRunResult | null>(null);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const timerRef = useRef<number | null>(null);

  // Load scenarios on mount
  useEffect(() => {
    simulationApi.getScenarios().then((res) => {
      setScenarios(res);
    });
  }, []);

  // Fetch or regenerate simulation sequence when scenario changes
  useEffect(() => {
    simulationApi.runSimulation(selectedScenario, 25, speed).then((res) => {
      setSimResult(res);
      setCurrentStepIndex(0);
      setIsRunning(false);
    });
  }, [selectedScenario]);

  // Handle Playback Interval
  useEffect(() => {
    if (isRunning && simResult) {
      timerRef.current = window.setInterval(() => {
        setCurrentStepIndex((prev) => {
          if (prev >= simResult.steps.length - 1) {
            setIsRunning(false);
            return prev;
          }
          return prev + 1;
        });
      }, speed);
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isRunning, simResult, speed]);

  const handleStart = () => {
    if (simResult && currentStepIndex >= simResult.steps.length - 1) {
      setCurrentStepIndex(0);
    }
    setIsRunning(true);
  };

  const handlePause = () => {
    setIsRunning(false);
  };

  const handleReset = () => {
    setIsRunning(false);
    setCurrentStepIndex(0);
  };

  const handleStepForward = () => {
    if (simResult && currentStepIndex < simResult.steps.length - 1) {
      setCurrentStepIndex((prev) => prev + 1);
    }
  };

  const activeScenarioObj = scenarios.find((s) => s.id === selectedScenario);

  return (
    <div className="space-y-6">
      {/* Top Scenario Explanation Card */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="p-1.5 rounded-lg bg-blue-500/20 text-blue-400 border border-blue-500/30">
                <PlayCircle className="w-5 h-5" />
              </span>
              <h2 className="text-xl font-bold text-white tracking-wide">
                Interactive Attack Simulation Testbed
              </h2>
            </div>
            <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
              Step-by-step sequential verification of how the NetForecast AI world model anticipates multi-stage intrusion campaigns. Select an adversary scenario and observe how model probabilities react to incoming telemetry.
            </p>
          </div>

          {activeScenarioObj && (
            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-xs font-mono">
              <span className="text-slate-400 block mb-1">Target MITRE Alignment:</span>
              <div className="flex items-center gap-1.5">
                {activeScenarioObj.mitre_targets.length > 0 ? (
                  activeScenarioObj.mitre_targets.map((m) => (
                    <span
                      key={m}
                      className="px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30 font-bold"
                    >
                      {m}
                    </span>
                  ))
                ) : (
                  <span className="text-emerald-400">Normal Baseline Traffic</span>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Simulation Controls */}
      <SimulationControls
        scenarios={scenarios}
        selectedScenario={selectedScenario}
        onScenarioChange={setSelectedScenario}
        isRunning={isRunning}
        onStart={handleStart}
        onPause={handlePause}
        onReset={handleReset}
        onStepForward={handleStepForward}
        horizon={horizon}
        onHorizonChange={setHorizon}
        speed={speed}
        onSpeedChange={setSpeed}
      />

      {/* Step Viewer & Live Progression Feedback */}
      {simResult && simResult.steps.length > 0 ? (
        <SimulationStepViewer
          currentStepIndex={currentStepIndex}
          steps={simResult.steps}
        />
      ) : (
        <CardSkeleton />
      )}
    </div>
  );
};
