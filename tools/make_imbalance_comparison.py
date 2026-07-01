"""Phase 4 (RQ3): compare class-imbalance strategies across the candidate models.

For each of the five models at the t=100% checkpoint, train under four strategies
and score on the held-out test — the "before vs after" imbalance comparison:

  * none          - no resampling, default class weights (the baseline);
  * class_weight  - cost-sensitive learning (class_weight='balanced', or
                    scale_pos_weight for XGBoost; N/A for the MLP/ANN);
  * SMOTE         - synthetic minority oversampling (train fold only);
  * ADASYN        - adaptive synthetic oversampling (train fold only).

Anti-leakage throughout: preprocessing is fit on the train fold only, and any
resampling touches the train fold ONLY — never the held-out test. Checkpointed:
each (model, strategy) row is written to imbalance_comparison.csv as it finishes
and skipped on resume.

CLI:
    python -m tools.make_imbalance_comparison            # 5 models x 4 strategies @ t=100
"""

from __future__ import annotations

import argparse
import os

from imblearn.over_sampling import ADASYN, SMOTE
from loguru import logger
import pandas as pd

from src import plots
from src.config import RANDOM_SEED, TABLES_DIR
from src.evaluation.make_split import load_checkpoint_split
from src.features.preprocessing import make_X_y, preprocess
from src.modeling.train import DEFAULT_MODELS, build_model, evaluate

COMPARISON_PATH = TABLES_DIR / "imbalance_comparison.csv"
STRATEGIES = ("none", "class_weight", "SMOTE", "ADASYN")
_METRICS = ("recall", "f1", "pr_auc", "roc_auc", "precision", "balanced_acc")


