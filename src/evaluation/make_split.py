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

import pandas as pd

from src.config import (
    RANDOM_SEED,
    SPLITS_DIR,
    TABLES_DIR,
    TEST_SIZE,
)

TEST_IDS_PATH = SPLITS_DIR / "test_student_ids.csv"
REPORT_PATH = TABLES_DIR / "split_report.csv"


def save_definition(
    master: pd.DataFrame, seed: int = RANDOM_SEED, test_size: float = TEST_SIZE
) -> set:
    """Compute the fixed test ids from the master roster and persist them.

    TODO: ids = make_fixed_test_ids(master, test_size, seed); write sorted ids to
    TEST_IDS_PATH (one column); return the set.
    """
    raise NotImplementedError


def load_test_ids() -> set:
    """TODO: read TEST_IDS_PATH -> set of id_student."""
    raise NotImplementedError


def load_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """TODO: split_by_ids(df, load_test_ids())."""
    raise NotImplementedError


def load_checkpoint_split(t_percent: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load dataset_t{t}.parquet and split it with the committed test ids.

    TODO: read CHECKPOINTS_DIR/f"dataset_t{t_percent}.parquet"; return load_split.
    This is the function the modelling phase calls.
    """
    raise NotImplementedError


def build_report(master: pd.DataFrame, ids: set) -> pd.DataFrame:
    """TODO: split master by ids, return build_split_report(train, test)."""
    raise NotImplementedError


def materialise(master: pd.DataFrame, ids: set) -> None:
    """Write *_train/_test parquet for master + every checkpoint (git-ignored).

    TODO: for master and each checkpoint, split_by_ids then save_parquet_atomic.
    """
    raise NotImplementedError


def main(argv: list[str] | None = None) -> int:
    """TODO: load master, save_definition, write report; if --materialise also
    materialise(); return 0."""
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
