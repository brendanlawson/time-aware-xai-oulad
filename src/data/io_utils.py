"""Shared I/O helpers: the at-risk label, atomic parquet writes, raw-table loading.

Centralising these keeps every pipeline stage (engagement, performance, master
table, checkpoints) consistent. The at-risk mapping lives here so it can never
drift between modules.

Constants below are GIVEN (project facts). The three functions are yours to
implement — see guide section "data/io_utils.py".
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import RAW_DATA_DIR  # re-used by callers as the default raw dir

# Short alias used across the data layer and tests.
RAW_DIR = RAW_DATA_DIR

# --- Composite keys shared by every per-student table -------------------------
GROUP_COLS = ["code_module", "code_presentation", "id_student"]
PRESENTATION_KEY = ["code_module", "code_presentation"]

# --- Target definition (Step-0 agreement, Option A) ---------------------------
# at-risk (1) = {Fail, Withdrawn}; not-at-risk (0) = {Pass, Distinction}.
# Derived from final_result and fixed across all checkpoints.
AT_RISK_RESULTS = ("Fail", "Withdrawn")

# --- Eight canonical VLE activity types kept as per-type engagement features ---
CANONICAL_ACTIVITY_TYPES = (
    "forumng",
    "oucontent",
    "resource",
    "homepage",
    "oucollaborate",
    "quiz",
    "subpage",
    "url",
)


def add_at_risk_label(student_info: pd.DataFrame) -> pd.DataFrame:
    """Append the binary ``at_risk`` column derived from ``final_result``.

    TODO:
      1. Copy the frame (do not mutate the caller's).
      2. at_risk = final_result is in AT_RISK_RESULTS -> 1 else 0 (dtype int8).
      3. Return the copy.
    """
    raise NotImplementedError


def save_parquet_atomic(df: pd.DataFrame, path: Path) -> Path:
    """Write ``df`` to parquet via a temp file + atomic rename (kill-safe).

    TODO:
      1. Ensure path.parent exists (mkdir parents=True, exist_ok=True).
      2. Write to a sibling temp path (e.g. path.with_suffix(".parquet.tmp")).
      3. os.replace(tmp, path)  # atomic on the same filesystem.
      4. Return path.
    Why: a crash mid-write must never leave a half-written parquet behind.
    """
    raise NotImplementedError


def load_raw_tables(raw_dir: Path = RAW_DATA_DIR) -> dict[str, pd.DataFrame]:
    """Load the OULAD CSVs into a dict keyed by table name.

    Tables: studentInfo, studentRegistration, studentVle, studentAssessment,
    assessments, vle, courses.

    TODO:
      1. Map name -> filename.csv under raw_dir.
      2. pd.read_csv each (consider dtype hints for big tables later).
      3. Return {name: DataFrame}.
    """
    raise NotImplementedError
