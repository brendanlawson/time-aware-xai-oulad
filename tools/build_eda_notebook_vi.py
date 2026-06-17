"""Generate a complete Vietnamese EDA notebook matching the Task-3 presentation.

The notebook narrates Chapter-4 EDA in Vietnamese following the slide deck order
(Slide 18-22: mục tiêu → univariate → bivariate → multivariate/leakage →
time-aware), runs the real analysis through the tested ``src.eda.eda`` module
(figures/tables never drift), and surfaces the exact numbers used on the slides.

Run:  python tools/build_eda_notebook_vi.py
Output: notebooks/EDA_Task3_VI.ipynb
"""

from pathlib import Path

import nbformat as nbf
from nbformat.v4 import new_code_cell, new_markdown_cell

NB_DIR = Path(__file__).resolve().parents[1] / "notebooks"

BOOT = (
    "import sys, json\n"
    "from pathlib import Path\n"
    "import pandas as pd\n"
    "from IPython.display import Image, display\n"
    "ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()\n"
    "sys.path.insert(0, str(ROOT))\n"
    "TABLES = ROOT / 'reports' / 'tables'\n"
    "FIGS = ROOT / 'reports' / 'figures'\n"
    "pd.set_option('display.max_columns', 40)\n"
    "pd.set_option('display.width', 160)\n"
    "from src.eda import eda\n"
    "print('Sẵn sàng — thư mục gốc:', ROOT.name)"
)


def fig(name: str, caption: str = "") -> str:
    line = f"display(Image(filename=str(FIGS / '{name}.png')))"
    return line


cells = []
md = lambda *t: cells.append(new_markdown_cell("".join(t)))
code = lambda t: cells.append(new_code_cell(t))

# --------------------------------------------------------------------------- #
# Title & intro
# --------------------------------------------------------------------------- #
md(
    "# Phân tích khám phá dữ liệu (EDA) — OULAD\n\n",
    "**DSP391m · Nhóm 1 · Đại học FPT** · Đề tài: *Time-Aware Explainable ML for "
    "Early At-Risk Student Prediction on OULAD* · GVHD: Nguyễn Thị Hoàng Yến\n\n",
    "> Notebook này là **bản chạy thật** của khối EDA trong báo cáo Task 3, khớp với "
    "slide **18–22** và kịch bản thuyết trình (`reports/Task3_Speaker_Script_VI.md`). "
    "Mọi phân tích gọi qua module đã kiểm thử `src/eda/eda.py` nên hình và bảng **không "
    "bị lệch** so với code; các con số in ra chính là số dùng trên slide.\n\n",
    "**Mạch phân tích (bốn góc nhìn):** từng biến một (univariate) → biến theo nhãn "
    "(bivariate) → các biến với nhau & kiểm tra rò rỉ (multivariate) → theo thời gian "
    "(time-aware, RQ1); kèm chất lượng dữ liệu, phân phối lớp, và tín hiệu sinh viên "
    "rút môn.",
)

# --------------------------------------------------------------------------- #
# 0. Mục tiêu & nạp dữ liệu (Slide 18)
# --------------------------------------------------------------------------- #
md(
    "## 0. Mục tiêu EDA & nạp dữ liệu  *(Slide 18)*\n\n",
    "**Làm gì:** hiểu dữ liệu (≈32.593 bản ghi, 33 biến, 3 nhóm), kiểm tra chất lượng, "
    "và tìm biến phân biệt được sinh viên nguy cơ.\n\n",
    "**Vì sao:** EDA không phải để trang trí — mỗi biểu đồ dẫn tới một quyết định: "
    "*chọn đặc trưng* hoặc *kiểm chứng không rò rỉ*.\n\n",
    "**Kết quả:** ba kết luận định hướng (xem mục cuối). Dùng `master_raw` (t=100%) cho "
    "univariate/bivariate/tương quan, và 6 bộ checkpoint cho phân tích thời gian.",
)
code(BOOT)
code(
    "master = eda.load_master()\n"
    "checkpoints = eda.load_checkpoints()\n"
    "print('master:', master.shape, '| 6 checkpoint gộp:',\n"
    "      None if checkpoints is None else checkpoints.shape)\n"
    "print('Số nhóm biến: nhân khẩu học / tương tác / điểm số')\n"
    "master.head(3)"
)

