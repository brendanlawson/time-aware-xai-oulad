"""Cross-cutting result plots (modeling + XAI), styled via src.eda.plot_style.

Keep EDA-specific charts in src/eda; put reusable result charts here:
  - metric-vs-checkpoint curves (the headline figure for RQ1)
  - feature-importance bars
  - stability drift curves (RQ2/RQ3)

Each function consumes a tidy DataFrame produced upstream (model metrics, SHAP/LIME
global importance, checkpoint-to-checkpoint stability) and writes a 300-dpi figure
via :func:`src.eda.plot_style.savefig`.

See guide section "plots.py".
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.eda.plot_style import CLASS_COLOURS, apply_style, savefig


def metric_vs_checkpoint(
    metrics: pd.DataFrame, metric: str = "roc_auc", name: str = "metric_vs_checkpoint"
) -> Path:
    """Line plot: x=t_percent, y=metric, one line per model.

    The headline figure for RQ1 — "how early can we predict at-risk students
    reliably?". ``metrics`` is the tidy table written by
    :func:`src.modeling.train.train_all` (columns: ``model``, ``t_percent`` and one
    column per metric).
    """
    apply_style()
    fig, ax = plt.subplots(figsize=(8, 5))
    for model, grp in metrics.groupby("model"):
        grp = grp.sort_values("t_percent")
        ax.plot(grp["t_percent"], grp[metric], marker="o", label=model)
    ticks = sorted(metrics["t_percent"].unique())
    ax.set_xticks(ticks)
    ax.set_xlabel("Course progress (%)")
    ax.set_ylabel(metric.replace("_", " "))
    ax.set_title(f"Model {metric} across the six checkpoints (RQ1)")
    ax.legend(title="Model")
    path = savefig(fig, name)
    plt.close(fig)
    return path


def importance_bar(
    importance: pd.DataFrame, top: int = 15, name: str = "feature_importance"
) -> Path:
    """Horizontal bar of the top-``top`` features.

    ``importance`` is the ranking from
    :func:`src.xai.shap_explain.global_importance` (columns ``feature`` and
    ``importance``, already sorted descending).
    """
    apply_style()
    imp = importance.sort_values("importance", ascending=False).head(top)
    fig, ax = plt.subplots(figsize=(8, max(3.0, 0.4 * len(imp) + 1)))
    bars = ax.barh(
        imp["feature"][::-1],
        imp["importance"][::-1],
        color=CLASS_COLOURS[1],
        edgecolor="white",
        linewidth=0.4,
    )
    ax.bar_label(bars, fmt="%.3f", padding=3, fontsize=8, color="#333333")
    ax.set_xlabel("Importance (mean |contribution|)")
    ax.set_title(f"Top {len(imp)} features by importance")
    path = savefig(fig, name)
    plt.close(fig)
    return path


def stability_drift(drift: pd.DataFrame, name: str = "stability_drift") -> Path:
    """Line plot of ranking agreement (jaccard + spearman) vs checkpoint transition.

    ``drift`` is the tidy frame from
    :func:`src.xai.stability.stability_across_checkpoints` (columns ``t_from``,
    ``t_to``, ``jaccard``, ``spearman``). A flat, high curve means the explanation
    is stable as more of the course is observed (RQ2/RQ3).
    """
    apply_style()
    d = drift.sort_values(["t_to", "t_from"])
    transitions = [f"{a}->{b}" for a, b in zip(d["t_from"], d["t_to"])]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(transitions, d["jaccard"], marker="o", color=CLASS_COLOURS[0], label="Jaccard@k")
    ax.plot(
        transitions,
        d["spearman"],
        marker="s",
        color=CLASS_COLOURS[1],
        label="Spearman",
    )
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("Checkpoint transition (% -> %)")
    ax.set_ylabel("Ranking agreement")
    ax.set_title("Explanation stability across checkpoints (RQ2/RQ3)")
    ax.legend()
    path = savefig(fig, name)
    plt.close(fig)
    return path
