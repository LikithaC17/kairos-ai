"""Temporal sliding-window sequence generation for World Model consumption.

Module: network-attack-forecasting.preprocessing.windowing
Author: Vikas (Feature Engineering & Preprocessing)

Features:
- Constructs sliding-window sequences X of shape (N, T, F) for GRU / LSTM / Transformer
- Aligns discrete state targets (current state at t, next state at t+1)
- Aligns human-readable attack stages (Baseline, Reconnaissance, Scanning, Initial Access, etc.)
- Aligns security metadata (flow_id, timestamp, scenario, label, severity)
- Generates next-step feature prediction targets y_feat of shape (N, F)
- Implements strict chronological splitting with zero window leakage across boundaries
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

# State progression mapping (matches simulation.common and models.temporal.lstm)
LADDER_STATES = ["NORMAL", "ELEVATED", "SUSPICIOUS", "ATTACK"]
STATE_TO_IDX = {s: i for i, s in enumerate(LADDER_STATES)}
IDX_TO_STATE = {i: s for i, s in enumerate(LADDER_STATES)}

# Attack stage mapping (matches prediction.state_machine)
STATE_TO_STAGES = {
    "NORMAL": ["Baseline"],
    "ELEVATED": ["Reconnaissance", "Scanning"],
    "SUSPICIOUS": ["Initial Access", "Command and Control"],
    "ATTACK": ["Lateral Movement", "Exfiltration", "Impact"],
}


def map_state_to_stage(state: str, history: Optional[List[str]] = None) -> str:
    """Map internal state label to human-readable attack stage with history awareness."""
    stages = STATE_TO_STAGES.get(state, ["Unknown"])
    if len(stages) == 1 or not history:
        return stages[0]

    # Count consecutive occurrences in history to pick deeper stage
    consecutive = 0
    for s in reversed(history):
        if s == state:
            consecutive += 1
        else:
            break

    idx = min(consecutive, len(stages) - 1)
    return stages[idx]


def create_sliding_windows(
    feature_matrix: np.ndarray,
    meta_df: pd.DataFrame,
    sequence_length: int = 20,
    forecast_horizon: int = 1,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, pd.DataFrame]:
    """Generate chronological sliding-window sequences and aligned targets.

    Parameters
    ----------
    feature_matrix : np.ndarray
        Array of shape (N_records, F_features).
    meta_df : pd.DataFrame
        DataFrame with metadata and ground-truth targets (state, label, severity, scenario, timestamp, flow_id).
    sequence_length : int
        Window length T (default 20).
    forecast_horizon : int
        Steps ahead for next-state prediction (default 1).

    Returns
    -------
    X : np.ndarray
        Shape (N_seqs, sequence_length, F_features).
    y_current : np.ndarray
        State index for the last step in the window (t). Shape (N_seqs,).
    y_next : np.ndarray
        State index for the forecasted step (t + forecast_horizon). Shape (N_seqs,).
    y_feat : np.ndarray
        Next-step continuous feature vector (t + forecast_horizon). Shape (N_seqs, F_features).
    target_meta : pd.DataFrame
        Aligned metadata, ground-truth label, severity, and attack stage for each sequence.
    """
    n_records = len(feature_matrix)
    required_steps = sequence_length + forecast_horizon

    if n_records < required_steps:
        raise ValueError(
            f"Not enough records ({n_records}) for sequence_length={sequence_length} and horizon={forecast_horizon}"
        )

    X_list = []
    y_curr_list = []
    y_next_list = []
    y_feat_list = []
    meta_rows = []

    state_col = meta_df["state"].values if "state" in meta_df.columns else ["NORMAL"] * n_records
    label_col = meta_df["label"].values if "label" in meta_df.columns else ["BENIGN"] * n_records
    sev_col = meta_df["severity"].values if "severity" in meta_df.columns else ["LOW"] * n_records
    scen_col = meta_df["scenario"].values if "scenario" in meta_df.columns else ["normal"] * n_records
    ts_col = meta_df["timestamp"].values if "timestamp" in meta_df.columns else range(n_records)
    flow_col = meta_df["flow_id"].values if "flow_id" in meta_df.columns else range(n_records)

    state_history = []

    for i in range(n_records - required_steps + 1):
        window_end = i + sequence_length
        target_idx = window_end + forecast_horizon - 1

        # Input window: [i .. window_end - 1]
        X_list.append(feature_matrix[i:window_end])

        # Current state: at last step of window
        curr_state_str = str(state_col[window_end - 1]).upper()
        curr_state_idx = STATE_TO_IDX.get(curr_state_str, 0)
        y_curr_list.append(curr_state_idx)

        # Next state: at target_idx
        next_state_str = str(state_col[target_idx]).upper()
        next_state_idx = STATE_TO_IDX.get(next_state_str, 0)
        y_next_list.append(next_state_idx)

        # Next features: at target_idx
        y_feat_list.append(feature_matrix[target_idx])

        # Attack stage resolution
        attack_stage = map_state_to_stage(next_state_str, history=state_history[-10:])
        state_history.append(curr_state_str)

        meta_rows.append({
            "sequence_id": i,
            "target_flow_id": flow_col[target_idx],
            "target_timestamp": ts_col[target_idx],
            "current_state": curr_state_str,
            "target_state": next_state_str,
            "target_stage": attack_stage,
            "target_label": label_col[target_idx],
            "target_severity": sev_col[target_idx],
            "target_scenario": scen_col[target_idx],
        })

    X = np.array(X_list, dtype=np.float32)
    y_current = np.array(y_curr_list, dtype=np.int64)
    y_next = np.array(y_next_list, dtype=np.int64)
    y_feat = np.array(y_feat_list, dtype=np.float32)
    target_meta_df = pd.DataFrame(meta_rows)

    return X, y_current, y_next, y_feat, target_meta_df


def split_temporal_dataset(
    df: pd.DataFrame,
    train_frac: float = 0.70,
    val_frac: float = 0.15,
    test_frac: float = 0.15,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Strict chronological partition of dataframe without shuffling.

    Ensures zero temporal data leakage across train, val, and test splits.
    """
    if not np.isclose(train_frac + val_frac + test_frac, 1.0):
        raise ValueError(f"Fractions must sum to 1.0 (got {train_frac + val_frac + test_frac})")

    n = len(df)
    train_end = int(train_frac * n)
    val_end = int((train_frac + val_frac) * n)

    train_df = df.iloc[:train_end].copy().reset_index(drop=True)
    val_df = df.iloc[train_end:val_end].copy().reset_index(drop=True)
    test_df = df.iloc[val_end:].copy().reset_index(drop=True)

    return train_df, val_df, test_df


