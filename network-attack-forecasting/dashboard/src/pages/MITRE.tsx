import React from 'react';
import { usePolling } from '../hooks/usePolling';
import { modelApi } from '../services/modelApi';
import { MitreHeatmap } from '../components/mitre/MitreHeatmap';
import { CardSkeleton } from '../components/common/Skeleton';
import { Crosshair, Shield, BookOpen, Layers } from 'lucide-react';

export const MITRE: React.FC = () => {
  const { data: mitreData, isLoading } = usePolling(
    () => modelApi.getMitreMapping(),
    15000
  );

  return (
    <div className="space-y-6">
      {/* Framework Summary Banner */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="p-1.5 rounded-lg bg-purple-500/20 text-purple-400 border border-purple-500/30">
                <Crosshair className="w-5 h-5" />
              </span>
              <h2 className="text-xl font-bold text-white tracking-wide">
                MITRE ATT&CK Enterprise Framework Alignment
              </h2>
            </div>
            <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
              Heuristic and algorithmic mapping of temporal state sequences to standardized adversary tactics and techniques. Integrates real-time flow telemetry with predictive look-ahead threat forecasting.
            </p>
          </div>

          <div className="flex items-center gap-3 font-mono text-xs">
            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-center">
              <span className="text-[10px] text-slate-500 uppercase block">Enterprise Tactics</span>
              <span className="text-lg font-bold text-purple-400">06</span>
            </div>
            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-center">
              <span className="text-[10px] text-slate-500 uppercase block">Monitored TTPs</span>
              <span className="text-lg font-bold text-blue-400">12</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Heatmap Matrix */}
      {isLoading || !mitreData ? (
        <CardSkeleton />
      ) : (
        <MitreHeatmap matrix={mitreData.matrix} />
      )}
    </div>
  );
};
