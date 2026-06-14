"""Generate the two deliverable notebooks as IEEE-style analytical reports.

The notebooks are thin over the tested src/ modules (so code/figures never drift)
but carry full narrative: abstract, numbered sections, interpretation after every
result, and references — matching the schema-survey notebook's standard.

Run:  python tools/build_notebooks.py
"""

from pathlib import Path

import nbformat as nbf
from nbformat.v4 import new_code_cell, new_markdown_cell, new_raw_cell

NB_DIR = Path(__file__).resolve().parents[1] / "notebooks"

BOOT = (
    "import sys, json\n"
    "from pathlib import Path\n"
    "import pandas as pd\n"
    "from IPython.display import Image, display\n"
    "ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()\n"
    "sys.path.insert(0, str(ROOT))\n"
    "TABLES = ROOT / 'reports' / 'tables'\n"
    "FIGS = ROOT / 'reports' / 'figures'\n"
)


def quarto_header(title: str, abstract: str, stt: str) -> str:
    return (
        "---\n"
        f'title: "{title}"\n'
        f'subtitle: "{stt} — DSP391m Capstone, Group 1, FPT University"\n'
        "author:\n  - name: Group 1 (DSP391m)\n    affiliation: FPT University\n"
        "date: last-modified\n"
        f"abstract: |\n  {abstract}\n"
        "number-sections: true\n"
        "format:\n  ieee-pdf:\n    pdf-engine: xelatex\n  ieee-html: default\n"
        "---"
    )


def show_fig(name: str) -> str:
    return f"display(Image(filename=str(FIGS / '{name}.png')))"


# =========================================================================== #
# Notebook 01 — Build master table (data collection, integration, cleaning)
# =========================================================================== #
nb01 = nbf.v4.new_notebook()
nb01.cells = [
    new_raw_cell(
        quarto_header(
            "Data Collection, Integration and Cleaning: Building the OULAD Master Table",
            "We document the reproducible construction of the analysis-ready master table for "
            "early at-risk student prediction on OULAD. Seven relational tables are integrated at "
            "the student-module-presentation grain through audited left-joins, the binary at-risk "
            "label is fixed per the Step-0 agreement, three feature groups are engineered, and the "
            "result is cleaned (deduplication, consistency, missing-value and outlier handling). "
            "Every join preserves the 32,593-record population and the pipeline re-runs end-to-end "
            "without manual intervention.",
            "Report 2 · Chapter 3 · STT 2-6",
        )
    ),
    new_markdown_cell(
        "# Introduction\n\n"
        "Predicting at-risk students early enables timely intervention but requires an "
        "analysis-ready table that integrates demographic, behavioural and assessment evidence "
        "without temporal or group leakage. This notebook builds that table from the seven raw "
        "OULAD CSVs and is the executable counterpart of the Chapter-3 deliverables (data "
        "specification, collection, cleaning). It calls the tested modules in `src/data` so the "
        "notebook and the committed code cannot drift.\n\n"
        "**Target definition (Step-0, Option A).** `at_risk = 1` if `final_result ∈ {Fail, "
        "Withdrawn}`, else `0`; the label is fixed across all checkpoints."
    ),
    new_code_cell(
        BOOT
        + "from src.data.build_master_table import build_master\nfrom src.data.io_utils import INTERIM_DIR"
    ),
    new_markdown_cell(
        "# Method: integration at the student-module-presentation grain\n\n"
        "`studentInfo` is the base table (one row per `id_student × code_module × "
        "code_presentation`). Registration, the aggregated engagement features (from the "
        "10.6M-row `studentVle` clickstream) and the aggregated performance features (from "
        "`studentAssessment`) are attached by **left joins**, each validated `many_to_one`. A "
        "before/after row-count log proves no duplication or loss."
    ),
    new_code_cell(
        "master = build_master(rebuild_engagement=False)\nprint('master_raw:', master.shape)"
    ),
    new_markdown_cell(
        "# Join-integrity evidence\n\n"
        "The join log below shows every step preserves exactly 32,593 records — confirming the "
        "aggregation collapsed the one-to-many event tables to the student grain *before* "
        "joining, so no row was duplicated."
    ),
    new_code_cell(
        "# Table 1 — Join log (every step preserves 32,593 records)\ndisplay(pd.read_csv(INTERIM_DIR / 'master_join_log.csv'))"
    ),
    new_markdown_cell(
        "# Cleaning: deduplication, consistency, missing values, outliers\n\n"
        "Cleaning is applied per the cleaning-methods analysis (`docs/03_cleaning`): duplicate "
        "composite keys are dropped (0 remain); categorical text is standardised; `imd_band` "
        "gaps become `Unknown`; assessment gaps become 0 plus the informative `not_submitted` "
        "flag; outliers are transformed (log1p / winsorize), never deleted. The cleaning log "
        "records the categorical cardinalities."
    ),
    new_code_cell("display(pd.read_csv(INTERIM_DIR / 'master_cleaning_log.csv'))"),
    new_markdown_cell(
        "# Output validation\n\n"
        "We confirm the population size, the absence of duplicate keys, and the fixed at-risk "
        "rate, then preview the analysis-ready table."
    ),
    new_code_cell(
        "print('rows:', len(master), '| columns:', master.shape[1])\n"
        "print('at_risk rate: {:.1%}'.format(master['at_risk'].mean()))\n"
        "key = ['code_module','code_presentation','id_student']\n"
        "assert len(master) == 32593 and master.duplicated(key).sum() == 0\n"
        "print('OK — 32,593 unique student-module-presentation records, no duplicate keys')\n"
        "master.head(3)"
    ),
    new_markdown_cell(
        "# Conclusion\n\n"
        "The master table (32,593 × 33) integrates the three feature groups and the fixed label "
        "with audited integrity, and is the single input to the time-aware checkpoint generation "
        "(`src/data/make_checkpoints`) and the EDA (notebook 02). *Restart & Run All* reproduces "
        "it from the raw CSVs without manual steps."
    ),
]

