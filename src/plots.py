"""Cross-cutting result plots (modeling + XAI), styled via src.eda.plot_style.

Keep EDA-specific charts in src/eda; put reusable result charts here:
  - metric-vs-checkpoint curves (the headline figure for RQ1)
  - feature-importance bars
  - stability drift curves (RQ2/RQ3)

See guide section "plots.py".
"""

from __future__ import annotations

import pandas as pd  # noqa: F401

from src.config import FIGURES_DIR  # noqa: F401
from src.eda.plot_style import apply_style, savefig  # noqa: F401


def metric_vs_checkpoint(
    metrics: pd.DataFrame, metric: str = "roc_auc", name: str = "metric_vs_checkpoint"
):
    """Line plot: x=t_percent, y=metric, one line per model.

    TODO: apply_style(); plot; savefig. This is the figure that answers
    "how early can we predict at-risk students reliably?".
    """
    raise NotImplementedError


def importance_bar(importance: pd.DataFrame, top: int = 15, name: str = "feature_importance"):
    """Horizontal bar of the top-`top` features. TODO: plot + savefig."""
    raise NotImplementedError


def stability_drift(drift: pd.DataFrame, name: str = "stability_drift"):
    """Line plot of jaccard/spearman vs checkpoint transition. TODO: plot + savefig."""
    raise NotImplementedError
