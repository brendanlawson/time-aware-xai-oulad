"""Time-aware utilities (Tasks 10 and 11, Khoa).

Task 10: build the checkpoint map converting progress percentages
         (10/20/40/60/80/100%) into concrete day thresholds per module-
         presentation, since course lengths differ.
Task 11: cut_at_checkpoint() keeps only records on or before the checkpoint day,
         simulating the information available at prediction time (leakage rule #2).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.data.io_utils import CHECKPOINT_MAP_PATH, PRESENTATION_KEY, RAW_DIR  # noqa: E402

CHECKPOINTS = (10, 20, 40, 60, 80, 100)


def build_checkpoint_map(
    courses: pd.DataFrame, checkpoints=CHECKPOINTS
) -> pd.DataFrame:
    """Lookup table: (code_module, code_presentation, t_percent) -> cutoff_day.

    cutoff_day = round(module_presentation_length * t / 100). Long format: one row
    per module-presentation per checkpoint.
    """
    rows = []
    for _, course in courses.iterrows():
        length = course["module_presentation_length"]
        for t in checkpoints:
            rows.append(
                {
                    "code_module": course["code_module"],
                    "code_presentation": course["code_presentation"],
                    "t_percent": t,
                    "module_presentation_length": length,
                    "cutoff_day": round(length * t / 100),
                }
            )
    return pd.DataFrame(rows)


def load_checkpoint_map(path=CHECKPOINT_MAP_PATH) -> pd.DataFrame:
    return pd.read_csv(path)


def cut_at_checkpoint(
    df: pd.DataFrame,
    t_percent: int,
    checkpoint_map: pd.DataFrame,
    date_col: str = "date",
) -> pd.DataFrame:
    """Keep only rows whose ``date_col`` does not exceed the checkpoint day.

    ``df`` must contain PRESENTATION_KEY and ``date_col`` (days relative to the
    presentation start). Rows with a missing date are dropped: their timing cannot
    be verified against the checkpoint.
    """
    if t_percent not in set(checkpoint_map["t_percent"]):
        raise ValueError(
            f"t_percent={t_percent} not in checkpoint map "
            f"(available: {sorted(checkpoint_map['t_percent'].unique())})"
        )
    missing = set(PRESENTATION_KEY + [date_col]) - set(df.columns)
    if missing:
        raise KeyError(f"df is missing required columns: {sorted(missing)}")

    cutoffs = checkpoint_map.loc[
        checkpoint_map["t_percent"] == t_percent,
        PRESENTATION_KEY + ["cutoff_day"],
    ]
    merged = df.merge(cutoffs, on=PRESENTATION_KEY, how="left", validate="many_to_one")
    if merged["cutoff_day"].isna().any():
        unmatched = (
            merged.loc[merged["cutoff_day"].isna(), PRESENTATION_KEY]
            .drop_duplicates()
            .to_records(index=False)
            .tolist()
        )
        raise ValueError(
            f"module-presentations missing from checkpoint map: {unmatched}"
        )

    kept = merged[merged[date_col].notna() & (merged[date_col] <= merged["cutoff_day"])]
    return kept.drop(columns="cutoff_day").reset_index(drop=True)


def main():
    courses = pd.read_csv(RAW_DIR / "courses.csv")
    checkpoint_map = build_checkpoint_map(courses)

    assert len(checkpoint_map) == len(courses) * len(
        CHECKPOINTS
    ), "expected 22 x 6 rows"
    expected = (
        (
            checkpoint_map["module_presentation_length"]
            * checkpoint_map["t_percent"]
            / 100
        )
        .round()
        .astype(int)
    )
    assert (
        checkpoint_map["cutoff_day"] == expected
    ).all(), "formula round(length * t%) violated"

    CHECKPOINT_MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_map.to_csv(CHECKPOINT_MAP_PATH, index=False)
    print(
        f"Wrote {CHECKPOINT_MAP_PATH} ({len(checkpoint_map)} rows = "
        f"{len(courses)} module-presentations x {len(CHECKPOINTS)} checkpoints)"
    )

    # Verify cut_at_checkpoint on one module-presentation (Task 11).
    module, presentation = "AAA", "2013J"
    vle = pd.read_csv(RAW_DIR / "studentVle.csv")
    vle = vle[
        (vle["code_module"] == module) & (vle["code_presentation"] == presentation)
    ]

    assessments = pd.read_csv(RAW_DIR / "assessments.csv")
    submissions = pd.read_csv(RAW_DIR / "studentAssessment.csv").merge(
        assessments[["id_assessment", "code_module", "code_presentation"]],
        on="id_assessment",
        how="left",
    )
    submissions = submissions[
        (submissions["code_module"] == module)
        & (submissions["code_presentation"] == presentation)
    ]

    print(
        f"\nVerification on {module}/{presentation} "
        f"(full data: {len(vle)} interactions, {len(submissions)} submissions):"
    )
    print(f"{'t%':>4} {'cutoff_day':>10} {'interactions':>12} {'submissions':>11}")
    prev_clicks, prev_subs = -1, -1
    for t in CHECKPOINTS:
        vle_t = cut_at_checkpoint(vle, t, checkpoint_map, date_col="date")
        sub_t = cut_at_checkpoint(
            submissions, t, checkpoint_map, date_col="date_submitted"
        )
        cutoff = checkpoint_map.loc[
            (checkpoint_map["code_module"] == module)
            & (checkpoint_map["code_presentation"] == presentation)
            & (checkpoint_map["t_percent"] == t),
            "cutoff_day",
        ].item()
        print(f"{t:>4} {cutoff:>10} {len(vle_t):>12} {len(sub_t):>11}")
        assert (
            len(vle_t) >= prev_clicks and len(sub_t) >= prev_subs
        ), "counts must be non-decreasing in t"
        prev_clicks, prev_subs = len(vle_t), len(sub_t)

    full_vle = vle[vle["date"].notna()]
    vle_100 = cut_at_checkpoint(vle, 100, checkpoint_map, date_col="date")
    assert len(vle_100) == len(full_vle), "t=100% should keep all dated interactions"
    print(
        "\nAll checks passed: counts non-decreasing in t; t=100% keeps all dated records."
    )


if __name__ == "__main__":
    main()
