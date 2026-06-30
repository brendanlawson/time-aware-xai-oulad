"""Train at-risk models at each time checkpoint.

Pipeline per (checkpoint t, model):
  load_checkpoint_split(t) -> make_X_y -> preprocess (anti-leakage) ->
  SMOTE on train only -> fit -> evaluate on the held-out test -> persist.

The point of the project is COMPARING performance across the six checkpoints, so
metrics are collected into one tidy table (model, t_percent, auc, f1, recall, ...).

CLI:
    python -m src.modeling.train                 # all models x all checkpoints
    python -m src.modeling.train --model logreg --t 40

See guide section "modeling/train.py".
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from imblearn.over_sampling import SMOTE
import joblib
from loguru import logger
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.neural_network import MLPClassifier

from src.config import CHECKPOINTS, MODELS_DIR, RANDOM_SEED, TABLES_DIR
from src.evaluation.make_split import load_checkpoint_split
from src.features.preprocessing import make_X_y, preprocess

# Tidy metrics table written by train_all (one row per model x checkpoint).
METRICS_PATH = TABLES_DIR / "model_metrics.csv"
_METRIC_COLS = [
    "model",
    "t_percent",
    "roc_auc",
    "pr_auc",
    "f1",
    "recall",
    "precision",
    "balanced_acc",
    "brier",
]


# --- small atomic-write / resume helpers (project rule: kill-safe checkpoints) -
def _dump_atomic(obj, path: Path) -> Path:
    """joblib.dump via a temp file + os.replace so a kill mid-write is safe."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    joblib.dump(obj, tmp)
    os.replace(tmp, path)
    return path


