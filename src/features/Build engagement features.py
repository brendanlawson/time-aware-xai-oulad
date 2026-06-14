"""
build_engagement_features.py
=============================
DSP391m - Nhom 1 | OULAD - VLE Engagement Feature Aggregation

Tac vu
------
Gop studentVle.csv voi vle.csv, sau do tong hop (aggregate) thanh
cac dac trung muc do tuong tac (engagement) cho moi sinh vien trong
moi module-presentation:

    - total_clicks      : tong so luot click
    - active_days       : so ngay co hoat dong (unique dates)
    - <activity_type>_count : so luot tuong tac theo tung loai hoat dong
                               (forumng_count, oucontent_count, ...)

Dau vao
-------
    data/raw/studentVle.csv
    data/raw/vle.csv

Dau ra
------
    data/interim/cleaned/engagement_agg.parquet

Cach chay
---------
    python build_engagement_features.py
    python build_engagement_features.py --data-dir ../data/raw --output-dir ../data/interim/cleaned
    python build_engagement_features.py --verbose
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

GROUP_COLS = ["code_module", "code_presentation", "id_student"]


# ════════════════════════════════════════════════════════════════════════
# 1. LOAD DATA
# ════════════════════════════════════════════════════════════════════════

def load_data(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Doc studentVle.csv va vle.csv tu data_dir."""
    student_vle_path = data_dir / "studentVle.csv"
    vle_path = data_dir / "vle.csv"

    for p in (student_vle_path, vle_path):
        if not p.exists():
            raise FileNotFoundError(f"Khong tim thay file: {p}")

    log.info("Doc %s", student_vle_path)
    student_vle_df = pd.read_csv(student_vle_path)

    log.info("Doc %s", vle_path)
    vle_df = pd.read_csv(vle_path)

    log.info(
        "studentVle.csv: %s dong | vle.csv: %s dong",
        f"{len(student_vle_df):,}", f"{len(vle_df):,}",
    )
    return student_vle_df, vle_df


# ════════════════════════════════════════════════════════════════════════
# 2. MERGE studentVle WITH vle (lay activity_type)
# ════════════════════════════════════════════════════════════════════════

def merge_vle(student_vle_df: pd.DataFrame, vle_df: pd.DataFrame) -> pd.DataFrame:
    """Gop studentVle voi vle de co cot activity_type cho moi luot click."""
    merged_df = pd.merge(
        student_vle_df,
        vle_df,
        on=["code_module", "code_presentation", "id_site"],
        how="left",
    )
    n_missing_type = merged_df["activity_type"].isnull().sum()
    if n_missing_type:
        log.warning(
            "%s dong khong khop activity_type sau khi merge (id_site khong co trong vle.csv)",
            f"{n_missing_type:,}",
        )
    log.info("Merged shape: %s", merged_df.shape)
    return merged_df


# ════════════════════════════════════════════════════════════════════════
# 3. AGGREGATE — activity_type counts (pivot)
# ════════════════════════════════════════════════════════════════════════

