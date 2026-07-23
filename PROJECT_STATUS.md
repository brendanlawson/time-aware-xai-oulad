# DSP391m — Nhóm 1: Trạng thái dự án

**Đề tài:** Phát hiện sớm sinh viên có nguy cơ học tập kém bằng học máy có khả năng giải thích
**Dataset:** OULAD (Open University Learning Analytics Dataset) — 32.593 lượt ghi danh, 28.785 sinh viên duy nhất, 22 module
**Nhóm:** 6 thành viên (Phúc, Đức, Khoa, Bình, An, Sơn) — Giảng viên hướng dẫn: Nguyễn Thị Hoàng Yến
**Cập nhật:** 2026-07-19

---

## Đã hoàn thành

### Task 1 — Thu thập & Hiểu dữ liệu ✅
- Xác minh 7 bảng OULAD bằng MD5 checksum (nguồn gốc dữ liệu đảm bảo)
- Đặc tả dữ liệu + từ điển đặc trưng (bilingual EN/VI)
- Nhãn mục tiêu: nhị phân `at_risk` = {Fail, Withdrawn} chiếm 52,8% (17.208 lượt)
- 33 đặc trưng phái sinh: nhân khẩu học, hành vi VLE, kết quả đánh giá

### Task 2 — Làm sạch & Chuẩn bị dữ liệu ✅
- Xử lý 787.170 bản ghi trùng trong `studentVle` (7,4% nguồn) — quyết định giữ và cộng dồn, có tài liệu
- Phát hiện và sửa lỗi 78 dòng bài tập "banked" bị gán nhãn sai (`not_submitted` → đúng)
- Pipeline tiền xử lý leakage-safe: fit trên train, transform trên test
- 21 automated test — tất cả PASS

### Task 3 — Phân chia dữ liệu & EDA ✅
- **Phân chia theo sinh viên** (StratifiedGroupKFold): 26.104 train / 6.489 test / 5.756 sinh viên test không trùng train
- Test IDs frozen vào git (`data/splits/test_student_ids.csv`) — split guard ngăn thay đổi giữa các lần chạy
- EDA toàn diện: 35+ biểu đồ, 15+ bảng CSV (univariate, bivariate, correlation, time-aware)
- Phát hiện quan trọng: sinh viên rút lui sớm có hồ sơ hành vi gần trống (0 click, inactive dài)

### Task 4 — Mô hình hoá, Dự đoán theo thời gian & XAI ✅

#### So tuyển mô hình (RQ1 — vế 1)
| Mô hình | Recall @t=100% | F1 | PR-AUC |
|---------|--------------|-----|--------|
| **XGBoost** ← chọn | **0,931** | 0,951 | 0,990 |
| LightGBM | 0,930 | 0,952 | **0,991** |
| Random Forest | 0,922 | 0,947 | 0,988 |
| Logistic Regression | 0,918 | 0,944 | 0,984 |
| ANN | 0,920 | 0,946 | 0,988 |

Kiểm định thống kê: Friedman (p < 0,05) + Wilcoxon hậu nghiệm — XGBoost cao hơn 4/4 mô hình còn lại về recall. Chọn XGBoost vì recall cao nhất + SHAP TreeExplainer chính xác cho cây.

#### Dự đoán theo thời gian (RQ1 — vế 2)
Kết quả **kép** — hai quần thể đánh giá khác nhau về bản chất:

| Mốc | Recall (toàn bộ) | Recall (còn theo học) |
|-----|-----------------|----------------------|
| 10% | 0,719 | 0,631 |
| 20% | 0,756 | 0,647 |
| 40% | 0,811 ⚠️ ranh giới | 0,678 |
| 60% | 0,849 ✅ | 0,735 |
| 80% | 0,893 ✅ | 0,796 |
| 100% | 0,931 ✅ | 0,841 ✅ |

> ⚠️ Tại t=40%, recall 0,811 có khoảng tin cậy bootstrap [0,798; 0,824] — chứa ngưỡng 0,80. Chỉ vững chắc từ t=60%.
> Quần thể còn theo học mới là bài toán can thiệp thực tế; đạt chuẩn ≥0,80 duy nhất tại t=100%.

#### Cân bằng lớp (RQ3)
4 chiến lược: none / class weight / SMOTE / ADASYN — chênh lệch recall tối đa **0,0069** trên mọi mô hình. Kết quả bền vững, không phụ thuộc chiến lược. Pipeline giữ SMOTE theo đề cương.

> Lưu ý: at-risk chiếm 52,8% (đa số nhẹ), nên SMOTE oversampling ngược chiều (oversample not-at-risk). Đây là phép thử độ bền, không phải "cứu lớp thiểu số".

#### Giải thích mô hình (RQ2)
- **Top đặc trưng SHAP:** `days_since_last_activity` (3,57) > `weighted_score_to_date` (2,08) > `n_activity_today` (1,42)
- Không có đặc trưng nhân khẩu học trong top-15 → cảnh báo dựa trên hành vi, không phải hoàn cảnh
- **Độ ổn định:** Jaccard top-10 qua 5 seed = 0,69 (vượt phân vị 99 mốc ngẫu nhiên = 0,119); Spearman = 0,97
- SHAP vs LIME: Jaccard top-10 = 0,43 (đồng thuận ở nhóm đặc trưng dẫn đầu); LIME kém ổn định ở đuôi thứ hạng

