"""NetForecast AI — Time-Series Transformer Forecaster (planned).

Status
------
This module is listed in the repository structure (README §23) as a planned
alternative temporal architecture to the primary GRU model in lstm.py.

The Transformer implementation is scoped for a future development sprint.
The primary temporal world model (NetworkStateGRU) is fully implemented
in lstm.py and is the recommended inference path for the prediction engine.

Planned architecture
--------------------
* Multi-head self-attention over the temporal sequence (T time steps)
* Positional encoding for ordered sequence awareness
* Feed-forward sublayers with residual connections and layer normalisation
* Dual classification heads (current state + next-state prediction)
  — identical output schema to NetworkStateGRU in lstm.py

Inference contract (when implemented)
--------------------------------------
Input  : numpy array shape (T, F)  where F=7 feature columns
Output : {
    "current_state"         : str,
    "current_probabilities" : dict[str, float],
    "predicted_next_state"  : str,
    "prediction_confidence" : float,
}

Note
----
The output schema is intentionally identical to the GRU model so the
prediction engine can swap architectures by changing only the loader call.
"""

# Implementation placeholder — to be completed in a subsequent sprint.
# See lstm.py for the fully operational GRU-based world model.

raise NotImplementedError(
    "TransformerForecaster is not yet implemented. "
    "Use models.temporal.lstm.NetworkStateGRU (via models.temporal.inference) instead."
)
