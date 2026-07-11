# Data Cleaning Methods: Analysis and Justification

**DSP391m – Group 1 · Report 2 (Data Tasks), Chapter 3 · Task 3.3 — Data Cleaning Methods**

---

## Abstract

This chapter provides an analytical account of the four data-cleaning problems addressed in the DSP391m Group 1 pipeline: duplicate records, categorical inconsistency, missing values, and outliers. A fifth concern — temporal leakage introduced by future-dated records — is treated as both a cleaning and a leakage-prevention step. For each problem the exposition covers purpose, detection mechanism, per-variable decisions, and verified post-cleaning outcomes. All cleaning logic resides in two modules: `src/data/build_master_table.py` (structural integrity, duplicates, consistency) and `src/features/preprocessing.py` (missing values, outliers). Decisions are reproducible: parameters are learned from the training split only, and every transformed row is retained in the dataset.

---

## 1. Introduction

Raw data assembled by joining seven OULAD tables contains defects that, if left uncorrected, would bias model training or invalidate evaluation metrics. Four categories of defect are treated systematically before the train/test split and again as part of the anti-leakage preprocessing sequence. The order of operations is: (1) structural cleaning at build time, (2) missing-value imputation fit on train, (3) outlier transformation fit on train, (4) encoding and scaling fit on train.

---

## 2. Duplicate Records

**Purpose.** Each row in the master table is intended to represent a unique student-module-presentation triple. Duplicated composite keys would inflate some students' records and corrupt aggregate statistics.

**Method.** The function `_clean` in `build_master_table.py` calls `pandas.DataFrame.drop_duplicates` on the composite key `(code_module, code_presentation, id_student)`, which corresponds to the constant `GROUP_COLS`. The deduplicated table is then re-indexed from zero.

**Result.** Post-cleaning verification confirms zero duplicate keys. The count is logged to `data/interim/master_cleaning_log.csv` under the item `duplicate_keys_removed`. The join log separately records row counts at each merge step so that unexpected row inflation is immediately visible.

### 2.1 Exact-duplicate clickstream rows — documented decision

**Observation.** The raw `studentVle.csv` contains 10,655,280 rows, of which 787,170 (7.4%) are exact duplicates of another row across all columns. This is a quirk of the OULAD distribution itself: the table has no unique key, and one row represents a student's interactions with one VLE material on one day, with `sum_click` already aggregated at source. By the schema alone, two identical rows are therefore indistinguishable from a legitimately repeated aggregate record.

**Decision — keep and accumulate.** The pipeline retains these rows; the checkpoint aggregation (`groupby` + `sum` over `sum_click`) accumulates them into the engagement features. Rationale: (i) fidelity to the dataset as published — absent a unique key, deleting one copy would be an unverifiable guess about which record is "real"; (ii) consistency with the baseline literature (Adnan et al. 2021; Tomasevic et al. 2020), which works from the original OULAD tables without clickstream deduplication, keeping our click-derived features comparable.

**Acknowledged limitation.** If some of these duplicates are double-logging artefacts at the source, click totals (`total_clicks`, `clicks_*`) are over-counted for the affected student-days. This is accepted and documented as a limitation of the source data rather than "repaired" by deletion. Note the contrast with the master-table deduplication above, where the composite key makes true duplicates identifiable.

---

## 3. Consistency and Standardisation

**Purpose.** Categorical string columns sourced from CSV may carry leading or trailing whitespace, causing what are semantically identical categories to appear as distinct values in a groupby or encoder.

**Method.** For every column in `CATEGORICAL_COLS` — `gender`, `region`, `highest_education`, `imd_band`, `age_band`, `disability` — the pipeline applies `str.strip()` after the join. No case-folding or synonym consolidation is performed; the intent is minimal, reversible normalisation.

**Verified cardinalities after cleaning.**