def _write_csv_atomic(df: "pd.DataFrame", path: Path) -> Path:
    """Write a CSV via temp file + os.replace (atomic on the same filesystem)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    df.to_csv(tmp, index=False)
    os.replace(tmp, path)
    return path


def _metrics_frame(results: dict) -> "pd.DataFrame":
    """Build the tidy metrics frame (stable column + row order) from a results map."""
    df = pd.DataFrame(list(results.values()))
    if df.empty:
        return df
    cols = [c for c in _METRIC_COLS if c in df.columns]
    cols += [c for c in df.columns if c not in cols]
    return df[cols].sort_values(["model", "t_percent"]).reset_index(drop=True)


def _load_existing(path: Path) -> dict:
    """Read a prior model_metrics.csv into a {(model, t): row} resume map."""
    if not Path(path).exists():
        return {}
    try:
        prev = pd.read_csv(path)
    except Exception:  # noqa: BLE001 - a missing/corrupt table just means start fresh
        return {}
    return {(str(r["model"]), int(r["t_percent"])): r.to_dict() for _, r in prev.iterrows()}


def _make_xgb(seed: int):
    # Lazy import: keep this module importable even where xgboost is absent.
    from xgboost import XGBClassifier

    return XGBClassifier(random_state=seed, n_jobs=-1, eval_metric="logloss", tree_method="hist")


def _make_lgbm(seed: int):
    # Lazy import: keep this module importable even where lightgbm is absent.
    from lightgbm import LGBMClassifier

    return LGBMClassifier(random_state=seed, n_jobs=-1, verbose=-1)


# Registry of estimator factories, each seeded with RANDOM_SEED. SMOTE balances
# the TRAIN fold (see train_at_checkpoint), so estimators keep their default
# class weights — adding class_weight="balanced" on top would double-correct the
# (mild) imbalance.
MODEL_REGISTRY = {
    "logreg": lambda seed: LogisticRegression(max_iter=1000, random_state=seed),
    "rf": lambda seed: RandomForestClassifier(random_state=seed, n_jobs=-1),
    "xgb": _make_xgb,
    "xgboost": _make_xgb,
    "lgbm": _make_lgbm,
    "ann": lambda seed: MLPClassifier(
        hidden_layer_sizes=(64, 32), max_iter=500, early_stopping=True, random_state=seed
    ),
    "gboost": lambda seed: HistGradientBoostingClassifier(random_state=seed),
}

# The five candidate algorithms benchmarked in the proposal (Phase 2): Logistic
# Regression, Random Forest, XGBoost, LightGBM and an ANN (MLP). `gboost`
# (HistGradientBoosting) stays in the registry as an extra fast-tree baseline.
DEFAULT_MODELS = ("logreg", "rf", "xgb", "lgbm", "ann")


def build_model(name: str, seed: int = RANDOM_SEED):
    """Return an unfitted estimator for ``name`` from :data:`MODEL_REGISTRY`.

    Valid names: logreg, rf, xgb (alias xgboost), lgbm, ann, gboost — each seeded
    with ``seed`` for reproducibility.
    """
    key = name.lower()
    if key not in MODEL_REGISTRY:
        raise ValueError(f"unknown model {name!r}; choose from {sorted(MODEL_REGISTRY)}")
    return MODEL_REGISTRY[key](seed)


def evaluate(model, X_test, y_test) -> dict:
    """Compute the metric suite on the test set.

    Returns roc_auc, pr_auc (average precision), f1, recall, precision,
    balanced_accuracy and brier. Recall of the at-risk (positive) class is the
    headline metric — catching students who need support matters most here.
    """
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    # recall (of the at-risk positive class) is the headline metric for this project.
    return {
        "roc_auc": round(float(roc_auc_score(y_test, y_proba)), 4),
        "pr_auc": round(float(average_precision_score(y_test, y_proba)), 4),
        "f1": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "balanced_acc": round(float(balanced_accuracy_score(y_test, y_pred)), 4),
        "brier": round(float(brier_score_loss(y_test, y_proba)), 4),
    }


def train_at_checkpoint(t_percent: int, model_name: str, seed: int = RANDOM_SEED) -> dict:
    """Full train+evaluate for one (t, model); persist the fitted pipeline.

    Loads checkpoint t's fixed split, fits preprocessing + SMOTE on the train fold
    only (anti-leakage), fits the model, evaluates on the held-out test, and saves
    a self-contained {model, ct, feat_names, stats} bundle for inference/XAI.
    """
    train_df, test_df = load_checkpoint_split(t_percent)
    X_train, y_train = make_X_y(train_df)
    X_test, y_test = make_X_y(test_df)
    # preprocess fits all stats (median/winsor/encoders/scaler) on TRAIN only;
    # return_stats keeps the train-learned median/winsor params for inference.
    Xtr, Xte, ct, feat_names, stats = preprocess(
        X_train, X_test, scaler_save_path=None, return_stats=True
    )
    # SMOTE the TRANSFORMED train fold ONLY — never the test fold.
    Xtr_res, y_res = SMOTE(random_state=seed).fit_resample(Xtr, y_train)
    model = build_model(model_name, seed).fit(Xtr_res, y_res)
    metrics = evaluate(model, Xte, y_test)
    # stats travel with the bundle so predict() is self-contained on raw rows.
    bundle = {"model": model, "ct": ct, "feat_names": feat_names, "stats": stats}
    _dump_atomic(bundle, MODELS_DIR / f"{model_name}_t{int(t_percent)}.joblib")
    logger.info(
        f"{model_name} @ t={t_percent}: "
        f"recall={metrics['recall']} pr_auc={metrics['pr_auc']} roc_auc={metrics['roc_auc']}"
    )
    return {"model": model_name, "t_percent": int(t_percent), **metrics}


def train_all(models=DEFAULT_MODELS, checkpoints=CHECKPOINTS) -> "pd.DataFrame":
    """Loop over models x checkpoints; return + save the held-out metrics table.

    Collects one ``train_at_checkpoint`` row per (model, t) into the tidy
    ``model_metrics.csv``. Resumable: a combo whose metrics row AND model bundle
    both already exist is skipped, and the table is rewritten after every new fit.
    """
    # Resume: seed from any prior table so re-runs continue instead of restarting.
    results = _load_existing(METRICS_PATH)
    n_new = n_skip = 0
    for model_name in models:
        for t in checkpoints:
            key = (str(model_name), int(t))
            bundle_path = MODELS_DIR / f"{model_name}_t{int(t)}.joblib"
            # A combo is done only if BOTH its metrics row and its bundle exist.
            if key in results and bundle_path.exists():
                logger.info(f"skip (resumed): {model_name} @ t={t}")
                n_skip += 1
                continue
            logger.info(f"training: {model_name} @ t={t}")
            results[key] = train_at_checkpoint(t, model_name)
            n_new += 1
            # Persist after every newly-trained combo -> interruptible + resumable.
            _write_csv_atomic(_metrics_frame(results), METRICS_PATH)
    logger.info(f"train_all: {n_new} trained, {n_skip} skipped -> {METRICS_PATH}")
    return _metrics_frame(results)


# --- Repeated cross-validation (proposal Phase 2: 5-fold x 5-seed on TRAIN) -----
CV_METRICS_PATH = TABLES_DIR / "cv_metrics.csv"  # one row per (model, t, repeat, fold)
CV_SUMMARY_PATH = TABLES_DIR / "cv_summary.csv"  # mean +/- std per (model, t)


def cross_validate(
    model_name: str,
    t_percent: int,
    n_splits: int = 5,
    n_repeats: int = 5,
    seed: int = RANDOM_SEED,
) -> "pd.DataFrame":
    """Repeated stratified-group CV on checkpoint t's TRAIN side (anti-leakage).

    For each of the n_splits x n_repeats folds, preprocessing + SMOTE are fit on
    that fold's train part ONLY, then the model is scored on the held-out fold.
    Each repeat reseeds both the partition and the estimator. Returns one row per
    fold: (model, t_percent, repeat, fold, <metric suite>).
    """
    from src.evaluation.split_harness import iter_cv_folds

    train_df, _ = load_checkpoint_split(t_percent)
    X_all, y_all = make_X_y(train_df)
    rows = []
    for r, fold, tr_idx, va_idx in iter_cv_folds(train_df, n_splits, n_repeats, seed):
        X_tr, X_va = X_all.iloc[tr_idx], X_all.iloc[va_idx]
        y_tr, y_va = y_all.iloc[tr_idx], y_all.iloc[va_idx]
        Xtr, Xva, _ct, _fn, _st = preprocess(X_tr, X_va, scaler_save_path=None, return_stats=True)
        Xtr_res, y_res = SMOTE(random_state=seed).fit_resample(Xtr, y_tr)
        model = build_model(model_name, seed + r).fit(Xtr_res, y_res)
        rows.append(
            {
                "model": model_name,
                "t_percent": int(t_percent),
                "repeat": r,
                "fold": fold,
                **evaluate(model, Xva, y_va),
            }
        )
    return pd.DataFrame(rows)


def _cv_summary(df: "pd.DataFrame") -> "pd.DataFrame":
    """Aggregate per-fold CV rows into mean +/- std per (model, t_percent)."""
    metric_cols = [c for c in _METRIC_COLS if c in df.columns and c not in ("model", "t_percent")]
    g = df.groupby(["model", "t_percent"])[metric_cols]
    out = g.mean().round(4).add_suffix("_mean").join(g.std(ddof=0).round(4).add_suffix("_std"))
    return out.reset_index().sort_values(["t_percent", "f1_mean"], ascending=[True, False])


def cross_validate_all(
    models=DEFAULT_MODELS, checkpoints=(100,), n_splits: int = 5, n_repeats: int = 5
) -> "pd.DataFrame":
    """Run repeated CV for each (model, t); write cv_metrics.csv + cv_summary.csv.

    Resumable at the (model, t) grain: a combo already present in cv_metrics.csv is
    skipped, and both tables are rewritten after every newly-evaluated combo.
    """
    prev = pd.read_csv(CV_METRICS_PATH) if CV_METRICS_PATH.exists() else pd.DataFrame()
    done = (
        set()
        if prev.empty
        else {(str(m), int(t)) for m, t in prev[["model", "t_percent"]].itertuples(index=False)}
    )
    parts = [prev] if not prev.empty else []
    for model_name in models:
        for t in checkpoints:
            if (str(model_name), int(t)) in done:
                logger.info(f"skip (resumed) CV: {model_name} @ t={t}")
                continue
            logger.info(f"CV ({n_splits}x{n_repeats}): {model_name} @ t={t}")
            parts.append(cross_validate(model_name, t, n_splits, n_repeats))
            allrows = pd.concat(parts, ignore_index=True)
            _write_csv_atomic(allrows, CV_METRICS_PATH)
            _write_csv_atomic(_cv_summary(allrows), CV_SUMMARY_PATH)
    allrows = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
    return _cv_summary(allrows) if not allrows.empty else allrows


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI: optional --model / --t; --cv switches to repeated cross-validation."""
    p = argparse.ArgumentParser(
        description="Train or cross-validate at-risk models across the six checkpoints."
    )
    p.add_argument(
        "--model",
        choices=sorted(MODEL_REGISTRY),
        default=None,
        help="only this model (default: the five benchmark models LR/RF/XGB/LGBM/ANN)",
    )
    p.add_argument(
        "--t",
        type=int,
        choices=CHECKPOINTS,
        default=None,
        help="only this checkpoint %% (default: all six; with --cv, default 100)",
    )
    p.add_argument(
        "--cv",
        action="store_true",
        help="repeated 5-fold x 5-seed CV on the train set instead of a held-out fit",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Parse args; run held-out training (default) or cross-validation (--cv)."""
    args = parse_args(argv)
    models = (args.model,) if args.model else DEFAULT_MODELS
    if args.cv:
        checkpoints = (args.t,) if args.t is not None else (100,)
        summary = cross_validate_all(models, checkpoints)
        if not summary.empty:
            logger.info("cv_summary.csv:\n" + summary.to_string(index=False))
        return 0
    checkpoints = (args.t,) if args.t is not None else CHECKPOINTS
    metrics = train_all(models, checkpoints)
    if not metrics.empty:
        logger.info("model_metrics.csv:\n" + metrics.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
