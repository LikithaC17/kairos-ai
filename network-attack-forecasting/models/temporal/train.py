"""Threatora AI / Threatora AI — Multi-Model Temporal Training Pipeline.

Supports training the baseline GRU, LSTM, and Transformer sequence forecasting models
under identical data splits, identical feature preprocessing, and identical evaluation criteria.

Usage
-----
    python models/temporal/train.py --model all [--epochs N] [--seed S] [--no-cuda]
    python models/temporal/train.py --model gru
    python models/temporal/train.py --model lstm
    python models/temporal/train.py --model transformer

Leakage Prevention & Fair Evaluation Protocol
----------------------------------------------
1. Multi-stage timeline sessions (benign -> reconnaissance -> attack -> recovery)
   are partitioned strictly chronologically across session boundaries:
     - 70% past sessions -> Training
     - 15% intermediate sessions -> Validation
     - 15% future sessions -> Frozen Test Holdout
   Zero sequence overlap across splits prevents temporal window leakage.
2. Every partition contains all four security ladder states:
   NORMAL, ELEVATED, SUSPICIOUS, ATTACK.
3. Preprocessing transformation (Log1p + StandardScaler) is fitted STRICTLY on
   training sequences and applied (without refitting) to validation and test sets.
4. Inverse-frequency class weighting is computed exclusively on training labels.
5. All models are trained with identical random seeds and evaluated on the identical
   held-out test set.
"""

from __future__ import annotations

import argparse
import json
import os
import pickle
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

# ── Ensure project root is importable ─────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulation.normal import generate_normal
from simulation.mixed_escalation import generate_mixed
from simulation.beaconing import generate_beaconing
from simulation.ddos import generate_ddos
from simulation.scanning import generate_scanning
from simulation.common import LADDER_STATES, FEATURE_COLUMNS

from models.temporal.gru import NetworkStateGRU, STATE_LABELS, NUM_FEATURES, NUM_STATES, Log1pStandardScaler
from models.temporal.lstm import NetworkStateLSTM
from models.temporal.transformer import NetworkStateTransformer

# ─────────────────────────────────────────────────────────────────────────────
# Constants & Defaults
# ─────────────────────────────────────────────────────────────────────────────
SEQUENCE_LENGTH = 20          # T: look-back window steps
CHECKPOINT_DIR  = PROJECT_ROOT / "checkpoints"
MODEL_PATH      = CHECKPOINT_DIR / "world_model_gru.pt"
MODEL_PATH_GRU  = CHECKPOINT_DIR / "world_model_gru.pt"
MODEL_PATH_LSTM = CHECKPOINT_DIR / "world_model_lstm.pt"
MODEL_PATH_TF   = CHECKPOINT_DIR / "world_model_transformer.pt"
MODEL_PATH_BASE = CHECKPOINT_DIR / "world_model.pt"
SCALER_PATH     = CHECKPOINT_DIR / "world_model_scaler.pkl"

STATE_TO_IDX = {s: i for i, s in enumerate(LADDER_STATES)}


# ─────────────────────────────────────────────────────────────────────────────
# Sequence & Window Generation
# ─────────────────────────────────────────────────────────────────────────────

def sequence_to_windows(
    sequence: list[dict],
    window_size: int = SEQUENCE_LENGTH,
) -> tuple[list[np.ndarray], list[int], list[int]]:
    """Slide a fixed window over a single sequence to produce (X, y_curr, y_next) tuples."""
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
    if not all_X:
        return (
            np.zeros((0, window_size, NUM_FEATURES), dtype=np.float32),
            np.zeros((0,), dtype=np.int64),
            np.zeros((0,), dtype=np.int64),
        )
    X  = np.stack(all_X, axis=0).astype(np.float32)
    yc = np.array(all_yc, dtype=np.int64)
    yn = np.array(all_yn, dtype=np.int64)
    return X, yc, yn


