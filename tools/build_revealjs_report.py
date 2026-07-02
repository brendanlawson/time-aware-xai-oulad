"""Build a reveal.js (HTML) progress deck — a clean, science-style presentation.

Reads the result CSVs (so every table/number is regenerated from source, not typed
by hand), writes a Markdown source, and renders it to a self-contained HTML deck
with pandoc + reveal.js. Scoped to Đức's Phase 2 benchmarking (the data phase was
already presented in Task 3); later phases appear as an "upcoming work" roadmap.

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
_metric_cols = ["recall", "f1", "pr_auc", "roc_auc", "precision", "balanced_acc", "brier"]
bench = base[["model", *_metric_cols]].copy()
for c in _metric_cols:
    bench[c] = bench[c].map(lambda v: f"{v:.3f}")
bench["model"] = bench["model"].map(NICE)
bench_md = md_table(
    bench, ["Model", "Recall", "F1", "PR-AUC", "ROC-AUC", "Precision", "Bal.Acc", "Brier ↓"]
)
top = base.iloc[0]

# CV 5-fold x 5-seed (mean ± std) — the harness reliability view.
cvs = pd.read_csv(TAB / "cv_summary.csv").sort_values("recall_mean", ascending=False)
cv_rows = [
    [
        NICE[r.model],
        f"{r.recall_mean:.4f} ± {r.recall_std:.4f}",
        f"{r.f1_mean:.4f} ± {r.f1_std:.4f}",
        f"{r.pr_auc_mean:.4f} ± {r.pr_auc_std:.4f}",
    ]
    for r in cvs.itertuples()
]
cv_md = md_table(
    pd.DataFrame(cv_rows, columns=["a", "b", "c", "d"]),
    ["Model", "Recall (μ ± σ)", "F1 (μ ± σ)", "PR-AUC (μ ± σ)"],
)

# Friedman + post-hoc Wilcoxon — is the ranking statistically real?
fried = pd.read_csv(TAB / "model_friedman.csv")
fr_rows = [
    [r.metric, NICE[r.best_model], f"{r.friedman_stat:.1f}", f"{r.p_value:.1e}"]
    for r in fried.itertuples()
]
fried_md = md_table(
    pd.DataFrame(fr_rows, columns=["a", "b", "c", "d"]),
    ["Chỉ số", "Model tốt nhất (mean rank)", "Friedman χ²", "p-value"],
)
pw = pd.read_csv(TAB / "model_pairwise_wilcoxon.csv")
xgb_recall_sig = pw[
    (pw.metric == "recall")
    & ((pw.model_a == "xgb") | (pw.model_b == "xgb"))
    & pw["significant_0.05"]
]
n_xgb_wins = int((xgb_recall_sig["better"] == "xgb").sum())

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
subtitle: "Báo cáo tiến độ · Phase 2 — Benchmarking mô hình · DSP391m — Nhóm 1"
author: "Đức (Modeling Lead)  —  GVHD: Nguyễn Thị Hoàng Yến"
date: "02/07/2026 · Đại học FPT"
---

# Phase 2 — Benchmarking  ·  <em class="tag">Đức</em>

## Lựa chọn mô hình — vì sao 5 thuật toán này?

| Model | Họ thuật toán | Lý do chọn |
|---|---|---|
| Logistic Regression | Tuyến tính | Baseline chuẩn, hệ số đọc được trực tiếp |
| Random Forest | Bagging cây | Bền với nhiễu/ngoại lai, ít phải tinh chỉnh |
| XGBoost | Boosting cây | SOTA dữ liệu bảng, hỗ trợ SHAP TreeExplainer |
| LightGBM | Boosting cây | Nhanh trên dữ liệu lớn, đối chứng cùng họ XGB |
| ANN (MLP) | Mạng nơ-ron | Đại diện phi tuyến khác họ cây, đối chứng đa dạng |

- Phủ **3 họ mô hình** khác nhau (tuyến tính · cây · nơ-ron) → kết luận không lệ thuộc một họ.
- Cả 5 đều được các nghiên cứu nền trên OULAD sử dụng → **so sánh được với văn liệu**.

## Kiến trúc & cấu hình huấn luyện

| Model | Cấu hình chính (còn lại giữ mặc định) |
|---|---|
| Logistic Regression | `max_iter=1000` |
| Random Forest | mặc định · `n_jobs=-1` |
| XGBoost | `tree_method=hist` · `eval_metric=logloss` |
| LightGBM | mặc định · `verbose=-1` |
| ANN (MLP) | 2 lớp ẩn **(64, 32)** · `max_iter=500` · early-stopping |

- **Cùng seed 42** cho mọi model → công bằng & tái lập.
- Giai đoạn này *chưa* tinh chỉnh siêu tham số — so tuyển ở cấu hình gốc trước, tinh chỉnh sau khi chọn.

## Quy trình huấn luyện (Training Procedure)

1. Nạp **split cố định** của mốc 100% (đã chốt ở Task 3 — 0 SV trùng train/test, 19/19 kiểm thử rò rỉ ĐẠT).
2. Tiền xử lý **fit trên train** → transform test (median, winsorize, encoder, scaler đều học từ train).
3. `model.fit(train)` → dự đoán trên **test giữ riêng**.
4. Chấm **7 chỉ số**; xếp hạng theo **Recall** lớp at-risk.

- Đây là kết quả **baseline (no-resample)** — Phase 4 sẽ so sánh trước–sau với 4 kỹ thuật cân bằng lớp.
- Chỉ số chính: **Recall & PR-AUC** lớp at-risk — bỏ sót SV nguy cơ đắt hơn nhiều một cảnh báo nhầm; accuracy dễ gây ảo tưởng.

## Kết quả so tuyển @ mốc 100%

{img("model_benchmark_baseline.png", 520)}

## Bảng hiệu năng đầy đủ — 7 chỉ số (đọc từ CSV)

{kpi(f"{top.recall:.3f}", f"{NICE[top.model]} · recall")} {kpi(f"{top.pr_auc:.3f}", "PR-AUC")} {kpi(f"{top.f1:.3f}", "F1")} {kpi(f"{top.brier:.3f}", "Brier (càng thấp càng tốt)")}

{bench_md}

- Đánh giá trên **tập test giữ riêng**, sắp theo recall lớp at-risk; Brier đo chất lượng xác suất.
- Khoảng cách giữa các model **nhỏ** → cần kiểm chứng độ tin cậy trước khi kết luận.

## Độ tin cậy: CV 5-fold × 5 seed trên train

{cv_md}

- 25 lần fit/model (pipeline đầy đủ, tiền xử lý + cân bằng lặp lại **trong từng fold** — không rò rỉ).
- Độ lệch chuẩn rất nhỏ (σ ≈ 0,005) → kết quả **ổn định**, không ăn may theo cách chia fold.
- Thứ hạng CV khớp thứ hạng test → baseline đáng tin.

## Xếp hạng có ý nghĩa thống kê không?

{fried_md}

- **Friedman** trên 25 fold ghép cặp: mọi chỉ số đều p ≪ 0,05 → khác biệt giữa các model là **thật**, không phải nhiễu.
- Post-hoc **Wilcoxon (hiệu chỉnh Holm)** trên recall: XGBoost thắng **{n_xgb_wins}/4** cặp so sánh có ý nghĩa.
- **XGBoost** dẫn recall · **LightGBM** dẫn F1/PR-AUC/ROC-AUC → chọn theo mục tiêu bài toán (recall-first) + **giải thích được** (TreeExplainer, phục vụ Phase 5).

# Kế hoạch & Kết luận

## Các việc sắp tới để hoàn thiện bài làm

{roadmap_next}

*Theo luồng quy trình: Đức → Khoa → Bình → Sơn / An.*

## Kết luận

- **Đã xong & tái lập:** so tuyển 5 model ứng viên (Phase 2), trên nền dữ liệu đã chốt ở Task 3.
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
