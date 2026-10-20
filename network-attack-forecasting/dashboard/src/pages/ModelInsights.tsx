import React from 'react';
import { usePolling } from '../hooks/usePolling';
import { modelApi } from '../services/modelApi';
import { FeatureImportanceChart } from '../components/explanations/FeatureImportanceChart';
import { Card } from '../components/common/Card';
import { CardSkeleton } from '../components/common/Skeleton';
import { Cpu, Layers, GitBranch, Award, CheckCircle2, Database, Shield } from 'lucide-react';

export const ModelInsights: React.FC = () => {
  const { data: modelInfo, isLoading: loadingInfo } = usePolling(
    () => modelApi.getModelInfo(),
    30000
  );

  const { data: explainability, isLoading: loadingExplain } = usePolling(
    () => modelApi.getModelExplain(),
    30000
  );

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="p-1.5 rounded-lg bg-purple-500/20 text-purple-400 border border-purple-500/30">
                <Cpu className="w-5 h-5" />
              </span>
              <h2 className="text-xl font-bold text-white tracking-wide">
                AI World Model Specification & Architecture
              </h2>
            </div>
            <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
              PyTorch Dual-Head Recurrent World Model (2-Layer GRU) trained with strict chronological splitting to eliminate look-ahead bias and model evolving network attack states.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-mono text-xs flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4" />
              Model Checkpoint: Frozen
            </span>
          </div>
        </div>
      </div>

      {/* Actual Model Metrics Grid */}
      {modelInfo ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 font-mono">
          <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
            <span className="text-[10px] text-slate-500 uppercase block">CURRENT STATE ACCURACY</span>
            <div className="text-xl font-bold text-blue-400 mt-1">
              {(modelInfo.evaluation_metrics.current_state_accuracy * 100).toFixed(2)}%
            </div>
            <span className="text-[10px] text-slate-500">Holdout Partition</span>
          </div>

          <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
            <span className="text-[10px] text-slate-500 uppercase block">NEXT STATE FORECAST ACC</span>
            <div className="text-xl font-bold text-emerald-400 mt-1">
              {(modelInfo.evaluation_metrics.next_state_accuracy * 100).toFixed(2)}%
            </div>
            <span className="text-[10px] text-slate-500">Dual-Head Head B</span>
          </div>

          <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
            <span className="text-[10px] text-slate-500 uppercase block">TEST NLL LOSS</span>
            <div className="text-xl font-bold text-purple-400 mt-1">
              {modelInfo.evaluation_metrics.test_loss.toFixed(4)}
            </div>
            <span className="text-[10px] text-slate-500">CrossEntropyLoss</span>
          </div>

          <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
            <span className="text-[10px] text-slate-500 uppercase block">AUROC METRIC</span>
            <div className="text-xl font-bold text-cyan-400 mt-1">
              {(modelInfo.evaluation_metrics.auc_roc * 100).toFixed(1)}%
            </div>
            <span className="text-[10px] text-slate-500">Macro Averaged</span>
          </div>

          <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
            <span className="text-[10px] text-slate-500 uppercase block">PARAMETERS</span>
            <div className="text-xl font-bold text-slate-200 mt-1">
              {modelInfo.parameters.toLocaleString()}
            </div>
            <span className="text-[10px] text-slate-500">Trainable Weights</span>
          </div>

          <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
            <span className="text-[10px] text-slate-500 uppercase block">HIDDEN DIMENSION</span>
            <div className="text-xl font-bold text-slate-200 mt-1">
              {modelInfo.hidden_dimension} dim
            </div>
            <span className="text-[10px] text-slate-500">Latent Embedding</span>
          </div>
        </div>
      ) : (
        <CardSkeleton />
      )}

      {/* Model Architecture Details */}
      {modelInfo && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 font-mono text-xs">
          <Card title="Structural Topology" subtitle="Recurrent backbone and decoding heads">
            <div className="space-y-3 text-slate-300">
              <div className="flex justify-between pb-2 border-b border-slate-800">
                <span className="text-slate-500">Model Family:</span>
                <span className="font-bold text-slate-100">{modelInfo.model_type}</span>
              </div>
              <div className="flex justify-between pb-2 border-b border-slate-800">
                <span className="text-slate-500">Input Feature Vector:</span>
                <span className="text-blue-400">7 Continuous Features ($T=20$)</span>
              </div>
              <div className="flex justify-between pb-2 border-b border-slate-800">
                <span className="text-slate-500">Scaling Strategy:</span>
                <span className="text-slate-200">Log1p + StandardScaler (Zero Leakage)</span>
              </div>
              <div className="flex justify-between pb-2 border-b border-slate-800">
                <span className="text-slate-500">Head A Function:</span>
                <span className="text-slate-200">{modelInfo.heads.head_a}</span>
              </div>
              <div className="flex justify-between pb-2 border-b border-slate-800">
                <span className="text-slate-500">Head B Function:</span>
                <span className="text-purple-400">{modelInfo.heads.head_b}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Loss Formulation:</span>
                <span className="text-emerald-400">Weighted Inverse-Frequency CrossEntropy</span>
              </div>
            </div>
          </Card>

          <Card title="Feature Contract & Inputs" subtitle="Normalized flow telemetry schema">
            <div className="space-y-2">
              {modelInfo.feature_list.map((feat, idx) => (
                <div
                  key={feat}
                  className="flex items-center justify-between p-2 rounded bg-slate-950/60 border border-slate-800/80"
                >
                  <span className="text-slate-300 font-bold">
                    0{idx + 1}. {feat}
                  </span>
                  <span className="text-slate-500 text-[10px]">float32 continuous</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Feature Attribution and Explainability */}
      {explainability && (
        <FeatureImportanceChart
          features={explainability.global_importance}
          rationale={explainability.example_rationale}
        />
      )}
    </div>
  );
};
