"""Executable embodiment of the chart presentation standard (Task 39).

Importing :func:`apply_style` configures matplotlib/seaborn so every EDA figure is
visually consistent with docs/07_standards/Chart_Standards. The fixed class colours
guarantee not-at-risk and at-risk always read the same across every chart.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns

FIGURES_DIR = Path(__file__).resolve().parents[2] / "reports" / "figures"

# Fixed target-class colours, identical in every chart (Chart Standard section 2).
CLASS_COLOURS = {0: "#2166AC", 1: "#D6604D"}  # 0 not-at-risk, 1 at-risk
CLASS_LABELS = {0: "Not-at-risk", 1: "At-risk"}

_RC = {
    "font.family": "DejaVu Sans",
    "font.size": 12,
    "axes.titlesize": 13,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.figsize": (8, 5),
    "figure.dpi": 110,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
    "axes.grid": True,
    "grid.alpha": 0.3,
}


def apply_style() -> None:
    """Apply the team chart standard to the current matplotlib session."""
    sns.set_theme(style="whitegrid", palette="colorblind")
    plt.rcParams.update(_RC)


def savefig(fig: plt.Figure, name: str) -> Path:
    """Save a figure to reports/figures/<name>.png at the standard DPI."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURES_DIR / f"{name}.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    return path
