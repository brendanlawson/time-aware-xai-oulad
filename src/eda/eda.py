"""Exploratory Data Analysis for Chapter 4 — professional, statistically grounded.

Covers the Task 3 EDA work items at the depth expected for an IEEE-style report:
data-quality profiling, univariate description with shape statistics, bivariate
analysis backed by hypothesis tests and effect sizes, multivariate correlation
with a leakage check, and a time-aware discrimination analysis that tracks how
class separability grows across the six checkpoints (directly informing RQ1).

Each function returns a findings dict and writes figures to reports/figures/ and
result tables to reports/tables/. The 02_eda notebook narrates these outputs.

Run:  python -m src.eda.eda
"""

from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
import seaborn as sns

from src.config import (
    CHECKPOINTS,
    CHECKPOINTS_DIR,
    INTERIM_DATA_DIR,
    RANDOM_SEED,
    REPORTS_DIR,
    TABLES_DIR,
)
from src.eda.plot_style import (
    CLASS_COLOURS,
    CLASS_LABELS,
    apply_style,
    savefig,
    tidy_axis,
)

# Feature groups (used to colour plots and aggregate discrimination by group).
DEMOGRAPHIC_NUM = ["num_of_prev_attempts", "studied_credits", "date_registration"]
ENGAGEMENT_NUM = [
    "total_clicks",
    "n_days_active",
    "max_clicks_single_day",
    "mean_clicks_per_active_day",
    "days_since_last_activity",
    "clicks_forumng",
    "clicks_oucontent",
    "clicks_resource",
    "clicks_homepage",
    "clicks_oucollaborate",
    "clicks_quiz",
    "clicks_subpage",
    "clicks_url",
]
PERFORMANCE_NUM = [
    "mean_score_to_date",
    "weighted_score_to_date",
    "n_assessments_submitted",
]
NUMERIC_ALL = DEMOGRAPHIC_NUM + ENGAGEMENT_NUM + PERFORMANCE_NUM
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

GROUP_OF = {
    **{c: "Demographic" for c in DEMOGRAPHIC_NUM},
    **{c: "Engagement" for c in ENGAGEMENT_NUM},
    **{c: "Performance" for c in PERFORMANCE_NUM},
}
GROUP_COLOUR = {
    "Demographic": "#7F8C8D",
    "Engagement": "#C0392B",
    "Performance": "#2166AC",
}


# --- loaders ------------------------------------------------------------------
def load_master(path=INTERIM_DATA_DIR / "master_raw.parquet") -> pd.DataFrame:
    return pd.read_parquet(path)


def load_checkpoints(checkpoints_dir=CHECKPOINTS_DIR) -> "pd.DataFrame | None":
    frames = []
    for t in CHECKPOINTS:
        p = checkpoints_dir / f"dataset_t{t}.parquet"
        if not p.exists():
            return None
        frames.append(pd.read_parquet(p))
    return pd.concat(frames, ignore_index=True)


# --- helpers ------------------------------------------------------------------
def _save_table(df: pd.DataFrame, name: str, index: bool = True) -> None:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(TABLES_DIR / f"{name}.csv", index=index, encoding="utf-8-sig")


def _cohens_d(a: pd.Series, b: pd.Series) -> float:
    """Pooled-SD standardised mean difference |Cohen's d|."""
    va, vb = a.var(ddof=1), b.var(ddof=1)
    pooled = np.sqrt((va + vb) / 2) or 1.0
    return float(abs(a.mean() - b.mean()) / pooled)


