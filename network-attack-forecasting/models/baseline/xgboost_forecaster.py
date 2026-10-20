"""NetForecast AI — XGBoost Temporal Forecaster.

What it does
------------
This model answers the question:
    "Given the CURRENT network state (observed over the last T time steps),
     what could happen NEXT?"

It is NOT a simple "is this traffic malicious?" classifier.
It is a TEMPORAL FORECASTER trained on windowed sequences of network flow
statistics, matching the exact same input/output contract as the GRU world
model in models/temporal/lstm.py.

Architecture
------------
Input  : Flattened temporal sequence  (T=20 steps x F=7 features = 140 features)
         — the same 20-step window used by the GRU, but flattened for XGBoost
         — this gives the tree model full temporal context across 20 timesteps

Two separate XGBoostClassifiers are trained:
    Booster A (xgb_current) : predicts the CURRENT security state
    Booster B (xgb_next)    : predicts the NEXT security state (1-step ahead)

Output schema (identical to GRU model for direct comparison):
    {
        "current_state"         : str,
        "current_probabilities" : dict[str, float],
        "predicted_next_state"  : str,
        "prediction_confidence" : float
    }

Why XGBoost + windowed sequences?
----------------------------------
Gradient Boosted Trees cannot process sequences natively, but by flattening
a fixed-length window into a feature vector, each timestep's features become
explicit input columns:
    [t-19_flow_dur, t-19_pkt_cnt, ..., t-0_flow_dur, t-0_pkt_cnt, ...]
This gives XGBoost temporal context while using its powerful gradient boosting
to capture non-linear state transitions — a strong ensemble baseline that sits
between logistic regression (no sequence context) and GRU (full recurrent context).

Usage
-----
    # Train and save
    python models/baseline/xgboost_forecaster.py

    # From another module
    from models.baseline.xgboost_forecaster import XGBoostForecaster
    clf = XGBoostForecaster.load("checkpoints/xgboost_forecaster.pkl")
    result = clf.predict(sequence)   # sequence: numpy (T, F)
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
from models.temporal.train import (
    generate_all_sequences,
    build_dataset,
    load_dataset_from_csv,
    SEQUENCE_LENGTH,
)
from models.temporal.lstm import Log1pStandardScaler

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
STATE_LABELS   = ["NORMAL", "ELEVATED", "SUSPICIOUS", "ATTACK"]
STATE_TO_IDX   = {s: i for i, s in enumerate(LADDER_STATES)}
NUM_FEATURES   = len(FEATURE_COLUMNS)
NUM_CLASSES    = len(STATE_LABELS)

CHECKPOINT_DIR = PROJECT_ROOT / "checkpoints"
XGB_PATH       = CHECKPOINT_DIR / "xgboost_forecaster.pkl"


# ---------------------------------------------------------------------------
# XGBoost Temporal Forecaster
# ---------------------------------------------------------------------------

class XGBoostForecaster:
    """XGBoost-based temporal forecaster for network security state prediction.

    Trains two gradient-boosted classifiers on flattened temporal windows:
        - xgb_current : predicts current security state from last T steps
        - xgb_next    : predicts next security state (1-step ahead forecast)

    Parameters
    ----------
    n_estimators  : number of boosting rounds
    max_depth     : maximum tree depth
    learning_rate : shrinkage factor (eta)
    subsample     : row subsampling ratio per tree
    colsample     : column subsampling ratio per tree
    """

    def __init__(
        self,
        n_estimators: int  = 300,
        max_depth: int     = 6,
        learning_rate: float = 0.1,
        subsample: float   = 0.8,
        colsample: float   = 0.8,
    ) -> None:
        self.n_estimators  = n_estimators
        self.max_depth     = max_depth
        self.learning_rate = learning_rate
        self.subsample     = subsample
        self.colsample     = colsample
        self._xgb_current  = None
        self._xgb_next     = None
        self._scaler       = Log1pStandardScaler()
        self._fitted       = False

    # ------------------------------------------------------------------
    def _flatten(self, X: np.ndarray) -> np.ndarray:
        """Flatten (N, T, F) -> (N, T*F) for XGBoost input."""
        N = X.shape[0]
        return X.reshape(N, -1)

    # ------------------------------------------------------------------
    def fit(
        self,
        X: np.ndarray,
        yc: np.ndarray,
        yn: np.ndarray,
        X_val: np.ndarray | None = None,
        yc_val: np.ndarray | None = None,
        yn_val: np.ndarray | None = None,
    ) -> "XGBoostForecaster":
        """Fit both boosters on windowed training data.

        Parameters
        ----------
        X   : (N, T, F) — windowed sequences
        yc  : (N,)      — current-state labels
        yn  : (N,)      — next-state labels
        X_val, yc_val, yn_val : optional validation set for early stopping
        """
        import xgboost as xgb

        # Scale
        X_s = self._scaler.fit_transform(X).astype(np.float32)
        X_flat = self._flatten(X_s)

        # Validation set
        eval_current = eval_next = None
        if X_val is not None:
            Xv_s    = self._scaler.transform(X_val).astype(np.float32)
            Xv_flat = self._flatten(Xv_s)
            eval_current = [(Xv_flat, yc_val)]
            eval_next    = [(Xv_flat, yn_val)]

        # Shared XGB params
        base_params = dict(
            n_estimators  = self.n_estimators,
            max_depth     = self.max_depth,
            learning_rate = self.learning_rate,
            subsample     = self.subsample,
            colsample_bytree = self.colsample,
            objective     = "multi:softprob",
            num_class     = NUM_CLASSES,
            eval_metric   = "mlogloss",
            use_label_encoder = False,
            random_state  = 42,
            n_jobs        = -1,
            verbosity     = 0,
        )

        # --- Booster A: Current State ---
        print("      Fitting Booster A (current state) ...")
        self._xgb_current = xgb.XGBClassifier(**base_params)
        if eval_current:
            self._xgb_current.set_params(early_stopping_rounds=20)
            self._xgb_current.fit(
                X_flat, yc,
                eval_set=eval_current,
                verbose=False,
            )
        else:
            self._xgb_current.fit(X_flat, yc, verbose=False)

        # --- Booster B: Next State (Forecasting) ---
        print("      Fitting Booster B (next-state forecast) ...")
        self._xgb_next = xgb.XGBClassifier(**base_params)
        if eval_next:
            self._xgb_next.set_params(early_stopping_rounds=20)
            self._xgb_next.fit(
                X_flat, yn,
                eval_set=eval_next,
                verbose=False,
            )
        else:
            self._xgb_next.fit(X_flat, yn, verbose=False)

        self._fitted = True
        return self

    # ------------------------------------------------------------------
    def predict(self, sequence: np.ndarray) -> dict:
        """Run temporal forecast on a single sequence window.

        Parameters
        ----------
        sequence : numpy array shape (T, F)  — temporal feature sequence
                   (same input format as the GRU model)

        Returns
        -------
        dict matching the GRU model's output schema:
            current_state         : str
            current_probabilities : dict[str, float]
            predicted_next_state  : str
            prediction_confidence : float
        """
        if not self._fitted:
            raise RuntimeError("Model not fitted. Call fit() or load() first.")

        seq = np.atleast_2d(sequence)           # (T, F)
        seq = seq[np.newaxis, :, :]             # (1, T, F)
        seq_s   = self._scaler.transform(seq).astype(np.float32)
        seq_flat = self._flatten(seq_s)         # (1, T*F)

        prob_curr = self._xgb_current.predict_proba(seq_flat)[0]
        prob_next = self._xgb_next.predict_proba(seq_flat)[0]

        curr_idx = int(np.argmax(prob_curr))
        next_idx = int(np.argmax(prob_next))

        return {
            "current_state": STATE_LABELS[curr_idx],
            "current_probabilities": {
                label: round(float(p), 4)
                for label, p in zip(STATE_LABELS, prob_curr)
            },
            "predicted_next_state":  STATE_LABELS[next_idx],
            "prediction_confidence": round(float(prob_next[next_idx]), 4),
        }

    # ------------------------------------------------------------------
    def predict_batch(self, sequences: np.ndarray) -> list[dict]:
        """Run temporal forecast on a batch of sequences.

        Parameters
        ----------
        sequences : (N, T, F) array

        Returns
        -------
        list of prediction dicts
        """
        if not self._fitted:
            raise RuntimeError("Model not fitted.")

        X_s    = self._scaler.transform(sequences).astype(np.float32)
        X_flat = self._flatten(X_s)

        prob_curr_all = self._xgb_current.predict_proba(X_flat)
        prob_next_all = self._xgb_next.predict_proba(X_flat)

        results = []
        for prob_curr, prob_next in zip(prob_curr_all, prob_next_all):
            curr_idx = int(np.argmax(prob_curr))
            next_idx = int(np.argmax(prob_next))
            results.append({
                "current_state": STATE_LABELS[curr_idx],
                "current_probabilities": {
                    label: round(float(p), 4)
                    for label, p in zip(STATE_LABELS, prob_curr)
                },
                "predicted_next_state":  STATE_LABELS[next_idx],
                "prediction_confidence": round(float(prob_next[next_idx]), 4),
            })
        return results

    # ------------------------------------------------------------------
    def score(self, X: np.ndarray, yc: np.ndarray, yn: np.ndarray) -> dict:
        """Compute metrics for both heads on a test set.

        Parameters
        ----------
        X  : (N, T, F) windowed sequences
        yc : (N,) current-state labels
        yn : (N,) next-state labels
        """
        if not self._fitted:
            raise RuntimeError("Model not fitted.")

        from sklearn.metrics import accuracy_score, f1_score, classification_report

        X_s    = self._scaler.transform(X).astype(np.float32)
        X_flat = self._flatten(X_s)

        pred_curr = self._xgb_current.predict(X_flat)
        pred_next = self._xgb_next.predict(X_flat)

        acc_c = accuracy_score(yc, pred_curr)
        acc_n = accuracy_score(yn, pred_next)
        f1_c  = f1_score(yc, pred_curr, average="weighted", zero_division=0)
        f1_n  = f1_score(yn, pred_next, average="weighted", zero_division=0)

        print("\n  HEAD A — Current State:")
        print(classification_report(
            yc, pred_curr,
            labels=list(range(NUM_CLASSES)),
            target_names=STATE_LABELS,
            zero_division=0, digits=4,
        ))
        print("  HEAD B — Next-State Forecast:")
        print(classification_report(
            yn, pred_next,
            labels=list(range(NUM_CLASSES)),
            target_names=STATE_LABELS,
            zero_division=0, digits=4,
        ))

        return {
            "current_accuracy":    round(float(acc_c), 4),
            "next_accuracy":       round(float(acc_n), 4),
            "current_f1_weighted": round(float(f1_c),  4),
            "next_f1_weighted":    round(float(f1_n),  4),
        }

    # ------------------------------------------------------------------
    def save(self, path: Path | str = XGB_PATH) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self, f)
        print(f"  XGBoost checkpoint saved -> {path}")

    # ------------------------------------------------------------------
    @classmethod
    def load(cls, path: Path | str = XGB_PATH) -> "XGBoostForecaster":
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(
                f"XGBoost checkpoint not found: {path}\n"
                "Run 'python models/baseline/xgboost_forecaster.py' first."
            )
        with open(path, "rb") as f:
            return pickle.load(f)


# ---------------------------------------------------------------------------
# Training entry-point
# ---------------------------------------------------------------------------

def train(
    n_estimators: int  = 300,
    max_depth: int     = 6,
    seed: int          = 42,
    total_per_scenario: int = 3000,
    csv_path: str | Path | None = None,
) -> None:
    print("=" * 65)
    print("  NetForecast AI -- XGBoost Temporal Forecaster Training")
    print("=" * 65)
    print("  Goal: 'Given the current network state sequence,")
    print("         what could happen NEXT?'")
    print(f"  Window  : {SEQUENCE_LENGTH} timesteps x {NUM_FEATURES} features")
    print(f"  Input   : flattened ({SEQUENCE_LENGTH * NUM_FEATURES} features per sample)")
    print(f"  Boosters: 2 (current state + next-state forecast)")

    rng = np.random.default_rng(seed)

    # --- Load or Generate windowed dataset -------------------------------
    if csv_path is not None:
        print(f"\n[1/4] Loading temporal sequence dataset from CSV: {csv_path} ...")
        t0 = time.time()
        X_all, yc_all, yn_all = load_dataset_from_csv(csv_path, SEQUENCE_LENGTH)
        print(f"      {len(X_all):,} windowed samples extracted in {time.time()-t0:.1f}s")

        n         = len(X_all)
        train_end = int(n * 0.70)
        val_end   = int(n * 0.85)

        X_tr, yc_tr, yn_tr = X_all[:train_end], yc_all[:train_end], yn_all[:train_end]
        X_va, yc_va, yn_va = X_all[train_end:val_end], yc_all[train_end:val_end], yn_all[train_end:val_end]
        X_te, yc_te, yn_te = X_all[val_end:], yc_all[val_end:], yn_all[val_end:]
    else:
        print("\n[1/4] Generating temporal sequence dataset ...")
        t0 = time.time()
        sequences = generate_all_sequences(rng, total_per_scenario)
        print(f"      {len(sequences):,} sequences in {time.time()-t0:.1f}s")

        n         = len(sequences)
        train_end = int(n * 0.70)
        val_end   = int(n * 0.85)
        seq_tr = sequences[:train_end]
        seq_va = sequences[train_end:val_end]
        seq_te = sequences[val_end:]

        X_tr, yc_tr, yn_tr = build_dataset(seq_tr, SEQUENCE_LENGTH)
        X_va, yc_va, yn_va = build_dataset(seq_va, SEQUENCE_LENGTH)
        X_te, yc_te, yn_te = build_dataset(seq_te, SEQUENCE_LENGTH)

    print(f"\n[2/4] Chronological split (no leakage)")
    print(f"      Train: {len(X_tr):,} | Val: {len(X_va):,} | Test: {len(X_te):,} windows")
    print(f"      Each window flattened: ({SEQUENCE_LENGTH} x {NUM_FEATURES}) = {SEQUENCE_LENGTH*NUM_FEATURES} features")

    # --- Fit ------------------------------------------------------------
    print(f"\n[3/4] Fitting XGBoost (n_estimators={n_estimators}, "
          f"max_depth={max_depth}, early_stopping=20) ...")
    clf = XGBoostForecaster(n_estimators=n_estimators, max_depth=max_depth)
    t0 = time.time()
    clf.fit(X_tr, yc_tr, yn_tr, X_val=X_va, yc_val=yc_va, yn_val=yn_va)
    print(f"      Fitted in {time.time()-t0:.1f}s")

    # --- Evaluate --------------------------------------------------------
    print(f"\n[4/4] Evaluation on frozen test set ...")
    print("-" * 65)
    print("  XGB TEST RESULTS (frozen chronological hold-out)")
    print("-" * 65)
    metrics = clf.score(X_te, yc_te, yn_te)
    print("-" * 65)
    print(f"  Current-State Accuracy : {metrics['current_accuracy']:.4f}  ({metrics['current_accuracy']*100:.2f}%)")
    print(f"  Next-State Accuracy    : {metrics['next_accuracy']:.4f}  ({metrics['next_accuracy']*100:.2f}%)")
    print(f"  Current F1-Weighted    : {metrics['current_f1_weighted']:.4f}")
    print(f"  Next    F1-Weighted    : {metrics['next_f1_weighted']:.4f}")
    print("-" * 65)

    clf.save(XGB_PATH)
    print("\n  Training complete.\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train the NetForecast XGBoost temporal forecaster"
    )
    parser.add_argument("--trees",      type=int,   default=300,  help="Number of boosting rounds")
    parser.add_argument("--depth",      type=int,   default=6,    help="Max tree depth")
    parser.add_argument("--seed",       type=int,   default=42,   help="Random seed")
    parser.add_argument("--rows",       type=int,   default=3000, help="Rows per scenario")
    parser.add_argument("--csv",        type=str,   default=None, help="Path to CSV dataset file")
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
        n_estimators=args.trees,
        max_depth=args.depth,
        seed=args.seed,
        total_per_scenario=args.rows,
        csv_path=csv_target,
    )
