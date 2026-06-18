"""Generate the two deliverable notebooks (English).

* notebook 01 — reproducible build of the master table (Chapter 3).
* notebook 02 — the canonical EDA report (English): executive summary, a
  structure-first profile table, formatted result tables (no raw JSON dumps),
  crisp interpretation after each section, and references. Both are thin over the
  tested ``src/`` modules so the notebook and the committed code can never drift.

The Vietnamese narration used when presenting lives in the speaker script
(reports/Task3_Speaker_Script_Merged.docx), not in this notebook.

Run:  python tools/build_notebooks.py
"""

from pathlib import Path

import nbformat as nbf
from nbformat.v4 import new_code_cell, new_markdown_cell, new_raw_cell

NB_DIR = Path(__file__).resolve().parents[1] / "notebooks"

BOOT = (
    "import sys\n"
    "from pathlib import Path\n"
    "import pandas as pd\n"
    "from IPython.display import Image, display\n"
    "ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()\n"
    "sys.path.insert(0, str(ROOT))\n"
    "TABLES = ROOT / 'reports' / 'tables'\n"
    "FIGS = ROOT / 'reports' / 'figures'\n"
    "pd.set_option('display.max_columns', 40)\n"
    "pd.set_option('display.width', 160)\n"
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
        "OULAD CSVs and is the executable counterpart of the Chapter-3 deliverables. It calls the "
        "tested modules in `src/data` so the notebook and the committed code cannot drift.\n\n"
        "**Target definition (Step-0, Option A).** `at_risk = 1` if `final_result ∈ {Fail, "
        "Withdrawn}`, else `0`; the label is fixed across all checkpoints."
    ),
    new_code_cell(
        BOOT
        + "from src.data.build_master_table import build_master\nfrom src.data.io_utils import INTERIM_DIR"
    ),
    new_markdown_cell(
        "# Method: integration at the student-module-presentation grain\n\n"
        "`studentInfo` is the base table. Registration, the aggregated engagement features (from "
        "the 10.6M-row `studentVle` clickstream) and the aggregated performance features (from "
        "`studentAssessment`) are attached by **left joins**, each validated `many_to_one`. A "
        "before/after row-count log proves no duplication or loss."
    ),
    new_code_cell(
        "master = build_master(rebuild_engagement=False)\nprint('master_raw:', master.shape)"
    ),
    new_markdown_cell(
        "# Join-integrity evidence\n\n"
        "Every step preserves exactly 32,593 records — the aggregation collapsed the one-to-many "
        "event tables to the student grain *before* joining, so no row was duplicated."
    ),
    new_code_cell("display(pd.read_csv(INTERIM_DIR / 'master_join_log.csv'))"),
    new_markdown_cell(
        "# Cleaning: deduplication, consistency, missing values, outliers\n\n"
        "Duplicate composite keys are dropped (0 remain); categorical text is standardised; "
        "`imd_band` gaps become `Unknown`; assessment gaps become 0 plus the informative "
        "`not_submitted` flag; outliers are transformed (log1p / winsorize), never deleted."
    ),
    new_code_cell("display(pd.read_csv(INTERIM_DIR / 'master_cleaning_log.csv'))"),
    new_markdown_cell(
        "# Output validation\n\n"
        "We confirm population size, absence of duplicate keys, and the fixed at-risk rate."
    ),
    new_code_cell(
        "print('rows:', len(master), '| columns:', master.shape[1])\n"
        "print('at_risk rate: {:.1%}'.format(master['at_risk'].mean()))\n"
        "key = ['code_module','code_presentation','id_student']\n"
        "assert len(master) == 32593 and master.duplicated(key).sum() == 0\n"
        "print('OK — 32,593 unique records, no duplicate keys')\n"
        "master.head(3)"
    ),
    new_markdown_cell(
        "# Conclusion\n\n"
        "The master table (32,593 × 33) integrates the three feature groups and the fixed label "
        "with audited integrity, and is the single input to the time-aware checkpoints "
        "(`src/data/make_checkpoints`) and the EDA (notebook 02)."
    ),
]