def _benjamini_hochberg(pvals: list[float]) -> list[float]:
    """BH-adjusted p-values (q-values) controlling the false discovery rate."""
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order] * n / (np.arange(n) + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(n)
    out[order] = np.clip(ranked, 0, 1)
    return out.tolist()


def _cramers_v(confusion: np.ndarray) -> float:
    chi2 = stats.chi2_contingency(confusion)[0]
    n = confusion.sum()
    r, k = confusion.shape
    return float(np.sqrt(chi2 / (n * (min(r, k) - 1)))) if min(r, k) > 1 else 0.0


# --------------------------------------------------------------------------- #
# 1. Data-quality profile (missingness, dtypes)
# --------------------------------------------------------------------------- #
def data_quality(master: pd.DataFrame) -> dict:
    apply_style()
    miss = master.isnull().sum()
    profile = pd.DataFrame(
        {
            "dtype": master.dtypes.astype(str),
            "n_missing": miss,
            "pct_missing": (miss / len(master) * 100).round(2),
            "n_unique": master.nunique(),
        }
    ).sort_values("pct_missing", ascending=False)
    _save_table(profile, "data_quality_profile")

    miss_cols = profile[profile["n_missing"] > 0]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(miss_cols.index[::-1], miss_cols["pct_missing"][::-1], color=CLASS_COLOURS[1])
    ax.set_xlabel("% missing")
    ax.set_title("Missing values by column (only columns with gaps)")
    savefig(fig, "quality_missingness")
    plt.close(fig)
    return {
        "n_records": int(len(master)),
        "n_columns": int(master.shape[1]),
        "columns_with_missing": miss_cols["n_missing"].to_dict(),
    }


# --------------------------------------------------------------------------- #
# 2. Univariate description (numeric shape + categorical frequency)
# --------------------------------------------------------------------------- #
def univariate(master: pd.DataFrame) -> dict:
    apply_style()
    desc = master[NUMERIC_ALL].describe().T
    desc["median"] = master[NUMERIC_ALL].median()
    desc["mode"] = master[NUMERIC_ALL].mode().iloc[0]
    desc["skew"] = master[NUMERIC_ALL].skew()
    desc["kurtosis"] = master[NUMERIC_ALL].kurtosis()
    desc = desc.round(3)
    _save_table(desc, "univariate_numeric")

    for col in CATEGORICAL_MAIN:
        freq = master[col].value_counts(dropna=False).rename_axis(col).reset_index(name="count")
        freq["pct"] = (freq["count"] / len(master) * 100).round(2)
        _save_table(freq, f"freq_{col}", index=False)

    # Histograms + KDE for the main numeric features, coloured by group.
    fig, axes = plt.subplots(2, 5, figsize=(20, 8.6), constrained_layout=True)
    for ax, col in zip(axes.ravel(), NUMERIC_MAIN):
        sns.histplot(
            master[col],
            kde=True,
            ax=ax,
            color=GROUP_COLOUR[GROUP_OF[col]],
            edgecolor="white",
            linewidth=0.3,
            alpha=0.9,
        )
        ax.set_title(col, fontsize=11)
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.text(
            0.95,
            0.93,
            f"skew {master[col].skew():.1f}",
            transform=ax.transAxes,
            ha="right",
            va="top",
            fontsize=8.5,
            color="#555555",
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#CCCCCC", lw=0.6),
        )
        tidy_axis(ax, nbins=4)
    fig.suptitle(
        "Univariate distributions of numeric features (histogram + KDE)\n"
        "colour = feature group — Engagement (red) · Performance (blue) · Demographic (grey)",
        fontweight="bold",
    )
    savefig(fig, "univariate_hist_kde")
    plt.close(fig)

    fig, axes = plt.subplots(2, 5, figsize=(20, 8.6), constrained_layout=True)
    for ax, col in zip(axes.ravel(), NUMERIC_MAIN):
        sns.boxplot(y=master[col], ax=ax, color=GROUP_COLOUR[GROUP_OF[col]])
        ax.set_title(col, fontsize=10)
        ax.set_ylabel("")
    fig.suptitle("Univariate boxplots (IQR outlier inspection)", fontweight="bold")
    savefig(fig, "univariate_boxplots")
    plt.close(fig)

    # Categorical frequency grid.
    fig, axes = plt.subplots(2, 3, figsize=(18, 10.5), constrained_layout=True)
    for ax, col in zip(axes.ravel(), CATEGORICAL_MAIN):
        vc = master[col].value_counts().sort_values()
        ax.barh(vc.index.astype(str), vc.values, color="#4D4D4D")
        ax.set_title(f"{col} ({master[col].nunique()} levels)")
        ax.tick_params(axis="y", labelsize=8)
        sns.despine(ax=ax)
    fig.suptitle("Categorical frequency distributions", fontweight="bold")
    savefig(fig, "univariate_categorical_freq")
    plt.close(fig)

    return {
        "most_skewed": desc["skew"].abs().sort_values(ascending=False).head(5).round(2).to_dict(),
        "most_leptokurtic": desc["kurtosis"]
        .sort_values(ascending=False)
        .head(5)
        .round(2)
        .to_dict(),
    }


# --------------------------------------------------------------------------- #
# 3. Target / class distribution
# --------------------------------------------------------------------------- #
def target_distribution(master: pd.DataFrame) -> dict:
    apply_style()
    counts = master["final_result"].value_counts()
    rate = float(master["at_risk"].mean())
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), constrained_layout=True)
    order = ["Distinction", "Pass", "Fail", "Withdrawn"]
    axes[0].bar(
        order,
        [counts.get(k, 0) for k in order],
        color=[CLASS_COLOURS[0], CLASS_COLOURS[0], CLASS_COLOURS[1], CLASS_COLOURS[1]],
    )
    axes[0].set_title("final_result")
    axes[0].set_ylabel("Students")
    axes[0].tick_params(axis="x", rotation=20)
    binary = master["at_risk"].map(CLASS_LABELS).value_counts()
    axes[1].bar(
        binary.index,
        binary.values,
        color=[CLASS_COLOURS[1] if "At" in i else CLASS_COLOURS[0] for i in binary.index],
    )
    axes[1].set_title(f"at_risk (positive rate = {rate:.1%})")
    fig.suptitle("Target distribution and class imbalance", fontweight="bold")
    savefig(fig, "target_distribution")
    plt.close(fig)
    return {
        "final_result_counts": counts.to_dict(),
        "at_risk_rate": round(rate, 4),
        "imbalance_ratio": round(rate / (1 - rate), 3),
    }