def build_activity_counts(merged_df: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot: voi moi (code_module, code_presentation, id_student),
    tinh so luot click theo tung activity_type
    -> cot dat ten <activity_type>_count.
    """
    activity_counts = pd.pivot_table(
        merged_df,
        values="sum_click",
        index=GROUP_COLS,
        columns="activity_type",
        aggfunc="count",
        fill_value=0,
    ).reset_index()

    activity_counts.columns.name = None
    activity_counts = activity_counts.rename(
        columns={
            col: f"{col}_count"
            for col in activity_counts.columns
            if col not in GROUP_COLS
        }
    )

    n_activity_cols = activity_counts.shape[1] - len(GROUP_COLS)
    log.info(
        "activity_counts shape: %s | so loai hoat dong: %d",
        activity_counts.shape, n_activity_cols,
    )
    return activity_counts


# ════════════════════════════════════════════════════════════════════════
# 4. AGGREGATE — total_clicks va active_days
# ════════════════════════════════════════════════════════════════════════

def build_total_clicks_active_days(merged_df: pd.DataFrame) -> pd.DataFrame:
    """
    Voi moi (code_module, code_presentation, id_student):
        total_clicks = tong sum_click
        active_days  = so ngay (date) khac nhau co hoat dong
    """
    agg_df = (
        merged_df.groupby(GROUP_COLS)
        .agg(
            total_clicks=("sum_click", "sum"),
            active_days=("date", "nunique"),
        )
        .reset_index()
    )
    log.info("agg_df shape: %s", agg_df.shape)
    return agg_df


# ════════════════════════════════════════════════════════════════════════
# 5. MERGE TONG HOP
# ════════════════════════════════════════════════════════════════════════

def merge_aggregates(agg_df: pd.DataFrame, activity_counts: pd.DataFrame) -> pd.DataFrame:
    """Gop agg_df (total_clicks, active_days) voi activity_counts (theo loai)."""
    engagement_agg = pd.merge(agg_df, activity_counts, on=GROUP_COLS)
    log.info("engagement_agg shape: %s", engagement_agg.shape)
    return engagement_agg


# ════════════════════════════════════════════════════════════════════════
# 6. VERIFICATION
# ════════════════════════════════════════════════════════════════════════

def verify(student_vle_df: pd.DataFrame, engagement_agg: pd.DataFrame) -> bool:
    """
    Kiem tra: so sinh vien duy nhat trong du lieu goc phai bang
    so dong trong engagement_agg (mot dong / sinh vien / module-presentation).
    """
    original_students = student_vle_df[GROUP_COLS].drop_duplicates()
    n_original = len(original_students)
    n_aggregated = len(engagement_agg)

    log.info("So sinh vien duy nhat (du lieu goc) : %s", f"{n_original:,}")
    log.info("So dong trong du lieu da tong hop   : %s", f"{n_aggregated:,}")

    ok = n_original == n_aggregated
    if ok:
        log.info("OK - Kiem chung thanh cong: so luong khop.")
    else:
        log.error("LOI - Kiem chung khong khop: so luong khac nhau!")
    return ok


# ════════════════════════════════════════════════════════════════════════
# 7. SAVE
# ════════════════════════════════════════════════════════════════════════

def save_output(engagement_agg: pd.DataFrame, output_dir: Path) -> Path:
    """Luu engagement_agg ra file parquet."""
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "engagement_agg.parquet"
    engagement_agg.to_parquet(out_path, index=False)
    log.info("Da luu: %s (%s dong, %s cot)", out_path, f"{len(engagement_agg):,}", engagement_agg.shape[1])
    return out_path


# ════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ════════════════════════════════════════════════════════════════════════

def run(data_dir: Path, output_dir: Path) -> pd.DataFrame:
    """Chay toan bo pipeline: load -> merge -> aggregate -> verify -> save."""
    log.info("====== build_engagement_features: bat dau ======")

    student_vle_df, vle_df = load_data(data_dir)
    merged_df = merge_vle(student_vle_df, vle_df)

    activity_counts = build_activity_counts(merged_df)
    agg_df = build_total_clicks_active_days(merged_df)
    engagement_agg = merge_aggregates(agg_df, activity_counts)

    ok = verify(student_vle_df, engagement_agg)
    if not ok:
        log.warning("Tiep tuc luu du lieu du khi kiem chung khong khop - vui long kiem tra lai.")

    save_output(engagement_agg, output_dir)

    log.info("====== build_engagement_features: hoan tat ======")
    return engagement_agg


# ════════════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════════════

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="OULAD - Tong hop dac trung engagement (VLE clickstream) cho moi sinh vien."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("../../data/raw"),
        help="Thu muc chua studentVle.csv va vle.csv (default: ../data/raw)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("../data/interim/cleaned"),
        help="Thu muc luu engagement_agg.parquet (default: ../data/interim/cleaned)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="In them thong tin debug",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.verbose:
        log.setLevel(logging.DEBUG)

    try:
        run(args.data_dir, args.output_dir)
    except FileNotFoundError as e:
        log.error("%s", e)
        return 1
    except Exception:
        log.exception("Pipeline that bai do loi khong mong doi:")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())