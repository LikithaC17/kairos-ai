"""
End-to-End Pipeline Integration & Validation Tests for NetForecast AI.

Validates the complete AI World Model pipeline:
Traffic / Simulation -> Dataset -> Preprocessing -> Feature Engineering ->
Temporal Sequences -> AI World Model (GRU) -> Current State Prediction ->
Next State Forecast -> Threat Scoring -> Evidence -> FastAPI -> Dashboard Contract.

Covers:
- Test 1: NORMAL traffic state
- Test 2: ELEVATED traffic state
- Test 3: SUSPICIOUS traffic state
- Test 4: ATTACK traffic state
- Test 5: RECOVERY transition from attack back to baseline
- Test 6: Measured real latency (inference_latency_ms and pipeline_latency_ms)
- Test 7: Honest failure reporting (MODEL_UNAVAILABLE / INFERENCE_ERROR, no fake 0.85 fallbacks)
- Test 8: Full API suite (/health, /api/predict/current, /api/simulate, /api/traffic/analyze)
"""

import sys
import unittest
import numpy as np
import pandas as pd
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api.app import app, generate_flows_for_scenario
from pipeline.orchestrator import EndToEndPipeline
from simulation.attack_simulator import SCENARIO_GENERATORS, add_tcp_flags


class TestEndToEndPipeline(unittest.TestCase):
    """
    Validates end-to-end pipeline execution and state progression.
    """

    @classmethod
    def setUpClass(cls):
        cls.pipeline = EndToEndPipeline()
        cls.client = TestClient(app)

    def test_state_1_normal(self):
        """Test 1 — NORMAL: Normal traffic produces NORMAL state."""
        flows = generate_flows_for_scenario("normal", rows=35, seed=42)
        df = pd.DataFrame(flows)
        result = self.pipeline.run(df, scenario_name="normal")

        decision = result.decision
        self.assertEqual(decision["current_state"], "NORMAL")
        self.assertLessEqual(decision["threat_score"], 30)
        self.assertEqual(decision["risk_level"], "LOW")
        self.assertGreater(result.inference_latency_ms, 0.0)

    def test_state_2_elevated(self):
        """Test 2 — ELEVATED: Scanning traffic produces ELEVATED state."""
        flows = generate_flows_for_scenario("scanning", rows=35, seed=42)
        df = pd.DataFrame(flows)
        result = self.pipeline.run(df, scenario_name="scanning")

        decision = result.decision
        self.assertEqual(decision["current_state"], "ELEVATED")
        self.assertIn(decision["current_stage"], ["Reconnaissance", "Scanning"])
        self.assertGreaterEqual(decision["threat_score"], 20)

    def test_state_3_suspicious(self):
        """Test 3 — SUSPICIOUS: Beaconing traffic produces SUSPICIOUS state."""
        flows = generate_flows_for_scenario("beaconing", rows=35, seed=42)
        df = pd.DataFrame(flows)
        result = self.pipeline.run(df, scenario_name="beaconing")

        decision = result.decision
        self.assertEqual(decision["current_state"], "SUSPICIOUS")
        self.assertIn(decision["current_stage"], ["Initial Access", "Command and Control"])

    def test_state_4_attack(self):
        """Test 4 — ATTACK: Strong attack traffic (DDoS / SYN flood) produces ATTACK state."""
        flows = generate_flows_for_scenario("ddos", rows=35, seed=42)
        df = pd.DataFrame(flows)
        result = self.pipeline.run(df, scenario_name="ddos")

        decision = result.decision
        self.assertEqual(decision["current_state"], "ATTACK")
        self.assertGreaterEqual(decision["threat_score"], 60)
        self.assertIn(decision["risk_level"], ["HIGH", "CRITICAL"])
        self.assertGreater(len(result.alerts), 0)

    def test_state_5_recovery_transition(self):
        """Test 5 — RECOVERY: Gradual transition from attack down to normal."""
        pipe = EndToEndPipeline()
        rng = np.random.default_rng(42)

        # Step A: Attack traffic
        attack_flows = generate_flows_for_scenario("ddos", rows=35, seed=42)
        res_attack = pipe.run(pd.DataFrame(attack_flows), scenario_name="ddos")
        self.assertEqual(res_attack.decision["current_state"], "ATTACK")

        # Step B: Normal traffic immediately following attack triggers recovery
        normal_flows = generate_flows_for_scenario("normal", rows=35, seed=99)
        res_rec = pipe.run(pd.DataFrame(normal_flows), scenario_name="normal")

        # The state transitions down to NORMAL and stage acknowledges recovery from ATTACK
        self.assertEqual(res_rec.decision["current_state"], "NORMAL")
        self.assertEqual(res_rec.decision["current_stage"], "Recovery")
        self.assertLess(res_rec.decision["threat_score"], res_attack.decision["threat_score"])

    def test_measured_latency_not_hardcoded(self):
        """Test 6: Verifies real measured latency instead of hard-coded values."""
        flows = generate_flows_for_scenario("normal", rows=25, seed=7)
        res = self.pipeline.run(pd.DataFrame(flows), scenario_name="bench")

        self.assertIsInstance(res.inference_latency_ms, float)
        self.assertGreater(res.inference_latency_ms, 0.0)
        self.assertIsInstance(res.pipeline_latency_ms, float)
        self.assertGreater(res.pipeline_latency_ms, res.inference_latency_ms)

    def test_model_unavailable_honest_reporting(self):
        """Test 7: Proves system does not disguise missing model with fake probabilities."""
        pipe_broken = EndToEndPipeline(checkpoint_dir="/non_existent_checkpoint_path_123")
        pipe_broken.world_model = None
        pipe_broken.scaler = None

        flows = generate_flows_for_scenario("normal", rows=25, seed=7)
        res = pipe_broken.run(pd.DataFrame(flows), scenario_name="test_broken")

        decision = res.decision
        self.assertEqual(decision["current_state"], "MODEL_UNAVAILABLE")
        self.assertEqual(decision["threat_type"], "AI World Model Unavailable")
        self.assertIn("FAIL", res.pipeline_status["AI World Model"])

    def test_api_health_endpoint(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["isBackendConnected"])
        self.assertTrue(data["modelLoaded"])
        self.assertGreaterEqual(data["inferenceLatencyMs"], 0.0)

    def test_api_predict_current_endpoint(self):
        res = self.client.get("/api/predict/current")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn(data["current_state"], ["NORMAL", "ELEVATED", "SUSPICIOUS", "ATTACK"])
        self.assertIn("alerts", data)
        self.assertIn("timeline", data)
        self.assertIn("network_graph", data)
        self.assertIn("mitre_mapping", data)
        self.assertIn("inferenceLatencyMs", data)

    def test_api_simulate_endpoint(self):
        for scenario in ["normal", "scanning", "ddos", "recovery"]:
            payload = {"scenario": scenario, "rows": 30}
            res = self.client.post("/api/simulate", json=payload)
            self.assertEqual(res.status_code, 200, f"Simulate failed for {scenario}")
            data = res.json()
            self.assertIn("current_state", data)
            self.assertIn("threat_score", data)
            self.assertIn("inferenceLatencyMs", data)

    def test_api_traffic_analyze_endpoint(self):
        flows = generate_flows_for_scenario("normal", rows=20, seed=88)
        payload = {"source": "live_stream_sensor", "flows": flows}
        res = self.client.post("/api/traffic/analyze", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["current_state"], "NORMAL")
        self.assertGreater(data["pipelineLatencyMs"], 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
