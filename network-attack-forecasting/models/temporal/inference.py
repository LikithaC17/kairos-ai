"""Threatora AI / Threatora AI — Multi-Model Unified Inference Interface.

Exposes public functions for running inference with any supported temporal sequence model
(GRU baseline, LSTM, or Transformer):

    load_world_model(checkpoint_dir, model_type="gru")  ->  (model, scaler)
    predict(model, scaler, sequence)                    ->  inference_dict
    predict_batch(model, scaler, sequences)             ->  list[inference_dict]

Inference Output Schema
-----------------------
{
    "model_type"           : str,           # e.g. "GRU", "LSTM", "Transformer"
    "current_state"        : str,           # NORMAL / ELEVATED / SUSPICIOUS / ATTACK
    "current_probabilities": dict[str,float],
    "predicted_state"      : str,
    "predicted_next_state" : str,
    "future_states"        : list[str],
    "prediction_confidence": float          # probability of the predicted next state
}
"""

from __future__ import annotations

import pickle
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import torch
import torch.nn as nn

# ── project root on path ─────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from models.temporal.gru import NetworkStateGRU, STATE_LABELS, NUM_FEATURES, NUM_STATES, FEATURE_COLUMNS, Log1pStandardScaler
from models.temporal.lstm import NetworkStateLSTM
from models.temporal.transformer import NetworkStateTransformer

# ─────────────────────────────────────────────────────────────────────────────
# Default Checkpoint Locations
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULT_CHECKPOINT_DIR = PROJECT_ROOT / "checkpoints"
_DEFAULT_SCALER_PATH    = _DEFAULT_CHECKPOINT_DIR / "world_model_scaler.pkl"

