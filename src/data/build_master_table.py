"""Build the OULAD master table (t=100%, full-course view).

Joins the OULAD tables into one flat table — one row per student-module-
presentation — carrying demographic + engagement + performance features, the
fixed ``at_risk`` label (Step-0 Option A) and the module length used for
checkpoint slicing.

  Join:  studentInfo <- registration <- engagement <- performance
         (left joins; log before/after row counts to prove no dup/loss).
  Clean: drop duplicate keys, standardise categorical text (log the cleaning).

CLI:
    python -m src.data.build_master_table              # uses cached engagement_agg
    python -m src.data.build_master_table --rebuild-engagement

See guide section "data/build_master_table.py".
"""

from __future__ import annotations

import argparse

import pandas as pd

# Categorical columns standardised in the consistency pass. Leave imd_band values
# (e.g. '10-20') verbatim — the ordinal encoder expects them.
CATEGORICAL_COLS = [
    "gender",
    "region",
    "highest_education",
    "imd_band",
    "age_band",
    "disability",
]


def build_master(
    raw: dict[str, pd.DataFrame],
    engagement: pd.DataFrame,
    rebuild: bool = False,
) -> pd.DataFrame:
    """Left-join the four sources into the master table; attach at_risk + length.

    TODO:
      1. Start from studentInfo (the roster) + add_at_risk_label.
      2. Merge studentRegistration (date_registration, date_unregistration).
      3. Merge engagement features (GROUP_COLS).
      4. Build cutoff_lookup = courses[PRESENTATION_KEY, module_presentation_length]
         renamed cutoff_day, then aggregate_performance(..., cutoff=length).
      5. Merge performance features (GROUP_COLS).
      6. Attach module_presentation_length (needed for checkpoints).
      7. Log row counts before/after each merge (assert no unexpected growth).
      8. Return the joined frame (uncleaned).
    """
    raise NotImplementedError


def _clean(master: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Drop duplicate keys + standardise categoricals; return (clean, log).

    TODO: strip/lower-case-normalise CATEGORICAL_COLS consistently, drop_duplicates
    on GROUP_COLS, and return a small cleaning-log DataFrame for the report.
    """
    raise NotImplementedError


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """TODO: --rebuild-engagement flag."""
    raise NotImplementedError


def main(argv: list[str] | None = None) -> int:
    """TODO: load raw, build/load engagement, build_master, _clean, save
    master_raw.parquet to INTERIM_DATA_DIR; return 0."""
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
