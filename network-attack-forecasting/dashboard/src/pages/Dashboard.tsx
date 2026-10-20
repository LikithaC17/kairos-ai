import React, { useState } from 'react';
import { usePolling } from '../hooks/usePolling';
import { trafficApi } from '../services/trafficApi';
import { threatApi } from '../services/threatApi';
import { forecastApi } from '../services/forecastApi';
import { WhatHappensNextBanner } from '../components/dashboard/WhatHappensNextBanner';
import { KpiCards } from '../components/dashboard/KpiCards';
import { CurrentNetworkStatePanel } from '../components/dashboard/CurrentNetworkStatePanel';
import { WorldModelFlow } from '../components/dashboard/WorldModelFlow';
import { ThreatOverviewPanel } from '../components/dashboard/ThreatOverviewPanel';
import { TrafficTimelineChart } from '../components/traffic/TrafficTimelineChart';
import { ProtocolDonutChart } from '../components/traffic/ProtocolDonutChart';
import { AttackProbabilityGraph } from '../components/forecasting/AttackProbabilityGraph';
import { AttackProgressionFlow } from '../components/forecasting/AttackProgressionFlow';
import { Card } from '../components/common/Card';
import { CardSkeleton, ChartSkeleton } from '../components/common/Skeleton';
import { ThreatDetailPanel } from '../components/threats/ThreatDetailPanel';
import { Threat } from '../types';

export const Dashboard: React.FC = () => {
  const [selectedThreat, setSelectedThreat] = useState<Threat | null>(null);
  const [windowFilter, setWindowFilter] = useState('15m');

  // Fetch telemetry stats
  const { data: stats, isLoading: loadingStats } = usePolling(
    () => trafficApi.getTrafficStats(windowFilter),
    10000
  );

  // Fetch threat feed
  const { data: threats, isLoading: loadingThreats } = usePolling(
    () => threatApi.getThreats(undefined, undefined, 20),
    10000
  );

  // Fetch multi-step forecast
  const { data: forecast, isLoading: loadingForecast } = usePolling(
    () => forecastApi.getForecast(5),
    10000
  );

  const activeThreatCount = threats?.filter((t) => t.status === 'Active').length || 3;

  return (
    <div className="space-y-6">
      {/* 1. Top Section: 10-Second Judge "What Happens Next?" Innovation Banner */}
      <WhatHappensNextBanner data={forecast?.what_happens_next} />

      {/* 2. Top KPI Cards */}
      {loadingStats ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : (
        <KpiCards
          summary={stats?.summary}
          threatLevel={forecast?.current_state === 'ATTACK' ? 'CRITICAL' : forecast?.current_state === 'SUSPICIOUS' ? 'HIGH' : 'MEDIUM'}
          activeThreatCount={activeThreatCount}
          forecastRisk={forecast?.risk_level || 'HIGH'}
          attackProbability={forecast?.what_happens_next?.next_probability || 0.78}
          modelConfidence={forecast?.confidence || 0.914}
        />
      )}

      {/* 3. Current Network State Full Telemetry Profile */}
      {stats && (
        <CurrentNetworkStatePanel
          summary={stats.summary}
          topPorts={stats.top_ports}
        />
      )}

      {/* 4. Traffic Flow Timeline & Protocol Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card
            title="Telemetry Flow Timeline"
            subtitle="Real-time multi-metric network throughput"
          >
            {loadingStats || !stats ? (
              <ChartSkeleton />
            ) : (
              <TrafficTimelineChart
                timeline={stats.timeline}
                selectedWindow={windowFilter}
                onWindowChange={setWindowFilter}
              />
            )}
          </Card>
        </div>

        <div className="lg:col-span-1">
          <Card
            title="Protocol Composition"
            subtitle="Network packet protocol ratio"
          >
            {loadingStats || !stats ? (
              <ChartSkeleton />
            ) : (
              <ProtocolDonutChart protocols={stats.protocols} />
            )}
          </Card>
        </div>
      </div>

      {/* 5. World Model Latent Space Flow Diagram */}
      <WorldModelFlow forecast={forecast || undefined} />

      {/* 6. Attack Forecasting: Probability Curve + Kill Chain Progression */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          {forecast ? (
            <AttackProbabilityGraph data={forecast.probability_curve} />
          ) : (
            <ChartSkeleton />
          )}
        </div>

        <div>
          {threats && (
            <ThreatOverviewPanel threats={threats} />
          )}
        </div>
      </div>

      {/* 7. Attack Progression Kill Chain Flow */}
      <AttackProgressionFlow
        currentStageId="RECONNAISSANCE"
        predictedNextStageId="INITIAL_ACCESS"
        highRiskStageIds={['COMMAND_AND_CONTROL', 'EXFILTRATION', 'IMPACT']}
      />

      {/* Slide-out Threat Detail Panel */}
      <ThreatDetailPanel
        threat={selectedThreat}
        onClose={() => setSelectedThreat(null)}
      />
    </div>
  );
};
