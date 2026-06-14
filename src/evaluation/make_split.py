"""Materialise the fixed train/test split (Tasks 7, 8, 15).

The split is defined ONCE at the student level — a 20% test set, stratified by
``at_risk`` and grouped by ``id_student`` (seed 42) — and reused identically across
``master_raw`` and all six checkpoint datasets. This module:

* writes the canonical split definition ``data/splits/test_student_ids.csv``
  (committed, ~6.5k ids) so every run and every team member uses the exact same
  hold-out set even if library versions drift;
* writes ``reports/tables/split_report.csv`` verifying sizes, class balance and
  zero student overlap;
* optionally materialises per-dataset ``*_train.parquet`` / ``*_test.parquet``
  files (git-ignored) for convenience.

The modelling phase should load the split with :func:`load_checkpoint_split`.

CLI
    python -m src.evaluation.make_split                # split definition + report
    python -m src.evaluation.make_split --materialise  # also write train/test parquet
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import RANDOM_SEED, TEST_SIZE  # noqa: E402
from src.data.io_utils import CHECKPOINTS_DIR, INTERIM_DIR, save_parquet_atomic  # noqa: E402
from src.data.time_utils import CHECKPOINTS  # noqa: E402
from src.evaluation.split_harness import (  # noqa: E402
    class_balance,
    group_overlap,
    make_fixed_test_ids,
    split_by_ids,
)

SPLITS_DIR = Path(__file__).resolve().parents[2] / "data" / "splits"
REPORT_PATH = (
    Path(__file__).resolve().parents[2] / "reports" / "tables" / "split_report.csv"
)
TEST_IDS_PATH = SPLITS_DIR / "test_student_ids.csv"


def save_definition(
    master: pd.DataFrame, seed: int = RANDOM_SEED, test_size: float = TEST_SIZE
) -> set:
    """Compute and persist the canonical test id_student list."""
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


def load_checkpoint_split(
    t: int, checkpoints_dir: Path = CHECKPOINTS_DIR
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Convenience for the modelling phase: (train, test) for checkpoint ``t``."""
    return load_split(pd.read_parquet(checkpoints_dir / f"dataset_t{t}.parquet"))


def build_report(master: pd.DataFrame, ids: set) -> pd.DataFrame:
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

    master = pd.read_parquet(INTERIM_DIR / "master_raw.parquet")
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
    sys.exit(main())
