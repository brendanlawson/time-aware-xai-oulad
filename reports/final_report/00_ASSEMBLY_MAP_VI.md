# Bản đồ lắp ráp báo cáo cuối — DSP391m Nhóm 1

> Dành cho Khoa (Report Coordinator). Mỗi mục của Project Template ánh xạ tới
> đúng nguồn liệu trong repo — lắp theo thứ tự, mọi con số chép từ CSV, không gõ tay.
> **Trước khi chốt số: chạy checklist renumber** (SO_TAY_BAO_VE_VI.md mục 6).

| # | Mục báo cáo (template) | Người phụ trách | Nguồn liệu trong repo | Trạng thái |
|---|---|---|---|---|
| 1 | Introduction & Background | Sơn | `reports/final_report/1_Introduction_and_Literature_Review_EN.md` (mục 1) | ✅ bản thảo 2026-07-12 |
| 2 | Literature Review | Sơn | cùng file trên (mục 2); đối chiếu `docs/06_references/Base_Studies_Comparison_EN.md` | ✅ bản thảo 2026-07-12 |
| 3 | Data Description | Phúc | `docs/01_data_specification/Data_Specification_EN.md`, `Data_Dictionary_EN.md`, notebook `00_data_understanding` + `reports/data_understanding/verified_numbers.json` | ✅ có sẵn |
| 4 | Data Cleaning & Preprocessing | Phúc + Đức | `docs/03_cleaning/Cleaning_Methods_EN.md` (kèm §duplicates + errata banked), `docs/04_transformation/*`, notebook `01`, `04` | ✅ có sẵn |
| 5 | Methodology — Data Splitting Strategy | Phúc | `docs/05_splitting/Split_Strategy_Analysis_EN.md` + `reports/tables/split_report.csv` | ✅ có sẵn |
| 6 | Methodology — Model Selection | Đức | slide script `reports/slides/Progress_Report_Script_VI.md` (slide 3–4) + `reports/slides/progress_report.md` | ✅ có sẵn |
| 7 | Model Development (Architecture, Training Procedure) | Đức | như trên (slide 4–5) + `src/modeling/train.py` docstrings + `reports/tables/imbalance_comparison.csv` (RQ3-accuracy) | ✅ có sẵn |
| 8 | Model Evaluation — Cross-Validation | Khoa | `reports/tables/cv_summary.csv`, `model_friedman.csv`, `model_pairwise_wilcoxon.csv` | ✅ số có sẵn, cần viết lời |
| 9 | Model Evaluation — Hyperparameter Tuning | Bình | `reports/tables/tuning_results.csv` (kết luận trung thực: gần như không cải thiện) | ✅ số có sẵn, cần viết lời |
| 10 | Results Interpretation & Visualization | Khoa (tổng hợp) | `time_aware_*.png` + `time_aware_best.csv` (RQ1 **viết kiểu dual-cohort**: kèm `sensitivity_active_xgb.csv` + `sensitivity_active_recall_xgb.png`); `threshold_validation.csv`; `fairness_subgroups.csv` + `fairness_gaps.csv` | ✅ số có sẵn, cần viết lời |
| 11 | XAI & Explanation Stability (RQ2/RQ3) | Bình | `xai_shap_importance.csv`, `xai_shap_vs_lime.csv` (nêu giới hạn n=30), `xai_stability_seeds.csv`, `xai_stability_checkpoints.csv`, `xai_stability_strategies.csv` + hình `shap_*`, `lime_*`, `xai_stability_drift` | ✅ số có sẵn, cần viết lời |
| 12 | Conclusion & Recommendations | Khoa | SO_TAY mục 1 (câu trả lời 3 RQ) + mục 3 (giới hạn trung thực) | ⬜ viết mới |
| 13 | Appendix — Dashboard architecture | An | `dashboard/app.py` (docstring mô tả kiến trúc UI-mỏng/logic-trong-src; chạy `streamlit run dashboard/app.py`) | ✅ app hoàn thành 2026-07-12 |
| 14 | References (IEEE) | Sơn | mục References trong `1_Introduction_and_Literature_Review_EN.md` | ✅ bản thảo |

## Nhắc trước khi nộp

1. Chạy **renumber** (SO_TAY mục 6) → mọi bảng/hình tự khớp lại → chép số vào Word.
2. Ký thật `docs/08_agreements/Step0_Agreement_Nhom1.pdf` (đang trống ngày + chữ ký).
3. Cập nhật xlsx phân công trong `references/task/`.
4. RQ1 trong mọi mục phải nói kèm cohort (quy tắc ở `docs/01_data_specification/Target_Variable_Definition_EN.md` §5).
