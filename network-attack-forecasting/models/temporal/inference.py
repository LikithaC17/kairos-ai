"""NetForecast AI — Reusable inference interface.

This module exposes two public functions that the prediction engine
(or any other module) can call without knowing the internals of the model:

    load_world_model(checkpoint_dir)  →  (model, scaler)
    predict(model, scaler, sequence)  →  inference_dict

Inference output contract
--------------------------
{
    "current_state"        : str,           # one of NORMAL/ELEVATED/SUSPICIOUS/ATTACK
    "current_probabilities": dict[str,float],
    "predicted_next_state" : str,
    "prediction_confidence": float          # probability of the predicted next state
}

Usage example
-------------
>>> from models.temporal.inference import load_world_model, predict
>>> import numpy as np
>>> model, scaler = load_world_model("checkpoints")
>>> # sequence: numpy array of shape (T, 7) — one row per time step
>>> seq = np.random.rand(20, 7)
>>> result = predict(model, scaler, seq)
>>> print(result)
"""

from __future__ import annotations

import pickle
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch

# ── project root on path ─────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from models.temporal.lstm import NetworkStateGRU, STATE_LABELS, NUM_FEATURES, FEATURE_COLUMNS

# ─────────────────────────────────────────────────────────────────────────────
# Default checkpoint locations (matches train.py)
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULT_CHECKPOINT_DIR = PROJECT_ROOT / "checkpoints"
_DEFAULT_MODEL_PATH     = _DEFAULT_CHECKPOINT_DIR / "world_model_gru.pt"
_DEFAULT_SCALER_PATH    = _DEFAULT_CHECKPOINT_DIR / "world_model_scaler.pkl"


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def load_world_model(
    checkpoint_dir: str | Path | None = None,
    device: str | torch.device | None = None,
) -> tuple[NetworkStateGRU, Any]:
    """Load the trained world model and scaler from disk.

    Parameters
    ----------
    checkpoint_dir : directory containing world_model_gru.pt and
                     world_model_scaler.pkl. Defaults to <project_root>/checkpoints.
    device         : torch device string or object. Defaults to CUDA if
                     available, otherwise CPU.

    Returns
    -------
    model  : NetworkStateGRU (eval mode, on requested device)
    scaler : fitted Log1pStandardScaler instance

    Raises
    ------
    FileNotFoundError if checkpoint files are missing.
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    elif isinstance(device, str):
        device = torch.device(device)

    if checkpoint_dir is None:
        model_path  = _DEFAULT_MODEL_PATH
        scaler_path = _DEFAULT_SCALER_PATH
    else:
        d = Path(checkpoint_dir)
        model_path  = d / "world_model_gru.pt"
        scaler_path = d / "world_model_scaler.pkl"

    if not model_path.exists():
        raise FileNotFoundError(
            f"Model checkpoint not found at {model_path}. "
            "Run 'python models/temporal/train.py' to train the model first."
        )
    if not scaler_path.exists():
        raise FileNotFoundError(
            f"Scaler not found at {scaler_path}. "
            "Run 'python models/temporal/train.py' to train the model first."
        )

    # Load and reconstruct model
    ckpt = torch.load(model_path, map_location=device)
    cfg  = ckpt["config"]
    model = NetworkStateGRU(
        input_size=cfg["input_size"],
        hidden_size=cfg["hidden_size"],
        num_layers=cfg["num_layers"],
        num_classes=cfg["num_classes"],
        dropout=cfg["dropout"],
    )
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device)
    model.eval()

    # Load scaler
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)

    return model, scaler


def predict(
    model: NetworkStateGRU,
    scaler: Any,
    sequence: np.ndarray,
    device: str | torch.device | None = None,
) -> dict[str, Any]:
    """Run world-model inference on a single temporal sequence.

    Parameters
    ----------
    model    : trained NetworkStateGRU (loaded via load_world_model)
    scaler   : fitted Log1pStandardScaler (loaded via load_world_model)
    sequence : numpy array of shape (T, F) where
                   T = number of time steps (e.g. 20)
                   F = number of features   (7: flow_duration, packet_count,
                       byte_count, packet_rate, byte_rate,
                       inter_arrival_time, connection_frequency)
               Values must be in the original (unscaled) domain.
    device   : torch device. If None, uses the device of the model parameters.

    Returns
    -------
    dict with keys:
        "current_state"         str  — most probable current security state
        "current_probabilities" dict — probability for each of the 4 states
        "predicted_next_state"  str  — most probable next security state
        "prediction_confidence" float — probability of the predicted next state

    Raises
    ------
    ValueError  if sequence shape is incompatible.
    RuntimeError if model is not in eval mode.
    """
    # ── Input validation ──────────────────────────────────────────────
    seq = np.asarray(sequence, dtype=np.float32)
    if seq.ndim == 1:
        # Single feature vector: treat as (1, F) — trivial sequence
        seq = seq[np.newaxis, :]
    if seq.ndim != 2:
        raise ValueError(
            f"sequence must be 2-D (T, F), got shape {seq.shape}"
        )
    T, F = seq.shape
    if F != NUM_FEATURES:
        raise ValueError(
            f"Expected {NUM_FEATURES} features per step (FEATURE_COLUMNS = {FEATURE_COLUMNS}), "
            f"got {F}."
        )

    # ── Scale features ────────────────────────────────────────────────
    seq_scaled = scaler.transform(seq[np.newaxis, :, :]).astype(np.float32)  # (1, T, F)

    # ── Device handling ───────────────────────────────────────────────
    if device is None:
        model_device = next(model.parameters()).device
    elif isinstance(device, str):
        model_device = torch.device(device)
    else:
        model_device = device

    x = torch.tensor(seq_scaled, dtype=torch.float32).to(model_device)  # (1, T, F)

    # ── Inference ─────────────────────────────────────────────────────
    model.eval()
    with torch.no_grad():
        log_curr, log_next = model(x)

    prob_curr = torch.exp(log_curr)[0].cpu().tolist()  # list of 4 floats
    prob_next = torch.exp(log_next)[0].cpu().tolist()

    curr_idx = int(np.argmax(prob_curr))
    next_idx = int(np.argmax(prob_next))

    future_states = [STATE_LABELS[next_idx]]
    current_proj = next_idx
    for _ in range(2):
        if current_proj < len(STATE_LABELS) - 1 and prob_next[current_proj] > 0.3:
            current_proj = min(current_proj + 1, len(STATE_LABELS) - 1)
        future_states.append(STATE_LABELS[current_proj])

    return {
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
    model: NetworkStateGRU,
    scaler: Any,
    sequences: np.ndarray,
    device: str | torch.device | None = None,
    batch_size: int = 128,
) -> list[dict[str, Any]]:
    """Run world-model inference on a batch of sequences.

    Parameters
    ----------
    model     : trained NetworkStateGRU
    scaler    : fitted Log1pStandardScaler
    sequences : numpy array of shape (N, T, F)
    batch_size: mini-batch size for GPU memory management

    Returns
    -------
    list of N inference dicts (same schema as predict())
    """
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

    ds     = TensorDataset(torch.tensor(seqs_scaled, dtype=torch.float32))
    loader = DataLoader(ds, batch_size=batch_size, shuffle=False)

    results = []
    model.eval()
    with torch.no_grad():
        for (X_b,) in loader:
            X_b = X_b.to(model_device)
            log_curr, log_next = model(X_b)
            prob_c = torch.exp(log_curr).cpu().numpy()
            prob_n = torch.exp(log_next).cpu().numpy()
            for pc, pn in zip(prob_c, prob_n):
                ci = int(pc.argmax())
                ni = int(pn.argmax())
                fut = [STATE_LABELS[ni]]
                c_proj = ni
                for _ in range(2):
                    if c_proj < len(STATE_LABELS) - 1 and pn[c_proj] > 0.3:
                        c_proj = min(c_proj + 1, len(STATE_LABELS) - 1)
                    fut.append(STATE_LABELS[c_proj])

                results.append({
                    "current_state": STATE_LABELS[ci],
                    "predicted_state": STATE_LABELS[ni],
                    "predicted_next_state": STATE_LABELS[ni],
                    "future_states": fut,
                    "current_probabilities": {
                        label: round(float(p), 4)
                        for label, p in zip(STATE_LABELS, pc)
                    },
                    "prediction_confidence": round(float(pn[ni]), 4),
                })
    return results


# ─────────────────────────────────────────────────────────────────────────────
# Smoke test (run as __main__)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json
    from models.temporal.train import generate_all_sequences, build_dataset, SEQUENCE_LENGTH

    print("=" * 65)
    print("  NetForecast AI — Inference Smoke Test")
    print("=" * 65)

    print("\n[1/3] Loading model and scaler ...")
    model, scaler = load_world_model()
    print(f"  Model device: {next(model.parameters()).device}")

    print("\n[2/3] Generating sample sequences from simulator ...")
    rng = np.random.default_rng(99)
    # Use simulation data for realistic smoke-test samples
    from simulation.normal import generate_normal
    from simulation.ddos import generate_ddos

    normal_seqs = generate_normal(rng, 200, min_len=SEQUENCE_LENGTH + 5, max_len=SEQUENCE_LENGTH + 10)
    ddos_seqs   = generate_ddos(rng,   200, min_len=SEQUENCE_LENGTH + 5, max_len=SEQUENCE_LENGTH + 10)

    sample_seqs = normal_seqs[:3] + ddos_seqs[:3]
    labels_true = (["NORMAL"] * 3) + (["ATTACK/SUSPICIOUS"] * 3)

    print(f"\n[3/3] Running inference on {len(sample_seqs)} sample sequences ...")
    print(f"\n{'-'*65}")

    for i, (seq, true_label) in enumerate(zip(sample_seqs, labels_true)):
        # Take the last SEQUENCE_LENGTH rows as the temporal window
        window = np.array([[row[col] for col in FEATURE_COLUMNS]
                           for row in seq[-SEQUENCE_LENGTH:]], dtype=np.float32)
        actual_state = seq[-1]["state"]

        result = predict(model, scaler, window)

        print(f"\n  Sample {i+1}  [True: {true_label} | Actual last state: {actual_state}]")
        print(f"    current_state        : {result['current_state']}")
        print(f"    current_probabilities: {result['current_probabilities']}")
        print(f"    predicted_next_state : {result['predicted_next_state']}")
        print(f"    prediction_confidence: {result['prediction_confidence']}")

    print(f"\n{'-'*65}")
    print("  Smoke test complete — inference interface working correctly.\n")
