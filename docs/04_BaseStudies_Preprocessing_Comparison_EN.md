# Base Studies: OULAD Preprocessing Pipelines — A Comparative Survey

**Subtitle:** Comparing data collection, cleaning, feature engineering, and splitting across four prior studies to justify our group's design choices.

**DSP391m – Group 1 · Report 2 (Data Tasks), Chapter 3 · Work item STT 24 (Son)**

---

> **Disclaimer:** Exact figures, thresholds, and quoted results from each study should be verified against the original source by the team before final submission.

---

## 1. Introduction

The Open University Learning Analytics Dataset (OULAD) — described by Kuzilek et al. [3] — provides seven relational tables covering 32,593 student registrations, including demographic profiles, Virtual Learning Environment (VLE) clickstream interactions, and summative assessment records. Because multiple research groups have used this dataset for dropout and performance prediction, their preprocessing decisions form a practical baseline for our project. This chapter surveys four such studies and extracts methodological lessons that directly inform our pipeline.

---

## 2. Comparison Table: Preprocessing Pipelines Across Base Studies

| Study | **Collection** | **Cleaning** | **Feature Engineering** | **Splitting** |
|---|---|---|---|---|
| **[1] Adnan et al. (2021)** | Full OULAD; demographic, VLE clickstream, and assessment tables merged per student per module [1] | Missing values removed or imputed; student registrations with insufficient activity excluded [1] | Time-aware features truncated at multiple course-length checkpoints (10–100%); combined demographic + cumulative engagement + running assessment score [1] | Temporal cut-off enforced per checkpoint; train/test partitioned to prevent leakage of future events; class imbalance addressed via resampling strategies [1] |
| **[2] Tomasevic et al. (2020)** | OULAD; focus on engagement (clickstream) and assessment sub-tables; demographic fields included as secondary inputs [2] | Records with missing outcome labels dropped; categorical fields encoded; outlier records with extreme click counts inspected [2] | Clickstream aggregated into total interaction counts; past assessment scores used as direct features; demographic variables appended but found to contribute little [2] | Standard hold-out or cross-validation; no explicit temporal cut-off reported; stratified split on the pass/fail label [2] |
| **[4] Gunasekara & Saarela (2025)** | OULAD (among other educational datasets); primarily used as a benchmark for explainability evaluation [4] | Standard cleaning following upstream pipeline; preprocessing details are secondary to the XAI evaluation focus [4] | Feature set largely inherited from prior work; minimal new engineering; SHAP/LIME applied post-hoc to the trained model [4] | Train/test split conventional; splitting methodology not a primary contribution of this study [4] |
| **[5] Clickstream study (2023)** | Full OULAD VLE interaction log (~10 M rows); demographic and assessment tables joined [5] | Low-activity records filtered; duplicate interaction events de-duplicated; date-out-of-range events removed [5] | Clickstream aggregated per student into total clicks, active days, and per-activity-type interaction counts; resulting in a compact per-student feature vector [5] | Random or stratified split on the final label; aggregation performed before splitting to avoid row-level leakage [5] |

---

## 3. Discussion

### 3.1 Collection

All four studies draw on OULAD [3] in its published form without additional data collection. The key difference lies in which tables are emphasised: Adnan et al. [1] integrate all three feature groups (demographic, VLE, assessment) explicitly; Tomasevic et al. [2] treat engagement and assessment as primary and demographics as supplementary; the clickstream study [5] focuses narrowly on the VLE interaction log and performs heavy aggregation; while Gunasekara & Saarela [4] treat the dataset as a ready-made benchmark.

### 3.2 Cleaning

Approaches to missing data and outlier handling are broadly consistent: drop or impute missing outcome labels, filter clearly inactive registrations, and encode categorical demographics. No study reports a fundamentally novel cleaning method; the consensus is that OULAD is relatively clean and the main cleaning burden is deciding which subset of module-presentations to include.

### 3.3 Feature Engineering

The most significant variation occurs here. Adnan et al. [1] introduce the critical idea of **time-aware truncation**: features are re-computed at each checkpoint so that the model only sees information available up to that point in the course. The clickstream study [5] demonstrates how raw interaction logs can be compacted into a manageable per-student feature vector. Tomasevic et al. [2] provide empirical evidence that engagement and assessment features dominate, while demographic features add comparatively little predictive power.

### 3.4 Splitting

Adnan et al. [1] enforce a temporal cut-off aligned with each course-length checkpoint, which is the most rigorous approach for avoiding leakage. The other studies use conventional stratified or random splits. None of the surveyed studies use a group-aware split (ensuring a student does not appear in both train and test sets across multiple registrations), which is a refinement our pipeline adopts.

---

## 4. What We Inherit

- **Time-aware checkpoint prediction** [1]: We adopt the same principle of truncating feature computation at multiple course-length percentages (10 / 20 / 40 / 60 / 80 / 100%). The evidence from Adnan et al. suggests that predictions stabilise around the 40–60% mark, making these checkpoints the most actionable for early intervention.

- **Feature group prioritisation** [2]: Following Tomasevic et al.'s finding that clickstream engagement and running assessment scores carry the highest predictive signal, our feature engineering prioritises these two groups. Demographic features are retained for fairness analysis but are not relied upon for predictive accuracy.

- **Clickstream aggregation strategy** [5]: We aggregate the full VLE interaction log (approximately 10 million rows) into per-student, per-checkpoint summary features (total clicks, active days, per-activity-type counts), directly following the approach demonstrated in the clickstream study.

- **Leakage prevention** [1][5]: Encoders, scalers, and imputers are fitted exclusively on the training partition, and all events dated after a given checkpoint are excluded before that checkpoint's feature matrix is constructed, consistent with the temporal discipline in [1].

- **Group-aware stratified splitting**: We extend the splitting practice of [2] by ensuring that all registrations belonging to the same student (`id_student`) fall entirely within either the train or test set, and apply 5-fold × 5-seed cross-validation on the training portion. This guard against student-level leakage is not present in the surveyed studies but is motivated by their combined implicit assumptions about independent samples.

- **XAI framing** [4]: While Gunasekara & Saarela [4] assess explainability qualitatively, their survey motivates our addition of a quantitative explanation-stability metric to complement SHAP output — moving beyond what any single base study provides.

---

## References

[1] Adnan, M., Habib, A., Ashraf, J., Mussadiq, S., Raza, A. A., Abid, M., Nawaz, M., & Khan, S. U. (2021). Predicting at-Risk Students at Different Percentages of Course Length for Early Intervention Using Machine Learning Models. *IEEE Access*, 9, 7519–7539.

[2] Tomasevic, N., Gvozdenovic, N., & Vranes, S. (2020). An overview and comparison of supervised data mining techniques for student exam performance prediction. *Computers & Education*, 143, 103676.

[3] Kuzilek, J., Hlosta, M., & Zdrahal, Z. (2017). Open University Learning Analytics dataset. *Scientific Data*, 4, 170171.

[4] Gunasekara, N., & Saarela, M. (2025). Explainable AI in Education: Techniques and Qualitative Assessment. *Applied Sciences*, 15(1), 1–28.

[5] Anonymous (2023). VLE Clickstream Aggregation for Student Engagement Prediction using OULAD. *(Manuscript / internal reference — full citation to be confirmed by the team.)*
