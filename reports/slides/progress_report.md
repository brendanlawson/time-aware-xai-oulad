
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

---
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

| Pha / Nhiệm vụ | Người | Trạng thái |
|---|---|---|
| Phase 1 — Data prep & harness | Phúc | ✅ Hoàn thành |
| Phase 2 — Benchmark 5 model @100% | Đức | ✅ Hoàn thành |
| Phase 4 — Xử lý mất cân bằng (RQ3) | Đức | ▶ Sắp tới |
| Phase 3 — Time-aware 6 mốc (RQ1) | Khoa | ▶ Sắp tới |
| Phase 5 — SHAP/LIME + độ ổn định (RQ2) | Bình | ▶ Sắp tới |
| Phase 6a/b — Dashboard & Báo cáo | Sơn / An | ▶ Sắp tới |

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

<img src="D:/dsp/reports/figures/preprocessing_sequence.png" style="max-height:430px" />

</div>
</div>

## Chia dữ liệu & chống rò rỉ — số liệu thật

<span class="kpi"><b>26,104</b>mẫu train</span> <span class="kpi"><b>6,489</b>mẫu test</span> <span class="kpi"><b>5,756</b>SV test</span> <span class="kpi"><b>0</b>SV trùng train/test</span>

| Chỉ số | Train | Test |
|---|---|---|
| Số mẫu | 26,104 | 6,489 |
| Tỉ lệ at-risk | 0.5299 | 0.5203 |

- Lệch tỉ lệ at-risk train–test chỉ **0.0096** → phân tầng đạt.
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

<img src="D:/dsp/reports/figures/model_benchmark_baseline.png" style="max-height:430px" />

</div>
</div>

## Bảng hiệu năng 5 model — baseline (đọc từ CSV)

<span class="kpi"><b>0.933</b>XGBoost · recall</span> <span class="kpi"><b>0.990</b>PR-AUC</span> <span class="kpi"><b>0.951</b>F1</span>

| Model | Recall | F1 | PR-AUC | ROC-AUC |
|---|---|---|---|---|
| XGBoost | 0.933 | 0.951 | 0.990 | 0.987 |
| LightGBM | 0.931 | 0.952 | 0.991 | 0.989 |
| ANN (MLP) | 0.923 | 0.947 | 0.990 | 0.987 |
| Random Forest | 0.921 | 0.949 | 0.990 | 0.987 |
| Logistic Reg. | 0.918 | 0.946 | 0.989 | 0.986 |

- Đánh giá trên **tập test giữ riêng**, sắp theo recall lớp at-risk.
- Khoảng cách giữa các model nhỏ → chọn theo **recall + khả năng giải thích được**.

# Kế hoạch & Kết luận

## Các việc sắp tới để hoàn thiện bài làm

| Phase — Công việc | Người | Sản phẩm / RQ |
|---|---|---|
| Phase 4 — no-resample/class-weight/SMOTE/ADASYN | Đức | Biểu đồ so sánh · RQ3 |
| Phase 3 — chạy thực nghiệm 6 mốc thời gian | Khoa | Đường cong hiệu năng · RQ1 |
| Phase 5 — SHAP/LIME + độ ổn định giải thích | Bình | Giải thích mô hình · RQ2 |
| Phase 6a — Streamlit dashboard | Sơn | App dự đoán + đóng gói |
| Phase 6b — Viết báo cáo & trực quan hoá | An | Báo cáo cuối + slide |

*Theo luồng quy trình: Đức → Khoa → Bình → Sơn / An.*

## Kết luận

- **Đã xong & tái lập:** pipeline dữ liệu (P1) + so tuyển 5 model ứng viên (P2).
- **XGBoost** dẫn đầu recall (**0.933**) ngay ở baseline; các model bám sát.
- **Kế tiếp:** P4 mất cân bằng → P3 time-aware RQ1 → P5 XAI RQ2 → P6 dashboard & báo cáo.
- Nền tảng tái lập từ `src/` + `tools/`; **19/19** kiểm thử rò rỉ ĐẠT.

### Cảm ơn đã lắng nghe!
