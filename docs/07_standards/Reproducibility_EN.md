# Reproducibility Guide

**Subtitle:** Everything an External Reader Needs to Recreate the Master Table and All Downstream Artifacts

_DSP391m – Group 1 · Report 2 (Data Tasks), Chapter 3 · Work item STT 31 (An)_

---

## 1. Purpose

Reproducibility is a first-class requirement for scientific data work. This guide documents the exact steps, environment, and data provenance controls that allow any external reader — including future team members and assessors — to recreate every artifact produced by this pipeline, bit-for-bit, starting from the raw OULAD download.

---

## 2. Determinism

A single global random seed is used throughout all scripts, notebooks, and test cases:

```python
RANDOM_SEED = 42
```

Every call to `numpy.random`, `random`, `sklearn` splitters, and any sampling function must consume this constant. It is defined once in `src/config.py` and imported everywhere else; it must never be hard-coded locally.

---

## 3. Data Provenance

### 3.1 Raw-Data Manifest

The file `data/raw/data_manifest.txt` is generated automatically by `setup_raw_data.py` and records the following fields for each of the seven OULAD CSV files:

| Field | Description |
|---|---|
| Filename | Exact file name (e.g., `studentInfo.csv`) |
| MD5 hash | Hex digest of the unmodified downloaded file |
| Size (MB) | File size rounded to two decimal places |
| Download date | ISO-8601 date on which the file was obtained |

The seven files covered are: `courses.csv`, `assessments.csv`, `vle.csv`, `studentInfo.csv`, `studentRegistration.csv`, `studentAssessment.csv`, `studentVle.csv`.

### 3.2 Read-Only Protection

After the manifest is written, `setup_raw_data.py` sets each raw CSV to read-only (`chmod 444` on Linux/macOS; `attrib +R` on Windows). This prevents accidental overwrites.

### 3.3 Integrity Verification

To verify integrity at any later point, re-run `setup_raw_data.py`. The script recomputes the MD5 of each file and compares it against the stored manifest. Any mismatch raises an exception before any downstream step runs.

---

## 4. Environment

- **Python version:** 3.13 (managed via Conda; see the verified set in Section 4.1)
- **Dependency pinning:** `requirements.txt` (pip-installable, exact versions) and `environment.yml` (full Conda environment, including non-Python packages)
- **Note on plotting:** Matplotlib figure generation requires an environment with a working freetype/font stack. On minimal headless servers, install `libfreetype6-dev` (Debian/Ubuntu) or the equivalent before running the EDA step.

To recreate the environment:

```bash
conda env create -f environment.yml
conda activate dsp
```

Or with pip only:

```bash
pip install -r requirements.txt
```

### 4.1 Verified Environment (2026-07-12)

All committed artifacts (model bundles, tables, figures) were built on Windows with the following package set, which `environment.yml` now pins:

| Package | Version | Package | Version |
|---|---|---|---|
| Python | 3.13.9 | matplotlib | 3.10.8 |
| numpy | 2.3.5 | seaborn | 0.13.2 |
| pandas | 2.3.3 | joblib | 1.5.2 |
| scipy | 1.16.3 | shap | 0.52.0 |
| pyarrow | 21.0.0 | lime | 0.2.0.1 |
| scikit-learn | 1.8.0 | loguru | 0.7.3 |
| xgboost | 3.1.3 | imbalanced-learn | 0.14.2 |
| lightgbm | 4.6.0 | | |

(Plus `python-dotenv`, `pytest`, `jupyter`, `nbformat`; `pandoc` 3.8 for docx/deck generation.)

**Bundle compatibility.** The committed `.joblib` bundles are scikit-learn 1.8 / numpy 2.x pickles. Under the older pins (Python 3.11 / scikit-learn 1.5 / numpy < 2), the ANN bundle (`models/ann_t100.joblib`) fails to load (`MT19937 is not a known BitGenerator`), and the remaining bundles load only with an `InconsistentVersionWarning` (results not guaranteed). Always use the pinned environment above.

**Split guard.** `data/splits/test_student_ids.csv` (5,756 students) is the committed source of truth. `python -m src.evaluation.make_split` is guarded: if the id file exists it only loads it and never re-derives the split. Re-deriving (`--rederive`) under a different scikit-learn version changes 4,574/5,756 ids and invalidates every published number — it is reserved for a whole-team decision.

---

## 5. Exact Reproduction Steps

Run all commands from the **project root directory** in the order shown. Each step is idempotent: re-running produces the same output.

```
1. python setup_raw_data.py
```
Verifies the seven raw CSVs against the manifest, writes `data/raw/data_manifest.txt` if missing, and sets files to read-only.

```
2. python -m src.data.time_utils
```
Builds `data/checkpoint_map.csv` and runs a self-check to confirm checkpoint boundaries are temporally correct (no future data leakage at any checkpoint).

```
3. python -m src.data.build_master_table
```
Produces:
- `data/interim/master_raw.parquet` — the master table (32,593 rows × 33 columns)
- `data/interim/master_join_log.csv` — row counts after each left-join step
- `data/interim/master_cleaning_log.csv` — a record of all cleaning decisions

```
4. python -m src.data.make_checkpoints
```
Produces:
- `data/checkpoints/dataset_t10.parquet` through `dataset_t100.parquet` (six files at 10 %, 30 %, 50 %, 70 %, 90 %, 100 % of the module)
- `data/checkpoints/checkpoint_summary.csv`

This step is **resumable**: if interrupted, re-running skips already-written checkpoint files and continues from where it left off.

```
5. python -m src.eda.eda
```
Produces:
- `reports/figures/*.png` — all EDA figures
- `reports/eda_findings.json` — machine-readable summary statistics

Requires a working freetype/font stack (see Section 4).

```
6. pytest tests/test_leakage.py
```
Runs temporal-leakage checks and split-integrity tests. All tests must pass before any modelling work begins.

---

## 6. Reproducibility Guarantees

| Property | Guarantee |
|---|---|
| Notebook execution | All notebooks run top-to-bottom without errors when executed via Restart & Run All |
| Long-running steps | Steps 3 and 4 are checkpointed and resumable; an interrupted run never corrupts output |
| Atomic writes | All Parquet files are written to a temporary path and renamed into place; a kill mid-write leaves the previous file intact |
| Seed usage | `RANDOM_SEED = 42` is consumed by every stochastic operation |

---

## 7. Verified Facts

The following facts were established on the canonical run and must hold after any reproduction:

- `master_raw.parquet` contains **32,593 rows × 33 columns**.
- All left-joins in `build_master_table` preserve exactly **32,593 rows** — no row duplication and no row loss.
- The master table contains **0 duplicate keys** (verified by `pytest tests/test_leakage.py`).
- The at-risk rate in the master table is **52.8 %**.
- The six checkpoint datasets share an identical roster of **32,593 enrolments (28,785 distinct students)** — no enrolment appears in one checkpoint but not another.

---

_DSP391m Group 1. Last updated: 2026-07-12._
