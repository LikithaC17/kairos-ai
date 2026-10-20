"""NetForecast AI — L2-Regularized Logistic Regression Baseline Forecaster.

Purpose
-------
This module provides a non-temporal, per-timestep baseline classifier for
network security state estimation. It intentionally uses no sequence history
(i.e., no look-back window), classifying each network flow snapshot
independently using its 7 raw feature values.

It serves as the benchmark comparison target for the temporal GRU world model
in models/temporal/lstm.py. A well-tuned temporal model must outperform this
baseline to justify the added complexity of sequence modelling.

Architecture
------------
Input  : single time-step feature vector  (F = 7 features)
Model  : Logistic Regression with L2 regularization (sklearn)
Output :
    current_state         : str  — predicted security state label
    current_probabilities : dict[str, float]  — per-class probabilities
    predicted_next_state  : str  — naive next-state (same as current; no temporal context)
    prediction_confidence : float

Feature columns (must match simulation/common.py::FEATURE_COLUMNS)
    flow_duration, packet_count, byte_count, packet_rate,
    byte_rate, inter_arrival_time, connection_frequency

Usage
-----
    # Train and save
    python models/baseline/logistic_regression.py --epochs 1000 --C 1.0

    # From another module
    from models.baseline.logistic_regression import BaselineForecaster
    clf = BaselineForecaster.load("checkpoints/baseline_lr.pkl")
    result = clf.predict(feature_vector)  # numpy array (7,)
"""

from __future__ import annotations

import argparse
import pickle
import sys
import time
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Project root on path
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from simulation.normal import generate_normal
from simulation.mixed_escalation import generate_mixed
from simulation.beaconing import generate_beaconing
from simulation.ddos import generate_ddos
from simulation.common import LADDER_STATES, FEATURE_COLUMNS

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
STATE_LABELS  = ["NORMAL", "ELEVATED", "SUSPICIOUS", "ATTACK"]
STATE_TO_IDX  = {s: i for i, s in enumerate(LADDER_STATES)}
NUM_FEATURES  = len(FEATURE_COLUMNS)

CHECKPOINT_DIR = PROJECT_ROOT / "checkpoints"
BASELINE_PATH  = CHECKPOINT_DIR / "baseline_lr.pkl"


# ---------------------------------------------------------------------------
# Scaler — simple log1p + standard scaling (no sklearn dependency for scaler)
# ---------------------------------------------------------------------------

class _Log1pScaler:
    """Lightweight log1p + z-score scaler (no sklearn dependency)."""

    def __init__(self) -> None:
        self.mean_: np.ndarray | None = None
        self.std_:  np.ndarray | None = None

    def fit(self, X: np.ndarray) -> "_Log1pScaler":
        """X shape: (N, F)."""
        log_X = np.log1p(np.abs(X))
        self.mean_ = log_X.mean(axis=0)
        self.std_  = log_X.std(axis=0) + 1e-8
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        log_X = np.log1p(np.abs(X))
        return (log_X - self.mean_) / self.std_

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        return self.fit(X).transform(X)


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def _generate_flat_dataset(rng: np.random.Generator,
                           total_per_scenario: int = 3000
                           ) -> tuple[np.ndarray, np.ndarray]:
    """Generate flat (non-windowed) train/test arrays from all scenarios.

    Returns
    -------
    X : (N, F)  float32 feature matrix — one row per timestep
    y : (N,)    int64 label vector
    """
    all_seqs: list[list[dict]] = []
    all_seqs += generate_normal(rng,    total_per_scenario, min_len=15, max_len=25)
    all_seqs += generate_beaconing(rng, total_per_scenario, min_len=15, max_len=25)
    all_seqs += generate_mixed(rng,     total_per_scenario, min_len=15, max_len=25)
    all_seqs += generate_ddos(rng,      total_per_scenario, min_len=15, max_len=25)

    rows_X, rows_y = [], []
    for seq in all_seqs:
        for step in seq:
            rows_X.append([step[col] for col in FEATURE_COLUMNS])
            rows_y.append(STATE_TO_IDX[step["state"]])

    X = np.array(rows_X, dtype=np.float32)
    y = np.array(rows_y, dtype=np.int64)
    return X, y


def _load_flat_from_csv(csv_path: str | Path) -> tuple[np.ndarray, np.ndarray]:
    """Load flat (non-windowed) feature matrix and labels from a CSV dataset file."""
    import pandas as pd

    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    missing = [c for c in FEATURE_COLUMNS + ["state"] if c not in df.columns]
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}")

    X = df[FEATURE_COLUMNS].values.astype(np.float32)
    y = np.array([STATE_TO_IDX[s] for s in df["state"]], dtype=np.int64)
    return X, y


