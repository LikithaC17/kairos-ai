"""
Integration / smoke tests for the enhanced Prediction Engine.

Tests verify:
  1. Output schema contains all required fields
  2. Attack stage names are valid
  3. Multi-step forecast() works correctly
  4. Threat score is in [0, 100] and distinct from model confidence
  5. Evidence list is populated from behavioural features
  6. Prints a sample prediction output for the final report
"""

import json
import sys
import os
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from prediction import PredictionEngine, WorldModelOutput
from prediction.schemas import CurrentObservation, ModelPredictions, ATTACK_STAGES

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_wmo(state: str, features: dict = None, next_state: str = None,
              probs: dict = None) -> WorldModelOutput:
    if probs is None:
        probs = {s: 0.9 if s == state else 0.033
                 for s in ["NORMAL", "ELEVATED", "SUSPICIOUS", "ATTACK"]}
    if features is None:
        features = {}
    if next_state is None:
        next_state = state
    return WorldModelOutput(
        timestamp="2026-10-04T09:15:00Z",
        current_observation=CurrentObservation(state=state, features=features),
        model_predictions=ModelPredictions(
            current_state_prob=probs,
            predicted_next_state=next_state,
            prediction_confidence=0.85
        )
    )

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

ALL_VALID_STAGES = set(ATTACK_STAGES)

class TestOutputSchema(unittest.TestCase):

    def _get_decision(self, state="NORMAL", features=None):
        engine = PredictionEngine()
        return engine.process(_make_wmo(state, features))

    def test_required_fields_present(self):
        d = self._get_decision("ELEVATED")
        required = [
            "timestamp", "current_stage", "predicted_stage",
            "threat_score", "confidence", "prediction_confidence",
            "evidence", "current_state", "predicted_next_state",
            "risk_level", "threat_type", "forecast"
        ]
        d_dict = d.to_dict()
        for field in required:
            self.assertIn(field, d_dict, f"Missing required field: {field}")

    def test_current_stage_valid(self):
        for state in ["NORMAL", "ELEVATED", "SUSPICIOUS", "ATTACK"]:
            d = self._get_decision(state)
            self.assertIn(d.current_stage, ALL_VALID_STAGES,
                          f"current_stage '{d.current_stage}' is not a valid stage")

    def test_predicted_stage_valid(self):
        d = self._get_decision("ELEVATED")
        self.assertIn(d.predicted_stage, ALL_VALID_STAGES,
                      f"predicted_stage '{d.predicted_stage}' is not a valid stage")

    def test_threat_score_range(self):
        for state in ["NORMAL", "ELEVATED", "SUSPICIOUS", "ATTACK"]:
            d = self._get_decision(state)
            self.assertGreaterEqual(d.threat_score, 0)
            self.assertLessEqual(d.threat_score, 100)

    def test_threat_score_not_probability(self):
        """threat_score is 0-100 integer; model confidence stays in [0,1]."""
        d = self._get_decision("ATTACK")
        self.assertIsInstance(d.threat_score, int)
        self.assertGreater(d.threat_score, 1)  # definitely not a 0-1 float
        self.assertLessEqual(d.confidence, 1.0)
        self.assertLessEqual(d.prediction_confidence, 1.0)

    def test_evidence_populated_from_features(self):
        features = {
            "packet_rate": 2500.0,
            "byte_rate": 1_200_000.0,
            "connection_frequency": 120.0,
            "syn_count": 700,
            "failed_conn_ratio": 0.75,
            "byte_asymmetry": 0.9,
            "port_entropy": 4.2,
        }
        d = self._get_decision("ATTACK", features)
        self.assertGreater(len(d.evidence), 0,
                           "Evidence should be non-empty for high-activity features")

    def test_no_evidence_without_features(self):
        d = self._get_decision("SUSPICIOUS", features={})
        self.assertEqual(d.evidence, [],
                         "Evidence should be empty when no features provided")


class TestMultiStepForecast(unittest.TestCase):

    def test_forecast_returns_k_steps(self):
        engine = PredictionEngine()
        wmo = _make_wmo("ELEVATED")
        steps = engine.forecast(wmo, k_steps=5)
        self.assertEqual(len(steps), 5)

    def test_forecast_step_keys(self):
        engine = PredictionEngine()
        steps = engine.forecast(_make_wmo("NORMAL"), k_steps=3)
        for step in steps:
            for key in ["step", "state", "stage", "threat_score", "risk_level", "confidence"]:
                self.assertIn(key, step, f"Missing key '{key}' in forecast step")

    def test_forecast_stage_valid(self):
        engine = PredictionEngine()
        steps = engine.forecast(_make_wmo("NORMAL"), k_steps=4)
        for step in steps:
            self.assertIn(step["stage"], ALL_VALID_STAGES,
                          f"forecast stage '{step['stage']}' is not valid")

    def test_forecast_confidence_decays(self):
        engine = PredictionEngine()
        steps = engine.forecast(_make_wmo("ELEVATED"), k_steps=3)
        confidences = [s["confidence"] for s in steps]
        self.assertTrue(confidences[0] >= confidences[-1],
                        "Confidence should not increase over forecast horizon")

    def test_forecast_threat_score_escalates(self):
        engine = PredictionEngine()
        steps = engine.forecast(_make_wmo("NORMAL"), k_steps=3)
        scores = [s["threat_score"] for s in steps]
        self.assertTrue(scores[0] <= scores[-1],
                        "Threat score should not decrease over forecast horizon")


class TestSampleOutput(unittest.TestCase):
    """Prints a live sample output — useful for the final report."""

    def test_print_sample_output(self):
        engine = PredictionEngine()

        # Simulate an escalating multi-stage session
        for state in ["NORMAL", "ELEVATED", "SUSPICIOUS"]:
            engine.process(_make_wmo(state))

        wmo = _make_wmo(
            state="ATTACK",
            features={
                "packet_rate": 3000.0,
                "byte_rate": 1_500_000.0,
                "connection_frequency": 200.0,
                "syn_count": 900,
                "failed_conn_ratio": 0.82,
                "byte_asymmetry": 0.93,
                "port_entropy": 4.7,
                "dst_ip_diversity": 80,
            },
            next_state="ATTACK",
            probs={"NORMAL": 0.01, "ELEVATED": 0.02,
                   "SUSPICIOUS": 0.12, "ATTACK": 0.85}
        )

        decision = engine.process(wmo)
        forecast = engine.forecast(wmo, k_steps=3)

        output = decision.to_dict()
        output["forecast"] = forecast

        print("\n" + "=" * 60)
        print("SAMPLE PREDICTION ENGINE OUTPUT")
        print("=" * 60)
        print(json.dumps(output, indent=2))
        print("=" * 60)

        # Assert final state is sane
        self.assertEqual(decision.current_state, "ATTACK")
        self.assertGreater(decision.threat_score, 60)
        self.assertGreater(len(decision.evidence), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
