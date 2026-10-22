"""Threatora AI / Threatora AI — Multi-Model World Model Comparative Evaluation.

Usage
-----
    python models/temporal/evaluate.py [--model {gru,lstm,transformer,all}] [--no-cuda]

What this script does
---------------------
1. Loads the saved model checkpoints (GRU, LSTM, Transformer) and the fitted scaler.
2. Regenerates the exact frozen chronological holdout test partition using seed=42.
3. For each model, computes:
   - Accuracy (Current State & Next-State Forecaster)
   - Macro-F1 & Weighted-F1
   - Macro AUROC (One-vs-Rest multi-class)
   - Per-Class Metrics (Precision, Recall, F1 for all 4 states)
   - Real-world single-sample and batch inference latency (ms over 100 iterations)
   - Trainable parameter counts and on-disk checkpoint sizes
4. Generates and saves confusion matrix figures:
   - checkpoints/confusion_matrix_gru_current.png
   - checkpoints/confusion_matrix_gru_next.png
   - checkpoints/confusion_matrix_lstm_current.png
   - checkpoints/confusion_matrix_lstm_next.png
   - checkpoints/confusion_matrix_transformer_current.png
   - checkpoints/confusion_matrix_transformer_next.png
   - checkpoints/confusion_matrix_current.png (GRU baseline alias)
   - checkpoints/confusion_matrix_next.png (GRU baseline alias)
5. Exports:
   - checkpoints/benchmark_comparison.json (consolidated side-by-side benchmark)
   - checkpoints/eval_report.json (backward-compatible evaluation report)

All values are empirically measured on the held-out test split — zero fabrication.
"""

from __future__ import annotations

import argparse
import json
import os
import pickle
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

# ── Ensure project root is importable ─────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulation.common import LADDER_STATES, FEATURE_COLUMNS
from models.temporal.gru import NetworkStateGRU, STATE_LABELS, NUM_FEATURES, NUM_STATES, Log1pStandardScaler
from models.temporal.lstm import NetworkStateLSTM
from models.temporal.transformer import NetworkStateTransformer
from models.temporal.train import (
    generate_balanced_session_sequences,
    build_dataset,
    generate_all_sequences,
    SEQUENCE_LENGTH,
    CHECKPOINT_DIR,
    MODEL_PATH,
    MODEL_PATH_GRU,
    MODEL_PATH_LSTM,
    MODEL_PATH_TF,
    MODEL_PATH_BASE,
    SCALER_PATH,
)

# Optional scikit-learn & matplotlib
try:
    from sklearn.metrics import (
        classification_report,
        confusion_matrix,
        roc_auc_score,
        f1_score,
        accuracy_score,
        precision_score,
        recall_score,
    )
    from sklearn.preprocessing import label_binarize
    _SKLEARN = True
except ImportError:
    _SKLEARN = False

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _MPL = True
except ImportError:
    _MPL = False

BENCHMARK_REPORT_PATH = CHECKPOINT_DIR / "benchmark_comparison.json"
EVAL_REPORT_PATH      = CHECKPOINT_DIR / "eval_report.json"
CM_CURR_PATH          = CHECKPOINT_DIR / "confusion_matrix_current.png"
CM_NEXT_PATH          = CHECKPOINT_DIR / "confusion_matrix_next.png"


# ─────────────────────────────────────────────────────────────────────────────
# Model Loading Helpers
# ─────────────────────────────────────────────────────────────────────────────

def load_scaler() -> Log1pStandardScaler:
    if not SCALER_PATH.exists():
        raise FileNotFoundError(
            f"Scaler checkpoint not found: {SCALER_PATH}\n"
            "Run 'python models/temporal/train.py' first."
        )
    with open(SCALER_PATH, "rb") as f:
        return pickle.load(f)


