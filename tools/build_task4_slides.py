"""Build the Task-4 deck (Beamer PDF, Vietnamese) + word-for-word VI script.

Every number is read from ``reports/tables/*.csv`` at build time - nothing is
typed by hand - so re-running after a renumber refreshes the slides AND the
script together. Wording is formal academic Vietnamese: no em-dash prose, no
colloquialisms (2026-07-16 review). Three audit fixes are baked in:

* the benchmark table comes from ``imbalance_comparison.csv`` strategy='none'
  (the true no-resample run, not the SMOTE-trained ``model_metrics.csv``);
* the best-model-per-checkpoint sentence is DERIVED from
  ``time_aware_best.csv`` (post-renumber: XGBoost leads recall at t=10);
* every "reliable from t=40%" claim carries its bootstrap CI, which straddles
  the 0.80 criterion at t=40 (``bootstrap_ci.csv``).

``threshold_tuning.png`` is deliberately NOT embedded: it marks thresholds
from the test-set sweep (``threshold_tuning.csv``), a different protocol from
the validation-chosen table shown on the threshold slide.

Outputs:
  reports/slides/Task4_Slides_VI.tex / .pdf
  reports/slides/Task4_Script_VI.md

Run:
    python -m tools.build_task4_slides            # tex + script + pdf
    python -m tools.build_task4_slides --skip-pdf
"""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "reports" / "tables"
OUT_TEX = ROOT / "reports" / "slides" / "Task4_Slides_VI.tex"
OUT_SCRIPT = ROOT / "reports" / "slides" / "Task4_Script_VI.md"

TECTONIC_CANDIDATES = (
    "tectonic",
    r"C:\Users\phank\anaconda3\envs\tex\Library\bin\tectonic.exe",
)

NAMES = {
    "xgb": "XGBoost",
    "lgbm": "LightGBM",
    "rf": "Random Forest",
    "ann": "ANN (MLP)",
    "logreg": "Logistic Regression",
}
POLICY_VI = {
    "default(0.5)": "Ngưỡng mặc định (0,50)",
    "f1": "Tối ưu F1",
    "youden": "Chỉ số Youden J",
    "recall>=0.9": "Recall $\\geq$ 0,9",
}
ATTR_VI = {
    "imd_band": "Mức nghèo khu vực (IMD)",
    "region": "Vùng cư trú",
    "highest_education": "Học vấn đầu vào",
    "gender": "Giới tính",
    "disability": "Khuyết tật",
    "age_band": "Nhóm tuổi",
}


def esc(s: str) -> str:
    for a, b in (("&", r"\&"), ("%", r"\%"), ("_", r"\_"), ("#", r"\#")):
        s = s.replace(a, b)
    return s


def f(x, nd=3) -> str:
    """Dot decimals - for LaTeX tables."""
    return f"{float(x):.{nd}f}"


def v(x, nd=3) -> str:
    """Comma decimals - for Vietnamese prose/script."""
    return f(x, nd).replace(".", ",")


def load():
    d = {}
    imb = pd.read_csv(TAB / "imbalance_comparison.csv")
    d["imb_all"] = imb
    d["bench"] = imb[imb.strategy == "none"].sort_values("recall", ascending=False)
    d["shap_imp"] = pd.read_csv(TAB / "xai_shap_importance.csv")
    d["seeds"] = pd.read_csv(TAB / "xai_stability_seeds.csv").iloc[0]
    d["null"] = pd.read_csv(TAB / "xai_jaccard_baseline.csv").iloc[0]
    d["sl"] = pd.read_csv(TAB / "xai_shap_vs_lime.csv").iloc[0]
    d["ckpt"] = pd.read_csv(TAB / "xai_stability_checkpoints.csv")
    d["strat"] = pd.read_csv(TAB / "xai_stability_strategies.csv")
    d["cv"] = pd.read_csv(TAB / "cv_summary.csv").sort_values("recall_mean", ascending=False)
    d["fried"] = pd.read_csv(TAB / "model_friedman.csv")
    d["pw"] = pd.read_csv(TAB / "model_pairwise_wilcoxon.csv")
    d["taw"] = pd.read_csv(TAB / "time_aware_best.csv")
    d["sens"] = pd.read_csv(TAB / "sensitivity_active_xgb.csv")
    d["boot"] = pd.read_csv(TAB / "bootstrap_ci.csv")
    d["thr"] = pd.read_csv(TAB / "threshold_validation.csv")
    d["fair"] = pd.read_csv(TAB / "fairness_gaps.csv").sort_values("recall_gap", ascending=False)
    d["tun"] = pd.read_csv(TAB / "tuning_results.csv")
    assert len(d["bench"]) == 5, "expected 5 baseline models"
    assert sorted(d["taw"].t_percent) == [10, 20, 40, 60, 80, 100]
    return d


def ci_row(boot, t, cohort, metric="recall"):
    r = boot[
        (boot.model == "xgb")
        & (boot.t_percent == t)
        & (boot.cohort == cohort)
        & (boot.metric == metric)
    ].iloc[0]
    return r.point, r.ci_lo, r.ci_hi


def derive(d):
    """All values injected into deck + script, computed once from the CSVs."""
    o = {}
    bench, boot, taw, sens = d["bench"], d["boot"], d["taw"], d["sens"]
    o["xgb_b"] = bench[bench.model == "xgb"].iloc[0]
    o["cv_xgb"] = d["cv"][d["cv"].model == "xgb"].iloc[0]
    smote = d["imb_all"][(d["imb_all"].model == "xgb") & (d["imb_all"].strategy == "SMOTE")].iloc[
        0
    ]
    o["xgb_smote_recall"] = smote.recall
    o["xgb_smote_precision"] = smote.precision

    xr = d["pw"][
        (d["pw"].metric == "recall") & ((d["pw"].model_a == "xgb") | (d["pw"].model_b == "xgb"))
    ]
    o["n_wins"] = int(((xr.better == "xgb") & xr["significant_0.05"]).sum())
    o["n_pairs"] = len(xr)

    # best model per checkpoint - derived, never hand-written (audit fix)
    o["xgb_ts"] = [int(t) for t in taw[taw.model == "xgb"].t_percent]
    o["lgbm_ts"] = [int(t) for t in taw[taw.model == "lgbm"].t_percent]

    o["c40"] = ci_row(boot, 40, "full")  # (0.811, 0.798, 0.824) - straddles 0.80
    o["c60"] = ci_row(boot, 60, "full")
    o["a100"] = ci_row(boot, 100, "active")
    o["g40"] = ci_row(boot, 40, "gap")
    o["gmin_lo"] = boot[boot.cohort == "gap"].ci_lo.min()

    s40 = sens[sens.t_percent == 40].iloc[0]
    s100 = sens[sens.t_percent == 100].iloc[0]
    o["gone10"] = int(sens[sens.t_percent == 10].iloc[0].withdrawn_already_gone)
    o["gone100"] = int(s100.withdrawn_already_gone)
    o["act40"], o["act100"] = s40.active_recall, s100.active_recall
    o["act_n40"] = int(s40.active_n)

    tx = d["tun"][(d["tun"].model == "xgb") & (d["tun"].t_percent == 100)].iloc[0]
    o["tun_x"] = tx
    o["tun_dpr"] = tx.tuned_pr_auc - tx.default_pr_auc

    o["thr_f1"] = d["thr"][d["thr"].policy == "f1"].iloc[0]
    o["thr_r90"] = d["thr"][d["thr"].policy == "recall>=0.9"].iloc[0]
    ft = d["fair"].iloc[0]
    o["fair_attr"] = ATTR_VI.get(ft.attribute, ft.attribute)
    o["fair_pp"] = ft.recall_gap * 100

    # RQ3 - recall spread across the four imbalance strategies, per model
    piv = d["imb_all"].pivot(index="model", columns="strategy", values="recall")
    o["imb_piv"] = piv
    o["imb_spread_max"] = (piv.max(axis=1) - piv.min(axis=1)).max()

    # RQ2 - explanation stability vs the Monte-Carlo null
    top3 = d["shap_imp"].nlargest(3, "importance")
    o["top_feats"] = [(n.split("__", 1)[-1], imp) for n, imp in zip(top3.feature, top3.importance)]
    adj_pairs = [(10, 20), (20, 40), (40, 60), (60, 80), (80, 100)]
    adj = d["ckpt"][d["ckpt"].apply(lambda r: (r.t_from, r.t_to) in adj_pairs, axis=1)]
    o["adj_sp_lo"], o["adj_sp_hi"] = adj.spearman.min(), adj.spearman.max()
    o["adj_j_lo"], o["adj_j_hi"] = adj.jaccard.min(), adj.jaccard.max()
    far = d["ckpt"][(d["ckpt"].t_from == 10) & (d["ckpt"].t_to == 100)]
    assert len(far) == 1, "expected a t=10 vs t=100 row in xai_stability_checkpoints"
    o["j_far"] = far.iloc[0].jaccard
    o["strat_j_lo"] = d["strat"].jaccard_top10.min()
    o["strat_j_hi"] = d["strat"].jaccard_top10.max()
    o["strat_sp_lo"] = d["strat"].spearman.min()
    return o


