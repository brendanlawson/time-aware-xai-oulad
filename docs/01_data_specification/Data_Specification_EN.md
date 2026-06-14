# Data Specification for Time-Aware Explainable Machine Learning on OULAD

**DSP391m – Group 1 · Report 2 (Data Tasks), Chapter 3 · Task 3.1 — Data Specification**

---

## Abstract

This document specifies the data requirements for the project "Time-Aware Explainable ML for Early At-Risk Student Prediction on OULAD." Three research questions govern the specification: (RQ1) determining the earliest reliable checkpoint for at-risk prediction and the most effective algorithm at that point; (RQ2) assessing the stability of SHAP/LIME post-hoc explanations across time windows; and (RQ3) evaluating how class-imbalance handling strategies—SMOTE, ADASYN, and class-weight adjustment—affect predictive accuracy and explanation coherence. Each requirement is derived directly from at least one research question and mapped to a specific table within the Open University Learning Analytics Dataset (OULAD) [3]. The analysis confirms that OULAD supplies all necessary data groups—demographic context, time-stamped behavioural engagement, and longitudinal academic performance—at sufficient scale and temporal granularity to support all three research questions.

---

## 1. Introduction

Early identification of at-risk students is a central challenge in learning analytics. Intervening before a student disengages or fails requires predictive models that are both accurate at early course-progress checkpoints and interpretable to academic advisors. This project operationalises the problem on OULAD [3], a publicly available relational dataset released by The Open University (UK). Before any modelling work can proceed, the data required must be rigorously identified and justified against the research questions. This document fulfils that obligation as Task 3.1 of the DSP391m capstone deliverable sequence.

---

## 2. Research Questions and Data Needs

The three research questions impose distinct data requirements:

- **RQ1** (Earliest reliable checkpoint): requires a time-indexed record of each student's behaviour and performance so that features can be computed at multiple discrete progress thresholds (e.g., 20%, 40%, 60%, 80% of course length). This necessitates both clickstream events and assessment submissions carrying date information, together with the total course duration against which progress percentages are calculated.

- **RQ2** (Explanation stability): requires that the same feature vectors used for prediction be available at each checkpoint so that SHAP and LIME attribution values can be compared across time. No additional tables are needed beyond those serving RQ1, but it reinforces the requirement for consistent, well-defined feature columns.

- **RQ3** (Imbalance handling): requires a binary at-risk outcome label and knowledge of its marginal distribution across the dataset. Both SMOTE/ADASYN (which synthesise minority-class samples) and class-weight adjustment operate on the label column and the full feature matrix. This makes the outcome variable and the complete feature set jointly necessary.

---

## 3. Data Requirements Mapped to OULAD Tables

Table 1 presents each data requirement, the research question(s) it serves, and the OULAD source table(s) that supply it.

**Table 1. Data Requirements and OULAD Sources**

| Requirement | Purpose / Why Required | OULAD Source Table(s) | Key Column(s) |
|---|---|---|---|
| Binary at-risk outcome label | Defines the prediction target; required by all three RQs | `studentInfo` | `final_result` (Pass/Distinction → not-at-risk; Fail/Withdrawn → at-risk) |
| Timestamped behavioural engagement | RQ1 needs time-aware signals to build checkpoint features; RQ2 needs consistent engagement features | `studentVle` (~10.6 M rows), `vle` | `date`, `sum_clicks`, `id_site`, `activity_type` |
| Longitudinal academic performance | Early score signals for checkpoint features (RQ1, RQ2); contributes to class structure (RQ3) | `studentAssessment`, `assessments` | `date_submitted`, `score`, `is_banked`, `assessment_type`, `weight`, `date` (deadline) |
| Demographic context | Secondary features for fairness analysis and model input (all RQs) | `studentInfo` | `gender`, `region`, `highest_education`, `imd_band`, `age_band`, `num_of_prev_attempts`, `studied_credits`, `disability` |
| Student registration timeline | Captures late registration and early withdrawal as behavioural signals (RQ1) | `studentRegistration` | `date_registration`, `date_unregistration` |
| Course timeline / duration | Converts raw event dates to course-progress percentages (RQ1) | `courses` | `module_presentation_length` |

---

## 4. Feature Groups and Target Variable

Three feature groups are constructed from the tables identified above, plus the target variable:

