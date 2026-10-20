import React, { useState } from 'react';
import { usePolling } from '../hooks/usePolling';
import { forecastApi } from '../services/forecastApi';
import { ForecastTimeline } from '../components/forecasting/ForecastTimeline';
import { AttackProbabilityGraph } from '../components/forecasting/AttackProbabilityGraph';
import { AttackProgressionFlow } from '../components/forecasting/AttackProgressionFlow';
import { WorldModelFlow } from '../components/dashboard/WorldModelFlow';
import { FeatureImportanceChart } from '../components/explanations/FeatureImportanceChart';
import { Card } from '../components/common/Card';
import { ChartSkeleton } from '../components/common/Skeleton';
import { TrendingUp, Sparkles, Brain, Cpu, ArrowRight } from 'lucide-react';

export const AttackForecast: React.FC = () => {
  const [horizon, setHorizon] = useState<number>(5);

  const { data: forecast, isLoading } = usePolling(
    () => forecastApi.getForecast(horizon),
    10000
  );

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-blue-950/40 via-purple-950/30 to-slate-900 border border-blue-500/30 rounded-2xl p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="p-1.5 rounded-lg bg-blue-500/20 text-blue-400 border border-blue-500/30">
                <TrendingUp className="w-5 h-5" />
              </span>
              <h2 className="text-xl font-bold text-white tracking-wide">
                Temporal Network World Model Forecast
              </h2>
            </div>
            <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
              Predicting multi-step adversary progression prior to hostile exploitation. Our dual-head GRU approximates network dynamics: $S_t \rightarrow h_t \in \mathbb&#123;R&#125;^{'{128}'} \rightarrow P(S_{'{t+K}'} \mid S_t)$.
            </p>
          </div>

          {/* Horizon Selection Tabs */}
          <div className="flex items-center gap-2 bg-slate-950 p-1.5 rounded-xl border border-slate-800 font-mono text-xs">
            <span className="text-slate-400 px-2">Look-Ahead:</span>
            {[3, 5, 8, 10].map((h) => (
              <button
                key={h}
                onClick={() => setHorizon(h)}
                className={`px-3 py-1.5 rounded-lg transition-colors ${
                  horizon === h
                    ? 'bg-blue-600 text-white font-bold shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                +{h} Steps
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 1. Multi-Step Future State Timeline (+1 to +K) */}
      {isLoading || !forecast ? (
        <ChartSkeleton />
      ) : (
        <ForecastTimeline
          currentState={forecast.current_state}
          futureStates={forecast.future_states}
        />
      )}

      {/* 2. Attack Probability Curve Graph & Progression Flow */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          {forecast ? (
            <AttackProbabilityGraph data={forecast.probability_curve} />
          ) : (
            <ChartSkeleton />
          )}
        </div>

        <div>
          {forecast ? (
            <div className="h-full flex flex-col justify-between">
              <AttackProgressionFlow
                currentStageId="RECONNAISSANCE"
                predictedNextStageId="INITIAL_ACCESS"
                highRiskStageIds={['COMMAND_AND_CONTROL', 'EXFILTRATION', 'IMPACT']}
              />
            </div>
          ) : (
            <ChartSkeleton />
          )}
        </div>
      </div>

      {/* 3. Deep World Model Architecture Flow */}
      <WorldModelFlow forecast={forecast || undefined} />

      {/* 4. Feature Attributions for Forecast */}
      {forecast?.attributions && (
        <FeatureImportanceChart
          features={forecast.attributions.map((a) => ({
            feature: a.feature,
            importance: Math.abs(a.impact),
            direction: a.impact >= 0 ? 'Positive' : 'Negative',
            description: a.description,
          }))}
          rationale={forecast.what_happens_next?.rationale}
        />
      )}
    </div>
  );
};