_MODEL_FILENAMES = {
    "gru": "world_model_gru.pt",
    "lstm": "world_model_lstm.pt",
    "transformer": "world_model_transformer.pt",
    "tf": "world_model_transformer.pt",
}


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def load_world_model(
    checkpoint_dir: str | Path | None = None,
    device: str | torch.device | None = None,
    model_type: str = "gru",
) -> tuple[nn.Module, Any]:
    """Load the specified trained world model (GRU, LSTM, Transformer) and scaler from disk.

    Parameters
    ----------
    checkpoint_dir : directory containing checkpoint .pt files and world_model_scaler.pkl.
    device         : torch device string or object. Defaults to CUDA if available, else CPU.
    model_type     : "gru", "lstm", or "transformer". Default is "gru".

    Returns
    -------
    model  : nn.Module (eval mode, on requested device)
    scaler : fitted Log1pStandardScaler instance
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    elif isinstance(device, str):
        device = torch.device(device)

    ckpt_dir = Path(checkpoint_dir or _DEFAULT_CHECKPOINT_DIR)
    scaler_path = ckpt_dir / "world_model_scaler.pkl"

    norm_type = model_type.lower()
    fname = _MODEL_FILENAMES.get(norm_type, f"world_model_{norm_type}.pt")
    model_path = ckpt_dir / fname

    # Fallback for baseline GRU to world_model.pt if world_model_gru.pt is absent
    if norm_type == "gru" and not model_path.exists():
        fallback = ckpt_dir / "world_model.pt"
        if fallback.exists():
            model_path = fallback

    if not model_path.exists():
        raise FileNotFoundError(
            f"Model checkpoint for '{model_type}' not found at {model_path}. "
            f"Run 'python models/temporal/train.py --model {norm_type}' to train the model first."
        )
    if not scaler_path.exists():
        raise FileNotFoundError(
            f"Scaler not found at {scaler_path}. "
            "Run 'python models/temporal/train.py' to train the models and generate scaler first."
        )

    # Load and reconstruct model
    ckpt = torch.load(model_path, map_location=device)
    cfg = ckpt.get("config", {})

    detected_type = ckpt.get("model_type", norm_type).lower()

    if "transformer" in detected_type or "tf" in detected_type or norm_type in ["transformer", "tf"]:
        model = NetworkStateTransformer(
            input_size=cfg.get("input_size", NUM_FEATURES),
            d_model=cfg.get("d_model", 64),
            nhead=cfg.get("nhead", 4),
            num_layers=cfg.get("num_layers", 2),
            dim_feedforward=cfg.get("dim_feedforward", 128),
            num_classes=cfg.get("num_classes", NUM_STATES),
            dropout=cfg.get("dropout", 0.2),
        )
    elif "lstm" in detected_type or norm_type == "lstm":
        model = NetworkStateLSTM(
            input_size=cfg.get("input_size", NUM_FEATURES),
            hidden_size=cfg.get("hidden_size", 128),
            num_layers=cfg.get("num_layers", 2),
            num_classes=cfg.get("num_classes", NUM_STATES),
            dropout=cfg.get("dropout", 0.3),
        )
    else:
        # Default GRU
        model = NetworkStateGRU(
            input_size=cfg.get("input_size", NUM_FEATURES),
            hidden_size=cfg.get("hidden_size", 128),
            num_layers=cfg.get("num_layers", 2),
            num_classes=cfg.get("num_classes", NUM_STATES),
            dropout=cfg.get("dropout", 0.3),
        )

    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device)
    model.eval()

    # Load scaler
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)

    return model, scaler


def predict(
    model: nn.Module,
    scaler: Any,
    sequence: np.ndarray,
    device: str | torch.device | None = None,
) -> dict[str, Any]:
    """Run world-model inference on a single temporal sequence."""
    seq = np.asarray(sequence, dtype=np.float32)
    if seq.ndim == 1:
        seq = seq[np.newaxis, :]
    if seq.ndim != 2:
        raise ValueError(f"sequence must be 2-D (T, F), got shape {seq.shape}")

    T, F = seq.shape
    if F != NUM_FEATURES:
        raise ValueError(
            f"Expected {NUM_FEATURES} features per step (FEATURE_COLUMNS = {FEATURE_COLUMNS}), got {F}."
        )

    # Scale features
    seq_scaled = scaler.transform(seq[np.newaxis, :, :]).astype(np.float32)

    if device is None:
        model_device = next(model.parameters()).device
    elif isinstance(device, str):
        model_device = torch.device(device)
    else:
        model_device = device

    x = torch.tensor(seq_scaled, dtype=torch.float32).to(model_device)

    model.eval()
    with torch.no_grad():
        log_curr, log_next = model(x)

    prob_curr = torch.exp(log_curr)[0].cpu().tolist()
    prob_next = torch.exp(log_next)[0].cpu().tolist()

    curr_idx = int(np.argmax(prob_curr))
    next_idx = int(np.argmax(prob_next))

    future_states = [STATE_LABELS[next_idx]]
    current_proj = next_idx
    for _ in range(2):
        if current_proj < len(STATE_LABELS) - 1 and prob_next[current_proj] > 0.3:
            current_proj = min(current_proj + 1, len(STATE_LABELS) - 1)
        future_states.append(STATE_LABELS[current_proj])

    m_name = getattr(model, "model_type", model.__class__.__name__)

    return {
        "model_type": m_name,
        "current_state": STATE_LABELS[curr_idx],
        "predicted_state": STATE_LABELS[next_idx],
        "predicted_next_state": STATE_LABELS[next_idx],
        "future_states": future_states,
        "current_probabilities": {
            label: round(float(p), 4)
            for label, p in zip(STATE_LABELS, prob_curr)
        },
        "prediction_confidence": round(float(prob_next[next_idx]), 4),
    }


def predict_batch(
    model: nn.Module,
    scaler: Any,
    sequences: np.ndarray,
    device: str | torch.device | None = None,
    batch_size: int = 128,
) -> list[dict[str, Any]]:
    """Run world-model inference on a batch of sequences."""
    from torch.utils.data import DataLoader, TensorDataset

    seqs = np.asarray(sequences, dtype=np.float32)
    if seqs.ndim != 3:
        raise ValueError(f"sequences must be 3-D (N, T, F), got shape {seqs.shape}")

    seqs_scaled = scaler.transform(seqs).astype(np.float32)

    if device is None:
        model_device = next(model.parameters()).device
    elif isinstance(device, str):
        model_device = torch.device(device)
    else:
        model_device = device

    ds = TensorDataset(torch.tensor(seqs_scaled, dtype=torch.float32))
    loader = DataLoader(ds, batch_size=batch_size, shuffle=False)

    results = []
    model.eval()
    with torch.no_grad():
        for (X_b,) in loader:
            X_b = X_b.to(model_device)
            log_curr, log_next = model(X_b)
            prob_curr = torch.exp(log_curr).cpu().numpy()
            prob_next = torch.exp(log_next).cpu().numpy()

            for pc, pn in zip(prob_curr, prob_next):
                c_idx = int(pc.argmax())
                n_idx = int(pn.argmax())

                f_states = [STATE_LABELS[n_idx]]
                curr_p = n_idx
                for _ in range(2):
                    if curr_p < len(STATE_LABELS) - 1 and pn[curr_p] > 0.3:
                        curr_p = min(curr_p + 1, len(STATE_LABELS) - 1)
                    f_states.append(STATE_LABELS[curr_p])

                m_name = getattr(model, "model_type", model.__class__.__name__)
                results.append({
                    "model_type": m_name,
                    "current_state": STATE_LABELS[c_idx],
                    "predicted_state": STATE_LABELS[n_idx],
                    "predicted_next_state": STATE_LABELS[n_idx],
                    "future_states": f_states,
                    "current_probabilities": {
                        lbl: round(float(p), 4) for lbl, p in zip(STATE_LABELS, pc)
                    },
                    "prediction_confidence": round(float(pn[n_idx]), 4),
                })

    return results


__all__ = [
    "load_world_model",
    "predict",
    "predict_batch",
    "STATE_LABELS",
    "NUM_FEATURES",
    "FEATURE_COLUMNS",
]
