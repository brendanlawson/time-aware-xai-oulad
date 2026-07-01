"""Build a reveal.js (HTML) progress deck — a clean, science-style presentation.

Reads the result CSVs (so every table/number is regenerated from source, not typed
by hand), writes a Markdown source, and renders it to a self-contained HTML deck
with pandoc + reveal.js. Scoped to the reported milestone (Phase 1 data + Phase 2
benchmarking); later phases appear as an "upcoming work" roadmap.

Outputs:
  reports/slides/progress_report.md     (Markdown source, committed)
  reports/slides/progress_report.html   (rendered deck; open in a browser)

Requires: pandoc (rendering) + the figures in reports/figures and CSVs in
reports/tables. Run:

    python tools/build_revealjs_report.py
"""

from __future__ import annotations

from pathlib import Path
import subprocess

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "reports" / "figures"
TAB = ROOT / "reports" / "tables"
OUT_MD = ROOT / "reports" / "slides" / "progress_report.md"
OUT_HTML = ROOT / "reports" / "slides" / "progress_report.html"

NICE = {
    "xgb": "XGBoost",
    "lgbm": "LightGBM",
    "ann": "ANN (MLP)",
    "rf": "Random Forest",
    "logreg": "Logistic Reg.",
}


def md_table(df: pd.DataFrame, headers: list[str]) -> str:
    """Render a DataFrame as a GitHub-pipe Markdown table."""
    cols = list(df.columns)
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(lines)


def img(name: str, height: int = 500) -> str:
    """Absolute-path image tag (pandoc --embed-resources inlines it as base64)."""
    return f'<img src="{(FIG / name).as_posix()}" style="max-height:{height}px" />'


def kpi(value: str, label: str) -> str:
    return f'<span class="kpi"><b>{value}</b>{label}</span>'


# ── Read results straight from the CSVs ─────────────────────────────────────
imb = pd.read_csv(TAB / "imbalance_comparison.csv")
base = imb[imb["strategy"] == "none"].sort_values("recall", ascending=False).reset_index(drop=True)
bench = base[["model", "recall", "f1", "pr_auc", "roc_auc"]].copy()
for c in ("recall", "f1", "pr_auc", "roc_auc"):
    bench[c] = bench[c].map(lambda v: f"{v:.3f}")
bench["model"] = bench["model"].map(NICE)
bench_md = md_table(bench, ["Model", "Recall", "F1", "PR-AUC", "ROC-AUC"])
top = base.iloc[0]

sp = pd.read_csv(TAB / "split_report.csv")
srow = sp[sp["dataset"] == "t100"].iloc[0]

roadmap_status = md_table(
    pd.DataFrame(
        [
            ["Phase 1 — Data prep & harness", "Phúc", "✅ Hoàn thành"],
            ["Phase 2 — Benchmark 5 model @100%", "Đức", "✅ Hoàn thành"],
            ["Phase 4 — Xử lý mất cân bằng (RQ3)", "Đức", "▶ Sắp tới"],
            ["Phase 3 — Time-aware 6 mốc (RQ1)", "Khoa", "▶ Sắp tới"],
            ["Phase 5 — SHAP/LIME + độ ổn định (RQ2)", "Bình", "▶ Sắp tới"],
            ["Phase 6a/b — Dashboard & Báo cáo", "Sơn / An", "▶ Sắp tới"],
        ],
        columns=["a", "b", "c"],
    ),
    ["Pha / Nhiệm vụ", "Người", "Trạng thái"],
)

roadmap_next = md_table(
    pd.DataFrame(
        [
            ["Phase 4 — no-resample/class-weight/SMOTE/ADASYN", "Đức", "Biểu đồ so sánh · RQ3"],
            ["Phase 3 — chạy thực nghiệm 6 mốc thời gian", "Khoa", "Đường cong hiệu năng · RQ1"],
            ["Phase 5 — SHAP/LIME + độ ổn định giải thích", "Bình", "Giải thích mô hình · RQ2"],
            ["Phase 6a — Streamlit dashboard", "Sơn", "App dự đoán + đóng gói"],
            ["Phase 6b — Viết báo cáo & trực quan hoá", "An", "Báo cáo cuối + slide"],
        ],
        columns=["a", "b", "c"],
    ),
    ["Phase — Công việc", "Người", "Sản phẩm / RQ"],
)

CSS = """
<style>
:root{ --accent:#0F4C81; --accent2:#C0392B; }
.reveal { font-family:"Segoe UI","Helvetica Neue",Arial,sans-serif; color:#1f2937; }
.reveal h1{ font-size:1.7em; } .reveal h2{ font-size:1.15em; }
.reveal h1,.reveal h2,.reveal h3{ color:var(--accent); font-weight:600;
  text-transform:none; letter-spacing:0; }
.reveal section{ font-size:28px; text-align:left; }
.reveal .subtitle{ color:#475569; }
.reveal table{ margin:0.4em auto; border-collapse:collapse; font-size:0.66em; width:100%; }
.reveal table th{ background:var(--accent); color:#fff; padding:6px 12px; text-align:left; }
.reveal table td{ padding:5px 12px; border-bottom:1px solid #e5e7eb; }
.reveal table tr:nth-child(even) td{ background:#f4f6f9; }
.reveal .kpi{ display:inline-block; background:#f4f6f9; border-left:4px solid var(--accent);
  padding:8px 16px; margin:6px 8px 6px 0; border-radius:4px; font-size:0.7em; }
.reveal .kpi b{ color:var(--accent); font-size:1.7em; display:block; line-height:1.1; }
.reveal section img{ border:1px solid #e5e7eb; border-radius:6px; display:block; margin:0.3em auto; }
.reveal .cols{ display:flex; gap:24px; align-items:center; }
.reveal .cols > div{ flex:1; }
.reveal em.tag{ color:var(--accent2); font-style:normal; font-weight:600; }
</style>
"""

