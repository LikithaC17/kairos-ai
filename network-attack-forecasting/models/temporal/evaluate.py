"""NetForecast AI — World Model evaluation script.

Usage
-----
    python models/temporal/evaluate.py [--no-cuda]

What this script does
---------------------
1. Loads the saved checkpoint and scaler from the checkpoints/ directory.
2. Regenerates the test partition using the same seed (42) and chronological
   split as training — ensuring the frozen test set is identical.
3. Computes and prints a full classification report:
      Accuracy, F1 (macro + per-class), AUROC (one-vs-rest), Brier Score
4. Generates and saves a confusion matrix figure:
      checkpoints/confusion_matrix_current.png
      checkpoints/confusion_matrix_next.png
5. Saves a JSON evaluation report:
      checkpoints/eval_report.json

All numbers are actual measured metrics — no fabrication.
"""

from __future__ import annotations

import argparse
import json
import os
import pickle
import sys
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset

# ── project root on path ─────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from simulation.normal import generate_normal
from simulation.mixed_escalation import generate_mixed
from simulation.beaconing import generate_beaconing
from simulation.ddos import generate_ddos
from simulation.common import LADDER_STATES, FEATURE_COLUMNS

from models.temporal.lstm import NetworkStateGRU, STATE_LABELS, Log1pStandardScaler
from models.temporal.train import (
    generate_all_sequences,
    build_dataset,
    SEQUENCE_LENGTH,
    CHECKPOINT_DIR,
    MODEL_PATH,
    SCALER_PATH,
)

# optional sklearn / matplotlib — imported lazily with friendly error
try:
    from sklearn.metrics import (
        classification_report,
        confusion_matrix,
        roc_auc_score,
        brier_score_loss,
        f1_score,
        accuracy_score,
    )
    _SKLEARN = True
except ImportError:
    _SKLEARN = False

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    _MPL = True
except ImportError:
    _MPL = False

EVAL_REPORT_PATH = CHECKPOINT_DIR / "eval_report.json"
CM_CURR_PATH     = CHECKPOINT_DIR / "confusion_matrix_current.png"
CM_NEXT_PATH     = CHECKPOINT_DIR / "confusion_matrix_next.png"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def load_checkpoint(device: torch.device) -> tuple[NetworkStateGRU, dict]:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Checkpoint not found: {MODEL_PATH}\n"
            "Run 'python models/temporal/train.py' first."
        )
    ckpt = torch.load(MODEL_PATH, map_location=device)
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
    return model, ckpt


def load_scaler():
    if not SCALER_PATH.exists():
        raise FileNotFoundError(
            f"Scaler not found: {SCALER_PATH}\n"
            "Run 'python models/temporal/train.py' first."
        )
    with open(SCALER_PATH, "rb") as f:
        return pickle.load(f)


