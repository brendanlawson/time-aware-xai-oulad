"""Chart presentation standard: one import to make every figure consistent,
colour-blind safe and print-ready (300 dpi).

The colour/label constants are GIVEN (the chart standard). The three functions
are yours — see guide section "eda/plot_style.py".
"""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator  # noqa: F401
import seaborn as sns  # noqa: F401  (you'll use sns.set_theme / palettes)

# Fixed target-class colours, identical in every chart.
CLASS_COLOURS = {0: "#2166AC", 1: "#C0392B"}  # 0 not-at-risk (blue), 1 at-risk (red)
CLASS_LABELS = {0: "Not-at-risk", 1: "At-risk"}

# Feature-group palette (kept here so eda.py and plots stay in sync).
GROUP_COLOURS = {
    "Demographic": "#7F8C8D",  # muted grey
    "Engagement": "#C0392B",  # red (behavioural)
    "Performance": "#2166AC",  # blue (assessment)
}

# matplotlib rcParams for the house style (resolution, typography, de-junked axes).
_RC = {
    "figure.dpi": 120,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.facecolor": "white",
    "figure.facecolor": "white",
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.titlepad": 8,
    "axes.labelsize": 10.5,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "axes.axisbelow": True,  # grid drawn below the data
}


def apply_style() -> None:
    """Apply _RC to matplotlib (call once at the top of an EDA notebook/run).

    TODO: plt.rcParams.update(_RC); optionally sns.set_theme(style='whitegrid').
    """
    raise NotImplementedError


def tidy_axis(ax: plt.Axes, *, nbins: int = 5, integer: bool = False) -> None:
    """De-clutter a numeric axis (max nbins ticks; thousands separators).

    TODO: ax.xaxis/yaxis.set_major_locator(MaxNLocator(nbins, integer=integer));
    apply a FuncFormatter for thousands separators where appropriate.
    """
    raise NotImplementedError


def savefig(fig: plt.Figure, name: str) -> "object":
    """Save fig to FIGURES_DIR/<name>.png at 300 dpi; return the path.

    TODO: ensure FIGURES_DIR exists, fig.savefig(path), return path.
    """
    raise NotImplementedError
