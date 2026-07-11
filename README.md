# Time-Aware Explainable Machine Learning for Early At-Risk Student Prediction on OULAD

> *Phát hiện sớm sinh viên có nguy cơ học tập kém bằng học máy có khả năng giải thích*

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/code%20license-MIT-green.svg)](LICENSE)
[![Data: CC-BY 4.0](https://img.shields.io/badge/data-CC--BY%204.0-lightgrey.svg)](https://analyse.kmi.open.ac.uk/open_dataset)
[![Status: WIP](https://img.shields.io/badge/status-work%20in%20progress-orange.svg)](#project-status)

A reproducible machine-learning pipeline that predicts at-risk students **early** (at multiple points across a course), **explains** every prediction with SHAP and LIME, and **quantifies the stability** of those explanations — all on the public Open University Learning Analytics Dataset (OULAD). This repository accompanies the DSP391m Data Science Capstone Project at FPT University.

---

## Table of Contents

1. [Motivation](#1-motivation)
2. [Research Questions](#2-research-questions)
3. [Contributions](#3-contributions)
4. [Dataset](#4-dataset)
5. [Repository Structure](#5-repository-structure)
6. [Methodology](#6-methodology)
7. [Getting Started](#7-getting-started)
8. [Reproducibility](#8-reproducibility)
9. [Team & Responsibilities](#9-team--responsibilities)
10. [Project Status](#10-project-status)
11. [Citation](#11-citation)
12. [References](#12-references)
13. [License](#13-license)

---

## 1. Motivation

Failure and drop-out remain persistent problems in Virtual Learning Environments, while the behavioural data captured by Learning Management Systems is largely under-used for timely intervention. Existing predictive models exhibit three recurring limitations:

- **Opacity.** The strongest models behave as black boxes, so instructors cannot see *why* a student is flagged and therefore cannot act with confidence.
- **Lateness.** Most studies predict at end-of-course, when intervention is no longer effective.
- **Class imbalance.** In the literature the at-risk class is usually a minority that models drift away from. Under this project's label mapping ({Fail, Withdrawn} vs {Pass, Distinction}) it is in fact a slight majority on OULAD — 52.8% of enrolments, imbalance ratio 1.12 — so imbalance handling is studied here as a controlled robustness question (RQ3), not as rescuing a rare class.

A concept-centric review of 27 representative papers (2019–2026) shows that *time-aware prediction*, *explainable AI*, and *imbalance handling* have each been studied in isolation but are rarely integrated — and never simultaneously on OULAD. This project targets exactly that empty cell.

## 2. Research Questions

| ID  | Question |
| --- | --- |
| **RQ1** | At different course-progress checkpoints (10–100% of course length), which algorithm gives the best at-risk prediction on OULAD, and how early can a prediction be considered reliable? |
| **RQ2** | How consistent are the explanations produced by SHAP and LIME for the same model, and how does their stability change across time and across imbalance-handling strategies? |
| **RQ3** | How does imbalance handling (SMOTE / ADASYN / class weighting) affect both predictive accuracy and explanation quality? |

## 3. Contributions

1. **An integrated time-aware XAI framework** that couples checkpoint-based prediction with SHAP/LIME explanations at each checkpoint — not previously done end-to-end on OULAD.
2. **An extended OULAD benchmark** adding ensemble methods (Random Forest, XGBoost, LightGBM) to the comparison that Tomasevic et al. (2020) did not include.
3. **A quantitative explanation-stability metric** (Jaccard top-*k* agreement and standard deviation of feature importance across seeds), addressing the qualitative-only gap noted in prior reviews.
4. **An optional instructor dashboard** that turns predictions into a practical early-warning tool.

## 4. Dataset

This project uses the **Open University Learning Analytics Dataset (OULAD)** (Kuzilek et al., 2017).

| Property | Value |
| --- | --- |
| Enrolments (student × module-presentation) | 32,593 (28,785 distinct students) |
| Module-presentations | 22 |
| Relational tables | 7 |
| Feature groups | Demographics · Engagement (VLE clickstream) · Performance (assessments) |
| Target | `final_result` mapped to a binary label: **at-risk** = {Fail, Withdrawn}, **not-at-risk** = {Pass, Distinction} |
| License | CC-BY 4.0 (anonymised at source) |
| Source | <https://analyse.kmi.open.ac.uk/open_dataset> · [Kaggle mirror](https://www.kaggle.com/datasets/anlgrbz/student-demographics-online-education-dataoulad) |

> The raw CSVs are **not** committed to the repository. Download them and place them under `data/raw/` as described in [Getting Started](#7-getting-started). File integrity is verified against the **committed** checksums in `data/oulad_md5_reference.txt` (via `python setup_raw_data.py` or `md5sum -c`).

## 5. Repository Structure

```text
time-aware-xai-oulad/
├── data/
│   ├── raw/                       # Seven original OULAD CSVs (git-ignored, read-only)
│   ├── interim/                   # Master table + intermediate parquet (git-ignored)
│   ├── checkpoints/               # Six time-sliced datasets, t = 10/20/40/60/80/100% (git-ignored)
│   └── splits/                    # Frozen train/test split — test_student_ids.csv is committed
├── notebooks/
│   ├── schema_survey.ipynb
│   ├── 00_data_understanding.ipynb
│   ├── 01_build_master_table.ipynb
│   ├── 02_eda.ipynb
│   ├── 03_make_checkpoints.ipynb
│   ├── 04_preprocessing.ipynb
│   ├── 05_modeling.ipynb
│   └── 06_xai.ipynb
├── src/
│   ├── config.py                  # Central paths, constants, checkpoint map
│   ├── plots.py
│   ├── data/
│   │   ├── io_utils.py
│   │   ├── time_utils.py          # cut_at_checkpoint(), checkpoint map
│   │   ├── build_engagement_features.py
│   │   ├── build_performance_features.py
│   │   ├── build_master_table.py
│   │   └── make_checkpoints.py
│   ├── eda/                       # EDA computations + shared plot style
│   ├── features/
│   │   └── preprocessing.py       # encoding, scaling, imputation (fit on train only)
│   ├── evaluation/
│   │   ├── split_harness.py       # StratifiedGroupKFold, fixed test set
│   │   ├── make_split.py          # materialises the frozen train/test split
│   │   └── stat_tests.py          # Friedman / Wilcoxon model comparisons
│   ├── modeling/
│   │   ├── train.py               # LR, RF, XGBoost, LightGBM, ANN at every checkpoint
│   │   ├── predict.py
│   │   └── threshold.py
│   └── xai/
│       ├── shap_explain.py        # SHAP (global + local)
│       ├── lime_explain.py        # LIME (local)
│       └── stability.py           # Jaccard top-k, feature-importance std
├── tests/
│   └── test_leakage.py            # asserts no records beyond each checkpoint
├── tools/                         # ~16 one-shot scripts that generate report artifacts
├── models/                        # Trained model bundles (*.joblib, git-ignored)
├── reports/
│   ├── figures/
│   ├── tables/                    # model_metrics, imbalance_comparison, xai_*, …
│   ├── slides/
│   ├── guide/
│   └── data_understanding/
├── docs/                          # 01_data_specification … 08_agreements + bilingual READMEs
├── requirements.txt
├── environment.yml
├── pyproject.toml
├── Makefile
├── .gitignore
├── LICENSE
└── README.md
```

## 6. Methodology

The workflow follows the **CRISP-DM** lifecycle and is organised into six phases, each producing an independently assessable deliverable.

| Phase | Focus | Key output |
| --- | --- | --- |
| **1. Data Preparation** | Merge the 7 OULAD tables into a master table; standardise the 3 feature groups; build the at-risk label; slice data at 6 checkpoints. | `master_raw.parquet`, six checkpoint datasets |
| **2. Benchmarking** | Compare LR, RF, XGBoost, LightGBM, ANN with repeated 5-fold cross-validation (5 seeds). | Model leaderboard (F1, ROC-AUC, PR-AUC, at-risk recall) |
| **3. Time-Aware Prediction** | Re-run the benchmark at each checkpoint → performance-vs-progress curve; locate the earliest reliable checkpoint **(RQ1)**. | Performance curves |
| **4. Imbalance Handling** | Compare no-resampling / class-weighting / SMOTE / ADASYN; measure the effect on accuracy *and* explanations **(RQ3)**. | Imbalance-strategy comparison |
| **5. XAI Layer** | SHAP (global + local) and LIME (local); quantify stability via Jaccard top-*k* and feature-importance std across seeds **(RQ2)**. | Explanation-stability report |
| **6. Dashboard (optional)** | Streamlit/Flask app: at-risk list + local SHAP explanation + intervention hints. | Instructor dashboard |

**Leakage prevention** is treated as a first-class concern: temporal cuts retain only records that exist before each checkpoint; the test set is fixed across all six checkpoints; and every component that learns from data (encoders, scaler, resampling) is fit on the training fold only.

## 7. Getting Started

> 🇻🇳 **Thành viên:** xem hướng dẫn từng bước (clone → tải data → sinh đủ `.parquet`) tại **[`SETUP_VI.md`](SETUP_VI.md)**.

### Prerequisites

- Python 3.10 or later
- `git`

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/<org-or-user>/time-aware-xai-oulad.git
cd time-aware-xai-oulad

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Obtain the data

```bash
# Download the seven OULAD CSVs from the official source or the Kaggle mirror,
# then place them under data/raw/ (the directory is git-ignored):
#   assessments.csv  courses.csv  studentAssessment.csv  studentInfo.csv
#   studentRegistration.csv  studentVle.csv  vle.csv
#
# Verify integrity against the committed reference checksums (either way works):
python setup_raw_data.py
md5sum -c data/oulad_md5_reference.txt
```

### Reproduce the pipeline

```bash
# Build the master table (Restart & Run All is idempotent)
jupyter nbconvert --to notebook --execute notebooks/01_build_master_table.ipynb

# Run the leakage tests
pytest tests/
```

## 8. Reproducibility

This project is designed so that an external reader can reproduce every result:

- **Deterministic seeds** are fixed throughout (`RANDOM_SEED = 42`).
- **Data provenance** is pinned by the committed `data/oulad_md5_reference.txt` (md5 per raw file); `setup_raw_data.py` verifies every download against it and records a local manifest.
- **Environment** is pinned in `requirements.txt` and `environment.yml`.
- **Notebooks** execute top-to-bottom without manual intervention (`Restart & Run All`).
- **Automated tests** (`tests/test_leakage.py`) guard against temporal leakage at all six checkpoints.

## 9. Team & Responsibilities

Group 1, DSP391m — FPT University. Supervisor: **Nguyễn Thị Hoàng Yến**.

| Member | Role | Responsibility |
| --- | --- | --- |
| Khoa | Methodology Lead | Predictive modelling, time-aware prediction (Themes 1 & 2) |
| Bình | XAI Lead | Explainability (SHAP/LIME), explanation stability (Theme 3) |
| Đức | Modeling Lead | Model development, class-imbalance handling (Themes 1 & 4) |
| Phúc | Implementation Lead | Data pipeline, experiment harness, evaluation |
| Sơn | Literature Review Lead | Introduction, literature review, references |
| An | Backend & Dashboard Lead | Model packaging, Streamlit dashboard (Phase 6a) |

## 10. Project Status

**Report 2 — Data Tasks (collection, cleaning, EDA): complete.** The full data pipeline (`src/data`, `src/features`, `src/eda`, `src/evaluation`) builds the master table (32,593 × 33), six time-aware checkpoint datasets, and the leakage-safe split harness; the automated leakage/split test suite (`tests/test_leakage.py`) passes; EDA figures, result tables and the bilingual documentation set live under `reports/` and `docs/`. Every work item (STT 1–40) and its artifact are mapped in [`docs/README_EN.md`](docs/README_EN.md) (Vietnamese: `docs/README_VI.md`).

**Phase 2–3 — Benchmarking + Time-Aware Prediction: complete.** The five candidate algorithms (Logistic Regression, Random Forest, XGBoost, LightGBM, ANN) are benchmarked across all six checkpoints with a leakage-safe held-out test and repeated 5-fold × 5-seed cross-validation at t=100% (`src/modeling/train.py`). XGBoost leads; at-risk prediction meets the reliability bar (recall ≥ 0.80) from the **40% checkpoint** on the full enrolment cohort, while on the actionable still-enrolled cohort it reaches the bar only at course end (see `reports/tables/sensitivity_active_xgb.csv`) — both cohorts are reported (RQ1). Results: `reports/tables/{model_metrics,cv_summary,time_aware_best}.csv` and the `time_aware_*` / `model_benchmark` figures.

**Phase 4–5 — Imbalance Handling + XAI: artifacts in place.** Phase 4 compares no-resampling / class-weighting / SMOTE / ADASYN at t=100% (the accuracy half of RQ3): all four strategies differ by ≤ 0.005 on every metric, so the headline benchmark keeps the no-resampling baseline (`reports/tables/imbalance_comparison.csv`). Phase 5 delivers SHAP/LIME explanations and their stability metrics (`reports/tables/xai_*.csv` + figures). Remaining: the instructor dashboard (Phase 6) and the final report.

## 11. Citation

If you use this work, please cite it as:

```bibtex
@misc{group1_2026_timeaware_xai_oulad,
  title        = {Time-Aware Explainable Machine Learning for Early
                  At-Risk Student Prediction on OULAD},
  author       = {S{\o}n and Khoa and An and {\DJ}{\'u}c and Ph{\'u}c and B{\`i}nh},
  howpublished = {DSP391m Data Science Capstone Project, FPT University},
  year         = {2026},
  note         = {Supervisor: Nguy{\~{\^e}}n Th{\d{i}} Ho{\`a}ng Y{\'{\^e}}n}
}
```

## 12. References

1. N. Tomasevic, N. Gvozdenovic, S. Vranes. *An overview and comparison of supervised data mining techniques for student exam performance prediction.* Computers & Education, 2020.
2. M. Adnan et al. *Predicting at-risk students at different percentages of course length for early intervention.* IEEE Access, 2021.
3. S. Gunasekara, M. Saarela. *Explainable AI in Education: Techniques and Qualitative Assessment.* Applied Sciences, vol. 15, no. 3, art. 1239, 2025.
4. H. Alamri, B. Alharbi. *Explainable Student Performance Prediction Models: A Systematic Review.* IEEE Access, 2021.
5. J. Kuzilek, M. Hlosta, Z. Zdrahal. *Open University Learning Analytics Dataset (OULAD).* Scientific Data, 2017.
6. S. Lundberg, S.-I. Lee. *A Unified Approach to Interpreting Model Predictions (SHAP).* NeurIPS, 2017.
7. M. Ribeiro, S. Singh, C. Guestrin. *"Why Should I Trust You?" Explaining the Predictions of Any Classifier (LIME).* KDD, 2016.
8. N. V. Chawla et al. *SMOTE: Synthetic Minority Over-sampling Technique.* JAIR, 2002.
9. J. Webster, R. T. Watson. *Analyzing the past to prepare for the future: Writing a literature review.* MIS Quarterly, 2002.

The full 30-review corpus is documented in the project proposal (Appendix A).

## 13. License

- **Code** is released under the [MIT License](LICENSE).
- **The OULAD dataset** is the property of The Open University and is distributed separately under [CC-BY 4.0](https://analyse.kmi.open.ac.uk/open_dataset); it is **not** redistributed in this repository.
