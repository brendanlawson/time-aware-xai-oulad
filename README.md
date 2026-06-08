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
- **Class imbalance.** The at-risk class is the minority; models drift toward predicting "Pass" and miss the very students who need support.

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
| Students | 32,593 |
| Module-presentations | 22 |
| Relational tables | 7 |
| Feature groups | Demographics · Engagement (VLE clickstream) · Performance (assessments) |
| Target | `final_result` mapped to a binary label: **at-risk** = {Fail, Withdrawn}, **not-at-risk** = {Pass, Distinction} |
| License | CC-BY 4.0 (anonymised at source) |
| Source | <https://analyse.kmi.open.ac.uk/open_dataset> · [Kaggle mirror](https://www.kaggle.com/datasets/anlgrbz/student-demographics-online-education-dataoulad) |

> The raw CSVs are **not** committed to the repository. Download them and place them under `data/raw/` as described in [Getting Started](#7-getting-started). File integrity is verified via the checksums recorded in `data/data_manifest.txt`.

## 5. Repository Structure

```text
time-aware-xai-oulad/
├── data/
│   ├── raw/                  # Seven original OULAD CSVs (git-ignored, read-only)
│   ├── interim/              # Aggregated / merged intermediate tables
│   ├── checkpoints/          # Six time-sliced datasets (t = 10/20/40/60/80/100%)
│   └── data_manifest.txt     # File name, md5 hash, size, download date
├── notebooks/
│   ├── 01_build_master_table.ipynb
│   ├── 02_eda.ipynb
│   ├── 03_benchmarking.ipynb
│   ├── 04_time_aware.ipynb
│   ├── 05_imbalance.ipynb
│   └── 06_xai_stability.ipynb
├── src/
│   ├── data/
│   │   ├── build_master_table.py
│   │   └── time_utils.py          # cut_at_checkpoint(), checkpoint_map
│   ├── features/
│   │   └── preprocessing.py       # encoding, scaling, imputation (fit on train only)
│   ├── models/
│   │   └── benchmark.py           # LR, RF, XGBoost, LightGBM, ANN
│   ├── evaluation/
│   │   ├── metrics.py             # F1, ROC-AUC, PR-AUC, at-risk recall
│   │   └── split_harness.py       # StratifiedGroupKFold, fixed test set
│   └── xai/
│       ├── explain.py             # SHAP (global+local), LIME (local)
│       └── stability.py           # Jaccard top-k, feature-importance std
├── tests/
│   └── test_leakage.py            # asserts no records beyond each checkpoint
├── dashboard/                     # Optional Streamlit early-warning app
├── reports/
│   ├── proposal/                  # Report 1 — Project Proposal
│   ├── data_tasks/                # Report 2 — Collection, Cleaning, EDA
│   └── figures/
├── docs/
│   └── data_dictionary.md
├── requirements.txt
├── environment.yml
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
# Verify integrity against the recorded checksums:
md5sum -c data/data_manifest.txt
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
- **Data provenance** is recorded in `data/data_manifest.txt` (version, md5 hash, download date).
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
| Sơn | Literature Review Lead | Learning-analytics context, review synthesis (Theme 5) |
| An | Documentation Lead | Background, reporting, references (Theme 5) |

## 10. Project Status

**Work in progress.** Current phase: Report 2 — Data Tasks (collection, cleaning, EDA). The repository scaffold and reproducibility tooling are being established; modelling and XAI phases follow per the seven-week work plan.

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
3. S. Gunasekara, M. Saarela. *Explainable AI in Education: Techniques and Qualitative Assessment.* Applied Sciences, 2025.
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
