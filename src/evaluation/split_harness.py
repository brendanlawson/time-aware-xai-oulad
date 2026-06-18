"""Leakage-safe train/test splitting primitives.

Three guarantees from ONE student-level split:
  * Group-aware  : id_student is the group -> a student never appears in both
                   train and test (no leakage across that student's presentations).
  * Stratified   : the at-risk class ratio is preserved in train and test.
  * Fixed test   : defined once, by id_student; the same membership applies to
                   every checkpoint (the roster is identical), so the six
                   performance points are comparable.

StratifiedGroupKFold gives group-aware + stratified at once; take one fold as the
fixed hold-out test set and cross-validate on the remainder.

See guide section "evaluation/split_harness.py".
"""

from __future__ import annotations

import numpy as np  # noqa: F401
import pandas as pd

from src.config import RANDOM_SEED, TEST_SIZE

GROUP_COL = "id_student"
TARGET_COL = "at_risk"


def make_fixed_test_ids(
    roster: pd.DataFrame, test_size: float = TEST_SIZE, seed: int = RANDOM_SEED
) -> set:
    """Return the set of id_student in the fixed hold-out test set.

    TODO:
      1. n_splits = max(2, round(1/test_size)).
      2. StratifiedGroupKFold(n_splits, shuffle=True, random_state=seed).
      3. Take the FIRST fold's test indices; return the unique id_student there.
    Splitting by id_student (not row) is what makes the test set reusable across
    checkpoints.
    """
    raise NotImplementedError


def split_by_ids(df: pd.DataFrame, test_ids: set) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split any (checkpoint) dataset into (train, test) by test_ids membership.

    TODO: mask = df[GROUP_COL].isin(test_ids); return df[~mask], df[mask].
    """
    raise NotImplementedError


def group_overlap(train: pd.DataFrame, test: pd.DataFrame) -> int:
    """Count id_student appearing in BOTH (must be 0). TODO."""
    raise NotImplementedError


def class_balance(df: pd.DataFrame) -> dict:
    """Return {0: n0, 1: n1, 'rate': at_risk_rate}. TODO."""
    raise NotImplementedError


def build_split_report(train: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    """One-row-per-set report: sizes, class balance, overlap. TODO."""
    raise NotImplementedError


def iter_cv_folds(train: pd.DataFrame, n_splits: int = 5, seed: int = RANDOM_SEED):
    """Yield (train_idx, val_idx) StratifiedGroupKFold folds over the TRAIN set.

    TODO: yield from StratifiedGroupKFold(...).split(train, y=at_risk,
    groups=id_student). Use inside model selection so CV is also leakage-safe.
    """
    raise NotImplementedError