# --------------------------------------------------------------------------- #
# 4. Bivariate: numeric features vs target (effect size + hypothesis test)
# --------------------------------------------------------------------------- #
def numeric_vs_target(master: pd.DataFrame) -> dict:
    apply_style()
    g1 = master[master["at_risk"] == 1]
    g0 = master[master["at_risk"] == 0]

    rows, pvals = [], []
    for col in NUMERIC_ALL:
        a, b = (
            g1[col].dropna(),
            g0[col].dropna(),
        )  # master_raw has a few raw NaNs (e.g. date_registration)
        d = _cohens_d(a, b)
        u, p = stats.mannwhitneyu(a, b, alternative="two-sided")
        rows.append(
            {
                "feature": col,
                "group": GROUP_OF[col],
                "mean_not_at_risk": round(b.mean(), 3),
                "mean_at_risk": round(a.mean(), 3),
                "cohens_d": round(d, 3),
                "mannwhitney_U": float(u),
                "p_value": p,
            }
        )
        pvals.append(p)
    table = pd.DataFrame(rows)
    table["p_adj_bh"] = _benjamini_hochberg(pvals)
    table["significant_(q<0.05)"] = table["p_adj_bh"] < 0.05
    table = table.sort_values("cohens_d", ascending=False).reset_index(drop=True)
    _save_table(table, "bivariate_numeric_tests", index=False)

    # Effect-size figure (ranked |Cohen's d|, coloured by group, values labelled).
    fig, ax = plt.subplots(figsize=(9.5, 7))
    t = table.iloc[::-1]
    bars = ax.barh(
        t["feature"],
        t["cohens_d"],
        color=[GROUP_COLOUR[g] for g in t["group"]],
        edgecolor="white",
        linewidth=0.4,
    )
    ax.bar_label(bars, fmt="%.2f", padding=3, fontsize=8, color="#333333")
    for x, ls in [(0.2, ":"), (0.5, "--"), (0.8, "-")]:
        ax.axvline(x, color="grey", ls=ls, lw=1)
    ax.set_xlim(0, float(t["cohens_d"].max()) * 1.12)
    ax.set_xlabel("|Cohen's d|  (dotted .2 small · dashed .5 medium · solid .8 large)")
    ax.set_title("Discriminative power of numeric features (at-risk vs not-at-risk)")
    handles = [
        plt.Rectangle((0, 0), 1, 1, color=GROUP_COLOUR[g])
        for g in ("Engagement", "Performance", "Demographic")
    ]
    ax.legend(
        handles,
        ("Engagement", "Performance", "Demographic"),
        loc="lower right",
        title="Feature group",
    )
    sns.despine(ax=ax)
    savefig(fig, "bivariate_effect_sizes")
    plt.close(fig)

    # Boxplots of the six strongest features.
    top = table.head(6)["feature"].tolist()
    fig, axes = plt.subplots(2, 3, figsize=(16, 9), constrained_layout=True)
    for ax, col in zip(axes.ravel(), top):
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
        ax.set_title(col)
        ax.set_xlabel("")
    fig.suptitle("Six most discriminative numeric features by class", fontweight="bold")
    savefig(fig, "bivariate_top_boxplots")
    plt.close(fig)

    return {
        "top5_by_cohens_d": table.head(5)[["feature", "cohens_d", "p_adj_bh"]].to_dict("records"),
        "n_significant": int(table["significant_(q<0.05)"].sum()),
        "n_tested": int(len(table)),
    }


