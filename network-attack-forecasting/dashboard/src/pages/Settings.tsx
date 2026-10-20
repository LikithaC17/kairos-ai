import React, { useState } from 'react';
import { Card } from '../components/common/Card';
import { API_BASE_URL } from '../services/api';
import { Settings as SettingsIcon, CheckCircle } from 'lucide-react';

export const Settings: React.FC = () => {
  const [apiUrl, setApiUrl] = useState(API_BASE_URL);
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    if (typeof window !== 'undefined' && window.localStorage) {
      if (apiUrl.trim()) {
        window.localStorage.setItem('NETSCOPE_API_URL', apiUrl.trim());
      } else {
        window.localStorage.removeItem('NETSCOPE_API_URL');
      }
    }
    setSaved(true);
    setTimeout(() => {
      setSaved(false);
      window.location.reload();
    }, 800);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6">
        <div className="flex items-center gap-2 mb-2">
          <span className="p-1.5 rounded-lg bg-blue-500/20 text-blue-400 border border-blue-500/30">
            <SettingsIcon className="w-5 h-5" />
          </span>
          <h2 className="text-xl font-bold text-white tracking-wide">
            Platform & SOC Configuration
          </h2>
        </div>
        <p className="text-xs text-slate-300">
          Configure API endpoints, telemetry polling, and SOC operational parameters.
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        <Card title="API Ingestion & Serving Endpoints" subtitle="Backend REST and inference engine locations">
          <div className="space-y-4 font-mono text-xs">
            <div>
              <label className="block text-slate-400 mb-1.5 uppercase tracking-wider text-[11px]">
                API Base URL (Environment: VITE_API_URL)
              </label>
              <input
                type="text"
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
                placeholder="https://cyber-network-traffic.onrender.com"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-blue-500 font-mono"
              />
              <span className="text-[10px] text-slate-500 mt-1 block">
                Production Backend: https://cyber-network-traffic.onrender.com
              </span>
            </div>
          </div>
        </Card>

        <Card title="SOC Alerting & Sensitivity Calibration" subtitle="Notification thresholds for early warning">
          <div className="space-y-4 font-mono text-xs">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-slate-200 font-bold block">Early Warning Trigger Threshold</span>
                <span className="text-slate-400 text-[11px]">
                  Minimum forecast attack probability required to dispatch proactive early warning.
                </span>
              </div>
              <select className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-slate-200 focus:outline-none">
                <option value="0.7">70% (Balanced)</option>
                <option value="0.8">80% (High Precision)</option>
                <option value="0.6">60% (Maximum Lead Time)</option>
              </select>
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-slate-800">
              <div>
                <span className="text-slate-200 font-bold block">Sequence History Window ($T$)</span>
                <span className="text-slate-400 text-[11px]">
                  Number of prior time steps ingested into the GRU hidden representation.
                </span>
              </div>
              <span className="text-blue-400 font-bold">20 steps (Fixed)</span>
            </div>
          </div>
        </Card>

        <div className="flex items-center justify-between">
          {saved ? (
            <span className="text-xs font-mono text-emerald-400 flex items-center gap-1.5">
              <CheckCircle className="w-4 h-4" />
              Settings updated successfully!
            </span>
          ) : (
            <span />
          )}

          <button
            type="submit"
            className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold font-mono tracking-wider transition-colors shadow"
          >
            Save Configuration
          </button>
        </div>
      </form>
    </div>
  );
};
