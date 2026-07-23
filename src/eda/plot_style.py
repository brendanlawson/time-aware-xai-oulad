"""Executable embodiment of the chart presentation standard.

Importing :func:`apply_style` configures matplotlib/seaborn so every EDA figure is
visually consistent, colour-blind safe and print-ready (300 dpi). The fixed class
colours guarantee not-at-risk and at-risk always read the same across every chart.

Design follows current publication-quality guidance: minimal chart-junk (top/right
spines removed), a light grid drawn *below* the data, restrained typography, and
de-cluttered numeric axes via :func:`tidy_axis`.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator
import seaborn as sns

from src.config import FIGURES_DIR

# Fixed target-class colours, identical in every chart (Chart Standard section 2).
CLASS_COLOURS = {0: "#2166AC", 1: "#C0392B"}  # 0 not-at-risk (blue), 1 at-risk (red)
CLASS_LABELS = {0: "Not-at-risk", 1: "At-risk"}

# Feature-group palette (re-exported so eda.py and plots stay in sync).
GROUP_COLOURS = {
    "Demographic": "#7F8C8D",  # muted grey
    "Engagement": "#C0392B",  # red (behavioural)
    "Performance": "#2166AC",  # blue (assessment)
}

# matplotlib rcParams for the house style (resolution, typography, de-junked axes).
_RC = {
    # resolution
    "figure.dpi": 120,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.facecolor": "white",
    "figure.facecolor": "white",
    # typography --- sized so labels stay legible (~8-9pt) after the figure is
    # scaled down to one IEEE column (~0.45x). Bumped from the on-screen sizes.
    "font.family": "DejaVu Sans",
    "font.size": 15,
    "axes.titlesize": 16,
    "axes.titleweight": "bold",
    "axes.titlepad": 8,
    "axes.labelsize": 15,
    "axes.labelcolor": "#222222",
    "xtick.labelsize": 13.5,
    "ytick.labelsize": 13.5,
    "xtick.color": "#444444",
    "ytick.color": "#444444",
    "legend.fontsize": 13.5,
    "legend.frameon": False,
    "figure.titlesize": 17,
    "figure.titleweight": "bold",
    # axes / spines / grid (less chart-junk)
    "axes.edgecolor": "#888888",
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.color": "#E6E6E6",
    "grid.linewidth": 0.7,
}


def apply_style() -> None:
    """Apply the team chart standard to the current matplotlib session."""
    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update(_RC)


_THOUSANDS = FuncFormatter(lambda x, _pos: f"{x:,.0f}")


def tidy_axis(ax: plt.Axes, *, nbins: int = 5, integer: bool = False) -> None:
    """De-clutter a numeric x-axis: few round ticks + thousands separators + despine.

    Prevents the overlapping tick labels that plague wide-range count features
    (e.g. ``total_clicks`` spanning 0-24,000).
    """
    ax.xaxis.set_major_locator(MaxNLocator(nbins=nbins, integer=integer))
    ax.xaxis.set_major_formatter(_THOUSANDS)
    sns.despine(ax=ax)


def savefig(fig: plt.Figure, name: str) -> Path:
    """Save a figure to reports/figures/<name>.png at print resolution (300 dpi)."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURES_DIR / f"{name}.png"
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    return path