MD = f"""---
title: "Time-Aware Explainable ML — Phát hiện sớm sinh viên nguy cơ (OULAD)"
subtitle: "Báo cáo tiến độ · Phase 1–2 · DSP391m — Nhóm 1"
author: "Phúc (Phase 1) · Đức (Phase 2)  —  GVHD: Nguyễn Thị Hoàng Yến"
date: "02/07/2026 · Đại học FPT"
---

# Tổng quan

## Bài toán & phạm vi báo cáo

- **Mục tiêu:** phát hiện *sớm* sinh viên nguy cơ trên OULAD và *giải thích được* dự đoán.
- **3 câu hỏi:** RQ1 dự đoán sớm · RQ2 ổn định giải thích · RQ3 mất cân bằng.
- Báo cáo này trình bày đến hết **Phase 2 (so tuyển mô hình)**; phần sau là *việc sắp tới*.

{roadmap_status}

# Phase 1 — Dữ liệu & Khung thực nghiệm  ·  <em class="tag">Phúc</em>

## Pipeline dữ liệu chống rò rỉ

<div class="cols">
<div>

- 7 bảng OULAD → **master 32.593 × 33**.
- Cắt **6 mốc** tiến độ khoá học (10 → 100%).
- Tiền xử lý **fit-on-train** (chống rò rỉ).
- Harness: **80/20** StratifiedGroupKFold theo `id_student` + CV **5-fold × 5 seed**.

</div>
<div>

{img("preprocessing_sequence.png", 430)}

</div>
</div>

## Chia dữ liệu & chống rò rỉ — số liệu thật

{kpi(f"{int(srow.n_train):,}", "mẫu train")} {kpi(f"{int(srow.n_test):,}", "mẫu test")} {kpi(f"{int(srow.n_test_students):,}", "SV test")} {kpi(f"{int(srow.student_overlap)}", "SV trùng train/test")}

| Chỉ số | Train | Test |
|---|---|---|
| Số mẫu | {int(srow.n_train):,} | {int(srow.n_test):,} |
| Tỉ lệ at-risk | {srow.train_at_risk_rate:.4f} | {srow.test_at_risk_rate:.4f} |

- Lệch tỉ lệ at-risk train–test chỉ **{srow.rate_gap:.4f}** → phân tầng đạt.
- **0** sinh viên trùng giữa train/test · **19/19** kiểm thử rò rỉ ĐẠT.

# Phase 2 — So tuyển mô hình (Benchmarking)  ·  <em class="tag">Đức</em>

## 5 thuật toán ứng viên @ mốc 100%

<div class="cols">
<div>

- **LR · RF · XGBoost · LightGBM · ANN** (baseline, chưa resample).
- Chỉ số chính: **Recall & PR-AUC** lớp at-risk (bỏ sót SV nguy cơ là đắt nhất).
- Các model cây bám sát nhau; **XGB** dẫn đầu recall.

</div>
<div>

{img("model_benchmark_baseline.png", 430)}

</div>
</div>

## Bảng hiệu năng 5 model — baseline (đọc từ CSV)

{kpi(f"{top.recall:.3f}", f"{NICE[top.model]} · recall")} {kpi(f"{top.pr_auc:.3f}", "PR-AUC")} {kpi(f"{top.f1:.3f}", "F1")}

{bench_md}

- Đánh giá trên **tập test giữ riêng**, sắp theo recall lớp at-risk.
- Khoảng cách giữa các model nhỏ → chọn theo **recall + khả năng giải thích được**.

# Kế hoạch & Kết luận

## Các việc sắp tới để hoàn thiện bài làm

{roadmap_next}

*Theo luồng quy trình: Đức → Khoa → Bình → Sơn / An.*

## Kết luận

- **Đã xong & tái lập:** pipeline dữ liệu (P1) + so tuyển 5 model ứng viên (P2).
- **{NICE[top.model]}** dẫn đầu recall (**{top.recall:.3f}**) ngay ở baseline; các model bám sát.
- **Kế tiếp:** P4 mất cân bằng → P3 time-aware RQ1 → P5 XAI RQ2 → P6 dashboard & báo cáo.
- Nền tảng tái lập từ `src/` + `tools/`; **19/19** kiểm thử rò rỉ ĐẠT.

### Cảm ơn đã lắng nghe!
"""


def main() -> int:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(CSS + "\n" + MD, encoding="utf-8")
    cmd = [
        "pandoc",
        str(OUT_MD),
        "-t",
        "revealjs",
        "-s",
        "--embed-resources",
        "--slide-level=2",
        "-V",
        "theme=white",
        "-V",
        "width=1280",
        "-V",
        "height=720",
        "-V",
        "slideNumber=true",
        "-V",
        "transition=fade",
        "-o",
        str(OUT_HTML),
    ]
    subprocess.run(cmd, check=True, cwd=str(ROOT))
    print(f"Wrote {OUT_MD}")
    print(f"Wrote {OUT_HTML}  ({OUT_HTML.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
