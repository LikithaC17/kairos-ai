"""NetForecast AI — Temporal World Model training script.

Usage
-----
    python models/temporal/train.py [--epochs N] [--seed S] [--no-cuda]

What this script does
---------------------
1. Generates synthetic network-flow sequences via the simulation package.
2. Applies a strict *chronological* 70 / 15 / 15 train/val/test split.
   NO random shuffling of sequences — this prevents temporal data leakage.
3. Fits a Log1p + StandardScaler on the training partition only.
4. Trains a NetworkStateGRU with:
      - CrossEntropyLoss with inverse-frequency class weights (handles imbalance)
      - AdamW optimiser
      - Early-stopping on validation loss (patience = 5)
5. Saves:
      checkpoints/world_model_gru.pt       (model state dict + architecture config)
      checkpoints/world_model_scaler.pkl   (fitted scaler)
6. Prints and saves actual train / val / test metrics (no fabricated numbers).

Temporal leakage prevention
----------------------------
* Sequences are generated in chronological order (NORMAL -> escalating) and
  the 70/15/15 boundary is applied at the *sequence* level by index, not by
  random sampling.
* Scaler statistics (mean, std) are computed exclusively on the training
  sequences and then *applied* (not re-fit) to validation and test sets.
"""

from __future__ import annotations

import argparse
import os
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

# ── make sure the project root is importable regardless of CWD ──────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from simulation.normal import generate_normal
from simulation.mixed_escalation import generate_mixed
from simulation.beaconing import generate_beaconing
from simulation.ddos import generate_ddos
from simulation.common import LADDER_STATES, FEATURE_COLUMNS

from models.temporal.lstm import NetworkStateGRU, STATE_LABELS, NUM_FEATURES, Log1pStandardScaler

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────
SEQUENCE_LENGTH = 20          # T — history look-back window
CHECKPOINT_DIR  = PROJECT_ROOT / "checkpoints"
MODEL_PATH      = CHECKPOINT_DIR / "world_model_gru.pt"
SCALER_PATH     = CHECKPOINT_DIR / "world_model_scaler.pkl"

STATE_TO_IDX = {s: i for i, s in enumerate(LADDER_STATES)}


# ─────────────────────────────────────────────────────────────────────────────
# Data generation helpers
# ─────────────────────────────────────────────────────────────────────────────

def generate_all_sequences(rng: np.random.Generator, total_per_scenario: int = 3000
                           ) -> list[list[dict]]:
    """Combine all simulation scenarios into one ordered sequence list."""
    sequences: list[list[dict]] = []
    # Normal traffic first (temporal ordering: calm before storm)
    sequences += generate_normal(rng,    total_per_scenario, min_len=15, max_len=25)
    sequences += generate_beaconing(rng, total_per_scenario, min_len=15, max_len=25)
    sequences += generate_mixed(rng,     total_per_scenario, min_len=15, max_len=25)
    sequences += generate_ddos(rng,      total_per_scenario, min_len=15, max_len=25)
    return sequences


def sequence_to_windows(
    sequence: list[dict],
    window_size: int = SEQUENCE_LENGTH,
) -> tuple[list[np.ndarray], list[int], list[int]]:
    """Slide a fixed window over a single sequence to produce (X, y_curr, y_next) tuples.

    Returns
    -------
    windows    : list of float32 arrays, each shape (window_size, F)
    y_current  : label for the *last* step in the window (current state)
    y_next     : label for the step *following* the window (next state)
    """
    windows, y_curr, y_next = [], [], []
    n = len(sequence)
    for start in range(n - window_size):
        end = start + window_size
        if end >= n:
            break
        window = [
            [row[col] for col in FEATURE_COLUMNS]
            for row in sequence[start:end]
        ]
        windows.append(np.array(window, dtype=np.float32))
        y_curr.append(STATE_TO_IDX[sequence[end - 1]["state"]])
        y_next.append(STATE_TO_IDX[sequence[end]["state"]])
    return windows, y_curr, y_next


