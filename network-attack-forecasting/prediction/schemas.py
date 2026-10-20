import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

VALID_STATES = {
    "NORMAL",
    "ELEVATED",
    "SUSPICIOUS",
    "ATTACK",
    "MODEL_UNAVAILABLE",
    "MODEL_LOAD_ERROR",
    "INFERENCE_ERROR",
}
VALID_RISK_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL", "UNKNOWN"}

# The human-readable attack progression stages exposed in the output.
# "Baseline" represents a clean / non-threat observation window.
ATTACK_STAGES = [
    "Baseline",
    "Reconnaissance",
    "Scanning",
    "Initial Access",
    "Command and Control",
    "Lateral Movement",
    "Exfiltration",
    "Impact",
    "Recovery",
    "Unavailable",
]


@dataclass
class CurrentObservation:
    state: str
    scenario: str = "inference"
    features: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if self.state not in VALID_STATES:
            raise ValueError(f"Invalid state '{self.state}'. Must be one of {VALID_STATES}")


@dataclass
class ModelPredictions:
    current_state_prob: Dict[str, float] = field(default_factory=dict)
    predicted_next_state: str = "NORMAL"
    prediction_confidence: float = 0.0
    next_state_prob: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if self.predicted_next_state not in VALID_STATES:
            raise ValueError(f"Invalid next state '{self.predicted_next_state}'.")
        self.prediction_confidence = float(max(0.0, min(1.0, self.prediction_confidence)))


@dataclass
class WorldModelOutput:
    timestamp: str
    current_observation: CurrentObservation
    model_predictions: ModelPredictions

    @classmethod
    def from_dict(cls, data: dict) -> "WorldModelOutput":
        obs = data.get("current_observation", {})
        preds = data.get("model_predictions", {})
        return cls(
            timestamp=data.get("timestamp", ""),
            current_observation=CurrentObservation(
                state=obs.get("state", "NORMAL"),
                scenario=obs.get("scenario", "inference"),
                features=obs.get("features", {})
            ),
            model_predictions=ModelPredictions(
                current_state_prob=preds.get("current_state_prob", {}),
                predicted_next_state=preds.get("predicted_next_state", "NORMAL"),
                prediction_confidence=preds.get("prediction_confidence", 0.0),
                next_state_prob=preds.get("next_state_prob", {})
            )
        )


@dataclass
class SecurityDecision:
    """
    Standardised output contract consumed by Nagarjuna's API / dashboard.

    Fields
    ------
    timestamp            : ISO-8601 observation time
    current_state        : Internal four-state label (NORMAL/ELEVATED/SUSPICIOUS/ATTACK)
    current_stage        : Human-readable attack stage for the current window
    predicted_next_state : Internal four-state label for the predicted next window
    predicted_stage      : Human-readable predicted next attack stage
    threat_score         : Composite risk score 0-100 (NOT a raw model probability)
    risk_level           : LOW / MEDIUM / HIGH / CRITICAL
    confidence           : Model confidence in the *current* state classification [0, 1]
    prediction_confidence: Model confidence in the *predicted next* state [0, 1]
    threat_type          : Heuristic threat category (DDoS-like, Scanning-like, …)
    evidence             : List of human-readable behavioural indicators
    forecast             : Optional list of K-step future SecurityDecision dicts
    """
    timestamp: str
    current_state: str
    current_stage: str
    predicted_next_state: str
    predicted_stage: str
    threat_score: int
    risk_level: str
    confidence: float
    prediction_confidence: float
    threat_type: str
    evidence: List[str]
    forecast: List[dict] = field(default_factory=list)

    def __post_init__(self):
        self.threat_score = int(max(0, min(100, self.threat_score)))
        if self.risk_level not in VALID_RISK_LEVELS:
            raise ValueError(f"Invalid risk level '{self.risk_level}'.")

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
