// TypeScript Interfaces for NetForecast AI Security World Model

export type SecurityState = 'NORMAL' | 'ELEVATED' | 'SUSPICIOUS' | 'ATTACK';
export type SeverityLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type AlertStatus = 'New' | 'Under Investigation' | 'Acknowledged' | 'Mitigated' | 'Resolved';

export interface TrafficRecord {
  flow_id: string;
  timestamp: string;
  src_ip: string;
  dst_ip: string;
  src_port: number;
  dst_port: number;
  protocol: 'TCP' | 'UDP' | 'ICMP';
  flow_duration: number;
  packet_count: number;
  byte_count: number;
  packet_rate: number;
  byte_rate: number;
  inter_arrival_time: number;
  connection_frequency: number;
  scenario: string;
  state: SecurityState;
  label: string;
  severity: SeverityLevel;
}

export interface TrafficSummary {
  packets_per_sec: number;
  bytes_per_sec: number;
  flows_per_sec: number;
  active_connections: number;
  total_bytes: number;
  total_packets: number;
  unique_src_ips: number;
  unique_dst_ips: number;
  avg_duration: number;
  avg_packet_size: number;
  tcp_udp_ratio: string;
  syn_ack_ratio: number;
}

export interface ProtocolDistribution {
  name: string;
  value: number;
  percentage: number;
  color: string;
}

export interface PortStat {
  port: string;
  count: number;
}

export interface TimelinePoint {
  time: string;
  timestamp: string;
  packets: number;
  bytes: number;
  flows: number;
  packet_rate: number;
  byte_rate: number;
  is_suspicious: boolean;
  state: SecurityState;
}

export interface TrafficStats {
  window: string;
  summary: TrafficSummary;
  protocols: ProtocolDistribution[];
  top_ports: PortStat[];
  timeline: TimelinePoint[];
}

export interface ThreatEvidence {
  packet_rate: number;
  byte_rate: number;
  packet_count: number;
  byte_count: number;
  flow_duration: number;
  inter_arrival_time: number;
  connection_frequency: number;
  entropy: number;
}

export interface Threat {
  id: string;
  timestamp: string;
  source_ip: string;
  destination_ip: string;
  source_port: number;
  destination_port: number;
  protocol: string;
  threat_type: string;
  severity: SeverityLevel;
  confidence: number;
  status: string;
  state: SecurityState;
  mitre_technique: string;
  evidence: ThreatEvidence;
  explanation: string;
}

export interface ForecastFutureState {
  step: string;
  horizon_step: number;
  expected_time: string;
  state: SecurityState;
  attack_stage: string;
  stage_code: string;
  probability: number;
  confidence: number;
  risk_level: SeverityLevel;
  mitre_technique: string;
  key_evidence: string[];
}

export interface ProbabilityCurvePoint {
  step: string;
  horizon: number;
  probability: number;
  confidence_lower: number;
  confidence_upper: number;
}

export interface FeatureAttribution {
  feature: string;
  impact: number;
  description: string;
}

export interface WhatHappensNext {
  headline: string;
  current_state: SecurityState;
  predicted_next_state: SecurityState;
  next_stage: string;
  next_mitre_technique: string;
  next_probability: number;
  next_confidence: number;
  rationale: string;
}

export interface ForecastResponse {
  timestamp: string;
  model_architecture: string;
  current_state: SecurityState;
  current_probabilities: Record<SecurityState, number>;
  predicted_next_state: SecurityState;
  confidence: number;
  risk_level: SeverityLevel;
  forecast_horizon_steps: number;
  what_happens_next: WhatHappensNext;
  future_states: ForecastFutureState[];
  probability_curve: ProbabilityCurvePoint[];
  latent_state_dimension: number;
  attributions: FeatureAttribution[];
}

export interface SimulationStep {
  step_index: number;
  step_label: string;
  timestamp: string;
  flow_id: string;
  src_ip: string;
  dst_ip: string;
  protocol: string;
  ground_truth_state: SecurityState;
  severity: SeverityLevel;
  packet_rate: number;
  byte_rate: number;
  inferred_current_state: SecurityState;
  inferred_next_state: SecurityState;
  prediction_confidence: number;
  current_probabilities: Record<SecurityState, number>;
  is_threat: boolean;
}

export interface SimulationScenario {
  id: string;
  name: string;
  description: string;
  progression: SecurityState[];
  mitre_targets: string[];
}

export interface SimulationRunResult {
  scenario: string;
  total_steps: number;
  steps: SimulationStep[];
  summary: {
    initial_state: SecurityState;
    final_state: SecurityState;
    escalation_detected_at_step: number | null;
  };
}

export interface MitreItem {
  tactic: string;
  technique_id: string;
  technique_name: string;
  description: string;
  observable: string;
  risk: SeverityLevel;
  stage: string;
  typical_state: SecurityState;
  current_status: string;
  predicted_probability: number;
  evidence_count: number;
}

export interface MitreResponse {
  framework: string;
  tactics_count: number;
  techniques_count: number;
  matrix: MitreItem[];
}

export interface Alert {
  id: string;
  timestamp: string;
  title: string;
  threat_type: string;
  severity: SeverityLevel;
  probability: number;
  confidence: number;
  source_ip: string;
  destination_ip: string;
  current_state: SecurityState;
  predicted_next_state: SecurityState;
  status: AlertStatus;
  reviewed: boolean;
  mitre_id: string;
}

export interface ModelInfo {
  model_name: string;
  model_type: string;
  version: string;
  parameters: number;
  input_features: number;
  sequence_length: number;
  hidden_dimension: number;
  dropout: number;
  heads: {
    head_a: string;
    head_b: string;
  };
  training_dataset: string;
  split: string;
  evaluation_metrics: {
    current_state_accuracy: number;
    next_state_accuracy: number;
    test_loss: number;
    precision: number;
    recall: number;
    f1_score: number;
    auc_roc: number;
  };
  feature_list: string[];
  state_ladder: string[];
}

export interface ExplainabilityFeature {
  feature: string;
  importance: number;
  direction: 'Positive' | 'Negative';
  description: string;
}

export interface ModelExplainResponse {
  method: string;
  global_importance: ExplainabilityFeature[];
  example_rationale: string;
}

export interface ServiceStatus {
  name: string;
  status: 'online' | 'degraded' | 'offline' | 'ready';
  latency_ms: number;
  version: string;
  last_heartbeat: string;
}

export interface SystemStatusResponse {
  services: ServiceStatus[];
  system_metrics: {
    cpu_usage_pct: number;
    memory_usage_pct: number;
    uptime_seconds: number;
    total_inferred_sequences: number;
    active_connections: number;
  };
}