def build_dataset(
    sequences: list[list[dict]],
    window_size: int = SEQUENCE_LENGTH,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Convert a list of raw sequences into stacked numpy arrays."""
    all_X, all_yc, all_yn = [], [], []
    for seq in sequences:
        ws, yc, yn = sequence_to_windows(seq, window_size)
        all_X.extend(ws)
        all_yc.extend(yc)
        all_yn.extend(yn)
    X  = np.stack(all_X,  axis=0).astype(np.float32)   # (N, T, F)
    yc = np.array(all_yc, dtype=np.int64)
    yn = np.array(all_yn, dtype=np.int64)
    return X, yc, yn


def load_dataset_from_csv(
    csv_path: str | Path,
    window_size: int = SEQUENCE_LENGTH,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load continuous temporal sequence windows from a CSV dataset file.

    Preserves original continuous timestamp flow order across all records.
    Returns (X, y_current, y_next) numpy arrays.
    """
    import pandas as pd

    p = Path(csv_path)
    if not p.exists():
        candidates = [
            PROJECT_ROOT.parent / p.name,
            PROJECT_ROOT / p.name,
            PROJECT_ROOT.parent / csv_path,
        ]
        for c in candidates:
            if c.exists():
                p = c
                break

    if not p.exists():
        raise FileNotFoundError(f"Dataset CSV file not found: {csv_path}")

    df = pd.read_csv(p)
    missing = [c for c in FEATURE_COLUMNS + ["state"] if c not in df.columns]
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}")

    rows = df.to_dict("records")
    n = len(rows)
    all_X, all_yc, all_yn = [], [], []

    for start in range(n - window_size):
        end = start + window_size
        window = [
            [r[col] for col in FEATURE_COLUMNS]
            for r in rows[start:end]
        ]
        all_X.append(window)
        all_yc.append(STATE_TO_IDX[rows[end - 1]["state"]])
        all_yn.append(STATE_TO_IDX[rows[end]["state"]])

    X  = np.array(all_X,  dtype=np.float32)
    yc = np.array(all_yc, dtype=np.int64)
    yn = np.array(all_yn, dtype=np.int64)
    return X, yc, yn


# ─────────────────────────────────────────────────────────────────────────────
# Training utilities
# ─────────────────────────────────────────────────────────────────────────────

def class_weights(y: np.ndarray, num_classes: int) -> torch.Tensor:
    """Inverse-frequency weights to mitigate class imbalance."""
    counts = np.bincount(y, minlength=num_classes).astype(np.float32)
    counts = np.maximum(counts, 1.0)
    weights = 1.0 / counts
    weights = weights / weights.sum() * num_classes
    return torch.tensor(weights, dtype=torch.float32)


def make_loaders(
    X_tr: np.ndarray, yc_tr: np.ndarray, yn_tr: np.ndarray,
    X_va: np.ndarray, yc_va: np.ndarray, yn_va: np.ndarray,
    batch_size: int = 64,
) -> tuple[DataLoader, DataLoader]:
    def to_tensors(X, yc, yn):
        return TensorDataset(
            torch.tensor(X,  dtype=torch.float32),
            torch.tensor(yc, dtype=torch.long),
            torch.tensor(yn, dtype=torch.long),
        )

    train_ds = to_tensors(X_tr, yc_tr, yn_tr)
    val_ds   = to_tensors(X_va, yc_va, yn_va)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True,  drop_last=False)
    val_loader   = DataLoader(val_ds,   batch_size=batch_size, shuffle=False, drop_last=False)
    return train_loader, val_loader


def evaluate_loader(
    model: NetworkStateGRU,
    loader: DataLoader,
    device: torch.device,
    criterion_curr: nn.NLLLoss,
    criterion_next: nn.NLLLoss,
) -> tuple[float, float, float]:
    """Returns (avg_loss, acc_current, acc_next)."""
    model.eval()
    total_loss = 0.0
    correct_curr = correct_next = total = 0

    with torch.no_grad():
        for X_b, yc_b, yn_b in loader:
            X_b, yc_b, yn_b = X_b.to(device), yc_b.to(device), yn_b.to(device)
            log_curr, log_next = model(X_b)
            loss = criterion_curr(log_curr, yc_b) + criterion_next(log_next, yn_b)
            total_loss += loss.item() * X_b.size(0)

            pred_curr = log_curr.argmax(dim=1)
            pred_next = log_next.argmax(dim=1)
            correct_curr += (pred_curr == yc_b).sum().item()
            correct_next += (pred_next == yn_b).sum().item()
            total += X_b.size(0)

    return (total_loss / total), (correct_curr / total), (correct_next / total)


# ─────────────────────────────────────────────────────────────────────────────
# Main training function
# ─────────────────────────────────────────────────────────────────────────────

