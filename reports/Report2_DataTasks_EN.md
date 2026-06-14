# Report 2 — Data Tasks: Collection, Cleaning, and Exploratory Data Analysis

**DSP391m – Data Science Capstone Project · Group 1 · FPT University**
*Project: Time-Aware Explainable Machine Learning for Early At-Risk Student Prediction on OULAD · Supervisor: Nguyễn Thị Hoàng Yến*
*Scope: CLO3–CLO4 · Chapter 3 (Collection & Cleaning) and Chapter 4 (EDA). This draft synthesises the team deliverables; detailed standalone documents are referenced inline.*

---

## Chapter 3 — Data Collection and Cleaning

### 3.1 Data source, licence, and ethics

This project uses the **Open University Learning Analytics Dataset (OULAD)** (Kuzilek et al., 2017 [3]): **32,593** student–module–presentation records over **22** module-presentations and **7** relational tables, covering three feature groups (demographic, engagement/VLE, assessment performance) and the outcome `final_result`. OULAD is **anonymised at source** and distributed under **CC-BY 4.0**, so the ethical requirement is met by correct citation; no sensitive personal data is processed. Data-collection methods and the rationale for a public secondary dataset are analysed in `docs/03_DataCollection_Methods`; the source/licence/ethics statement is in `docs/DataSource_License_Ethics`.

### 3.2 Target variable definition

The task is **binary classification**. The label is derived from `final_result` and **fixed across all checkpoints**:

| Class | Values | Count | Share |
|---|---|---|---|
| not-at-risk (0) | Pass (12,361) + Distinction (3,024) | 15,385 | 47.2% |
| at-risk (1) | Fail (7,052) + Withdrawn (10,156) | 17,208 | **52.8%** |

The at-risk class is a **slight majority** (imbalance is mild); the 68/32 figure on the course slides is illustrative only. Full justification and the Withdrawn-over-time convention (**Option A**: fixed label, fixed population, keep Withdrawn-before-*t* as at-risk) are in `docs/01_TargetVariable_Definition` (agreement BB-B0-N1).

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
- **Outliers:** right-skewed clickstream features use `log1p`; others use `winsorize`; **no rows are dropped** (`src/features/preprocessing.py`, `docs/07_Preprocessing_Sequence`).

### 3.5 Time-aware feature extraction

Course lengths differ, so each progress percentage is converted to a concrete day: `cutoff_day = round(module_presentation_length × t / 100)` for `t ∈ {10,20,40,60,80,100}` (`data/checkpoint_map.csv`, 22×6 rows). `cut_at_checkpoint()` keeps only events on or before the cutoff, and the master pipeline is re-run per checkpoint to produce **six datasets** (`dataset_t10 … dataset_t100`), each **32,593 rows** sharing an **identical roster** (Option A). At-risk rate is constant at 52.8% across checkpoints (labels are fixed); only engagement/performance features change with *t*.

### 3.6 Leakage prevention and splitting

Two leakage axes are controlled. On the **time** axis, three rules (drop post-cutoff submissions; drop post-cutoff clicks; keep Withdrawn-before-*t* as at-risk) are documented in `docs/02_LeakagePrevention_Rules`. On the **feature** axis, the sequence **split → impute → outliers → encode/scale → resample** fits every learner on the training fold only (`docs/07_Preprocessing_Sequence`). The split is **group-aware (by `id_student`) + stratified** with a **fixed 20% test set** reused across checkpoints (`docs/06_SplitStrategy_Analysis`): train ≈ 26,104 rows, test ≈ 6,489 rows, **0 student overlap**, class ratio 0.53/0.52. CV on the training set uses **5-fold × 5 seeds**; headline metrics are **PR-AUC** and **recall** on the at-risk class. `tests/test_leakage.py` asserts all of this: **16/16 tests pass**.

### 3.7 Reproducibility

`RANDOM_SEED = 42` throughout; provenance in `data/data_manifest.txt` (MD5 + size + date); environment pinned in `requirements.txt`/`environment.yml`; notebooks run *Restart & Run All*; long steps are checkpointed/resumable; parquet writes are atomic. Full steps in `docs/10_Reproducibility`.

---

## Chapter 4 — Exploratory Data Analysis

All figures use the team chart standard (`docs/08_Chart_Standards`); analysis code is in `src/eda/eda.py` (notebook `02`).

