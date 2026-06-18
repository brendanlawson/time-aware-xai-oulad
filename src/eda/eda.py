"""Exploratory Data Analysis — statistically grounded, report-ready.

Data-quality profiling, univariate description, bivariate analysis backed by
hypothesis tests + effect sizes, multivariate correlation with a leakage check,
and a TIME-AWARE discrimination analysis tracking how class separability grows
across the six checkpoints (this directly informs RQ1).

Each public function returns a findings dict, writes figures to reports/figures/
and tables to reports/tables/. The 02_eda notebook narrates these outputs.

Run: python -m src.eda.eda

See guide section "eda/eda.py".
"""

from __future__ import annotations

import json  # noqa: F401

import numpy as np
import pandas as pd
from scipy import stats  # noqa: F401

from src.config import CHECKPOINTS_DIR, INTERIM_DATA_DIR
from src.eda.plot_style import (
    CLASS_COLOURS,  # noqa: F401
    CLASS_LABELS,  # noqa: F401
    apply_style,  # noqa: F401
    savefig,  # noqa: F401
    tidy_axis,  # noqa: F401
)

# Feature groups (used to colour plots and aggregate discrimination by group).
# TODO: fill from the data dictionary.
DEMOGRAPHIC_NUM: list[str] = []
ENGAGEMENT_NUM: list[str] = []
PERFORMANCE_NUM: list[str] = []


# --- loaders ------------------------------------------------------------------
def load_master(path=INTERIM_DATA_DIR / "master_raw.parquet") -> pd.DataFrame:
    """TODO: read the master parquet."""
    raise NotImplementedError


def load_checkpoints(checkpoints_dir=CHECKPOINTS_DIR) -> "pd.DataFrame | None":
    """Concatenate the six checkpoint parquets (with a t_percent column).

    TODO: read dataset_t{t}.parquet for each t in CHECKPOINTS; return None if none
    exist yet (EDA on the master table should still run).
    """
    raise NotImplementedError


# --- helpers ------------------------------------------------------------------
def _save_table(df: pd.DataFrame, name: str, index: bool = True) -> None:
    """TODO: write df to TABLES_DIR/<name>.csv."""
    raise NotImplementedError


def _cohens_d(a: pd.Series, b: pd.Series) -> float:
    """Effect size for two groups. TODO: (mean_a-mean_b)/pooled_sd."""
    raise NotImplementedError


def _benjamini_hochberg(pvals: list[float]) -> list[float]:
    """BH-adjusted p-values (controls FDR across many tests). TODO."""
    raise NotImplementedError


def _cramers_v(confusion: np.ndarray) -> float:
    """Association strength for a contingency table. TODO: from chi2."""
    raise NotImplementedError


# --- analyses (each returns a findings dict; writes figs + tables) ------------
def data_quality(master: pd.DataFrame) -> dict:
    """Missingness, duplicates, dtype/range checks. TODO."""
    raise NotImplementedError


def univariate(master: pd.DataFrame) -> dict:
    """Per-feature distribution + shape stats (skew/kurtosis); histograms. TODO."""
    raise NotImplementedError


def target_distribution(master: pd.DataFrame) -> dict:
    """Class balance of at_risk overall + by module. TODO."""
    raise NotImplementedError


def numeric_vs_target(master: pd.DataFrame) -> dict:
    """Numeric features vs at_risk: Mann-Whitney/t-test + Cohen's d + BH. TODO."""
    raise NotImplementedError


def categorical_vs_target(master: pd.DataFrame) -> dict:
    """Categoricals vs at_risk: chi-square + Cramér's V. TODO."""
    raise NotImplementedError


def correlation(master: pd.DataFrame) -> dict:
    """Correlation heatmap + a leakage check (no feature ~perfectly predicts y). TODO."""
    raise NotImplementedError


def time_aware(checkpoints: "pd.DataFrame | None") -> dict:
    """How class separability (e.g. AUC of single features / Cohen's d) grows
    across the six checkpoints. TODO — central to RQ1."""
    raise NotImplementedError


def withdrawn_analysis(master: pd.DataFrame) -> dict:
    """Behaviour of Withdrawn students (part of the at-risk class). TODO."""
    raise NotImplementedError


def run_all() -> dict:
    """Apply the style, load data, run every analysis, dump a findings JSON.

    TODO: apply_style(); load_master/load_checkpoints; call each analysis;
    merge dicts; write reports/eda_findings.json; return findings.
    """
    raise NotImplementedError


if __name__ == "__main__":
    run_all()
