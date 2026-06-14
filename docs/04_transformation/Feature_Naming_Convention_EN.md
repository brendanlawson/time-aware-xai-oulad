# Feature Naming Convention for Derived Features

**Subtitle:** Ensuring Readable SHAP/LIME Explanations Through Consistent Feature Names

_DSP391m – Group 1 · Report 2 (Data Tasks) · Work item STT 40 (Binh)_

---

## 1. Purpose

Machine-learning explainability tools such as SHAP and LIME display feature names verbatim in their outputs. If a feature is named `f_017` or `x3`, an instructor reading the explanation cannot tell what the number means. This document establishes a mandatory naming convention for every derived feature produced in this project so that explanations are immediately interpretable without consulting a separate lookup table.

The convention was reviewed and approved by all Group 1 members and applies to every feature added to the master table and downstream checkpoint datasets.

---

## 2. Naming Rules

All feature names follow **snake\_case** (lowercase letters, digits, and underscores only — no spaces, no camelCase, no hyphens).

### 2.1 Prefix/Suffix Semantics

| Pattern | Meaning | Example |
|---|---|---|
| `n_...` | Integer count of something | `n_days_active`, `n_assessments_submitted` |
| `clicks_<activity_type>` | Click count for a specific VLE activity type | `clicks_forumng`, `clicks_quiz` |
| `..._to_date` | Value accumulated using **only** data up to the current checkpoint (no future leakage) | `mean_score_to_date`, `weighted_score_to_date` |
| `total_...` | Sum aggregation made explicit | `total_clicks` |
| `max_...` | Maximum aggregation made explicit | `max_clicks_single_day` |
| `mean_...` | Arithmetic mean aggregation made explicit | `mean_clicks_per_active_day` |

### 2.2 General Rules

1. Names must describe **what** is measured, not **how** it was computed.
2. The activity-type segment in `clicks_<activity_type>` must match the exact string used in the OULAD `vle.csv` `activity_type` column (e.g., `forumng`, `oucontent`, `resource`).
3. Boolean/binary columns use an adjective or past-participle form (`at_risk`, `not_submitted`).
4. Names must not exceed 40 characters.

---

## 3. Canonical Feature List

The table below is the single source of truth for all features used in modelling. Any addition must follow this convention and be appended here.

| Feature | Meaning | Group |
|---|---|---|
| `total_clicks` | Total VLE clicks by the student up to checkpoint | Engagement |
| `n_days_active` | Number of distinct days with at least one click | Engagement |
| `clicks_forumng` | Clicks on Forum-NG activity type | Engagement |
| `clicks_oucontent` | Clicks on OUContent activity type | Engagement |
| `clicks_resource` | Clicks on Resource activity type | Engagement |
| `clicks_homepage` | Clicks on Homepage activity type | Engagement |
| `clicks_oucollaborate` | Clicks on OUCollaborate activity type | Engagement |
| `clicks_quiz` | Clicks on Quiz activity type | Engagement |
| `clicks_subpage` | Clicks on Subpage activity type | Engagement |
| `clicks_url` | Clicks on URL activity type | Engagement |
| `max_clicks_single_day` | Maximum clicks recorded on any single day | Engagement |
| `mean_clicks_per_active_day` | Mean clicks per active day (`total_clicks / n_days_active`) | Engagement |
| `days_since_last_activity` | Days between the last click and the current checkpoint | Engagement |
| `mean_score_to_date` | Mean assessment score using submissions up to checkpoint | Performance |
| `weighted_score_to_date` | Score weighted by assessment weight, up to checkpoint | Performance |
| `n_assessments_submitted` | Number of assessments submitted up to checkpoint | Performance |
| `not_submitted` | Number of assessments due but not submitted up to checkpoint | Performance |
| `at_risk` | **Target variable** — 1 if student withdrew or failed, 0 otherwise | Target |

---

## 4. Why This Matters for Explainability

SHAP summary plots and LIME tabular explanations render feature names as axis labels or table rows. A name such as `mean_score_to_date` tells an instructor immediately that the model is responding to the student's average score so far, while `weighted_score_to_date` signals that higher-weight assessments are driving the signal. The `_to_date` suffix is particularly important: it proves to a reviewer that the feature is temporally safe (computed only from past data at inference time).

Instructors who receive an early-warning alert will read these names without any ML background. Clear names reduce the cognitive load of interpreting a prediction and increase the likelihood that the system is trusted and acted upon.

---

## 5. Compliance and Enforcement

- Any new feature added to the pipeline must follow this convention before a pull request is merged.
- The CI test suite includes a name-format check (`pytest tests/test_feature_names.py`) that rejects any column not matching the approved patterns.
- Deviations require a written justification and group approval.

---

_Approved by DSP391m Group 1. Last updated: 2026-06-14._
