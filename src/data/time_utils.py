"""Time-aware utilities — the heart of the "time-aware" framing.

build_checkpoint_map: convert progress percentages (10/20/40/60/80/100%) into
    concrete day thresholds per module-presentation (course lengths differ).
cut_at_checkpoint: keep only records on/before the checkpoint day — simulates the
    information available at prediction time (anti-leakage rule #2).

See guide section "data/time_utils.py".
"""

from __future__ import annotations

import pandas as pd

from src.config import CHECKPOINT_MAP_PATH, CHECKPOINTS


def build_checkpoint_map(courses: pd.DataFrame, checkpoints=CHECKPOINTS) -> pd.DataFrame:
    """Lookup table: (code_module, code_presentation, t_percent) -> cutoff_day.

    cutoff_day = round(module_presentation_length * t / 100). Long format: one
    row per module-presentation per checkpoint.

    TODO:
      1. For each course row and each t in checkpoints, emit a dict with
         PRESENTATION_KEY, t_percent, module_presentation_length, cutoff_day.
      2. Return pd.DataFrame(rows).
    """
    raise NotImplementedError


def load_checkpoint_map(path=CHECKPOINT_MAP_PATH) -> pd.DataFrame:
    """Read the checkpoint map CSV. TODO: pd.read_csv(path)."""
    raise NotImplementedError


def cut_at_checkpoint(
    df: pd.DataFrame,
    t_percent: int,
    checkpoint_map: pd.DataFrame,
    date_col: str = "date",
) -> pd.DataFrame:
    """Keep only rows whose ``date_col`` <= the cutoff_day for that presentation.

    TODO:
      1. From checkpoint_map, select rows where t_percent == t_percent to get the
         per-presentation cutoff_day.
      2. Merge that cutoff onto df by PRESENTATION_KEY.
      3. Return rows where df[date_col] <= cutoff_day (drop the helper column).
    Note: rows with NaN date are an edge case — decide and document your rule.
    """
    raise NotImplementedError
