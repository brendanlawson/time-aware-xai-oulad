"""Bias-variance diagnostics (course Ch.6: overfitting / underfitting, bias-variance).

Two complementary views, both for the selected model (xgb):

  1. Train-vs-test metric gap across all six checkpoints.
     Reuses the DEPLOYED bundles (no retraining): apply predict() to the train and
     test rows and score both. A small train->test drop is direct evidence of low
     variance (the model is not memorising); a low train score would flag bias.

  2. A learning curve at t=100 (train score vs held-out CV score as the training
     set grows). Converging curves with a small gap = a healthy bias-variance
     balance; a wide persistent gap = variance (overfit); both curves low = bias
     (underfit).

Honest simplification (same as tools/tune_models.py): for the learning curve the
encoder/scaler is fit once on the full train fold, while the leakage-sensitive
step (SMOTE) stays inside each CV fold via an imblearn Pipeline. This is a
DIAGNOSTIC, not a headline metric, so the mild rescaling optimism is acceptable.

Outputs:
  reports/tables/bias_variance_gap.csv          per (checkpoint) train vs test metrics + gap
  reports/tables/bias_variance_learning_curve.csv  per train-size mean/std train & cv recall
  reports/figures/bias_variance_gap.png
  reports/figures/bias_variance_learning_curve.png

Run:
    python -m tools.make_bias_variance                 # xgb, all checkpoints
    python -m tools.make_bias_variance --model lgbm --force
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from loguru import logger
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold, learning_curve

from src.config import CHECKPOINTS, RANDOM_SEED, TABLES_DIR
from src.eda.plot_style import apply_style, savefig
from src.evaluation.make_split import load_checkpoint_split
from src.features.preprocessing import make_X_y, preprocess
from src.modeling.predict import load_bundle, predict
from src.modeling.train import build_model

GAP_CSV = TABLES_DIR / "bias_variance_gap.csv"
LC_CSV = TABLES_DIR / "bias_variance_learning_curve.csv"


def _write_csv_atomic(df: pd.DataFrame, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    df.to_csv(tmp, index=False)
    os.replace(tmp, path)
    return path


def _score(y_true, pred, proba) -> dict:
    return {
        "recall": round(float(recall_score(y_true, pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, pred, zero_division=0)), 4),
        "pr_auc": round(float(average_precision_score(y_true, proba)), 4),
        "roc_auc": round(float(roc_auc_score(y_true, proba)), 4),
    }


def train_test_gap(model_name: str, checkpoints=CHECKPOINTS) -> pd.DataFrame:
    """Score the deployed bundle on its own train fold vs the held-out test fold.

    No retraining: this is exactly the deployed model, so the gap is the honest
    generalisation gap. One row per checkpoint with train_*, test_* and gap_*.
    """
    rows = []
    for t in checkpoints:
        train_df, test_df = load_checkpoint_split(t)
        Xtr, ytr = make_X_y(train_df)
        Xte, yte = make_X_y(test_df)
        bundle = load_bundle(model_name, t)
        ptr = predict(bundle, Xtr)
        pte = predict(bundle, Xte)
        tr = _score(ytr, ptr["pred"], ptr["proba"])
        te = _score(yte, pte["pred"], pte["proba"])
        row = {"model": model_name, "t_percent": int(t)}
        row.update({f"train_{k}": v for k, v in tr.items()})
        row.update({f"test_{k}": v for k, v in te.items()})
        row.update({f"gap_{k}": round(tr[k] - te[k], 4) for k in tr})
        rows.append(row)
        logger.info(
            f"{model_name} t={t}: train recall={tr['recall']} test recall={te['recall']} "
            f"gap={row['gap_recall']}"
        )
    return pd.DataFrame(rows)


def learning_curve_at(
    model_name: str, t_percent: int = 100, seed: int = RANDOM_SEED
) -> pd.DataFrame:
    """Recall learning curve: SMOTE stays per-fold; encoder/scaler fit once (see header)."""
    train_df, _ = load_checkpoint_split(t_percent)
    X_raw, y = make_X_y(train_df)
    groups = train_df["id_student"].to_numpy()
    # ponytail: ct fit once on full train (diagnostic, not a headline metric); SMOTE per-fold.
    Xtr, _Xte, _ct, _fn, _st = preprocess(X_raw, X_raw, scaler_save_path=None, return_stats=True)
    pipe = ImbPipeline(
        [("smote", SMOTE(random_state=seed)), ("model", build_model(model_name, seed))]
    )
    cv = StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=seed)
    sizes, train_scores, cv_scores = learning_curve(
        pipe,
        Xtr,
        y,
        groups=groups,
        cv=cv,
        scoring="recall",
        train_sizes=np.linspace(0.1, 1.0, 6),
        n_jobs=-1,
    )
    return pd.DataFrame(
        {
            "model": model_name,
            "t_percent": int(t_percent),
            "train_size": sizes,
            "train_recall_mean": train_scores.mean(axis=1).round(4),
            "train_recall_std": train_scores.std(axis=1).round(4),
            "cv_recall_mean": cv_scores.mean(axis=1).round(4),
            "cv_recall_std": cv_scores.std(axis=1).round(4),
        }
    )


def _plot_gap(df: pd.DataFrame, model_name: str) -> Path:
    apply_style()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(df["t_percent"], df["train_recall"], marker="o", label="Train recall", color="#2166AC")
    ax.plot(df["t_percent"], df["test_recall"], marker="s", label="Test recall", color="#C0392B")
    ax.fill_between(
        df["t_percent"], df["train_recall"], df["test_recall"], alpha=0.12, color="gray"
    )
    for _, r in df.iterrows():
        ax.annotate(
            f"gap {r['gap_recall']:+.3f}",
            (r["t_percent"], r["test_recall"]),
            textcoords="offset points",
            xytext=(0, -14),
            ha="center",
            fontsize=7.5,
            color="#555555",
        )
    ax.set_xticks(df["t_percent"])
    ax.set_ylim(0.5, 1.02)
    ax.set_xlabel("Course progress (%)")
    ax.set_ylabel("Recall (at-risk)")
    ax.set_title(f"Train vs test recall gap across checkpoints ({model_name})")
    ax.legend()
    path = savefig(fig, "bias_variance_gap")
    plt.close(fig)
    return path


def _plot_learning_curve(df: pd.DataFrame, model_name: str) -> Path:
    apply_style()
    fig, ax = plt.subplots(figsize=(8, 5))
    for col, colour, lab in [
        ("train_recall", "#2166AC", "Train"),
        ("cv_recall", "#C0392B", "Cross-val"),
    ]:
        m, s = df[f"{col}_mean"], df[f"{col}_std"]
        ax.plot(df["train_size"], m, marker="o", color=colour, label=lab)
        ax.fill_between(df["train_size"], m - s, m + s, alpha=0.15, color=colour)
    ax.set_xlabel("Training examples")
    ax.set_ylabel("Recall (at-risk)")
    ax.set_title(f"Learning curve at t=100% ({model_name}) — bias-variance view")
    ax.legend()
    path = savefig(fig, "bias_variance_learning_curve")
    plt.close(fig)
    return path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Bias-variance diagnostics (gap + learning curve).")
    p.add_argument("--model", default="xgb", help="model name (default xgb)")
    p.add_argument("--force", action="store_true", help="recompute even if output CSVs exist")
    p.add_argument("--skip-learning-curve", action="store_true", help="only the train/test gap")
    args = p.parse_args(argv)

    if args.force or not GAP_CSV.exists():
        gap = train_test_gap(args.model)
        _write_csv_atomic(gap, GAP_CSV)
        _plot_gap(gap, args.model)
        logger.info(f"gap -> {GAP_CSV}")
    else:
        gap = pd.read_csv(GAP_CSV)
        logger.info(f"skip (resumed): {GAP_CSV} exists")

    if not args.skip_learning_curve and (args.force or not LC_CSV.exists()):
        lc = learning_curve_at(args.model, 100)
        _write_csv_atomic(lc, LC_CSV)
        _plot_learning_curve(lc, args.model)
        logger.info(f"learning curve -> {LC_CSV}")
    elif not args.skip_learning_curve:
        logger.info(f"skip (resumed): {LC_CSV} exists")

    logger.info(
        "\n"
        + gap[["t_percent", "train_recall", "test_recall", "gap_recall"]].to_string(index=False)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