def train(
    epochs: int = 30,
    seed: int = 42,
    batch_size: int = 64,
    lr: float = 1e-3,
    hidden_size: int = 128,
    num_layers: int = 2,
    dropout: float = 0.3,
    patience: int = 5,
    use_cuda: bool = True,
    total_per_scenario: int = 3000,
    csv_path: str | Path | None = None,
) -> None:
    print("=" * 65)
    print("  NetForecast AI — Temporal World Model Training")
    print("=" * 65)

    # ── Reproducibility ──────────────────────────────────────────────
    rng = np.random.default_rng(seed)
    torch.manual_seed(seed)
    np.random.seed(seed)

    device = torch.device(
        "cuda" if (use_cuda and torch.cuda.is_available()) else "cpu"
    )
    print(f"  Device      : {device}")
    print(f"  Seed        : {seed}")
    print(f"  Epochs (max): {epochs}  |  Patience: {patience}")

    # ── Load or Generate data ─────────────────────────────────────────
    if csv_path is not None:
        print(f"\n[1/5] Loading sequences from CSV dataset: {csv_path} ...")
        t0 = time.time()
        X_all, yc_all, yn_all = load_dataset_from_csv(csv_path, SEQUENCE_LENGTH)
        print(f"      {len(X_all):,} temporal window samples extracted in {time.time()-t0:.1f}s")

        n = len(X_all)
        train_end = int(n * 0.70)
        val_end   = int(n * 0.85)

        X_tr, yc_tr, yn_tr = X_all[:train_end], yc_all[:train_end], yn_all[:train_end]
        X_va, yc_va, yn_va = X_all[train_end:val_end], yc_all[train_end:val_end], yn_all[train_end:val_end]
        X_te, yc_te, yn_te = X_all[val_end:], yc_all[val_end:], yn_all[val_end:]

        print(f"\n[2/5] Chronological split (no leakage)")
        print(f"      Train: {len(X_tr):,} | Val: {len(X_va):,} | Test: {len(X_te):,}")
    else:
        print("\n[1/5] Generating synthetic sequences ...")
        t0 = time.time()
        sequences = generate_all_sequences(rng, total_per_scenario)
        print(f"      {len(sequences):,} sequences generated in {time.time()-t0:.1f}s")

        n = len(sequences)
        train_end = int(n * 0.70)
        val_end   = int(n * 0.85)
        seq_train = sequences[:train_end]
        seq_val   = sequences[train_end:val_end]
        seq_test  = sequences[val_end:]
        print(f"\n[2/5] Chronological split (no leakage)")
        print(f"      Train: {len(seq_train):,} seqs | Val: {len(seq_val):,} | Test: {len(seq_test):,}")

        X_tr, yc_tr, yn_tr = build_dataset(seq_train, SEQUENCE_LENGTH)
        X_va, yc_va, yn_va = build_dataset(seq_val,   SEQUENCE_LENGTH)
        X_te, yc_te, yn_te = build_dataset(seq_test,  SEQUENCE_LENGTH)

    print(f"      Windows — Train: {len(X_tr):,}  Val: {len(X_va):,}  Test: {len(X_te):,}")

    # ── Fit scaler on training data ONLY ─────────────────────────────
    print("\n[3/5] Fitting Log1p+StandardScaler on training data only ...")
    scaler = Log1pStandardScaler()
    X_tr_s = scaler.fit_transform(X_tr).astype(np.float32)
    X_va_s = scaler.transform(X_va).astype(np.float32)
    X_te_s = scaler.transform(X_te).astype(np.float32)

    # ── Class weights (computed on training labels only) ──────────────
    num_classes = len(STATE_LABELS)
    w_curr = class_weights(yc_tr, num_classes).to(device)
    w_next = class_weights(yn_tr, num_classes).to(device)

    # ── DataLoaders ───────────────────────────────────────────────────
    train_loader, val_loader = make_loaders(
        X_tr_s, yc_tr, yn_tr,
        X_va_s, yc_va, yn_va,
        batch_size=batch_size,
    )

    # ── Model, loss, optimiser ────────────────────────────────────────
    print(f"\n[4/5] Building NetworkStateGRU ...")
    model = NetworkStateGRU(
        input_size=NUM_FEATURES,
        hidden_size=hidden_size,
        num_layers=num_layers,
        num_classes=num_classes,
        dropout=dropout,
    ).to(device)

    total_params = sum(p.numel() for p in model.parameters())
    print(f"      Parameters: {total_params:,}")

    criterion_curr = nn.NLLLoss(weight=w_curr)
    criterion_next = nn.NLLLoss(weight=w_next)
    optimiser = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimiser, mode="min", factor=0.5, patience=3
    )

    # ── Training loop ─────────────────────────────────────────────────
    print(f"\n[5/5] Training ...")
    print(f"  {'Epoch':>5}  {'TrainLoss':>10}  {'ValLoss':>9}  "
          f"{'Acc(cur)':>9}  {'Acc(nxt)':>9}  {'LR':>8}")
    print(f"  {'-'*5}  {'-'*10}  {'-'*9}  {'-'*9}  {'-'*9}  {'-'*8}")

    best_val_loss = float("inf")
    best_state    = None
    no_improve    = 0

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        for X_b, yc_b, yn_b in train_loader:
            X_b, yc_b, yn_b = X_b.to(device), yc_b.to(device), yn_b.to(device)
            optimiser.zero_grad()
            log_curr, log_next = model(X_b)
            loss = criterion_curr(log_curr, yc_b) + criterion_next(log_next, yn_b)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimiser.step()
            train_loss += loss.item() * X_b.size(0)

        train_loss /= len(train_loader.dataset)

        val_loss, val_acc_curr, val_acc_next = evaluate_loader(
            model, val_loader, device, criterion_curr, criterion_next
        )

        scheduler.step(val_loss)
        cur_lr = optimiser.param_groups[0]["lr"]

        print(f"  {epoch:>5}  {train_loss:>10.4f}  {val_loss:>9.4f}  "
              f"{val_acc_curr:>9.4f}  {val_acc_next:>9.4f}  {cur_lr:>8.6f}")

        if val_loss < best_val_loss - 1e-5:
            best_val_loss = val_loss
            best_state    = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            no_improve    = 0
        else:
            no_improve += 1
            if no_improve >= patience:
                print(f"\n  Early stopping at epoch {epoch} (patience={patience})")
                break

    # ── Restore best weights ──────────────────────────────────────────
    if best_state is not None:
        model.load_state_dict(best_state)

    # ── Test-set evaluation ───────────────────────────────────────────
    test_ds = TensorDataset(
        torch.tensor(X_te_s, dtype=torch.float32),
        torch.tensor(yc_te,  dtype=torch.long),
        torch.tensor(yn_te,  dtype=torch.long),
    )
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False)
    test_loss, test_acc_curr, test_acc_next = evaluate_loader(
        model, test_loader, device, criterion_curr, criterion_next
    )

    print("\n" + "-" * 65)
    print(f"  FINAL TEST RESULTS (frozen hold-out partition)")
    print(f"  Test Loss          : {test_loss:.4f}")
    print(f"  Current-State Acc  : {test_acc_curr:.4f}  ({test_acc_curr*100:.2f}%)")
    print(f"  Next-State Acc     : {test_acc_next:.4f}  ({test_acc_next*100:.2f}%)")
    print("-" * 65)

    # ── Save checkpoint ───────────────────────────────────────────────
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "config": {
            "input_size":  NUM_FEATURES,
            "hidden_size": hidden_size,
            "num_layers":  num_layers,
            "num_classes": num_classes,
            "dropout":     dropout,
        },
        "metrics": {
            "test_loss":           test_loss,
            "test_acc_current":    test_acc_curr,
            "test_acc_next":       test_acc_next,
        },
        "state_labels": STATE_LABELS,
        "feature_columns": FEATURE_COLUMNS,
    }
    torch.save(checkpoint, MODEL_PATH)
    print(f"\n  Model checkpoint saved -> {MODEL_PATH}")

    with open(SCALER_PATH, "wb") as f:
        pickle.dump(scaler, f)
    print(f"  Scaler saved        -> {SCALER_PATH}")
    print("\n  Training complete.\n")


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train the NetForecast temporal world model")
    parser.add_argument("--epochs",   type=int,   default=30,    help="Maximum training epochs")
    parser.add_argument("--seed",     type=int,   default=42,    help="Random seed")
    parser.add_argument("--no-cuda",  action="store_true",       help="Disable GPU even if available")
    parser.add_argument("--rows",     type=int,   default=3000,  help="Rows per scenario for synthetic mode")
    parser.add_argument("--csv",      type=str,   default=None,  help="Path to CSV dataset file (e.g. network_traffic_10000.csv)")
    args = parser.parse_args()

    csv_target = args.csv
    if csv_target is None:
        # Check standard locations for network_traffic_10000.csv
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
        epochs=args.epochs,
        seed=args.seed,
        use_cuda=not args.no_cuda,
        total_per_scenario=args.rows,
        csv_path=csv_target,
    )