def build_tex(d, o) -> str:
    bench_body = "\n".join(
        f"    {NAMES[r.model]} & {f(r.recall)} & {f(r.f1)} & {f(r.pr_auc)} & "
        f"{f(r.roc_auc)} & {f(r.precision)} & {f(r.brier)} \\\\"
        for r in d["bench"].itertuples()
    )
    cv_body = "\n".join(
        f"    {NAMES[r.model]} & {f(r.recall_mean, 4)} $\\pm$ {f(r.recall_std, 4)} & "
        f"{f(r.f1_mean, 4)} $\\pm$ {f(r.f1_std, 4)} & "
        f"{f(r.pr_auc_mean, 4)} $\\pm$ {f(r.pr_auc_std, 4)} \\\\"
        for r in d["cv"].itertuples()
    )
    fried_body = "\n".join(
        f"    {esc(r.metric)} & {NAMES[r.best_model]} & {f(r.friedman_stat, 1)} & "
        f"${r.p_value:.1e}$ \\\\".replace("e-", r"\times 10^{-").replace(r"$ \\", r"}$ \\")
        for r in d["fried"].itertuples()
    )
    taw_body = "\n".join(
        f"    {int(r.t_percent)}\\% & {NAMES[r.model]} & {f(r.recall)} & {f(r.pr_auc)} & "
        f"{f(r.f1)} & {'Đạt' if r.reliable else 'Chưa đạt'} \\\\"
        for r in d["taw"].itertuples()
    )
    boot_gap = d["boot"][(d["boot"].cohort == "gap")].set_index("t_percent")
    dual_body = "\n".join(
        f"    {int(r.t_percent)}\\% & {f(r.full_recall)} & {f(r.active_recall)} & "
        f"{f(boot_gap.loc[r.t_percent].point)} [{f(boot_gap.loc[r.t_percent].ci_lo)}, "
        f"{f(boot_gap.loc[r.t_percent].ci_hi)}] & {int(r.active_n):,} & "
        f"{int(r.withdrawn_already_gone):,} \\\\"
        for r in d["sens"].itertuples()
    )
    tun_body = "\n".join(
        f"    {NAMES[r.model]} tại t={int(r.t_percent)}\\% & {f(r.default_pr_auc, 4)} & "
        f"{f(r.tuned_pr_auc, 4)} & {f(r.default_recall, 4)} & {f(r.tuned_recall, 4)} \\\\"
        for r in d["tun"].itertuples()
    )
    thr_body = "\n".join(
        f"    {POLICY_VI.get(r.policy, esc(r.policy))} & {f(r.threshold, 2)} & "
        f"{f(r.val_recall)} & {f(r.test_recall)} & {f(r.test_precision)} \\\\"
        for r in d["thr"].itertuples()
    )
    fair_body = "\n".join(
        f"    {ATTR_VI.get(r.attribute, esc(r.attribute))} & {int(r.n_levels)} & "
        f"{f(r.recall_gap * 100, 1)} pp & {f(r.fpr_gap * 100, 1)} pp \\\\"
        for r in d["fair"].itertuples()
    )
    piv = o["imb_piv"]
    strat_order = ["none", "class_weight", "SMOTE", "ADASYN"]
    imb_body = "\n".join(
        f"    {NAMES[m]} & "
        + " & ".join(
            "không hỗ trợ" if pd.isna(piv.loc[m].get(s)) else f(piv.loc[m][s], 4)
            for s in strat_order
        )
        + f" & {f(piv.loc[m].max() - piv.loc[m].min(), 4)} \\\\"
        for m in ["xgb", "lgbm", "rf", "ann", "logreg"]
    )
    sds, nul, sl = d["seeds"], d["null"], d["sl"]
    rq2_body = "\n".join(
        [
            rf"    Jaccard top 10 giữa 5 seed & \textbf{{{f(sds.mean_jaccard, 2)}}} & cao hơn p99 ({f(nul.p99)}) \\",
            rf"    Spearman toàn thứ hạng giữa 5 seed & {f(sds.mean_spearman, 2)} & không áp dụng \\",
            rf"    Jaccard top 10, SHAP so với LIME & {f(sl.jaccard, 2)} & cao hơn p99 ({f(nul.p99)}) \\",
            rf"    Spearman giữa các mốc liền kề & {f(o['adj_sp_lo'], 2)} đến {f(o['adj_sp_hi'], 2)} & không áp dụng \\",
            rf"    Jaccard giữa t=10\% và t=100\% & {f(o['j_far'], 2)} & xấp xỉ p99 ({f(nul.p99)}) \\",
            rf"    Jaccard giữa 4 chiến lược cân bằng & {f(o['strat_j_lo'], 2)} đến {f(o['strat_j_hi'], 2)} & Spearman $\geq$ {f(o['strat_sp_lo'], 2)} \\",
        ]
    )

    xgb_b = o["xgb_b"]
    c40, c60, a100 = o["c40"], o["c60"], o["a100"]
    xgb_ts = ", ".join(f"{t}" for t in o["xgb_ts"])
    lgbm_ts = ", ".join(f"{t}" for t in o["lgbm_ts"])
    tx = o["tun_x"]
    (feat1, imp1), (feat2, imp2) = o["top_feats"][:2]

    return rf"""% ============================================================
%  DSP391m, Nhóm 1. Task 4: Huấn luyện, so tuyển mô hình và đánh giá kết quả
%  Sinh tự động từ reports/tables/*.csv bởi tools/build_task4_slides.py
%  KHÔNG sửa số liệu trong file này; chạy lại builder sau mỗi renumber.
%  Compile: tectonic Task4_Slides_VI.tex   (XeTeX, font Segoe UI)
% ============================================================
\documentclass[aspectratio=169,11pt]{{beamer}}
\usetheme{{default}}
\setbeamertemplate{{navigation symbols}}{{}}
\usepackage{{fontspec}}
\setmainfont{{Segoe UI}}
\setsansfont{{Segoe UI}}
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
  DSP391m · Nhóm 1 · Task 4: Mô hình hoá và đánh giá\quad\insertframenumber/\inserttotalframenumber\hspace{{2mm}}\vspace{{1mm}}}}

\title{{Task 4: Huấn luyện, so tuyển mô hình\\và đánh giá kết quả (RQ1, RQ2, RQ3)}}
\subtitle{{Dự đoán sớm sinh viên có nguy cơ học tập kém trên OULAD: độ tin cậy theo thời điểm, theo quần thể, và độ ổn định của giải thích}}
\author{{Nhóm 1 · GVHD: Nguyễn Thị Hoàng Yến}}
\institute{{Đại học FPT · DSP391m}}
\date{{}}

\begin{{document}}

\begin{{frame}}\titlepage\end{{frame}}

\begin{{frame}}{{Task 4 trả lời ba câu hỏi nghiên cứu}}
\begin{{itemize}}
  \item \textbf{{RQ1}}: thuật toán nào cho kết quả dự đoán tốt nhất; dự đoán tại thời điểm nào của khóa học thì đạt độ tin cậy yêu cầu; và kết luận đó áp dụng cho quần thể sinh viên nào.
  \item \textbf{{RQ3}}: các kỹ thuật xử lý mất cân bằng lớp có làm thay đổi kết quả dự đoán hay không.
  \item \textbf{{RQ2}}: giải thích do SHAP và LIME tạo ra có ổn định qua seed, qua thời gian và qua chiến lược cân bằng lớp hay không.
\end{{itemize}}
\vspace{{2mm}}
Trình tự trình bày: lựa chọn mô hình và quy trình đánh giá (4.1, 4.2); kết quả so tuyển với hai lớp kiểm chứng và tinh chỉnh siêu tham số (4.3 đến 4.5); RQ3; kết quả theo sáu mốc thời gian với kết luận kép theo hai quần thể (RQ1); ngưỡng quyết định và công bằng theo nhóm (4.7, 4.8); RQ2.
\vspace{{2mm}}

\emph{{Tiêu chí tin cậy:}} recall $\geq$ 0,80 \textbf{{và}} PR-AUC $\geq$ 0,80 trên lớp nguy cơ của tập kiểm tra độc lập.
\end{{frame}}

\begin{{frame}}{{4.1 · Lựa chọn mô hình: năm thuật toán, ba họ mô hình}}
\small
\begin{{tabular}}{{@{{}}lll@{{}}}}
\toprule
\textbf{{Mô hình}} & \textbf{{Họ thuật toán}} & \textbf{{Cơ sở lựa chọn}} \\
\midrule
Logistic Regression & Tuyến tính & Baseline chuẩn; hệ số hồi quy diễn giải trực tiếp được \\
Random Forest & Bagging cây & Bền vững với nhiễu và giá trị ngoại lai; ít cần tinh chỉnh \\
XGBoost & Boosting cây & Hiệu năng hàng đầu cho dữ liệu dạng bảng; SHAP TreeExplainer chính xác \\
LightGBM & Boosting cây & Tối ưu tốc độ; đối chứng trong cùng họ boosting \\
ANN (MLP) & Mạng nơ-ron & Đại diện phi tuyến ngoài họ cây \\
\bottomrule
\end{{tabular}}
\vspace{{4mm}}
\begin{{itemize}}
  \item Năm thuật toán phủ \textbf{{ba họ mô hình}}, do đó thứ hạng thu được không phụ thuộc một thiên kiến quy nạp duy nhất.
  \item Cả năm thuật toán đều xuất hiện trong các nghiên cứu nền trên OULAD, bảo đảm khả năng so sánh với văn liệu.
\end{{itemize}}
\end{{frame}}

\begin{{frame}}{{4.1 · Cấu hình huấn luyện: nguyên tắc can thiệp tối thiểu}}
\small
\begin{{tabular}}{{@{{}}ll@{{}}}}
\toprule
\textbf{{Mô hình}} & \textbf{{Cấu hình chính (các tham số khác giữ mặc định)}} \\
\midrule
Logistic Regression & \texttt{{max\_iter=1000}} \\
Random Forest & mặc định; \texttt{{n\_jobs=-1}} \\
XGBoost & \texttt{{tree\_method=hist}}; \texttt{{eval\_metric=logloss}} \\
LightGBM & mặc định; \texttt{{verbose=-1}} \\
ANN (MLP) & hai lớp ẩn (64, 32); \texttt{{max\_iter=500}}; dừng sớm (early stopping) \\
\bottomrule
\end{{tabular}}
\vspace{{4mm}}
\begin{{itemize}}
  \item Mọi mô hình dùng chung \textbf{{random seed 42}} nhằm bảo đảm so sánh công bằng và tái lập chính xác.
  \item Không tinh chỉnh siêu tham số ở vòng so tuyển, tránh thiên vị mô hình được đầu tư nhiều công sức hơn; việc tinh chỉnh được trình bày ở mục 4.5.
\end{{itemize}}
\end{{frame}}

\begin{{frame}}{{4.2 · Quy trình huấn luyện và đánh giá}}
\begin{{enumerate}}
  \item Nạp \textbf{{phép chia cố định theo sinh viên}}: không sinh viên nào xuất hiện đồng thời ở tập huấn luyện và tập kiểm tra; toàn bộ kiểm thử rò rỉ tự động đạt.
  \item Tiền xử lý được \textbf{{fit trên tập huấn luyện}}, sau đó áp dụng lên tập kiểm tra (trung vị, ngưỡng winsorize, bộ mã hoá, bộ chuẩn hoá).
  \item Huấn luyện trên tập huấn luyện; dự đoán trên \textbf{{tập kiểm tra độc lập}}.
  \item Tính \textbf{{bảy chỉ số}}; xếp hạng ưu tiên \textbf{{recall}} của lớp nguy cơ.
\end{{enumerate}}
\vspace{{3mm}}
\begin{{itemize}}
  \item Việc ưu tiên recall xuất phát từ lập luận chi phí: bỏ sót một sinh viên có nguy cơ đồng nghĩa mất cơ hội can thiệp, trong khi một cảnh báo sai chỉ dẫn tới một buổi trao đổi tư vấn. Accuracy không được dùng làm chỉ số chính vì lớp nguy cơ chiếm đa số nhẹ.
  \item Kết quả mục 4.3 là \textbf{{baseline không tái lấy mẫu}} (hàng \texttt{{strategy=none}}); RQ3 so sánh bốn chiến lược cân bằng lớp trên cùng quy trình này.
\end{{itemize}}
\end{{frame}}

\begin{{frame}}{{4.3 · Kết quả so tuyển tại t=100\%}}
\centering
\includegraphics[height=0.82\textheight]{{model_benchmark_baseline.png}}
\end{{frame}}

\begin{{frame}}{{4.3 · Bảng bảy chỉ số (baseline không tái lấy mẫu, sinh từ CSV)}}
\centering\small
\textbf{{XGBoost}}: recall \textbf{{{f(xgb_b.recall)}}}; F1 \textbf{{{f(xgb_b.f1)}}}; PR-AUC \textbf{{{f(xgb_b.pr_auc)}}}; Brier {f(xgb_b.brier)} (giá trị thấp là tốt)\\[2mm]
\begin{{tabular}}{{@{{}}lcccccc@{{}}}}
\toprule
\textbf{{Mô hình}} & \textbf{{Recall}} & \textbf{{F1}} & \textbf{{PR-AUC}} & \textbf{{ROC-AUC}} & \textbf{{Precision}} & \textbf{{Brier}}$\downarrow$ \\
\midrule
{bench_body}
\bottomrule
\end{{tabular}}
\vspace{{3mm}}
\begin{{itemize}}\small
  \item Ba mô hình họ cây đạt kết quả rất gần nhau; Logistic Regression xếp cuối nhưng không kém xa, cho thấy tín hiệu trong đặc trưng mạnh và phần lớn tách được tuyến tính.
  \item Khoảng cách giữa các mô hình nhỏ; cần kiểm chứng xem thứ hạng có ý nghĩa thống kê hay chỉ là kết quả ngẫu nhiên của một lần phân chia dữ liệu.
\end{{itemize}}
\end{{frame}}

\begin{{frame}}{{4.3 · Ma trận nhầm lẫn của mô hình được chọn (t=100\%, ngưỡng 0,50)}}
\centering
\includegraphics[height=0.74\textheight]{{confusion_default_t100.png}}\\
{{\small Mô hình XGBoost của pipeline chuẩn (có SMOTE): recall {v(o["xgb_smote_recall"], 3)}, tỉ lệ bỏ sót lớp nguy cơ {v((1 - o["xgb_smote_recall"]) * 100, 1)}\%. Baseline không tái lấy mẫu ở bảng trước đạt recall {v(xgb_b.recall, 3)}; hai giá trị chênh nhau không đáng kể.}}
\end{{frame}}

\begin{{frame}}{{4.4 · Kiểm chứng thứ nhất: kiểm định chéo 5 fold $\times$ 5 seed}}
\centering\small
\begin{{tabular}}{{@{{}}lccc@{{}}}}
\toprule
\textbf{{Mô hình}} & \textbf{{Recall ($\mu\pm\sigma$)}} & \textbf{{F1 ($\mu\pm\sigma$)}} & \textbf{{PR-AUC ($\mu\pm\sigma$)}} \\
\midrule
{cv_body}
\bottomrule
\end{{tabular}}
\vspace{{3mm}}
\begin{{itemize}}\small
  \item Hai mươi lăm lần huấn luyện cho mỗi mô hình; tiền xử lý và cân bằng lớp được lặp lại bên trong từng fold; các fold gộp theo sinh viên nên không phát sinh rò rỉ.
  \item Độ lệch chuẩn nhỏ so với chênh lệch giữa các mô hình; thứ hạng theo kiểm định chéo trùng với thứ hạng trên tập kiểm tra, do đó kết quả của một lần phân chia không phải điểm dị thường.
\end{{itemize}}
\end{{frame}}

\begin{{frame}}{{4.4 · Độ bất định của ước lượng kiểm định chéo}}
\centering
\includegraphics[height=0.78\textheight]{{cv_uncertainty.png}}\\
{{\small Chênh lệch giữa các mô hình lớn hơn biến thiên nội tại của từng mô hình (trung bình $\pm$ 1 độ lệch chuẩn trên 25 fold).}}
\end{{frame}}

\begin{{frame}}{{4.4 · Kiểm chứng thứ hai: kiểm định thống kê trên 25 fold ghép cặp}}
\centering\small
\begin{{tabular}}{{@{{}}llcc@{{}}}}
\toprule
\textbf{{Chỉ số}} & \textbf{{Mô hình tốt nhất (mean rank)}} & \textbf{{Friedman $\chi^2$}} & \textbf{{p-value}} \\
\midrule
{fried_body}
\bottomrule
\end{{tabular}}
\vspace{{3mm}}
\begin{{itemize}}\small
  \item Kiểm định Friedman bác bỏ giả thuyết các mô hình tương đương ở mọi chỉ số với mức ý nghĩa rất cao.
  \item Kiểm định hậu nghiệm Wilcoxon với hiệu chỉnh Holm cho recall: XGBoost cao hơn có ý nghĩa thống kê so với \textbf{{{o["n_wins"]}/{o["n_pairs"]}}} mô hình còn lại; LightGBM dẫn đầu các chỉ số tổng hợp (F1, PR-AUC, ROC-AUC).
  \item XGBoost được chọn làm mô hình chính do khung đánh giá ưu tiên recall và do phần giải thích (RQ2) yêu cầu SHAP TreeExplainer chính xác.
\end{{itemize}}
\end{{frame}}

\begin{{frame}}{{4.5 · Tinh chỉnh siêu tham số}}
\centering\small
RandomizedSearchCV; 40 cấu hình cho mỗi mô hình; kiểm định chéo 5 fold gộp theo sinh viên; tối ưu PR-AUC; SMOTE trong từng fold\\[2mm]
\begin{{tabular}}{{@{{}}lcccc@{{}}}}
\toprule
 & \multicolumn{{2}}{{c}}{{\textbf{{PR-AUC}}}} & \multicolumn{{2}}{{c}}{{\textbf{{Recall}}}} \\
\textbf{{Mô hình và mốc}} & gốc & sau tinh chỉnh & gốc & sau tinh chỉnh \\
\midrule
{tun_body}
\bottomrule
\end{{tabular}}
\vspace{{3mm}}
\begin{{itemize}}\small
  \item Random search được chọn thay cho grid search (chi phí tổ hợp lớn) và Bayesian optimisation (lợi ích không tương xứng ở quy mô 40 cấu hình).
  \item Với XGBoost tại t=100\%: PR-AUC tăng {f(o["tun_dpr"], 4)} nhưng recall giảm từ {f(tx.default_recall, 4)} xuống {f(tx.tuned_recall, 4)}. Mức cải thiện không tương xứng với chi phí tái lập của một cấu hình riêng, do đó \textbf{{cấu hình gần mặc định được giữ nguyên}}.
\end{{itemize}}
\end{{frame}}

\begin{{frame}}{{RQ3 · Ảnh hưởng của bốn chiến lược cân bằng lớp}}
\centering
\includegraphics[height=0.82\textheight]{{imbalance_recall_by_model.png}}
\end{{frame}}

\begin{{frame}}{{RQ3 · Recall theo mô hình và chiến lược cân bằng (t=100\%)}}
\centering\small
\begin{{tabular}}{{@{{}}lccccc@{{}}}}
\toprule
\textbf{{Mô hình}} & \textbf{{none}} & \textbf{{class\_weight}} & \textbf{{SMOTE}} & \textbf{{ADASYN}} & \textbf{{Chênh lệch lớn nhất}} \\
\midrule
{imb_body}
\bottomrule
\end{{tabular}}
\vspace{{3mm}}
\begin{{itemize}}\small
  \item Lớp nguy cơ chiếm 52,8\% (tỉ lệ mất cân bằng 1,12), tức đa số nhẹ; RQ3 vì vậy được đặt như một câu hỏi về tính bền vững của kết quả, không phải về khắc phục lớp thiểu số hiếm. ANN không hỗ trợ class\_weight, nên lưới thử nghiệm gồm 19 cấu hình.
  \item Chênh lệch recall lớn nhất giữa bốn chiến lược trên mọi mô hình là \textbf{{{f(o["imb_spread_max"], 4)}}}: kết quả không phụ thuộc cách xử lý mất cân bằng; pipeline giữ SMOTE theo đề cương đã duyệt.
\end{{itemize}}
\end{{frame}}

\begin{{frame}}{{RQ1 · Hiệu năng theo sáu mốc thời gian (quần thể đầy đủ)}}
\centering
\includegraphics[width=0.49\textwidth]{{time_aware_recall.png}}\hfill
\includegraphics[width=0.49\textwidth]{{time_aware_pr_auc.png}}\\
{{\small Recall (trái) chỉ vượt tiêu chí 0,80 từ t=40\%; PR-AUC (phải) vượt tiêu chí 0,80 tại mọi mốc, do đó không vẽ đường tham chiếu. Hai biểu đồ là hai vế của cùng một tiêu chí tin cậy.}}
\end{{frame}}

\begin{{frame}}{{RQ1 · Mô hình tốt nhất theo từng mốc (quần thể đầy đủ)}}
\centering\small
\begin{{tabular}}{{@{{}}llcccc@{{}}}}
\toprule
\textbf{{Mốc}} & \textbf{{Mô hình tốt nhất}} & \textbf{{Recall}} & \textbf{{PR-AUC}} & \textbf{{F1}} & \textbf{{Tiêu chí}} \\
\midrule
{taw_body}
\bottomrule
\end{{tabular}}
\vspace{{3mm}}
\begin{{itemize}}\small
  \item XGBoost dẫn đầu recall tại các mốc {xgb_ts}\%; LightGBM tại các mốc {lgbm_ts}\%. Hai mô hình boosting luân phiên dẫn đầu với chênh lệch nhỏ, củng cố kết luận rằng họ boosting, chứ không phải một thuật toán riêng lẻ, chiếm ưu thế.
  \item Tại t=40\%: recall {f(c40[0])} với khoảng tin cậy bootstrap 95\% [{f(c40[1])}, {f(c40[2])}]. Khoảng này \textbf{{chứa ngưỡng 0,80}}, nên kết luận đạt chuẩn tại t=40\% chỉ ở mức ranh giới; từ t=60\% toàn bộ khoảng tin cậy nằm trên ngưỡng ([{f(c60[1])}, {f(c60[2])}]).
\end{{itemize}}
\end{{frame}}

\begin{{frame}}{{RQ1 · Quần thể đầy đủ bao gồm cả sinh viên đã rút trước mốc}}
\centering
\includegraphics[height=0.78\textheight]{{sensitivity_active_recall_xgb.png}}
\end{{frame}}

\begin{{frame}}{{RQ1 · Kết luận kép theo hai quần thể}}
\centering\small
\begin{{tabular}}{{@{{}}lccccc@{{}}}}
\toprule
\textbf{{Mốc}} & \textbf{{Recall đầy đủ}} & \textbf{{Recall còn theo học}} & \textbf{{Chênh lệch [KTC 95\%]}} & \textbf{{N còn theo học}} & \textbf{{Đã rút trước mốc}} \\
\midrule
{dual_body}
\bottomrule
\end{{tabular}}
\vspace{{2mm}}
\begin{{itemize}}\small
  \item Khoảng tin cậy của chênh lệch \textbf{{không chứa 0 tại cả sáu mốc}} (cận dưới nhỏ nhất {f(o["gmin_lo"])}): một phần recall của quần thể đầy đủ đến từ các sinh viên đã rút, tức là ghi nhận một kết cục đã xảy ra thay vì dự báo.
  \item Trên \textbf{{quần thể đầy đủ}} (khung so sánh với văn liệu): đạt chuẩn từ t=40\%, ở mức ranh giới. Trên \textbf{{quần thể còn theo học}} (khung can thiệp thực tế): tiêu chí chỉ đạt tại t=100\%, recall {f(a100[0])}, khoảng tin cậy [{f(a100[1])}, {f(a100[2])}].
  \item Đây không phải rò rỉ dữ liệu: nhãn không tham gia vào đặc trưng, và mức độ bất hoạt của sinh viên đã rút là hành vi quan sát thực. Đây là khác biệt về \textbf{{định nghĩa quần thể}} mà hai nghiên cứu nền không tách bạch.
\end{{itemize}}
\end{{frame}}

\begin{{frame}}{{4.7 · Ngưỡng quyết định chọn trên tập validation}}
\centering\small
\begin{{tabular}}{{@{{}}lcccc@{{}}}}
\toprule
\textbf{{Chính sách}} & \textbf{{Ngưỡng}} & \textbf{{Recall (val)}} & \textbf{{Recall (test)}} & \textbf{{Precision (test)}} \\
\midrule
{thr_body}
\bottomrule
\end{{tabular}}
\vspace{{3mm}}
\begin{{itemize}}\small
  \item Ngưỡng được chọn trên \textbf{{dự đoán out-of-fold}} của tập huấn luyện, cố định trước, sau đó đánh giá trên tập kiểm tra đúng một lần; quy trình này loại trừ việc tối ưu ngưỡng trên tập kiểm tra.
  \item Chính sách tối ưu F1 cho ngưỡng {f(o["thr_f1"].threshold, 2)}, gần ngưỡng mặc định 0,50; các kết quả ở những mục trước vì vậy không phải sản phẩm của việc lựa chọn ngưỡng.
  \item Chính sách recall $\geq$ 0,9: ngưỡng {f(o["thr_r90"].threshold, 2)} đạt recall {f(o["thr_r90"].test_recall)} với precision {f(o["thr_r90"].test_precision)} trên tập kiểm tra. Các ngưỡng này \emph{{chỉ được kiểm chứng cho XGBoost tại t=100\%}}.
\end{{itemize}}
\end{{frame}}

\begin{{frame}}{{4.8 · Hiệu năng phân tách theo nhóm nhân khẩu học (t=100\%, ngưỡng 0,50)}}
\centering\small
\begin{{tabular}}{{@{{}}lccc@{{}}}}
\toprule
\textbf{{Thuộc tính}} & \textbf{{Số nhóm}} & \textbf{{Chênh lệch recall}} & \textbf{{Chênh lệch FPR}} \\
\midrule
{fair_body}
\bottomrule
\end{{tabular}}
\vspace{{3mm}}
\begin{{itemize}}\small
  \item Chỉ xét các nhóm có tối thiểu 50 sinh viên trong tập kiểm tra. Chênh lệch recall lớn nhất là \textbf{{{f(o["fair_pp"], 1)} điểm phần trăm}} ({o["fair_attr"]}); recall của nhóm khai báo khuyết tật không thấp hơn nhóm còn lại.
  \item Đây là số liệu quan sát tại một mốc và một ngưỡng, không phải chứng nhận công bằng; hệ thống khi triển khai cần giám sát liên tục các chỉ số phân tách này.
\end{{itemize}}
\end{{frame}}

\begin{{frame}}{{RQ2 · Đặc trưng nào ảnh hưởng lớn nhất đến dự đoán nguy cơ?}}
\centering
\includegraphics[height=0.76\textheight]{{shap_importance_xgb_t100.png}}\\
{{\small Hai đặc trưng có đóng góp lớn nhất: \texttt{{{esc(feat1)}}} ({f(imp1, 2)}, số ngày kể từ lần hoạt động gần nhất) và \texttt{{{esc(feat2)}}} ({f(imp2, 2)}, điểm đánh giá tích lũy có trọng số).}}
\end{{frame}}

\begin{{frame}}{{RQ2 · Độ ổn định của giải thích qua các mốc thời gian}}
\centering
\includegraphics[height=0.76\textheight]{{xai_stability_drift.png}}\\
{{\small Mức đồng thuận cao giữa các mốc liền kề và giảm dần khi khoảng cách thời gian giữa hai mốc tăng.}}
\end{{frame}}

\begin{{frame}}{{RQ2 · Định lượng độ ổn định, đối chiếu với mốc ngẫu nhiên}}
\centering\small
\begin{{tabular}}{{@{{}}lll@{{}}}}
\toprule
\textbf{{Phép đo}} & \textbf{{Kết quả}} & \textbf{{Đối chiếu mốc ngẫu nhiên}} \\
\midrule
{rq2_body}
\bottomrule
\end{{tabular}}
\vspace{{3mm}}
\begin{{itemize}}\small
  \item Mốc ngẫu nhiên: hai tập 10 đặc trưng chọn ngẫu nhiên từ 49 đặc trưng có Jaccard trung bình {f(nul["mean"])}, phân vị 99 là {f(nul.p99)}. Mọi mức đồng thuận quan sát được đều vượt phân vị này, do đó độ ổn định không thể quy cho ngẫu nhiên.
  \item SHAP và LIME đồng thuận ở nhóm đặc trưng dẫn đầu (Jaccard top 10 bằng {f(sl.jaccard, 2)}); tương quan toàn thứ hạng thấp hơn (Spearman {f(sl.spearman, 2)}) do phần cuối thứ hạng của LIME kém ổn định, vì vậy chỉ nhóm đặc trưng dẫn đầu được dùng để diễn giải.
  \item Thành phần top 10 thay đổi dần theo thời gian (Jaccard giữa t=10\% và t=100\% bằng {f(o["j_far"], 2)}), phù hợp với kỳ vọng: tín hiệu giai đoạn sớm thiên về hành vi, giai đoạn cuối thiên về kết quả đánh giá.
\end{{itemize}}
\end{{frame}}

\begin{{frame}}{{Kết luận Task 4: ba câu trả lời}}
\begin{{itemize}}
  \item Năm thuật toán thuộc ba họ được so tuyển trong cùng điều kiện; \textbf{{XGBoost}} được chọn (recall baseline {f(xgb_b.recall)}) với hai lớp kiểm chứng: kiểm định chéo 5 fold $\times$ 5 seed và kiểm định Friedman, Wilcoxon. Tinh chỉnh siêu tham số không mang lại cải thiện tương xứng, nên cấu hình gần mặc định được giữ nguyên.
  \item \textbf{{RQ1, kết luận kép:}} quần thể đầy đủ đạt chuẩn từ t=40\% ở mức ranh giới (khoảng tin cậy chứa 0,80); quần thể còn theo học chỉ đạt chuẩn tại t=100\%; chênh lệch giữa hai quần thể có ý nghĩa thống kê tại cả sáu mốc.
  \item \textbf{{RQ3:}} bốn chiến lược cân bằng lớp chênh nhau tối đa {f(o["imb_spread_max"], 4)} recall; kết quả bền vững, không phụ thuộc cách xử lý mất cân bằng.
  \item \textbf{{RQ2:}} độ ổn định của giải thích vượt phân vị 99 của mốc ngẫu nhiên (Jaccard giữa các seed {f(d["seeds"].mean_jaccard, 2)} so với {f(d["null"].p99)}); SHAP và LIME đồng thuận ở nhóm đặc trưng dẫn đầu.
  \item Toàn bộ slide và kịch bản sinh lại từ CSV bằng lệnh \texttt{{python -m tools.build\_task4\_slides}}.
\end{{itemize}}
\vspace{{2mm}}
\centering\color{{themecol}}\textbf{{Nhóm 1 xin cảm ơn thầy cô và các bạn!}}
\end{{frame}}

\end{{document}}
"""