# --------------------------------------------------------------------------- #
# Chất lượng dữ liệu
# --------------------------------------------------------------------------- #
md(
    "## 1. Chất lượng dữ liệu\n\n",
    "Chỉ **ba cột** có giá trị khuyết: `date_unregistration` (thiếu cấu trúc — đa số "
    "không rút môn, không dùng làm đặc trưng), `imd_band` (1.111 → `Unknown`), "
    "`date_registration` (45 → trung vị train). Không cột đặc trưng nào thiếu đáng kể.",
)
code(
    "q = eda.data_quality(master)\n"
    "print(json.dumps(q, indent=2, ensure_ascii=False))\n"
    "display(pd.DataFrame.from_dict(q['columns_with_missing'], orient='index',\n"
    "        columns=['số_thiếu']))\n"
    + fig("quality_missingness")
)

# --------------------------------------------------------------------------- #
# 2. Univariate (Slide 19)
# --------------------------------------------------------------------------- #
md(
    "## 2. Phân tích từng biến — Univariate  *(Slide 19)*\n\n",
    "**Làm gì:** histogram + KDE và boxplot cho mỗi biến số.\n\n",
    "**Vì sao:** phần lớn biến click **lệch phải rất mạnh** — đuôi nặng là ngoại lai "
    "*thật* (hành vi học thật), nên không xóa mà biến đổi `log1p`.\n\n",
    "**Kết quả:** `clicks_resource` có **skew ≈ 34,7**, **kurtosis ≈ 2.125** — bằng "
    "chứng thực nghiệm cho `log1p`; và vì dữ liệu không chuẩn nên các bước sau dùng "
    "**kiểm định phi tham số Mann–Whitney**.",
)
code(
    "uni = eda.univariate(master)\n"
    "num = pd.read_csv(TABLES / 'univariate_numeric.csv', index_col=0)\n"
    "print('clicks_resource  -> skew = {:.2f} | kurtosis = {:.2f}'.format(\n"
    "      num.loc['clicks_resource','skew'], num.loc['clicks_resource','kurtosis']))\n"
    "print('5 biến lệch nhất:', json.dumps(uni['most_skewed'], ensure_ascii=False))\n"
    "display(num[['mean','std','min','50%','max','skew','kurtosis']])"
)
code(fig("univariate_hist_kde"))
code(fig("univariate_boxplots"))
code(fig("univariate_categorical_freq"))

# --------------------------------------------------------------------------- #
# 3. Phân phối lớp (Slide 20 intro)
# --------------------------------------------------------------------------- #
md(
    "## 3. Phân phối lớp & mất cân bằng  *(Slide 20)*\n\n",
    "Tỉ lệ at-risk quan sát được là **52,8%** (tỉ số mất cân bằng **1,12**) — đa số "
    "*nhẹ*, là số thật của bộ dữ liệu chứ không phải 68/32. Vì bỏ sót sinh viên nguy cơ "
    "là sai lầm đắt nhất, chỉ số chính là **PR-AUC & recall** lớp at-risk.",
)
code(
    "td = eda.target_distribution(master)\n"
    "print(json.dumps(td, indent=2, ensure_ascii=False))\n"
    + fig("target_distribution")
)

# --------------------------------------------------------------------------- #
# 4. Bivariate numeric (Slide 20)
# --------------------------------------------------------------------------- #
md(
    "## 4. Biến số theo nhãn — Bivariate  *(Slide 20)*\n\n",
    "**Làm gì:** với mỗi biến số, đo **Cohen's d** + kiểm định **Mann–Whitney** (hiệu "
    "chỉnh Benjamini–Hochberg).\n\n",
    "**Vì sao:** ở n≈32k, p-value gần như luôn nhỏ → **xếp hạng bằng độ lớn hiệu ứng**, "
    "không bằng p.\n\n",
    "**Kết quả:** ba biến mạnh nhất thuộc tương tác & điểm — `days_since_last_activity` "
    "**d=2,55** (171 vs 14 ngày), `n_assessments_submitted` **2,05** (2,3 vs 8,6 bài), "
    "`weighted_score_to_date` **1,96**. **19/19 biến có ý nghĩa** → tín hiệu nằm ở hành "
    "vi & điểm, không phải nhân khẩu học.",
)
code(
    "bv = eda.numeric_vs_target(master)\n"
    "tb = pd.read_csv(TABLES / 'bivariate_numeric_tests.csv')\n"
    "top5 = tb.sort_values('cohens_d', ascending=False).head(5)\n"
    "display(top5[['feature','group','mean_not_at_risk','mean_at_risk','cohens_d','p_adj_bh']])\n"
    "r = tb.set_index('feature')\n"
    "print('days_since_last_activity: at-risk {:.0f} ngày  vs  not-at-risk {:.0f} ngày'.format(\n"
    "      r.loc['days_since_last_activity','mean_at_risk'], r.loc['days_since_last_activity','mean_not_at_risk']))\n"
    "print('n_assessments_submitted : at-risk {:.1f} bài   vs  not-at-risk {:.1f} bài'.format(\n"
    "      r.loc['n_assessments_submitted','mean_at_risk'], r.loc['n_assessments_submitted','mean_not_at_risk']))\n"
    "print('Số biến có ý nghĩa (q<0.05): {}/{}'.format(bv['n_significant'], bv['n_tested']))"
)
code(fig("bivariate_effect_sizes"))
code(fig("bivariate_top_boxplots"))