def generate_balanced_session_sequences(
    rng: np.random.Generator,
    num_sessions: int = 25,
    rows_per_session_scenario: int = 300,
) -> tuple[list[list[dict]], list[list[dict]], list[list[dict]]]:
    """Generate multi-stage chronological monitoring sessions partitioned without temporal leakage.

    Each session simulates an operational cycle containing:
    1. Normal benign baseline traffic
    2. Subtle beaconing / C2 heartbeats
    3. Lateral movement & mixed attack escalation
    4. Volumetric DDoS assault

    Partitions:
    - First 70% of chronological sessions -> Train
    - Next 15% of chronological sessions -> Validation
    - Final 15% of chronological sessions -> Test Holdout
    """
    sessions: list[list[list[dict]]] = []
    for _ in range(num_sessions):
        session_seqs = []
        session_seqs += generate_normal(rng,    rows_per_session_scenario, min_len=15, max_len=25)
        session_seqs += generate_scanning(rng,  rows_per_session_scenario, min_len=15, max_len=25)
        session_seqs += generate_beaconing(rng, rows_per_session_scenario, min_len=15, max_len=25)
        session_seqs += generate_mixed(rng,     rows_per_session_scenario, min_len=15, max_len=25)
        session_seqs += generate_ddos(rng,      rows_per_session_scenario, min_len=15, max_len=25)
        sessions.append(session_seqs)

    train_cutoff = int(num_sessions * 0.70)
    val_cutoff   = int(num_sessions * 0.85)

    seq_train = [seq for s in sessions[:train_cutoff] for seq in s]
    seq_val   = [seq for s in sessions[train_cutoff:val_cutoff] for seq in s]
    seq_test  = [seq for s in sessions[val_cutoff:] for seq in s]

    return seq_train, seq_val, seq_test


def generate_all_sequences(
    rng: np.random.Generator,
    total_per_scenario: int = 3000,
) -> list[list[dict]]:
    """Backward-compatible sequence generator returning interleaved multi-scenario sessions."""
    num_sessions = 25
    rows_per_scenario = max(40, total_per_scenario // num_sessions)
    train_seqs, val_seqs, test_seqs = generate_balanced_session_sequences(
        rng, num_sessions=num_sessions, rows_per_session_scenario=rows_per_scenario
    )
    return train_seqs + val_seqs + test_seqs


# ─────────────────────────────────────────────────────────────────────────────
# Training Utilities
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
    train_ds = TensorDataset(
        torch.tensor(X_tr,  dtype=torch.float32),
        torch.tensor(yc_tr, dtype=torch.long),
        torch.tensor(yn_tr, dtype=torch.long),
    )
    val_ds = TensorDataset(
        torch.tensor(X_va,  dtype=torch.float32),
        torch.tensor(yc_va, dtype=torch.long),
        torch.tensor(yn_va, dtype=torch.long),
    )
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True,  drop_last=False)
    val_loader   = DataLoader(val_ds,   batch_size=batch_size, shuffle=False, drop_last=False)
    return train_loader, val_loader