def load_model_by_type(
    model_type: str,
    device: torch.device,
) -> tuple[nn.Module, dict]:
    """Loads a specific model checkpoint (gru, lstm, transformer)."""
    m_type = model_type.lower()
    if m_type == "gru":
        ckpt_path = MODEL_PATH_GRU if MODEL_PATH_GRU.exists() else MODEL_PATH_BASE
    elif m_type == "lstm":
        ckpt_path = MODEL_PATH_LSTM
    elif m_type in ["transformer", "tf"]:
        ckpt_path = MODEL_PATH_TF
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    if not ckpt_path.exists():
        raise FileNotFoundError(
            f"Checkpoint for {model_type} not found at {ckpt_path}.\n"
            f"Run 'python models/temporal/train.py --model {m_type}' first."
        )

    ckpt = torch.load(ckpt_path, map_location=device)
    cfg  = ckpt.get("config", {})

    if m_type == "gru":
        model = NetworkStateGRU(
            input_size=cfg.get("input_size", NUM_FEATURES),
            hidden_size=cfg.get("hidden_size", 128),
            num_layers=cfg.get("num_layers", 2),
            num_classes=cfg.get("num_classes", NUM_STATES),
            dropout=cfg.get("dropout", 0.3),
        )
    elif m_type == "lstm":
        model = NetworkStateLSTM(
            input_size=cfg.get("input_size", NUM_FEATURES),
            hidden_size=cfg.get("hidden_size", 128),
            num_layers=cfg.get("num_layers", 2),
            num_classes=cfg.get("num_classes", NUM_STATES),
            dropout=cfg.get("dropout", 0.3),
        )
    elif m_type in ["transformer", "tf"]:
        model = NetworkStateTransformer(
            input_size=cfg.get("input_size", NUM_FEATURES),
            d_model=cfg.get("d_model", 64),
            nhead=cfg.get("nhead", 4),
            num_layers=cfg.get("num_layers", 2),
            dim_feedforward=cfg.get("dim_feedforward", 128),
            num_classes=cfg.get("num_classes", NUM_STATES),
            dropout=cfg.get("dropout", 0.2),
        )

    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device)
    model.eval()
    return model, ckpt


# Backward-compatible load_checkpoint for GRU
def load_checkpoint(device: torch.device) -> tuple[NetworkStateGRU, dict]:
    return load_model_by_type("gru", device)  # type: ignore


# ─────────────────────────────────────────────────────────────────────────────
# Inference & Latency Profiling
# ─────────────────────────────────────────────────────────────────────────────

