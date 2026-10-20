import React, { useState } from 'react';
import { usePolling } from '../hooks/usePolling';
import { threatApi } from '../services/threatApi';
import { Alert, SeverityLevel } from '../types';
import { SeverityBadge, StateBadge } from '../components/common/Badge';
import { formatTime } from '../utils';
import { Bell, CheckCheck, Search, Filter, ShieldAlert, ArrowRight } from 'lucide-react';
import { TableSkeleton } from '../components/common/Skeleton';

export const Alerts: React.FC = () => {
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [reviewedIds, setReviewedIds] = useState<Set<string>>(new Set());

  const { data: alertsData, isLoading } = usePolling(
    () => threatApi.getAlerts(),
    10000
  );

  const toggleReviewed = (id: string) => {
    setReviewedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const markAllReviewed = () => {
    if (alertsData) {
      setReviewedIds(new Set(alertsData.map((a) => a.id)));
    }
  };

  const filteredAlerts = (alertsData || []).filter((a) => {
    const matchSev = filterSeverity === 'ALL' || a.severity === filterSeverity;
    const matchSearch =
      a.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.source_ip.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.destination_ip.toLowerCase().includes(searchTerm.toLowerCase());
    return matchSev && matchSearch;
  });

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900/90 border border-slate-800 rounded-xl p-5">
        <div>
          <h2 className="text-base font-bold text-white tracking-wide uppercase flex items-center gap-2">
            <Bell className="w-5 h-5 text-rose-400" />
            Security Operations Center Alerts Feed
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time proactive intrusion warnings and multi-step escalation alerts
          </p>
        </div>

        <button
          onClick={markAllReviewed}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 text-xs font-mono text-slate-200 hover:bg-slate-700 transition-colors"
        >
          <CheckCheck className="w-4 h-4 text-emerald-400" />
          <span>Mark All As Reviewed</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900/90 border border-slate-800 rounded-xl p-4">
        <div className="relative flex-1 min-w-[240px] max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search alerts by IP or title..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-100 placeholder-slate-500 font-mono focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="text-slate-400">Severity:</span>
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>
      </div>

      {/* Alerts Feed List */}
      {isLoading ? (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <TableSkeleton rows={6} />
        </div>
      ) : (
        <div className="space-y-3">
          {filteredAlerts.length === 0 ? (
            <div className="p-8 text-center text-slate-500 font-mono text-xs bg-slate-900/60 rounded-xl border border-slate-800">
              No security alerts match the selected criteria.
            </div>
          ) : (
            filteredAlerts.map((alert) => {
              const isReviewed = reviewedIds.has(alert.id) || alert.reviewed;
              return (
                <div
                  key={alert.id}
                  className={`p-4 rounded-xl border transition-all ${
                    isReviewed
                      ? 'bg-slate-950/40 border-slate-800 opacity-60'
                      : alert.severity === 'CRITICAL'
                      ? 'bg-rose-950/20 border-rose-500/40'
                      : alert.severity === 'HIGH'
                      ? 'bg-orange-950/20 border-orange-500/40'
                      : 'bg-slate-900 border-slate-800'
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
                    <div className="flex items-center gap-3">
                      <SeverityBadge severity={alert.severity} size="sm" />
                      <h4 className="text-xs font-bold text-slate-100">{alert.title}</h4>
                      <span className="text-[11px] font-mono text-purple-400 bg-purple-500/10 px-1.5 py-0.2 rounded border border-purple-500/20">
                        {alert.mitre_id}
                      </span>
                    </div>

                    <div className="flex items-center gap-3 text-xs font-mono">
                      <span className="text-slate-500">{formatTime(alert.timestamp)}</span>
                      <button
                        onClick={() => toggleReviewed(alert.id)}
                        className={`px-2 py-0.5 rounded text-[10px] font-semibold transition-colors ${
                          isReviewed
                            ? 'bg-slate-800 text-slate-400 hover:text-white'
                            : 'bg-blue-600 text-white hover:bg-blue-500'
                        }`}
                      >
                        {isReviewed ? 'Reviewed ✓' : 'Mark Reviewed'}
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 text-xs font-mono text-slate-300">
                    <div>
                      <span className="text-slate-500 text-[10px] block">SOURCE → DESTINATION</span>
                      <span>
                        {alert.source_ip} → {alert.destination_ip}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <div>
                        <span className="text-slate-500 text-[10px] block">STATE TRANSITION</span>
                        <div className="flex items-center gap-1.5 mt-0.5">
                          <StateBadge state={alert.current_state} size="sm" />
                          <ArrowRight className="w-3 h-3 text-slate-500" />
                          <StateBadge state={alert.predicted_next_state} size="sm" />
                        </div>
                      </div>
                    </div>

                    <div>
                      <span className="text-slate-500 text-[10px] block">PREDICTION RISK & CERTAINTY</span>
                      <span className="text-blue-400 font-bold">
                        P: {Math.round(alert.probability * 100)}%
                      </span>{' '}
                      · Conf: {Math.round(alert.confidence * 100)}%
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
};
