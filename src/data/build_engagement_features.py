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
import logging

import pandas as pd

from src.config import INTERIM_DATA_DIR, RAW_DATA_DIR
from src.data.io_utils import CANONICAL_ACTIVITY_TYPES, GROUP_COLS, save_parquet_atomic

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# Compact dtypes keep the ~10.6M-row table within a tight memory budget.
_STUDENT_VLE_DTYPES = {
    "code_module": "string",
    "code_presentation": "string",
    "id_student": "int32",
    "id_site": "int32",
    "date": "int32",
    "sum_click": "int32",
}


def load_student_vle(raw_dir=RAW_DATA_DIR, chunksize: int = 500_000) -> pd.DataFrame:
    """Read studentVle.csv in chunks with compact dtypes.

    The file is large, so it is streamed in chunks and concatenated once. Any
    categorical conversion is left to downstream callers; building a category
    hash table during the C parse can spike memory on a file this size.
    """
    path = raw_dir / "studentVle.csv"
    if not path.exists():
        raise FileNotFoundError(path)
    log.info("Reading %s (chunksize=%d)", path.name, chunksize)
    frames = [c for c in pd.read_csv(path, dtype=_STUDENT_VLE_DTYPES, chunksize=chunksize)]
    df = pd.concat(frames, ignore_index=True)
    log.info(
        "studentVle: %s rows, %.0f MB",
        f"{len(df):,}",
        df.memory_usage(deep=True).sum() / 1e6,
    )
    return df


def attach_activity_type(clickstream: pd.DataFrame, vle: pd.DataFrame) -> pd.DataFrame:
    """Label each click's id_site with its activity_type via a lookup Series.

    id_site is globally unique in vle.csv, so a map-by-site avoids a 10M-row merge
    and stays unambiguous. Clicks whose id_site is absent from vle.csv get a NaN
    activity_type (they still count toward total_clicks).
    """
    if vle["id_site"].duplicated().any():
        raise ValueError("id_site is not unique in vle.csv; lookup-by-site is unsafe")
    site_to_activity = vle.set_index("id_site")["activity_type"]
    out = clickstream.copy()
    out["activity_type"] = out["id_site"].map(site_to_activity)
    n_missing = int(out["activity_type"].isna().sum())
    if n_missing:
        log.warning(
            "%s clicks had no activity_type (id_site absent in vle.csv)",
            f"{n_missing:,}",
        )
    return out


def aggregate_engagement(clickstream: pd.DataFrame) -> pd.DataFrame:
    """Aggregate a (full or cut) clickstream into per-student engagement features.

    ``clickstream`` must contain GROUP_COLS plus ``date``, ``sum_click`` and
    ``activity_type``. Returns one flat row per student-module-presentation.
    """
    required = set(GROUP_COLS) | {"date", "sum_click", "activity_type"}
    missing = required - set(clickstream.columns)
    if missing:
        raise KeyError(f"clickstream missing columns: {sorted(missing)}")

    grouped = clickstream.groupby(GROUP_COLS, observed=True)
    base = grouped.agg(
        total_clicks=("sum_click", "sum"),
        n_days_active=("date", "nunique"),
        last_active_day=("date", "max"),
    )

    # Clicks per day, then the busiest single day per student.
    daily = clickstream.groupby(GROUP_COLS + ["date"], observed=True)["sum_click"].sum()
    base["max_clicks_single_day"] = daily.groupby(level=GROUP_COLS, observed=True).max()

    # Per-type click counts, restricted to the eight canonical activity types.
    by_type = (
        clickstream.groupby(GROUP_COLS + ["activity_type"], observed=True)["sum_click"]
        .sum()
        .unstack(fill_value=0)
    )
    by_type = by_type.reindex(columns=list(CANONICAL_ACTIVITY_TYPES), fill_value=0)
    by_type.columns = [f"clicks_{c}" for c in by_type.columns]
    base = base.join(by_type)

    base["mean_clicks_per_active_day"] = (
        base["total_clicks"] / base["n_days_active"].where(base["n_days_active"] > 0)
    ).fillna(0.0)

    return base.reset_index()


def build(raw_dir=RAW_DATA_DIR, output_dir=INTERIM_DATA_DIR) -> pd.DataFrame:
    """Full pipeline for t=100%: load -> attach type -> aggregate -> verify -> save."""
    student_vle = load_student_vle(raw_dir)
    vle_meta = pd.read_csv(raw_dir / "vle.csv")
    clickstream = attach_activity_type(student_vle, vle_meta)

    engagement = aggregate_engagement(clickstream)

    n_students = len(student_vle[GROUP_COLS].drop_duplicates())
    if n_students != len(engagement):
        log.error("Student count mismatch: raw=%d aggregated=%d", n_students, len(engagement))
    else:
        log.info("Verified: %s students preserved through aggregation", f"{n_students:,}")

    out = save_parquet_atomic(engagement, output_dir / "engagement_agg.parquet")
    log.info("Wrote %s (%s rows, %d cols)", out, f"{len(engagement):,}", engagement.shape[1])
    return engagement


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Aggregate OULAD VLE clickstream into engagement features."
    )
    p.add_argument("--verbose", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.verbose:
        log.setLevel(logging.DEBUG)
    try:
        build()
    except FileNotFoundError as e:
        log.error("Missing input file: %s", e)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
