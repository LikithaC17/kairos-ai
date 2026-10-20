"""NetForecast AI — Temporal World Model package.

Public API
----------
WorldModel          : the PyTorch GRU module (dual-head classifier)
load_world_model    : convenience loader (model + scaler) from checkpoint dir
predict             : run inference on a single temporal sequence

Example
-------
>>> from models.temporal import load_world_model, predict
>>> model, scaler = load_world_model("checkpoints")
>>> result = predict(model, scaler, sequence)   # sequence shape: (T, 7)
>>> print(result["current_state"], result["predicted_next_state"])
"""

from models.temporal.lstm import NetworkStateGRU as WorldModel
from models.temporal.inference import load_world_model, predict

__all__ = ["WorldModel", "load_world_model", "predict"]