def evaluate_loader(
    model: nn.Module,
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

    if total == 0:
        return 0.0, 0.0, 0.0
    return (total_loss / total), (correct_curr / total), (correct_next / total)


def train_single_model(
    model_name: str,
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    test_loader: DataLoader,
    device: torch.device,
    criterion_curr: nn.NLLLoss,
    criterion_next: nn.NLLLoss,
    epochs: int = 30,
    lr: float = 1e-3,
    patience: int = 5,
    save_path: Optional[Path] = None,
    config: Optional[dict] = None,
) -> dict:
    """Train and evaluate an individual model."""
    print(f"\n[{model_name.upper()}] Commencing training...")
    total_params = sum(p.numel() for p in model.parameters())
    print(f"  Architecture: {model.__class__.__name__} | Trainable parameters: {total_params:,}")

    optimiser = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimiser, mode="min", factor=0.5, patience=2
    )

    best_val_loss = float("inf")
    best_state = None
    no_improve = 0
    start_time = time.perf_counter()

    print(f"  {'Epoch':>5}  {'TrainLoss':>10}  {'ValLoss':>9}  "
          f"{'Acc(cur)':>9}  {'Acc(nxt)':>9}  {'LR':>8}")
    print(f"  {'-'*5}  {'-'*10}  {'-'*9}  {'-'*9}  {'-'*9}  {'-'*8}")

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
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            no_improve = 0
        else:
            no_improve += 1
            if no_improve >= patience:
                print(f"  Early stopping triggered at epoch {epoch} (patience={patience})")
                break

    training_duration_s = round(time.perf_counter() - start_time, 2)

    if best_state is not None:
        model.load_state_dict(best_state)

    # Final holdout test evaluation
    test_loss, test_acc_curr, test_acc_next = evaluate_loader(
        model, test_loader, device, criterion_curr, criterion_next
    )

    print(f"  Final Test Holdout -> Loss: {test_loss:.4f} | "
          f"CurAcc: {test_acc_curr*100:.2f}% | NxtAcc: {test_acc_next*100:.2f}% | "
          f"Time: {training_duration_s}s")

    result = {
        "model_name": model.__class__.__name__,
        "model_key": model_name,
        "parameters": total_params,
        "training_time_seconds": training_duration_s,
        "test_loss": round(float(test_loss), 4),
        "test_acc_current": round(float(test_acc_curr), 4),
        "test_acc_next": round(float(test_acc_next), 4),
    }

    if save_path:
        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        checkpoint = {
            "model_type": model_name,
            "architecture": model.__class__.__name__,
            "model_state_dict": model.state_dict(),
            "config": config or {},
            "metrics": {
                "test_loss": test_loss,
                "test_acc_current": test_acc_curr,
                "test_acc_next": test_acc_next,
                "training_time_seconds": training_duration_s,
            },
            "state_labels": STATE_LABELS,
            "feature_columns": FEATURE_COLUMNS,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        torch.save(checkpoint, save_path)
        print(f"  Saved checkpoint -> {save_path}")

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Master Multi-Model Training Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def train(
    model_choice: str = "all",
    epochs: int = 25,
    seed: int = 42,
    batch_size: int = 64,
    lr: float = 1e-3,
    hidden_size: int = 128,
    num_layers: int = 2,
    dropout: float = 0.3,
    patience: int = 4,
    use_cuda: bool = True,
    num_sessions: int = 25,
    rows_per_session_scenario: int = 300,
) -> dict:
    print("=" * 70)
    print("  Threatora AI / Threatora AI — Multi-Model World Training Pipeline")
    print("=" * 70)

    # ── Reproducibility ──────────────────────────────────────────────
    rng = np.random.default_rng(seed)
    torch.manual_seed(seed)
    np.random.seed(seed)

    device = torch.device("cuda" if (use_cuda and torch.cuda.is_available()) else "cpu")
    print(f"  Target Device : {device}")
    print(f"  Random Seed   : {seed}")
    print(f"  Model Selection: {model_choice.upper()}")
    print(f"  Epochs / Pat  : {epochs} max / patience={patience}")

    # ── Partitioned Sequence Generation (No Leakage) ─────────────────
    print(f"\n[1/4] Generating balanced multi-session chronological sequences...")
    t0 = time.time()
    seq_train, seq_val, seq_test = generate_balanced_session_sequences(
        rng, num_sessions=num_sessions, rows_per_session_scenario=rows_per_session_scenario
    )
    print(f"      Sessions: {num_sessions} total (70% Train, 15% Val, 15% Test)")
    print(f"      Sequences: Train={len(seq_train)}, Val={len(seq_val)}, Test={len(seq_test)} in {time.time()-t0:.2f}s")

    X_tr, yc_tr, yn_tr = build_dataset(seq_train, SEQUENCE_LENGTH)
    X_va, yc_va, yn_va = build_dataset(seq_val,   SEQUENCE_LENGTH)
    X_te, yc_te, yn_te = build_dataset(seq_test,  SEQUENCE_LENGTH)

    print(f"      Extracted Windows:")
    print(f"        Train: {len(X_tr):,} samples | class distribution: {np.bincount(yc_tr, minlength=4)}")
    print(f"        Val  : {len(X_va):,} samples | class distribution: {np.bincount(yc_va, minlength=4)}")
    print(f"        Test : {len(X_te):,} samples | class distribution: {np.bincount(yc_te, minlength=4)}")

    # ── Fit Scaler on Training Partition Only ────────────────────────
    print(f"\n[2/4] Fitting Log1p + StandardScaler on training sequences only (Zero Leakage)...")
    scaler = Log1pStandardScaler()
    X_tr_s = scaler.fit_transform(X_tr).astype(np.float32)
    X_va_s = scaler.transform(X_va).astype(np.float32)
    X_te_s = scaler.transform(X_te).astype(np.float32)

    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    with open(SCALER_PATH, "wb") as f:
        pickle.dump(scaler, f)
    print(f"      Fitted scaler saved -> {SCALER_PATH}")

    # ── Prepare Loaders & Loss ────────────────────────────────────────
    num_classes = len(STATE_LABELS)
    w_curr = class_weights(yc_tr, num_classes).to(device)
    w_next = class_weights(yn_tr, num_classes).to(device)
    criterion_curr = nn.NLLLoss(weight=w_curr)
    criterion_next = nn.NLLLoss(weight=w_next)

    train_loader, val_loader = make_loaders(
        X_tr_s, yc_tr, yn_tr,
        X_va_s, yc_va, yn_va,
        batch_size=batch_size,
    )
    test_ds = TensorDataset(
        torch.tensor(X_te_s, dtype=torch.float32),
        torch.tensor(yc_te,  dtype=torch.long),
        torch.tensor(yn_te,  dtype=torch.long),
    )
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False)

    # ── Model Instantiations ──────────────────────────────────────────
    models_to_train: list[str]
    if model_choice == "all":
        models_to_train = ["gru", "lstm", "transformer"]
    elif model_choice in ["gru", "lstm", "transformer"]:
        models_to_train = [model_choice]
    else:
        raise ValueError(f"Unknown model choice: {model_choice}. Choose from gru, lstm, transformer, all.")

    results_summary = {}

    print(f"\n[3/4] Training selected models on the identical chronological partition...")

    for m_key in models_to_train:
        if m_key == "gru":
            model = NetworkStateGRU(
                input_size=NUM_FEATURES,
                hidden_size=hidden_size,
                num_layers=num_layers,
                num_classes=num_classes,
                dropout=dropout,
            ).to(device)
            cfg = {
                "input_size": NUM_FEATURES,
                "hidden_size": hidden_size,
                "num_layers": num_layers,
                "num_classes": num_classes,
                "dropout": dropout,
            }
            save_p = MODEL_PATH_GRU
        elif m_key == "lstm":
            model = NetworkStateLSTM(
                input_size=NUM_FEATURES,
                hidden_size=hidden_size,
                num_layers=num_layers,
                num_classes=num_classes,
                dropout=dropout,
            ).to(device)
            cfg = {
                "input_size": NUM_FEATURES,
                "hidden_size": hidden_size,
                "num_layers": num_layers,
                "num_classes": num_classes,
                "dropout": dropout,
            }
            save_p = MODEL_PATH_LSTM
        elif m_key == "transformer":
            model = NetworkStateTransformer(
                input_size=NUM_FEATURES,
                d_model=64,
                nhead=4,
                num_layers=2,
                dim_feedforward=128,
                num_classes=num_classes,
                dropout=0.2,
            ).to(device)
            cfg = {
                "input_size": NUM_FEATURES,
                "d_model": 64,
                "nhead": 4,
                "num_layers": 2,
                "dim_feedforward": 128,
                "num_classes": num_classes,
                "dropout": 0.2,
            }
            save_p = MODEL_PATH_TF

        m_res = train_single_model(
            model_name=m_key,
            model=model,
            train_loader=train_loader,
            val_loader=val_loader,
            test_loader=test_loader,
            device=device,
            criterion_curr=criterion_curr,
            criterion_next=criterion_next,
            epochs=epochs,
            lr=lr,
            patience=patience,
            save_path=save_p,
            config=cfg,
        )
        results_summary[m_key] = m_res

        # For baseline GRU, also mirror to world_model.pt
        if m_key == "gru":
            torch.save(torch.load(save_p, map_location="cpu"), MODEL_PATH_BASE)

    # ── Summary of Training Runs ──────────────────────────────────────
    print(f"\n[4/4] Multi-Model Training Run Complete")
    print("-" * 70)
    print(f"  {'Model':<12} {'Params':>10} {'Cur Acc':>10} {'Next Acc':>10} {'Loss':>8} {'Time (s)':>10}")
    print(f"  {'-'*12} {'-'*10} {'-'*10} {'-'*10} {'-'*8} {'-'*10}")
    for m_key, res in results_summary.items():
        print(f"  {m_key.upper():<12} {res['parameters']:>10,} "
              f"{res['test_acc_current']*100:>9.2f}% "
              f"{res['test_acc_next']*100:>9.2f}% "
              f"{res['test_loss']:>8.4f} "
              f"{res['training_time_seconds']:>9.2f}s")
    print("-" * 70)

    # Save training metadata
    meta_path = CHECKPOINT_DIR / "training_metadata.json"
    with open(meta_path, "w") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "seed": seed,
            "train_samples": len(X_tr),
            "val_samples": len(X_va),
            "test_samples": len(X_te),
            "models_trained": results_summary,
        }, f, indent=2)
    print(f"  Metadata saved -> {meta_path}\n")

    return results_summary


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train the Threatora AI temporal world models")
    parser.add_argument("--model",    type=str,   default="all", choices=["gru", "lstm", "transformer", "all"], help="Architecture to train")
    parser.add_argument("--epochs",   type=int,   default=25,    help="Maximum training epochs")
    parser.add_argument("--seed",     type=int,   default=42,    help="Random seed")
    parser.add_argument("--no-cuda",  action="store_true",       help="Disable GPU even if available")
    parser.add_argument("--sessions", type=int,   default=25,    help="Number of chronological simulation sessions")
    parser.add_argument("--rows-per-scenario", type=int, default=300, help="Rows per scenario per session")
    args = parser.parse_args()

    train(
        model_choice=args.model,
        epochs=args.epochs,
        seed=args.seed,
        use_cuda=not args.no_cuda,
        num_sessions=args.sessions,
        rows_per_session_scenario=args.rows_per_scenario,
    )
