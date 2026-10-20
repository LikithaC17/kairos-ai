import React from 'react';
import { X, ShieldAlert, Cpu, Sparkles, Network, ArrowRight } from 'lucide-react';
import { Threat } from '../../types';
import { StateBadge, SeverityBadge } from '../common/Badge';
import { formatTime, formatBytes } from '../../utils';

interface ThreatDetailPanelProps {
  threat: Threat | null;
  onClose: () => void;
}

export const ThreatDetailPanel: React.FC<ThreatDetailPanelProps> = ({ threat, onClose }) => {
  if (!threat) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-[480px] z-50 bg-[#0d1527] border-l border-slate-800 shadow-2xl flex flex-col justify-between overflow-hidden">
      {/* Header */}
      <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
        <div className="flex items-center gap-2.5">
          <ShieldAlert className="w-5 h-5 text-rose-400" />
          <div>
            <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wide">
              Threat Vector Investigation
            </h3>
            <p className="text-[11px] font-mono text-slate-400">{threat.id}</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 p-5 overflow-y-auto space-y-5 text-xs font-mono">
        {/* Threat Summary Banner */}
        <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Classified Threat:</span>
            <span className="text-slate-100 font-bold">{threat.threat_type}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Severity & Status:</span>
            <div className="flex items-center gap-1.5">
              <SeverityBadge severity={threat.severity} size="sm" />
              <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 text-[10px]">
                {threat.status}
              </span>
            </div>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Model Confidence:</span>
            <span className="text-emerald-400 font-bold">{(threat.confidence * 100).toFixed(1)}%</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Security State:</span>
            <StateBadge state={threat.state} size="sm" />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">MITRE Technique:</span>
            <span className="px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
              {threat.mitre_technique}
            </span>
          </div>
        </div>

        {/* Socket Endpoint Details */}
        <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-3">
          <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Network className="w-3.5 h-3.5 text-blue-400" />
            <span>Connection Endpoints</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-slate-300">
            <div>
              <span className="text-[10px] text-slate-500 block">SOURCE ADDRESS</span>
              <span className="font-bold text-slate-200">{threat.source_ip}</span>:
              <span className="text-blue-400">{threat.source_port}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-500 block">DESTINATION ADDRESS</span>
              <span className="font-bold text-slate-200">{threat.destination_ip}</span>:
              <span className="text-rose-400">{threat.destination_port}</span>
            </div>
          </div>
          <div className="pt-2 border-t border-slate-800/80 flex justify-between text-slate-400">
            <span>Protocol: {threat.protocol}</span>
            <span>Recorded: {formatTime(threat.timestamp)}</span>
          </div>
        </div>

        {/* Feature Evidence Matrix */}
        <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-3">
          <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-purple-400" />
            <span>Extracted Telemetry Evidence</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-[11px]">
            <div className="p-2 rounded bg-slate-900 border border-slate-800">
              <span className="text-slate-500 block text-[10px]">PACKET TRANSMISSION RATE</span>
              <span className="font-bold text-slate-200">{threat.evidence.packet_rate} pkts/s</span>
            </div>
            <div className="p-2 rounded bg-slate-900 border border-slate-800">
              <span className="text-slate-500 block text-[10px]">THROUGHPUT BYTE RATE</span>
              <span className="font-bold text-slate-200">{formatBytes(threat.evidence.byte_rate)}/s</span>
            </div>
            <div className="p-2 rounded bg-slate-900 border border-slate-800">
              <span className="text-slate-500 block text-[10px]">INTER-ARRIVAL TIME (IAT)</span>
              <span className="font-bold text-slate-200">{threat.evidence.inter_arrival_time}s</span>
            </div>
            <div className="p-2 rounded bg-slate-900 border border-slate-800">
              <span className="text-slate-500 block text-[10px]">CONNECTION FREQUENCY</span>
              <span className="font-bold text-slate-200">{threat.evidence.connection_frequency} bursts</span>
            </div>
            <div className="p-2 rounded bg-slate-900 border border-slate-800">
              <span className="text-slate-500 block text-[10px]">FLOW DURATION</span>
              <span className="font-bold text-slate-200">{threat.evidence.flow_duration}s</span>
            </div>
            <div className="p-2 rounded bg-slate-900 border border-slate-800">
              <span className="text-slate-500 block text-[10px]">PORT ENTROPY</span>
              <span className="font-bold text-slate-200">{threat.evidence.entropy}</span>
            </div>
          </div>
        </div>

        {/* Explainable AI: Why was this detected? */}
        <div className="bg-amber-950/20 p-4 rounded-xl border border-amber-600/30 space-y-2">
          <div className="flex items-center gap-1.5 text-amber-400 font-bold uppercase tracking-wider text-[11px]">
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span>Why was this detected? (XAI Rationale)</span>
          </div>
          <p className="text-slate-300 font-sans text-xs leading-relaxed italic">
            "{threat.explanation}"
          </p>
          <div className="pt-2 border-t border-amber-600/20 text-[10px] text-amber-400/80">
            Attribution derived from model hidden-state perturbation and SHAP feature scoring.
          </div>
        </div>
      </div>

      {/* Footer Actions */}
      <div className="p-4 border-t border-slate-800 bg-slate-900/80 flex items-center justify-between">
        <span className="text-xs text-slate-400 font-mono">SOC Action: Contain Host</span>
        <button
          onClick={onClose}
          className="px-4 py-2 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-500 transition-colors"
        >
          Acknowledge & Close
        </button>
      </div>
    </div>
  );
};
