"""Run the explainability layer end-to-end (Phase 5, RQ2/RQ3) on the trained models.

The SHAP / LIME / stability *code* lives in ``src/xai/``; this script executes it and
materialises the report artifacts, using the frozen split and the trained checkpoint
bundles. Everything is checkpointed: per-seed and per-checkpoint SHAP importance
vectors are cached under ``reports/tables/_xai_cache/`` and reused on resume, so a
kill mid-run continues instead of restarting.

Writes:
  tables : xai_shap_importance.csv, xai_shap_vs_lime.csv,
           xai_stability_seeds.csv, xai_stability_checkpoints.csv
  figures: shap_summary_xgb_t100.png, shap_importance_xgb_t100.png,
           lime_local_example.png, xai_stability_drift.png

CLI:
    python -m tools.make_xai_analysis                      # xgb, 5 seeds, 30 LIME rows
    python -m tools.make_xai_analysis --model xgb --seeds 5 --lime-n 30 --sample 1500
"""

from __future__ import annotations

import argparse
import os

from imblearn.over_sampling import SMOTE
import joblib
from loguru import logger
import numpy as np
import pandas as pd

from src import plots
from src.config import CHECKPOINTS, MODELS_DIR, RANDOM_SEED, TABLES_DIR
from src.evaluation.make_split import load_checkpoint_split
from src.features.preprocessing import (
    handle_missing,
    handle_outliers,
    make_X_y,
    preprocess,
    transform_test,
)
from src.modeling.train import build_model
from src.xai import lime_explain, shap_explain, stability

CACHE_DIR = TABLES_DIR / "_xai_cache"