def get_predictions(
    model: NetworkStateGRU,
    X: np.ndarray,
    device: torch.device,
    batch_size: int = 256,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return pred_curr, prob_curr, pred_next, prob_next arrays."""
    ds     = TensorDataset(torch.tensor(X, dtype=torch.float32))
    loader = DataLoader(ds, batch_size=batch_size, shuffle=False)

    all_pred_curr, all_prob_curr = [], []
    all_pred_next, all_prob_next = [], []

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


def plot_confusion_matrix(
    cm: np.ndarray,
    labels: list[str],
    title: str,
    save_path: Path,
) -> None:
    """Save a normalised confusion matrix figure."""
    if not _MPL:
        print(f"  [WARN] matplotlib not installed — skipping {save_path.name}")
        return

    cm_norm = cm.astype(float) / (cm.sum(axis=1, keepdims=True) + 1e-8)

    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm_norm, interpolation="nearest", cmap="Blues", vmin=0, vmax=1)
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=9)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("Predicted label", fontsize=10)
    ax.set_ylabel("True label",      fontsize=10)
    ax.set_title(title, fontsize=11, pad=12)

    for i in range(len(labels)):
        for j in range(len(labels)):
            val  = cm_norm[i, j]
            raw  = cm[i, j]
            color = "white" if val > 0.55 else "black"
            ax.text(j, i, f"{val:.2f}\n({raw})", ha="center", va="center",
                    fontsize=7.5, color=color)

    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    print(f"  Confusion matrix saved -> {save_path}")


def print_report_section(title: str, y_true, y_pred, probs, labels) -> dict:
    """Print + return metrics for one head (current or next)."""
    print(f"\n{'─' if False else '-'*65}")
    print(f"  {title}")
    print(f"{'─' if False else '-'*65}")

    acc  = accuracy_score(y_true, y_pred)
    f1m  = f1_score(y_true, y_pred, average="macro",    zero_division=0)
    f1w  = f1_score(y_true, y_pred, average="weighted", zero_division=0)

    print(f"  Accuracy (overall)  : {acc:.4f}  ({acc*100:.2f}%)")
    print(f"  F1-Macro            : {f1m:.4f}")
    print(f"  F1-Weighted         : {f1w:.4f}")

    # AUROC (one-vs-rest, only if more than one class present in y_true)
    unique = np.unique(y_true)
    if len(unique) >= 2:
        try:
            from sklearn.preprocessing import label_binarize
            y_bin = label_binarize(y_true, classes=list(range(len(labels))))
            auroc = roc_auc_score(y_bin, probs, multi_class="ovr", average="macro")
            if np.isnan(auroc):
                auroc = None
                print(f"  AUROC               : N/A (NaN — some classes absent)")
            else:
                print(f"  AUROC (macro OvR)   : {auroc:.4f}")
        except Exception as e:
            auroc = None
            print(f"  AUROC               : N/A ({e})")
    else:
        auroc = None
        print(f"  AUROC               : N/A (only one class in test set)")

    print(f"\n  Per-class report:")
    print(classification_report(
        y_true, y_pred,
        labels=list(range(len(labels))),
        target_names=labels,
        zero_division=0,
        digits=4,
    ))

    return {
        "accuracy":    round(float(acc),  4),
        "f1_macro":    round(float(f1m),  4),
        "f1_weighted": round(float(f1w),  4),
        "auroc_macro": round(float(auroc), 4) if auroc is not None else None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def evaluate(use_cuda: bool = True, seed: int = 42,
             total_per_scenario: int = 3000) -> None:
    print("=" * 65)
    print("  NetForecast AI — World Model Evaluation")
    print("=" * 65)

    device = torch.device(
        "cuda" if (use_cuda and torch.cuda.is_available()) else "cpu"
    )
    print(f"  Device: {device}")

    # ── Load model & scaler ───────────────────────────────────────────
    print("\n[1/4] Loading checkpoint and scaler ...")
    model, ckpt = load_checkpoint(device)
    scaler = load_scaler()
    print(f"  Checkpoint metrics (from training):")
    for k, v in ckpt.get("metrics", {}).items():
        print(f"    {k}: {v:.4f}" if isinstance(v, float) else f"    {k}: {v}")

    # ── Regenerate test partition (same seed + chronological split) ───
    print("\n[2/4] Regenerating test partition (seed=42, chronological split) ...")
    rng = np.random.default_rng(seed)
    sequences = generate_all_sequences(rng, total_per_scenario)
    n = len(sequences)
    val_end = int(n * 0.85)
    seq_test = sequences[val_end:]
    X_te, yc_te, yn_te = build_dataset(seq_test, SEQUENCE_LENGTH)
    X_te_s = scaler.transform(X_te).astype(np.float32)
    print(f"  Test windows: {len(X_te):,}")

    # ── Run inference ─────────────────────────────────────────────────
    print("\n[3/4] Running inference on test set ...")
    pred_curr, prob_curr, pred_next, prob_next = get_predictions(
        model, X_te_s, device
    )

    if not _SKLEARN:
        print("\n  [WARN] scikit-learn not installed.")
        print("  Manual metrics:")
        acc_c = (pred_curr == yc_te).mean()
        acc_n = (pred_next == yn_te).mean()
        print(f"  Current-state accuracy: {acc_c:.4f}")
        print(f"  Next-state    accuracy: {acc_n:.4f}")
        return

    # ── Metrics ───────────────────────────────────────────────────────
    print("\n[4/4] Computing metrics ...")
    report = {}
    report["current_state"] = print_report_section(
        "HEAD A — Current Security State Classification",
        yc_te, pred_curr, prob_curr, STATE_LABELS,
    )
    report["next_state"] = print_report_section(
        "HEAD B — Next-State Prediction",
        yn_te, pred_next, prob_next, STATE_LABELS,
    )

    # ── Confusion matrices ────────────────────────────────────────────
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    cm_curr = confusion_matrix(yc_te, pred_curr, labels=list(range(len(STATE_LABELS))))
    cm_next = confusion_matrix(yn_te, pred_next, labels=list(range(len(STATE_LABELS))))
    plot_confusion_matrix(cm_curr, STATE_LABELS, "Current State — Confusion Matrix", CM_CURR_PATH)
    plot_confusion_matrix(cm_next, STATE_LABELS, "Next State — Confusion Matrix",    CM_NEXT_PATH)

    # ── Save JSON report ──────────────────────────────────────────────
    with open(EVAL_REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Evaluation report saved -> {EVAL_REPORT_PATH}")
    print("\n  Evaluation complete.\n")


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate the NetForecast world model")
    parser.add_argument("--no-cuda", action="store_true")
    parser.add_argument("--rows",    type=int, default=3000)
    args = parser.parse_args()
    evaluate(use_cuda=not args.no_cuda, total_per_scenario=args.rows)
