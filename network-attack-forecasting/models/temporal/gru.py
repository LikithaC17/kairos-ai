"""Threatora AI / Threatora AI — Dual-Head GRU World Model.

Architecture:
- Input: (batch, T=20, F=7)
- 2-layer GRU (hidden=128, dropout=0.3)
- Final step hidden state (batch, 128)
- Head A: Current State Classifier (Linear 128->64 -> ReLU -> Dropout -> Linear 64->4 -> log_softmax)
- Head B: Next State Forecaster (Linear 128->64 -> ReLU -> Dropout -> Linear 64->4 -> log_softmax)

States:
- 0: NORMAL | 1: ELEVATED | 2: SUSPICIOUS | 3: ATTACK
"""

from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn

STATE_LABELS = ["NORMAL", "ELEVATED", "SUSPICIOUS", "ATTACK"]
NUM_STATES = len(STATE_LABELS)

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
        self.model_type = "GRU"

        # Recurrent backbone
        self.gru = nn.GRU(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )

        self.dropout = nn.Dropout(p=dropout)

        # Head A: classify current state
        self.head_current = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Dropout(p=dropout * 0.5),
            nn.Linear(64, num_classes),
        )

        # Head B: predict next state
        self.head_next = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Dropout(p=dropout * 0.5),
            nn.Linear(64, num_classes),
        )

        self._init_weights()

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

    def forward(
        self,
        x: torch.Tensor,
        h0: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Forward pass.

        Parameters
        ----------
        x  : input tensor of shape (batch, T, input_size)
        h0 : optional initial hidden state (num_layers, batch, hidden_size)

        Returns
        -------
        log_probs_current : (batch, num_classes)
        log_probs_next    : (batch, num_classes)
        """
        out, _ = self.gru(x, h0)
        last = out[:, -1, :]
        last = self.dropout(last)

        log_probs_current = nn.functional.log_softmax(self.head_current(last), dim=-1)
        log_probs_next = nn.functional.log_softmax(self.head_next(last), dim=-1)

        return log_probs_current, log_probs_next

    def predict_dict(self, x: torch.Tensor) -> dict:
        """Run forward pass and return structured inference output dict."""
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


class Log1pStandardScaler:
    """Feature-wise log1p transform followed by zero-mean unit-variance scaling."""

    def __init__(self) -> None:
        self.mean_: np.ndarray | None = None
        self.std_: np.ndarray | None = None

    def fit(self, X: np.ndarray) -> Log1pStandardScaler:
        """X shape: (N, T, F) — fit on training data only."""
        log_X = np.log1p(np.abs(X))
        flat = log_X.reshape(-1, X.shape[-1])
        self.mean_ = flat.mean(axis=0)
        self.std_ = flat.std(axis=0) + 1e-8
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        log_X = np.log1p(np.abs(X))
        return (log_X - self.mean_) / self.std_

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        return self.fit(X).transform(X)
