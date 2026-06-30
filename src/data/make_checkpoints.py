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
import logging

import pandas as pd

from src.config import CHECKPOINTS, CHECKPOINTS_DIR, INTERIM_DATA_DIR, RAW_DATA_DIR
from src.data.build_engagement_features import (
    aggregate_engagement,
    attach_activity_type,
    load_student_vle,
)
from src.data.build_performance_features import aggregate_performance
from src.data.io_utils import (
    GROUP_COLS,
    PRESENTATION_KEY,
    add_at_risk_label,
    load_raw_tables,
    save_parquet_atomic,
)
from src.data.time_utils import build_checkpoint_map, cut_at_checkpoint

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# Demographic + registration columns carried verbatim from the fixed roster (they
# do not change with t). date_registration is a registration field merged into the
# roster once, upstream of the per-checkpoint loop.
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

    Cuts the clickstream/submissions at the checkpoint day, re-aggregates the
    engagement + performance features, and joins them onto the fixed roster.
    """
    cutoff_t = checkpoint_map.loc[
        checkpoint_map["t_percent"] == t_percent, PRESENTATION_KEY + ["cutoff_day"]
    ]

    # 1. Engagement on the time-sliced clickstream.
    vle_t = cut_at_checkpoint(clickstream, t_percent, checkpoint_map, date_col="date")
    engagement = aggregate_engagement(vle_t)
    engagement = engagement.merge(cutoff_t, on=PRESENTATION_KEY, how="left")
    engagement["days_since_last_activity"] = (
        engagement["cutoff_day"] - engagement["last_active_day"]
    ).clip(lower=0)
    engagement = engagement.drop(columns=["last_active_day", "cutoff_day"])

    # 2. Performance as of the same cutoff day.
    performance = aggregate_performance(submissions, assessments, cutoff_t, roster=roster)

    # 3. Assemble onto the fixed roster (demographics never change with t).
    master_t = roster[GROUP_COLS + DEMOGRAPHIC_COLS + ["final_result"]].copy()
    master_t = master_t.merge(engagement, on=GROUP_COLS, how="left", validate="many_to_one")
    master_t = master_t.merge(performance, on=GROUP_COLS, how="left", validate="many_to_one")

    # 4. Fill engagement gaps with 0 for students absent from studentVle -- EXCEPT
    # days_since_last_activity, whose "no activity" value is NOT 0 (that would read as
    # "just active"). A student with zero activity has been idle for the whole observed
    # window, so fill it with the checkpoint's cutoff_day. At t=100 cutoff_day equals
    # module_presentation_length, so this reproduces master_raw exactly.
    engagement_fill = [
        c for c in engagement.columns if c not in GROUP_COLS and c != "days_since_last_activity"
    ]
    master_t[engagement_fill] = master_t[engagement_fill].fillna(0)
    master_t = master_t.merge(cutoff_t, on=PRESENTATION_KEY, how="left")
    master_t["days_since_last_activity"] = master_t["days_since_last_activity"].fillna(
        master_t["cutoff_day"]
    )
    master_t = master_t.drop(columns=["cutoff_day"])

    # 5. Fixed label + checkpoint marker.
    master_t = add_at_risk_label(master_t)
    master_t.insert(0, "t_percent", t_percent)
    return master_t


def make_checkpoints(
    checkpoints=CHECKPOINTS, force: bool = False, out_dir=CHECKPOINTS_DIR
) -> None:
    """Build the six checkpoint datasets with resume support.

    An existing ``dataset_t{t}.parquet`` is skipped on restart (unless ``force``),
    so an interrupted run continues rather than restarting; every write is atomic.
    """
    raw = load_raw_tables(RAW_DATA_DIR)
    checkpoint_map = build_checkpoint_map(raw["courses"])

    # Fixed roster: studentInfo + the registration date used as a demographic feature.
    # Built once; identical across every checkpoint (Step-0 Option A).
    roster = raw["studentInfo"].merge(
        raw["studentRegistration"][PRESENTATION_KEY + ["id_student", "date_registration"]],
        on=GROUP_COLS,
        how="left",
        validate="many_to_one",
    )

    todo = [t for t in checkpoints if force or not (out_dir / f"dataset_t{t}.parquet").exists()]
    skip = [t for t in checkpoints if t not in todo]
    if skip:
        log.info("Resume: skipping existing checkpoints %s", skip)
    log.info("Building checkpoints %s", todo)

    # The 10.6M-row clickstream is only loaded when there is work to do.
    clickstream = None
    if todo:
        clickstream = attach_activity_type(load_student_vle(RAW_DATA_DIR), raw["vle"])

    roster_ids = set(map(tuple, roster[GROUP_COLS].itertuples(index=False)))
    stats = []
    for t in checkpoints:
        path = out_dir / f"dataset_t{t}.parquet"
        if t in todo:
            df = _assemble_checkpoint(
                t,
                roster,
                clickstream,
                raw["studentAssessment"],
                raw["assessments"],
                checkpoint_map,
            )
            save_parquet_atomic(df, path)
            log.info("newly built %s (%s rows x %d cols)", path.name, f"{len(df):,}", df.shape[1])
        else:
            df = pd.read_parquet(path)
            log.info("skip (resumed) %s", path.name)
        # The roster must be identical at every checkpoint.
        assert (
            set(map(tuple, df[GROUP_COLS].itertuples(index=False))) == roster_ids
        ), f"checkpoint t={t} roster differs from the fixed student set"
        stats.append(
            {
                "t_percent": t,
                "n_records": len(df),
                "n_columns": df.shape[1],
                "at_risk_rate": round(df["at_risk"].mean(), 4),
            }
        )

    summary = pd.DataFrame(stats)
    INTERIM_DATA_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(INTERIM_DATA_DIR / "checkpoint_summary.csv", index=False)
    log.info("Checkpoint summary:\n%s", summary.to_string(index=False))
    log.info(
        "All %d checkpoints share an identical %d-student roster.",
        len(checkpoints),
        len(roster_ids),
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate six time-aware checkpoint datasets.")
    p.add_argument("--force", action="store_true", help="rebuild all checkpoints")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    make_checkpoints(force=args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