def _write_csv_atomic(df: pd.DataFrame, path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    df.to_csv(tmp, index=False)
    os.replace(tmp, path)


def _class_weighted(name: str, y_train, seed: int):
    """Return a cost-sensitive estimator, or None if the family has no class weighting.

    logreg/rf/lgbm take ``class_weight='balanced'``; XGBoost uses
    ``scale_pos_weight = n_neg/n_pos``; the MLP/ANN supports neither, so it is
    reported as N/A for the class_weight strategy.
    """
    key = name.lower()
    if key == "logreg":
        from sklearn.linear_model import LogisticRegression

        return LogisticRegression(max_iter=1000, class_weight="balanced", random_state=seed)
    if key == "rf":
        from sklearn.ensemble import RandomForestClassifier

        return RandomForestClassifier(class_weight="balanced", n_jobs=-1, random_state=seed)
    if key == "lgbm":
        from lightgbm import LGBMClassifier

        return LGBMClassifier(class_weight="balanced", random_state=seed, n_jobs=-1, verbose=-1)
    if key in ("xgb", "xgboost"):
        from xgboost import XGBClassifier

        n_pos = int((y_train == 1).sum())
        n_neg = int((y_train == 0).sum())
        spw = (n_neg / n_pos) if n_pos else 1.0
        return XGBClassifier(
            random_state=seed,
            n_jobs=-1,
            eval_metric="logloss",
            tree_method="hist",
            scale_pos_weight=spw,
        )
    return None  # ann/MLP: no class weighting


def _fit_eval(model_name: str, strategy: str, Xtr, ytr, Xte, yte, seed: int) -> dict | None:
    """Train ``model_name`` under ``strategy`` on the train fold; eval on test.

    Returns a metrics row, or None when the strategy does not apply to the model
    (class_weight on the ANN).
    """
    if strategy == "none":
        model = build_model(model_name, seed).fit(Xtr, ytr)
    elif strategy == "class_weight":
        est = _class_weighted(model_name, ytr, seed)
        if est is None:
            return None
        model = est.fit(Xtr, ytr)
    elif strategy == "SMOTE":
        Xr, yr = SMOTE(random_state=seed).fit_resample(Xtr, ytr)
        model = build_model(model_name, seed).fit(Xr, yr)
    elif strategy == "ADASYN":
        Xr, yr = ADASYN(random_state=seed).fit_resample(Xtr, ytr)
        model = build_model(model_name, seed).fit(Xr, yr)
    else:
        raise ValueError(f"unknown strategy {strategy!r}")
    return {"model": model_name, "strategy": strategy, **evaluate(model, Xte, yte)}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Imbalance-strategy comparison (Phase 4 / RQ3).")
    p.add_argument("--t", type=int, default=100, help="checkpoint %% (proposal: 100)")
    p.add_argument("--headline", default="xgb", help="model for the before/after figure")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    seed = RANDOM_SEED

    train_df, test_df = load_checkpoint_split(args.t)
    Xtr_raw, ytr = make_X_y(train_df)
    Xte_raw, yte = make_X_y(test_df)
    Xtr, Xte, _ct, _fn, _st = preprocess(
        Xtr_raw, Xte_raw, scaler_save_path=None, return_stats=True
    )
    logger.info(
        f"imbalance comparison @ t={args.t}: {len(STRATEGIES)} strategies x {len(DEFAULT_MODELS)} models"
    )

    # Resume: keep any already-computed (model, strategy) rows.
    prev = pd.read_csv(COMPARISON_PATH) if COMPARISON_PATH.exists() else pd.DataFrame()
    done = (
        set()
        if prev.empty
        else {(str(m), str(s)) for m, s in prev[["model", "strategy"]].itertuples(index=False)}
    )
    rows = prev.to_dict("records") if not prev.empty else []

    for model_name in DEFAULT_MODELS:
        for strat in STRATEGIES:
            if (model_name, strat) in done:
                logger.info(f"skip (resumed): {model_name} / {strat}")
                continue
            row = _fit_eval(model_name, strat, Xtr, ytr, Xte, yte, seed)
            if row is None:
                logger.info(f"N/A: {model_name} / {strat} (no class weighting)")
                continue
            rows.append(row)
            _write_csv_atomic(pd.DataFrame(rows), COMPARISON_PATH)  # checkpoint each combo
            logger.info(
                f"{model_name:7s} / {strat:12s} -> recall={row['recall']} "
                f"f1={row['f1']} pr_auc={row['pr_auc']}"
            )

    df = pd.DataFrame(rows).sort_values(["model", "strategy"]).reset_index(drop=True)
    _write_csv_atomic(df, COMPARISON_PATH)

    # Figure 1: before/after for the headline model (x = strategy, bars = metrics).
    head = df[df["model"] == args.headline].set_index("strategy").reindex(STRATEGIES).reset_index()
    plots.grouped_bar(
        head,
        "strategy",
        ("recall", "f1", "pr_auc"),
        name="imbalance_comparison",
        title=f"{args.headline} @ t={args.t}% — imbalance strategy (before vs after)",
        xlabel="Imbalance strategy",
    )
    # Figure 2: recall of every model under each strategy (x = model, bars = strategy).
    wide = df.pivot_table(index="model", columns="strategy", values="recall").reset_index()
    wide = wide[["model", *[s for s in STRATEGIES if s in wide.columns]]]
    plots.grouped_bar(
        wide,
        "model",
        tuple(s for s in STRATEGIES if s in wide.columns),
        name="imbalance_recall_by_model",
        title=f"At-risk recall by model x imbalance strategy (t={args.t}%)",
        xlabel="Model",
    )
    # Figure 3: Phase-2 baseline benchmark (no-resample) — the "before imbalance" view.
    base = (
        df[df["strategy"] == "none"].sort_values("recall", ascending=False).reset_index(drop=True)
    )
    plots.grouped_bar(
        base,
        "model",
        ("recall", "f1", "pr_auc", "roc_auc"),
        name="model_benchmark_baseline",
        title=f"Benchmark 5 model @ t={args.t}% (baseline, no-resample)",
        xlabel="Model",
    )

    logger.info("imbalance_comparison.csv:\n" + df.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
