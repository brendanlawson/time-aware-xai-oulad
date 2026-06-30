"""Aggregate assessment submissions (studentAssessment) into performance features,
computed *as of a cutoff day* (so it works for the master table at t=100% and for
every checkpoint).

Per student-module-presentation:
    n_assessments_submitted  - submissions with date_submitted <= cutoff
    mean_score_to_date        - mean score of those submissions
    weighted_score_to_date    - sum(score * weight / 100) of those submissions
    not_submitted             - 1 if >=1 assessment whose deadline already passed
                                (deadline <= cutoff) was NOT submitted by cutoff.

`aggregate_performance` MUST be pure and cutoff-driven. `not_submitted`
distinguishes a genuine miss from "no deadline yet", so filling missing scores
with 0 downstream stays meaningful.

See guide section "data/build_performance_features.py".
"""

from __future__ import annotations

import pandas as pd

from src.data.io_utils import GROUP_COLS, PRESENTATION_KEY


def aggregate_performance(
    submissions: pd.DataFrame,
    assessments: pd.DataFrame,
    cutoff_lookup: pd.DataFrame,
    roster: pd.DataFrame,
) -> pd.DataFrame:
    """Build per-student performance features as of each presentation's cutoff.

    Parameters
    ----------
    submissions   : studentAssessment (id_assessment, id_student, date_submitted,
                    is_banked, score).
    assessments   : assessments.csv (id_assessment, PRESENTATION_KEY,
                    assessment_type, date [deadline; NaN for final exam], weight).
    cutoff_lookup : PRESENTATION_KEY + ``cutoff_day`` (module length for t=100%,
                    or the checkpoint day).
    roster        : every student to emit a row for (GROUP_COLS); guarantees
                    non-submitters still receive features (and not_submitted).
    """
    meta = assessments.merge(cutoff_lookup, on=PRESENTATION_KEY, how="left")
    # An assessment is "due to date" when it has a real deadline on/before cutoff.
    meta["is_due"] = meta["date"].notna() & (meta["date"] <= meta["cutoff_day"])
    due_per_pres = meta[meta["is_due"]].groupby(PRESENTATION_KEY).size().rename("n_due_to_date")

    sub = submissions.merge(
        meta[["id_assessment", *PRESENTATION_KEY, "weight", "cutoff_day", "is_due"]],
        on="id_assessment",
        how="left",
    )
    # Submissions counted "to date": real (not banked) and submitted by cutoff.
    submitted = sub[(sub["is_banked"] == 0) & (sub["date_submitted"] <= sub["cutoff_day"])].copy()
    submitted["weighted"] = submitted["score"] * submitted["weight"] / 100.0

    agg = submitted.groupby(GROUP_COLS).agg(
        n_assessments_submitted=("id_assessment", "count"),
        mean_score_to_date=("score", "mean"),
        weighted_score_to_date=("weighted", "sum"),
    )
    # Of those, how many were for assessments whose deadline had passed.
    submitted_due = (
        submitted[submitted["is_due"]].groupby(GROUP_COLS).size().rename("n_submitted_due")
    )

    out = roster[GROUP_COLS].drop_duplicates().copy()
    out = out.merge(agg, on=GROUP_COLS, how="left")
    out = out.merge(submitted_due, on=GROUP_COLS, how="left")
    out = out.merge(due_per_pres, on=PRESENTATION_KEY, how="left")

    out["n_assessments_submitted"] = out["n_assessments_submitted"].fillna(0).astype("int32")
    out["mean_score_to_date"] = out["mean_score_to_date"].fillna(0.0)
    out["weighted_score_to_date"] = out["weighted_score_to_date"].fillna(0.0)
    n_due = out["n_due_to_date"].fillna(0)
    n_submitted_due = out["n_submitted_due"].fillna(0)
    out["not_submitted"] = ((n_due - n_submitted_due) > 0).astype("int8")

    return out.drop(columns=["n_submitted_due", "n_due_to_date"])