# =========================================================================== #
# Notebook 02 — Exploratory Data Analysis (Chapter 4)
# =========================================================================== #
ABSTRACT_02 = (
    "We present an exploratory analysis of the OULAD master table for early at-risk prediction. "
    "Beyond visual summaries, every comparison is supported by an appropriate statistic: "
    "Mann-Whitney U tests with Benjamini-Hochberg correction and Cohen's d for numeric features, "
    "chi-square tests with Cramer's V for categorical features, and Pearson/Spearman correlation "
    "with an explicit leakage check. A time-aware analysis tracks how class separability grows "
    "across the six checkpoints, identifying the earliest reliable prediction point (RQ1). We "
    "find that behavioural and performance features dominate (all 19 numeric features are "
    "significant; the strongest reach Cohen's d > 2), demographic association is weak "
    "(Cramer's V <= 0.15), no feature leaks the label (|r| < 0.95), and the at-risk signal is "
    "already strong by 20-40% of course length."
)

nb02 = nbf.v4.new_notebook()
nb02.cells = [
    new_raw_cell(
        quarto_header(
            "Exploratory Data Analysis of the OULAD Master Table for Early At-Risk Prediction",
            ABSTRACT_02,
            "Report 2 · Chapter 4 · STT 27-28, 35-38",
        )
    ),
    new_markdown_cell(
        "# Introduction\n\n"
        "Exploratory Data Analysis (EDA) characterises the data before modelling: its quality, "
        "the shape of each variable, which variables separate at-risk from not-at-risk students, "
        "how variables relate to one another, and — because this is a *time-aware* problem — when "
        "the predictive signal emerges. These observations directly inform the three research "
        "questions: the earliest reliable checkpoint and best algorithm (**RQ1**), the features "
        "whose importance SHAP/LIME should later explain stably (**RQ2**), and the class balance "
        "that motivates the imbalance study (**RQ3**)."
    ),
    new_markdown_cell(
        "# Data and statistical method\n\n"
        "The analysis uses the master table (t = 100%) for univariate, bivariate and correlation "
        "analysis, and the six checkpoint datasets for the time-aware analysis. To move beyond "
        "visual impression we apply: the **Mann-Whitney U** test (non-parametric, appropriate for "
        "the right-skewed features) with **Benjamini-Hochberg** false-discovery-rate correction "
        "and **Cohen's d** effect size for numeric-vs-target comparisons; the **chi-square** test "
        "of independence with **Cramer's V** effect size for categorical-vs-target association; "
        "and **Pearson/Spearman** correlation for multivariate structure. All charts follow the "
        "team chart standard (`docs/standards`)."
    ),
    new_code_cell(
        BOOT
        + "from src.eda import eda\nmaster = eda.load_master()\ncheckpoints = eda.load_checkpoints()\nprint('master:', master.shape, '| checkpoints stacked:', None if checkpoints is None else checkpoints.shape)"
    ),
    new_markdown_cell(
        "# Data quality\n\n"
        "Only three columns contain missing values: `date_unregistration` (structurally absent "
        "for students who never withdraw — not a feature), `imd_band` (1,111; filled `Unknown`), "
        "and `date_registration` (45; train-median imputed). No feature column is materially "
        "incomplete."
    ),
    new_code_cell(
        "print(json.dumps(eda.data_quality(master), indent=2))\n"
        + show_fig("quality_missingness")
    ),
    new_markdown_cell(
        "# Univariate analysis\n\n"
        "Engagement (clickstream) features are strongly right-skewed and heavy-tailed "
        "(`clicks_resource` skew ≈ 35, `max_clicks_single_day` ≈ 11), which justifies the "
        "`log1p` transform applied during cleaning. Categorical features are well populated "
        "across their levels."
    ),
    new_code_cell(
        "# Table — numeric descriptive statistics (with skew & kurtosis)\n"
        "print(json.dumps(eda.univariate(master), indent=2, ensure_ascii=False))\n"
        "display(pd.read_csv(TABLES / 'univariate_numeric.csv', index_col=0))"
    ),
    new_code_cell(show_fig("univariate_hist_kde")),
    new_code_cell(show_fig("univariate_boxplots")),
    new_code_cell(show_fig("univariate_categorical_freq")),
    new_markdown_cell(
        "# Target distribution and class imbalance (STT 27)\n\n"
        "The observed at-risk rate is **52.8%** (imbalance ratio 1.12): a *slight majority*, not "
        "the 68/32 shown illustratively on the course slides. Imbalance is therefore mild — which "
        "we report honestly and which frames **RQ3** (resampling may yield only modest gains). PR-AUC "
        "and recall on the at-risk class remain the headline metrics because a missed at-risk "
        "student is the costly error."
    ),
    new_code_cell(
        "print(json.dumps(eda.target_distribution(master), indent=2))\n"
        + show_fig("target_distribution")
    ),
    new_markdown_cell(
        "# Bivariate analysis — numeric features vs the target (STT 36)\n\n"
        "For each numeric feature we test whether its distribution differs by class (Mann-Whitney "
        "U, BH-corrected) and quantify the gap (Cohen's d). **All 19 features are significant** "
        "(q < 0.05) — expected at n ≈ 32k — so effect size, not the p-value, is the discriminator. "
        "The strongest are behavioural/performance: `days_since_last_activity` (d = 2.55), "
        "`n_assessments_submitted` (2.05) and `weighted_score_to_date` (1.96). Demographic features "
        "are weakest (`studied_credits` 0.28, `num_of_prev_attempts` 0.21), empirically reproducing "
        "the prior-work finding that behaviour outweighs demographics."
    ),
    new_code_cell(
        "# Table — effect size + Mann-Whitney U (BH-corrected) per numeric feature\n"
        "print(json.dumps(eda.numeric_vs_target(master), indent=2))\n"
        "display(pd.read_csv(TABLES / 'bivariate_numeric_tests.csv'))"
    ),
    new_code_cell(show_fig("bivariate_effect_sizes")),
    new_code_cell(show_fig("bivariate_top_boxplots")),
    new_markdown_cell(
        "# Bivariate analysis — categorical features vs the target\n\n"
        "Chi-square tests are significant but the **Cramer's V** effect sizes are small: "
        "`highest_education` (0.15) and `imd_band` (0.15) are the strongest demographic "
        "associations, while `gender` (0.02) is negligible. This confirms demographics carry "
        "limited standalone signal and are best retained for fairness analysis rather than "
        "predictive reliance."
    ),
    new_code_cell(
        "print(json.dumps(eda.categorical_vs_target(master), indent=2))\ndisplay(pd.read_csv(TABLES / 'bivariate_categorical_tests.csv'))\n"
        + show_fig("bivariate_categorical_rate")
    ),
    new_markdown_cell(
        "# Multivariate analysis — correlation, multicollinearity, leakage (STT 37)\n\n"
        "Pearson and Spearman matrices agree on the structure. Two pairs are multicollinear "
        "(|r| ≥ 0.8): `n_days_active`–`total_clicks` (0.84) and `days_since_last_activity`–"
        "`n_assessments_submitted` (−0.83); this is relevant to explanation stability (**RQ2**), "
        "since SHAP/LIME may distribute importance among correlated features. Critically, **no "
        "feature correlates ≥ 0.95 with the target**, so no leakage feature is present."
    ),
    new_code_cell("print(json.dumps(eda.correlation(master), indent=2))"),
    new_code_cell(show_fig("corr_pearson")),
    new_code_cell(show_fig("corr_spearman")),
    new_code_cell(show_fig("corr_with_target")),
    new_markdown_cell(
        "# Time-aware analysis — when does the signal emerge? (STT 38, RQ1)\n\n"
        "This is the analysis specific to a time-aware problem. The left panel shows the mean "
        "trajectory of each feature by class across checkpoints; the right panel tracks "
        "**|Cohen's d| per checkpoint** — i.e. how strongly each feature separates the classes as "
        "the course progresses. `n_days_active` already exceeds the large-effect threshold "
        "(d ≥ 0.8) at **10%**; `mean_score_to_date`, `n_assessments_submitted` and "
        "`weighted_score_to_date` cross it by **20%**. The behavioural signal is therefore "
        "actionable from ~20–40% of course length, grounding the RQ1 checkpoint schedule in "
        "evidence rather than convention."
    ),
    new_code_cell(
        "print(json.dumps(eda.time_aware(checkpoints), indent=2))\ndisplay(pd.read_csv(TABLES / 'discrimination_by_checkpoint.csv', index_col=0))"
    ),
    new_code_cell(show_fig("time_mean_trajectory")),
    new_code_cell(show_fig("time_discrimination_curve")),
    new_markdown_cell(
        "# The Withdrawn early-warning signal (Step-0 Option A)\n\n"
        "Under Option A, students who withdrew before a checkpoint are kept and labelled at-risk; "
        "their features reflect only pre-withdrawal activity. The data confirms this is a genuine "
        "signal rather than noise: median inactivity is 11 days for not-at-risk students, 116 for "
        "Fail and **233 for Withdrawn**, while median total clicks fall from 1,425 (not-at-risk) "
        "to 89 (Withdrawn). The activity collapse of withdrawing students is exactly what makes "
        "early detection feasible."
    ),
    new_code_cell(
        "print(json.dumps(eda.withdrawn_analysis(master), indent=2))\n"
        + show_fig("withdrawn_activity_decay")
    ),
    new_markdown_cell(
        "# Findings and implications for modelling\n\n"
        "1. **Early signal exists (RQ1).** Behavioural and performance features separate the "
        "classes from 10–20% of course length and strengthen monotonically; 40–60% is a robust, "
        "actionable window.\n"
        "2. **Behaviour > demographics (RQ1/RQ2).** Engagement and assessment features dominate "
        "(d up to 2.5); demographic association is small (V ≤ 0.15). Modelling should centre on "
        "behavioural features; SHAP/LIME are expected to rank these highly.\n"
        "3. **Mild imbalance (RQ3).** At 52.8% at-risk, aggressive resampling may add little; "
        "RQ3 will quantify SMOTE/ADASYN/class-weight against this baseline using PR-AUC/recall.\n"
        "4. **Correlated features (RQ2).** Multicollinear engagement features may make explanation "
        "importance unstable — a factor the stability metric must account for.\n"
        "5. **No leakage.** No feature is near-perfectly correlated with the label, and the "
        "time-aware cut removes future events; held-out estimates should be trustworthy.\n\n"
        "# References\n\n"
        "[1] M. Adnan et al., *IEEE Access*, 9:7519–7539, 2021.  \n"
        "[2] N. Tomasevic, N. Gvozdenovic, S. Vranes, *Computers & Education*, 143:103676, 2020.  \n"
        "[3] J. Kuzilek, M. Hlosta, Z. Zdrahal, *Scientific Data*, 4:170171, 2017."
    ),
]

for name, nb in [("01_build_master_table.ipynb", nb01), ("02_eda.ipynb", nb02)]:
    path = NB_DIR / name
    nbf.write(nb, path)
    print("wrote", path)