**4.1 Demographic Features**
Sourced from `studentInfo` and `studentRegistration`. These include gender, region, highest prior education, IMD deprivation band, age band, number of previous attempts, studied credits, disability status, date of registration, and (where applicable) date of unregistration. Demographic features are static per student-module-presentation record and serve as baseline covariates.

**4.2 Engagement (VLE) Features**
Sourced from `studentVle` (interaction events) joined to `vle` (activity type metadata). Raw clickstream data (~10,655,280 interactions) is aggregated by student, module-presentation, and course-progress checkpoint to produce counts and rates of activity per type (e.g., `oucontent`, `quiz`, `resource`, `forumng`). The `date` column in `studentVle` is essential: it is the temporal anchor that allows features to be truncated at each checkpoint threshold.

**4.3 Performance (Assessment) Features**
Sourced from `studentAssessment` (submission records) joined to `assessments` (assessment metadata). Features include cumulative weighted score, proportion of assessments submitted on time, and whether any assessment was banked. The `date_submitted` column in `studentAssessment` enables time-aware truncation analogous to the VLE engagement approach.

**4.4 Target Variable**
The binary label is derived from `final_result` in `studentInfo`. Records with `final_result` ∈ {Fail, Withdrawn} are labelled at-risk (positive class = 1); records with {Pass, Distinction} are labelled not-at-risk (0). The observed at-risk rate across the dataset is approximately 52.8%, indicating a mild class imbalance that motivates RQ3.

---

## 5. Data Grain and Composite Key

The unit of analysis is one record per **(id\_student, code\_module, code\_presentation)** triple. Because a single student may enrol in multiple module-presentations, the composite key of these three columns is required to uniquely identify each observation. All feature tables are joined on this composite key before any modelling takes place. The final analytical dataset contains **32,593** such records, drawn from **28,785** unique students across **22** module-presentations.

---

## 6. Role of Each OULAD Table

Table 2 summarises why all seven OULAD tables are required and indicates which are time-indexed.

**Table 2. OULAD Table Roles**

| Table | Role in This Study | Time-Indexed? |
|---|---|---|
| `studentInfo` | Provides outcome label and all demographic features | No |
| `studentRegistration` | Provides registration and withdrawal dates per enrolment | Partial (`date_registration`, `date_unregistration`) |
| `studentVle` | Primary source of behavioural engagement; ~10.6 M clickstream events | Yes (`date`) |
| `vle` | Maps `id_site` to `activity_type`; required to create per-type engagement features | No |
| `studentAssessment` | Assessment submission records with submission date and score | Yes (`date_submitted`) |
| `assessments` | Provides assessment type, weight, and deadline date; necessary to compute weighted performance features | Partial (`date` as deadline) |
| `courses` | Provides `module_presentation_length` to convert event dates to progress percentages | No |

The time-indexed columns—`studentVle.date` and `studentAssessment.date_submitted`—are the architectural foundation of the time-aware requirement. Without them, checkpoint-based truncation (essential to RQ1 and RQ2) cannot be performed.

---

## 7. Data Scale and Sufficiency

The following scale statistics confirm that OULAD is adequate for the intended study:

- **32,593** student-module-presentation records (analytical grain)
- **28,785** unique students
- **22** module-presentations (7 courses × multiple presentation years)
- **7** relational tables
- **10,655,280** VLE interaction rows
- **173,912** assessment submission rows
- **~52.8%** at-risk rate (mild imbalance; warrants but does not severely constrain modelling)

The dataset's scale is sufficient for training and evaluating multiple classifiers at each of several checkpoint thresholds, for generating stable SHAP/LIME attributions, and for comparing three imbalance-handling strategies. The temporal granularity (daily resolution in both `studentVle` and `studentAssessment`) is sufficient to operationalise checkpoint thresholds at fine intervals.

---

## 8. Data Adequacy Conclusion

OULAD supplies all data groups required by RQ1–RQ3: a binary outcome label, time-stamped behavioural engagement, longitudinal assessment performance, and demographic context. The composite key `(id_student, code_module, code_presentation)` ensures unambiguous linkage across all seven tables. With over 32,000 analytical records, more than 10.6 million timestamped interaction events, and a temporal resolution of one day, the dataset provides sufficient scale and granularity to support time-aware checkpoint modelling, explanation-stability analysis, and imbalance-handling experiments. No external data sources are required to address the three research questions.

---

## References

[3] J. Kuzilek, M. Hlosta, Z. Zdrahal, "Open University Learning Analytics dataset," *Scientific Data*, vol. 4, art. 170171, 2017.