def get_predictions(
    model: nn.Module,
    X: np.ndarray,
    device: torch.device,
    batch_size: int = 128,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return pred_curr, prob_curr, pred_next, prob_next arrays."""
    ds     = TensorDataset(torch.tensor(X, dtype=torch.float32))
    loader = DataLoader(ds, batch_size=batch_size, shuffle=False)

    all_pred_curr, all_prob_curr = [], []
    all_pred_next, all_prob_next = [], []

    model.eval()
    with torch.no_grad():
        for (X_b,) in loader:
            X_b = X_b.to(device)
            lc, ln = model(X_b)
            pc = torch.exp(lc).cpu().numpy()
            pn = torch.exp(ln).cpu().numpy()
            all_pred_curr.append(pc.argmax(axis=1))
            all_prob_curr.append(pc)
            all_pred_next.append(pn.argmax(axis=1))
            all_prob_next.append(pn)

    return (
        np.concatenate(all_pred_curr),
        np.concatenate(all_prob_curr),
        np.concatenate(all_pred_next),
        np.concatenate(all_prob_next),
    )


def measure_inference_latency(
    model: nn.Module,
    sample_window: np.ndarray,
    device: torch.device,
    warmup: int = 20,
    iterations: int = 100,
) -> dict:
    """Accurately measure average single-sample and batch inference latency in milliseconds."""
    x_single = torch.tensor(sample_window[np.newaxis, :, :], dtype=torch.float32).to(device)
    x_batch  = torch.tensor(np.repeat(sample_window[np.newaxis, :, :], 32, axis=0), dtype=torch.float32).to(device)

    model.eval()
    with torch.no_grad():
        # Warmup
        for _ in range(warmup):
            _ = model(x_single)

        # Single-sample latency
        t0 = time.perf_counter()
        for _ in range(iterations):
            _ = model(x_single)
        single_ms = ((time.perf_counter() - t0) / iterations) * 1000.0

        # Batch (32) latency
        t0 = time.perf_counter()
        for _ in range(iterations):
            _ = model(x_batch)
        batch_ms = ((time.perf_counter() - t0) / iterations) * 1000.0

    return {
        "single_sample_ms": round(float(single_ms), 3),
        "batch_32_ms": round(float(batch_ms), 3),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Visualisation & Metrics Formatting
# ─────────────────────────────────────────────────────────────────────────────

def plot_confusion_matrix(
    cm: np.ndarray,
    labels: list[str],
    title: str,
    save_path: Path,
) -> None:
    if not _MPL:
        return
    cm_norm = cm.astype(float) / (cm.sum(axis=1, keepdims=True) + 1e-8)

    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm_norm, interpolation="nearest", cmap="Blues", vmin=0, vmax=1)
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=9)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("Predicted Label", fontsize=10)
    ax.set_ylabel("True Label", fontsize=10)
    ax.set_title(title, fontsize=11, pad=12)

    for i in range(len(labels)):
        for j in range(len(labels)):
            val = cm_norm[i, j]
            raw = cm[i, j]
            color = "white" if val > 0.55 else "black"
            ax.text(j, i, f"{val:.2f}\n({raw})", ha="center", va="center", fontsize=8, color=color)

    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)


def compute_head_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    probs: np.ndarray,
    labels: list[str],
) -> dict:
    acc  = accuracy_score(y_true, y_pred)
    f1m  = f1_score(y_true, y_pred, average="macro", zero_division=0)
    f1w  = f1_score(y_true, y_pred, average="weighted", zero_division=0)
    prec = precision_score(y_true, y_pred, average="macro", zero_division=0)
    rec  = recall_score(y_true, y_pred, average="macro", zero_division=0)

    # Macro AUROC
    unique = np.unique(y_true)
    if len(unique) >= 2:
        try:
            y_bin = label_binarize(y_true, classes=list(range(len(labels))))
            auroc = roc_auc_score(y_bin, probs, multi_class="ovr", average="macro")
            if np.isnan(auroc):
                auroc = None
        except Exception:
            auroc = None
    else:
        auroc = None

    # Per-class metrics
    per_class = {}
    cr = classification_report(
        y_true, y_pred,
        labels=list(range(len(labels))),
        target_names=labels,
        output_dict=True,
        zero_division=0,
    )
    for lbl in labels:
        if lbl in cr:
            per_class[lbl] = {
                "precision": round(cr[lbl]["precision"], 4),
                "recall": round(cr[lbl]["recall"], 4),
                "f1": round(cr[lbl]["f1-score"], 4),
                "support": int(cr[lbl]["support"]),
            }

    return {
        "accuracy": round(float(acc), 4),
        "f1_macro": round(float(f1m), 4),
        "f1_weighted": round(float(f1w), 4),
        "precision_macro": round(float(prec), 4),
        "recall_macro": round(float(rec), 4),
        "auroc_macro": round(float(auroc), 4) if auroc is not None else None,
        "per_class": per_class,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Master Evaluation Function
# ─────────────────────────────────────────────────────────────────────────────

def evaluate(
    model_choice: str = "all",
    use_cuda: bool = True,
    seed: int = 42,
    num_sessions: int = 25,
    rows_per_session_scenario: int = 300,
) -> dict:
    print("=" * 70)
    print("  Threatora AI / Threatora AI — Multi-Model World Model Evaluation")
    print("=" * 70)

    device = torch.device("cuda" if (use_cuda and torch.cuda.is_available()) else "cpu")
    print(f"  Evaluation Device : {device}")
    print(f"  Random Seed       : {seed}")
    print(f"  Target Models     : {model_choice.upper()}")

    scaler = load_scaler()

    # ── Regenerate the exact held-out test partition ──────────────────
    print(f"\n[1/3] Reconstructing frozen chronological holdout test partition...")
    rng = np.random.default_rng(seed)
    seq_train, seq_val, seq_test = generate_balanced_session_sequences(
        rng, num_sessions=num_sessions, rows_per_session_scenario=rows_per_session_scenario
    )
    X_te, yc_te, yn_te = build_dataset(seq_test, SEQUENCE_LENGTH)
    X_te_s = scaler.transform(X_te).astype(np.float32)

    print(f"      Holdout Test Windows: {len(X_te):,} samples")
    print(f"      Class Distribution  : {np.bincount(yc_te, minlength=4)} -> {STATE_LABELS}")

    target_models = ["gru", "lstm", "transformer"] if model_choice == "all" else [model_choice.lower()]
    benchmark_report: Dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "test_samples": len(X_te),
        "state_labels": STATE_LABELS,
        "models": {},
    }

    print(f"\n[2/3] Evaluating models on identical frozen test holdout...")

    for m_type in target_models:
        try:
            model, ckpt = load_model_by_type(m_type, device)
        except FileNotFoundError as e:
            print(f"  [SKIP] {m_type.upper()}: Checkpoint not found ({e})")
            continue

        ckpt_path = MODEL_PATH_GRU if m_type == "gru" else (MODEL_PATH_LSTM if m_type == "lstm" else MODEL_PATH_TF)
        file_size_kb = round(ckpt_path.stat().st_size / 1024.0, 1) if ckpt_path.exists() else 0.0
        total_params = sum(p.numel() for p in model.parameters())

        # Predictions
        pred_curr, prob_curr, pred_next, prob_next = get_predictions(model, X_te_s, device)

        # Latency profiling
        lat = measure_inference_latency(model, X_te_s[0], device)

        # Compute metrics
        curr_metrics = compute_head_metrics(yc_te, pred_curr, prob_curr, STATE_LABELS)
        next_metrics = compute_head_metrics(yn_te, pred_next, prob_next, STATE_LABELS)

        # Confusion matrices
        cm_curr = confusion_matrix(yc_te, pred_curr, labels=list(range(len(STATE_LABELS))))
        cm_next = confusion_matrix(yn_te, pred_next, labels=list(range(len(STATE_LABELS))))

        cm_curr_file = CHECKPOINT_DIR / f"confusion_matrix_{m_type}_current.png"
        cm_next_file = CHECKPOINT_DIR / f"confusion_matrix_{m_type}_next.png"
        plot_confusion_matrix(cm_curr, STATE_LABELS, f"{m_type.upper()} Current State — Confusion Matrix", cm_curr_file)
        plot_confusion_matrix(cm_next, STATE_LABELS, f"{m_type.upper()} Next State — Confusion Matrix", cm_next_file)

        # Mirror baseline GRU to standard paths
        if m_type == "gru":
            plot_confusion_matrix(cm_curr, STATE_LABELS, "Current Security State — Confusion Matrix", CM_CURR_PATH)
            plot_confusion_matrix(cm_next, STATE_LABELS, "Next Security State — Confusion Matrix", CM_NEXT_PATH)

        model_entry = {
            "model_name": model.__class__.__name__,
            "model_type": (
                "Recurrent Neural Network (2-Layer GRU Baseline)" if m_type == "gru"
                else ("Recurrent Neural Network (2-Layer LSTM with Cell State)" if m_type == "lstm"
                else "Temporal Transformer (Self-Attention & Positional Encoding)")
            ),
            "architecture_key": m_type,
            "parameters": total_params,
            "checkpoint_size_kb": file_size_kb,
            "single_sample_latency_ms": lat["single_sample_ms"],
            "batch_32_latency_ms": lat["batch_32_ms"],
            "current_state": curr_metrics,
            "next_state": next_metrics,
        }
        benchmark_report["models"][m_type] = model_entry

        print(f"\n  --- {m_type.upper()} ({model.__class__.__name__}) ---")
        print(f"  Params: {total_params:,} | Size: {file_size_kb} KB | Latency (1-sample): {lat['single_sample_ms']:.2f}ms")
        print(f"  Head A (Current State) -> Acc: {curr_metrics['accuracy']*100:.2f}% | Macro-F1: {curr_metrics['f1_macro']:.4f} | AUROC: {curr_metrics['auroc_macro']}")
        print(f"  Head B (Next State)    -> Acc: {next_metrics['accuracy']*100:.2f}% | Macro-F1: {next_metrics['f1_macro']:.4f} | AUROC: {next_metrics['auroc_macro']}")

    # ── Summary & Export ──────────────────────────────────────────────
    print(f"\n[3/3] Exporting benchmark comparisons and reports...")
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

    with open(BENCHMARK_REPORT_PATH, "w") as f:
        json.dump(benchmark_report, f, indent=2)
    print(f"  Benchmark comparison saved -> {BENCHMARK_REPORT_PATH}")

    # Backward-compatible eval_report.json (based on GRU baseline or first model)
    primary_key = "gru" if "gru" in benchmark_report["models"] else list(benchmark_report["models"].keys())[0]
    primary = benchmark_report["models"][primary_key]
    eval_compat = {
        "current_state": {
            "accuracy": primary["current_state"]["accuracy"],
            "f1_macro": primary["current_state"]["f1_macro"],
            "f1_weighted": primary["current_state"]["f1_weighted"],
            "auroc_macro": primary["current_state"]["auroc_macro"],
        },
        "next_state": {
            "accuracy": primary["next_state"]["accuracy"],
            "f1_macro": primary["next_state"]["f1_macro"],
            "f1_weighted": primary["next_state"]["f1_weighted"],
            "auroc_macro": primary["next_state"]["auroc_macro"],
        },
    }
    with open(EVAL_REPORT_PATH, "w") as f:
        json.dump(eval_compat, f, indent=2)
    print(f"  Backward-compatible report -> {EVAL_REPORT_PATH}")

    # Print Comparative Table
    print("\n" + "=" * 80)
    print(f"  EMPIRICAL BENCHMARK COMPARISON TABLE (Frozen Test Partition, N={len(X_te)})")
    print("=" * 80)
    print(f"  {'Model':<12} {'Params':>8} {'Size(KB)':>9} {'Cur Acc':>9} {'Nxt Acc':>9} {'Macro-F1':>10} {'AUROC':>8} {'Latency':>9}")
    print(f"  {'-'*12} {'-'*8} {'-'*9} {'-'*9} {'-'*9} {'-'*10} {'-'*8} {'-'*9}")
    for k, m in benchmark_report["models"].items():
        nxt = m["next_state"]
        cur = m["current_state"]
        auroc_str = f"{nxt['auroc_macro']:.3f}" if nxt['auroc_macro'] is not None else "N/A"
        print(f"  {k.upper():<12} {m['parameters']:>8,} {m['checkpoint_size_kb']:>9.1f} "
              f"{cur['accuracy']*100:>8.2f}% {nxt['accuracy']*100:>8.2f}% "
              f"{nxt['f1_macro']:>10.4f} {auroc_str:>8} {m['single_sample_latency_ms']:>7.2f}ms")
    print("=" * 80 + "\n")

    return benchmark_report


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Threatora AI world models")
    parser.add_argument("--model",   type=str, default="all", choices=["gru", "lstm", "transformer", "all"])
    parser.add_argument("--no-cuda", action="store_true")
    parser.add_argument("--seed",    type=int, default=42)
    args = parser.parse_args()

    evaluate(
        model_choice=args.model,
        use_cuda=not args.no_cuda,
        seed=args.seed,
    )