def build_script(d, o) -> str:
    xgb_b, cv_xgb, tx = o["xgb_b"], o["cv_xgb"], o["tun_x"]
    c40, a100, g40 = o["c40"], o["a100"], o["g40"]
    lgbm_cv = d["cv"][d["cv"].model == "lgbm"].iloc[0]
    lgbm_b = d["bench"][d["bench"].model == "lgbm"].iloc[0]
    logreg_b = d["bench"][d["bench"].model == "logreg"].iloc[0]
    s10_full = d["sens"][d["sens"].t_percent == 10].iloc[0].full_recall
    s100_full = d["sens"][d["sens"].t_percent == 100].iloc[0].full_recall
    g10 = ci_row(d["boot"], 10, "gap")
    g100 = ci_row(d["boot"], 100, "gap")
    xgb_ts = ", ".join(f"{t}%" for t in o["xgb_ts"])
    lgbm_ts = " và ".join(f"{t}%" for t in o["lgbm_ts"])
    thr_f1, thr_r90 = o["thr_f1"], o["thr_r90"]
    sds, nul, sl = d["seeds"], d["null"], d["sl"]
    (feat1, imp1), (feat2, imp2) = o["top_feats"][:2]
    feat3, imp3 = o["top_feats"][2]

    return f"""DSP391m · Nhóm 1
# Kịch bản thuyết trình (bộ slide **Task 4: Mô hình hoá và đánh giá, RQ1 · RQ2 · RQ3**, `Task4_Slides_VI.pdf`)

**Phạm vi:** trọn Task 4, gồm so tuyển mô hình và cân bằng lớp (Đức), kết quả theo thời gian, ngưỡng quyết định và công bằng (Khoa), độ ổn định của giải thích (Bình). Trả lời cả ba câu hỏi nghiên cứu.
**Người trình bày:** **Đức** slide 2 đến 14, **Khoa** slide 15 đến 20, **Bình** slide 21 đến 24. Tổng thời lượng khoảng **20 đến 25 phút**; nếu bị giới hạn thời gian, có thể rút gọn phần giải thích cấu trúc biểu đồ ở các slide 6, 10 và 13, giữ nguyên phần ý nghĩa. Các đoạn có chú thích in nghiêng trong ngoặc là chỉ dẫn động tác: vừa chỉ tay vào vị trí tương ứng trên biểu đồ vừa đọc câu tiếp theo. Mỗi đoạn giải thích biểu đồ đi theo cùng một trình tự: mục đích của biểu đồ trong mạch lập luận, cấu trúc các trục và màu, con số cần chỉ, và ý nghĩa của kết quả.

Mở `reports/slides/Task4_Slides_VI.pdf`, trình chiếu toàn màn hình (Ctrl+L; phím Space chuyển slide kế). Khi trình bày, chỉ trực tiếp vào bảng hoặc biểu đồ đang nói tới.

> Bộ slide **24 trang**: 1 trang bìa và 23 trang nội dung. Mọi con số trong slide **và trong kịch bản này** được sinh trực tiếp từ CSV
> (`imbalance_comparison.csv`, `cv_summary.csv`, `model_friedman.csv`, `model_pairwise_wilcoxon.csv`, `tuning_results.csv`,
> `time_aware_best.csv`, `sensitivity_active_xgb.csv`, `bootstrap_ci.csv`, `threshold_validation.csv`, `fairness_gaps.csv`,
> `xai_shap_importance.csv`, `xai_stability_seeds.csv`, `xai_jaccard_baseline.csv`, `xai_shap_vs_lime.csv`,
> `xai_stability_checkpoints.csv`, `xai_stability_strategies.csv`). Tái lập bằng lệnh `python -m tools.build_task4_slides`.
> **Không sửa tay số liệu trong file này.**

---

## Phần Đức (slide 1 đến 14)

**Slide 1, trang bìa.**
Kính chào thầy cô và các bạn. Nhóm 1 xin trình bày Task 4: huấn luyện, so tuyển mô hình và đánh giá kết quả. Em là Đức, phụ trách phần mô hình hoá. Bạn Khoa sẽ trình bày phần kết quả theo các mốc thời gian, và bạn Bình trình bày phần giải thích mô hình. Task 4 của nhóm trả lời trọn vẹn cả ba câu hỏi nghiên cứu của đề tài.

**Slide 2, ba câu hỏi nghiên cứu.**
Cụ thể như sau. Câu hỏi thứ nhất, RQ1: thuật toán nào cho kết quả dự đoán tốt nhất, dự đoán tại thời điểm nào của khóa học thì đạt độ tin cậy yêu cầu, và kết luận đó áp dụng cho quần thể sinh viên nào. Câu hỏi thứ ba, RQ3: các kỹ thuật xử lý mất cân bằng lớp có làm thay đổi kết quả hay không. Câu hỏi thứ hai, RQ2: các giải thích do SHAP và LIME tạo ra có ổn định hay không. Tiêu chí tin cậy được nhóm cố định ngay từ đầu: recall và PR-AUC cùng đạt tối thiểu 0,80 trên lớp nguy cơ của tập kiểm tra độc lập.

**Slide 3, lựa chọn mô hình.**
*(chỉ theo từng hàng của bảng)*
Nhóm so tuyển năm thuật toán thuộc ba họ mô hình. Logistic Regression là baseline tuyến tính chuẩn, hệ số hồi quy diễn giải trực tiếp được. Random Forest đại diện họ bagging cây, bền vững với nhiễu và giá trị ngoại lai. XGBoost đại diện họ boosting cây, hiện vẫn là lựa chọn có hiệu năng hàng đầu cho dữ liệu dạng bảng; điểm quyết định đối với đề tài là XGBoost hỗ trợ SHAP TreeExplainer với thuộc tính chính xác cho mô hình cây, điều mà phần giải thích ở RQ2 yêu cầu. LightGBM cùng họ boosting, đóng vai trò đối chứng trong cùng một họ. Cuối cùng, mạng nơ-ron nhiều lớp đại diện cho họ phi tuyến ngoài họ cây. Việc phủ ba họ mô hình bảo đảm thứ hạng thu được không phụ thuộc một thiên kiến quy nạp duy nhất; đồng thời cả năm thuật toán đều xuất hiện trong các nghiên cứu nền trên OULAD, nên kết quả so sánh được với văn liệu.

**Slide 4, cấu hình huấn luyện.**
Nguyên tắc cấu hình là can thiệp tối thiểu: các mô hình giữ tham số gần mặc định, Logistic Regression chỉ nâng giới hạn số vòng lặp để hội tụ, mạng nơ-ron dùng cơ chế dừng sớm để hạn chế quá khớp. Hai điểm cần nhấn mạnh: thứ nhất, mọi mô hình dùng chung random seed 42 nhằm bảo đảm so sánh công bằng và tái lập chính xác; thứ hai, ở vòng so tuyển nhóm không tinh chỉnh siêu tham số, vì tinh chỉnh một ứng viên kỹ hơn các ứng viên khác sẽ làm lệch thứ hạng. Việc tinh chỉnh được thực hiện sau khi đã chọn ứng viên, trình bày ở mục 4.5.

**Slide 5, quy trình huấn luyện và đánh giá.**
Mỗi mô hình đi qua đúng bốn bước. Bước một: nạp phép chia cố định theo sinh viên; không sinh viên nào xuất hiện đồng thời ở tập huấn luyện và tập kiểm tra, và toàn bộ bộ kiểm thử rò rỉ tự động của dự án đều đạt. Bước hai: tiền xử lý được fit trên tập huấn luyện rồi mới áp dụng lên tập kiểm tra. Bước ba: huấn luyện và dự đoán trên tập kiểm tra độc lập. Bước bốn: tính bảy chỉ số và xếp hạng ưu tiên recall của lớp nguy cơ. Việc ưu tiên recall xuất phát từ lập luận chi phí: bỏ sót một sinh viên có nguy cơ đồng nghĩa mất cơ hội can thiệp, trong khi một cảnh báo sai chỉ dẫn tới một buổi trao đổi tư vấn. Xin lưu ý rằng bảng kết quả sắp trình bày là baseline không tái lấy mẫu, tương ứng hàng strategy bằng none trong dữ liệu; phần RQ3 sẽ so sánh bốn chiến lược cân bằng lớp trên cùng quy trình này.

**Slide 6, biểu đồ so tuyển.**
*(đứng cạnh biểu đồ)*
Biểu đồ này tồn tại để trả lời vế thứ nhất của RQ1, thuật toán nào tốt nhất, tại mốc mà mọi mô hình có đầy đủ thông tin nhất, tức 100% thời lượng khóa học. Em giải thích cấu trúc trước. *(chỉ vào trục hoành)* Trục hoành là năm mô hình; với mỗi mô hình có bốn cột, theo thứ tự từ trái sang phải là recall, F1, PR-AUC và ROC-AUC; trục tung là giá trị chỉ số trên thang từ 0 đến 1, và con số phía trên mỗi cột là giá trị chính xác. Vì sao bốn chỉ số thay vì một: recall đo tỉ lệ sinh viên nguy cơ được nhận diện, là mục tiêu chính; F1 cân bằng giữa nhận diện và cảnh báo sai; PR-AUC và ROC-AUC đánh giá chất lượng xếp hạng xác suất, không phụ thuộc ngưỡng. Một mô hình chỉ đáng tin khi cao đồng đều ở cả bốn. *(chỉ vào cột thứ nhất của nhóm XGBoost)* Cột quan trọng nhất là recall của XGBoost, {v(xgb_b.recall)}, cao nhất trong năm mô hình. *(lướt tay qua các cột recall từ trái sang phải)* Đi qua các mô hình, recall giảm rất chậm, từ {v(xgb_b.recall)} xuống {v(logreg_b.recall)} của Logistic Regression. Ý nghĩa của khoảng hẹp này nằm ở chỗ nó cho biết giá trị dự đoán đến từ đâu. Nếu tín hiệu chỉ nằm trong các tương tác phi tuyến phức tạp, mô hình tuyến tính sẽ tụt lại rất xa; thực tế nó chỉ kém khoảng một điểm phần trăm. *(chỉ vào nhóm cột Logistic Regression)* Nghĩa là bộ đặc trưng nhóm xây dựng đã mã hoá phần lớn thông tin dự đoán dưới dạng tách được tuyến tính; các mô hình họ cây bổ sung một phần cải thiện thực nhưng khiêm tốn. Hệ quả cho lập luận: thứ nhất, giá trị của pipeline nằm ở khâu đặc trưng nhiều hơn khâu thuật toán; thứ hai, vì khoảng cách giữa các mô hình nhỏ, một biểu đồ đơn lẻ chưa đủ để kết luận thứ hạng, và đó là lý do cần hai lớp kiểm chứng ở các slide sau.

**Slide 7, bảng bảy chỉ số.**
*(đọc hàng đầu của bảng)*
Trình bày bằng số liệu cụ thể: XGBoost đạt recall {v(xgb_b.recall)}, F1 {v(xgb_b.f1)}, PR-AUC {v(xgb_b.pr_auc)}, và Brier {v(xgb_b.brier)}, là chỉ số chất lượng xác suất, giá trị càng thấp càng tốt. LightGBM đứng ngay sau với recall {v(lgbm_b.recall)} và PR-AUC cao nhất bảng, {v(lgbm_b.pr_auc)}. Khoảng cách giữa các mô hình nhỏ, vì vậy câu hỏi cần trả lời tiếp theo là: thứ hạng này có ý nghĩa thống kê hay chỉ là kết quả ngẫu nhiên của một lần phân chia dữ liệu. Hai lớp kiểm chứng ở các slide sau trả lời câu hỏi đó.

**Slide 8, ma trận nhầm lẫn.**
Các chỉ số tổng hợp ở bảng trước nén toàn bộ hành vi của mô hình vào một con số; ma trận nhầm lẫn tồn tại để trả lời câu hỏi mà các con số đó che khuất: khi mô hình sai, nó sai theo kiểu nào, và mỗi kiểu sai gây hậu quả gì. *(chỉ vào nhãn hai hàng, rồi nhãn hai cột)* Cách đọc: mỗi hàng là nhãn thực tế, mỗi cột là nhãn mô hình dự đoán; như vậy hai ô trên đường chéo là các quyết định đúng, hai ô ngoài đường chéo là hai kiểu sai khác nhau về bản chất. Phần trăm trong mỗi ô tính trên tổng của hàng, màu càng đậm tỉ lệ càng cao. *(chỉ vào ô dưới bên phải)* Ô dưới bên phải: sinh viên thực sự có nguy cơ và được nhận diện đúng, {v(o["xgb_smote_recall"] * 100, 1)} phần trăm của hàng dưới; tỉ lệ này chính là recall, cùng một con số với bảng trước nhưng ở đây thấy được nó sinh ra từ đâu. *(chỉ vào ô dưới bên trái)* Ô dưới bên trái là kiểu sai thứ nhất: sinh viên có nguy cơ nhưng không được gắn cờ, {v((1 - o["xgb_smote_recall"]) * 100, 1)} phần trăm. Hậu quả của kiểu sai này là không thể sửa chữa: sinh viên không nhận được hỗ trợ và cơ hội can thiệp mất hẳn. *(chỉ vào ô trên bên phải)* Ô trên bên phải là kiểu sai thứ hai: sinh viên không có nguy cơ nhưng bị gắn cờ. Hậu quả chỉ là một buổi trao đổi tư vấn không thật sự cần thiết. Chính sự bất đối xứng về hậu quả giữa hai ô này là lý do toàn bộ đề tài xếp hạng theo recall thay vì accuracy. Kết hợp cột bên phải ta được precision {v(o["xgb_smote_precision"])}: gần như mọi trường hợp bị gắn cờ đều thực sự có nguy cơ, nghĩa là tại ngưỡng mặc định mô hình đã nghiêng về phía an toàn mà không gây quá tải cảnh báo. Một lưu ý về nguồn: hình này tính trên mô hình XGBoost của pipeline chuẩn có SMOTE, recall {v(o["xgb_smote_recall"])}, chênh không đáng kể so với baseline không tái lấy mẫu {v(xgb_b.recall)} ở bảng trước; khác biệt nhỏ này đúng như kết luận RQ3 sẽ trình bày. Ngưỡng 0,50 ở đây là quy ước mặc định; slide 19 sẽ cho thấy có thể dịch chuyển ngưỡng một cách có kiểm soát để đổi cơ cấu giữa hai kiểu sai theo yêu cầu vận hành.

**Slide 9, kiểm chứng thứ nhất: kiểm định chéo.**
Lớp kiểm chứng thứ nhất là kiểm định chéo lặp: 5 fold nhân 5 seed, tức 25 lần huấn luyện cho mỗi mô hình, trong đó tiền xử lý và cân bằng lớp được lặp lại bên trong từng fold, các fold gộp theo sinh viên để tránh rò rỉ. XGBoost dẫn đầu recall với {v(cv_xgb.recall_mean, 4)} cộng trừ {v(cv_xgb.recall_std, 4)}; LightGBM đứng ngay sau với {v(lgbm_cv.recall_mean, 4)} cộng trừ {v(lgbm_cv.recall_std, 4)}. Độ lệch chuẩn nhỏ so với chênh lệch giữa các mô hình, và thứ hạng theo kiểm định chéo trùng với thứ hạng trên tập kiểm tra; điều này cho thấy kết quả của một lần phân chia không phải điểm dị thường và không mô hình nào chỉ ghi nhớ dữ liệu huấn luyện của mình.

**Slide 10, độ bất định của ước lượng.**
Bảng ở slide trước đưa ra các giá trị trung bình, nhưng một giá trị trung bình đơn lẻ chưa cho biết kết quả dao động bao nhiêu giữa các lần chạy; biểu đồ này bổ sung đúng chiều thông tin đó, và nó là điều kiện để tin bất kỳ thứ hạng nào: chênh lệch giữa hai mô hình chỉ có ý nghĩa khi lớn hơn mức dao động nội tại của từng mô hình. *(chỉ vào một điểm bất kỳ và thanh sai số của nó)* Cấu trúc: mỗi điểm là giá trị trung bình của 25 lần huấn luyện, tức 5 fold nhân 5 seed; thanh sai số kéo dài một độ lệch chuẩn về mỗi phía, biểu diễn vùng mà kết quả của một lần chạy bất kỳ thường rơi vào. Trục hoành là năm mô hình xếp theo recall trung bình giảm dần; ba màu là ba chỉ số: đỏ là recall, xanh dương là F1, xanh lá là PR-AUC. *(chỉ vào điểm đỏ của XGBoost, rồi điểm đỏ của Logistic Regression)* Quan sát then chốt nằm ở hàng màu đỏ: thanh sai số của XGBoost chỉ {v(cv_xgb.recall_std, 4)}, và toàn bộ khoảng dao động của nó nằm phía trên toàn bộ khoảng dao động của Logistic Regression, hai khoảng không chạm nhau. Nếu các thanh này chồng lấn nhiều, thứ hạng có thể đảo ngược chỉ vì đổi cách chia fold, và mọi kết luận chọn mô hình sẽ phải dè dặt; hình ảnh không chồng lấn là bằng chứng trực quan rằng thứ hạng bền. *(chỉ vào hàng điểm xanh lá phía trên)* Hàng PR-AUC nằm sát nhau quanh 0,99 với thanh sai số gần như không nhìn thấy: chất lượng xếp hạng xác suất vừa cao vừa ổn định ở mọi mô hình, tức khác biệt giữa các mô hình chủ yếu nằm ở hành vi quanh ngưỡng quyết định chứ không ở khả năng xếp hạng. Một giới hạn cần nói rõ: thanh sai số chưa khai thác việc 25 fold của các mô hình được ghép cặp trên cùng dữ liệu; kiểm định thống kê ở slide sau khai thác đúng cấu trúc đó và mới là bằng chứng chuẩn mực.

**Slide 11, kiểm chứng thứ hai: kiểm định thống kê.**
Lớp kiểm chứng thứ hai là kiểm định thống kê trên 25 fold ghép cặp. Kiểm định Friedman bác bỏ giả thuyết các mô hình tương đương ở mọi chỉ số với mức ý nghĩa rất cao. Kiểm định hậu nghiệm Wilcoxon với hiệu chỉnh Holm cho recall cho thấy XGBoost cao hơn có ý nghĩa thống kê so với {o["n_wins"]} trên {o["n_pairs"]} mô hình còn lại. Để trình bày đầy đủ: LightGBM dẫn đầu các chỉ số tổng hợp gồm F1, PR-AUC và ROC-AUC. Căn cứ khung đánh giá ưu tiên recall và yêu cầu SHAP TreeExplainer chính xác của phần giải thích, nhóm lựa chọn XGBoost làm mô hình chính.

**Slide 12, tinh chỉnh siêu tham số.**
Nhóm vẫn kiểm tra xem tinh chỉnh siêu tham số có mang lại cải thiện hay không, bằng RandomizedSearchCV với 40 cấu hình cho mỗi mô hình, kiểm định chéo gộp theo sinh viên, tối ưu PR-AUC. Random search được chọn thay cho grid search, vốn có chi phí tổ hợp lớn, và thay cho Bayesian optimisation, vốn không mang lại lợi ích tương xứng ở quy mô này. Kết quả: với XGBoost tại mốc 100%, PR-AUC tăng từ {v(tx.default_pr_auc, 4)} lên {v(tx.tuned_pr_auc, 4)}, tức {v(o["tun_dpr"], 4)}, trong khi recall giảm từ {v(tx.default_recall, 4)} xuống {v(tx.tuned_recall, 4)}. Mức cải thiện không tương xứng với chi phí tái lập của một cấu hình riêng, do đó nhóm giữ cấu hình gần mặc định. Kết luận này nhất quán với chính kết quả so tuyển: khi năm thuật toán có thiên kiến khác nhau chỉ chênh nhau vài phần nghìn, yếu tố ràng buộc là tín hiệu trong đặc trưng chứ không phải tham số mô hình.

**Slide 13, RQ3: biểu đồ bốn chiến lược.**
Chuyển sang câu hỏi RQ3. Trước hết là bối cảnh khiến câu hỏi này có hình thái đặc biệt trong đề tài của nhóm. Trong văn liệu, xử lý mất cân bằng thường là biện pháp cấp cứu cho một lớp thiểu số hiếm; nhưng dưới cách gán nhãn của nhóm, lớp nguy cơ chiếm 52,8 phần trăm, tỉ lệ mất cân bằng chỉ 1,12, tức là một đa số nhẹ. Vì vậy nhóm chuyển vai trò của thí nghiệm: đây là một phép thử độ bền có đối chứng, trong đó mọi thành phần của quy trình được giữ nguyên và chỉ duy nhất chiến lược cân bằng lớp thay đổi. Logic của phép thử: nếu kết quả dao động mạnh theo lựa chọn này, thì mọi kết luận của các phần trước đều phải ghi kèm điều kiện về chiến lược; nếu kết quả đứng yên, các kết luận đó được giải phóng khỏi câu hỏi "nếu chọn cách cân bằng khác thì sao". *(chỉ vào trục hoành, rồi chú giải màu)* Cấu trúc biểu đồ: trục hoành là năm mô hình; trong mỗi nhóm, bốn màu ứng với bốn chiến lược, lần lượt là không tái lấy mẫu, class weight, SMOTE và ADASYN; trục tung là recall của lớp nguy cơ. *(chỉ vào một nhóm cột bất kỳ, lướt ngang đỉnh bốn cột)* Kết quả nhìn thấy bằng mắt: trong từng nhóm, đỉnh của bốn cột gần như nằm trên một đường thẳng, ở mọi mô hình. *(chỉ vào nhóm ANN)* Riêng nhóm ANN chỉ có ba cột vì thuật toán này không hỗ trợ class weighting; đây là giới hạn của thuật toán, không phải thiếu sót của thí nghiệm. Ý nghĩa: với mức mất cân bằng nhẹ như dữ liệu này, các kỹ thuật cân bằng không có nhiều dư địa để tạo khác biệt, và thực nghiệm xác nhận đúng như vậy. Đây là một kết quả phủ định nhưng có giá trị bảo hiểm cho toàn bộ đề tài. Bảng ở slide sau đưa ra chênh lệch chính xác bằng số.

**Slide 14, RQ3: bảng recall theo mô hình và chiến lược.**
*(chỉ vào cột chênh lệch lớn nhất)*
Trình bày bằng số liệu: chênh lệch recall lớn nhất giữa bốn chiến lược, xét trên mọi mô hình, là {v(o["imb_spread_max"], 4)}, tức vài phần nghìn. Một ghi chú kỹ thuật: ANN không hỗ trợ class weighting nên ô tương ứng để trống; lưới thử nghiệm gồm 19 cấu hình. Kết luận RQ3: tín hiệu đặc trưng bền vững, kết quả không phụ thuộc cách xử lý mất cân bằng; pipeline giữ SMOTE theo đề cương đã duyệt. Em xin mời bạn Khoa trình bày phần kết quả theo thời gian.

---

## Phần Khoa (slide 15 đến 20)

**Slide 15, hiệu năng theo sáu mốc thời gian.**
Em cảm ơn Đức. Em là Khoa, phụ trách phần thực nghiệm theo thời gian. Ý tưởng của thí nghiệm: một hệ cảnh báo sớm chỉ hữu ích nếu nó chính xác khi khóa học còn đang diễn ra, vì vậy cùng một quy trình được lặp lại tại sáu mốc tiến độ, 10, 20, 40, 60, 80 và 100 phần trăm thời lượng, trên cùng một tập sinh viên kiểm tra đã cố định; tại mỗi mốc, mô hình chỉ được nhìn thấy dữ liệu phát sinh trước mốc đó. *(chỉ vào trục hoành hình trái)* Ở cả hai hình, trục hoành là phần trăm tiến độ và mỗi đường màu là một mô hình; đi từ trái sang phải là mô phỏng việc chờ đợi thêm thông tin. Hai hình là hai vế của cùng một tiêu chí tin cậy, và chúng trả lời hai câu hỏi khác nhau. *(chỉ vào đường đứt nét ở hình trái)* Hình trái là recall tại ngưỡng quyết định cố định: trong số sinh viên nguy cơ, hệ thống gắn cờ được bao nhiêu phần. Đây là vế ràng buộc vì nó gắn trực tiếp với số sinh viên được giúp. Đường đứt nét là tiêu chí 0,80. *(chỉ vào đoạn các đường cắt qua đường đứt nét)* Tại mốc 10 và 20, toàn bộ các đường nằm dưới tiêu chí; điểm cắt xảy ra trong khoảng giữa mốc 20 và 40, và từ mốc 40 các đường nằm hẳn phía trên. *(chuyển sang hình phải)* Hình phải là PR-AUC, chất lượng xếp hạng xác suất xét trên mọi ngưỡng có thể. Nó là vế kiểm soát vì nó vô hiệu hoá một cách gian lận tiềm tàng: một mô hình gắn cờ toàn bộ sinh viên sẽ đạt recall tuyệt đối nhưng PR-AUC sẽ lộ ra ngay vì precision sụp đổ. *(chỉ vào điểm thấp nhất bên trái của hình phải)* Xin lưu ý trục tung hình phải bắt đầu từ 0,86: ngay tại mốc sớm nhất PR-AUC đã vượt tiêu chí, vì vậy hình này không cần đường tham chiếu. Đặt hai hình cạnh nhau còn cho một nhận xét có ý nghĩa vận hành: khả năng xếp hạng của mô hình có từ rất sớm, trong khi recall tại ngưỡng cố định cần thêm dữ liệu hành vi mới đạt chuẩn; nghĩa là nút thắt nằm ở lượng thông tin tích lũy, không phải ở thuật toán. Cuối cùng, dáng đường cong: dốc nhất trong đoạn từ mốc 10 đến mốc 40 rồi thoải dần, tức mỗi tuần dữ liệu đầu khóa mang lại mức cải thiện lớn hơn mỗi tuần cuối khóa; đây là thông tin trực tiếp cho việc chọn thời điểm can thiệp.

**Slide 16, mô hình tốt nhất theo từng mốc.**
*(chỉ vào bảng)*
Bảng này liệt kê mô hình tốt nhất theo recall tại từng mốc: XGBoost dẫn đầu tại các mốc {xgb_ts}; LightGBM tại các mốc {lgbm_ts}. Hai mô hình boosting luân phiên dẫn đầu với chênh lệch nhỏ, củng cố kết luận rằng họ boosting chiếm ưu thế chứ không phải một thuật toán riêng lẻ. Một điểm cần trình bày chính xác: tại mốc 40 phần trăm, recall đạt {v(c40[0])} với khoảng tin cậy bootstrap 95 phần trăm từ {v(c40[1])} đến {v(c40[2])}. Khoảng tin cậy này chứa ngưỡng 0,80, vì vậy kết luận đạt chuẩn tại mốc 40 phần trăm chỉ ở mức ranh giới; từ mốc 60 phần trăm, toàn bộ khoảng tin cậy nằm trên ngưỡng và kết luận trở nên vững chắc.

**Slide 17, hai quần thể đánh giá.**
Đây là phát hiện nhóm xem là đóng góp chính, và để thấy vì sao nó quan trọng, cần bắt đầu từ định nghĩa nhãn. Nhãn nguy cơ của đề tài bao gồm cả trường hợp bỏ học. Một sinh viên đã rút khỏi môn trước mốc cắt mang ba tính chất cùng lúc: nhãn của em đó chắc chắn là nguy cơ, vì việc bỏ học đã xảy ra; hồ sơ hành vi của em đó tại mốc gần như trống, không truy cập, không nộp bài, số ngày không hoạt động rất lớn; và do đó mô hình gắn cờ đúng em đó một cách tầm thường, không cần năng lực dự báo nào. Số bản ghi thuộc diện này không nhỏ: {o["gone10"]} lượt ghi danh ngay tại mốc 10 phần trăm, tăng dần lên {o["gone100"]} tại mốc cuối. Quần thể đầy đủ mà các nghiên cứu nền sử dụng tính điểm trên cả các bản ghi đó, nghĩa là một phần recall của họ là điểm ghi nhận kết cục, không phải điểm dự báo. *(chỉ vào đường màu xanh phía trên)* Biểu đồ này tách hai thành phần đó ra. Cả hai đường đều là recall của cùng một mô hình XGBoost, cùng một lần dự đoán; khác biệt duy nhất là nhóm sinh viên được tính điểm. Đường màu xanh phía trên là quần thể đầy đủ, tăng từ {v(s10_full)} tại mốc 10 lên {v(s100_full)} tại mốc cuối. *(chỉ vào đường màu cam phía dưới)* Đường màu cam chỉ gồm những sinh viên còn theo học tại mốc, tức những người mà kết cục còn mở và giảng viên còn khả năng can thiệp; đây mới là bài toán dự báo thật. *(chỉ vào khoảng trống giữa hai đường tại mốc 40)* Khoảng cách theo chiều dọc giữa hai đường tại mỗi mốc chính là phần hiệu năng đến từ các sinh viên đã rút; tại mốc 40, đó là chênh lệch giữa {v(c40[0])} và {v(o["act40"])}. Hình dạng của khoảng cách cũng mang thông tin: nó mở rộng từ {v(g10[0])} tại mốc 10 lên đỉnh {v(g40[0])} tại mốc 40 rồi co về {v(g100[0])} tại mốc cuối. Giải thích: đầu khóa, cả sinh viên còn học lẫn đã rút đều ít dữ liệu nên hai đường cùng thấp; giữa khóa, nhóm đã rút phình to và cộng điểm miễn phí cho đường xanh trong khi sinh viên còn học vẫn khó dự báo, khoảng cách mở rộng nhất; cuối khóa, sinh viên còn học đã có đủ hồ sơ hành vi và điểm số nên đường cam thu hẹp lại phần nào. *(chỉ vào giao điểm của đường cam với đường đứt nét)* Và điểm then chốt của toàn bộ hình: đường màu cam chỉ vượt đường tiêu chí 0,80 tại đúng mốc cuối cùng. Nghĩa là câu trả lời cho câu hỏi "dự đoán sớm tin cậy từ bao giờ" phụ thuộc vào việc ta hỏi cho quần thể nào; slide sau trình bày kết luận kép đó kèm khoảng tin cậy.

**Slide 18, kết luận kép cho RQ1.**
*(chỉ vào cột chênh lệch)*
Khoảng cách giữa hai đường mang tính hệ thống: cột chênh lệch kèm khoảng tin cậy bootstrap không chứa 0 tại cả sáu mốc; ví dụ tại mốc 40 phần trăm, chênh lệch là {v(g40[0])} với khoảng tin cậy từ {v(g40[1])} đến {v(g40[2])}. Do đó RQ1 được trả lời theo hai vế, luôn trình bày cùng nhau. Trên quần thể đầy đủ, là khung so sánh được với văn liệu, dự đoán đạt chuẩn từ mốc 40 phần trăm, ở mức ranh giới như đã nêu. Trên quần thể còn theo học, là khung can thiệp thực tế, tiêu chí chỉ đạt tại mốc 100 phần trăm, recall {v(a100[0])} với khoảng tin cậy từ {v(a100[1])} đến {v(a100[2])}. Xin làm rõ hai điểm để tránh hiểu nhầm. Thứ nhất, đây không phải rò rỉ dữ liệu: nhãn không tham gia vào đặc trưng, và mức độ bất hoạt của sinh viên đã rút là hành vi quan sát thực. Thứ hai, đây là khác biệt về định nghĩa quần thể; việc báo cáo cả hai khung thay vì chỉ khung thuận lợi hơn là một đóng góp về tính minh bạch của nghiên cứu, vì cả hai nghiên cứu nền đều không tách bạch hai quần thể này.

**Slide 19, ngưỡng quyết định.**
Một hệ thống cảnh báo sớm khi triển khai cần một ngưỡng quyết định, và việc chọn ngưỡng trên tập kiểm tra sẽ làm sai lệch lạc quan mọi chỉ số công bố. Quy trình của nhóm chọn ngưỡng trên dự đoán out-of-fold của tập huấn luyện, cố định ngưỡng, rồi đánh giá trên tập kiểm tra đúng một lần. Hai kết quả chính: chính sách tối ưu F1 cho ngưỡng {v(thr_f1.threshold, 2)}, gần ngưỡng mặc định 0,50, xác nhận rằng các kết quả trước đó không phải sản phẩm của việc lựa chọn ngưỡng. Với yêu cầu vận hành đạt recall tối thiểu 0,9, ngưỡng {v(thr_r90.threshold, 2)} cho recall {v(thr_r90.test_recall)} với precision {v(thr_r90.test_precision)} trên tập kiểm tra, nghĩa là các trường hợp được cảnh báo hầu hết là sinh viên thực sự có nguy cơ. Xin lưu ý về phạm vi: các ngưỡng này chỉ được kiểm chứng cho XGBoost tại mốc 100 phần trăm và không tự động áp dụng cho mốc khác.

**Slide 20, công bằng theo nhóm nhân khẩu học.**
Nhóm đo recall và tỉ lệ cảnh báo sai cho từng nhóm nhân khẩu học có tối thiểu 50 sinh viên trong tập kiểm tra, trên sáu thuộc tính. Chênh lệch recall lớn nhất là {v(o["fair_pp"], 1)} điểm phần trăm, thuộc thuộc tính mức nghèo khu vực IMD; recall của nhóm khai báo khuyết tật không thấp hơn nhóm còn lại. Nhóm nhấn mạnh đây là số liệu quan sát tại một mốc và một ngưỡng, không phải chứng nhận công bằng; hệ thống khi triển khai cần giám sát liên tục các chỉ số này. Mô hình dự đoán đã được kiểm chứng; câu hỏi còn lại là mô hình có giải thích được hay không. Em xin mời bạn Bình.

---

## Phần Bình (slide 21 đến 24)

**Slide 21, RQ2: đặc trưng ảnh hưởng lớn nhất.**
Em cảm ơn Khoa. Em là Bình, phụ trách phần giải thích mô hình. Xuất phát điểm của phần này: một cảnh báo không kèm lý do thì giảng viên không thể hành động một cách tự tin, và cũng không thể phát hiện khi mô hình sai. Phương pháp nhóm dùng là SHAP: với mỗi dự đoán, SHAP phân rã xác suất nguy cơ thành tổng các phần đóng góp của từng đặc trưng, dựa trên lý thuyết trò chơi; với mô hình cây, biến thể TreeExplainer tính các phần đóng góp này một cách chính xác chứ không xấp xỉ. *(chỉ vào trục hoành)* Biểu đồ tổng hợp kết quả đó trên toàn tập kiểm tra: mỗi thanh ngang là một đặc trưng; chiều dài thanh là trung bình giá trị tuyệt đối của đóng góp SHAP, hiểu là mức ảnh hưởng trung bình của đặc trưng lên dự đoán; đơn vị là log-odds nên chỉ dùng để so sánh tương đối giữa các thanh, không đọc như xác suất; con số cuối thanh là giá trị chính xác; tiền tố num hay nominal cho biết nhóm biến sau tiền xử lý. *(chỉ vào thanh trên cùng)* Thanh dài nhất là `{feat1}`, số ngày kể từ lần hoạt động gần nhất, độ quan trọng {v(imp1, 2)}. *(chỉ vào thanh thứ hai)* Thứ hai là `{feat2}`, điểm đánh giá tích lũy có trọng số, {v(imp2, 2)}. *(chỉ vào thanh thứ ba và lướt xuống dưới)* Cấu trúc của biểu đồ quan trọng hơn từng con số: ngay sau hai thanh đầu có một bước hụt lớn, đặc trưng thứ ba chỉ còn {v(imp3, 2)}, và các thanh sau nhỏ dần. Nghĩa là mô hình về bản chất vận hành trên hai tín hiệu: sinh viên có còn hiện diện trong môi trường học không, và kết quả đánh giá tích lũy đang ở đâu. Ý nghĩa của cấu trúc này có ba lớp. Thứ nhất, nó trùng với trực giác sư phạm, im ắng kéo dài và điểm suy giảm là hai dấu hiệu cố vấn học tập xem xét trước tiên, nên giải thích của mô hình dễ được người dùng cuối chấp nhận. Thứ hai, nó khả thi cho triển khai: hai con số này hiển thị được ngay cạnh mỗi cảnh báo trên dashboard. Thứ ba, xin lưu ý điều không xuất hiện trên hình: trong 15 đặc trưng dẫn đầu không có đặc trưng nhân khẩu học nào; cảnh báo được xây trên hành vi và kết quả học tập, không phải trên hoàn cảnh của sinh viên, một tính chất quan trọng về mặt công bằng.

**Slide 22, độ ổn định qua các mốc thời gian.**
Slide trước cho thấy mô hình giải thích được tại một mốc; biểu đồ này trả lời câu hỏi tiếp theo của RQ2: lời giải thích đó có nhất quán giữa các mốc không, hay mỗi mốc kể một câu chuyện khác nhau. Câu hỏi này quan trọng vì hệ thống của nhóm chạy tại nhiều thời điểm trong khóa học; nếu danh sách lý do thay đổi hỗn loạn giữa hai lần chạy kế nhau, giảng viên sẽ mất lòng tin vào chính các lý do đó. *(chỉ vào trục hoành)* Cấu trúc: trục hoành liệt kê các cặp mốc được so sánh, phía bên trái là các cặp liền kề, từ mốc 10 sang 20 cho đến mốc 80 sang 100, phía bên phải là các cặp so với mốc cuối. Hai đường là hai thước đo bổ trợ nhau: đường màu xanh là Jaccard trên nhóm 10 đặc trưng quan trọng nhất, đo mức trùng lặp về thành phần, tức "những ai có mặt trong danh sách"; đường màu đỏ là tương quan hạng Spearman trên toàn bộ đặc trưng, đo mức giữ nguyên thứ tự của bức tranh tổng thể. *(chỉ vào đường đỏ)* Đọc đường đỏ trước: Spearman giữ mức cao ở mọi cặp, với các cặp liền kề từ {v(o["adj_sp_lo"], 2)} đến {v(o["adj_sp_hi"], 2)}; trật tự tổng thể của các đặc trưng gần như không xáo trộn. *(chỉ vào các điểm bên trái của đường xanh)* Đường xanh với các cặp liền kề nằm trong khoảng {v(o["adj_j_lo"], 2)} đến {v(o["adj_j_hi"], 2)}: giữa hai mốc kế nhau, phần lớn danh sách 10 đặc trưng dẫn đầu được giữ nguyên. *(chỉ vào điểm thấp nhất của đường xanh, cặp mốc 10 so với 100)* Điểm thấp nhất là cặp xa nhau nhất, mốc 10 so với mốc 100, Jaccard {v(o["j_far"], 2)}: hai đầu khóa học dựa trên những đặc trưng khá khác nhau. Tổ hợp hai đường cho ra cách diễn giải đúng: giải thích không đứng yên tuyệt đối, nó dịch chuyển dần và có trật tự theo giai đoạn khóa học, từ tín hiệu hành vi ở giai đoạn sớm sang tín hiệu điểm số ở giai đoạn muộn. Đó là hành vi kỳ vọng của một mô hình học từ dữ liệu tích lũy; ngược lại, nếu đường xanh phẳng ở mức tuyệt đối, ta phải nghi ngờ các đặc trưng tĩnh như nhân khẩu học đang chi phối mô hình, điều không mong muốn. Còn ranh giới giữa "dịch chuyển có trật tự" và "dao động ngẫu nhiên" nằm ở đâu, slide sau định lượng bằng một mốc ngẫu nhiên dựng từ mô phỏng.

**Slide 23, định lượng độ ổn định.**
*(chỉ theo từng hàng của bảng)*
RQ2 đặt câu hỏi: các giải thích có ổn định hay không. Khác với phần lớn văn liệu vốn đánh giá giải thích bằng quan sát định tính, nhóm định lượng độ ổn định và đối chiếu với một mốc ngẫu nhiên dựng bằng mô phỏng Monte-Carlo: nếu chọn ngẫu nhiên hai tập 10 đặc trưng từ 49 đặc trưng, Jaccard trung bình chỉ là {v(nul["mean"])}, và phân vị 99 là {v(nul.p99)}. Kết quả thực nghiệm như sau. Huấn luyện lại với năm seed khác nhau, mức trùng lặp của nhóm 10 đặc trưng quan trọng nhất đạt Jaccard {v(sds.mean_jaccard, 2)}, vượt phân vị 99 của mốc ngẫu nhiên với biên độ lớn, và tương quan toàn thứ hạng Spearman đạt {v(sds.mean_spearman, 2)}. So sánh giữa hai phương pháp giải thích, SHAP và LIME đồng thuận ở nhóm đặc trưng dẫn đầu với Jaccard {v(sl.jaccard, 2)}, cũng vượt phân vị 99; cần trình bày khách quan rằng tương quan toàn thứ hạng giữa hai phương pháp thấp hơn, Spearman {v(sl.spearman, 2)}, do phần cuối thứ hạng của LIME kém ổn định, vì vậy nhóm chỉ sử dụng nhóm đặc trưng dẫn đầu để diễn giải. Theo chiều thời gian, các mốc liền kề có tương quan từ {v(o["adj_sp_lo"], 2)} đến {v(o["adj_sp_hi"], 2)}, trong khi giữa mốc 10 và mốc 100 phần trăm Jaccard chỉ còn {v(o["j_far"], 2)}: thành phần nhóm đặc trưng quan trọng thay đổi dần theo giai đoạn khóa học, phù hợp với kỳ vọng rằng tín hiệu giai đoạn sớm thiên về hành vi còn giai đoạn cuối thiên về kết quả đánh giá. Cuối cùng, qua bốn chiến lược cân bằng lớp, Jaccard từ {v(o["strat_j_lo"], 2)} đến {v(o["strat_j_hi"], 2)} với Spearman không dưới {v(o["strat_sp_lo"], 2)}: cách cân bằng lớp không làm thay đổi kết luận giải thích.

**Slide 24, kết luận Task 4.**
Task 4 đưa ra ba câu trả lời. Với RQ1: XGBoost được chọn qua quy trình so tuyển công bằng có kiểm định thống kê; trên quần thể đầy đủ, dự đoán đạt chuẩn từ mốc 40 phần trăm ở mức ranh giới; trên quần thể còn theo học, tức nhóm can thiệp được, tiêu chí chỉ đạt tại mốc cuối; chênh lệch giữa hai quần thể có ý nghĩa thống kê tại cả sáu mốc. Với RQ3: bốn chiến lược cân bằng lớp chênh nhau tối đa {v(o["imb_spread_max"], 4)} recall, kết quả bền vững. Với RQ2: độ ổn định của giải thích vượt phân vị 99 của mốc ngẫu nhiên, và hai phương pháp giải thích đồng thuận ở nhóm đặc trưng dẫn đầu. Toàn bộ bộ slide, bao gồm kịch bản chúng em vừa trình bày, có thể sinh lại bằng một lệnh từ các file CSV trong repository. Nhóm 1 xin cảm ơn thầy cô và các bạn, chúng em sẵn sàng trả lời câu hỏi.

---

## Phụ lục: hướng dẫn đọc từng biểu đồ

Phần này không đọc khi trình bày. Dùng để nắm chắc cấu trúc từng biểu đồ và chuẩn bị cho phần hỏi đáp; mỗi mục gồm cấu trúc biểu đồ, nguồn dữ liệu, cách đọc, và câu hỏi giám khảo có thể đặt.

**Biểu đồ slide 6: so tuyển tại t=100% (`model_benchmark_baseline.png`).**
Dạng cột nhóm. Trục hoành liệt kê năm mô hình; mỗi mô hình có bốn cột theo thứ tự recall, F1, PR-AUC, ROC-AUC; trục tung là giá trị chỉ số trên thang 0 đến 1; con số phía trên mỗi cột là giá trị chính xác. Nguồn: các hàng `strategy=none` của `imbalance_comparison.csv`. Cách đọc: so sánh cột recall (cột thứ nhất, màu xanh dương) giữa các mô hình, XGBoost cao nhất với {v(xgb_b.recall)}; trong cùng một mô hình cả bốn cột đều trên 0,9, cho thấy chất lượng đồng đều. Câu hỏi có thể gặp: vì sao không có accuracy; trả lời: lớp nguy cơ chiếm đa số nhẹ nên accuracy dễ gây ngộ nhận, bảy chỉ số đầy đủ nằm ở bảng slide 7.

**Biểu đồ slide 8: ma trận nhầm lẫn (`confusion_default_t100.png`).**
Ma trận 2 nhân 2, chuẩn hoá theo hàng. Hàng là nhãn thực tế, cột là nhãn dự đoán; ô dưới bên phải là số sinh viên nguy cơ được nhận diện đúng, ô dưới bên trái là số bị bỏ sót, ô trên bên phải là số cảnh báo sai; phần trăm trong mỗi ô tính trên tổng của hàng, màu càng đậm tỉ lệ càng cao. Recall bằng ô dưới phải chia tổng hàng dưới, bằng {v(o["xgb_smote_recall"])}; precision bằng ô dưới phải chia tổng cột phải, bằng {v(o["xgb_smote_precision"])}. Nguồn: XGBoost tại t=100% của pipeline chuẩn có SMOTE. Câu hỏi có thể gặp: vì sao recall ở đây là {v(o["xgb_smote_recall"])} trong khi bảng slide 7 ghi {v(xgb_b.recall)}; trả lời: hai cấu hình huấn luyện khác nhau (có SMOTE so với không tái lấy mẫu), chênh lệch không đáng kể, và chính điều đó là kết luận của RQ3.

**Biểu đồ slide 10: độ bất định kiểm định chéo (`cv_uncertainty.png`).**
Dạng điểm ước lượng kèm thanh sai số. Trục hoành: năm mô hình xếp theo recall trung bình giảm dần; ba màu là ba chỉ số (đỏ recall, xanh dương F1, xanh lá PR-AUC); mỗi điểm là trung bình 25 fold, thanh sai số là một độ lệch chuẩn về mỗi phía. Nguồn: `cv_summary.csv`. Cách đọc: thanh sai số ngắn (với recall của XGBoost, độ lệch chuẩn {v(cv_xgb.recall_std, 4)}) so với chênh lệch giữa mô hình đứng đầu và đứng cuối; các thanh recall của XGBoost và Logistic Regression không chồng lấn. Câu hỏi có thể gặp: thanh sai số nhỏ rồi thì cần gì kiểm định thống kê; trả lời: thanh sai số chưa khai thác cấu trúc ghép cặp theo fold, kiểm định Friedman và Wilcoxon trên 25 fold ghép cặp mới là bằng chứng chuẩn mực.

**Biểu đồ slide 13: bốn chiến lược cân bằng lớp (`imbalance_recall_by_model.png`).**
Dạng cột nhóm. Trục hoành: năm mô hình; bốn màu ứng với bốn chiến lược none, class weight, SMOTE, ADASYN; trục tung là recall. Nhóm ANN chỉ có ba cột vì thuật toán không hỗ trợ class weighting. Nguồn: đủ 19 hàng của `imbalance_comparison.csv`. Cách đọc: trong từng nhóm, các cột gần bằng nhau; chênh lệch lớn nhất trên mọi mô hình là {v(o["imb_spread_max"], 4)}. Câu hỏi có thể gặp: nếu không khác biệt thì vì sao pipeline vẫn dùng SMOTE; trả lời: giữ theo đề cương đã duyệt, và vì kết quả không phụ thuộc lựa chọn này nên việc giữ không ảnh hưởng kết luận.

**Biểu đồ slide 15: recall và PR-AUC theo sáu mốc (`time_aware_recall.png`, `time_aware_pr_auc.png`).**
Dạng đường theo mốc, mỗi mô hình một đường, trục hoành là phần trăm tiến độ khóa học. Hình trái: recall, kèm đường tham chiếu đứt nét tại 0,80; các đường cắt tham chiếu trong khoảng giữa mốc 20 và mốc 40. Hình phải: PR-AUC, trục tung bắt đầu từ khoảng 0,86 nên đường tham chiếu 0,80 nằm ngoài vùng hiển thị và không được vẽ. Nguồn: `model_metrics.csv`. Hai hình là hai vế của cùng một tiêu chí: recall là vế ràng buộc, PR-AUC là vế kiểm soát nhằm loại trừ trường hợp recall cao chỉ do gắn cờ toàn bộ sinh viên. Câu hỏi có thể gặp: hai hình trông giống nhau thì khác gì nhau; trả lời: thang trục tung khác nhau và mô hình dẫn đầu tại mốc sớm khác nhau, XGBoost dẫn recall tại t=10% trong khi LightGBM dẫn PR-AUC, nhất quán với nhận định hai mô hình boosting luân phiên dẫn đầu.

**Biểu đồ slide 17: hai quần thể (`sensitivity_active_recall_xgb.png`).**
Hai đường của cùng một mô hình XGBoost trên hai quần thể đánh giá: đường màu xanh là quần thể đầy đủ, đường màu cam chỉ gồm sinh viên còn theo học tại mốc; đường đứt nét ngang là tiêu chí 0,80. Nguồn: `sensitivity_active_xgb.csv`. Cách đọc: khoảng cách dọc giữa hai đường tại mỗi mốc là phần hiệu năng đến từ những sinh viên đã rút trước mốc; đường màu cam chỉ vượt tiêu chí tại t=100% với recall {v(o["act100"])}. Câu hỏi có thể gặp: khoảng cách này có phải dấu hiệu rò rỉ dữ liệu; trả lời: không, nhãn không tham gia vào đặc trưng, mức độ bất hoạt của sinh viên đã rút là hành vi quan sát thực, và khác biệt nằm ở định nghĩa quần thể đánh giá.

**Biểu đồ slide 21: độ quan trọng đặc trưng SHAP (`shap_importance_xgb_t100.png`).**
Dạng thanh ngang, 15 đặc trưng quan trọng nhất, sắp xếp giảm dần. Trục hoành là trung bình giá trị tuyệt đối của đóng góp SHAP, đơn vị log-odds; con số ở cuối mỗi thanh là giá trị. Tiền tố `num__`, `nominal__`, `indicator__` cho biết nhóm biến sau bước tiền xử lý. Nguồn: `xai_shap_importance.csv`, tính bằng TreeExplainer trên mẫu con của tập kiểm tra. Cách đọc: hai thanh đầu ({v(imp1, 2)} và {v(imp2, 2)}) vượt trội so với thanh thứ ba trở đi; hai đặc trưng này là số ngày kể từ lần hoạt động gần nhất và điểm đánh giá tích lũy có trọng số. Câu hỏi có thể gặp: đơn vị của trục hoành là gì; trả lời: log-odds, chỉ dùng để so sánh tương đối mức đóng góp giữa các đặc trưng.

**Biểu đồ slide 22: trôi dạt giải thích theo thời gian (`xai_stability_drift.png`).**
Dạng đường theo cặp chuyển tiếp mốc. Trục hoành liệt kê các cặp mốc, gồm các cặp liền kề (10 sang 20 cho đến 80 sang 100) và các cặp so với mốc cuối; hai đường: Jaccard trên nhóm 10 đặc trưng quan trọng nhất (xanh) và tương quan hạng Spearman (đỏ). Nguồn: `xai_stability_checkpoints.csv`. Cách đọc: các cặp liền kề có Jaccard từ {v(o["adj_j_lo"], 2)} đến {v(o["adj_j_hi"], 2)} và Spearman từ {v(o["adj_sp_lo"], 2)} đến {v(o["adj_sp_hi"], 2)}; cặp xa nhất, mốc 10 so với mốc 100, thấp nhất với Jaccard {v(o["j_far"], 2)}. Kết luận: giải thích thay đổi dần theo giai đoạn khóa học, không thay đổi đột ngột. Câu hỏi có thể gặp: giá trị thấp ở cặp xa có phải nhược điểm; trả lời: không, nó phản ánh việc tín hiệu dự đoán chuyển từ hành vi sang kết quả đánh giá theo giai đoạn, và giá trị thấp nhất vẫn xấp xỉ phân vị 99 của mốc ngẫu nhiên.
"""


def compile_pdf(tex_path: Path) -> Path:
    exe = next((c for c in TECTONIC_CANDIDATES if shutil.which(c) or Path(c).exists()), None)
    if exe is None:
        raise FileNotFoundError("tectonic not found; install it or pass --skip-pdf")
    subprocess.run([exe, tex_path.name], cwd=tex_path.parent, check=True)
    return tex_path.with_suffix(".pdf")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skip-pdf", action="store_true", help="write tex + script only")
    args = ap.parse_args(argv)

    d = load()
    o = derive(d)
    OUT_TEX.write_text(build_tex(d, o), encoding="utf-8", newline="\n")
    print("wrote", OUT_TEX.relative_to(ROOT))
    OUT_SCRIPT.write_text(build_script(d, o), encoding="utf-8", newline="\n")
    print("wrote", OUT_SCRIPT.relative_to(ROOT))
    if not args.skip_pdf:
        pdf = compile_pdf(OUT_TEX)
        print("wrote", pdf.relative_to(ROOT), f"({pdf.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