#### Ngưỡng quyết định & Công bằng
- Ngưỡng tuned trên out-of-fold validation (không dùng test set), áp dụng test đúng 1 lần
- Chính sách recall ≥ 0,9: ngưỡng 0,86 → recall 0,900, precision 0,993 trên test
- Khoảng cách công bằng tối đa: 6,6 điểm phần trăm (theo nhóm IMD — mức nghèo khu vực)

#### Sản phẩm kèm theo
| Artifact | Trạng thái |
|----------|-----------|
| Slide Task 4 (Beamer PDF) | ✅ `reports/slides/Task4_Slides_VI.pdf` |
| Kịch bản thuyết trình | ✅ `reports/slides/Task4_Script_VI.md` |
| Sổ tay bảo vệ (6 vai) | ✅ `reports/guide/SO_TAY_BAO_VE_VI.md` |
| Dashboard Streamlit | ✅ `dashboard/app.py` |
| Empirical paper (LaTeX) | ✅ `paper/main.pdf` |
| 50+ bảng CSV (nguồn sự thật) | ✅ `reports/tables/` |
| 35+ biểu đồ | ✅ `reports/figures/` |

---

## Kết quả chính (tóm gọn)

| Câu hỏi | Kết luận |
|---------|---------|
| **RQ1: Mô hình nào tốt nhất?** | XGBoost — recall 0,931 ± 0,005 @t=100%, validated bằng Friedman + Wilcoxon |
| **RQ1: Dự đoán tin cậy từ bao giờ?** | Toàn quần thể: t=40% (ranh giới) / t=60% (vững). Còn theo học: chỉ t=100% |
| **RQ3: Cân bằng lớp có quan trọng không?** | Không — max Δrecall = 0,007. Pipeline robust với mọi chiến lược |
| **RQ2: Giải thích có ổn định không?** | Có — Spearman 0,97 qua seed; top đặc trưng bền vượt mốc ngẫu nhiên (p99) |

---

## Hướng đang làm / Còn lại

### Ưu tiên cao
- [ ] **Ký Step-0 PDF** — file `docs/08_agreements/Step0_Agreement_Nhom1.pdf` còn trắng chữ ký
- [ ] **Hoàn thiện báo cáo cuối** — draft chương Giới thiệu + Văn liệu (Sơn đã làm); cần ghép thành Word theo template (`reports/final_report/00_ASSEMBLY_MAP_VI.md`)
- [ ] **Viết phần Kết luận** — outline có trong sổ tay bảo vệ, cần prose hóa

### Ưu tiên thấp
- [ ] Commit các file Task4 chưa tracked (`Task4_Slides_VI.*`, `Task4_Script_VI.md`, `build_task4_slides.py`)
- [ ] Cập nhật bảng phân công Excel (tracker lỗi thời, thực tế 40/40 hạng mục đã xong)
- [ ] Xem xét zoom trục y biểu đồ RQ3 (`imbalance_recall_by_model.png`) từ [0,1.0] → [0,88,0,95] để chênh lệch nhỏ visible hơn khi trình bày

---

## Kiến trúc kỹ thuật

```
OULAD raw (7 CSVs, MD5-locked)
  └─► src/data/build_master_table.py    → 32.593 × 33 master
        └─► src/data/make_checkpoints.py → 6 time slices (t=10/20/40/60/80/100%)
              └─► src/features/preprocessing.py  → leakage-safe transform
                    └─► src/modeling/train.py     → 5 models × 6 checkpoints
                          ├─► src/xai/shap_explain.py  → SHAP global + local
                          ├─► src/xai/lime_explain.py  → LIME (n=100)
                          ├─► src/xai/stability.py     → Jaccard, Spearman
                          └─► dashboard/app.py          → Streamlit UI
```

**Tái lập toàn bộ:** `bash tools/renumber.sh` (~36 phút, 20+ stamp files)
**Test:** `pytest tests/` — 21/21 PASS
**Môi trường:** Python 3.13, scikit-learn 1.8.0, numpy 2.3.5 (pinned trong `environment.yml`)

---

## 7 điểm trung thực cần nắm khi bảo vệ

1. **Dual-cohort** — recall cao ở mốc sớm một phần vì sinh viên đã rút (kết cục đã xảy ra, không phải dự báo)
2. **SMOTE ngược chiều** — at-risk là đa số nhẹ; oversample not-at-risk; giữ SMOTE vì không ảnh hưởng kết luận
3. **Ngưỡng OOF** — đã sửa từ "tuned trên test" sang "tuned trên OOF validation" để tránh lạc quan thiên kiến
4. **Khoảng cách công bằng** — tối đa 6,6pp theo IMD; không có nhóm nào bị bỏ sót hệ thống
5. **Lỗi banked** — 78 dòng (0,24%); đã sửa, test bao phủ, mọi số liệu đã re-run
6. **Split guard** — test IDs frozen; `make_split` không tự ghi đè (cần `--rederive`)
7. **Provenance** — 7 file raw locked bằng MD5; `setup_raw_data.py` kiểm tra integrity
