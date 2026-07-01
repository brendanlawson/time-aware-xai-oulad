"""Significance tests comparing the benchmark models on repeated-CV scores.

The held-out table (``model_metrics.csv``) gives one number per model, which
cannot say whether XGBoost really beats LightGBM or just won by sampling noise.
The repeated 5x5 cross-validation (``cv_metrics.csv``) gives 25 *paired* scores
per model on the SAME folds, so the comparison can be tested properly:

* Friedman test across all K models (non-parametric repeated-measures ANOVA),
  one per metric — "is ANY model different?";
* if significant, post-hoc pairwise Wilcoxon signed-rank tests on the paired
  folds with Holm correction across the K*(K-1)/2 pairs — "which pairs differ?".

CLI:
    python -m src.evaluation.stat_tests            # all metrics @ t=100

See guide section "evaluation/stat_tests.py".
"""

from __future__ import annotations

import argparse
from itertools import combinations
import os

from loguru import logger
import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare, wilcoxon

from src.config import TABLES_DIR

CV_METRICS_PATH = TABLES_DIR / "cv_metrics.csv"
FRIEDMAN_PATH = TABLES_DIR / "model_friedman.csv"
PAIRWISE_PATH = TABLES_DIR / "model_pairwise_wilcoxon.csv"

DEFAULT_METRICS = ("recall", "f1", "pr_auc", "roc_auc")


def _pivot(cv: pd.DataFrame, metric: str, t_percent: int) -> pd.DataFrame:
    """Blocks x models matrix of ``metric`` at checkpoint t (index=(repeat, fold)).

    Only fully-paired blocks (every model scored on that fold) are kept, so the
    Friedman/Wilcoxon comparisons are genuinely paired.
    """
    sub = cv[cv["t_percent"] == t_percent]
    wide = sub.pivot_table(index=["repeat", "fold"], columns="model", values=metric)
    return wide.dropna(axis=0)


def friedman_by_metric(cv: pd.DataFrame, metric: str, t_percent: int = 100) -> dict:
    """Friedman test across models for one metric.

    Returns the statistic, p-value, #models, #blocks and the best model by mean
    rank (lower mean rank = consistently higher score across folds).
    """
    wide = _pivot(cv, metric, t_percent)
    cols = list(wide.columns)
    stat, p = friedmanchisquare(*[wide[c].to_numpy() for c in cols])
    ranks = wide.rank(axis=1, ascending=False).mean().sort_values()  # rank 1 = best
    return {
        "metric": metric,
        "t_percent": int(t_percent),
        "k_models": len(cols),
        "n_blocks": int(wide.shape[0]),
        "friedman_stat": round(float(stat), 4),
        "p_value": float(p),
        "significant_0.05": bool(p < 0.05),
        "best_model": ranks.index[0],
        "mean_rank_best": round(float(ranks.iloc[0]), 3),
    }


def _holm(pvals: np.ndarray) -> np.ndarray:
    """Holm-Bonferroni step-down adjusted p-values (returned in the input order)."""
    m = len(pvals)
    order = np.argsort(pvals)
    adj = np.empty(m)
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, (m - rank) * pvals[idx])
        adj[idx] = min(running, 1.0)
    return adj


def pairwise_wilcoxon(cv: pd.DataFrame, metric: str, t_percent: int = 100) -> pd.DataFrame:
    """Post-hoc paired Wilcoxon signed-rank per model pair with Holm-corrected p.

    ``better`` names the higher-mean model of the pair; ``significant_0.05`` flags
    pairs whose Holm-adjusted p-value clears 0.05.
    """
    wide = _pivot(cv, metric, t_percent)
    cols = list(wide.columns)
    rows, pvals = [], []
    for a, b in combinations(cols, 2):
        xa, xb = wide[a].to_numpy(), wide[b].to_numpy()
        if np.allclose(xa, xb):
            stat, p = 0.0, 1.0  # identical fold scores -> no difference
        else:
            stat, p = wilcoxon(xa, xb, zero_method="zsplit")
        rows.append(
            {
                "metric": metric,
                "model_a": a,
                "model_b": b,
                "mean_a": round(float(xa.mean()), 4),
                "mean_b": round(float(xb.mean()), 4),
                "better": a if xa.mean() >= xb.mean() else b,
                "wilcoxon_stat": round(float(stat), 2),
                "p_raw": float(p),
            }
        )
        pvals.append(p)
    out = pd.DataFrame(rows)
    if not out.empty:
        out["p_holm"] = _holm(np.asarray(pvals)).round(5)
        out["significant_0.05"] = out["p_holm"] < 0.05
    return out


def run_all(cv: pd.DataFrame | None = None, metrics=DEFAULT_METRICS, t_percent: int = 100):
    """Friedman + pairwise Wilcoxon for each metric; return ``(friedman_df, pairwise_df)``."""
    if cv is None:
        cv = pd.read_csv(CV_METRICS_PATH)
    fried = pd.DataFrame([friedman_by_metric(cv, m, t_percent) for m in metrics])
    pair = pd.concat([pairwise_wilcoxon(cv, m, t_percent) for m in metrics], ignore_index=True)
    return fried, pair


def _write_csv_atomic(df: pd.DataFrame, path) -> None:
    """Write a CSV via temp file + os.replace (atomic on the same filesystem)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    df.to_csv(tmp, index=False)
    os.replace(tmp, path)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI: --t selects the CV checkpoint (only 100 is cross-validated by default)."""
    p = argparse.ArgumentParser(description="Friedman + post-hoc Wilcoxon model comparison.")
    p.add_argument("--t", type=int, default=100, help="checkpoint %% present in cv_metrics.csv")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the tests, write the two tables, and log the Friedman summary."""
    args = parse_args(argv)
    fried, pair = run_all(t_percent=args.t)
    _write_csv_atomic(fried, FRIEDMAN_PATH)
    _write_csv_atomic(pair, PAIRWISE_PATH)
    logger.info(f"friedman -> {FRIEDMAN_PATH}\n" + fried.to_string(index=False))
    logger.info(f"pairwise wilcoxon -> {PAIRWISE_PATH} ({len(pair)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