# ---------------------------------------------------------------------------
# Baseline model wrapper
# ---------------------------------------------------------------------------

class BaselineForecaster:
    """L2-Regularized Logistic Regression baseline for security state classification.

    This classifier operates on a single time-step feature vector — it has
    no temporal context (no sequence history). Its purpose is to provide a
    fair non-temporal benchmark against the GRU world model.

    Parameters
    ----------
    C         : inverse regularization strength (higher = less regularization)
    max_iter  : maximum solver iterations
    solver    : sklearn LogisticRegression solver
    """

    def __init__(
        self,
        C: float = 1.0,
        max_iter: int = 1000,
        solver: str = "lbfgs",
    ) -> None:
        self.C        = C
        self.max_iter = max_iter
        self.solver   = solver
        self._clf     = None   # sklearn model, loaded lazily
        self._scaler  = _Log1pScaler()
        self._fitted  = False

    # ------------------------------------------------------------------
    def fit(self, X: np.ndarray, y: np.ndarray) -> "BaselineForecaster":
        """Fit on training data.

        Parameters
        ----------
        X : (N, F) float array of raw features
        y : (N,)   int array of class indices
        """
        from sklearn.linear_model import LogisticRegression

        X_s = self._scaler.fit_transform(X)
        self._clf = LogisticRegression(
            C=self.C,
            l1_ratio=0,                # l1_ratio=0 == pure L2 (modern sklearn >= 1.8)
            solver=self.solver,
            max_iter=self.max_iter,
            class_weight="balanced",
            random_state=42,
        )
        self._clf.fit(X_s, y)
        self._fitted = True
        return self

    # ------------------------------------------------------------------
    def predict(self, x: np.ndarray) -> dict:
        """Run inference on a single feature vector.

        Parameters
        ----------
        x : numpy array shape (F,) or (1, F) — one time-step snapshot

        Returns
        -------
        dict matching the temporal model's output schema:
            current_state         : str
            current_probabilities : dict[str, float]
            predicted_next_state  : str   (same as current — no temporal ctx)
            prediction_confidence : float
        """
        if not self._fitted:
            raise RuntimeError("Model not fitted. Call fit() or load() first.")

        x = np.atleast_2d(x).astype(np.float32)   # (1, F)
        x_s = self._scaler.transform(x)

        probs    = self._clf.predict_proba(x_s)[0]  # (num_classes,)
        pred_idx = int(np.argmax(probs))

        return {
            "current_state": STATE_LABELS[pred_idx],
            "current_probabilities": {
                label: round(float(p), 4)
                for label, p in zip(STATE_LABELS, probs)
            },
            # Baseline has no temporal context — naive assumption: state persists
            "predicted_next_state":  STATE_LABELS[pred_idx],
            "prediction_confidence": round(float(probs[pred_idx]), 4),
        }

    # ------------------------------------------------------------------
    def predict_batch(self, X: np.ndarray) -> list[dict]:
        """Run inference on a batch of feature vectors.

        Parameters
        ----------
        X : (N, F) array

        Returns
        -------
        List of prediction dicts, one per row.
        """
        return [self.predict(x) for x in X]

    # ------------------------------------------------------------------
    def score(self, X: np.ndarray, y: np.ndarray) -> dict:
        """Compute accuracy and per-class metrics on a labelled dataset.

        Parameters
        ----------
        X : (N, F)
        y : (N,)

        Returns
        -------
        dict with accuracy, f1_macro, f1_weighted
        """
        if not self._fitted:
            raise RuntimeError("Model not fitted.")

        from sklearn.metrics import accuracy_score, f1_score, classification_report

        X_s   = self._scaler.transform(X)
        preds = self._clf.predict(X_s)

        acc = accuracy_score(y, preds)
        f1m = f1_score(y, preds, average="macro",    zero_division=0)
        f1w = f1_score(y, preds, average="weighted", zero_division=0)

        print(classification_report(
            y, preds,
            labels=list(range(len(STATE_LABELS))),
            target_names=STATE_LABELS,
            zero_division=0,
            digits=4,
        ))

        return {
            "accuracy":    round(float(acc), 4),
            "f1_macro":    round(float(f1m), 4),
            "f1_weighted": round(float(f1w), 4),
        }

    # ------------------------------------------------------------------
    def save(self, path: Path | str = BASELINE_PATH) -> None:
        """Pickle the fitted forecaster to disk."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self, f)
        print(f"  Baseline checkpoint saved -> {path}")

    # ------------------------------------------------------------------
    @classmethod
    def load(cls, path: Path | str = BASELINE_PATH) -> "BaselineForecaster":
        """Load a saved BaselineForecaster from disk."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(
                f"Baseline checkpoint not found: {path}\n"
                "Run 'python models/baseline/logistic_regression.py' first."
            )
        with open(path, "rb") as f:
            obj = pickle.load(f)
        if not isinstance(obj, cls):
            raise TypeError(f"Loaded object is {type(obj)}, expected BaselineForecaster.")
        return obj


