"""Aggregate the VLE clickstream (studentVle) into per-student engagement features.

Task 3 (Phuc). The heavy table studentVle (~10.6M rows) is collapsed to one row
per (code_module, code_presentation, id_student) with the engagement features
named per the group convention (Task 40) and the data dictionary:

    total_clicks, n_days_active,
    clicks_forumng, clicks_oucontent, clicks_resource, clicks_homepage,
    clicks_oucollaborate, clicks_quiz, clicks_subpage, clicks_url,
    max_clicks_single_day, mean_clicks_per_active_day,
    last_active_day            (helper; days_since_last_activity is derived
                                downstream once the reference/cutoff day is known)

`aggregate_engagement` is deliberately pure: it takes a clickstream DataFrame
(full or already cut at a checkpoint) and returns the aggregated features. The
checkpoint builder reuses it on time-sliced clickstreams, so the exact same
aggregation logic runs at every checkpoint.

CLI
    python -m src.data.build_engagement_features            # writes parquet
    python -m src.data.build_engagement_features --verbose
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.data.io_utils import (  # noqa: E402
    CANONICAL_ACTIVITY_TYPES,
    GROUP_COLS,
    INTERIM_DIR,
    RAW_DIR,
    save_parquet_atomic,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

_STUDENT_VLE_DTYPES = {
    "code_module": "string",
    "code_presentation": "string",
    "id_student": "int32",
    "id_site": "int32",
    "date": "int32",
    "sum_click": "int32",
}


def load_student_vle(raw_dir: Path = RAW_DIR, chunksize: int = 500_000) -> pd.DataFrame:
    """Read studentVle.csv in chunks with simple dtypes.

    Categorical conversion is done *after* the full frame is in memory; building a
    category hash table during the C parse can spike memory on large files.
    """
    path = raw_dir / "studentVle.csv"
    if not path.exists():
        raise FileNotFoundError(path)
    log.info("Reading %s (chunksize=%d)", path.name, chunksize)
    frames = [
        c for c in pd.read_csv(path, dtype=_STUDENT_VLE_DTYPES, chunksize=chunksize)
    ]
    df = pd.concat(frames, ignore_index=True)
    log.info(
        "studentVle: %s rows, %.0f MB",
        f"{len(df):,}",
        df.memory_usage(deep=True).sum() / 1e6,
    )
    return df


def attach_activity_type(
    student_vle: pd.DataFrame, vle_meta: pd.DataFrame
) -> pd.DataFrame:
    """Map id_site -> activity_type via a lookup Series (avoids a 10M-row merge).

    id_site is globally unique in vle.csv, so the lookup is unambiguous.
    """
    if vle_meta["id_site"].duplicated().any():
        raise ValueError("id_site is not unique in vle.csv; lookup-by-site is unsafe")
    site_to_activity = vle_meta.set_index("id_site")["activity_type"]
    out = student_vle.copy()
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
    ``activity_type``. Returns one row per student-module-presentation.
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


def build(raw_dir: Path = RAW_DIR, output_dir: Path = INTERIM_DIR) -> pd.DataFrame:
    """Full pipeline for t=100%: load -> attach type -> aggregate -> verify -> save."""
    student_vle = load_student_vle(raw_dir)
    vle_meta = pd.read_csv(raw_dir / "vle.csv")
    clickstream = attach_activity_type(student_vle, vle_meta)

    engagement = aggregate_engagement(clickstream)

    n_students = len(student_vle[GROUP_COLS].drop_duplicates())
    if n_students != len(engagement):
        log.error(
            "Student count mismatch: raw=%d aggregated=%d", n_students, len(engagement)
        )
    else:
        log.info(
            "Verified: %s students preserved through aggregation", f"{n_students:,}"
        )

    out = save_parquet_atomic(engagement, output_dir / "engagement_agg.parquet")
    log.info(
        "Wrote %s (%s rows, %d cols)", out, f"{len(engagement):,}", engagement.shape[1]
    )
    return engagement


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Aggregate OULAD VLE clickstream into engagement features."
    )
    p.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    p.add_argument("--output-dir", type=Path, default=INTERIM_DIR)
    p.add_argument("--verbose", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.verbose:
        log.setLevel(logging.DEBUG)
    try:
        build(args.raw_dir, args.output_dir)
    except FileNotFoundError as e:
        log.error("Missing input file: %s", e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
