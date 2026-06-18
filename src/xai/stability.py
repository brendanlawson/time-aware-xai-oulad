"""Explanation-stability metrics — the project's research contribution (RQ2/RQ3).

"Stability" = do explanations stay consistent when something that *shouldn't*
change the story changes? We measure it along two axes:

  * across SEEDS      — retrain/re-explain with different random_state; a trustworthy
                        explanation should rank features similarly each time.
  * across CHECKPOINTS — how the explanation drifts as more of the course is seen
                        (this drift is expected and interesting, not just noise).

Core comparison primitives compare two feature-importance rankings/vectors.

See guide section "xai/stability.py".
"""

from __future__ import annotations

import numpy as np  # noqa: F401
import pandas as pd


def jaccard_topk(rank_a: list[str], rank_b: list[str], k: int = 10) -> float:
    """Jaccard overlap of the top-k features of two rankings.

    TODO: set(a[:k]) & set(b[:k]) / set(a[:k]) | set(b[:k]).
    """
    raise NotImplementedError


def spearman_rank(imp_a: pd.Series, imp_b: pd.Series) -> float:
    """Spearman correlation between two feature-importance vectors (aligned by
    feature). TODO: align indices, scipy.stats.spearmanr."""
    raise NotImplementedError


def kendall_tau(imp_a: pd.Series, imp_b: pd.Series) -> float:
    """Kendall's tau between two importance rankings. TODO."""
    raise NotImplementedError


def stability_across_seeds(importances_by_seed: dict[int, pd.Series], k: int = 10) -> dict:
    """Aggregate pairwise agreement across seeds for ONE checkpoint/model.

    TODO: for every seed pair compute jaccard_topk + spearman_rank; return
    {"mean_jaccard":..., "mean_spearman":..., "n_pairs":...}. High mean => stable.
    """
    raise NotImplementedError


def stability_across_checkpoints(
    importances_by_t: dict[int, pd.Series], k: int = 10
) -> pd.DataFrame:
    """Track how the explanation drifts checkpoint-to-checkpoint.

    TODO: for consecutive t pairs (and vs t=100% reference) compute jaccard_topk +
    spearman_rank; return a tidy DataFrame[t_from, t_to, jaccard, spearman] for
    plotting the drift curve.
    """
    raise NotImplementedError


def shap_lime_agreement(shap_imp: pd.Series, lime_imp: pd.Series, k: int = 10) -> dict:
    """Do SHAP and LIME tell the same story? TODO: jaccard_topk + spearman_rank."""
    raise NotImplementedError
