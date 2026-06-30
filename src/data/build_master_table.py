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
import logging

import pandas as pd

from src.config import INTERIM_DATA_DIR, RAW_DATA_DIR
from src.data import build_engagement_features as eng
from src.data.build_performance_features import aggregate_performance
from src.data.io_utils import (
    GROUP_COLS,
    PRESENTATION_KEY,
    add_at_risk_label,
    load_raw_tables,
    save_parquet_atomic,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

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


def _load_engagement(raw_dir, output_dir, rebuild: bool) -> pd.DataFrame:
    """Load the cached engagement aggregation, or (re)build it from studentVle."""
    cache = output_dir / "engagement_agg.parquet"
    if cache.exists() and not rebuild:
        log.info("Loading cached engagement_agg: %s", cache)
        return pd.read_parquet(cache)
    log.info("Building engagement features from studentVle ...")
    return eng.build(raw_dir, output_dir)


def build_master(
    raw: dict[str, pd.DataFrame],
    engagement: pd.DataFrame,
    rebuild: bool = False,
) -> pd.DataFrame:
    """Left-join the four sources into the master table; attach at_risk + length.

    studentInfo is the roster (left side of every join), so no join may add rows:
    each merge is ``validate="many_to_one"`` and logs its before/after row counts.
    Returns the joined frame *before* the consistency clean (see :func:`_clean`).
    """
    student_info = add_at_risk_label(raw["studentInfo"])
    courses = raw["courses"]

    # Full-course cutoff = module length (t=100%).
    cutoff_lookup = courses[PRESENTATION_KEY + ["module_presentation_length"]].rename(
        columns={"module_presentation_length": "cutoff_day"}
    )

    performance = aggregate_performance(
        raw["studentAssessment"], raw["assessments"], cutoff_lookup, roster=student_info
    )
    registration = raw["studentRegistration"]

    join_log: list[dict] = []

    def _merge(left: pd.DataFrame, right: pd.DataFrame, cols, name: str) -> pd.DataFrame:
        before = len(left)
        merged = left.merge(right, on=cols, how="left", validate="many_to_one")
        join_log.append(
            {
                "step": name,
                "rows_before": before,
                "rows_after": len(merged),
                "n_students": merged["id_student"].nunique(),
                "delta": len(merged) - before,
            }
        )
        log.info("join %-14s rows %d -> %d", name, before, len(merged))
        return merged

    master = student_info.copy()
    join_log.append(
        {
            "step": "studentInfo(base)",
            "rows_before": len(master),
            "rows_after": len(master),
            "n_students": master["id_student"].nunique(),
            "delta": 0,
        }
    )
    master = _merge(
        master,
        registration[
            PRESENTATION_KEY + ["id_student", "date_registration", "date_unregistration"]
        ],
        GROUP_COLS,
        "registration",
    )
    master = _merge(master, engagement, GROUP_COLS, "engagement")
    master = _merge(master, performance, GROUP_COLS, "performance")
    master = _merge(
        master,
        courses[PRESENTATION_KEY + ["module_presentation_length"]],
        PRESENTATION_KEY,
        "courses",
    )

    # Derive days_since_last_activity from last_active_day (helper col), then drop it.
    # A student absent from studentVle has last_active_day == NaN; their idle span is
    # the whole window, so fill with module_presentation_length (NOT 0).
    master["days_since_last_activity"] = (
        master["module_presentation_length"] - master["last_active_day"]
    ).clip(lower=0)
    master["days_since_last_activity"] = master["days_since_last_activity"].fillna(
        master["module_presentation_length"]
    )
    master = master.drop(columns=["last_active_day"])

    # Fill engagement gaps: a student absent from studentVle simply had no activity.
    engagement_fill = [
        c for c in engagement.columns if c not in GROUP_COLS and c != "last_active_day"
    ]
    master[engagement_fill] = master[engagement_fill].fillna(0)

    INTERIM_DATA_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(join_log).to_csv(INTERIM_DATA_DIR / "master_join_log.csv", index=False)
    return master


def _clean(master: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Drop duplicate keys + standardise categorical text; return (clean, log)."""
    rows = []
    n_dup = _dup_count(master)
    master = master.drop_duplicates(subset=GROUP_COLS).reset_index(drop=True)
    rows.append({"item": "duplicate_keys_removed", "value": n_dup})

    for col in CATEGORICAL_COLS:
        if col in master.columns and master[col].dtype == object:
            master[col] = master[col].str.strip()
            rows.append({"item": f"{col}_n_unique", "value": master[col].nunique(dropna=True)})

    return master, pd.DataFrame(rows)


def _dup_count(df: pd.DataFrame) -> int:
    return int(df.duplicated(subset=GROUP_COLS).sum())


def _feature_nans(df: pd.DataFrame) -> int:
    # imd_band and date_unregistration are legitimately missing for some students.
    cols = [c for c in df.columns if c not in ("imd_band", "date_unregistration")]
    return int(df[cols].isnull().sum().sum())


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build the OULAD master table.")
    p.add_argument("--rebuild-engagement", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    raw = load_raw_tables(RAW_DATA_DIR)
    engagement = _load_engagement(RAW_DATA_DIR, INTERIM_DATA_DIR, args.rebuild_engagement)

    master = build_master(raw, engagement)
    master, cleaning_log = _clean(master)

    save_parquet_atomic(master, INTERIM_DATA_DIR / "master_raw.parquet")
    cleaning_log.to_csv(INTERIM_DATA_DIR / "master_cleaning_log.csv", index=False)

    log.info("master_raw: %s rows x %d cols", f"{len(master):,}", master.shape[1])
    log.info("at_risk rate: %.1f%%", 100 * master["at_risk"].mean())
    log.info(
        "duplicated keys: %d | feature NaNs: %d",
        _dup_count(master),
        _feature_nans(master),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
