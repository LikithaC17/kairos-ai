from typing import Dict, List, Tuple

# Internal four-state progression ladder
LADDER = ["NORMAL", "ELEVATED", "SUSPICIOUS", "ATTACK"]

# Maps each internal state to one or more possible human-readable attack stages.
# The stage selected depends on context / history; the *primary* stage is index 0.
_STATE_TO_STAGES: Dict[str, List[str]] = {
    "NORMAL":     ["Baseline"],
    "ELEVATED":   ["Reconnaissance", "Scanning"],
    "SUSPICIOUS": ["Initial Access", "Command and Control"],
    "ATTACK":     ["Lateral Movement", "Exfiltration", "Impact"],
    "MODEL_UNAVAILABLE": ["Unavailable"],
    "MODEL_LOAD_ERROR":  ["Unavailable"],
    "INFERENCE_ERROR":   ["Unavailable"],
}

# When estimating what comes NEXT, we escalate one rung on the ladder.
_NEXT_STATE_MAP: Dict[str, str] = {
    "NORMAL":     "ELEVATED",
    "ELEVATED":   "SUSPICIOUS",
    "SUSPICIOUS": "ATTACK",
    "ATTACK":     "ATTACK",   # already at max
    "MODEL_UNAVAILABLE": "MODEL_UNAVAILABLE",
    "MODEL_LOAD_ERROR":  "MODEL_LOAD_ERROR",
    "INFERENCE_ERROR":   "INFERENCE_ERROR",
}


def map_state_to_stage(state: str, history: List[str] = None) -> str:
    """
    Translate an internal state label to a human-readable attack stage.

    The mapping uses history to pick among multiple possible stages for the
    same internal state (e.g. a *second* ELEVATED window is more likely
    "Scanning" than initial "Reconnaissance"). Also identifies recovery
    transition when network returns from ATTACK down towards baseline.
    """
    if history and "ATTACK" in history[-3:] and state in ("SUSPICIOUS", "ELEVATED", "NORMAL"):
        return "Recovery"

    stages = _STATE_TO_STAGES.get(state, ["Unknown"])

    if len(stages) == 1 or not history:
        return stages[0]

    # Count how many consecutive times we have seen this state in history
    consecutive = 0
    for s in reversed(history):
        if s == state:
            consecutive += 1
        else:
            break

    # Pick deeper stage after repeated observations of the same internal state
    idx = min(consecutive, len(stages) - 1)
    return stages[idx]


class StateMachine:
    """
    Maintains temporal state history and provides stage mapping + K-step
    lookahead forecasting consumed by PredictionEngine.
    """

    def __init__(self, max_history: int = 30):
        self.history: List[str] = []
        self.max_history = max_history
        self.current_state = "NORMAL"

    # ------------------------------------------------------------------
    # State determination
    # ------------------------------------------------------------------

    def determine_state(self, probs: Dict[str, float]) -> Tuple[str, float]:
        """
        Determines current state from actual model probability distribution.
        Returns (best_state, best_prob). Does NOT fabricate probabilities.
        """
        if not probs:
            return "NORMAL", 1.0

        if all(p == 0.0 for p in probs.values()):
            return "MODEL_UNAVAILABLE", 0.0

        best_state = "NORMAL"
        best_prob = -1.0
        for s, p in probs.items():
            if p > best_prob:
                best_prob = p
                best_state = s

        return best_state, best_prob

    # ------------------------------------------------------------------
    # State update
    # ------------------------------------------------------------------

    def update(self, observed_state: str) -> str:
        """
        Updates the temporal state machine with the latest observed state.
        Supports escalation AND recovery transitions freely.
        """
        self.history.append(self.current_state)
        if len(self.history) > self.max_history:
            self.history.pop(0)

        if observed_state in LADDER or observed_state in ("MODEL_UNAVAILABLE", "MODEL_LOAD_ERROR", "INFERENCE_ERROR"):
            self.current_state = observed_state
        else:
            self.current_state = "UNKNOWN"

        return self.current_state

    # ------------------------------------------------------------------
    # Stage mapping helpers (used by PredictionEngine)
    # ------------------------------------------------------------------

    def current_stage(self) -> str:
        """Human-readable stage name for the current internal state."""
        return map_state_to_stage(self.current_state, self.history)

    def predicted_next_state(self, model_next: str) -> str:
        """
        Resolves the predicted next internal state.
        Prefers the World Model's prediction; falls back to ladder escalation.
        """
        if model_next in LADDER or model_next in ("MODEL_UNAVAILABLE", "MODEL_LOAD_ERROR", "INFERENCE_ERROR"):
            return model_next
        return _NEXT_STATE_MAP.get(self.current_state, "NORMAL")

    def predicted_next_stage(self, model_next: str) -> str:
        """Human-readable stage name for the predicted next state."""
        next_state = self.predicted_next_state(model_next)
        # Build a projected history with current appended to choose the right stage
        projected_history = self.history + [self.current_state]
        return map_state_to_stage(next_state, projected_history)

    # ------------------------------------------------------------------
    # Multi-step lookahead
    # ------------------------------------------------------------------

    def forecast_states(self, start_state: str, k_steps: int) -> List[str]:
        """
        Projects the progression of internal states over k_steps future
        windows by following the escalation ladder.

        This is a *deterministic* structural forecast, not a trained model
        output. It represents the worst-case trajectory for early warning.
        """
        states = []
        state = start_state
        for _ in range(k_steps):
            state = _NEXT_STATE_MAP.get(state, state)
            states.append(state)
        return states
