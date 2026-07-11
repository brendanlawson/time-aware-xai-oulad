# DSP391m – Group 1
## Report 3 – Task 3 | Data Collection, Cleaning & Analysis
### Data Source, License & Ethical Considerations


---

> **Deliverable (Step 30)**
> A written section presenting: (1) the origin and provenance of the OULAD dataset, (2) the applicable license and terms of use, and (3) the ethical considerations governing its use in this project. To be incorporated as Section 3.1 of Report 2 (Chapter 3). Citation: Kuzilek et al. (2017) and CC-BY 4.0 license link required.

---

## 1. Data Origin & Provenance

### 1.1. Dataset Overview

The Open University Learning Analytics Dataset (OULAD) is a publicly available educational dataset released by the Knowledge Media Institute (KMi) at The Open University (OU), United Kingdom. It was formally published in 2017 by Kuzilek, Hlosta, and Zdrahal as a data descriptor in *Scientific Data* (Nature Publishing Group).

OULAD is one of the most widely cited open datasets in the Learning Analytics and Educational Data Mining (EDM) research communities. As of 2025, the original data descriptor paper has accumulated several hundred citations across IEEE, ACM, Springer, and Elsevier publications.

### 1.2. Collection Context

The dataset was constructed from the Open University's Virtual Learning Environment (VLE), which hosts distance-learning courses for tens of thousands of students annually. Data was drawn from the 2013 and 2014 academic years and covers seven selected modules (courses) presented across multiple semesters.

The OU operates as a fully distance-learning institution, meaning all student–course interaction occurs digitally through the VLE. This makes it uniquely suited for learning analytics research: every student action — reading materials, submitting assessments, browsing resources — is captured as a timestamped log entry.

### 1.3. Dataset Composition

| Table | Content | Approx. Size |
|---|---|---|
| `studentInfo.csv` | Student demographics and final outcome (`final_result`) | 32,593 records |
| `studentRegistration.csv` | Module registration and withdrawal dates per student | 32,593 records |
| `studentAssessment.csv` | Assessment submission dates and scores | ~173,000 records |
| `studentVle.csv` | Daily clickstream logs (interactions with VLE activities) | ~10.6 million records |
| `assessments.csv` | Assessment metadata: type, weight, deadline | ~173 entries |
| `vle.csv` | Catalogue of VLE activity types | ~465 entries |
| `courses.csv` | Module duration (in days) per semester | 22 records |

**Key statistics:** 32,593 enrolments (28,785 distinct students) • 22 module–semester combinations • 7 CSV tables • 10,655,280 VLE interaction entries

### 1.4. Official Citation

