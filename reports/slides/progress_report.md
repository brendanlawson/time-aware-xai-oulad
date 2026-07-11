
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

<img src="D:/dsp/reports/figures/model_benchmark_baseline.png" style="max-height:520px" />

## Bảng hiệu năng đầy đủ — 7 chỉ số (đọc từ CSV)

<span class="kpi"><b>0.933</b>XGBoost · recall</span> <span class="kpi"><b>0.990</b>PR-AUC</span> <span class="kpi"><b>0.951</b>F1</span> <span class="kpi"><b>0.039</b>Brier (càng thấp càng tốt)</span>

| Model | Recall | F1 | PR-AUC | ROC-AUC | Precision | Bal.Acc | Brier ↓ |
|---|---|---|---|---|---|---|---|
| XGBoost | 0.933 | 0.951 | 0.990 | 0.987 | 0.969 | 0.950 | 0.039 |
| LightGBM | 0.931 | 0.952 | 0.991 | 0.989 | 0.973 | 0.952 | 0.037 |
| ANN (MLP) | 0.923 | 0.947 | 0.990 | 0.987 | 0.972 | 0.947 | 0.040 |
| Random Forest | 0.921 | 0.949 | 0.990 | 0.987 | 0.978 | 0.949 | 0.040 |
| Logistic Reg. | 0.918 | 0.946 | 0.989 | 0.986 | 0.976 | 0.947 | 0.041 |

- Đánh giá trên **tập test giữ riêng**, sắp theo recall lớp at-risk; Brier đo chất lượng xác suất.
- Khoảng cách giữa các model **nhỏ** → cần kiểm chứng độ tin cậy trước khi kết luận.

## Độ tin cậy: CV 5-fold × 5 seed trên train

| Model | Recall (μ ± σ) | F1 (μ ± σ) | PR-AUC (μ ± σ) |
|---|---|---|---|
| XGBoost | 0.9307 ± 0.0054 | 0.9506 ± 0.0036 | 0.9901 ± 0.0008 |
| LightGBM | 0.9294 ± 0.0056 | 0.9515 ± 0.0034 | 0.9907 ± 0.0008 |
| ANN (MLP) | 0.9238 ± 0.0066 | 0.9460 ± 0.0037 | 0.9891 ± 0.0010 |
| Random Forest | 0.9199 ± 0.0051 | 0.9486 ± 0.0031 | 0.9887 ± 0.0010 |
| Logistic Reg. | 0.9184 ± 0.0053 | 0.9453 ± 0.0031 | 0.9888 ± 0.0010 |

- 25 lần fit/model (pipeline đầy đủ, tiền xử lý + cân bằng lặp lại **trong từng fold** — không rò rỉ).
- Độ lệch chuẩn rất nhỏ (σ ≈ 0,005) → kết quả **ổn định**, không ăn may theo cách chia fold.
- Thứ hạng CV khớp thứ hạng test → baseline đáng tin.

## Xếp hạng có ý nghĩa thống kê không?

| Chỉ số | Model tốt nhất (mean rank) | Friedman χ² | p-value |
|---|---|---|---|
| recall | XGBoost | 65.2 | 2.4e-13 |
| f1 | LightGBM | 82.1 | 6.1e-17 |
| pr_auc | LightGBM | 83.1 | 3.9e-17 |
| roc_auc | LightGBM | 80.4 | 1.4e-16 |

- **Friedman** trên 25 fold ghép cặp: mọi chỉ số đều p ≪ 0,05 → khác biệt giữa các model là **thật**, không phải nhiễu.
- Post-hoc **Wilcoxon (hiệu chỉnh Holm)** trên recall: XGBoost thắng **4/4** cặp so sánh có ý nghĩa.
- **XGBoost** dẫn recall · **LightGBM** dẫn F1/PR-AUC/ROC-AUC → chọn theo mục tiêu bài toán (recall-first) + **giải thích được** (TreeExplainer, phục vụ Phase 5).

# Kế hoạch & Kết luận

## Các việc sắp tới để hoàn thiện bài làm

| Phase — Công việc | Người | Sản phẩm / RQ |
|---|---|---|
| Phase 4 — no-resample/class-weight/SMOTE/ADASYN | Đức | Biểu đồ so sánh · RQ3 |
| Phase 3 — chạy thực nghiệm 6 mốc thời gian | Khoa | Đường cong hiệu năng · RQ1 |
| Phase 5 — SHAP/LIME + độ ổn định giải thích | Bình | Giải thích mô hình · RQ2 |
| Phase 6a — Streamlit dashboard | An | App dự đoán + đóng gói |
| Phase 6b — Introduction / Literature Review | Sơn | Mở đầu + tổng quan + tài liệu |

*Theo luồng quy trình: Đức → Khoa → Bình → An (dashboard) / Sơn (lit review); báo cáo cuối do Khoa tổng hợp.*

## Kết luận

- **Đã xong & tái lập:** so tuyển 5 model ứng viên (Phase 2), trên nền dữ liệu đã chốt ở Task 3.
- **XGBoost** dẫn đầu recall (**0.933**) ngay ở baseline; các model bám sát.
- **Kế tiếp:** P4 mất cân bằng → P3 time-aware RQ1 → P5 XAI RQ2 → P6 dashboard & báo cáo.
- Nền tảng tái lập từ `src/` + `tools/`; **19/19** kiểm thử rò rỉ ĐẠT.

### Cảm ơn đã lắng nghe!
