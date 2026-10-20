import React, { useState } from 'react';
import { usePolling } from '../hooks/usePolling';
import { threatApi } from '../services/threatApi';
import { ThreatTable } from '../components/threats/ThreatTable';
import { ThreatDetailPanel } from '../components/threats/ThreatDetailPanel';
import { Threat } from '../types';
import { TableSkeleton } from '../components/common/Skeleton';
import { ShieldAlert, AlertTriangle, CheckCircle, ShieldCheck } from 'lucide-react';

export const ThreatDetection: React.FC = () => {
  const [selectedThreat, setSelectedThreat] = useState<Threat | null>(null);

  const { data: threats, isLoading } = usePolling(
    () => threatApi.getThreats(undefined, undefined, 50),
    10000
  );

  const criticalCount = threats?.filter((t) => t.severity === 'CRITICAL').length || 0;
  const highCount = threats?.filter((t) => t.severity === 'HIGH').length || 0;
  const activeCount = threats?.filter((t) => t.status === 'Active').length || 0;

  return (
    <div className="space-y-6">
      {/* Overview Stat Badges */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono">
        <div className="bg-rose-950/20 border border-rose-500/30 p-4 rounded-xl flex items-center justify-between">
          <div>
            <span className="text-[11px] text-rose-400 uppercase tracking-wider">Critical Threats</span>
            <div className="text-2xl font-bold text-rose-300 mt-1">{criticalCount}</div>
          </div>
          <ShieldAlert className="w-8 h-8 text-rose-400/50" />
        </div>

        <div className="bg-orange-950/20 border border-orange-500/30 p-4 rounded-xl flex items-center justify-between">
          <div>
            <span className="text-[11px] text-orange-400 uppercase tracking-wider">High Risk Vectors</span>
            <div className="text-2xl font-bold text-orange-300 mt-1">{highCount}</div>
          </div>
          <AlertTriangle className="w-8 h-8 text-orange-400/50" />
        </div>

        <div className="bg-blue-950/20 border border-blue-500/30 p-4 rounded-xl flex items-center justify-between">
          <div>
            <span className="text-[11px] text-blue-400 uppercase tracking-wider">Active Containments</span>
            <div className="text-2xl font-bold text-blue-300 mt-1">{activeCount}</div>
          </div>
          <ShieldCheck className="w-8 h-8 text-blue-400/50" />
        </div>
      </div>

      {/* Main Threat Detections Table */}
      {isLoading || !threats ? (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <TableSkeleton rows={8} />
        </div>
      ) : (
        <ThreatTable
          threats={threats}
          onSelectThreat={(t) => setSelectedThreat(t)}
        />
      )}

      {/* Slide-out Threat Detail Panel */}
      <ThreatDetailPanel
        threat={selectedThreat}
        onClose={() => setSelectedThreat(null)}
      />
    </div>
  );
};