# --------------------------------------------------------------------------- #
# 5. Bivariate categorical
# --------------------------------------------------------------------------- #
md(
    "## 5. Biến phân loại theo nhãn  *(Slide 20 — phần phụ)*\n\n",
    "Chi-square có ý nghĩa nhưng **Cramér's V** đều nhỏ: `highest_education` (0,15) và "
    "`imd_band` (0,15) dẫn đầu, `gender` (0,02) gần như không đáng kể → nhân khẩu học "
    "mang tín hiệu độc lập hạn chế, **giữ để phân tích công bằng** hơn là để dự đoán.",
)
code(
    "cv = eda.categorical_vs_target(master)\n"
    "print(json.dumps(cv, indent=2, ensure_ascii=False))\n"
    "display(pd.read_csv(TABLES / 'bivariate_categorical_tests.csv'))\n"
    + fig("bivariate_categorical_rate")
)

# --------------------------------------------------------------------------- #
# 6. Multivariate & leakage (Slide 21)
# --------------------------------------------------------------------------- #
md(
    "## 6. Tương quan, đa cộng tuyến & kiểm tra rò rỉ — Multivariate  *(Slide 21)*\n\n",
    "**Làm gì:** ma trận Pearson + Spearman; tương quan với nhãn; kiểm tra rò rỉ.\n\n",
    "**Vì sao:** rò rỉ là bước **bắt buộc** — nếu một biến |r| ≥ 0,95 với nhãn thì rất "
    "đáng nghi chứa sẵn đáp án.\n\n",
    "**Kết quả:** tương quan mạnh nhất với nhãn là `days_since` **+0,78** (khớp Cohen's d "
    "→ hai phương pháp độc lập, cùng kết luận); **không biến nào |r| ≥ 0,95 → không rò "
    "rỉ**; 2 cặp đa cộng tuyến ≥ 0,8 (để dành RQ2).",
)
code(
    "co = eda.correlation(master)\n"
    "ct = pd.read_csv(TABLES / 'correlation_with_target.csv', index_col=0)\n"
    "display(ct)\n"
    "mx = ct['pearson_r_with_at_risk'].abs().max()\n"
    "print('Đa cộng tuyến |r|>=0.8:', json.dumps(co['multicollinear_ge_0.8'], ensure_ascii=False))\n"
    "print('|r| lớn nhất với nhãn = {:.3f}  ->  {}'.format(\n"
    "      mx, 'KHÔNG rò rỉ (ngưỡng 0.95)' if mx < 0.95 else 'CẢNH BÁO rò rỉ'))\n"
    "assert mx < 0.95, 'Phát hiện đặc trưng nghi rò rỉ!'\n"
    "print('Nghi rò rỉ (>=0.95):', co['leakage_suspects_ge_0.95'])"
)
code(fig("corr_pearson"))
code(fig("corr_spearman"))
code(fig("corr_with_target"))