# --------------------------------------------------------------------------- #
# 5. Bivariate: categorical features vs target (chi-square + Cramer's V)
# --------------------------------------------------------------------------- #
def categorical_vs_target(master: pd.DataFrame) -> dict:
    apply_style()
    rows = []
    for col in CATEGORICAL_MAIN:
        ct = pd.crosstab(master[col].fillna("Unknown"), master["at_risk"])
        chi2, p, dof, _ = stats.chi2_contingency(ct)
        rows.append(
            {
                "feature": col,
                "chi2": round(chi2, 2),
                "dof": dof,
                "p_value": p,
                "cramers_v": round(_cramers_v(ct.values), 3),
            }
        )
    table = pd.DataFrame(rows).sort_values("cramers_v", ascending=False).reset_index(drop=True)
    _save_table(table, "bivariate_categorical_tests", index=False)

    overall = master["at_risk"].mean()
    fig, axes = plt.subplots(2, 3, figsize=(18, 10.5), constrained_layout=True)
    for ax, col in zip(axes.ravel(), CATEGORICAL_MAIN):
        rate = master.groupby(col)["at_risk"].mean().sort_values()
        v = table.loc[table["feature"] == col, "cramers_v"].iloc[0]
        ax.barh(rate.index.astype(str), rate.values, color=CLASS_COLOURS[1])
        ax.axvline(overall, color="grey", ls="--", lw=1)
        ax.set_title(f"At-risk rate by {col}  (Cramer's V={v})")
        ax.set_xlabel("At-risk rate")
        ax.tick_params(axis="y", labelsize=8)
        sns.despine(ax=ax)
    fig.suptitle(
        "At-risk rate across categorical levels (dashed = overall 52.8%)",
        fontweight="bold",
    )
    savefig(fig, "bivariate_categorical_rate")
    plt.close(fig)
    return {"association_cramers_v": table.set_index("feature")["cramers_v"].to_dict()}


