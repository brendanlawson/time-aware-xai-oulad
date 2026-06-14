"""Generate a complete bilingual data dictionary from the actual master table.

Reads data/interim/master_raw.parquet and emits, into docs/01_data_specification/,
Data_Dictionary_{EN,VI}.md and Data_Dictionary.xlsx covering 100% of the columns
(asserted). Deriving it from the real table keeps coverage in sync with the pipeline.

Run:  python tools/make_data_dictionary.py
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "data" / "interim" / "master_raw.parquet"

# col -> (group, type_en, type_vi, origin, desc_en, desc_vi)
DESC = {
    "code_module": (
        "Identifier",
        "Nominal (ID)",
        "Danh định (ID)",
        "Original",
        "Module code; part of the composite key.",
        "Mã môn học; thuộc khoá tổng hợp.",
    ),
    "code_presentation": (
        "Identifier",
        "Nominal (ID)",
        "Danh định (ID)",
        "Original",
        "Presentation code (B=Feb, J=Oct); part of the composite key.",
        "Mã kỳ học (B=tháng 2, J=tháng 10); thuộc khoá tổng hợp.",
    ),
    "id_student": (
        "Identifier",
        "Nominal (ID)",
        "Danh định (ID)",
        "Original",
        "Unique student id; the group key for GroupKFold (not a feature).",
        "Mã sinh viên duy nhất; khoá nhóm cho GroupKFold (không là đặc trưng).",
    ),
    "gender": (
        "Demographic",
        "Binary",
        "Nhị phân",
        "Original",
        "Gender; encoded M=1, F=0.",
        "Giới tính; mã hoá M=1, F=0.",
    ),
    "region": (
        "Demographic",
        "Nominal",
        "Danh định",
        "Original",
        "Region of the UK/Ireland (13 values); one-hot encoded.",
        "Vùng của Anh/Ireland (13 giá trị); mã hoá one-hot.",
    ),
    "highest_education": (
        "Demographic",
        "Ordinal",
        "Thứ bậc",
        "Original",
        "Highest education level; ordinal 0..4.",
        "Trình độ học vấn cao nhất; thứ bậc 0..4.",
    ),
    "imd_band": (
        "Demographic",
        "Ordinal",
        "Thứ bậc",
        "Original",
        "Index of Multiple Deprivation band; ordinal; 1,111 missing -> 'Unknown'.",
        "Chỉ số nghèo khó (IMD) theo vùng; thứ bậc; 1.111 khuyết -> 'Unknown'.",
    ),
    "age_band": (
        "Demographic",
        "Ordinal",
        "Thứ bậc",
        "Original",
        "Age band; ordinal 0..2.",
        "Nhóm tuổi; thứ bậc 0..2.",
    ),
    "num_of_prev_attempts": (
        "Demographic",
        "Numeric (discrete)",
        "Định lượng (rời rạc)",
        "Original",
        "Number of previous attempts at the module.",
        "Số lần học lại môn trước đó.",
    ),
    "studied_credits": (
        "Demographic",
        "Numeric (discrete)",
        "Định lượng (rời rạc)",
        "Original",
        "Total credits the student is studying.",
        "Tổng số tín chỉ đang học.",
    ),
    "disability": (
        "Demographic",
        "Binary",
        "Nhị phân",
        "Original",
        "Declared disability; encoded Y=1, N=0.",
        "Khai báo khuyết tật; mã hoá Y=1, N=0.",
    ),
    "final_result": (
        "Target (raw)",
        "Nominal (raw)",
        "Danh định (gốc)",
        "Original",
        "Raw outcome (Pass/Distinction/Fail/Withdrawn); source of the label.",
        "Kết quả gốc (Pass/Distinction/Fail/Withdrawn); nguồn của nhãn.",
    ),
    "at_risk": (
        "Target",
        "Binary (target)",
        "Nhị phân (mục tiêu)",
        "Derived",
        "1 if final_result in {Fail, Withdrawn}, else 0. Fixed across checkpoints.",
        "1 nếu final_result thuộc {Fail, Withdrawn}, ngược lại 0. Cố định qua các mốc.",
    ),
    "date_registration": (
        "Temporal",
        "Numeric (continuous)",
        "Định lượng (liên tục)",
        "Original",
        "Registration day relative to course start (can be negative); 45 missing -> train median.",
        "Ngày đăng ký tương đối so với ngày bắt đầu (có thể âm); 45 khuyết -> trung vị train.",
    ),
    "date_unregistration": (
        "Temporal",
        "Numeric (continuous)",
        "Định lượng (liên tục)",
        "Original",
        "Withdrawal day; NaN if not withdrawn. Used for Withdrawn analysis, not a feature.",
        "Ngày rút môn; NaN nếu không rút. Dùng để phân tích Withdrawn, không là đặc trưng.",
    ),
    "total_clicks": (
        "Engagement",
        "Numeric (continuous)",
        "Định lượng (liên tục)",
        "Derived",
        "Total VLE clicks up to the checkpoint; right-skewed -> log1p.",
        "Tổng lượt click VLE tới mốc; lệch phải -> log1p.",
    ),
    "n_days_active": (
        "Engagement",
        "Numeric (discrete)",
        "Định lượng (rời rạc)",
        "Derived",
        "Number of distinct active days up to the checkpoint.",
        "Số ngày có hoạt động (distinct) tới mốc.",
    ),
    "max_clicks_single_day": (
        "Engagement",
        "Numeric (continuous)",
        "Định lượng (liên tục)",
        "Derived",
        "Maximum clicks on any single day up to the checkpoint; strongly right-skewed -> log1p.",
        "Số click tối đa trong một ngày tới mốc; lệch phải mạnh -> log1p.",
    ),
    "clicks_forumng": (
        "Engagement",
        "Numeric (continuous)",
        "Định lượng (liên tục)",
        "Derived",
        "Clicks on 'forumng' activities up to the checkpoint.",
        "Click loại 'forumng' tới mốc.",
    ),
    "clicks_oucontent": (
        "Engagement",
        "Numeric (continuous)",
        "Định lượng (liên tục)",
        "Derived",
        "Clicks on 'oucontent' activities up to the checkpoint.",
        "Click loại 'oucontent' tới mốc.",
    ),
    "clicks_resource": (
        "Engagement",
        "Numeric (continuous)",
        "Định lượng (liên tục)",
        "Derived",
        "Clicks on 'resource' activities up to the checkpoint.",
        "Click loại 'resource' tới mốc.",
    ),
    "clicks_homepage": (
        "Engagement",
        "Numeric (continuous)",
        "Định lượng (liên tục)",
        "Derived",
        "Clicks on 'homepage' activities up to the checkpoint.",
        "Click loại 'homepage' tới mốc.",
    ),
    "clicks_oucollaborate": (
        "Engagement",
        "Numeric (continuous)",
        "Định lượng (liên tục)",
        "Derived",
        "Clicks on 'oucollaborate' activities up to the checkpoint.",
        "Click loại 'oucollaborate' tới mốc.",
    ),
    "clicks_quiz": (
        "Engagement",
        "Numeric (continuous)",
        "Định lượng (liên tục)",
        "Derived",
        "Clicks on 'quiz' activities up to the checkpoint.",
        "Click loại 'quiz' tới mốc.",
    ),
    "clicks_subpage": (
        "Engagement",
        "Numeric (continuous)",
        "Định lượng (liên tục)",
        "Derived",
        "Clicks on 'subpage' activities up to the checkpoint.",
        "Click loại 'subpage' tới mốc.",
    ),
    "clicks_url": (
        "Engagement",
        "Numeric (continuous)",
        "Định lượng (liên tục)",
        "Derived",
        "Clicks on 'url' activities up to the checkpoint.",
        "Click loại 'url' tới mốc.",
    ),
    "mean_clicks_per_active_day": (
        "Engagement",
        "Numeric (continuous)",
        "Định lượng (liên tục)",
        "Derived",
        "total_clicks / n_days_active (0 when no active day); right-skewed -> log1p.",
        "total_clicks / n_days_active (0 nếu không có ngày hoạt động); lệch phải -> log1p.",
    ),
    "days_since_last_activity": (
        "Engagement",
        "Numeric (continuous)",
        "Định lượng (liên tục)",
        "Derived",
        "Days from the last activity to the checkpoint day (large when disengaged).",
        "Số ngày từ lần hoạt động cuối tới ngày mốc (lớn khi mất tương tác).",
    ),
    "n_assessments_submitted": (
        "Performance",
        "Numeric (discrete)",
        "Định lượng (rời rạc)",
        "Derived",
        "Assessments submitted (not banked) up to the checkpoint.",
        "Số bài đánh giá đã nộp (không banked) tới mốc.",
    ),
    "mean_score_to_date": (
        "Performance",
        "Numeric (continuous)",
        "Định lượng (liên tục)",
        "Derived",
        "Mean score of submissions up to the checkpoint [0-100]; 0 if none.",
        "Điểm trung bình các bài đã nộp tới mốc [0-100]; 0 nếu chưa nộp.",
    ),
    "weighted_score_to_date": (
        "Performance",
        "Numeric (continuous)",
        "Định lượng (liên tục)",
        "Derived",
        "Sum of score x weight/100 of submissions up to the checkpoint.",
        "Tổng score x weight/100 các bài đã nộp tới mốc.",
    ),
    "not_submitted": (
        "Performance",
        "Binary (indicator)",
        "Nhị phân (chỉ báo)",
        "Derived",
        "1 if the student missed >=1 assessment whose deadline had passed; a risk signal.",
        "1 nếu sinh viên bỏ lỡ >=1 bài đã quá hạn nộp; tín hiệu nguy cơ.",
    ),
    "module_presentation_length": (
        "Temporal",
        "Numeric (discrete)",
        "Định lượng (rời rạc)",
        "Original",
        "Length of the module-presentation in days; used to convert checkpoints to days.",
        "Độ dài môn-kỳ tính bằng ngày; dùng để quy đổi mốc sang ngày.",
    ),
}

GROUP_ORDER = [
    "Identifier",
    "Demographic",
    "Engagement",
    "Performance",
    "Temporal",
    "Target (raw)",
    "Target",
]


def build(lang: str, master: pd.DataFrame) -> str:
    en = lang == "EN"
    title = (
        "# OULAD Master-Table Data Dictionary (complete)"
        if en
        else "# Từ điển dữ liệu bảng hợp nhất OULAD (đầy đủ)"
    )
    sub = (
        "*Covers 100% of the master_raw columns. Auto-generated from the master table.*"
        if en
        else "*Bao phủ 100% cột của master_raw. Tự sinh từ bảng hợp nhất.*"
    )
    meta = (
        "**DSP391m – Group 1 · Report 2 · STT 29 (An)**"
        if en
        else "**DSP391m – Nhóm 1 · Báo cáo 2 · STT 29 (An)**"
    )
    hdr = (
        "| # | Variable | Type | Origin | Description | Example / Range |"
        if en
        else "| # | Biến | Kiểu | Nguồn gốc | Mô tả | Ví dụ / Khoảng |"
    )
    sep = "|---|---|---|---|---|---|"

    lines = [
        title,
        "",
        sub,
        "",
        meta,
        "",
        f"Total variables: **{len(master.columns)}**"
        if en
        else f"Tổng số biến: **{len(master.columns)}**",
        "",
    ]
    n = 0
    for group in GROUP_ORDER:
        cols = [c for c in master.columns if DESC[c][0] == group]
        if not cols:
            continue
        lines += [f"## {group}", "", hdr, sep]
        for c in cols:
            n += 1
            g, ten, tvi, origin, den, dvi = DESC[c]
            s = master[c]
            if pd.api.types.is_numeric_dtype(s):
                ex = f"min {s.min():g}, max {s.max():g}"
            else:
                ex = f"{s.nunique(dropna=True)} unique"
            typ = ten if en else tvi
            desc = den if en else dvi
            lines.append(f"| {n} | `{c}` | {typ} | {origin} | {desc} | {ex} |")
        lines.append("")
    return "\n".join(lines)


def build_xlsx(master: pd.DataFrame, path: Path) -> None:
    rows = []
    for c in master.columns:
        g, ten, tvi, origin, den, dvi = DESC[c]
        s = master[c]
        ex = (
            f"min {s.min():g}, max {s.max():g}"
            if pd.api.types.is_numeric_dtype(s)
            else f"{s.nunique(dropna=True)} unique"
        )
        rows.append(
            {
                "variable": c,
                "group": g,
                "type_EN": ten,
                "type_VI": tvi,
                "origin": origin,
                "description_EN": den,
                "description_VI": dvi,
                "example_range": ex,
            }
        )
    pd.DataFrame(rows).to_excel(path, index=False, sheet_name="DataDictionary")


def main():
    master = pd.read_parquet(MASTER)
    uncovered = [c for c in master.columns if c not in DESC]
    assert not uncovered, f"Data dictionary missing columns: {uncovered}"
    out_dir = ROOT / "docs" / "01_data_specification"
    out_dir.mkdir(parents=True, exist_ok=True)
    for lang in ("EN", "VI"):
        out = out_dir / f"Data_Dictionary_{lang}.md"
        out.write_text(build(lang, master), encoding="utf-8")
        print("wrote", out, "covering", len(master.columns), "columns")
    build_xlsx(master, out_dir / "Data_Dictionary.xlsx")
    print("wrote", out_dir / "Data_Dictionary.xlsx")


if __name__ == "__main__":
    sys.exit(main())
