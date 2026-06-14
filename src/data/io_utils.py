"""Shared I/O helpers: project paths, the at-risk label, atomic parquet writes.

Centralising these keeps every pipeline stage (engagement, performance, master
table, checkpoints) consistent with the Step-0 agreement (BB-B0-N1) and with the
data dictionary. The at-risk mapping lives here so it can never drift between
modules.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

# --- Project layout (resolved from this file, independent of the cwd) ---------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
INTERIM_DIR = PROJECT_ROOT / "data" / "interim"
CHECKPOINTS_DIR = PROJECT_ROOT / "data" / "checkpoints"
CHECKPOINT_MAP_PATH = PROJECT_ROOT / "data" / "checkpoint_map.csv"

# --- Composite key shared by every per-student table --------------------------
GROUP_COLS = ["code_module", "code_presentation", "id_student"]
PRESENTATION_KEY = ["code_module", "code_presentation"]

# --- Target definition (Step-0 agreement, Option A) ---------------------------
# at-risk (1) = {Fail, Withdrawn}; not-at-risk (0) = {Pass, Distinction}.
# The label is derived from final_result and is fixed across all checkpoints.
AT_RISK_RESULTS = ("Fail", "Withdrawn")

# Eight canonical VLE activity types kept as engagement features. total_clicks
# still sums clicks over *all* activity types; these eight are the per-type
# breakdown referenced by preprocessing.py and the data dictionary.
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
    """Append the binary ``at_risk`` column derived from ``final_result``."""
    out = student_info.copy()
    out["at_risk"] = out["final_result"].isin(AT_RISK_RESULTS).astype("int8")
    return out


def save_parquet_atomic(df: pd.DataFrame, path: Path) -> Path:
    """Write a DataFrame to parquet via a temp file + atomic rename.

    A crash mid-write therefore never leaves a half-written, unreadable parquet
    in place of a good one (global checkpointing rule).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    df.to_parquet(tmp, index=False)
    os.replace(tmp, path)
    return path


def load_raw_tables(raw_dir: Path = RAW_DIR) -> dict[str, pd.DataFrame]:
    """Load the small OULAD tables (everything except the 432 MB studentVle).

    studentVle is read separately by the engagement builder, which streams it in
    chunks to bound peak memory.
    """
    names = [
        "studentInfo",
        "studentRegistration",
        "studentAssessment",
        "assessments",
        "courses",
        "vle",
    ]
    return {name: pd.read_csv(raw_dir / f"{name}.csv") for name in names}
