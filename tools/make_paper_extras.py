"""Paper-grade statistics the course report did not need (empirical-paper prep).

1. Bootstrap confidence intervals for the headline test metrics. The frozen
   test set is scored once per checkpoint with the saved bundle, then resampled
   ``--n-boot`` times (seed 42): recall and PR-AUC on the full cohort, recall on
   the still-enrolled cohort, and the full-minus-active recall gap — so the
   dual-cohort claim carries a CI, not just point estimates.
   -> reports/tables/bootstrap_ci.csv

2. A null baseline for the top-k Jaccard agreement metrics (RQ2): the expected
   Jaccard of two independent random top-10 sets drawn from the model's feature
   space, via Monte-Carlo. Observed agreements are meaningful only against this.
   -> reports/tables/xai_jaccard_baseline.csv

Per-checkpoint bootstrap rows are cached atomically under
``reports/tables/_paper_cache/`` and reused on resume.

Run:
    python -m tools.make_paper_extras            # xgb, 1000 resamples
"""

from __future__ import annotations

import argparse
import os

from loguru import logger
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

from src.config import CHECKPOINT_MAP_PATH, CHECKPOINTS, RANDOM_SEED, RAW_DATA_DIR, TABLES_DIR
from src.evaluation.make_split import load_checkpoint_split
from src.features.preprocessing import make_X_y
from src.modeling.predict import load_bundle, predict

KEY = ["code_module", "code_presentation", "id_student"]
PRES = ["code_module", "code_presentation"]
CACHE = TABLES_DIR / "_paper_cache"


def _write_csv_atomic(df: pd.DataFrame, path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    df.to_csv(tmp, index=False)
    os.replace(tmp, path)


def _recall(y, pred) -> float:
    pos = y == 1
    return float((pred & pos).sum() / pos.sum()) if pos.sum() else float("nan")


def bootstrap_checkpoint(model_name: str, t: int, n_boot: int, rng) -> pd.DataFrame:
    """One row per (cohort, metric) with the point estimate and 95% CI at t."""
    _, test_df = load_checkpoint_split(t)
    X, y = make_X_y(test_df)
    out = predict(load_bundle(model_name, t), X)
    y = y.to_numpy()
    pred = out["pred"].to_numpy().astype(bool)
    proba = out["proba"].to_numpy()

    reg = pd.read_csv(RAW_DATA_DIR / "studentRegistration.csv")[KEY + ["date_unregistration"]]
    cut = pd.read_csv(CHECKPOINT_MAP_PATH)
    cut = cut[cut.t_percent == t][PRES + ["cutoff_day"]]
    td = test_df[KEY].merge(reg, on=KEY, how="left").merge(cut, on=PRES, how="left")
    active = (
        td["date_unregistration"].isna() | (td["date_unregistration"] > td["cutoff_day"])
    ).to_numpy()

    n = len(y)
    stats = {k: [] for k in ("recall_full", "prauc_full", "recall_active", "gap_recall")}
    for _ in range(n_boot):
        idx = rng.randint(0, n, size=n)
        yb, pb, qb, ab = y[idx], pred[idx], proba[idx], active[idx]
        rf = _recall(yb, pb)
        ra = _recall(yb[ab], pb[ab])
        stats["recall_full"].append(rf)
        stats["recall_active"].append(ra)
        stats["gap_recall"].append(rf - ra)
        stats["prauc_full"].append(float(average_precision_score(yb, qb)))

    point = {
        "recall_full": _recall(y, pred),
        "recall_active": _recall(y[active], pred[active]),
        "gap_recall": _recall(y, pred) - _recall(y[active], pred[active]),
        "prauc_full": float(average_precision_score(y, proba)),
    }
    rows = []
    for k, vals in stats.items():
        cohort, metric = (
            ("gap", "recall") if k == "gap_recall" else (k.split("_")[1], k.split("_")[0])
        )
        lo, hi = np.nanpercentile(vals, [2.5, 97.5])
        rows.append(
            {
                "model": model_name,
                "t_percent": t,
                "cohort": cohort,
                "metric": {"prauc": "pr_auc"}.get(metric, metric),
                "point": round(point[k], 4),
                "ci_lo": round(float(lo), 4),
                "ci_hi": round(float(hi), 4),
                "n_boot": n_boot,
            }
        )
    return pd.DataFrame(rows)


def jaccard_null(n_features: int, k: int = 10, n_sims: int = 100_000, seed: int = RANDOM_SEED):
    """Monte-Carlo null distribution of Jaccard(top-k A, top-k B) for random rankings."""
    rng = np.random.RandomState(seed)
    vals = np.empty(n_sims)
    for i in range(n_sims):
        a = set(rng.choice(n_features, size=k, replace=False))
        b = set(rng.choice(n_features, size=k, replace=False))
        vals[i] = len(a & b) / len(a | b)
    return {
        "n_features": n_features,
        "k": k,
        "n_sims": n_sims,
        "mean": round(float(vals.mean()), 4),
        "p95": round(float(np.percentile(vals, 95)), 4),
        "p99": round(float(np.percentile(vals, 99)), 4),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="xgb")
    ap.add_argument("--n-boot", type=int, default=1000)
    args = ap.parse_args(argv)
    CACHE.mkdir(parents=True, exist_ok=True)

    parts = []
    for t in CHECKPOINTS:
        cache = CACHE / f"boot_{args.model}_t{t}_{args.n_boot}.csv"
        if cache.exists():
            logger.info(f"resume (cached): {cache.name}")
            parts.append(pd.read_csv(cache))
            continue
        logger.info(f"bootstrap {args.model} @ t={t} ({args.n_boot} resamples)")
        rows = bootstrap_checkpoint(args.model, t, args.n_boot, np.random.RandomState(RANDOM_SEED))
        _write_csv_atomic(rows, cache)
        parts.append(rows)
    ci = pd.concat(parts, ignore_index=True)
    _write_csv_atomic(ci, TABLES_DIR / "bootstrap_ci.csv")
    logger.info(f"bootstrap_ci.csv:\n{ci.to_string(index=False)}")

    n_features = len(pd.read_csv(TABLES_DIR / "xai_shap_importance.csv"))
    null = jaccard_null(n_features)
    _write_csv_atomic(pd.DataFrame([null]), TABLES_DIR / "xai_jaccard_baseline.csv")
    logger.info(f"jaccard null (k=10, {n_features} features): {null}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
