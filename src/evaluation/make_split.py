"""Materialise the fixed train/test split and reuse it everywhere.

The split is defined ONCE at the student level — 20% test, stratified by at_risk,
grouped by id_student (seed 42) — and reused identically across master_raw and all
six checkpoints. This module:
  * writes data/splits/test_student_ids.csv (committed) so every run/teammate uses
    the EXACT same hold-out set even if library versions drift;
  * writes reports/tables/split_report.csv (sizes, balance, zero overlap);
  * optionally materialises per-dataset *_train.parquet / *_test.parquet.

Modelling loads the split via load_checkpoint_split().

CLI:
    python -m src.evaluation.make_split                # definition + report
    python -m src.evaluation.make_split --materialise  # also write parquet

See guide section "evaluation/make_split.py".
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.config import (
    CHECKPOINTS,
    CHECKPOINTS_DIR,
    INTERIM_DATA_DIR,
    RANDOM_SEED,
    SPLITS_DIR,
    TABLES_DIR,
    TEST_SIZE,
)
from src.data.io_utils import save_parquet_atomic
from src.evaluation.split_harness import (
    class_balance,
    group_overlap,
    make_fixed_test_ids,
    split_by_ids,
)

TEST_IDS_PATH = SPLITS_DIR / "test_student_ids.csv"
REPORT_PATH = TABLES_DIR / "split_report.csv"


def save_definition(
    master: pd.DataFrame, seed: int = RANDOM_SEED, test_size: float = TEST_SIZE
) -> set:
    """Compute the fixed test ids from the master roster and persist them.

    The committed ``test_student_ids.csv`` is the source of truth: every run and
    teammate reuses the exact same hold-out membership even if library versions
    drift.
    """
    ids = make_fixed_test_ids(master, test_size, seed)
    SPLITS_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"id_student": sorted(ids)}).to_csv(TEST_IDS_PATH, index=False)
    return ids


def load_test_ids() -> set:
    """Load the committed test id_student list (the source of truth)."""
    return set(pd.read_csv(TEST_IDS_PATH)["id_student"])


def load_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split any dataset into (train, test) using the committed test ids."""
    return split_by_ids(df, load_test_ids())


def load_checkpoint_split(t_percent: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load dataset_t{t}.parquet and split it with the committed test ids.

    This is the convenience entry point the modelling phase calls.
    """
    return load_split(pd.read_parquet(CHECKPOINTS_DIR / f"dataset_t{t_percent}.parquet"))


def build_report(master: pd.DataFrame, ids: set) -> pd.DataFrame:
    """Summarise the split across master and every materialised checkpoint.

    One row per dataset: train/test sizes, at-risk rates, the rate gap and the
    student overlap (which must be 0). Written to ``reports/tables/split_report.csv``.
    """
    rows = []
    datasets = {"master": master}
    for t in CHECKPOINTS:
        p = CHECKPOINTS_DIR / f"dataset_t{t}.parquet"
        if p.exists():
            datasets[f"t{t}"] = pd.read_parquet(p)
    for name, df in datasets.items():
        train, test = split_by_ids(df, ids)
        tr, te = class_balance(train), class_balance(test)
        rows.append(
            {
                "dataset": name,
                "n_train": tr["n_rows"],
                "n_test": te["n_rows"],
                "n_test_students": te["n_students"],
                "train_at_risk_rate": tr["at_risk_rate"],
                "test_at_risk_rate": te["at_risk_rate"],
                "rate_gap": round(abs(tr["at_risk_rate"] - te["at_risk_rate"]), 4),
                "student_overlap": group_overlap(train, test),
            }
        )
    report = pd.DataFrame(rows)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(REPORT_PATH, index=False)
    return report


def materialise(master: pd.DataFrame, ids: set) -> None:
    """Write per-dataset train/test parquet files (git-ignored)."""
    train, test = split_by_ids(master, ids)
    save_parquet_atomic(train, SPLITS_DIR / "master_train.parquet")
    save_parquet_atomic(test, SPLITS_DIR / "master_test.parquet")
    for t in CHECKPOINTS:
        p = CHECKPOINTS_DIR / f"dataset_t{t}.parquet"
        if not p.exists():
            continue
        tr, te = split_by_ids(pd.read_parquet(p), ids)
        save_parquet_atomic(tr, SPLITS_DIR / f"dataset_t{t}_train.parquet")
        save_parquet_atomic(te, SPLITS_DIR / f"dataset_t{t}_test.parquet")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Materialise the fixed train/test split.")
    p.add_argument(
        "--materialise", action="store_true", help="also write train/test parquet files"
    )
    args = p.parse_args(argv)

    master = pd.read_parquet(INTERIM_DATA_DIR / "master_raw.parquet")
    ids = save_definition(master)
    report = build_report(master, ids)
    print(
        f"Test set: {len(ids)} students (seed={RANDOM_SEED}, test_size={TEST_SIZE}); "
        f"definition -> {TEST_IDS_PATH.relative_to(Path.cwd()) if TEST_IDS_PATH.is_relative_to(Path.cwd()) else TEST_IDS_PATH}"
    )
    print(report.to_string(index=False))
    assert (report["student_overlap"] == 0).all(), "student overlap detected"
    assert (report["rate_gap"] <= 0.02).all(), "class ratio not preserved"
    if args.materialise:
        materialise(master, ids)
        print(f"Materialised train/test parquet under {SPLITS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