### 4.1 Class distribution and imbalance (STT 27)

The real at-risk rate is **52.8%** (imbalance ratio 1.12 — mild). This rules out severe-imbalance assumptions but still justifies PR-AUC/recall, because the **at-risk positive class is the one we must not miss**.

![Class distribution: final_result and the binary at_risk label](figures/dist_class_distribution.png)

### 4.2 Descriptive statistics (STT 28)

Engagement features are strongly **right-skewed** — `max_clicks_single_day` (skew 10.6), `total_clicks` (3.0), `mean_clicks_per_active_day` (1.6) — empirically justifying the `log1p` transform. Full table: `reports/eda_descriptive_stats.csv`.

![Histograms with KDE for the main numeric features](figures/dist_numeric_hist_kde.png)
![Boxplots for outlier inspection](figures/dist_numeric_boxplots.png)

### 4.3 Bivariate analysis vs. the target (STT 36)

Standardised mean differences (|Cohen's d|) between classes rank the most **discriminative** features:

| Feature | \|Cohen's d\| |
|---|---|
| days_since_last_activity | 2.55 |
| n_assessments_submitted | 2.05 |
| weighted_score_to_date | 1.96 |
| n_days_active | 1.58 |
| mean_score_to_date | 1.58 |

Engagement and performance features dominate; demographic features are weak (`studied_credits` 0.28, `num_of_prev_attempts` 0.21).

![Numeric features by at-risk class](figures/bivar_numeric_by_label.png)
![At-risk rate across categorical features](figures/bivar_atrisk_rate_by_category.png)

### 4.4 Correlation analysis (STT 37)

Strongest target correlations: `days_since_last_activity` (r=0.78), `n_assessments_submitted` (0.72), `weighted_score_to_date` (0.71), `n_days_active` (0.63). The strongest feature–feature pair is `n_days_active`–`total_clicks` (0.84). **No feature correlates ≥0.95 with the target**, so no leakage feature is flagged.

![Pearson correlation matrix](figures/corr_pearson.png)
![Spearman correlation matrix](figures/corr_spearman.png)

### 4.5 Time-aware EDA (STT 38)

The between-class gap in mean `total_clicks` widens monotonically — **237 → 397 → 653 → 1,027 → 1,340 → 1,616** from t=10%→100% — and `n_days_active` likewise. The mean-score gap **saturates near t≈40%** (29.5 → 35.8 → 40.8, then flat).

![Time-aware behaviour by class across checkpoints](figures/time_trends_by_label.png)

### 4.6 Key findings and hypotheses

1. **F1 (RQ1) — early signal exists.** Engagement separates the classes from **t=10–20%** and the score signal is largely established by **t≈40%**, supporting reliable early prediction around 40–60% (consistent with Adnan et al. [1]).
2. **F2 (RQ1/RQ2) — behaviour > demographics.** `days_since_last_activity`, assessment submission, and accumulated score are the top discriminators while demographics are weak, matching Tomasevic et al. [2]; this guides feature emphasis and sets expectations for which features SHAP/LIME should rank highly (RQ2).
3. **F3 (RQ3) — mild imbalance.** At 52.8% at-risk, aggressive resampling may yield only modest gains; RQ3 will compare none/class-weight/SMOTE/ADASYN against this baseline using PR-AUC/recall.
4. **F4 (RQ2) — correlated engagement features.** Highly correlated engagement features (e.g., `total_clicks`–`n_days_active`, r=0.84) may make SHAP/LIME distribute importance among them, a factor to watch when measuring explanation stability (RQ2).

---

## References

1. M. Adnan et al., "Predicting at-Risk Students at Different Percentages of Course Length for Early Intervention," *IEEE Access*, vol. 9, pp. 7519–7539, 2021.
2. N. Tomasevic, N. Gvozdenovic, S. Vranes, "An overview and comparison of supervised data mining techniques for student exam performance prediction," *Computers & Education*, vol. 143, art. 103676, 2020.
3. J. Kuzilek, M. Hlosta, Z. Zdrahal, "Open University Learning Analytics dataset," *Scientific Data*, vol. 4, art. 170171, 2017.
4. S. Gunasekara, M. Saarela, "Explainable AI in Education: Techniques and Qualitative Assessment," *Applied Sciences*, 2025.
8. N. V. Chawla et al., "SMOTE: Synthetic Minority Over-sampling Technique," *JAIR*, 2002.
