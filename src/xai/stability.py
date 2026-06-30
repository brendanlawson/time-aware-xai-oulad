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

import itertools

import numpy as np
import pandas as pd


def _as_series(obj) -> pd.Series:
    """Coerce an importance object to a feature-indexed Series."""
    if isinstance(obj, pd.Series):
        return obj
    if isinstance(obj, pd.DataFrame):
        if {"feature", "importance"}.issubset(obj.columns):
            return obj.set_index("feature")["importance"]
        return obj.set_index(obj.columns[0])[obj.columns[1]]
    raise TypeError(f"Cannot interpret {type(obj)!r} as a feature-importance vector.")


def _as_ranking(obj) -> list:
    """Coerce to a list of features ordered by descending importance."""
    if isinstance(obj, (pd.Series, pd.DataFrame)):
        return _as_series(obj).sort_values(ascending=False).index.tolist()
    return list(obj)


def _align(imp_a, imp_b) -> tuple[np.ndarray, np.ndarray]:
    """Align two importance vectors on their shared features (by name)."""
    a, b = _as_series(imp_a), _as_series(imp_b)
    common = a.index.intersection(b.index)
    return a.loc[common].to_numpy(dtype=float), b.loc[common].to_numpy(dtype=float)


def jaccard_topk(rank_a: list[str], rank_b: list[str], k: int = 10) -> float:
    """Jaccard overlap of the top-k features of two rankings.

    ``|top_k(a) & top_k(b)| / |top_k(a) | top_k(b)|``. Accepts ranked name lists or
    importance Series/DataFrames (coerced to a descending ranking first).
    """
    top_a = set(_as_ranking(rank_a)[:k])
    top_b = set(_as_ranking(rank_b)[:k])
    union = top_a | top_b
    if not union:
        return float("nan")
    return len(top_a & top_b) / len(union)


def spearman_rank(imp_a: pd.Series, imp_b: pd.Series) -> float:
    """Spearman correlation between two feature-importance vectors (aligned by
    feature)."""
    from scipy.stats import spearmanr

    a, b = _align(imp_a, imp_b)
    if len(a) < 2:
        return float("nan")
    rho, _ = spearmanr(a, b)
    return float(rho)


def kendall_tau(imp_a: pd.Series, imp_b: pd.Series) -> float:
    """Kendall's tau between two feature-importance vectors (aligned by feature)."""
    from scipy.stats import kendalltau

    a, b = _align(imp_a, imp_b)
    if len(a) < 2:
        return float("nan")
    tau, _ = kendalltau(a, b)
    return float(tau)


def stability_across_seeds(importances_by_seed: dict[int, pd.Series], k: int = 10) -> dict:
    """Aggregate pairwise agreement across seeds for ONE checkpoint/model.

    For every seed pair computes jaccard_topk + spearman_rank and averages them,
    returning ``{"mean_jaccard", "mean_spearman", "n_pairs"}``. A high mean means
    the explanation is stable to the random seed.
    """
    seeds = sorted(importances_by_seed)
    jaccards, spearmans = [], []
    for seed_a, seed_b in itertools.combinations(seeds, 2):
        imp_a, imp_b = importances_by_seed[seed_a], importances_by_seed[seed_b]
        jaccards.append(jaccard_topk(imp_a, imp_b, k=k))
        spearmans.append(spearman_rank(imp_a, imp_b))
    n_pairs = len(jaccards)
    return {
        "mean_jaccard": float(np.nanmean(jaccards)) if n_pairs else float("nan"),
        "mean_spearman": float(np.nanmean(spearmans)) if n_pairs else float("nan"),
        "n_pairs": n_pairs,
    }


def stability_across_checkpoints(
    importances_by_t: dict[int, pd.Series], k: int = 10
) -> pd.DataFrame:
    """Track how the explanation drifts checkpoint-to-checkpoint.

    For consecutive ``t`` pairs and for each ``t`` vs the t=100% reference, computes
    jaccard_topk + spearman_rank and returns a tidy
    ``DataFrame[t_from, t_to, jaccard, spearman]`` for plotting the drift curve.
    """
    ts = sorted(importances_by_t)
    reference = 100 if 100 in importances_by_t else (ts[-1] if ts else None)

    rows: list[dict] = []
    seen: set[tuple[int, int]] = set()

    def _add(t_from, t_to) -> None:
        if t_from == t_to or (t_from, t_to) in seen:
            return
        seen.add((t_from, t_to))
        imp_a, imp_b = importances_by_t[t_from], importances_by_t[t_to]
        rows.append(
            {
                "t_from": t_from,
                "t_to": t_to,
                "jaccard": jaccard_topk(imp_a, imp_b, k=k),
                "spearman": spearman_rank(imp_a, imp_b),
            }
        )

    for t_from, t_to in zip(ts[:-1], ts[1:]):  # consecutive drift
        _add(t_from, t_to)
    if reference is not None:  # drift vs the full-course view
        for t in ts:
            _add(t, reference)

    return pd.DataFrame(rows, columns=["t_from", "t_to", "jaccard", "spearman"])


def shap_lime_agreement(shap_imp: pd.Series, lime_imp: pd.Series, k: int = 10) -> dict:
    """Do SHAP and LIME tell the same story? Returns jaccard_topk + spearman_rank
    (plus kendall_tau) between the two importance vectors."""
    return {
        "jaccard": jaccard_topk(shap_imp, lime_imp, k=k),
        "spearman": spearman_rank(shap_imp, lime_imp),
        "kendall": kendall_tau(shap_imp, lime_imp),
    }
