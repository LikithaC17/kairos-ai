"""Threatora AI / Threatora AI — Dual-Head Temporal Transformer World Model.

Architecture:
- Input: (batch, T=20, F=7)
- Linear Input Projection: 7 -> d_model (64)
- Sinusoidal Positional Encoding
- 2-layer Transformer Encoder (d_model=64, nhead=4, dim_feedforward=128, dropout=0.2, batch_first=True)
- Temporal Sequence Aggregation (Last time step representation + LayerNorm)
- Head A: Current State Classifier (Linear 64->64 -> ReLU -> Dropout -> Linear 64->4 -> log_softmax)
- Head B: Next State Forecaster (Linear 64->64 -> ReLU -> Dropout -> Linear 64->4 -> log_softmax)
"""

from __future__ import annotations

import math
import numpy as np
import torch
import torch.nn as nn

from .gru import STATE_LABELS, NUM_STATES, FEATURE_COLUMNS, NUM_FEATURES


class PositionalEncoding(nn.Module):
    """Sinusoidal positional encoding for sequence position awareness."""

    def __init__(self, d_model: int, max_len: int = 500, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # (1, max_len, d_model)

        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (batch, seq_len, d_model)
        x = x + self.pe[:, : x.size(1)]
        return self.dropout(x)


class NetworkStateTransformer(nn.Module):
    """Dual-head Time-Series Transformer world model for network security state estimation.

    Parameters
    ----------
    input_size  : number of input features per time step (default 7)
    d_model     : internal transformer embedding dimension (default 64)
    nhead       : number of attention heads (default 4)
    num_layers  : stacked transformer encoder layers (default 2)
    dim_feedforward : dimension of feedforward network inside encoder (default 128)
    num_classes : number of discrete security states (default 4)
    dropout     : dropout probability (default 0.2)
    """

    def __init__(
        self,
        input_size: int = NUM_FEATURES,
        d_model: int = 64,
        nhead: int = 4,
        num_layers: int = 2,
        dim_feedforward: int = 128,
        num_classes: int = NUM_STATES,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()

        self.input_size = input_size
        self.d_model = d_model
        self.nhead = nhead
        self.num_layers = num_layers
        self.num_classes = num_classes
        self.model_type = "Transformer"

        # Feature projection to embedding dimension
        self.input_proj = nn.Linear(input_size, d_model)
        self.pos_encoder = PositionalEncoding(d_model=d_model, dropout=dropout)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            activation="relu",
            batch_first=True,
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.layer_norm = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(p=dropout)

        # Head A: classify current state
        self.head_current = nn.Sequential(
            nn.Linear(d_model, 64),
            nn.ReLU(),
            nn.Dropout(p=dropout * 0.5),
            nn.Linear(64, num_classes),
        )

        # Head B: predict next state
        self.head_next = nn.Sequential(
            nn.Linear(d_model, 64),
            nn.ReLU(),
            nn.Dropout(p=dropout * 0.5),
            nn.Linear(64, num_classes),
        )

        self._init_weights()

    def _init_weights(self) -> None:
        """Xavier-uniform init for linear projections."""
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)

    def forward(
        self,
        x: torch.Tensor,
        mask: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Forward pass.

        Parameters
        ----------
        x    : input tensor of shape (batch, T, input_size)
        mask : optional attention mask

        Returns
        -------
        log_probs_current : (batch, num_classes)
        log_probs_next    : (batch, num_classes)
        """
        # Linear projection + positional encoding
        h = self.input_proj(x)
        h = self.pos_encoder(h)

        # Transformer encoding
        out = self.transformer_encoder(h, mask=mask)  # (batch, T, d_model)

        # Temporal representation: last step
        last = out[:, -1, :]
        last = self.layer_norm(last)
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


__all__ = [
    "NetworkStateTransformer",
    "PositionalEncoding",
    "STATE_LABELS",
    "NUM_STATES",
    "FEATURE_COLUMNS",
    "NUM_FEATURES",
]
