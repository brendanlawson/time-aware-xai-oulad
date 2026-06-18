"""Automated temporal-leakage and split-integrity tests (Task 14, Khoa).

Guards the two mechanisms that prevent over-optimistic results:

* cut_at_checkpoint never keeps a record dated after its checkpoint day, for all
  six checkpoints, on both the clickstream and the assessment submissions;
* the split harness produces no student overlap and preserves the class ratio.

Run:  pytest tests/test_leakage.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.io_utils import PRESENTATION_KEY, RAW_DIR, add_at_risk_label  # noqa: E402
from src.data.time_utils import CHECKPOINTS, build_checkpoint_map, cut_at_checkpoint  # noqa: E402
from src.evaluation.split_harness import (  # noqa: E402
    build_split_report,
    group_overlap,
    make_fixed_test_ids,
    split_by_ids,
)


@pytest.fixture(scope="module")
def checkpoint_map() -> pd.DataFrame:
    return build_checkpoint_map(pd.read_csv(RAW_DIR / "courses.csv"))


@pytest.fixture(scope="module")
def clickstream() -> pd.DataFrame:
    return pd.read_csv(RAW_DIR / "studentVle.csv")


@pytest.fixture(scope="module")
def submissions() -> pd.DataFrame:
    assessments = pd.read_csv(RAW_DIR / "assessments.csv")
    return pd.read_csv(RAW_DIR / "studentAssessment.csv").merge(
        assessments[["id_assessment", *PRESENTATION_KEY]],
        on="id_assessment",
        how="left",
    )


@pytest.fixture(scope="module")
def roster() -> pd.DataFrame:
    return add_at_risk_label(pd.read_csv(RAW_DIR / "studentInfo.csv"))


def _max_date_exceeds_cutoff(
    cut: pd.DataFrame, cmap: pd.DataFrame, t: int, date_col: str
) -> int:
    cutoffs = cmap.loc[cmap["t_percent"] == t, PRESENTATION_KEY + ["cutoff_day"]]
    merged = cut.merge(cutoffs, on=PRESENTATION_KEY, how="left")
    return int((merged[date_col] > merged["cutoff_day"]).sum())


@pytest.mark.parametrize("t", CHECKPOINTS)
def test_no_clickstream_leakage(clickstream, checkpoint_map, t):
    cut = cut_at_checkpoint(clickstream, t, checkpoint_map, date_col="date")
    assert _max_date_exceeds_cutoff(cut, checkpoint_map, t, "date") == 0


@pytest.mark.parametrize("t", CHECKPOINTS)
def test_no_submission_leakage(submissions, checkpoint_map, t):
    cut = cut_at_checkpoint(submissions, t, checkpoint_map, date_col="date_submitted")
    assert _max_date_exceeds_cutoff(cut, checkpoint_map, t, "date_submitted") == 0


def test_counts_non_decreasing_in_t(clickstream, checkpoint_map):
    counts = [
        len(cut_at_checkpoint(clickstream, t, checkpoint_map, "date"))
        for t in CHECKPOINTS
    ]
    assert counts == sorted(counts)


def test_t100_keeps_all_dated_clicks(clickstream, checkpoint_map):
    cut = cut_at_checkpoint(clickstream, 100, checkpoint_map, date_col="date")
    assert len(cut) == int(clickstream["date"].notna().sum())


def test_split_has_no_group_overlap(roster):
    test_ids = make_fixed_test_ids(roster)
    train, test = split_by_ids(roster, test_ids)
    assert group_overlap(train, test) == 0


def test_split_preserves_class_ratio(roster):
    report = build_split_report(roster).set_index("split")
    train_rate = report.loc["train", "at_risk_rate"]
    test_rate = report.loc["test", "at_risk_rate"]
    assert abs(train_rate - test_rate) <= 0.02


def test_preprocessing_uses_train_only_stats():
    """Imputation median and winsorize bounds must be learned on TRAIN and applied
    to TEST — no test-set statistic may leak into the test transform (Task 22)."""
    from src.features.preprocessing import handle_missing, handle_outliers

    train = pd.DataFrame(
        {"date_registration": [0.0, 10.0, 20.0], "studied_credits": [30.0, 60.0, 100.0]}
    )
    test = pd.DataFrame(
        {"date_registration": [np.nan, 5.0], "studied_credits": [40.0, 99999.0]}
    )

    # Missing: a TEST NaN must be filled with the TRAIN median (10), not test's own (5).
    m_stats: dict = {}
    handle_missing(train.copy(), stats=m_stats)
    te = handle_missing(test.copy(), stats=m_stats)
    assert m_stats["date_registration_median"] == 10.0
    assert te["date_registration"].iloc[0] == 10.0

    # Outliers: a TEST extreme must be clipped to the TRAIN p99, not test's own.
    o_stats: dict = {}
    tr = handle_outliers(train.copy(), stats=o_stats)
    teo = handle_outliers(test.copy(), stats=o_stats)
    _, hi = o_stats["winsor_studied_credits"]
    assert hi < 1000  # train p99 ~99, far below the test extreme 99999
    assert teo["studied_credits"].max() <= hi + 1e-6
    assert tr["studied_credits"].max() <= hi + 1e-6


def test_feature_frame_excludes_leaky_columns():
    """make_X_y hands the model only allow-listed features — never the label, its raw
    source (final_result) or the withdrawal date (the classic 'drop the label' leak)."""
    from src.features.preprocessing import LEAKY_COLUMNS, make_X_y

    master = pd.read_parquet(PROJECT_ROOT / "data" / "interim" / "master_raw.parquet")
    X, y = make_X_y(master)
    assert not (set(X.columns) & LEAKY_COLUMNS), "leaky column reached X"
    assert "date_unregistration" not in X.columns
    assert "final_result" not in X.columns
    assert y is not None and set(pd.unique(y)) <= {0, 1}


def test_checkpoint_t100_idle_matches_master():
    """At t=100% the checkpoint must reproduce master_raw for days_since_last_activity,
    including no-activity students (idle = full window, not 0). Guards the engagement
    fill-order bug where no-activity idle was wrongly set to 0."""
    interim = PROJECT_ROOT / "data" / "interim" / "master_raw.parquet"
    ckpt = PROJECT_ROOT / "data" / "checkpoints" / "dataset_t100.parquet"
    if not (interim.exists() and ckpt.exists()):
        pytest.skip("master_raw / dataset_t100 parquet not materialised")
    key = ["code_module", "code_presentation", "id_student"]
    col = "days_since_last_activity"
    m = pd.read_parquet(interim)[key + [col]].set_index(key)
    c = pd.read_parquet(ckpt)[key + [col]].set_index(key)
    diff = (m[col] - c.reindex(m.index)[col]).abs()
    assert diff.max() <= 1.0, f"t100 idle disagrees with master (max diff {diff.max()})"
