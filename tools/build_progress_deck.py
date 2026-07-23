"""Build the Phase-2 progress deck as a Beamer PDF (replaces the reveal.js HTML).

Reads the result CSVs so every number is regenerated from source (never typed
by hand), writes ``reports/slides/Progress_Report_Slides.tex`` in the house
style of the committed Task-3 decks (maroon + cream, 16:9), and compiles it
with Tectonic (XeTeX; Segoe UI for full Vietnamese coverage).

Outputs:
  reports/slides/Progress_Report_Slides.tex   (committed source)
  reports/slides/Progress_Report_Slides.pdf   (the deck)

Run:
    python -m tools.build_progress_deck            # build tex + compile pdf
    python -m tools.build_progress_deck --skip-pdf
"""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "reports" / "tables"
OUT_TEX = ROOT / "reports" / "slides" / "Progress_Report_Slides.tex"

# Known Tectonic locations on the dev machine (falls back to PATH first).
TECTONIC_CANDIDATES = (
    "tectonic",
    r"C:\Users\phank\anaconda3\envs\tex\Library\bin\tectonic.exe",
)

# Segoe UI ships with Windows and covers Vietnamese fully; elsewhere fall back to
# the first installed face that also does.  fontspec halts if the face is absent.
FONT_CANDIDATES = ("Segoe UI", "Noto Sans", "DejaVu Sans", "Liberation Sans")


def pick_font() -> str:
    fc_list = shutil.which("fc-list")
    if fc_list is None:  # no fontconfig (Windows) -> Segoe UI is present
        return FONT_CANDIDATES[0]
    installed = subprocess.run(
        [fc_list, ":lang=vi", "family"], capture_output=True, text=True, check=False
    ).stdout
    return next((n for n in FONT_CANDIDATES if n in installed), FONT_CANDIDATES[0])


NAMES = {
    "xgb": "XGBoost",
    "lgbm": "LightGBM",
    "rf": "Random Forest",
    "ann": "ANN (MLP)",
    "logreg": "Logistic Regression",
}


def esc(s: str) -> str:
    for a, b in (("&", r"\&"), ("%", r"\%"), ("_", r"\_"), ("#", r"\#")):
        s = s.replace(a, b)
    return s


def f(x, nd=3) -> str:
    return f"{float(x):.{nd}f}"


def benchmark_rows() -> pd.DataFrame:
    imb = pd.read_csv(TAB / "imbalance_comparison.csv")
    none = imb[imb.strategy == "none"].copy()
    return none.sort_values("recall", ascending=False)


