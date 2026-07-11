"""RQ3, explanation half: does the imbalance strategy change the explanation?

``imbalance_comparison.csv`` answered RQ3 for *accuracy* only. This script
answers the other half: train the headline model (xgb @ t=100) once per
imbalance strategy — none / class_weight (scale_pos_weight) / SMOTE / ADASYN —
on the SAME transformed train matrix, compute SHAP global importance on the
SAME 1,500-row test sample, and compare the four rankings pairwise
(Jaccard top-10 + Spearman), mirroring the seed/checkpoint stability metrics.

Per-strategy SHAP importance vectors are cached atomically under
``reports/tables/_xai_cache/`` and reused on resume (interruption-safe).

Writes:
  reports/tables/xai_importance_by_strategy.csv   (feature x strategy, wide)
  reports/tables/xai_stability_strategies.csv     (pairwise jaccard/spearman)

Run:
    python -m tools.make_xai_by_strategy
"""

from __future__ import annotations

import argparse
from itertools import combinations

from imblearn.over_sampling import ADASYN, SMOTE
from loguru import logger
import pandas as pd
from tools.make_xai_analysis import (
    CACHE_DIR,
    _cached_importance,
    _prep_full,
    _sample_idx,
    _shap_importance,
    _write_csv_atomic,
)

from src.config import RANDOM_SEED, TABLES_DIR
from src.modeling.train import build_model
from src.xai import stability

STRATEGIES = ("none", "class_weight", "smote", "adasyn")


def _fit(strategy: str, model_name: str, Xtr, ytr):
    """Fit one model under the given imbalance strategy (train side only)."""
    seed = RANDOM_SEED
    if strategy == "smote":
        Xr, yr = SMOTE(random_state=seed).fit_resample(Xtr, ytr)
        return build_model(model_name, seed).fit(Xr, yr)
    if strategy == "adasyn":
        Xr, yr = ADASYN(random_state=seed).fit_resample(Xtr, ytr)
        return build_model(model_name, seed).fit(Xr, yr)
    model = build_model(model_name, seed)
    if strategy == "class_weight":
        # xgb's cost-sensitive knob; at_risk (1) is the mild majority, so this
        # slightly DOWN-weights the positive class - documented, not hidden.
        pos = int((ytr == 1).sum())
        neg = int(len(ytr) - pos)
        model.set_params(scale_pos_weight=neg / pos)
    return model.fit(Xtr, ytr)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="xgb", help="model family (default xgb)")
    ap.add_argument("--sample", type=int, default=1500, help="#test rows for SHAP")
    ap.add_argument("--k", type=int, default=10, help="top-k for Jaccard")
    args = ap.parse_args(argv)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    Xtr, ytr, Xte, _yte, feat_names = _prep_full(100)
    idx = _sample_idx(len(Xte), args.sample)

    imp_by_strategy: dict[str, pd.Series] = {}
    for s in STRATEGIES:

        def _compute(s=s):
            logger.info(f"strategy={s}: fit {args.model} + SHAP on {len(idx)} rows")
            model = _fit(s, args.model, Xtr, ytr)
            imp, _v, _x = _shap_importance(model, Xte, feat_names, idx)
            return imp

        imp_by_strategy[s] = _cached_importance(
            CACHE_DIR / f"shap_{args.model}_strategy_{s}.csv", _compute
        )

    wide = pd.DataFrame(imp_by_strategy)
    wide.index.name = "feature"
    _write_csv_atomic(
        wide.sort_values("none", ascending=False).reset_index(),
        TABLES_DIR / "xai_importance_by_strategy.csv",
    )

    rows = [
        {
            "strategy_a": a,
            "strategy_b": b,
            "jaccard_top10": round(
                stability.jaccard_topk(imp_by_strategy[a], imp_by_strategy[b], k=args.k), 4
            ),
            "spearman": round(stability.spearman_rank(imp_by_strategy[a], imp_by_strategy[b]), 4),
        }
        for a, b in combinations(STRATEGIES, 2)
    ]
    pairs = pd.DataFrame(rows)
    _write_csv_atomic(pairs, TABLES_DIR / "xai_stability_strategies.csv")
    logger.info(f"xai_stability_strategies.csv:\n{pairs.to_string(index=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