| Variable | Distinct values |
|---|---|
| `region` | 13 |
| `highest_education` | 5 |
| `imd_band` | 10 |
| `age_band` | 3 |
| `gender` | 2 |
| `disability` | 2 |

**OULAD quirk: `imd_band` value `"10-20"`.** The OULAD source data omits the `%` sign from the second band, rendering it `"10-20"` instead of `"10-20%"`. The pipeline retains this value verbatim. The ordinal encoder defined in `preprocessing.py` lists `"10-20"` explicitly at rank 2 in the `ORDINAL_ORDERS["imd_band"]` sequence. Silently rewriting the raw category would introduce a discrepancy between source data and encoder configuration and would complicate reproducibility audits.

---

## 4. Missing Values

**Purpose.** Unaddressed missing values prevent sklearn estimators from training and may, if imputed naively, introduce information leakage or distort the inferential signal.

**Method.** The function `handle_missing` in `preprocessing.py` applies variable-specific strategies. Imputation statistics (the training-set median for `date_registration`) are derived from the training fold only and then applied identically to the test fold, satisfying the anti-leakage requirement.

**Table 1: Missing-value analysis.**

| Variable | # Missing | Assumed Mechanism | Strategy |
|---|---|---|---|
| `imd_band` | 1,111 | MAR / MCAR | Fill `'Unknown'`; insert as rank-0 category in `ORDINAL_ORDERS["imd_band"]` |
| `mean_score_to_date` | gaps when no submission yet | MNAR | Fill `0`; binary indicator `not_submitted` already created by feature engineering |
| `weighted_score_to_date` | gaps when no submission yet | MNAR | Fill `0`; covered by the same `not_submitted` indicator |
| `n_assessments_submitted` | gaps when no submission yet | MNAR | Fill `0`; covered by the same `not_submitted` indicator |
| `date_registration` | 45 | MCAR | Fill with training-set median (fit on train only) |
| `date_unregistration` | 22,521 | Structural absence | Not imputed; not used as a feature |

**Decision rationale.**

- `imd_band`: Missingness is plausibly administrative rather than outcome-related (MAR or MCAR). Introducing a dedicated `"Unknown"` category preserves the ordinal scale for the remaining 10 values without fabricating a socioeconomic estimate.
- Score variables (MNAR): A missing score at checkpoint *t* means the student has submitted no assessments by that date. This is itself a strong predictive signal for at-risk status. Filling with zero makes the signal explicit; the binary indicator `not_submitted` captures the fact of absence separately, preventing the zero from being conflated with a genuine zero-score submission.
- `date_registration`: Only 45 records are affected, and the missingness appears unrelated to outcome (MCAR). Median imputation fit on the training set is simple and introduces negligible bias.
- `date_unregistration`: Most students complete without withdrawing, so 22,521 missing values are structurally unavoidable. Including this column as a feature would require imputing a fictional unregistration date for the majority of the cohort, which has no justification.

**Verified result.** After `handle_missing`, `df.isnull().sum()` equals zero across every feature column in both the training and test splits, as confirmed by the assertion in the pipeline smoke test.

**Errata (2026-07-12): banked assessments & `not_submitted`.** A defect was found and fixed on 2026-07-12 in `src/data/build_performance_features.py`: assessments carried over from a previous presentation ("banked", `is_banked = 1`) were excluded from the set of submitted assessments, yet the same assessments were still counted as due at the checkpoint — so the `not_submitted` indicator was incorrectly set to 1 for students who had banked them. Measured impact: 78 of 32,593 enrolment records (0.24%) at *t* = 100%. The code now counts a banked assessment as covering its deadline. Result tables committed before this date were computed with the pre-fix code and will be recomputed in full during the final report-freeze run (the renumbering checklist is tracked in the defence handbook).

---

## 5. Outliers

**Purpose.** Extreme values in right-skewed engagement features would distort distance-based models and inflate variance estimates in tree-based models. The goal is to reduce the influence of extremes without discarding any student record.

