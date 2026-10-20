"""
Master End-to-End Pipeline Orchestrator for NetForecast AI.

Connects every module from Traffic Input to Security Dashboard:
1. TRAFFIC INGESTION (CSV, NetFlow, or Simulation)
2. PREPROCESSING & CLEANING (Vikas)
3. TEMPORAL WINDOWING (Vikas)
4. FEATURE STATE & NETWORK GRAPH (Nagarjuna)
5. AI WORLD MODEL INFERENCE (Likitha)
6. K-STEP LOOKAHEAD FORECASTING (Likitha / Prediction Engine)
7. RISK & ATTACK STAGE PREDICTION (Prediction Engine)
8. MITRE ATT&CK MAPPING (Nagarjuna)
9. EXPLAINABLE AI (XAI) (Nagarjuna)
10. ALERT GENERATION (Nagarjuna)
11. SOC DASHBOARD & API EXPORT (Siddarth / Nagarjuna)
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

# Add repo root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from explainability.shap_analysis import ExplainabilityEngine, FeatureExplanation
from graph.network_graph import NetworkGraphBuilder, FlowGraphSnapshot
from mitre.attack_mapping import MitreAttackMapping, map_to_mitre
from models.temporal.inference import load_world_model, predict as run_world_model_inference
from prediction.alert_engine import AlertEngine, SecurityAlert
from prediction.prediction_engine import PredictionEngine
from prediction.schemas import CurrentObservation, ModelPredictions, SecurityDecision, WorldModelOutput
from preprocessing.clean import clean_traffic_data
from preprocessing.feature_extraction import CORE_WORLD_MODEL_FEATURES, extract_cyber_features
from preprocessing.windowing import create_sliding_windows


@dataclass
class PipelineRunResult:
    """Consolidated output of the full end-to-end network attack forecasting pipeline."""
    timestamp: str
    decision: Dict[str, Any]
    alerts: List[Dict[str, Any]]
    timeline: List[Dict[str, Any]]
    network_graph: Dict[str, Any]
    mitre_mapping: Dict[str, Any]
    explainability: Dict[str, Any]
    forecast_steps: List[Dict[str, Any]]
    pipeline_status: Dict[str, str]
    inference_latency_ms: float = 0.0
    pipeline_latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "decision": self.decision,
            "alerts": self.alerts,
            "timeline": self.timeline,
            "network_graph": self.network_graph,
            "mitre_mapping": self.mitre_mapping,
            "explainability": self.explainability,
            "forecast_steps": self.forecast_steps,
            "pipeline_status": self.pipeline_status,
            "inference_latency_ms": self.inference_latency_ms,
            "pipeline_latency_ms": self.pipeline_latency_ms,
        }


class EndToEndPipeline:
    """
    Unified end-to-end execution pipeline connecting all system modules.
    """

    def __init__(
        self,
        checkpoint_dir: Optional[Union[str, Path]] = None,
        sequence_length: int = 20,
        forecast_horizon: int = 3,
    ):
        self.sequence_length = sequence_length
        self.forecast_horizon = forecast_horizon
        self.checkpoint_dir = Path(checkpoint_dir or (PROJECT_ROOT / "checkpoints"))

        # Initialize engines
        self.prediction_engine = PredictionEngine()
        self.graph_builder = NetworkGraphBuilder(directed=True)
        self.xai_engine = ExplainabilityEngine()
        self.alert_engine = AlertEngine(alert_threshold=35)

        # Load trained world model and scaler
        self.world_model = None
        self.scaler = None
        self._load_model()

    def _load_model(self):
        try:
            self.world_model, self.scaler = load_world_model(self.checkpoint_dir)
        except Exception as e:
            # Model will be loaded when available
            self.world_model, self.scaler = None, None

    def run(
        self,
        traffic_data: Union[pd.DataFrame, str, Path],
        scenario_name: str = "live",
    ) -> PipelineRunResult:
        """
        Executes the complete pipeline on raw or simulated network traffic flows.
        """
        status: Dict[str, str] = {}
        t_pipeline_start = time.perf_counter()
        iso_now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Step 1: Ingestion
        try:
            if isinstance(traffic_data, (str, Path)):
                df_raw = pd.read_csv(traffic_data)
            elif isinstance(traffic_data, pd.DataFrame):
                df_raw = traffic_data.copy()
            else:
                raise TypeError(f"Unsupported traffic input type: {type(traffic_data)}")
            status["Traffic ingestion"] = "PASS"
        except Exception as e:
            status["Traffic ingestion"] = f"FAIL ({e})"
            raise

        # Step 2: Preprocessing & Cleaning
        try:
            cleaned_df = clean_traffic_data(df_raw, sort_chronological=True)
            status["Preprocessing & Cleaning"] = "PASS"
        except Exception as e:
            status["Preprocessing & Cleaning"] = f"FAIL ({e})"
            cleaned_df = df_raw

        # Step 3: Feature Engineering
        try:
            featured_df = extract_cyber_features(cleaned_df, include_core_only=False)
            status["Feature Engineering"] = "PASS"
        except Exception as e:
            status["Feature Engineering"] = f"FAIL ({e})"
            featured_df = cleaned_df

        # Step 4: Network Graph Construction
        try:
            graph_snapshot = self.graph_builder.extract_snapshot(cleaned_df)
            status["Network Graph Generation"] = "PASS"
        except Exception as e:
            status["Network Graph Generation"] = f"FAIL ({e})"
            graph_snapshot = self.graph_builder.extract_snapshot([])

        # Step 5: Temporal Windowing
        try:
            # Extract core 7 features for the GRU model
            core_cols = [c for c in CORE_WORLD_MODEL_FEATURES if c in featured_df.columns]
            if len(core_cols) < 7:
                # If some columns missing, fill with defaults
                for col in CORE_WORLD_MODEL_FEATURES:
                    if col not in featured_df.columns:
                        featured_df[col] = 0.0

            raw_core_matrix = featured_df[CORE_WORLD_MODEL_FEATURES].values.astype(np.float64)

            # Ensure we have at least sequence_length rows
            if len(raw_core_matrix) < self.sequence_length:
                # Pad earlier timesteps with first row
                padding = np.repeat(raw_core_matrix[:1], self.sequence_length - len(raw_core_matrix), axis=0)
                seq_matrix = np.vstack([padding, raw_core_matrix])
            else:
                seq_matrix = raw_core_matrix[-self.sequence_length:]

            status["Temporal Windowing"] = "PASS"
        except Exception as e:
            status["Temporal Windowing"] = f"FAIL ({e})"
            seq_matrix = np.zeros((self.sequence_length, 7), dtype=np.float64)

        # Step 6: World Model Inference (Real AI Pipeline)
        t_infer_start = time.perf_counter()
        infer_latency_ms = 0.0
        try:
            if self.world_model is None or self.scaler is None:
                self._load_model()

            if self.world_model is not None and self.scaler is not None:
                inf_result = run_world_model_inference(self.world_model, self.scaler, seq_matrix)
                infer_latency_ms = round((time.perf_counter() - t_infer_start) * 1000, 2)
                current_state = inf_result["current_state"]
                current_probs = inf_result["current_probabilities"]
                pred_next_state = inf_result["predicted_next_state"]
                pred_conf = inf_result["prediction_confidence"]
                status["AI World Model"] = "PASS"
            else:
                infer_latency_ms = 0.0
                current_state = "MODEL_UNAVAILABLE"
                current_probs = {"NORMAL": 0.0, "ELEVATED": 0.0, "SUSPICIOUS": 0.0, "ATTACK": 0.0}
                pred_next_state = "MODEL_UNAVAILABLE"
                pred_conf = 0.0
                status["AI World Model"] = "FAIL (Model checkpoint unavailable)"
        except Exception as e:
            infer_latency_ms = round((time.perf_counter() - t_infer_start) * 1000, 2)
            status["AI World Model"] = f"FAIL ({e})"
            current_state = "INFERENCE_ERROR"
            current_probs = {"NORMAL": 0.0, "ELEVATED": 0.0, "SUSPICIOUS": 0.0, "ATTACK": 0.0}
            pred_next_state = "INFERENCE_ERROR"
            pred_conf = 0.0

        # Step 7: Construct WorldModelOutput
        latest_features = {}
        for c in featured_df.columns:
            if pd.api.types.is_numeric_dtype(featured_df[c]):
                latest_features[c] = float(featured_df[c].iloc[-1])

        wmo = WorldModelOutput(
            timestamp=iso_now,
            current_observation=CurrentObservation(
                state=current_state,
                scenario=scenario_name,
                features=latest_features,
            ),
            model_predictions=ModelPredictions(
                current_state_prob=current_probs,
                predicted_next_state=pred_next_state,
                prediction_confidence=pred_conf,
            ),
        )

        # Step 8: Risk Scoring, Attack Stage & Multi-step Forecasting
        if current_state in ("MODEL_UNAVAILABLE", "INFERENCE_ERROR"):
            status["Risk & Stage Forecasting"] = f"FAIL ({current_state})"
            decision = SecurityDecision(
                timestamp=iso_now,
                current_state=current_state,
                current_stage="Unavailable",
                predicted_next_state=current_state,
                predicted_stage="Unavailable",
                threat_score=0,
                risk_level="UNKNOWN",
                confidence=0.0,
                prediction_confidence=0.0,
                threat_type="AI World Model Unavailable",
                evidence=[f"AI World Model error: {status.get('AI World Model', 'Model unavailable')}"],
            )
            forecast_steps = []
        else:
            try:
                decision = self.prediction_engine.process(wmo)
                forecast_steps = self.prediction_engine.forecast(wmo, k_steps=self.forecast_horizon)
                status["Risk & Stage Forecasting"] = "PASS"
            except Exception as e:
                status["Risk & Stage Forecasting"] = f"FAIL ({e})"
                decision = SecurityDecision(
                    timestamp=iso_now,
                    current_state=current_state,
                    current_stage="Baseline",
                    predicted_next_state=pred_next_state,
                    predicted_stage="Baseline",
                    threat_score=10,
                    risk_level="LOW",
                    confidence=pred_conf,
                    prediction_confidence=pred_conf,
                    threat_type="Normal Operations",
                    evidence=[f"Scoring fallback error: {str(e)}"],
                )
                forecast_steps = []

        # Step 9: MITRE ATT&CK Mapping
        try:
            mitre_map = map_to_mitre(
                attack_stage=decision.predicted_stage,
                evidence=decision.evidence,
                threat_type=decision.threat_type,
                confidence=decision.prediction_confidence,
            )
            status["MITRE ATT&CK Mapping"] = "PASS"
        except Exception as e:
            status["MITRE ATT&CK Mapping"] = f"FAIL ({e})"
            mitre_map = None

        # Step 10: Explainable AI (XAI)
        try:
            xai_result = self.xai_engine.explain_features(
                features=latest_features,
                predicted_state=decision.predicted_next_state,
                threat_score=decision.threat_score,
            )
            status["Explainable AI (XAI)"] = "PASS"
        except Exception as e:
            status["Explainable AI (XAI)"] = f"FAIL ({e})"
            xai_result = FeatureExplanation(important_features=[], feature_contributions={}, explanation="")

        # Step 11: Alert Generation
        try:
            alert = self.alert_engine.evaluate_decision(
                timestamp=iso_now,
                risk_score=decision.threat_score,
                confidence=decision.prediction_confidence,
                attack_stage=decision.current_stage,
                predicted_stage=decision.predicted_stage,
                threat_type=decision.threat_type,
                evidence=decision.evidence,
                mitre_mapping=mitre_map,
            )
            alerts_list = [alert.to_dict()] if alert else []
            status["Alert Engine"] = "PASS"
        except Exception as e:
            status["Alert Engine"] = f"FAIL ({e})"
            alerts_list = []

        # Step 12: Prepare Timeline Observation
        timeline = [{
            "time": time.strftime("%H:%M:%S", time.gmtime()),
            "timestamp": iso_now,
            "packetRate": latest_features.get("packet_rate", 0.0),
            "threatScore": decision.threat_score,
            "state": decision.current_state,
            "isForecast": False,
        }]

        # Add forecast timeline points
        for step in forecast_steps:
            timeline.append({
                "time": f"+{step['step']*5}s",
                "timestamp": iso_now,
                "packetRate": latest_features.get("packet_rate", 0.0),
                "threatScore": step["threat_score"],
                "state": step["state"],
                "isForecast": True,
            })

        pipeline_latency_ms = round((time.perf_counter() - t_pipeline_start) * 1000, 2)
        status["Security Dashboard & API Integration"] = "PASS"

        decision_dict = decision.to_dict()
        decision_dict["forecast"] = forecast_steps
        decision_dict["inference_latency_ms"] = infer_latency_ms
        decision_dict["pipeline_latency_ms"] = pipeline_latency_ms
        decision_dict["forecast_method"] = "Controlled Horizon Projection (GRU Dual-Head + State Dynamics)"

        return PipelineRunResult(
            timestamp=iso_now,
            decision=decision_dict,
            alerts=alerts_list,
            timeline=timeline,
            network_graph=graph_snapshot.to_dict(),
            mitre_mapping=mitre_map.to_dict() if mitre_map else {},
            explainability=xai_result.to_dict(),
            forecast_steps=forecast_steps,
            pipeline_status=status,
            inference_latency_ms=infer_latency_ms,
            pipeline_latency_ms=pipeline_latency_ms,
        )
