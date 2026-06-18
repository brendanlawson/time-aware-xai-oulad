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
    cutoff_lookup : PRESENTATION_KEY + ``cutoff_day``.
    roster        : every student to emit a row for (GROUP_COLS) — guarantees
                    non-submitters still get features (and not_submitted).

    TODO:
      1. Attach PRESENTATION_KEY + deadline + weight to submissions via id_assessment.
      2. Merge cutoff_lookup; keep submissions with date_submitted <= cutoff_day.
      3. Group by GROUP_COLS -> n_assessments_submitted, mean_score_to_date,
         weighted_score_to_date.
      4. not_submitted: per presentation, find assessments with deadline <= cutoff
         ("due to date"); a student is flagged if they submitted fewer than the
         number due to date. (Build a per-presentation "n_due_to_date" count.)
      5. Left-join everything onto roster so every student appears. Return frame.
    """
    raise NotImplementedError