# =========================================================================== #
# Notebook 02 — EDA (English) — canonical report
# =========================================================================== #
nb02 = nbf.v4.new_notebook()
nb02.cells = [
    new_markdown_cell(
        "# Exploratory Data Analysis (EDA) — OULAD\n\n"
        "**DSP391m · Group 1 · FPT University** · Topic: *Time-Aware Explainable ML for Early "
        "At-Risk Student Detection (OULAD)*\n\n"
        "> **Executable EDA**: every analysis is run through the tested `src/eda/eda.py` module, "
        "so the figures & tables never drift from the code, and the numbers printed here are the "
        "ones used on the slides. We use `master_raw` (t=100%) for univariate/bivariate/"
        "correlation, and the six checkpoint datasets for the time-aware analysis.\n\n"
        "> The Vietnamese narration for presenting lives in the speaker script "
        "(`reports/Task3_Speaker_Script_Merged.docx`)."
    ),
    new_markdown_cell(
        "## Executive summary\n\n"
        "On the master table (**32,593** records, at-risk rate **52.8%**), five findings shape the "
        "modelling plan:\n\n"
        "1. **Behaviour dominates demographics.** Engagement & assessment features separate the "
        "classes strongly (Cohen's *d* up to **2.55**; all **19/19** numeric features significant "
        "at *q* < 0.05); demographic association is weak (Cramér's *V* ≤ **0.15**).\n"
        "2. **Clickstream is strongly right-skewed** (skew up to ~35) → motivates the `log1p` "
        "transform.\n"
        "3. **`days_since_last_activity` is bimodal** — the structural signature of disengagement.\n"
        "4. **No leakage:** no feature correlates ≥ 0.95 with the label; two engagement pairs are "
        "multicollinear (|r| ≥ 0.8) and flagged for SHAP attribution.\n"
        "5. **Signal is early:** `n_days_active` and `days_since_last_activity` reach a large "
        "effect (*d* ≥ 0.8) by **10%** of course length, scores by **20%** — grounding the "
        "early-intervention goal (RQ1)."
    ),
    new_markdown_cell(
        "## 0. Objectives & statistical method\n\n"
        "**What:** understand data quality and shape, find features that separate at-risk "
        "students, check for leakage, and locate when the signal emerges over time.\n\n"
        "**Why:** EDA is not decoration — each chart drives a decision (*feature selection* or "
        "*proving no leakage*).\n\n"
        "**Method:** Mann–Whitney U (non-parametric, fits the skewed features) + Benjamini–Hochberg "
        "correction & **Cohen's d** for numeric features; **chi-square + Cramér's V** for "
        "categorical features; **Pearson/Spearman** for multivariate structure. Figures follow the "
        "team chart standard (`src/eda/plot_style.py`, 300 dpi, colour-blind safe)."
    ),
    new_code_cell(
        BOOT + "from src.eda import eda\n"
        "master = eda.load_master()\n"
        "checkpoints = eda.load_checkpoints()\n"
        "print('master:', master.shape,\n"
        "      '| checkpoints stacked:', None if checkpoints is None else checkpoints.shape)"
    ),
    new_markdown_cell(
        "## 1. Dataset profile (structure-first)\n\n"
        "An analyst's first pass: for every column — its type, completeness, cardinality and "
        "(for numeric features) distribution shape. This single table replaces guesswork and "
        "flags exactly what cleaning must address (the few columns with gaps and the strongly "
        "skewed clickstream features)."
    ),
    new_code_cell(
        'num_cols = master.select_dtypes("number").columns\n'
        "profile = pd.DataFrame({\n"
        '    "dtype": master.dtypes.astype(str),\n'
        '    "n_missing": master.isnull().sum(),\n'
        '    "pct_missing": (master.isnull().mean() * 100).round(2),\n'
        '    "n_unique": master.nunique(),\n'
        '    "skew": master[num_cols].skew().round(2),\n'
        '}).sort_values("pct_missing", ascending=False)\n'
        'key = ["code_module", "code_presentation", "id_student"]\n'
        'print(f"{len(master):,} rows x {master.shape[1]} columns  |  numeric = {len(num_cols)}  |  "\n'
        '      f"duplicate composite keys = {master.duplicated(key).sum()}  |  "\n'
        "      f\"at-risk rate = {master['at_risk'].mean():.1%}\")\n"
        "display(profile)"
    ),
    new_markdown_cell(
        "## 2. Data quality\n\n"
        "Only three columns contain missing values: `date_unregistration` (structurally absent "
        "for students who never withdraw — not a feature), `imd_band` (1,111 ≈ 3.4%; filled "
        "`Unknown`), and `date_registration` (45 ≈ 0.14%; train-median imputed). After cleaning "
        "there is **0 NaN** in any feature column."
    ),
    new_code_cell(
        "_ = eda.data_quality(master)\n"
        "display(pd.read_csv(TABLES / 'data_quality_profile.csv', index_col=0))\n"
        + show_fig("quality_missingness")
    ),
    new_markdown_cell(
        "## 3. Univariate analysis\n\n"
        "**What:** histogram + KDE and boxplots per numeric feature.\n\n"
        "**Why:** most clickstream features are **strongly right-skewed** — the heavy tails are "
        "*real* learning behaviour, so we use `log1p` rather than deleting rows.\n\n"
        "**Result:** `clicks_resource` skew ≈ **34.7**, kurtosis ≈ **2,125** → evidence for "
        "`log1p`; `days_since_last_activity` is **bimodal**. Non-normal ⇒ later steps use "
        "**non-parametric** tests."
    ),
    new_code_cell(
        "_ = eda.univariate(master)\n"
        "num = pd.read_csv(TABLES / 'univariate_numeric.csv', index_col=0)\n"
        "display(num[['mean','std','min','50%','max','skew','kurtosis']])\n"
        + show_fig("univariate_hist_kde")
    ),
    new_code_cell(show_fig("univariate_boxplots")),
    new_markdown_cell(
        "**Categorical.** 83% of students hold A-Level or below; Post-Graduate / No-Formal are "
        "rare (<1.1% each) — hence one-hot with `handle_unknown=ignore` rather than dropping rare "
        "levels."
    ),
    new_code_cell(show_fig("univariate_categorical_freq")),
    new_markdown_cell(
        "## 4. Target distribution & class imbalance\n\n"
        "The observed at-risk rate is **52.8%** (imbalance ratio 1.12): a *slight majority*, not "
        "a severe imbalance — the real figure, not 68/32. Because a missed at-risk student is the "
        "costly error, PR-AUC and recall on the at-risk class are the headline metrics. "
        "**Withdrawn** is the single largest class, which matters for the time-aware analysis."
    ),
    new_code_cell(
        "_ = eda.target_distribution(master)\n"
        "counts = master['final_result'].value_counts().rename_axis('final_result').reset_index(name='count')\n"
        "counts['pct'] = (counts['count'] / len(master) * 100).round(1)\n"
        "counts['label'] = counts['final_result'].isin(['Fail','Withdrawn']).map({True:'at-risk (1)', False:'not-at-risk (0)'})\n"
        "display(counts)\n" + show_fig("target_distribution")
    ),
    new_markdown_cell(
        "## 5. Bivariate — numeric features vs the target\n\n"
        "**What:** for each numeric feature, **Cohen's d** + a Mann–Whitney U test (BH-corrected).\n\n"
        "**Why:** at n≈32k almost every p-value is tiny → **rank by effect size**, not p.\n\n"
        "**Result:** strongest are behavioural/performance — `days_since_last_activity` "
        "(*d*=**2.55**, 171 vs 14 days), `n_assessments_submitted` (2.05, 2.3 vs 8.6), "
        "`weighted_score_to_date` (1.96). **All 19/19 features significant**."
    ),
    new_code_cell(
        "_ = eda.numeric_vs_target(master)\n"
        "tb = pd.read_csv(TABLES / 'bivariate_numeric_tests.csv').sort_values('cohens_d', ascending=False)\n"
        "display(tb[['feature','group','mean_not_at_risk','mean_at_risk','cohens_d','p_adj_bh','significant_(q<0.05)']].head(10))\n"
        "print(f\"Significant features (q<0.05): {int(tb['significant_(q<0.05)'].sum())}/{len(tb)}\")\n"
        + show_fig("bivariate_effect_sizes")
    ),
    new_code_cell(show_fig("bivariate_top_boxplots")),
    new_markdown_cell(
        "## 6. Bivariate — categorical features vs the target (Cramér's V)\n\n"
        "Chi-square tests are significant (large *n*), but **Cramér's V** effect sizes are small: "
        "`highest_education` (0.15) and `imd_band` (0.15) lead, while `gender` (0.02) is "
        "negligible. Demographics carry limited standalone signal and are best kept for "
        "**fairness analysis** (watch deprivation and education, not gender), not prediction."
    ),
    new_code_cell(
        "_ = eda.categorical_vs_target(master)\n"
        "display(pd.read_csv(TABLES / 'bivariate_categorical_tests.csv'))\n"
        + show_fig("bivariate_categorical_rate")
    ),
    new_markdown_cell(
        "## 7. Multivariate — correlation, multicollinearity, leakage\n\n"
        "**What:** Pearson + Spearman matrices; correlation with the label; leakage check.\n\n"
        "**Why:** leakage is a **mandatory** check — a feature with |r| ≥ 0.95 vs the label is "
        "suspicious.\n\n"
        "**Result:** top |r| with the label is `days_since_last_activity` **+0.78** (agreeing with "
        "Cohen's d → two independent methods, same conclusion); **no feature |r| ≥ 0.95** ⇒ no "
        "leakage; two multicollinear pairs ≥ 0.8 (flagged for RQ2/SHAP)."
    ),
    new_code_cell(
        "_ = eda.correlation(master)\n"
        "print('Strong pairs (|r| >= 0.6):')\n"
        "display(pd.read_csv(TABLES / 'correlation_strong_pairs.csv'))\n"
        "print('Correlation with the target (top |r|):')\n"
        "display(pd.read_csv(TABLES / 'correlation_with_target.csv', index_col=0))\n"
        + show_fig("corr_pearson")
    ),
    new_code_cell(show_fig("corr_with_target")),
    new_markdown_cell(
        "## 8. Time-aware analysis — when does the signal emerge? (RQ1)\n\n"
        "**What:** measure |Cohen's d| per feature at six checkpoints 10%→100%.\n\n"
        "**Why:** the analysis specific to a time-aware problem — find the earliest reliable "
        "checkpoint for prediction (RQ1).\n\n"
        "**Result:** discrimination grows steadily; first to reach *d* ≥ 0.8: `n_days_active` "
        "**and** `days_since_last_activity` from **10%**, scores/submissions from **20%** → early "
        "prediction is feasible from **~10–20%** of course length.\n\n"
        "> *Consistency note:* after fixing the no-activity fill for `days_since_last_activity`, "
        "its *d* at t=100% (per-checkpoint table) equals **2.55**, matching the value computed on "
        "`master_raw` in §5."
    ),
    new_code_cell(
        "ta = eda.time_aware(checkpoints)\n"
        "display(pd.read_csv(TABLES / 'discrimination_by_checkpoint.csv', index_col=0).round(3))\n"
        "print('Earliest checkpoint reaching d>=0.8:', ta['earliest_checkpoint_d_ge_0.8'])\n"
        + show_fig("time_discrimination_curve")
    ),
    new_code_cell(show_fig("time_mean_trajectory")),
    new_markdown_cell(
        "## 9. The Withdrawn early-warning signal (Step-0 Option A)\n\n"
        "Withdrawal produces a **genuine signal**, not noise: median days-since-last-activity rises "
        "from **11** (not-at-risk) → **116** (Fail) → **233** (Withdrawn); median total clicks "
        "collapse from ~1,425 to ~89.\n\n"
        "**Honest caveat:** because withdrawn students are near-inactive, they are *trivially* "
        "separable at **late** checkpoints → late-checkpoint recall/PR-AUC can look optimistic; "
        "the genuine test of the model is at the **early** checkpoints."
    ),
    new_code_cell(
        "_ = eda.withdrawn_analysis(master)\n"
        "import numpy as np\n"
        "m = master.copy()\n"
        "m['status'] = np.where(m['final_result'].eq('Withdrawn'), 'Withdrawn',\n"
        "                       np.where(m['at_risk'].eq(1), 'Fail', 'Not-at-risk'))\n"
        "summary = m.groupby('status').agg(\n"
        "    median_days_idle=('days_since_last_activity', 'median'),\n"
        "    median_total_clicks=('total_clicks', 'median'),\n"
        "    n=('at_risk', 'size')).reindex(['Not-at-risk','Fail','Withdrawn'])\n"
        "display(summary.round(1))\n" + show_fig("withdrawn_activity_decay")
    ),
    new_markdown_cell(
        "## 10. Findings & implications for modelling\n\n"
        "1. **Early signal (RQ1).** Behavioural/performance features separate the classes from "
        "10–20% of course length and strengthen monotonically; 40–60% is a robust, actionable "
        "window.\n"
        "2. **Behaviour ≫ demographics (RQ1/RQ2).** Engagement/assessment reach *d* > 2; "
        "demographic association is small (Cramér's V ≤ 0.15) → SHAP/LIME are expected to rank "
        "behavioural features highest.\n"
        "3. **Mild imbalance (RQ3).** 52.8% at-risk → RQ3 quantifies SMOTE/ADASYN/class-weight "
        "against this baseline using PR-AUC/recall.\n"
        "4. **Correlated features (RQ2).** Two multicollinear pairs may make explanation "
        "importance unstable — a factor the stability metric must account for.\n"
        "5. **No leakage.** No feature is near-perfectly correlated with the label, and the "
        "time-aware cut removes future events → held-out estimates should be trustworthy.\n\n"
        "**References.** [1] Kuzilek, Hlosta, Zdrahal, *Scientific Data* 4:170171, 2017. "
        "[2] Adnan et al., *IEEE Access* 9:7519–7539, 2021. "
        "[3] Tomasevic, Gvozdenovic, Vranes, *Computers & Education* 143:103676, 2020."
    ),
]

for name, nb in [("01_build_master_table.ipynb", nb01), ("02_eda.ipynb", nb02)]:
    path = NB_DIR / name
    nbf.write(nb, path)
    print("wrote", path)
