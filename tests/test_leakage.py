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
