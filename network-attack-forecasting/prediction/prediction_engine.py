from typing import Union, List

from .schemas import WorldModelOutput, SecurityDecision
from .state_machine import StateMachine
from .threat_classifier import classify_threat
from .risk_scorer import calculate_risk_score
from .evidence import extract_evidence


class PredictionEngine:
    """
    Main orchestration engine that converts World Model Output into a
    structured SecurityDecision for Nagarjuna's API / dashboard.

    Responsibilities
    ----------------
    1. Determine the current network / attack stage from model state probs.
    2. Forecast the next possible stage using the World Model's prediction.
    3. Calculate a composite threat score (0-100, distinct from model prob).
    4. Preserve model confidence separately from the threat score.
    5. Generate explainable evidence strings from behavioural features.
    6. Support K-step multi-horizon forecasting via forecast().
    """

    def __init__(self):
        self.state_machine = StateMachine()

    # ------------------------------------------------------------------
    # Single-step processing
    # ------------------------------------------------------------------

    def process(self, wmo_input: Union[dict, WorldModelOutput]) -> SecurityDecision:
        """
        Processes a single WorldModelOutput and returns a SecurityDecision.
        """
        if isinstance(wmo_input, dict):
            wmo = WorldModelOutput.from_dict(wmo_input)
        else:
            wmo = wmo_input

        obs   = wmo.current_observation
        preds = wmo.model_predictions

        # 1. State Machine: determine current state from model probs
        observed_state, current_conf = self.state_machine.determine_state(
            preds.current_state_prob
        )

        # 2. State Machine: update temporal history
        current_state = self.state_machine.update(observed_state)

        # 3. Human-readable attack stage for the current window
        current_stage = self.state_machine.current_stage()

        # 4. Predicted next state (from World Model) + human-readable stage
        predicted_next = self.state_machine.predicted_next_state(
            preds.predicted_next_state
        )
        predicted_stage = self.state_machine.predicted_next_stage(
            preds.predicted_next_state
        )
        pred_conf = preds.prediction_confidence

        # 5. Threat Classification
        threat_type = classify_threat(obs.features, current_state)

        # 6. Evidence Extraction
        evidence = extract_evidence(obs.features)

        # 7. Risk / Threat Score (NOT raw model probability)
        threat_score, risk_level = calculate_risk_score(
            preds.current_state_prob,
            obs.features,
            self.state_machine.history
        )

        return SecurityDecision(
            timestamp=wmo.timestamp,
            current_state=current_state,
            current_stage=current_stage,
            predicted_next_state=predicted_next,
            predicted_stage=predicted_stage,
            threat_score=threat_score,
            risk_level=risk_level,
            confidence=current_conf,
            prediction_confidence=pred_conf,
            threat_type=threat_type,
            evidence=evidence,
            forecast=[]
        )

    # ------------------------------------------------------------------
    # Multi-step forecasting
    # ------------------------------------------------------------------

    def forecast(
        self,
        wmo_input: Union[dict, WorldModelOutput],
        k_steps: int = 3
    ) -> List[dict]:
        """
        Produces a K-step forward structural forecast starting from the
        current World Model Output.

        Each step in the returned list corresponds to one future observation
        window and contains:
          - step          : lookahead index (1-based)
          - state         : projected internal state label
          - stage         : projected human-readable attack stage
          - threat_score  : estimated threat score for that future window
          - risk_level    : LOW / MEDIUM / HIGH / CRITICAL
          - confidence    : prediction confidence (decays with horizon)

        NOTE: This is a *structural* worst-case escalation forecast derived
        from the last known state. It is NOT a trained model's multi-step
        probability output.
        """
        if isinstance(wmo_input, dict):
            wmo = WorldModelOutput.from_dict(wmo_input)
        else:
            wmo = wmo_input

        # Take a snapshot of the engine state BEFORE processing the input
        # so that forecast is always relative to the current observation.
        baseline_decision = self.process(wmo_input)
        start_state = baseline_decision.current_state

        future_states = self.state_machine.forecast_states(start_state, k_steps)

        steps = []
        base_score = baseline_decision.threat_score
        base_conf  = baseline_decision.prediction_confidence

        for i, future_state in enumerate(future_states, start=1):
            # Threat score escalates toward 100 as we project further
            step_score = min(100, base_score + i * 8)

            if step_score <= 29:
                rl = "LOW"
            elif step_score <= 59:
                rl = "MEDIUM"
            elif step_score <= 79:
                rl = "HIGH"
            else:
                rl = "CRITICAL"

            # Confidence degrades with horizon distance
            step_conf = max(0.10, round(base_conf - i * 0.08, 2))

            projected_history = self.state_machine.history + [start_state] * i
            from .state_machine import map_state_to_stage
            stage = map_state_to_stage(future_state, projected_history)

            steps.append({
                "step": i,
                "state": future_state,
                "stage": stage,
                "threat_score": step_score,
                "risk_level": rl,
                "confidence": step_conf,
            })

        return steps


def predict_and_score(model_output: dict) -> dict:
    """
    Convenience function: accepts World Model output dict, returns the
    standardised SecurityDecision dict (single-step).
    """
    engine = PredictionEngine()
    decision = engine.process(model_output)
    return decision.to_dict()
