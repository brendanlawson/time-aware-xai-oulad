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
from sklearn.metrics import confusion_matrix

from src.eda.plot_style import CLASS_COLOURS, CLASS_LABELS, apply_style, savefig


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


def model_comparison_bar(
    metrics: pd.DataFrame,
    t_percent: int = 100,
    metric_cols: tuple[str, ...] = ("recall", "f1", "pr_auc", "roc_auc"),
    name: str = "model_benchmark",
) -> Path:
    """Grouped bars comparing the candidate algorithms at one checkpoint (Phase 2).

    ``metrics`` is the tidy table from :func:`src.modeling.train.train_all`; one
    group of bars per model, one bar per metric. The proposal's headline
    benchmark figure at t=100% (which model wins on recall / PR-AUC).
    """
    apply_style()
    sub = metrics[metrics["t_percent"] == t_percent].sort_values("recall", ascending=False)
    models = sub["model"].tolist()
    x = range(len(models))
    width = 0.8 / len(metric_cols)
    fig, ax = plt.subplots(figsize=(9, 5))
    for i, m in enumerate(metric_cols):
        ax.bar([xi + i * width for xi in x], sub[m], width=width, label=m.replace("_", " "))
    ax.set_xticks([xi + width * (len(metric_cols) - 1) / 2 for xi in x])
    ax.set_xticklabels(models)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Model")
    ax.set_ylabel("score")
    ax.set_title(f"Model benchmark at t={t_percent}% of course length (Phase 2)")
    ax.legend(ncol=len(metric_cols), fontsize=8)
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


def confusion_matrix_plot(
    y_true, y_pred, name: str = "confusion_matrix", title: str | None = None
) -> Path:
    """Annotated confusion-matrix heatmap for the at-risk classifier.

    Each cell shows the raw count over its row-normalised rate, so both the error
    volume and the per-class rates read at a glance. Rows are the true class,
    columns the prediction; the bottom-right cell is correctly-flagged at-risk
    students (true positives) — the ones the early-warning system exists to catch,
    and the top-right cell (false negatives) the ones it misses.
    """
    apply_style()
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    cm_norm = cm / cm.sum(axis=1, keepdims=True).clip(min=1)
    labels = [CLASS_LABELS[0], CLASS_LABELS[1]]
    fig, ax = plt.subplots(figsize=(5.2, 4.6))
    im = ax.imshow(cm_norm, cmap="Blues", vmin=0, vmax=1)
    for i in range(2):
        for j in range(2):
            ax.text(
                j,
                i,
                f"{cm[i, j]:,}\n{cm_norm[i, j]:.1%}",
                ha="center",
                va="center",
                color="white" if cm_norm[i, j] > 0.5 else "#222222",
                fontsize=11,
                fontweight="bold",
            )
    ax.set_xticks([0, 1])
    ax.set_xticklabels(labels)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(title or "Confusion matrix")
    ax.grid(False)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="row-normalised rate")
    path = savefig(fig, name)
    plt.close(fig)
    return path


def local_explanation_bar(
    weights: pd.DataFrame, name: str = "local_explanation", title: str | None = None
) -> Path:
    """Signed local-attribution bar for ONE student (LIME/SHAP explanation).

    ``weights`` has columns ``feature`` and ``weight`` (signed). Red bars push the
    prediction toward *at-risk*, blue bars pull it toward *not-at-risk* — the "why"
    behind a single early-warning flag.
    """
    apply_style()
    w = weights.reindex(weights["weight"].abs().sort_values(ascending=True).index)
    colours = [CLASS_COLOURS[1] if v >= 0 else CLASS_COLOURS[0] for v in w["weight"]]
    fig, ax = plt.subplots(figsize=(8, max(3.0, 0.4 * len(w) + 1)))
    ax.barh(w["feature"], w["weight"], color=colours, edgecolor="white", linewidth=0.4)
    ax.axvline(0, color="#888888", lw=0.8)
    ax.set_xlabel("Local weight  (red → at-risk, blue → not-at-risk)")
    ax.set_title(title or "Local explanation for one student")
    path = savefig(fig, name)
    plt.close(fig)
    return path


def threshold_curve(
    sweep: pd.DataFrame, chosen: dict | None = None, name: str = "threshold_tuning"
) -> Path:
    """Precision / recall / F1 versus decision threshold, with chosen operating points.

    ``sweep`` is the grid from :func:`src.modeling.threshold.sweep_thresholds`
    (columns ``threshold``, ``precision``, ``recall``, ``f1``). ``chosen`` maps a
    policy name -> threshold and draws a dashed marker at each; the dotted line at
    0.5 is the naive default, so the reader sees why a tuned cut beats it for an
    imbalanced early-warning task.
    """
    apply_style()
    fig, ax = plt.subplots(figsize=(8.5, 5))
    ax.plot(sweep["threshold"], sweep["precision"], label="precision", color=CLASS_COLOURS[0])
    ax.plot(sweep["threshold"], sweep["recall"], label="recall", color=CLASS_COLOURS[1])
    ax.plot(sweep["threshold"], sweep["f1"], label="F1", color="#2E7D32")
    ax.axvline(0.5, ls=":", lw=1.0, color="#999999", label="default 0.5")
    if chosen:
        for i, (policy, thr) in enumerate(chosen.items()):
            ax.axvline(thr, ls="--", lw=1.1, color="#555555")
            ax.text(thr, 0.03 + 0.06 * i, f" {policy}={thr:.2f}", fontsize=8, color="#333333")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("Decision threshold")
    ax.set_ylabel("score")
    ax.set_title("Threshold tuning: precision / recall / F1 trade-off")
    ax.legend(ncol=2, fontsize=8)
    path = savefig(fig, name)
    plt.close(fig)
    return path
