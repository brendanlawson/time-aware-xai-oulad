"""Subgroup (fairness) metrics on the frozen test set.

Delivers the disaggregated report promised in
``docs/02_collection/Data_Source_License_Ethics`` ("Evaluate model performance
separately per demographic subgroup; report disaggregated metrics").

Scores the committed test split ONCE with a saved bundle (default: xgb @ t=100,
threshold 0.5 — the same operating point as model_metrics.csv), then reports per
level of each demographic attribute: n, base at-risk rate, recall (TPR), FPR,
precision, F1. A second table gives the max-min recall gap per attribute over
levels with n >= 50 (tiny cells are noise, not evidence).

Single fast pass (one predict on 6,489 rows) — per-item checkpointing would be
pointless here; outputs are still written atomically.

Run:
    python -m tools.make_fairness_report                 # xgb @ t=100
    python -m tools.make_fairness_report --model lgbm
"""

from __future__ import annotations

import argparse
import os

from loguru import logger
import pandas as pd

from src.config import TABLES_DIR
from src.evaluation.make_split import load_checkpoint_split
from src.features.preprocessing import make_X_y
from src.modeling.predict import load_bundle, predict

ATTRS = ["gender", "disability", "age_band", "imd_band", "highest_education", "region"]
MIN_N = 50  # levels below this are reported but excluded from the gap summary


def _write_csv_atomic(df: pd.DataFrame, path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    df.to_csv(tmp, index=False)
    os.replace(tmp, path)


def subgroup_metrics(test_df: pd.DataFrame, y, pred) -> pd.DataFrame:
    """One row per (attribute, level): n, base rate, TPR/FPR, precision, F1."""
    d = test_df[ATTRS].copy()
    d["imd_band"] = d["imd_band"].fillna("Missing")
    d["y"], d["pred"] = y.to_numpy(), pred
    rows = []
    for attr in ATTRS:
        for level, g in d.groupby(attr, dropna=False):
            pos, neg = g[g.y == 1], g[g.y == 0]
            tp = int((pos.pred == 1).sum())
            fp = int((neg.pred == 1).sum())
            rows.append(
                {
                    "attribute": attr,
                    "level": level,
                    "n": len(g),
                    "at_risk_rate": round(g.y.mean(), 4),
                    "recall": round(tp / len(pos), 4) if len(pos) else None,
                    "fpr": round(fp / len(neg), 4) if len(neg) else None,
                    "precision": round(tp / (tp + fp), 4) if (tp + fp) else None,
                    "f1": round(2 * tp / (2 * tp + fp + (len(pos) - tp)), 4)
                    if (2 * tp + fp + (len(pos) - tp))
                    else None,
                }
            )
    return pd.DataFrame(rows)


def gap_summary(sub: pd.DataFrame) -> pd.DataFrame:
    """Max-min recall/FPR spread per attribute (levels with n >= MIN_N only)."""
    big = sub[(sub.n >= MIN_N) & sub.recall.notna()]
    rows = []
    for attr, g in big.groupby("attribute"):
        rows.append(
            {
                "attribute": attr,
                "n_levels": len(g),
                "recall_min": g.recall.min(),
                "recall_max": g.recall.max(),
                "recall_gap": round(g.recall.max() - g.recall.min(), 4),
                "fpr_gap": round(g.fpr.max() - g.fpr.min(), 4),
            }
        )
    return pd.DataFrame(rows).sort_values("recall_gap", ascending=False)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="xgb", help="saved bundle name (default: xgb)")
    ap.add_argument("--t", type=int, default=100, help="checkpoint %% (default: 100)")
    args = ap.parse_args(argv)

    _, test_df = load_checkpoint_split(args.t)
    X, y = make_X_y(test_df)
    out = predict(load_bundle(args.model, args.t), X)

    sub = subgroup_metrics(test_df, y, out["pred"].to_numpy())
    sub.insert(0, "model", args.model)
    sub.insert(1, "t_percent", args.t)
    gaps = gap_summary(sub)

    _write_csv_atomic(sub, TABLES_DIR / "fairness_subgroups.csv")
    _write_csv_atomic(gaps, TABLES_DIR / "fairness_gaps.csv")
    logger.info(f"fairness_subgroups.csv ({len(sub)} rows) + fairness_gaps.csv:")
    logger.info("\n" + gaps.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