# --------------------------------------------------------------------------- #
# 7. Time-aware (Slide 22)
# --------------------------------------------------------------------------- #
md(
    "## 7. Phân tích theo thời gian — khi nào tín hiệu xuất hiện?  *(Slide 22 · RQ1)*\n\n",
    "**Làm gì:** đo |Cohen's d| của từng biến tại 6 mốc 10%→100%.\n\n",
    "**Vì sao:** đây là phân tích đặc thù của bài toán *time-aware* — xác định mốc sớm "
    "nhất đáng tin để dự đoán (RQ1).\n\n",
    "**Kết quả:** sức phân biệt **tăng dần đều**; mốc đầu đạt d≥0,8: `n_days_active` từ "
    "**10%**, điểm/số bài nộp từ **20%**, `days_since` từ **40%** → **dự đoán sớm khả "
    "thi từ ~20% khóa học**.\n\n",
    "> ⚠️ Lưu ý nhất quán: d của `days_since` trong bảng theo-mốc (tính trên "
    "`dataset_t100`, đã cắt click sau mốc) là **1,56**, khác d=2,55 ở mục 4 (tính trên "
    "`master_raw`). Khi thuyết trình hãy trích `weighted_score`/`n_assessments` (khớp "
    "tuyệt đối giữa hai bảng) — xem Q&A #6.",
)
code(
    "ta = eda.time_aware(checkpoints)\n"
    "disc = pd.read_csv(TABLES / 'discrimination_by_checkpoint.csv', index_col=0)\n"
    "display(disc)\n"
    "print('Mốc sớm nhất đạt d>=0.8:')\n"
    "print(json.dumps(ta['earliest_checkpoint_d_ge_0.8'], indent=2, ensure_ascii=False))"
)
code(fig("time_mean_trajectory"))
code(fig("time_discrimination_curve"))

# --------------------------------------------------------------------------- #
# 8. Withdrawn signal (Slide 22)
# --------------------------------------------------------------------------- #
md(
    "## 8. Tín hiệu cảnh báo sớm của sinh viên Withdrawn  *(Slide 22 · Phương án A)*\n\n",
    "Dữ liệu xác nhận rút môn tạo **tín hiệu thật**, không phải nhiễu: trung vị số ngày "
    "không hoạt động là **11** (not-at-risk), **116** (Fail), **233** (Withdrawn); trung "
    "vị tổng click giảm từ **1.425** xuống **89**. Sự sụp đổ hoạt động này là điều khiến "
    "phát hiện sớm khả thi.",
)
code(
    "wd = eda.withdrawn_analysis(master)\n"
    "print(json.dumps(wd, indent=2, ensure_ascii=False))\n"
    + fig("withdrawn_activity_decay")
)

# --------------------------------------------------------------------------- #
# 9. Kết luận
# --------------------------------------------------------------------------- #
md(
    "## 9. Kết luận EDA & hàm ý cho mô hình\n\n",
    "1. **Tín hiệu sớm (RQ1).** Đặc trưng hành vi/kết quả phân biệt hai lớp từ 10–20% và "
    "mạnh dần đơn điệu; 40–60% là vùng ổn định, khả thi.\n",
    "2. **Hành vi ≫ nhân khẩu học (RQ1/RQ2).** Tương tác/kết quả đạt d > 2, còn liên hệ "
    "nhân khẩu học nhỏ (Cramér's V ≤ 0,15) → SHAP/LIME kỳ vọng xếp đặc trưng hành vi cao "
    "nhất.\n",
    "3. **Mất cân bằng nhẹ (RQ3).** 52,8% at-risk → RQ3 định lượng SMOTE/ADASYN/class-"
    "weight bằng PR-AUC/recall.\n",
    "4. **Đặc trưng tương quan cao (RQ2).** Các biến tương tác đa cộng tuyến có thể làm "
    "độ quan trọng giải thích kém ổn định — yếu tố chỉ số ổn định phải tính đến.\n",
    "5. **Không rò rỉ.** Không biến nào tương quan ~hoàn hảo với nhãn; phép cắt thời gian "
    "loại sự kiện tương lai → ước lượng trên test đáng tin.\n\n",
    "*Ba kết luận trọng tâm cho slide:* tín hiệu nằm ở **tương tác + điểm**; **không rò "
    "rỉ**; **dự đoán sớm khả thi từ ~20% khóa học**.",
)

nb = nbf.v4.new_notebook()
nb.cells = cells
nb.metadata = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
}

out = NB_DIR / "EDA_Task3_VI.ipynb"
nbf.write(nb, out)
print("wrote", out, "(", len(cells), "cells )")
