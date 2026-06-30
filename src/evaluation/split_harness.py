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

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

from src.config import RANDOM_SEED, TEST_SIZE

GROUP_COL = "id_student"
TARGET_COL = "at_risk"


def make_fixed_test_ids(
    roster: pd.DataFrame, test_size: float = TEST_SIZE, seed: int = RANDOM_SEED
) -> set:
    """Return the set of id_student in the fixed hold-out test set.

    Splitting by id_student (not by row) is what makes the test set reusable
    across checkpoints: every checkpoint shares the same roster, so the same ids
    select the same rows everywhere.
    """
    n_splits = max(2, round(1 / test_size))
    sgkf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    y = roster[TARGET_COL].to_numpy()
    groups = roster[GROUP_COL].to_numpy()
    _, test_idx = next(sgkf.split(roster, y, groups))
    return set(roster.iloc[test_idx][GROUP_COL].unique())


def split_by_ids(df: pd.DataFrame, test_ids: set) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split any (checkpoint) dataset into (train, test) by test_ids membership."""
    is_test = df[GROUP_COL].isin(test_ids)
    return df[~is_test].reset_index(drop=True), df[is_test].reset_index(drop=True)


def group_overlap(train: pd.DataFrame, test: pd.DataFrame) -> int:
    """Number of id_student present in both sets (must be 0)."""
    return len(set(train[GROUP_COL]) & set(test[GROUP_COL]))


def class_balance(df: pd.DataFrame) -> dict:
    """Row/student counts and the at-risk rate for one split."""
    return {
        "n_rows": int(len(df)),
        "n_students": int(df[GROUP_COL].nunique()),
        "at_risk_rate": round(float(df[TARGET_COL].mean()), 4),
    }


def build_split_report(
    master: pd.DataFrame, test_size: float = TEST_SIZE, seed: int = RANDOM_SEED
) -> pd.DataFrame:
    """One-row-per-split summary used to verify and document the split.

    Performs the fixed split internally so callers can pass just the roster/master
    table; returns rows ``train`` / ``test`` / ``overlap_students``.
    """
    test_ids = make_fixed_test_ids(master, test_size, seed)
    train, test = split_by_ids(master, test_ids)
    overlap = group_overlap(train, test)
    rows = [
        {"split": "train", **class_balance(train)},
        {"split": "test", **class_balance(test)},
        {
            "split": "overlap_students",
            "n_rows": overlap,
            "n_students": overlap,
            "at_risk_rate": np.nan,
        },
    ]
    return pd.DataFrame(rows)


def iter_cv_folds(
    train: pd.DataFrame, n_splits: int = 5, n_repeats: int = 5, seed: int = RANDOM_SEED
):
    """Yield ``(repeat, fold, train_idx, val_idx)`` for repeated stratified group
    k-fold over the TRAIN set — the 5-fold x 5-seed scheme from the proposal. Each
    repeat uses a different seed so results do not hinge on a single partition.
    """
    y = train[TARGET_COL].to_numpy()
    groups = train[GROUP_COL].to_numpy()
    for r in range(n_repeats):
        sgkf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed + r)
        for fold_idx, (tr, va) in enumerate(sgkf.split(train, y, groups)):
            yield r, fold_idx, tr, va
