"""Exploratory Data Analysis for Chapter 4 (Tasks 27, 28, 35-38).

Reusable functions, each producing a figure (saved under reports/figures/) and/or a
table, plus a findings dictionary used by the report. The 02_eda notebook calls
these so the notebook and the committed figures stay in lock-step.

Run as a script to regenerate every figure and reports/eda_findings.json:
    python -m src.eda.eda
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import matplotlib.pyplot as plt  # noqa: E402

from src.data.io_utils import CHECKPOINTS_DIR, INTERIM_DIR  # noqa: E402
from src.data.time_utils import CHECKPOINTS  # noqa: E402
from src.eda.plot_style import CLASS_COLOURS, CLASS_LABELS, apply_style, savefig  # noqa: E402

REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"

NUMERIC_MAIN = [
    "total_clicks",
    "n_days_active",
    "mean_clicks_per_active_day",
    "max_clicks_single_day",
    "days_since_last_activity",
    "mean_score_to_date",
    "weighted_score_to_date",
    "n_assessments_submitted",
    "num_of_prev_attempts",
    "studied_credits",
]
CATEGORICAL_MAIN = [
    "gender",
    "region",
    "highest_education",
    "imd_band",
    "age_band",
    "disability",
]


def load_master(path: Path = INTERIM_DIR / "master_raw.parquet") -> pd.DataFrame:
    return pd.read_parquet(path)


def load_checkpoints(checkpoints_dir: Path = CHECKPOINTS_DIR) -> pd.DataFrame | None:
    frames = []
    for t in CHECKPOINTS:
        p = checkpoints_dir / f"dataset_t{t}.parquet"
        if not p.exists():
            return None
        frames.append(pd.read_parquet(p))
    return pd.concat(frames, ignore_index=True)


# --- Task 27: class distribution & imbalance ---------------------------------
def class_distribution(master: pd.DataFrame) -> dict:
    apply_style()
    counts = master["final_result"].value_counts()
    at_risk_rate = float(master["at_risk"].mean())

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    order = ["Distinction", "Pass", "Fail", "Withdrawn"]
    bar_colours = [
        CLASS_COLOURS[0],
        CLASS_COLOURS[0],
        CLASS_COLOURS[1],
        CLASS_COLOURS[1],
    ]
    axes[0].bar(order, [counts.get(k, 0) for k in order], color=bar_colours)
    axes[0].set_title("final_result distribution")
    axes[0].set_ylabel("Number of students")
    axes[0].tick_params(axis="x", rotation=20)

    binary = master["at_risk"].map(CLASS_LABELS).value_counts()
    axes[1].bar(
        binary.index,
        binary.values,
        color=[
            CLASS_COLOURS[1] if "At" in i else CLASS_COLOURS[0] for i in binary.index
        ],
    )
    axes[1].set_title(f"at_risk distribution (at-risk = {at_risk_rate:.1%})")
    axes[1].set_ylabel("Number of students")
    fig.suptitle("Class distribution and imbalance", fontweight="bold")
    savefig(fig, "dist_class_distribution")
    plt.close(fig)

    return {
        "n_records": int(len(master)),
        "final_result_counts": counts.to_dict(),
        "at_risk_rate": round(at_risk_rate, 4),
        "not_at_risk_rate": round(1 - at_risk_rate, 4),
        "imbalance_ratio": round(at_risk_rate / (1 - at_risk_rate), 3),
    }


# --- Task 28: descriptive statistics -----------------------------------------
def descriptive_stats(master: pd.DataFrame) -> dict:
    desc = master[NUMERIC_MAIN].describe().T
    desc["median"] = master[NUMERIC_MAIN].median()
    desc["skew"] = master[NUMERIC_MAIN].skew()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    desc.to_csv(REPORTS_DIR / "eda_descriptive_stats.csv", encoding="utf-8-sig")

    missing = master.isnull().sum()
    missing = missing[missing > 0]
    return {
        "descriptive_stats_path": "reports/eda_descriptive_stats.csv",
        "missing_values": missing.to_dict(),
        "most_skewed": desc["skew"]
        .sort_values(ascending=False)
        .head(5)
        .round(2)
        .to_dict(),
    }


# --- Task 35: distribution plots (hist/KDE/box) ------------------------------
def distribution_plots(master: pd.DataFrame) -> None:
    apply_style()
    import seaborn as sns

    fig, axes = plt.subplots(2, 5, figsize=(20, 8))
    for ax, col in zip(axes.ravel(), NUMERIC_MAIN):
        sns.histplot(master[col], kde=True, ax=ax, color=CLASS_COLOURS[0])
        ax.set_title(col)
        ax.set_xlabel("")
    fig.suptitle(
        "Distributions of main numeric features (histogram + KDE)", fontweight="bold"
    )
    savefig(fig, "dist_numeric_hist_kde")
    plt.close(fig)

    fig, axes = plt.subplots(2, 5, figsize=(20, 8))
    for ax, col in zip(axes.ravel(), NUMERIC_MAIN):
        sns.boxplot(y=master[col], ax=ax, color=CLASS_COLOURS[0])
        ax.set_title(col)
        ax.set_ylabel("")
    fig.suptitle(
        "Boxplots of main numeric features (outlier inspection)", fontweight="bold"
    )
    savefig(fig, "dist_numeric_boxplots")
    plt.close(fig)


# --- Task 36: bivariate analysis vs target -----------------------------------
def bivariate_analysis(master: pd.DataFrame) -> dict:
    apply_style()
    import seaborn as sns

    feats = [
        "total_clicks",
        "n_days_active",
        "mean_score_to_date",
        "weighted_score_to_date",
        "n_assessments_submitted",
        "days_since_last_activity",
    ]
    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    for ax, col in zip(axes.ravel(), feats):
        sns.boxplot(
            x=master["at_risk"].map(CLASS_LABELS),
            y=master[col],
            ax=ax,
            hue=master["at_risk"].map(CLASS_LABELS),
            palette={
                CLASS_LABELS[0]: CLASS_COLOURS[0],
                CLASS_LABELS[1]: CLASS_COLOURS[1],
            },
            legend=False,
        )
        ax.set_title(f"{col} by class")
        ax.set_xlabel("")
    fig.suptitle(
        "Bivariate analysis: numeric features by at-risk class", fontweight="bold"
    )
    savefig(fig, "bivar_numeric_by_label")
    plt.close(fig)

    # Discriminative power: standardised mean difference (|Cohen's d|).
    disc = {}
    g1 = master[master["at_risk"] == 1]
    g0 = master[master["at_risk"] == 0]
    for col in NUMERIC_MAIN:
        m1, m0 = g1[col].mean(), g0[col].mean()
        s = np.sqrt((g1[col].var() + g0[col].var()) / 2) or 1.0
        disc[col] = round(abs(m1 - m0) / s, 3)
    disc = dict(sorted(disc.items(), key=lambda kv: kv[1], reverse=True))

    # At-risk rate across categorical levels.
    fig, axes = plt.subplots(2, 3, figsize=(18, 9))
    for ax, col in zip(axes.ravel(), CATEGORICAL_MAIN):
        rate = master.groupby(col)["at_risk"].mean().sort_values()
        ax.barh(rate.index.astype(str), rate.values, color=CLASS_COLOURS[1])
        ax.axvline(master["at_risk"].mean(), color="grey", ls="--", lw=1)
        ax.set_title(f"At-risk rate by {col}")
        ax.set_xlabel("At-risk rate")
    fig.suptitle(
        "At-risk rate across categorical features (dashed = overall rate)",
        fontweight="bold",
    )
    savefig(fig, "bivar_atrisk_rate_by_category")
    plt.close(fig)

    return {
        "discriminative_power_cohens_d": disc,
        "top5_discriminative": list(disc)[:5],
    }


# --- Task 37: correlation analysis -------------------------------------------
def correlation_analysis(master: pd.DataFrame) -> dict:
    apply_style()
    import seaborn as sns

    num = master[NUMERIC_MAIN + ["at_risk"]]
    for method, fname in [("pearson", "corr_pearson"), ("spearman", "corr_spearman")]:
        corr = num.corr(method=method)
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(
            corr,
            annot=True,
            fmt=".2f",
            cmap="vlag",
            center=0,
            ax=ax,
            cbar_kws={"label": f"{method.title()} r"},
        )
        ax.set_title(f"{method.title()} correlation matrix")
        savefig(fig, fname)
        plt.close(fig)

    pear = num.corr("pearson")
    pairs = (
        pear.where(~np.eye(len(pear), dtype=bool))
        .abs()
        .unstack()
        .dropna()
        .sort_values(ascending=False)
    )
    strong = [
        (a, b, round(pear.loc[a, b], 3))
        for (a, b), v in pairs.items()
        if a < b and v >= 0.6
    ]
    target_corr = pear["at_risk"].drop("at_risk").abs().sort_values(ascending=False)
    leakage_flags = [c for c, v in target_corr.items() if v >= 0.95]

    # Scatter of the strongest feature-feature pair.
    if strong:
        a, b, r = strong[0]
        fig, ax = plt.subplots()
        ax.scatter(master[a], master[b], s=5, alpha=0.2, color=CLASS_COLOURS[0])
        ax.set_xlabel(a)
        ax.set_ylabel(b)
        ax.set_title(f"{a} vs {b} (Pearson r={r})")
        savefig(fig, "corr_scatter_top_pair")
        plt.close(fig)

    return {
        "strong_pairs_ge_0.6": strong[:12],
        "top_target_corr": target_corr.head(8).round(3).to_dict(),
        "leakage_suspects_ge_0.95": leakage_flags,
    }


# --- Task 38: time-aware EDA across checkpoints ------------------------------
def time_trends(checkpoints: pd.DataFrame | None) -> dict:
    if checkpoints is None:
        return {"status": "checkpoints_not_found"}
    apply_style()

    feats = ["total_clicks", "n_days_active", "mean_score_to_date"]
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    summary = {}
    for ax, col in zip(axes, feats):
        grp = checkpoints.groupby(["t_percent", "at_risk"])[col].mean().unstack()
        for label in (0, 1):
            ax.plot(
                grp.index,
                grp[label],
                marker="o",
                color=CLASS_COLOURS[label],
                label=CLASS_LABELS[label],
            )
        ax.set_title(f"Mean {col} by checkpoint")
        ax.set_xlabel("Course progress (%)")
        ax.set_ylabel(f"Mean {col}")
        ax.legend()
        gap = (grp[0] - grp[1]).abs()
        summary[col] = {int(t): round(float(gap.loc[t]), 2) for t in gap.index}
    fig.suptitle("Time-aware behaviour by class across checkpoints", fontweight="bold")
    savefig(fig, "time_trends_by_label")
    plt.close(fig)
    return {"mean_gap_by_checkpoint": summary}


def run_all() -> dict:
    plt.switch_backend("Agg")
    master = load_master()
    findings = {
        "class_distribution": class_distribution(master),
        "descriptive_stats": descriptive_stats(master),
        "bivariate": bivariate_analysis(master),
        "correlation": correlation_analysis(master),
        "time_trends": time_trends(load_checkpoints()),
    }
    distribution_plots(master)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORTS_DIR / "eda_findings.json", "w", encoding="utf-8") as f:
        json.dump(findings, f, ensure_ascii=False, indent=2)
    return findings


if __name__ == "__main__":
    out = run_all()
    print(json.dumps(out, ensure_ascii=False, indent=2))
