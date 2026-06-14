# Base Studies: OULAD Preprocessing Pipelines — A Comparative Survey

**Subtitle:** Comparing data collection, cleaning, feature engineering, and splitting across four prior studies to justify our group's design choices.

**DSP391m – Group 1 · Report 2 (Data Tasks), Chapter 3 · Work item STT 24 (Son)**

---

> **Verification note.** The cells below were cross-checked against sources: full text for [1] (open mirror) and [4] (authors' open-access repository); the abstract plus independent citing studies for [2] and [5] (publisher full text paywalled). Cells the source does not state are marked *"not specified"* rather than inferred.

---

## 1. Introduction

The Open University Learning Analytics Dataset (OULAD) — described by Kuzilek et al. [3] — provides seven relational tables covering 32,593 student registrations, including demographic profiles, Virtual Learning Environment (VLE) clickstream interactions, and summative assessment records. Because multiple research groups have used this dataset for dropout and performance prediction, their preprocessing decisions form a practical baseline for our project. This chapter surveys four such studies and extracts methodological lessons that directly inform our pipeline.

---

## 2. Comparison Table: Preprocessing Pipelines Across Base Studies

| Study | **Collection** | **Cleaning** | **Feature Engineering** | **Splitting / Validation** |
|---|---|---|---|---|
| **[1] Adnan et al. (2021)** | Full OULAD (22 module-presentations, 32,593 students); demographic, VLE clickstream, and assessment tables [1] | Missing date values imputed with the **mean**; Withdrawn kept as a class; no inactive-student filtering reported [1] | Three feature groups (demographic; clickstream sum/mean clicks; assessment scores, relative score, late-submission counts) computed cumulatively at **course start and 20/40/60/80/100%** of course length [1] | **10-fold CV** for the ML models, **85/15 split** for the deep model; imbalance handled by **class-merging** (Pass+Distinction; Fail+Withdrawn), *not* resampling; metrics: accuracy, precision, recall, F-score, AUC [1] |
| **[2] Tomasevic et al. (2020)** | OULAD; demographic, engagement (clickstream) and past-performance data combined [2] | *Not specified* in the paper's accessible text [2] | Three feature groups; key finding: **engagement + performance** carry the highest signal, while demographics "did not show significant influence" [2] | Classification and regression tasks; **ANN performed best**; the exact split/CV procedure is *not specified* in accessible sources [2] |
| **[4] Gunasekara & Saarela (2025)** | OULAD **only**, a **3-module subset (AAA/BBB/CCC)** → 14 features, 17,091 samples (Pass 5,963 / Fail 7,128); used as a benchmark to illustrate XAI [4] | Rows/columns with excessive missingness removed; numerical features normalised to ~0–1; classes merged (Pass+Distinction; Fail+Withdrawn) [4] | **14 selected/aggregated** OULAD attributes (e.g. `sum_click`, `assessment_count`, `delay`, `score` + demographics); SHAP/LIME applied post-hoc [4] | **5-fold CV repeated 50×** (+ a train/test split); **ANN vs Decision Tree**; SHAP+LIME, mainly qualitative local explanations [4] |
| **[5] Liu et al. (2023)** | OULAD; `studentInfo` merged with the `studentVle` clickstream; **5,341 students** after cleaning [5] | **180 students with no recorded clicks removed** (→ 5,341); other steps *not specified* [5] | Clicks on **12 learning sites**, aggregated at **weekly and monthly** intervals (top-influential: content, subpage, homepage, quiz) [5] | Binary pass/fail; **LSTM vs 1D-CNN vs traditional ML** (LSTM best, ≈90%); accuracy rises across the term; train/test ratio and imbalance handling *not specified* [5] |

---

## 3. Discussion

### 3.1 Collection

All four studies draw on OULAD [3] without additional collection, but at different scope: Adnan et al. [1] use the full set and integrate all three feature groups; Tomasevic et al. [2] combine engagement, performance and demographic data; Liu et al. [5] focus on the VLE clickstream merged with `studentInfo`; and Gunasekara & Saarela [4] deliberately use only a **3-module subset** as an XAI benchmark. Our pipeline, like [1], uses the full 32,593-record set across all three feature groups.

### 3.2 Cleaning

Where described, cleaning is light: Adnan et al. [1] mean-impute missing dates; Gunasekara & Saarela [4] drop excessively-missing rows/columns, normalise, and merge classes; Liu et al. [5] drop the 180 click-less students. Tomasevic et al. [2] do not report their preprocessing in accessible text. Notably, **none mean-imputes scores or treats "not submitted" as an informative signal** — a gap our pipeline fills with the `not_submitted` indicator.

### 3.3 Feature Engineering

This is where the studies differ most. Adnan et al. [1] introduce **time-aware truncation** — re-computing features cumulatively at fixed course-length percentages — which is the direct basis of our checkpoint design (though they use 20–100% while we add a 10% point). Liu et al. [5] show how raw clicks compress into per-site weekly/monthly counts. Tomasevic et al. [2] provide the empirical basis for prioritising engagement and performance over demographics.

### 3.4 Splitting / Validation

The studies rely on standard hold-out or k-fold cross-validation (10-fold in [1], 5-fold ×50 in [4]); only [1] enforces a temporal cut-off aligned with each checkpoint. Importantly, **none uses a group-aware split** keyed on the student, so a student with several module-presentations can fall in both train and test — a leakage risk our pipeline removes (Section "What we inherit").

---

## 4. What We Inherit

- **Time-aware checkpoint prediction** [1]: we adopt cumulative feature truncation at course-length percentages. Adnan et al. use 20/40/60/80/100%; we add a 10% point (10/20/40/60/80/100%) and treat **40–60%** as the reliable early window they report.

- **Feature-group prioritisation** [2]: following the finding that engagement and performance dominate while demographics contribute little, our engineering centres on the behavioural and assessment groups; demographics are kept for fairness analysis, not predictive reliance.

- **Clickstream aggregation** [5]: like Liu et al., we compress the ~10.6M-row clickstream into compact per-student features (total clicks, active days, per-activity-type counts, plus derived rates), but computed **per checkpoint** for the time-aware setting.

- **Leakage prevention** [1]: encoders, scaler and imputer are fitted on the training fold only, and all events after a checkpoint are removed before that checkpoint's features are built — extending the temporal discipline of [1].

- **Group-aware stratified split (our addition)**: unlike any surveyed study, we keep every record of a given `id_student` entirely in train or test, with a fixed 20% test set reused across checkpoints and 5-fold × 5-seed CV on the training portion — closing the student-level leakage gap left open by their row-level splits.

- **Quantitative explanation stability** [4]: Gunasekara & Saarela evaluate SHAP/LIME mainly qualitatively; we add a quantitative stability metric (Jaccard top-*k* + feature-importance standard deviation), moving beyond their qualitative assessment.

---

## References

[1] M. Adnan et al., "Predicting at-Risk Students at Different Percentages of Course Length for Early Intervention Using Machine Learning Models," *IEEE Access*, vol. 9, pp. 7519–7539, 2021.

[2] N. Tomasevic, N. Gvozdenovic, and S. Vranes, "An overview and comparison of supervised data mining techniques for student exam performance prediction," *Computers & Education*, vol. 143, art. 103676, 2020.

[3] J. Kuzilek, M. Hlosta, and Z. Zdrahal, "Open University Learning Analytics dataset," *Scientific Data*, vol. 4, art. 170171, 2017.

[4] S. Gunasekara and M. Saarela, "Explainable AI in Education: Techniques and Qualitative Assessment," *Applied Sciences*, vol. 15, no. 3, art. 1239, 2025.

[5] Y. Liu, S. Fan, S. Xu, A. Sajjanhar, S. Yeom, and Y. Wei, "Predicting Student Performance Using Clickstream Data and Machine Learning," *Education Sciences*, vol. 13, no. 1, art. 17, 2023.