**Detection.** The IQR rule is applied: a value is flagged as a suspected outlier when it falls below Q1 − 1.5 × IQR or above Q3 + 1.5 × IQR. Thresholds are computed from the training set only. No rows are deleted.

**Transformation strategies.**

- `log1p`: Applied to strongly right-skewed clickstream features. The transformation `x → log(1 + x)` compresses the long right tail while mapping zero to zero, which is essential given that many students record no activity in a given activity type.
- `winsorize`: Applied at 1% limits (bottom and top 1%). Values below the 1st percentile or above the 99th percentile are clipped to those boundary values, preserving the ordinal rank of every observation.
- `none`: Applied where the variable is naturally bounded or where IQR analysis revealed no genuine outliers.

**Evidence of skew from exploratory data analysis.** The `max_clicks_single_day` variable exhibits a skewness of approximately 10.6; `total_clicks` approximately 3.0; `mean_clicks_per_active_day` approximately 1.6. These values justify the `log1p` treatment.

**Table 2: Outlier-handling decisions.**

| Variable (group) | Detection | Strategy | Reason |
|---|---|---|---|
| `total_clicks` | IQR | `log1p` | Skewness ≈ 3.0; max in thousands |
| `n_days_active` | IQR | `log1p` | Strongly right-skewed count |
| `clicks_forumng`, `clicks_oucontent`, `clicks_resource`, `clicks_homepage`, `clicks_oucollaborate`, `clicks_quiz`, `clicks_subpage`, `clicks_url` | IQR | `log1p` | Per-activity click counts, same distributional shape |
| `max_clicks_single_day` | IQR | `log1p` | max = 7,920; skewness ≈ 10.6 |
| `mean_clicks_per_active_day` | IQR | `log1p` | max = 1,879; skewness ≈ 1.6 |
| `days_since_last_activity` | IQR | `winsorize` (1%) | Only 6 flagged records; mild skew |
| `studied_credits` | IQR | `winsorize` (1%) | max = 655; moderate right skew |
| `num_of_prev_attempts` | IQR | `winsorize` (1%) | IQR = 0, Q1 = Q3 = 0; winsorize preserves the "repeated-attempt" signal for at-risk students |
| `weighted_score_to_date` | IQR | `winsorize` (1%) | Open theoretical range; winsorize is safer than log1p for a score |
| `mean_score_to_date` | IQR | `none` | Upper bound 103.15 from IQR analysis exceeds physical maximum of 100, indicating no genuine outliers |
| `n_assessments_submitted` | IQR | `none` | Bounded by course assessment count |
| `date_registration` | IQR | `none` | Natural signed range (negative = pre-course); no transformation needed |

---

## 6. Temporal Cleaning

**Purpose.** The pipeline generates multiple feature snapshots at predefined checkpoints (e.g., day 60, day 90, full-course). Any record dated after checkpoint *t* — whether a VLE interaction or an assessment submission — must be excluded before computing features for that checkpoint.

**Method.** The function `cut_at_checkpoint` (in `src/data/time_utils.py`) filters rows to retain only those with a date ≤ *t* before feature aggregation. This step is both a data-cleaning operation (removing temporally inadmissible observations) and a leakage-prevention measure (ensuring no information from after the prediction date influences the features). It is applied independently for each checkpoint and for each fold of the train/test split.

---

## 7. Why This Matters for Modelling

Clean, consistent, and leak-free inputs are a prerequisite for valid modelling. Duplicate rows inflate certain students' influence on learned parameters; whitespace artefacts cause encoders to generate spurious categories; unaddressed missingness in MNAR variables discards predictive signal rather than imputing it; untreated right skew causes gradient-based and distance-based estimators to overfit to extreme values; and future-dated records introduce label leakage that makes evaluation metrics artificially optimistic. The four cleaning steps described in this chapter, applied in the order established by the anti-leakage pipeline sequence, produce a dataset on which the train/test split and the transformation stage can operate correctly and reproducibly.