def _write_csv_atomic(df: pd.DataFrame, path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    df.to_csv(tmp, index=False)
    os.replace(tmp, path)


def _transformed_test(bundle: dict, t: int):
    """Test matrix a saved bundle's model actually sees (train-fit stats + ct)."""
    _, test_df = load_checkpoint_split(t)
    X, y = make_X_y(test_df)
    stats = bundle.get("stats")
    if stats:
        X = handle_missing(X.copy(), stats=dict(stats["missing"]))
        X = handle_outliers(X, stats=dict(stats["outlier"]))
    return transform_test(bundle["ct"], X), y


def _shap_importance(model, X, feat_names, idx):
    """SHAP global importance (mean|value|) on the sampled rows ``X[idx]``."""
    Xs = X.iloc[idx] if hasattr(X, "iloc") else X[idx]
    expl = shap_explain.build_explainer(model, Xs)
    vals = shap_explain.compute_shap_values(expl, Xs)
    return shap_explain.global_importance(vals, feat_names), vals, Xs


def _cached_importance(cache_path, compute) -> pd.Series:
    """Load a cached [feature, importance] vector, else compute + persist it."""
    if cache_path.exists():
        logger.info(f"resume (cached): {cache_path.name}")
        imp = pd.read_csv(cache_path)
    else:
        logger.info(f"compute: {cache_path.name}")
        imp = compute()
        _write_csv_atomic(imp, cache_path)
    return imp.set_index("feature")["importance"]


def _sample_idx(n: int, sample: int, seed: int = RANDOM_SEED) -> np.ndarray:
    rng = np.random.RandomState(seed)
    return np.arange(n) if n <= sample else rng.choice(n, size=sample, replace=False)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="SHAP + LIME + explanation-stability (Phase 5).")
    p.add_argument("--model", default="xgb", help="model family to explain (default xgb)")
    p.add_argument("--seeds", type=int, default=5, help="#seeds for seed-stability (RQ2)")
    p.add_argument("--lime-n", type=int, default=30, help="#test rows for SHAP-vs-LIME agreement")
    p.add_argument("--sample", type=int, default=1500, help="#rows sampled for SHAP")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    model_name = args.model
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"XAI: model={model_name} seeds={args.seeds} lime_n={args.lime_n}")

    # --- SHAP global + summary on the headline model @ t=100 --------------------
    bundle = joblib.load(MODELS_DIR / f"{model_name}_t100.joblib")
    Xt100, y100 = _transformed_test(bundle, 100)
    n100 = Xt100.shape[0]
    idx = _sample_idx(n100, args.sample)
    shap_imp100, vals100, Xs100 = _shap_importance(
        bundle["model"], Xt100, bundle["feat_names"], idx
    )
    _write_csv_atomic(shap_imp100, TABLES_DIR / "xai_shap_importance.csv")
    plots.importance_bar(shap_imp100, top=15, name=f"shap_importance_{model_name}_t100")
    shap_explain.save_summary_plot(
        vals100, Xs100, bundle["feat_names"], name=f"shap_summary_{model_name}_t100"
    )
    shap_series100 = shap_imp100.set_index("feature")["importance"]

    # --- LIME: one local example + global SHAP-vs-LIME agreement ----------------
    Xtr, ytr, Xte, yte, feat_names = _prep_full(100)
    lime_expl = lime_explain.build_explainer(Xtr, feat_names)

    yte_arr = np.asarray(yte)
    proba = bundle["model"].predict_proba(Xte)[:, 1]
    example = int(np.argmax(np.where(yte_arr == 1, proba, -1)))  # most confident at-risk
    local = lime_explain.explain_instance(
        lime_expl, bundle["model"], Xte[example], num_features=12
    )
    plots.local_explanation_bar(
        local, name="lime_local_example", title="LIME — most-confident at-risk student"
    )

    lime_idx = _sample_idx(len(Xte), args.lime_n, seed=RANDOM_SEED + 1)
    lime_cache = CACHE_DIR / "lime_global.csv"
    if lime_cache.exists():
        logger.info("resume (cached): lime_global.csv")
        lime_series = pd.read_csv(lime_cache).set_index("feature")["importance"]
    else:
        logger.info(f"compute LIME on {len(lime_idx)} rows (slow)...")
        lw = lime_explain.local_importance_vector(
            lime_expl, bundle["model"], Xte[lime_idx], feat_names
        )
        lime_series = lw.abs().mean(axis=0).sort_values(ascending=False)
        lime_series.index.name = "feature"
        lime_series.name = "importance"
        _write_csv_atomic(lime_series.reset_index(), lime_cache)

    agree = stability.shap_lime_agreement(shap_series100, lime_series, k=10)
    _write_csv_atomic(pd.DataFrame([agree]), TABLES_DIR / "xai_shap_vs_lime.csv")

    # --- RQ2: stability across seeds @ t=100 -----------------------------------
    imp_by_seed = {}
    for s in range(args.seeds):
        seed = RANDOM_SEED + s

        def _compute(seed=seed):
            Xr, yr = SMOTE(random_state=seed).fit_resample(Xtr, ytr)
            mdl = build_model(model_name, seed).fit(Xr, yr)
            imp, _v, _x = _shap_importance(mdl, Xte, feat_names, idx)
            return imp

        imp_by_seed[seed] = _cached_importance(
            CACHE_DIR / f"shap_{model_name}_seed{seed}.csv", _compute
        )
    seeds_res = stability.stability_across_seeds(imp_by_seed, k=10)
    _write_csv_atomic(pd.DataFrame([seeds_res]), TABLES_DIR / "xai_stability_seeds.csv")

    # --- RQ3: stability across checkpoints -------------------------------------
    imp_by_t = {}
    for t in CHECKPOINTS:

        def _compute(t=t):
            b = joblib.load(MODELS_DIR / f"{model_name}_t{t}.joblib")
            Xtt, _y = _transformed_test(b, t)
            ix = _sample_idx(Xtt.shape[0], args.sample)
            imp, _v, _x = _shap_importance(b["model"], Xtt, b["feat_names"], ix)
            return imp

        imp_by_t[t] = _cached_importance(CACHE_DIR / f"shap_{model_name}_t{t}.csv", _compute)
    drift = stability.stability_across_checkpoints(imp_by_t, k=10)
    _write_csv_atomic(drift, TABLES_DIR / "xai_stability_checkpoints.csv")
    plots.stability_drift(drift, name="xai_stability_drift")

    logger.info(f"SHAP top-10 @100:\n{shap_imp100.head(10).to_string(index=False)}")
    logger.info(f"SHAP-vs-LIME agreement: {agree}")
    logger.info(f"seed stability (RQ2): {seeds_res}")
    logger.info(f"checkpoint drift (RQ3):\n{drift.to_string(index=False)}")
    return 0


def _prep_full(t: int):
    """Transformed train + test matrices at checkpoint t (for LIME + seed retrain)."""
    train_df, test_df = load_checkpoint_split(t)
    Xtr_raw, ytr = make_X_y(train_df)
    Xte_raw, yte = make_X_y(test_df)
    Xtr, Xte, _ct, feat_names, _stats = preprocess(
        Xtr_raw, Xte_raw, scaler_save_path=None, return_stats=True
    )
    return np.asarray(Xtr, dtype=float), ytr, np.asarray(Xte, dtype=float), yte, feat_names


if __name__ == "__main__":
    raise SystemExit(main())