# --------------------------------------------------------------------------- #
# 6. Multivariate: correlation, multicollinearity, leakage check
# --------------------------------------------------------------------------- #
def correlation(master: pd.DataFrame) -> dict:
    apply_style()
    num = master[NUMERIC_MAIN + ["at_risk"]]
    for method, fname in [("pearson", "corr_pearson"), ("spearman", "corr_spearman")]:
        corr = num.corr(method=method)
        fig, ax = plt.subplots(figsize=(10.5, 8.5))
        sns.heatmap(
            corr,
            annot=True,
            fmt=".2f",
            cmap="RdBu_r",
            center=0,
            vmin=-1,
            vmax=1,
            square=True,
            linewidths=0.5,
            linecolor="white",
            annot_kws={"size": 8},
            cbar_kws={"label": f"{method.title()} r", "shrink": 0.82},
            ax=ax,
        )
        ax.set_title(f"{method.title()} correlation of numeric features (incl. at_risk)", pad=12)
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        plt.setp(ax.get_yticklabels(), rotation=0)
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
        {"a": a, "b": b, "r": round(pear.loc[a, b], 3)}
        for (a, b), v in pairs.items()
        if a < b and v >= 0.6
    ]
    _save_table(pd.DataFrame(strong), "correlation_strong_pairs", index=False)

    target_corr = pear["at_risk"].drop("at_risk").sort_values(key=np.abs, ascending=False)
    _save_table(
        target_corr.round(3).rename("pearson_r_with_at_risk").to_frame(),
        "correlation_with_target",
    )
    fig, ax = plt.subplots(figsize=(8, 6))
    tc = target_corr.iloc[::-1]
    ax.barh(
        tc.index,
        tc.values,
        color=[CLASS_COLOURS[1] if v > 0 else CLASS_COLOURS[0] for v in tc.values],
    )
    ax.set_xlabel("Pearson r with at_risk")
    ax.set_title("Correlation of numeric features with the target")
    savefig(fig, "corr_with_target")
    plt.close(fig)

    # Scatter views of the strongest numeric-numeric pairs (Chart_Standards:
    # bivariate numeric vs numeric -> scatter, alpha=0.4), class-coloured on a
    # fixed-seed 4,000-row sample so the figure stays readable and reproducible.
    top_pairs = [p for p in strong if "at_risk" not in (p["a"], p["b"])][:4]
    if top_pairs:
        rng = np.random.RandomState(RANDOM_SEED)
        sample = master.iloc[rng.choice(len(master), size=min(4000, len(master)), replace=False)]
        fig, axes = plt.subplots(2, 2, figsize=(12, 9.5), constrained_layout=True)
        for ax, p in zip(axes.ravel(), top_pairs):
            for cls in (0, 1):
                part = sample[sample["at_risk"] == cls]
                ax.scatter(
                    part[p["a"]],
                    part[p["b"]],
                    s=8,
                    alpha=0.4,
                    color=CLASS_COLOURS[cls],
                    label=CLASS_LABELS[cls],
                    linewidths=0,
                )
            ax.set_xlabel(p["a"])
            ax.set_ylabel(p["b"])
            ax.set_title(f"Pearson r = {p['r']:.2f}", fontsize=10)
            tidy_axis(ax, nbins=5)
        handles, labels = axes.ravel()[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="upper right", ncols=2)
        fig.suptitle(
            "Strongest numeric-numeric relationships (scatter, 4,000-row sample)",
            fontweight="bold",
        )
        savefig(fig, "bivariate_scatter_pairs")
        plt.close(fig)

    multicollinear = [p for p in strong if abs(p["r"]) >= 0.8]
    leakage = [c for c, v in target_corr.abs().items() if v >= 0.95]
    return {
        "strong_pairs_ge_0.6": strong[:12],
        "multicollinear_ge_0.8": multicollinear,
        "top_target_corr": target_corr.abs().head(8).round(3).to_dict(),
        "leakage_suspects_ge_0.95": leakage,
    }


