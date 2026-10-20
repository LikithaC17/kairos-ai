"""NetForecast AI — GRU World Model architecture.

Architecture overview
---------------------
Input : (batch, T, F)  where T = sequence length, F = 7 numerical features

    Log1p normalisation  →  handles heavy-tailed network statistics
    GRU (2-layer, hidden=128, dropout=0.3)
    Take final hidden state  →  (batch, 128)
    Dropout (0.3)
    ┌──────────────────────────────────┬──────────────────────────────────┐
    │  Head A — current state          │  Head B — next-state prediction   │
    │  Linear(128, 64) → ReLU          │  Linear(128, 64) → ReLU           │
    │  Linear(64, 4)   → log_softmax   │  Linear(64, 4)   → log_softmax    │
    └──────────────────────────────────┴──────────────────────────────────┘

States (index order matches LADDER_STATES in simulation/common.py)
    0: NORMAL | 1: ELEVATED | 2: SUSPICIOUS | 3: ATTACK

Design decisions
----------------
* GRU chosen over LSTM: sequences are 10-30 steps (short-to-medium horizon)
  where GRU achieves comparable accuracy with fewer parameters and faster
  convergence.
* Log1p normalisation is baked into the forward pass so the exported
  checkpoint is self-contained; external scaler handles per-feature
  mean/std centering after log1p.
* Dual-head: head A classifies the *current* security state from the full
  observed sequence; head B predicts the *next* state — cleanly separating
  "what is happening now" from "what may happen next".
* Outputs are log-probabilities (NLLLoss compatible); inference converts
  to probabilities via exp().
"""

from __future__ import annotations

import torch
import torch.nn as nn

# ─────────────────────────────────────────────────────────────────────────────
# State labels — must match simulation/common.py::LADDER_STATES
# ─────────────────────────────────────────────────────────────────────────────
STATE_LABELS = ["NORMAL", "ELEVATED", "SUSPICIOUS", "ATTACK"]
NUM_STATES = len(STATE_LABELS)

# Feature columns in the exact order expected by the model
# (matches simulation/common.py::FEATURE_COLUMNS)
FEATURE_COLUMNS = [
    "flow_duration",
    "packet_count",
    "byte_count",
    "packet_rate",
    "byte_rate",
    "inter_arrival_time",
    "connection_frequency",
]
NUM_FEATURES = len(FEATURE_COLUMNS)


# ─────────────────────────────────────────────────────────────────────────────
# Model
# ─────────────────────────────────────────────────────────────────────────────

class NetworkStateGRU(nn.Module):
    """Dual-head GRU world model for network security state estimation.

    Parameters
    ----------
    input_size  : number of input features per time step (default 7)
    hidden_size : GRU hidden dimension (default 128)
    num_layers  : stacked GRU layers (default 2)
    num_classes : number of discrete security states (default 4)
    dropout     : dropout probability applied between layers and before heads
    """

    def __init__(
        self,
        input_size: int = NUM_FEATURES,
        hidden_size: int = 128,
        num_layers: int = 2,
        num_classes: int = NUM_STATES,
        dropout: float = 0.3,
    ) -> None:
        super().__init__()

        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.num_classes = num_classes

        # Recurrent backbone
        self.gru = nn.GRU(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )

        self.dropout = nn.Dropout(p=dropout)

        # Head A: classify the current observed state
        self.head_current = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Dropout(p=dropout * 0.5),
            nn.Linear(64, num_classes),
        )

        # Head B: predict the next security state
        self.head_next = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Dropout(p=dropout * 0.5),
            nn.Linear(64, num_classes),
        )

        self._init_weights()

    # ------------------------------------------------------------------
    def _init_weights(self) -> None:
        """Xavier-uniform init for linear layers, orthogonal for GRU."""
        for name, param in self.gru.named_parameters():
            if "weight_ih" in name:
                nn.init.xavier_uniform_(param.data)
            elif "weight_hh" in name:
                nn.init.orthogonal_(param.data)
            elif "bias" in name:
                param.data.zero_()

        for module in [self.head_current, self.head_next]:
            for layer in module:
                if isinstance(layer, nn.Linear):
                    nn.init.xavier_uniform_(layer.weight)
                    nn.init.zeros_(layer.bias)

    # ------------------------------------------------------------------
    def forward(
        self,
        x: torch.Tensor,
        h0: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Forward pass.

        Parameters
        ----------
        x  : input tensor of shape (batch, T, input_size)
        h0 : optional initial hidden state (batch, num_layers, hidden_size)

        Returns
        -------
        log_probs_current : (batch, num_classes) — current state log-probabilities
        log_probs_next    : (batch, num_classes) — next state log-probabilities
        """
        # x: (batch, T, features)
        out, _ = self.gru(x, h0)          # out: (batch, T, hidden_size)
        last = out[:, -1, :]              # last time step: (batch, hidden_size)
        last = self.dropout(last)

        log_probs_current = nn.functional.log_softmax(self.head_current(last), dim=-1)
        log_probs_next    = nn.functional.log_softmax(self.head_next(last),    dim=-1)

        return log_probs_current, log_probs_next

    # ------------------------------------------------------------------
    def predict_dict(self, x: torch.Tensor) -> dict:
        """Run forward pass and return the structured inference output dict.

        Parameters
        ----------
        x : input tensor of shape (1, T, input_size) — single sequence

        Returns
        -------
        dict with keys:
            current_state        : str
            current_probabilities: dict[str, float]
            predicted_next_state : str
            prediction_confidence: float
        """
        self.eval()
        with torch.no_grad():
            log_curr, log_next = self.forward(x)

        prob_curr = torch.exp(log_curr)[0].cpu().tolist()
        prob_next = torch.exp(log_next)[0].cpu().tolist()

        curr_idx = int(torch.argmax(log_curr[0]).item())
        next_idx = int(torch.argmax(log_next[0]).item())

        return {
            "current_state": STATE_LABELS[curr_idx],
            "current_probabilities": {
                label: round(float(p), 4)
                for label, p in zip(STATE_LABELS, prob_curr)
            },
            "predicted_next_state": STATE_LABELS[next_idx],
            "prediction_confidence": round(float(prob_next[next_idx]), 4),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Scaler — defined here so pickle always resolves to this stable module path
# (models.temporal.world_model.Log1pStandardScaler) regardless of which
# script is __main__ at save vs. load time.
# ─────────────────────────────────────────────────────────────────────────────

import numpy as np  # noqa: E402  (placed after torch imports intentionally)


class Log1pStandardScaler:
    """Feature-wise log1p transform followed by zero-mean unit-variance scaling.

    Handles the heavy-tailed distributions typical in network statistics
    (packet_count, byte_count can span several orders of magnitude).
    Only the training partition must be used to fit mean and std.
    """

    def __init__(self) -> None:
        self.mean_: "np.ndarray | None" = None
        self.std_:  "np.ndarray | None" = None

    def fit(self, X: "np.ndarray") -> "Log1pStandardScaler":
        """X shape: (N, T, F) — fit on training data only."""
        log_X = np.log1p(np.abs(X))
        flat  = log_X.reshape(-1, X.shape[-1])
        self.mean_ = flat.mean(axis=0)
        self.std_  = flat.std(axis=0) + 1e-8
        return self

    def transform(self, X: "np.ndarray") -> "np.ndarray":
        log_X = np.log1p(np.abs(X))
        return (log_X - self.mean_) / self.std_

    def fit_transform(self, X: "np.ndarray") -> "np.ndarray":
        return self.fit(X).transform(X)

