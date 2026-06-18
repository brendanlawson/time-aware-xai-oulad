"""Generate the six time-aware checkpoint datasets.

For each t in {10,20,40,60,80,100}% the clickstream and submissions are cut at
the checkpoint day (anti-leakage rules #1 and #2), re-aggregated, and joined onto
the FIXED student roster. The roster never changes (Step-0 Option A); only the
time-sliced engagement/performance features differ.

Long-running by design (the 10.6M-row clickstream is re-aggregated six times), so
it MUST checkpoint + resume:
  - write each dataset_t{t}.parquet atomically;
  - on restart, skip a t whose parquet already exists;
  - log which checkpoints are skipped (resumed) vs newly built.

CLI:
    python -m src.data.make_checkpoints           # resume; build missing only
    python -m src.data.make_checkpoints --force   # rebuild all

See guide section "data/make_checkpoints.py".
"""

from __future__ import annotations

import argparse

import pandas as pd

from src.config import CHECKPOINTS, CHECKPOINTS_DIR

DEMOGRAPHIC_COLS = [
    "gender",
    "region",
    "highest_education",
    "imd_band",
    "age_band",
    "disability",
    "num_of_prev_attempts",
    "studied_credits",
    "date_registration",
]


def _assemble_checkpoint(
    t_percent: int,
    roster: pd.DataFrame,
    clickstream: pd.DataFrame,
    submissions: pd.DataFrame,
    assessments: pd.DataFrame,
    checkpoint_map: pd.DataFrame,
) -> pd.DataFrame:
    """Build ONE checkpoint dataset for the given t%.

    TODO:
      1. cut_at_checkpoint(clickstream, t, map) then aggregate_engagement.
      2. cutoff_lookup = checkpoint_map[t] (PRESENTATION_KEY -> cutoff_day);
         aggregate_performance(submissions, assessments, cutoff_lookup, roster).
      3. days_since_last_activity = cutoff_day - last_active_day (per presentation).
      4. Left-join demographic roster + engagement + performance; fill missing
         engagement/performance with 0 (meaningful thanks to not_submitted).
      5. add_at_risk_label; add a t_percent column. Return the frame.
    """
    raise NotImplementedError


def make_checkpoints(
    checkpoints=CHECKPOINTS, force: bool = False, out_dir=CHECKPOINTS_DIR
) -> None:
    """Loop over checkpoints with resume support.

    TODO:
      1. Load raw tables + roster (master roster / studentInfo) once.
      2. Build checkpoint_map from courses.
      3. Load + type-attach the clickstream once (reuse across t).
      4. For each t: out = out_dir / f"dataset_t{t}.parquet".
         - if out exists and not force: log "skip (resumed)" and continue.
         - else _assemble_checkpoint(...) and save_parquet_atomic(out).
      5. Log newly built vs skipped counts.
    """
    raise NotImplementedError


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """TODO: --force flag."""
    raise NotImplementedError


def main(argv: list[str] | None = None) -> int:
    """TODO: parse args, call make_checkpoints(force=...); return 0."""
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
