# Report 2 — Data Tasks: Collection, Cleaning, and Exploratory Data Analysis

**DSP391m – Data Science Capstone Project · Group 1 · FPT University**
*Project: Time-Aware Explainable Machine Learning for Early At-Risk Student Prediction on OULAD · Supervisor: Nguyễn Thị Hoàng Yến*
*Scope: CLO3–CLO4 · Chapter 3 (Collection & Cleaning) and Chapter 4 (EDA). This draft synthesises the team deliverables; detailed standalone documents are referenced inline.*

---

## Chapter 3 — Data Collection and Cleaning

### 3.1 Data source, licence, and ethics

This project uses the **Open University Learning Analytics Dataset (OULAD)** (Kuzilek et al., 2017 [3]): **32,593** student–module–presentation records over **22** module-presentations and **7** relational tables, covering three feature groups (demographic, engagement/VLE, assessment performance) and the outcome `final_result`. OULAD is **anonymised at source** and distributed under **CC-BY 4.0**, so the ethical requirement is met by correct citation; no sensitive personal data is processed. Data-collection methods and the rationale for a public secondary dataset are analysed in `docs/02_collection/Data_Collection_Methods`; the source/licence/ethics statement is in `docs/02_collection/Data_Source_License_Ethics`.

### 3.2 Target variable definition

The task is **binary classification**. The label is derived from `final_result` and **fixed across all checkpoints**:

| Class | Values | Count | Share |
|---|---|---|---|
| not-at-risk (0) | Pass (12,361) + Distinction (3,024) | 15,385 | 47.2% |
| at-risk (1) | Fail (7,052) + Withdrawn (10,156) | 17,208 | **52.8%** |

The at-risk class is a **slight majority** (imbalance is mild); the 68/32 figure on the course slides is illustrative only. Full justification and the Withdrawn-over-time convention (**Option A**: fixed label, fixed population, keep Withdrawn-before-*t* as at-risk) are in `docs/01_data_specification/Target_Variable_Definition` (agreement BB-B0-N1).

### 3.3 Data integration — the master table

The seven tables are merged into one flat **master table**, one row per student–module–presentation. `studentInfo` is the base; `studentRegistration`, the aggregated engagement table, and the aggregated performance table are joined with **left joins**; a before/after **join log** proves integrity:

| Step | rows_before | rows_after | n_students |
|---|---|---|---|
| studentInfo (base) | 32,593 | 32,593 | 28,785 |
| + registration | 32,593 | 32,593 | 28,785 |
| + engagement | 32,593 | 32,593 | 28,785 |
| + performance | 32,593 | 32,593 | 28,785 |

No row is duplicated or lost. **Engagement features** are aggregated from the **10,655,280-row** `studentVle` clickstream (joined to `vle` for activity type): `total_clicks`, `n_days_active`, eight `clicks_<type>` counts, `max_clicks_single_day`, `mean_clicks_per_active_day`, and `days_since_last_activity`. **Performance features** are aggregated from `studentAssessment` with assessment weights/deadlines: `mean_score_to_date`, `weighted_score_to_date`, `n_assessments_submitted`, and the `not_submitted` risk flag (a deadline passed without submission). Result: **master_raw = 32,593 × 33 columns** (`src/data/build_master_table.py`, notebook `01`).

### 3.4 Data cleaning

- **Duplicates:** 0 duplicate composite keys after `drop_duplicates`.
- **Consistency:** categorical labels standardised; cardinalities match the data dictionary (region 13, education 5, imd_band 10, age_band 3, gender/disability 2).
- **Missing values:** `imd_band` (1,111) → `"Unknown"`; assessment gaps → 0 plus the `not_submitted` indicator (a *signal*, not noise); `date_registration` (45) → train median. The only large gap, `date_unregistration` (22,521), is **expected** — most students never withdraw — and is not used as a feature.
- **Outliers:** right-skewed clickstream features use `log1p`; others use `winsorize`; **no rows are dropped** (`src/features/preprocessing.py`, `docs/04_transformation/Preprocessing_Sequence`).

### 3.5 Time-aware feature extraction

Course lengths differ, so each progress percentage is converted to a concrete day: `cutoff_day = round(module_presentation_length × t / 100)` for `t ∈ {10,20,40,60,80,100}` (`data/checkpoint_map.csv`, 22×6 rows). `cut_at_checkpoint()` keeps only events on or before the cutoff, and the master pipeline is re-run per checkpoint to produce **six datasets** (`dataset_t10 … dataset_t100`), each **32,593 rows** sharing an **identical roster** (Option A). At-risk rate is constant at 52.8% across checkpoints (labels are fixed); only engagement/performance features change with *t*.

