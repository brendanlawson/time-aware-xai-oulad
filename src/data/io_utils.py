"""Shared I/O helpers: the at-risk label, atomic parquet writes, raw-table loading.

Centralising these keeps every pipeline stage (engagement, performance, master
table, checkpoints) consistent. The at-risk mapping lives here so it can never
drift between modules.

Constants below are GIVEN (project facts). The three functions implement the
contract described in guide section "data/io_utils.py".
"""

from __future__ import annotations

import os
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

    at-risk (1) = ``final_result`` in :data:`AT_RISK_RESULTS`; else 0 (dtype
    int8). The caller's frame is never mutated.
    """
    out = student_info.copy()
    out["at_risk"] = out["final_result"].isin(AT_RISK_RESULTS).astype("int8")
    return out


def save_parquet_atomic(df: pd.DataFrame, path: Path) -> Path:
    """Write ``df`` to parquet via a temp file + atomic rename (kill-safe).

    A crash mid-write therefore never leaves a half-written, unreadable parquet in
    place of a good one (the project's checkpointing rule).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    df.to_parquet(tmp, index=False)
    os.replace(tmp, path)  # atomic on the same filesystem
    return path


def load_raw_tables(raw_dir: Path = RAW_DATA_DIR) -> dict[str, pd.DataFrame]:
    """Load the small OULAD tables into a dict keyed by table name.

    Everything except the 432 MB ``studentVle`` is read eagerly; the engagement
    builder streams ``studentVle`` in chunks separately to bound peak memory, so
    loading it here would only waste RAM.
    """
    names = [
        "studentInfo",
        "studentRegistration",
        "studentAssessment",
        "assessments",
        "courses",
        "vle",
    ]
    return {name: pd.read_csv(Path(raw_dir) / f"{name}.csv") for name in names}
