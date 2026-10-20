import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { TrafficAnalysis } from './pages/TrafficAnalysis';
import { ThreatDetection } from './pages/ThreatDetection';
import { AttackForecast } from './pages/AttackForecast';
import { Simulation } from './pages/Simulation';
import { MITRE } from './pages/MITRE';
import { Alerts } from './pages/Alerts';
import { ModelInsights } from './pages/ModelInsights';
import { SystemStatus } from './pages/SystemStatus';
import { Settings } from './pages/Settings';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/traffic" element={<TrafficAnalysis />} />
          <Route path="/threats" element={<ThreatDetection />} />
          <Route path="/forecast" element={<AttackForecast />} />
          <Route path="/simulation" element={<Simulation />} />
          <Route path="/mitre" element={<MITRE />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/model" element={<ModelInsights />} />
          <Route path="/status" element={<SystemStatus />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
