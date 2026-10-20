"""
Prediction Engine and Threat Scoring Module
============================================

Public API
----------
    from prediction import PredictionEngine, WorldModelOutput, SecurityDecision
    from prediction.schemas import CurrentObservation, ModelPredictions, ATTACK_STAGES

Usage
-----
    engine = PredictionEngine()
    decision = engine.process(world_model_output)
    print(decision.to_dict())
"""

from prediction.prediction_engine import PredictionEngine, predict_and_score
from prediction.threat_classifier import classify_threat
from prediction.risk_scorer import calculate_risk_score
from prediction.evidence import extract_evidence
from prediction.state_machine import StateMachine, map_state_to_stage
from prediction.schemas import (
    WorldModelOutput,
    CurrentObservation,
    ModelPredictions,
    SecurityDecision,
    ATTACK_STAGES,
    VALID_STATES,
    VALID_RISK_LEVELS,
)

__all__ = [
    "PredictionEngine",
    "predict_and_score",
    "classify_threat",
    "calculate_risk_score",
    "extract_evidence",
    "StateMachine",
    "map_state_to_stage",
    "WorldModelOutput",
    "CurrentObservation",
    "ModelPredictions",
    "SecurityDecision",
    "ATTACK_STAGES",
    "VALID_STATES",
    "VALID_RISK_LEVELS",
]