> J. Kuzilek, M. Hlosta, and Z. Zdrahal, "Open University Learning Analytics dataset," *Scientific Data*, vol. 4, p. 170171, Nov. 2017, doi: [10.1038/sdata.2017.171](https://doi.org/10.1038/sdata.2017.171).

**Official dataset homepage:**
https://analyse.kmi.open.ac.uk/open_dataset

**Download mirrors:**
- [Kaggle — Open University Learning Analytics Dataset](https://www.kaggle.com/datasets/rocki37/open-university-learning-analytics-dataset)
- [UCI Machine Learning Repository — OULAD](https://archive.ics.uci.edu/dataset/349/open+university+learning+analytics+dataset)

---

## 2. License & Terms of Use

### 2.1. License Type

OULAD is released under the **Creative Commons Attribution 4.0 International License (CC-BY 4.0)**. This is one of the most permissive open licenses available and is widely used in scientific data publishing.

License reference: https://creativecommons.org/licenses/by/4.0/

### 2.2. What CC-BY 4.0 Permits

| Permission | Details |
|---|---|
| **Share** | Copy and redistribute the dataset in any medium or format. |
| **Adapt** | Remix, transform, and build upon the dataset for any purpose, including commercial use. |
| **Use in research** | Freely use in academic and applied research projects without restriction. |
| **Reproduce in publications** | Include data excerpts, tables, and derived outputs in academic reports and papers. |

### 2.3. Obligations Under CC-BY 4.0

The only requirement under CC-BY 4.0 is proper attribution. This project fulfils this obligation by:

1. Citing the original data descriptor paper (Kuzilek et al., 2017) in all sections referencing the dataset.
2. Including the full IEEE-format citation in this document and in the final report bibliography.
3. Stating the license type (CC-BY 4.0) in this ethics section and in the reproducibility documentation (Step 31).

### 2.4. No Additional Restrictions

The dataset carries no non-commercial clause, no share-alike requirement, and no no-derivatives restriction. The OU has not imposed additional usage terms beyond the CC-BY 4.0 license. The dataset may therefore be freely used, processed, and reported on within the scope of this academic capstone project.

---

## 3. Ethical Considerations

### 3.1. Anonymisation at Source

OULAD was anonymised by The Open University prior to public release. The anonymisation process was applied at the source institution and is described in the original data descriptor (Kuzilek et al., 2017). Specifically:

- All direct personal identifiers (names, email addresses, student ID numbers) have been removed and replaced with arbitrary numeric keys.
- Geographic data is reported at the regional level only (not postcode or address).
- Socioeconomic indicators (`imd_band`) are reported as band ranges, not precise values.
- Age is reported as a banded category (0–35, 35–55, 55+), not as exact birth dates.

As a result, no individual student can be re-identified from the published dataset under normal circumstances. This project does not attempt any re-identification and does not combine OULAD with any external dataset that could enable re-identification.

### 3.2. Compliance with Data Protection Principles

| Principle | How This Project Complies |
|---|---|
| **Lawfulness & transparency** | Dataset is publicly available under CC-BY 4.0; no special access required. |
| **Purpose limitation** | Data is used solely for academic research within DSP391m; not for commercial or surveillance purposes. |
| **Data minimisation** | Only the seven original CSV tables are used; no additional data collection is performed. |
| **Accuracy** | Source data is stored read-only (`/data/raw`) with md5 hash verification to prevent unintentional modification. |
| **Storage limitation** | Data is retained only for the duration of the project; not shared beyond the project team. |
| **No sensitive processing** | No special-category data (health, religion, political opinion) is present or processed. |

### 3.3. Absence of Consent Requirements

Because OULAD is secondary data — collected and anonymised by a third party (The Open University) under its own institutional ethical framework — this project is not required to obtain individual consent from the students represented in the dataset. The original data collection was conducted under the OU's internal ethics procedures, and the public release under CC-BY 4.0 constitutes the OU's authorisation for downstream research use.

### 3.4. Responsible Use Commitments

Beyond the minimum legal requirements, this project commits to the following responsible use practices:

1. The dataset is used only to build predictive models intended to support student success, not to penalise, surveil, or discriminate against any group.
2. Model outputs will be interpreted with awareness of potential algorithmic bias, particularly regarding demographic variables such as `imd_band`, `region`, and `disability` status.
3. No attempt will be made to infer personal identities, contact students, or share individual-level predictions outside the academic context of this project.
4. All derivative outputs (processed tables, trained models, EDA charts) will be stored securely and accessed only by project team members.

### 3.5. Potential Ethical Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Algorithmic bias against socioeconomic or demographic groups | Medium | Evaluate model performance separately per demographic subgroup; report disaggregated metrics. |
| Misuse of at-risk predictions to penalise rather than support students | Low (academic context) | Clearly frame all outputs as decision-support tools, not automated decisions. |
| Re-identification through data combination | Very low (data already anonymised) | No external data sources are combined with OULAD in this project. |
| Data breach or unauthorised access | Low | Data stored locally with read-only permissions; not uploaded to public repositories. |

---

## 4. Summary

> **Section 3.1 Summary for Report 2**
>
> The OULAD dataset (Kuzilek et al., 2017) was collected by The Open University from its Virtual Learning Environment during the 2013–2014 academic years and covers 32,593 students across 22 module–semester combinations. It is published under a Creative Commons Attribution 4.0 International (CC-BY 4.0) license, which permits unrestricted use, adaptation, and redistribution provided attribution is given. Prior to public release, the OU anonymised all personal identifiers at the source; no individual student can be re-identified from the published tables. This project uses the dataset solely for academic research within DSP391m, applies no additional data collection, and commits to responsible use practices that prioritise student wellbeing and guard against algorithmic bias.

---

*DSP391m – Group 1*