### 3.6 Leakage prevention and splitting

Two leakage axes are controlled. On the **time** axis, three rules (drop post-cutoff submissions; drop post-cutoff clicks; keep Withdrawn-before-*t* as at-risk) are documented in `docs/03_cleaning/Leakage_Prevention_Rules`. On the **feature** axis, the sequence **split → impute → outliers → encode/scale → resample** fits every learner on the training fold only (`docs/04_transformation/Preprocessing_Sequence`). The split is **group-aware (by `id_student`) + stratified** with a **fixed 20% test set** reused across checkpoints (`docs/05_splitting/Split_Strategy_Analysis`): train ≈ 26,104 rows, test ≈ 6,489 rows, **0 student overlap**, class ratio 0.53/0.52. CV on the training set uses **5-fold × 5 seeds**; headline metrics are **PR-AUC** and **recall** on the at-risk class. `tests/test_leakage.py` asserts all of this: **16/16 tests pass**.

### 3.7 Reproducibility

`RANDOM_SEED = 42` throughout; provenance in `data/data_manifest.txt` (MD5 + size + date); environment pinned in `requirements.txt`/`environment.yml`; notebooks run *Restart & Run All*; long steps are checkpointed/resumable; parquet writes are atomic. Full steps in `docs/07_standards/Reproducibility`.

---

## Chapter 4 — Exploratory Data Analysis

Every comparison is supported by an appropriate statistic, not visual impression alone: **Mann-Whitney U** tests (Benjamini-Hochberg corrected) with **Cohen's d** for numeric features, **chi-square** with **Cramér's V** for categorical features, and Pearson/Spearman correlation with an explicit leakage check. Figures follow the chart standard (`docs/07_standards/Chart_Standards`); the analysis is `src/eda/eda.py`, narrated in notebook `02`, with result tables under `reports/tables/`.

### 4.0 Data quality

Only three columns contain gaps: `date_unregistration` (22,521 — structurally absent for students who never withdraw, not a feature), `imd_band` (1,111 → `Unknown`) and `date_registration` (45 → train median). No feature column is materially incomplete.

![Missing values by column](figures/quality_missingness.png)

### 4.1 Class distribution and imbalance (STT 27)

The observed at-risk rate is **52.8%** (imbalance ratio 1.12) — a slight majority, not the illustrative 68/32 on the slides. Imbalance is therefore mild (reported honestly; it frames RQ3); PR-AUC and recall on the at-risk class remain the headline metrics because a missed at-risk student is the costly error.

![Target distribution and imbalance](figures/target_distribution.png)

### 4.2 Univariate description (STT 28)

Engagement features are strongly right-skewed and heavy-tailed — `clicks_resource` (skew ≈ 35, kurtosis ≈ 2,125), `clicks_url` (skew ≈ 13), `max_clicks_single_day` (skew ≈ 11) — empirically justifying the `log1p` transform applied during cleaning. The full table (mean/median/std/quartiles/skew/kurtosis) is `reports/tables/univariate_numeric.csv`.

![Univariate distributions (histogram + KDE), coloured by feature group](figures/univariate_hist_kde.png)
![Univariate boxplots (IQR outlier inspection)](figures/univariate_boxplots.png)
![Categorical frequency distributions](figures/univariate_categorical_freq.png)

### 4.3 Bivariate — numeric features vs. the target (STT 36)

Mann-Whitney U tests (BH-corrected) find **all 19 numeric features significant** (q < 0.05) — unsurprising at n ≈ 32,593 — so **effect size**, not the p-value, is the discriminator. Ranked by |Cohen's d|:

| Feature | Group | \|Cohen's d\| |
|---|---|---|
| days_since_last_activity | Engagement | **2.55** |
| n_assessments_submitted | Performance | **2.05** |
| weighted_score_to_date | Performance | **1.96** |
| n_days_active | Engagement | **1.58** |
| mean_score_to_date | Performance | **1.58** |

Behaviour and performance dominate; demographics are weakest (`studied_credits` 0.28, `num_of_prev_attempts` 0.21). Full test table: `reports/tables/bivariate_numeric_tests.csv`.

