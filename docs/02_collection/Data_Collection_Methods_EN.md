# Data Collection Methods and Source Selection

**Justifying the Use of the OULAD Public Dataset for At-Risk Student Prediction**

DSP391m – Group 1 · Report 2 (Data Tasks), Chapter 3 · Work item STT 23 (Son)

---

## 1. Overview

Every data-science project begins with a decision about where and how data will be obtained. This chapter analyses the main categories of data sources, weighs their trade-offs, and then argues why the Open University Learning Analytics Dataset (OULAD) is the appropriate choice for the project *"Time-Aware Explainable Machine Learning for Early At-Risk Student Prediction on OULAD"*.

---

## 2. Types of Data Sources and Their Trade-offs

Four broad categories of data sources are commonly considered in educational-data-mining and learning-analytics projects.

### 2.1 Internal Institutional Databases

An institution's own student information system (SIS), LMS logs, and grade records constitute the richest possible data for a specific context. The collection design is fully controlled, field definitions are known exactly, and linkage across tables is straightforward.

**Trade-offs:** Data are not publicly accessible; ethics approval and data-sharing agreements are required for external research. Results are institution-specific and difficult to replicate or compare across studies.

### 2.2 Application Programming Interfaces (APIs)

Many learning platforms (Canvas, Moodle, edX) expose REST APIs that allow programmatic extraction of course activity, forum posts, and grade items. APIs provide fresh, structured data and can be automated.

**Trade-offs:** API access requires credentials and institutional permission. Rate limits and schema changes can interrupt long-running collection. Personally identifiable information (PII) is typically present, requiring a separate anonymisation step before analysis. Reproducibility is limited because the platform state changes over time.

### 2.3 Web Scraping

Public-facing course catalogues, student reviews, or discussion forums can be scraped to supplement structured data. This method can reach information not exposed through an API.

**Trade-offs:** Legal and ethical status varies by jurisdiction and terms of service. HTML structure changes frequently, making scrapers brittle. Data quality is inconsistent, and PII may be inadvertently collected. Reproducibility is low because web content changes.

### 2.4 Public / Secondary Datasets

Curated datasets released by research institutions or government bodies are available for download, already anonymised, and accompanied by documented schemas and licenses. Secondary data are collected by a third party for purposes that may differ from the researcher's own objectives.

**Trade-offs:** No control over the original collection design (instruments, timing, feature selection). However, availability is immediate, anonymisation is handled at source, and the same dataset can be used by multiple independent studies, enabling direct comparability.

### 2.5 Summary Comparison

| Criterion | Internal DB | API | Web Scraping | Public / Secondary |
|---|---|---|---|---|
| Control over collection design | High | Medium | Low | None |
| Immediate availability | Low | Medium | Medium | **High** |
| Anonymisation required | Yes | Yes | Yes | **Already done** |
| Reproducibility | Low | Low | Very low | **High** |
| Comparability with prior work | Low | Low | Low | **High** |
| Ethical/legal complexity | High | Medium | High | **Low (CC licence)** |

---

## 3. Source-Selection Criteria for This Project

The project requires a dataset that satisfies all of the following conditions simultaneously:

1. **Publicly available** — the dataset must be freely downloadable without institutional access agreements, ensuring that findings can be fully reproduced by independent researchers.
2. **Three required feature groups present** — (a) *student demographics* (age band, highest education, disability status, region, IMD band), (b) *engagement / VLE clickstream* (daily interaction counts with virtual learning environment resources), and (c) *assessment performance* (scores and submission dates for coursework and examinations).
3. **A labelled target variable** — the field `final_result` must exist, taking values Pass, Distinction, Fail, or Withdrawn, so that the binary classification target `at_risk = {Fail, Withdrawn}` can be derived directly.
4. **Used by the base studies** — to enable direct methodological comparison, the dataset must be the same one used in the primary reference studies [1] and [2].

---

## 4. Why OULAD Fits This Project

The Open University Learning Analytics Dataset (OULAD) [3] was released by The Open University (UK) and is publicly hosted at https://analyse.kmi.open.ac.uk/open_dataset with a Kaggle mirror.

**Key characteristics:**

- **Scale:** 32,593 student-module-presentation records; 28,785 unique students; 22 module-presentations across 7 relational tables.
- **Feature coverage:** All three required feature groups are present — `studentInfo` (demographics), `studentVle` (daily VLE click counts), and `studentAssessment` / `assessments` (scores and deadlines).
- **Label:** The `final_result` column in `studentInfo` enables direct construction of the binary at-risk label.
- **Static download:** The dataset is a fixed snapshot, meaning every researcher downloads an identical file. This guarantees byte-for-byte reproducibility of preprocessing and modelling pipelines.
- **Anonymisation at source:** The Open University anonymised all records before release. No additional PII-handling steps are required by this project.
- **Prior-work alignment:** Both base studies [1] and [2] use OULAD. Using the same dataset enables direct comparison of model performance metrics and methodology, which is an explicit goal of this project.
- **License:** CC-BY 4.0 — only correct citation is required, with no restrictions on academic or commercial reuse.

---

## 5. Note on Secondary Data

OULAD is secondary data: it was collected and curated by The Open University for their own operational and research purposes, then released publicly. This entails a trade-off that the project team acknowledges.

**Advantages:** The data are immediately available, already anonymised, and stable. Any team worldwide can reproduce the exact same experiment.

**Disadvantages:** The project has no control over which features were recorded, how the VLE was designed, which assessment types were used, or how attrition was defined. Generalisability to other institutions depends on how similar their learning environments are to The Open University's.

Given the project's stated goal — developing and benchmarking a time-aware, explainable model — these limitations are acceptable. The benefit of reproducibility and comparability with prior work outweighs the lack of collection-design control.

---

## 6. Data Privacy, Ethics, and Legal Compliance

OULAD is anonymised at source by The Open University. No student names, email addresses, or national identifiers appear in any table. The dataset is released under the Creative Commons Attribution 4.0 International (CC-BY 4.0) licence.

The project's obligations are therefore limited to:

- Citing the dataset correctly as [3].
- Not attempting to re-identify individuals from the data.
- Acknowledging the licence in all publications and submissions.

No additional institutional ethics approval is required for analysis of this publicly released, anonymised dataset within the scope of academic coursework.

---

## References

[1] M. Adnan et al., "Predicting at-Risk Students at Different Percentages of Course Length for Early Intervention Using Machine Learning Models," *IEEE Access*, vol. 9, pp. 7519–7539, 2021.

[2] N. Tomasevic, N. Gvozdenovic, and S. Vranes, "An overview and comparison of supervised data mining techniques for student exam performance prediction," *Computers & Education*, vol. 143, art. 103676, 2020.

[3] J. Kuzilek, M. Hlosta, and Z. Zdrahal, "Open University Learning Analytics dataset," *Scientific Data*, vol. 4, art. 170171, 2017.
