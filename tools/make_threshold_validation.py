"""Pick the decision threshold on VALIDATION data (out-of-fold), never on test.

The original ``threshold_tuning.csv`` swept thresholds directly against the
held-out test labels, making the test set part of model selection (2026-07
audit finding). This script fixes the protocol:

  1. build out-of-fold (OOF) probabilities on checkpoint t's TRAIN side with the
     same pipeline as training (per-fold preprocess fit + SMOTE + model,
     5-fold StratifiedGroupKFold, seed 42);
  2. choose the three policy thresholds (max-F1, Youden, recall >= target) on
     the OOF sweep — test labels are never touched;
  3. load the saved bundle and score the frozen test ONCE at those thresholds.

Writes ``reports/tables/threshold_validation.csv`` (one row per policy with the
validation and single-shot test metrics side by side). Per-fold OOF predictions
are checkpointed atomically under ``reports/tables/_thr_cache/`` and reused on
resume, so an interrupted run continues instead of restarting.

Run:
    python -m tools.make_threshold_validation                  # xgb @ t=100
    python -m tools.make_threshold_validation --model lgbm --target-recall 0.9
"""

from __future__ import annotations

import argparse
import os

from imblearn.over_sampling import SMOTE
from loguru import logger
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, precision_score, recall_score

from src.config import RANDOM_SEED, TABLES_DIR
from src.evaluation.make_split import load_checkpoint_split
from src.evaluation.split_harness import iter_cv_folds
from src.features.preprocessing import make_X_y, preprocess
from src.modeling import threshold as thr
from src.modeling.predict import predict_checkpoint
from src.modeling.train import build_model

CACHE_DIR = TABLES_DIR / "_thr_cache"
OUT_PATH = TABLES_DIR / "threshold_validation.csv"


def _write_csv_atomic(df: pd.DataFrame, path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    df.to_csv(tmp, index=False)
    os.replace(tmp, path)


def oof_probabilities(model_name: str, t_percent: int, n_splits: int = 5) -> tuple:
    """OOF at-risk probabilities over checkpoint t's train side (resumable)."""
    train_df, _ = load_checkpoint_split(t_percent)
    X_all, y_all = make_X_y(train_df)
    oof = np.full(len(train_df), np.nan)

    for _r, fold, tr_idx, va_idx in iter_cv_folds(train_df, n_splits, n_repeats=1):
        cache = CACHE_DIR / f"{model_name}_t{t_percent}_fold{fold}.csv"
        if cache.exists():
            logger.info(f"resume (cached): {cache.name}")
            cached = pd.read_csv(cache)
            oof[cached["row"].to_numpy()] = cached["proba"].to_numpy()
            continue
        logger.info(f"fold {fold}: fit {model_name} on {len(tr_idx)} rows")
        Xtr, Xva, _ct, _fn, _st = preprocess(
            X_all.iloc[tr_idx], X_all.iloc[va_idx], scaler_save_path=None, return_stats=True
        )
        Xres, yres = SMOTE(random_state=RANDOM_SEED).fit_resample(Xtr, y_all.iloc[tr_idx])
        model = build_model(model_name, RANDOM_SEED).fit(Xres, yres)
        proba = model.predict_proba(Xva)[:, 1]
        _write_csv_atomic(pd.DataFrame({"row": va_idx, "proba": proba}), cache)
        oof[va_idx] = proba

    assert not np.isnan(oof).any(), "OOF coverage incomplete"
    return y_all.to_numpy(), oof


def _exact_metrics(y_true, proba, threshold: float) -> dict:
    pred = (np.asarray(proba) >= threshold).astype(int)
    return {
        "precision": round(float(precision_score(y_true, pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, pred, zero_division=0)), 4),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="xgb")
    ap.add_argument("--t", type=int, default=100)
    ap.add_argument("--target-recall", type=float, default=0.9)
    args = ap.parse_args(argv)

    y_val, oof = oof_probabilities(args.model, args.t)
    sweep = thr.sweep_thresholds(y_val, oof)
    chosen = {
        "default(0.5)": 0.5,
        "f1": thr.pick_by_f1(sweep),
        "youden": thr.pick_by_youden(sweep),
        f"recall>={args.target_recall:g}": thr.pick_by_target_recall(sweep, args.target_recall),
    }

    # The frozen test is scored exactly once, at thresholds fixed above.
    test = predict_checkpoint(args.model, args.t)
    rows = []
    for policy, cut in chosen.items():
        val = {f"val_{k}": v for k, v in _exact_metrics(y_val, oof, cut).items()}
        tst = {
            f"test_{k}": v for k, v in _exact_metrics(test["y_true"], test["proba"], cut).items()
        }
        rows.append(
            {"model": args.model, "t_percent": args.t, "policy": policy, "threshold": cut}
            | val
            | tst
        )
    table = pd.DataFrame(rows)
    _write_csv_atomic(table, OUT_PATH)
    logger.info(f"threshold_validation.csv:\n{table.to_string(index=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