![Discriminative power (|Cohen's d|), coloured by feature group](figures/bivariate_effect_sizes.png)
![The six strongest numeric features by class](figures/bivariate_top_boxplots.png)

### 4.4 Bivariate — categorical features vs. the target

Chi-square tests are significant, but the **Cramér's V** effect sizes are small: `highest_education` (0.15) and `imd_band` (0.15) lead, while `gender` (0.02) is negligible. Demographics carry limited standalone signal and are best retained for fairness analysis rather than predictive reliance.

![At-risk rate across categorical levels (dashed = overall 52.8%)](figures/bivariate_categorical_rate.png)

### 4.5 Multivariate — correlation, multicollinearity, leakage (STT 37)

Pearson and Spearman agree on the structure. Two pairs are multicollinear (|r| ≥ 0.8): `n_days_active`–`total_clicks` (0.84) and `days_since_last_activity`–`n_assessments_submitted` (−0.83) — relevant to explanation stability (RQ2). Strongest target correlations: `days_since_last_activity` (0.78), `n_assessments_submitted` (0.72), `weighted_score_to_date` (0.71). **No feature correlates ≥ 0.95 with the target**, so none acts as a leakage proxy.

![Pearson correlation matrix](figures/corr_pearson.png)
![Spearman correlation matrix](figures/corr_spearman.png)
![Correlation of features with the target](figures/corr_with_target.png)

### 4.6 Time-aware analysis — when does the signal emerge? (STT 38, RQ1)

Tracking **|Cohen's d| per checkpoint** shows how class separability grows as the course progresses. `n_days_active` already exceeds the large-effect threshold (d ≥ 0.8) at **t = 10%**; the score and submission features cross it by **t = 20%**; `days_since_last_activity` by **t = 40%**. The behavioural signal is therefore actionable from ~20–40% of course length, grounding the RQ1 schedule in evidence.

| Feature | earliest *t* with \|d\| ≥ 0.8 |
|---|---|
| n_days_active | 10% |
| mean_score_to_date · n_assessments_submitted · weighted_score_to_date | 20% |
| days_since_last_activity | 40% |
| total_clicks | 60% |

![Mean feature trajectory by class across checkpoints](figures/time_mean_trajectory.png)
![Discrimination growth across checkpoints (RQ1)](figures/time_discrimination_curve.png)

### 4.7 The Withdrawn early-warning signal (Step-0 Option A)

The data confirms Option A's premise that withdrawal produces a genuine signal rather than noise: median inactivity is **11 days for not-at-risk, 116 for Fail, and 233 for Withdrawn**, while median total clicks fall from **1,425 (not-at-risk) to 89 (Withdrawn)**. The activity collapse of withdrawing students is exactly what makes early detection feasible.

![Withdrawn students: the activity-decay signal](figures/withdrawn_activity_decay.png)

### 4.8 Findings and implications for modelling

1. **F1 (RQ1) — early, growing signal.** Behavioural/performance features separate the classes from t = 10–20% and strengthen monotonically; 40–60% is a robust, actionable window (consistent with Adnan et al. [1]).
2. **F2 (RQ1/RQ2) — behaviour ≫ demographics.** Engagement/performance reach d > 2 while demographic association stays small (Cramér's V ≤ 0.15), reproducing Tomasevic et al. [2]; SHAP/LIME are expected to rank behavioural features highest.
3. **F3 (RQ3) — mild imbalance.** At 52.8% at-risk, resampling may add little; RQ3 quantifies SMOTE/ADASYN/class-weight against this baseline using PR-AUC/recall.
4. **F4 (RQ2) — correlated features.** Multicollinear engagement features may destabilise explanation importance — a factor the stability metric must account for.
5. **F5 — no leakage.** No feature is near-perfectly correlated with the label, and the time-aware cut removes future events; held-out estimates should be trustworthy.

---

## References

1. M. Adnan et al., "Predicting at-Risk Students at Different Percentages of Course Length for Early Intervention," *IEEE Access*, vol. 9, pp. 7519–7539, 2021.
2. N. Tomasevic, N. Gvozdenovic, S. Vranes, "An overview and comparison of supervised data mining techniques for student exam performance prediction," *Computers & Education*, vol. 143, art. 103676, 2020.
3. J. Kuzilek, M. Hlosta, Z. Zdrahal, "Open University Learning Analytics dataset," *Scientific Data*, vol. 4, art. 170171, 2017.
4. S. Gunasekara, M. Saarela, "Explainable AI in Education: Techniques and Qualitative Assessment," *Applied Sciences*, vol. 15, no. 3, art. 1239, 2025.
8. N. V. Chawla et al., "SMOTE: Synthetic Minority Over-sampling Technique," *JAIR*, 2002.