# --------------------------------------------------------------------------- #
# 7. Time-aware analysis: how class separability grows across checkpoints
# --------------------------------------------------------------------------- #
def time_aware(checkpoints: "pd.DataFrame | None") -> dict:
    if checkpoints is None:
        return {"status": "checkpoints_not_found"}
    apply_style()
    feats = [
        "total_clicks",
        "n_days_active",
        "mean_score_to_date",
        "n_assessments_submitted",
    ]

    # (a) Mean trajectory by class.
    fig, axes = plt.subplots(1, 4, figsize=(22, 5), constrained_layout=True)
    for ax, col in zip(axes, feats):
        grp = checkpoints.groupby(["t_percent", "at_risk"])[col].mean().unstack()
        for lab in (0, 1):
            ax.plot(
                grp.index,
                grp[lab],
                marker="o",
                color=CLASS_COLOURS[lab],
                label=CLASS_LABELS[lab],
            )
        ax.set_title(f"Mean {col}")
        ax.set_xlabel("Course progress (%)")
        ax.legend()
    fig.suptitle("Mean feature trajectory by class across checkpoints", fontweight="bold")
    savefig(fig, "time_mean_trajectory")
    plt.close(fig)

    # (b) Discrimination curve: |Cohen's d| per feature at each checkpoint (RQ1).
    disc_rows = []
    for t in CHECKPOINTS:
        sub = checkpoints[checkpoints["t_percent"] == t]
        g1, g0 = sub[sub["at_risk"] == 1], sub[sub["at_risk"] == 0]
        for col in feats + ["days_since_last_activity", "weighted_score_to_date"]:
            disc_rows.append(
                {
                    "t_percent": t,
                    "feature": col,
                    "cohens_d": round(_cohens_d(g1[col], g0[col]), 3),
                }
            )
    disc = pd.DataFrame(disc_rows)
    _save_table(
        disc.pivot(index="t_percent", columns="feature", values="cohens_d"),
        "discrimination_by_checkpoint",
    )
    fig, ax = plt.subplots(figsize=(10, 6))
    for col in disc["feature"].unique():
        s = disc[disc["feature"] == col]
        ax.plot(s["t_percent"], s["cohens_d"], marker="o", label=col)
    ax.axhline(0.8, color="grey", ls="--", lw=1)
    ax.set_xlabel("Course progress (%)")
    ax.set_ylabel("|Cohen's d| (class separability)")
    ax.set_title("How feature discrimination grows across checkpoints (RQ1)")
    ax.legend(fontsize=8, ncol=2)
    savefig(fig, "time_discrimination_curve")
    plt.close(fig)

    earliest = {}
    for col in disc["feature"].unique():
        s = disc[disc["feature"] == col].sort_values("t_percent")
        hit = s[s["cohens_d"] >= 0.8]
        earliest[col] = int(hit["t_percent"].iloc[0]) if len(hit) else None
    return {
        "discrimination_by_checkpoint": disc.pivot(
            index="t_percent", columns="feature", values="cohens_d"
        ).to_dict(),
        "earliest_checkpoint_d_ge_0.8": earliest,
    }


# --------------------------------------------------------------------------- #
# 8. Withdrawn-specific analysis (Option A early-warning signal)
# --------------------------------------------------------------------------- #
def withdrawn_analysis(master: pd.DataFrame) -> dict:
    apply_style()
    m = master.copy()
    m["status"] = np.where(
        m["final_result"] == "Withdrawn",
        "Withdrawn",
        np.where(m["at_risk"] == 1, "Fail", "Not-at-risk"),
    )
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)
    sns.boxplot(
        x="status",
        y="days_since_last_activity",
        data=m,
        ax=axes[0],
        order=["Not-at-risk", "Fail", "Withdrawn"],
        color=CLASS_COLOURS[1],
    )
    axes[0].set_title("Inactivity gap by outcome")
    sns.boxplot(
        x="status",
        y="total_clicks",
        data=m,
        ax=axes[1],
        order=["Not-at-risk", "Fail", "Withdrawn"],
        color=CLASS_COLOURS[0],
    )
    axes[1].set_title("Total clicks by outcome")
    fig.suptitle(
        "Withdrawn students: the activity-decay early-warning signal (Option A)",
        fontweight="bold",
    )
    savefig(fig, "withdrawn_activity_decay")
    plt.close(fig)
    return {
        "median_days_since_last_activity": m.groupby("status")["days_since_last_activity"]
        .median()
        .round(1)
        .to_dict(),
        "median_total_clicks": m.groupby("status")["total_clicks"].median().round(1).to_dict(),
    }


def run_all() -> dict:
    """Apply the style, load data, run every analysis, dump a findings JSON."""
    plt.switch_backend("Agg")
    master = load_master()
    checkpoints = load_checkpoints()
    findings = {
        "data_quality": data_quality(master),
        "univariate": univariate(master),
        "target_distribution": target_distribution(master),
        "numeric_vs_target": numeric_vs_target(master),
        "categorical_vs_target": categorical_vs_target(master),
        "correlation": correlation(master),
        "time_aware": time_aware(checkpoints),
        "withdrawn_analysis": withdrawn_analysis(master),
    }
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORTS_DIR / "eda_findings.json", "w", encoding="utf-8") as f:
        json.dump(findings, f, ensure_ascii=False, indent=2)
    return findings


if __name__ == "__main__":
    print(json.dumps(run_all(), ensure_ascii=False, indent=2))