def create_split_sequences(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_columns: List[str],
    sequence_length: int = 20,
    forecast_horizon: int = 1,
) -> Dict[str, Dict[str, Union[np.ndarray, pd.DataFrame]]]:
    """Create temporal sequences strictly within each split boundary.

    No sliding window crosses the split border, strictly eliminating data leakage.
    """
    splits = {"train": train_df, "val": val_df, "test": test_df}
    result = {}

    for split_name, split_df in splits.items():
        feat_mat = split_df[feature_columns].values.astype(np.float32)
        X, yc, yn, yf, meta = create_sliding_windows(
            feature_matrix=feat_mat,
            meta_df=split_df,
            sequence_length=sequence_length,
            forecast_horizon=forecast_horizon,
        )
        result[split_name] = {
            "X": X,
            "y_curr": yc,
            "y_next": yn,
            "y_feat": yf,
            "metadata": meta,
        }

    return result


def save_sequence_artifacts(
    split_sequences: Dict[str, Dict[str, Union[np.ndarray, pd.DataFrame]]],
    output_dir: Union[str, Path],
) -> Dict[str, Path]:
    """Save temporal sequence artifacts to output directory.

    Saves:
    - X_train.npy, X_val.npy, X_test.npy
    - y_curr_train.npy, y_curr_val.npy, y_curr_test.npy
    - y_next_train.npy, y_next_val.npy, y_next_test.npy
    - metadata_train.csv, metadata_val.csv, metadata_test.csv
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    saved_paths = {}

    for split_name, data in split_sequences.items():
        x_path = out_path / f"X_{split_name}.npy"
        yc_path = out_path / f"y_curr_{split_name}.npy"
        yn_path = out_path / f"y_next_{split_name}.npy"
        yf_path = out_path / f"y_feat_{split_name}.npy"
        meta_path = out_path / f"metadata_{split_name}.csv"

        np.save(x_path, data["X"])
        np.save(yc_path, data["y_curr"])
        np.save(yn_path, data["y_next"])
        np.save(yf_path, data["y_feat"])
        data["metadata"].to_csv(meta_path, index=False)

        saved_paths[f"X_{split_name}"] = x_path
        saved_paths[f"y_curr_{split_name}"] = yc_path
        saved_paths[f"y_next_{split_name}"] = yn_path
        saved_paths[f"y_feat_{split_name}"] = yf_path
        saved_paths[f"metadata_{split_name}"] = meta_path

    return saved_paths
