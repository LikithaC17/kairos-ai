import React, { useState, useMemo } from 'react';
import { Search, Filter, ArrowUpDown, ChevronLeft, ChevronRight, Eye } from 'lucide-react';
import { Threat, SeverityLevel } from '../../types';
import { SeverityBadge, StateBadge } from '../common/Badge';
import { formatTime } from '../../utils';

interface ThreatTableProps {
  threats: Threat[];
  onSelectThreat: (threat: Threat) => void;
}

export const ThreatTable: React.FC<ThreatTableProps> = ({ threats, onSelectThreat }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [protocolFilter, setProtocolFilter] = useState<string>('ALL');
  const [sortField, setSortField] = useState<'timestamp' | 'severity' | 'confidence'>('timestamp');
  const [sortAsc, setSortAsc] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 8;

  // Filter and sort
  const filteredThreats = useMemo(() => {
    return threats.filter((t) => {
      const matchSearch =
        t.source_ip.toLowerCase().includes(searchTerm.toLowerCase()) ||
        t.destination_ip.toLowerCase().includes(searchTerm.toLowerCase()) ||
        t.threat_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
        t.mitre_technique.toLowerCase().includes(searchTerm.toLowerCase());
      const matchSeverity = severityFilter === 'ALL' || t.severity === severityFilter;
      const matchProtocol = protocolFilter === 'ALL' || t.protocol === protocolFilter;
      return matchSearch && matchSeverity && matchProtocol;
    }).sort((a, b) => {
      let valA: any = a[sortField];
      let valB: any = b[sortField];
      if (sortField === 'timestamp') {
        valA = new Date(a.timestamp).getTime();
        valB = new Date(b.timestamp).getTime();
      }
      return sortAsc ? (valA > valB ? 1 : -1) : (valA < valB ? 1 : -1);
    });
  }, [threats, searchTerm, severityFilter, protocolFilter, sortField, sortAsc]);

  // Pagination
  const totalPages = Math.ceil(filteredThreats.length / pageSize) || 1;
  const paginatedThreats = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredThreats.slice(start, start + pageSize);
  }, [filteredThreats, currentPage, pageSize]);

  const handleSort = (field: 'timestamp' | 'severity' | 'confidence') => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden flex flex-col justify-between">
      {/* Controls Bar: Search + Filters */}
      <div className="p-4 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3 bg-slate-950/40">
        <div className="relative flex-1 min-w-[240px] max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by IP, technique, threat vector..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1);
            }}
            className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 font-mono"
          />
        </div>

        <div className="flex items-center gap-2">
          {/* Severity Filter */}
          <select
            value={severityFilter}
            onChange={(e) => {
              setSeverityFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 font-mono focus:outline-none focus:border-blue-500"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>

          {/* Protocol Filter */}
          <select
            value={protocolFilter}
            onChange={(e) => {
              setProtocolFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 font-mono focus:outline-none focus:border-blue-500"
          >
            <option value="ALL">All Protocols</option>
            <option value="TCP">TCP</option>
            <option value="UDP">UDP</option>
            <option value="ICMP">ICMP</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 uppercase tracking-wider">
            <tr>
              <th
                onClick={() => handleSort('timestamp')}
                className="py-3 px-4 cursor-pointer hover:text-slate-200"
              >
                <div className="flex items-center gap-1">
                  <span>Time</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="py-3 px-4">Source Endpoint</th>
              <th className="py-3 px-4">Destination</th>
              <th className="py-3 px-4">Proto</th>
              <th className="py-3 px-4">Threat Type</th>
              <th
                onClick={() => handleSort('severity')}
                className="py-3 px-4 cursor-pointer hover:text-slate-200"
              >
                <div className="flex items-center gap-1">
                  <span>Severity</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th
                onClick={() => handleSort('confidence')}
                className="py-3 px-4 cursor-pointer hover:text-slate-200"
              >
                <div className="flex items-center gap-1">
                  <span>Confidence</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {paginatedThreats.length === 0 ? (
              <tr>
                <td colSpan={9} className="py-8 text-center text-slate-500 font-sans">
                  No active threats match current search filters.
                </td>
              </tr>
            ) : (
              paginatedThreats.map((threat) => (
                <tr
                  key={threat.id}
                  onClick={() => onSelectThreat(threat)}
                  className="hover:bg-slate-800/40 cursor-pointer transition-colors"
                >
                  <td className="py-3 px-4 text-slate-400">{formatTime(threat.timestamp)}</td>
                  <td className="py-3 px-4 text-slate-200 font-semibold">
                    {threat.source_ip}:{threat.source_port}
                  </td>
                  <td className="py-3 px-4 text-slate-300">
                    {threat.destination_ip}:{threat.destination_port}
                  </td>
                  <td className="py-3 px-4 text-blue-400">{threat.protocol}</td>
                  <td className="py-3 px-4 text-slate-200">
                    <div>{threat.threat_type}</div>
                    <span className="text-[10px] text-purple-400 font-mono">{threat.mitre_technique}</span>
                  </td>
                  <td className="py-3 px-4">
                    <SeverityBadge severity={threat.severity} size="sm" />
                  </td>
                  <td className="py-3 px-4 text-emerald-400 font-bold">
                    {(threat.confidence * 100).toFixed(0)}%
                  </td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded text-[11px] bg-slate-800 text-slate-300 border border-slate-700">
                      {threat.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectThreat(threat);
                      }}
                      className="p-1 rounded bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition-colors"
                      title="Inspect Threat Evidence"
                    >
                      <Eye className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="p-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400 font-mono bg-slate-950/40">
        <div>
          Showing {filteredThreats.length > 0 ? (currentPage - 1) * pageSize + 1 : 0} to{' '}
          {Math.min(currentPage * pageSize, filteredThreats.length)} of {filteredThreats.length} detections
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="p-1 rounded bg-slate-900 border border-slate-800 text-slate-400 hover:text-white disabled:opacity-30"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span>
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            className="p-1 rounded bg-slate-900 border border-slate-800 text-slate-400 hover:text-white disabled:opacity-30"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
