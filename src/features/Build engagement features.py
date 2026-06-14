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
    """
    Doc studentVle.csv va vle.csv tu data_dir.

    Quan trong - vi sao KHONG doc truc tiep voi dtype='category'
    --------------------------------------------------------------
    Pandas' C parser (_categorical_convert) phai xay dung bang hash
    category NGAY TRONG LUC PARSE FILE. Voi file lon (~10.6 trieu dong)
    tren may co RAM rat han che, buoc nay co the bao loi
    ArrayMemoryError ngay ca khi chi can cap phat 1 MiB - vi tai thoi
    diem do RAM da gan can kiet boi cac buffer parser khac.

    Chunking voi dtype='category' con te hon: moi chunk tu xay dung
    bang category RIENG, sau do pd.concat() phai HOA HOP cac bang
    category khac nhau giua cac chunk -> spike bo nho them lan nua.

    Cach lam an toan hon
    --------------------
    1. Doc CSV o dang dtype don gian (int32 cho so, string cho text),
       KHONG dung category trong luc parse.
    2. Dung chunksize de gioi han bo nho dinh (peak memory) trong
       luc doc, nhung KHONG dung category cho tung chunk.
    3. Sau khi da co DataFrame day du (object/string), MOI chuyen
       code_module/code_presentation sang 'category' MOT LAN
       (astype sau khi du lieu da nam san trong RAM re hon nhieu
       so voi categorical hoa trong luc parse).

    Neu van loi ArrayMemoryError o buoc nay
    -----------------------------------------
    -> RAM kha dung qua thap so voi kich thuoc file (vai tram MB).
       Can xem lai cac chuong trinh khac dang chiem RAM, hoac doc
       tung phan (theo code_module) va xu ly rieng tung phan
       (xem ham load_data_by_module o cuoi file).
    """
    student_vle_path = data_dir / "studentVle.csv"
    vle_path = data_dir / "vle.csv"

    for p in (student_vle_path, vle_path):
        if not p.exists():
            raise FileNotFoundError(f"Khong tim thay file: {p}")

    # KHONG dung 'category' trong dtype luc doc - chi dung kieu so
    # don gian. code_module/code_presentation doc nhu string thuong.
    student_vle_dtypes = {
        "code_module": "string",
        "code_presentation": "string",
        "id_student": "int32",
        "id_site": "int32",
        "date": "int32",
        "sum_click": "int32",
    }

    log.info("Doc %s (chunksize=500_000, khong dung category luc parse)", student_vle_path)

    chunks = []
    for i, chunk in enumerate(
        pd.read_csv(student_vle_path, dtype=student_vle_dtypes, chunksize=500_000)
    ):
        chunks.append(chunk)
        log.debug("  da doc chunk %d (%s dong)", i + 1, f"{len(chunk):,}")

    student_vle_df = pd.concat(chunks, ignore_index=True)
    del chunks  # giai phong ngay danh sach chunk trung gian

    # Chuyen sang category SAU KHI da co DataFrame day du trong RAM -
    # an toan hon nhieu so voi categorical hoa trong luc parse CSV.
    student_vle_df["code_module"] = student_vle_df["code_module"].astype("category")
    student_vle_df["code_presentation"] = student_vle_df["code_presentation"].astype("category")

    log.info("Doc %s", vle_path)
    vle_df = pd.read_csv(vle_path)

    log.info(
        "studentVle.csv: %s dong | vle.csv: %s dong",
        f"{len(student_vle_df):,}", f"{len(vle_df):,}",
    )
    log.info(
        "Memory usage studentVle_df: %.1f MB",
        student_vle_df.memory_usage(deep=True).sum() / 1e6,
    )
    return student_vle_df, vle_df


def load_data_by_module(data_dir: Path):
    """
    Phuong an du phong (KHONG goi mac dinh): neu load_data() van
    bao ArrayMemoryError do RAM may qua thap, co the doc va xu ly
    studentVle.csv THEO TUNG code_module rieng le, ghi engagement_agg
    cho moi module ra file tam, sau do gop lai bang concat cac
    file parquet nho.

    Day la generator: yield (code_module, student_vle_chunk_df)
    de ham run() ben ngoai co the xu ly tung module mot va giai
    phong bo nho giua cac lan.

    Vi du su dung
    -------------
        for module, chunk_df in load_data_by_module(data_dir):
            merged = merge_vle(chunk_df, vle_df)
            ... build_activity_counts, build_total_clicks_active_days ...
            engagement_agg_module.to_parquet(f"engagement_agg_{module}.parquet")

    Sau do gop tat ca engagement_agg_<module>.parquet bang
    pd.concat() (file parquet rieng le rat nho, an toan de gop).
    """
    student_vle_path = data_dir / "studentVle.csv"

    student_vle_dtypes = {
        "code_module": "string",
        "code_presentation": "string",
        "id_student": "int32",
        "id_site": "int32",
        "date": "int32",
        "sum_click": "int32",
    }

    # Lay danh sach code_module duy nhat bang cach doc rieng cot nay
    modules = pd.read_csv(
        student_vle_path, usecols=["code_module"], dtype={"code_module": "string"}
    )["code_module"].unique()

    for module in sorted(modules):
        chunks = []
        for chunk in pd.read_csv(
            student_vle_path, dtype=student_vle_dtypes, chunksize=500_000
        ):
            chunks.append(chunk[chunk["code_module"] == module])
        module_df = pd.concat(chunks, ignore_index=True)
        yield module, module_df


