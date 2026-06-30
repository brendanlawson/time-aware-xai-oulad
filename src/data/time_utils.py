"""Time-aware utilities — the heart of the "time-aware" framing.

build_checkpoint_map: convert progress percentages (10/20/40/60/80/100%) into
    concrete day thresholds per module-presentation (course lengths differ).
cut_at_checkpoint: keep only records on/before the checkpoint day — simulates the
    information available at prediction time (anti-leakage rule #2).

See guide section "data/time_utils.py".
"""

from __future__ import annotations

import pandas as pd

from src.config import CHECKPOINT_MAP_PATH, CHECKPOINTS
from src.data.io_utils import PRESENTATION_KEY, RAW_DIR


def build_checkpoint_map(courses: pd.DataFrame, checkpoints=CHECKPOINTS) -> pd.DataFrame:
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
    """Read the checkpoint map CSV written by :func:`main`."""
    return pd.read_csv(path)


def cut_at_checkpoint(
    df: pd.DataFrame,
    t_percent: int,
    checkpoint_map: pd.DataFrame,
    date_col: str = "date",
) -> pd.DataFrame:
    """Keep only rows whose ``date_col`` does not exceed the checkpoint day.

    ``df`` must contain :data:`PRESENTATION_KEY` and ``date_col`` (days relative to
    the presentation start). Rows with a missing date are dropped: their timing
    cannot be verified against the checkpoint, so they are excluded everywhere
    consistently (and at t=100% this means "all dated records are kept").
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
        raise ValueError(f"module-presentations missing from checkpoint map: {unmatched}")

    kept = merged[merged[date_col].notna() & (merged[date_col] <= merged["cutoff_day"])]
    return kept.drop(columns="cutoff_day").reset_index(drop=True)


def main():
    """Build, validate and persist the checkpoint map; spot-check cut_at_checkpoint."""
    courses = pd.read_csv(RAW_DIR / "courses.csv")
    checkpoint_map = build_checkpoint_map(courses)

    assert len(checkpoint_map) == len(courses) * len(CHECKPOINTS), "expected 22 x 6 rows"
    expected = (
        (checkpoint_map["module_presentation_length"] * checkpoint_map["t_percent"] / 100)
        .round()
        .astype(int)
    )
    assert (checkpoint_map["cutoff_day"] == expected).all(), "round(length * t%) violated"

    CHECKPOINT_MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_map.to_csv(CHECKPOINT_MAP_PATH, index=False)
    print(
        f"Wrote {CHECKPOINT_MAP_PATH} ({len(checkpoint_map)} rows = "
        f"{len(courses)} module-presentations x {len(CHECKPOINTS)} checkpoints)"
    )

    # Sanity-check the cut on one module-presentation: counts non-decreasing in t,
    # and t=100% keeps every dated interaction.
    vle = pd.read_csv(RAW_DIR / "studentVle.csv")
    vle = vle[(vle["code_module"] == "AAA") & (vle["code_presentation"] == "2013J")]
    prev = -1
    for t in CHECKPOINTS:
        n = len(cut_at_checkpoint(vle, t, checkpoint_map, date_col="date"))
        assert n >= prev, "counts must be non-decreasing in t"
        prev = n
    n100 = len(cut_at_checkpoint(vle, 100, checkpoint_map, date_col="date"))
    assert n100 == int(vle["date"].notna().sum()), "t=100% must keep all dated clicks"
    print("Checks passed: counts non-decreasing in t; t=100% keeps all dated records.")


if __name__ == "__main__":
    main()