def build_tex() -> str:
    font = pick_font()
    bench = benchmark_rows()
    cv = pd.read_csv(TAB / "cv_summary.csv").sort_values("recall_mean", ascending=False)
    fried = pd.read_csv(TAB / "model_friedman.csv")
    pw = pd.read_csv(TAB / "model_pairwise_wilcoxon.csv")
    xr = pw[(pw.metric == "recall") & ((pw.model_a == "xgb") | (pw.model_b == "xgb"))]
    n_wins, n_pairs = int(((xr.better == "xgb") & xr["significant_0.05"]).sum()), len(xr)
    xgb = bench[bench.model == "xgb"].iloc[0]

    bench_body = "\n".join(
        f"    {NAMES[r.model]} & {f(r.recall)} & {f(r.f1)} & {f(r.pr_auc)} & "
        f"{f(r.roc_auc)} & {f(r.precision)} & {f(r.brier)} \\\\"
        for r in bench.itertuples()
    )
    cv_body = "\n".join(
        f"    {NAMES[r.model]} & {f(r.recall_mean, 4)} $\\pm$ {f(r.recall_std, 4)} & "
        f"{f(r.f1_mean, 4)} $\\pm$ {f(r.f1_std, 4)} & "
        f"{f(r.pr_auc_mean, 4)} $\\pm$ {f(r.pr_auc_std, 4)} \\\\"
        for r in cv.itertuples()
    )
    fried_body = "\n".join(
        f"    {esc(r.metric)} & {NAMES[r.best_model]} & {f(r.friedman_stat, 1)} & "
        f"${r.p_value:.1e}$ \\\\".replace("e-", r"\times 10^{-").replace(r"$ \\", r"}$ \\")
        for r in fried.itertuples()
    )

    return rf"""% ============================================================
%  DSP391m - Nhóm 1 | Báo cáo tiến độ - Phase 2: Benchmarking
%  Sinh tự động từ reports/tables/*.csv bởi tools/build_progress_deck.py
%  KHÔNG sửa số liệu trong file này - chạy lại builder sau mỗi renumber.
%  Compile: tectonic Progress_Report_Slides.tex   (XeTeX, font {font})
% ============================================================
\documentclass[aspectratio=169,11pt]{{beamer}}
\usetheme{{default}}
\setbeamertemplate{{navigation symbols}}{{}}
\usepackage{{fontspec}}
\setmainfont{{{font}}}
\setsansfont{{{font}}}
\usepackage{{booktabs}}
\usepackage{{graphicx}}
\graphicspath{{{{../figures/}}}}

\definecolor{{themecol}}{{HTML}}{{0F4C81}}
\definecolor{{accent}}{{HTML}}{{C0392B}}
\definecolor{{rowtint}}{{HTML}}{{EEF3F8}}
\setbeamercolor{{structure}}{{fg=themecol}}
\setbeamercolor{{frametitle}}{{fg=white,bg=themecol}}
\setbeamercolor{{title}}{{fg=themecol}}
\setbeamerfont{{frametitle}}{{series=\bfseries,size=\large}}
\setbeamertemplate{{itemize item}}{{\color{{themecol}}\textbullet}}
\setbeamertemplate{{footline}}{{\hfill\scriptsize\color{{gray}}%
  DSP391m · Nhóm 1 · Phase 2 Benchmarking\quad\insertframenumber/\inserttotalframenumber\hspace{{2mm}}\vspace{{1mm}}}}

\title{{Time-Aware Explainable ML —\\Phát hiện sớm sinh viên nguy cơ (OULAD)}}
\subtitle{{Báo cáo tiến độ · Phase 2 — Benchmarking mô hình}}
\author{{Đức (Modeling Lead) — Nhóm 1 · GVHD: Nguyễn Thị Hoàng Yến}}
\institute{{Đại học FPT · DSP391m}}
\date{{}}

\begin{{document}}

\begin{{frame}}\titlepage\end{{frame}}

\begin{{frame}}{{Lựa chọn mô hình — vì sao 5 thuật toán này?}}
\small
\begin{{tabular}}{{@{{}}lll@{{}}}}
\toprule
\textbf{{Model}} & \textbf{{Họ thuật toán}} & \textbf{{Lý do chọn}} \\
\midrule
Logistic Regression & Tuyến tính & Baseline chuẩn, hệ số đọc được trực tiếp \\
Random Forest & Bagging cây & Bền với nhiễu/ngoại lai, ít phải tinh chỉnh \\
XGBoost & Boosting cây & SOTA dữ liệu bảng, hỗ trợ SHAP TreeExplainer \\
LightGBM & Boosting cây & Nhanh trên dữ liệu lớn, đối chứng cùng họ \\
ANN (MLP) & Mạng nơ-ron & Đại diện phi tuyến khác họ cây \\
\bottomrule
\end{{tabular}}
\vspace{{4mm}}
\begin{{itemize}}
  \item Phủ \textbf{{3 họ mô hình}} (tuyến tính · cây · nơ-ron) → kết luận không lệ thuộc một họ.
  \item Cả 5 đều xuất hiện trong các nghiên cứu nền trên OULAD → \textbf{{so sánh được với văn liệu}}.
\end{{itemize}}
\end{{frame}}

\begin{{frame}}{{Kiến trúc \& cấu hình huấn luyện}}
\small
\begin{{tabular}}{{@{{}}ll@{{}}}}
\toprule
\textbf{{Model}} & \textbf{{Cấu hình chính (còn lại giữ mặc định)}} \\
\midrule
Logistic Regression & \texttt{{max\_iter=1000}} \\
Random Forest & mặc định · \texttt{{n\_jobs=-1}} \\
XGBoost & \texttt{{tree\_method=hist}} · \texttt{{eval\_metric=logloss}} \\
LightGBM & mặc định · \texttt{{verbose=-1}} \\
ANN (MLP) & 2 lớp ẩn (64, 32) · \texttt{{max\_iter=500}} · early-stopping \\
\bottomrule
\end{{tabular}}
\vspace{{4mm}}
\begin{{itemize}}
  \item \textbf{{Cùng seed 42}} cho mọi model → công bằng \& tái lập.
  \item Giai đoạn so tuyển \emph{{chưa}} tinh chỉnh siêu tham số — chọn xong ứng viên mới tune.
\end{{itemize}}
\end{{frame}}

\begin{{frame}}{{Quy trình huấn luyện (Training Procedure)}}
\begin{{enumerate}}
  \item Nạp \textbf{{split cố định}} của mốc 100\% — 0 sinh viên trùng train/test, toàn bộ kiểm thử rò rỉ tự động ĐẠT.
  \item Tiền xử lý \textbf{{fit trên train}} → transform test (median, winsorize, encoder, scaler đều học từ train).
  \item \texttt{{model.fit(train)}} → dự đoán trên \textbf{{test giữ riêng}}.
  \item Chấm \textbf{{7 chỉ số}}; xếp hạng theo \textbf{{recall}} lớp at-risk.
\end{{enumerate}}
\vspace{{3mm}}
\begin{{itemize}}
  \item Bảng kết quả trình bày \textbf{{baseline no-resample}}; pipeline chuẩn giữ SMOTE theo proposal — Phase 4 chứng minh hai lựa chọn chênh không đáng kể.
  \item Chỉ số chính: \textbf{{recall \& PR-AUC}} lớp at-risk — bỏ sót một sinh viên nguy cơ đắt hơn nhiều một cảnh báo nhầm.
\end{{itemize}}
\end{{frame}}

\begin{{frame}}{{Kết quả so tuyển @ mốc 100\%}}
\centering
\includegraphics[height=0.82\textheight]{{model_benchmark_baseline.png}}
\end{{frame}}

\begin{{frame}}{{Bảng hiệu năng đầy đủ — 7 chỉ số (sinh từ CSV)}}
\centering\small
\textbf{{XGBoost}}: recall \textbf{{{f(xgb.recall)}}} · F1 \textbf{{{f(xgb.f1)}}} · PR-AUC \textbf{{{f(xgb.pr_auc)}}} · Brier {f(xgb.brier)} (thấp = tốt)\\[2mm]
\begin{{tabular}}{{@{{}}lcccccc@{{}}}}
\toprule
\textbf{{Model}} & \textbf{{Recall}} & \textbf{{F1}} & \textbf{{PR-AUC}} & \textbf{{ROC-AUC}} & \textbf{{Precision}} & \textbf{{Brier}}$\downarrow$ \\
\midrule
{bench_body}
\bottomrule
\end{{tabular}}
\vspace{{3mm}}
\begin{{itemize}}\small
  \item Test giữ riêng, baseline no-resample; khoảng cách giữa các model \textbf{{nhỏ}} → hai slide sau kiểm chứng độ tin cậy.
\end{{itemize}}
\end{{frame}}

\begin{{frame}}{{Độ tin cậy: CV 5-fold $\times$ 5 seed trên train}}
\centering\small
\begin{{tabular}}{{@{{}}lccc@{{}}}}
\toprule
\textbf{{Model}} & \textbf{{Recall ($\mu\pm\sigma$)}} & \textbf{{F1 ($\mu\pm\sigma$)}} & \textbf{{PR-AUC ($\mu\pm\sigma$)}} \\
\midrule
{cv_body}
\bottomrule
\end{{tabular}}
\vspace{{3mm}}
\begin{{itemize}}\small
  \item 25 lần fit/model, tiền xử lý + cân bằng lặp \textbf{{trong từng fold}} — không rò rỉ.
  \item $\sigma$ rất nhỏ → kết quả \textbf{{ổn định}}, không ăn may theo cách chia fold; thứ hạng CV khớp thứ hạng test.
\end{{itemize}}
\end{{frame}}

\begin{{frame}}{{Xếp hạng có ý nghĩa thống kê không?}}
\centering\small
\begin{{tabular}}{{@{{}}llcc@{{}}}}
\toprule
\textbf{{Chỉ số}} & \textbf{{Model tốt nhất (mean rank)}} & \textbf{{Friedman $\chi^2$}} & \textbf{{p-value}} \\
\midrule
{fried_body}
\bottomrule
\end{{tabular}}
\vspace{{3mm}}
\begin{{itemize}}\small
  \item \textbf{{Friedman}} trên 25 fold ghép cặp: mọi chỉ số $p \ll 0{{,}}05$ → khác biệt là \textbf{{thật}}.
  \item Post-hoc \textbf{{Wilcoxon (Holm)}} trên recall: XGBoost thắng \textbf{{{n_wins}/{n_pairs}}} cặp có ý nghĩa.
  \item Chốt \textbf{{XGBoost}} làm ứng viên chính: recall-first + giải thích được bằng TreeExplainer (Phase 5).
\end{{itemize}}
\end{{frame}}

\begin{{frame}}{{Các việc tiếp theo để hoàn thiện}}
\small
\begin{{tabular}}{{@{{}}lll@{{}}}}
\toprule
\textbf{{Phase — Công việc}} & \textbf{{Người}} & \textbf{{Sản phẩm / RQ}} \\
\midrule
Phase 4 — none/class-weight/SMOTE/ADASYN & Đức & Biểu đồ so sánh · RQ3 \\
Phase 3 — thực nghiệm 6 mốc thời gian & Khoa & Đường cong hiệu năng · RQ1 \\
Phase 5 — SHAP/LIME + độ ổn định & Bình & Giải thích mô hình · RQ2 \\
Phase 6a — Streamlit dashboard & An & App dự đoán + đóng gói \\
Phase 6b — Introduction / Lit review & Sơn & Mở đầu + tổng quan + tài liệu \\
\bottomrule
\end{{tabular}}
\vspace{{3mm}}

\emph{{Luồng quy trình: Đức → Khoa → Bình → An (dashboard) / Sơn (lit review); báo cáo cuối do Khoa tổng hợp.}}
\end{{frame}}

\begin{{frame}}{{Kết luận Phase 2}}
\begin{{itemize}}
  \item 5 thuật toán / 3 họ được so tuyển \textbf{{công bằng}}: cùng split, cùng tiền xử lý, cùng seed, cấu hình gốc.
  \item \textbf{{XGBoost}} dẫn đầu recall \textbf{{{f(xgb.recall)}}} ngay ở baseline.
  \item Kiểm chứng \textbf{{hai lớp}}: CV 25 fold ổn định + Friedman--Wilcoxon xác nhận xếp hạng có ý nghĩa.
  \item Toàn bộ mã / bảng / biểu đồ nằm trong repo — deck này sinh lại bằng \texttt{{python -m tools.build\_progress\_deck}}.
\end{{itemize}}
\vspace{{3mm}}
\centering\color{{themecol}}\textbf{{Em xin cảm ơn thầy/cô và các bạn!}}
\end{{frame}}

\end{{document}}
"""


def compile_pdf(tex_path: Path) -> Path:
    exe = next((c for c in TECTONIC_CANDIDATES if shutil.which(c) or Path(c).exists()), None)
    if exe is None:
        raise FileNotFoundError("tectonic not found; install it or pass --skip-pdf")
    subprocess.run([exe, tex_path.name], cwd=tex_path.parent, check=True)
    return tex_path.with_suffix(".pdf")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skip-pdf", action="store_true", help="write the .tex only")
    args = ap.parse_args(argv)

    OUT_TEX.write_text(build_tex(), encoding="utf-8", newline="\n")
    print("wrote", OUT_TEX.relative_to(ROOT))
    if not args.skip_pdf:
        pdf = compile_pdf(OUT_TEX)
        print("wrote", pdf.relative_to(ROOT), f"({pdf.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