# ---------------------------------------------------------------------------
# Training entry-point
# ---------------------------------------------------------------------------

def train(
    C: float = 1.0,
    max_iter: int = 1000,
    seed: int = 42,
    total_per_scenario: int = 3000,
    csv_path: str | Path | None = None,
) -> None:
    print("=" * 65)
    print("  NetForecast AI -- Baseline LR Forecaster Training")
    print("=" * 65)

    rng = np.random.default_rng(seed)

    # --- Load or Generate data -------------------------------------------
    if csv_path is not None:
        print(f"\n[1/4] Loading flat timestep dataset from CSV: {csv_path} ...")
        t0 = time.time()
        X, y = _load_flat_from_csv(csv_path)
        print(f"      {len(X):,} timestep samples loaded in {time.time()-t0:.1f}s")
    else:
        print("\n[1/4] Generating flat timestep dataset ...")
        t0 = time.time()
        X, y = _generate_flat_dataset(rng, total_per_scenario)
        print(f"      {len(X):,} timestep samples in {time.time()-t0:.1f}s")

    # --- Chronological split (match temporal model protocol) -------------
    n         = len(X)
    train_end = int(n * 0.70)
    val_end   = int(n * 0.85)
    X_tr, y_tr = X[:train_end],      y[:train_end]
    X_va, y_va = X[train_end:val_end], y[train_end:val_end]
    X_te, y_te = X[val_end:],         y[val_end:]

    print(f"\n[2/4] Chronological split (no leakage)")
    print(f"      Train: {len(X_tr):,} | Val: {len(X_va):,} | Test: {len(X_te):,}")

    # --- Fit -------------------------------------------------------------
    print(f"\n[3/4] Fitting Logistic Regression (C={C}, L2, max_iter={max_iter}) ...")
    clf = BaselineForecaster(C=C, max_iter=max_iter)
    t0 = time.time()
    clf.fit(X_tr, y_tr)
    print(f"      Converged in {time.time()-t0:.1f}s")

    # --- Evaluate --------------------------------------------------------
    print(f"\n[4/4] Evaluation on held-out test set ...")
    print("-" * 65)
    print("  BASELINE TEST RESULTS (frozen chronological hold-out)")
    print("-" * 65)
    metrics = clf.score(X_te, y_te)
    print(f"  Accuracy    : {metrics['accuracy']:.4f}  ({metrics['accuracy']*100:.2f}%)")
    print(f"  F1-Macro    : {metrics['f1_macro']:.4f}")
    print(f"  F1-Weighted : {metrics['f1_weighted']:.4f}")
    print("-" * 65)

    # Also score on validation set
    print(f"\n  Validation metrics (sanity check):")
    val_metrics = clf.score(X_va, y_va)
    print(f"  Val Accuracy    : {val_metrics['accuracy']:.4f}")

    # --- Save ------------------------------------------------------------
    clf.save(BASELINE_PATH)
    print("\n  Training complete.\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train the NetForecast baseline logistic regression forecaster"
    )
    parser.add_argument("--C",     type=float, default=1.0,   help="Inverse regularization strength")
    parser.add_argument("--iter",  type=int,   default=1000,  help="Max solver iterations")
    parser.add_argument("--seed",  type=int,   default=42,    help="Random seed")
    parser.add_argument("--rows",  type=int,   default=3000,  help="Rows per scenario")
    parser.add_argument("--csv",   type=str,   default=None,  help="Path to CSV dataset file")
    args = parser.parse_args()

    csv_target = args.csv
    if csv_target is None:
        candidates = [
            PROJECT_ROOT.parent / "network_traffic_10000.csv",
            PROJECT_ROOT / "network_traffic_10000.csv",
            Path("network_traffic_10000.csv"),
        ]
        for candidate in candidates:
            if candidate.exists():
                csv_target = candidate
                break

    train(
        C=args.C,
        max_iter=args.iter,
        seed=args.seed,
        total_per_scenario=args.rows,
        csv_path=csv_target,
    )
