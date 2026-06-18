"""Generate the six time-aware checkpoint datasets (Task 13, Khoa).

For each t in {10,20,40,60,80,100}% the clickstream and submissions are cut at the
checkpoint day (leakage rules #1 and #2), re-aggregated, and joined onto the fixed
student roster. The roster never changes, so the student list is identical across
all checkpoints (Step-0 Option A); only the time-sliced engagement/performance
features differ.

Long-running by design (the 10.6M-row clickstream is re-aggregated six times), so
each checkpoint is written atomically and the run resumes: an existing
dataset_t{t}.parquet is skipped on restart.

CLI
    python -m src.data.make_checkpoints           # resume; build missing checkpoints
    python -m src.data.make_checkpoints --force   # rebuild all
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.data.build_engagement_features import (
    aggregate_engagement,
    attach_activity_type,
    load_student_vle,
)  # noqa: E402
from src.data.build_performance_features import aggregate_performance  # noqa: E402
from src.data.io_utils import (  # noqa: E402
    CHECKPOINTS_DIR,
    GROUP_COLS,
    INTERIM_DIR,
    PRESENTATION_KEY,
    RAW_DIR,
    add_at_risk_label,
    load_raw_tables,
    save_parquet_atomic,
)
from src.data.time_utils import CHECKPOINTS, build_checkpoint_map, cut_at_checkpoint  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

DEMOGRAPHIC_COLS = [
    "gender",
    "region",
    "highest_education",
    "imd_band",
    "age_band",
    "num_of_prev_attempts",
    "studied_credits",
    "disability",
]


def _assemble_checkpoint(
    t: int,
    clickstream: pd.DataFrame,
    raw: dict[str, pd.DataFrame],
    student_info: pd.DataFrame,
    checkpoint_map: pd.DataFrame,
) -> pd.DataFrame:
    cutoff_t = checkpoint_map.loc[
        checkpoint_map["t_percent"] == t, PRESENTATION_KEY + ["cutoff_day"]
    ]

    vle_t = cut_at_checkpoint(clickstream, t, checkpoint_map, date_col="date")
    engagement = aggregate_engagement(vle_t)
    engagement = engagement.merge(cutoff_t, on=PRESENTATION_KEY, how="left")
    engagement["days_since_last_activity"] = (
        engagement["cutoff_day"] - engagement["last_active_day"]
    ).clip(lower=0)
    engagement = engagement.drop(columns=["last_active_day", "cutoff_day"])

    performance = aggregate_performance(
        raw["studentAssessment"], raw["assessments"], cutoff_t, roster=student_info
    )

    base_cols = GROUP_COLS + DEMOGRAPHIC_COLS + ["final_result", "at_risk"]
    master_t = student_info[base_cols].copy()
    master_t = master_t.merge(
        raw["studentRegistration"][
            PRESENTATION_KEY + ["id_student", "date_registration"]
        ],
        on=GROUP_COLS,
        how="left",
        validate="many_to_one",
    )
    master_t = master_t.merge(
        engagement, on=GROUP_COLS, how="left", validate="many_to_one"
    )
    master_t = master_t.merge(
        performance, on=GROUP_COLS, how="left", validate="many_to_one"
    )
    master_t = master_t.merge(
        raw["courses"][PRESENTATION_KEY + ["module_presentation_length"]],
        on=PRESENTATION_KEY,
        how="left",
        validate="many_to_one",
    )

    # Fill engagement gaps with 0 for students absent from studentVle -- EXCEPT
    # days_since_last_activity, whose "no activity" value is NOT 0 (that would read as
    # "just active"). A student with zero activity has been idle for the whole observed
    # window, so fill it with the checkpoint's cutoff_day. At t=100 cutoff_day equals
    # module_presentation_length, so this reproduces master_raw exactly.
    engagement_fill = [
        c
        for c in engagement.columns
        if c not in GROUP_COLS and c != "days_since_last_activity"
    ]
    master_t[engagement_fill] = master_t[engagement_fill].fillna(0)
    master_t = master_t.merge(cutoff_t, on=PRESENTATION_KEY, how="left")
    master_t["days_since_last_activity"] = master_t["days_since_last_activity"].fillna(
        master_t["cutoff_day"]
    )
    master_t = master_t.drop(columns=["cutoff_day"])
    master_t.insert(0, "t_percent", t)
    return master_t


def make_checkpoints(
    raw_dir: Path = RAW_DIR,
    out_dir: Path = CHECKPOINTS_DIR,
    interim_dir: Path = INTERIM_DIR,
    force: bool = False,
) -> pd.DataFrame:
    raw = load_raw_tables(raw_dir)
    student_info = add_at_risk_label(raw["studentInfo"])
    checkpoint_map = build_checkpoint_map(raw["courses"])

    todo = [
        t
        for t in CHECKPOINTS
        if force or not (out_dir / f"dataset_t{t}.parquet").exists()
    ]
    skip = [t for t in CHECKPOINTS if t not in todo]
    if skip:
        log.info("Resume: skipping existing checkpoints %s", skip)
    log.info("Building checkpoints %s", todo)

    clickstream = None
    if todo:
        clickstream = attach_activity_type(load_student_vle(raw_dir), raw["vle"])

    roster_ids = set(map(tuple, student_info[GROUP_COLS].itertuples(index=False)))
    stats = []
    for t in CHECKPOINTS:
        path = out_dir / f"dataset_t{t}.parquet"
        if t in todo:
            df = _assemble_checkpoint(t, clickstream, raw, student_info, checkpoint_map)
            save_parquet_atomic(df, path)
            log.info(
                "Wrote %s (%s rows x %d cols)", path.name, f"{len(df):,}", df.shape[1]
            )
        else:
            df = pd.read_parquet(path)
        # Roster must be identical at every checkpoint.
        assert (
            set(map(tuple, df[GROUP_COLS].itertuples(index=False))) == roster_ids
        ), f"checkpoint t={t} roster differs from the fixed student set"
        n_features = (
            df.shape[1] - len(GROUP_COLS) - 2
        )  # minus ids, t_percent, final_result
        stats.append(
            {
                "t_percent": t,
                "n_records": len(df),
                "n_columns": df.shape[1],
                "n_features": n_features,
                "at_risk_rate": round(df["at_risk"].mean(), 4),
            }
        )

    summary = pd.DataFrame(stats)
    summary.to_csv(interim_dir / "checkpoint_summary.csv", index=False)
    log.info("Checkpoint summary:\n%s", summary.to_string(index=False))
    log.info(
        "All six checkpoints share an identical %d-student roster.", len(roster_ids)
    )
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate six time-aware checkpoint datasets."
    )
    p.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    p.add_argument("--out-dir", type=Path, default=CHECKPOINTS_DIR)
    p.add_argument("--force", action="store_true", help="rebuild all checkpoints")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    make_checkpoints(args.raw_dir, args.out_dir, force=args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
