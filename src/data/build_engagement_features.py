"""Aggregate the VLE clickstream (studentVle, ~10.6M rows) into per-student
engagement features.

Output features (group naming convention + data dictionary):
    total_clicks, n_days_active,
    clicks_forumng, clicks_oucontent, clicks_resource, clicks_homepage,
    clicks_oucollaborate, clicks_quiz, clicks_subpage, clicks_url,
    max_clicks_single_day, mean_clicks_per_active_day,
    last_active_day  (helper; days_since_last_activity derived downstream).

`aggregate_engagement` MUST be pure: clickstream DataFrame in -> features out, so
the checkpoint builder can reuse it on time-sliced clickstreams unchanged.

CLI: python -m src.data.build_engagement_features [--verbose]

See guide section "data/build_engagement_features.py".
"""

from __future__ import annotations

import argparse

import pandas as pd

from src.config import INTERIM_DATA_DIR, RAW_DATA_DIR


def load_student_vle(raw_dir=RAW_DATA_DIR, chunksize: int = 500_000) -> pd.DataFrame:
    """Load studentVle.csv (big — read in chunks, downcast dtypes).

    TODO: read studentVle.csv, keep code_module, code_presentation, id_student,
    id_site, date, sum_click with compact dtypes (int32/string). Concatenate
    chunks. Return the frame.
    """
    raise NotImplementedError


def attach_activity_type(clickstream: pd.DataFrame, vle: pd.DataFrame) -> pd.DataFrame:
    """Join the vle table to label each id_site with its activity_type.

    TODO: merge clickstream with vle[code_module, code_presentation, id_site,
    activity_type]. Map any activity_type not in CANONICAL_ACTIVITY_TYPES to a
    bucket you choose (or leave for total_clicks only). Return enriched frame.
    """
    raise NotImplementedError


def aggregate_engagement(clickstream: pd.DataFrame) -> pd.DataFrame:
    """Collapse the (already type-attached) clickstream to one row per student.

    TODO (group by GROUP_COLS):
      - total_clicks         = sum(sum_click)
      - n_days_active        = nunique(date)
      - clicks_<type>        = sum(sum_click) per canonical activity_type (pivot)
      - max_clicks_single_day= max over day of daily click sums
      - mean_clicks_per_active_day = total_clicks / n_days_active
      - last_active_day      = max(date)
    Return a flat frame indexed by GROUP_COLS (reset_index).
    """
    raise NotImplementedError


def build(raw_dir=RAW_DATA_DIR, output_dir=INTERIM_DATA_DIR) -> pd.DataFrame:
    """End-to-end: load -> attach type -> aggregate -> save engagement_agg.parquet.

    TODO: orchestrate the three functions above + save_parquet_atomic.
    """
    raise NotImplementedError


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """TODO: --verbose flag; return parsed args."""
    raise NotImplementedError


def main(argv: list[str] | None = None) -> int:
    """TODO: parse args, configure logging, call build(); return 0."""
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