# ════════════════════════════════════════════════════════════════════════
# 2. MERGE studentVle WITH vle (lay activity_type)
# ════════════════════════════════════════════════════════════════════════

def merge_vle(student_vle_df: pd.DataFrame, vle_df: pd.DataFrame) -> pd.DataFrame:
    """
    Gop studentVle voi vle de co cot activity_type cho moi luot click.

    Luu y ve hieu nang / bo nho
    ---------------------------
    studentVle.csv co ~10.6 trieu dong. pd.merge() tren key gom 3 cot
    (code_module, code_presentation, id_site) yeu cau pandas tinh toan
    join-index bang cach nhan cac ma factorize cua tung cot - voi du lieu
    lon, mang trung gian nay co the gay ArrayMemoryError tren may co RAM
    han che.

    Thay vi merge, ta:
      1. id_site la khoa duy nhat tren toan bo OULAD -> tao Series tra cuu
         id_site -> activity_type tu vle_df (chi 6,364 dong - rat nho).
      2. Dung Series.map() (vectorized, khong tao join-index O(n*k)) de
         gan activity_type truc tiep vao student_vle_df.

    Cach nay giam dang ke peak memory vi khong tao ban sao merge day du
    voi cac cot trung lap cua vle_df.
    """
    site_to_activity = vle_df.set_index("id_site")["activity_type"]

    merged_df = student_vle_df.copy()
    merged_df["activity_type"] = merged_df["id_site"].map(site_to_activity)

    n_missing_type = merged_df["activity_type"].isnull().sum()
    if n_missing_type:
        log.warning(
            "%s dong khong khop activity_type (id_site khong co trong vle.csv)",
            f"{n_missing_type:,}",
        )

    # Giam bo nho: chuyen cac cot phan loai / so nguyen ve kieu nho hon
    for col in ("code_module", "code_presentation", "activity_type"):
        if col in merged_df.columns:
            merged_df[col] = merged_df[col].astype("category")
    for col in ("id_student", "id_site", "date", "sum_click"):
        if col in merged_df.columns:
            merged_df[col] = pd.to_numeric(merged_df[col], downcast="integer")

    log.info("Merged shape: %s", merged_df.shape)
    log.info(
        "Memory usage sau merge: %.1f MB",
        merged_df.memory_usage(deep=True).sum() / 1e6,
    )
    return merged_df


# ════════════════════════════════════════════════════════════════════════
# 3. AGGREGATE — activity_type counts (pivot)
# ════════════════════════════════════════════════════════════════════════

def build_activity_counts(merged_df: pd.DataFrame) -> pd.DataFrame:
    """
    Voi moi (code_module, code_presentation, id_student), tinh so luot
    click theo tung activity_type -> cot dat ten <activity_type>_count.

    Luu y ve hieu nang / bo nho
    ---------------------------
    pd.pivot_table() voi index/columns la kieu category co the tao ra
    "cross-product" cua TAT CA gia tri category (ke ca khong xuat hien
    trong du lieu), lam DataFrame trung gian phinh to bat thuong voi
    10.6 trieu dong.

    Thay vao do, dung groupby(..., observed=True).size().unstack():
    - observed=True chi giu cac to hop thuc su xuat hien trong du lieu.
    - .size() dem so dong (tuong duong aggfunc='count' tren sum_click,
      vi moi dong la 1 ban ghi click-log).
    """
    counts = (
        merged_df.groupby(GROUP_COLS + ["activity_type"], observed=True)
        .size()
        .unstack(fill_value=0)
    )
    activity_counts = counts.reset_index()

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

    # Duong dan mac dinh tinh theo vi tri file script (.py), khong phu
    # thuoc vao cwd luc chay python. Gia su cau truc:
    #   <PROJECT_ROOT>/src/features/build_engagement_features.py
    #   <PROJECT_ROOT>/data/raw/...
    #   <PROJECT_ROOT>/data/interim/cleaned/...
    # => tu SCRIPT_DIR (src/features) di len 2 cap la PROJECT_ROOT.
    SCRIPT_DIR = Path(__file__).parent.resolve()
    PROJECT_ROOT = SCRIPT_DIR.parent.parent

    parser.add_argument(
        "--data-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "raw",
        help="Thu muc chua studentVle.csv va vle.csv (default: <project_root>/data/raw)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "interim" / "cleaned",
        help="Thu muc luu engagement_agg.parquet (default: <project_root>/data/interim/cleaned)",
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