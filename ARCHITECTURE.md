# DSP391m — Kiến trúc hệ thống

> Phát hiện sớm sinh viên có nguy cơ học tập kém bằng học máy có khả năng giải thích
> Dataset: OULAD (Open University Learning Analytics) — FPT University, Nhóm 1

---

## Tổng quan

Hệ thống dự đoán sinh viên at-risk theo thời gian thực tại 6 mốc tiến độ khoá học. Pipeline leakage-safe: dữ liệu test không bao giờ chạm vào quá trình huấn luyện hoặc preprocessing.

```
OULAD raw (7 CSVs, MD5-locked)
        │
        ▼
[Build] build_master_table.py     → 32.593 lượt ghi danh × 33 đặc trưng
        │
        ▼
[Split] make_split.py             → frozen student-level split (test_student_ids.csv ← git truth)
        │                            26.104 train / 6.489 test / 5.756 sinh viên test
        ▼
[Slice] make_checkpoints.py       → 6 time slices: t ∈ {10, 20, 40, 60, 80, 100}%
        │
        ▼
[Feat]  preprocessing.py          → ColumnTransformer fit-on-train-only
        │                            28 đặc trưng đã mã hoá (num, ordinal, nominal, binary, indicator)
        ▼
[Train] train.py                  → 5 mô hình × 6 checkpoints = 30 bundles (.joblib)
        │                            SMOTE trên train fold only; atomic write; resumable
        ▼
        ├─► [XAI] shap_explain.py → SHAP TreeExplainer (exact), global + local
        │         lime_explain.py → LIME (n=100 perturbations)
        │         stability.py   → Jaccard top-k, Spearman, vs Monte-Carlo null
        │
        ├─► [Eval] eval_analysis.py → Friedman + Wilcoxon-Holm, bootstrap CI (1000 resamples)
        │          threshold.py    → OOF threshold tuning; fairness by IMD band
        │
        ├─► [Supp] make_ds_supplement.py → rule baseline · calibration · feature ablation
        │
        └─► [Dashboard] app.py    → Streamlit: dual-cohort view, SHAP waterfall, risk table
```

---

## Lớp dữ liệu

| Nguồn | Vai trò | Bảo vệ |
|---|---|---|
| `data/raw/` (7 CSV) | Ground truth gốc, MD5-locked | `setup_raw_data.py` kiểm tra integrity |
| `data/splits/test_student_ids.csv` | Frozen test split | Split guard: `make_split` không ghi đè mặc định |
| `data/checkpoints/t{10..100}/` | 6 time slices | Tái tạo từ master table, deterministic |
| `reports/tables/*.csv` | Nguồn sự thật cho mọi con số | **Không được hand-edit** — rerun tools/ |
| `models/*.joblib` | Bundle (preprocessor + model) | Atomic write; `predict.py` load theo tên + t |

### Nhãn mục tiêu

```
at_risk = 1  ← Fail hoặc Withdrawn  (17.208 lượt, 52,8%)
at_risk = 0  ← Pass hoặc Distinction (15.385 lượt, 47,2%)
```

Lớp at-risk là **đa số nhẹ** (imbalance ratio 1,12). SMOTE trong pipeline oversample not-at-risk — đây là phép thử độ bền, không phải xử lý mất cân bằng nghiêm trọng.

---

## Pipeline huấn luyện

### Đặc trưng đầu vào (28 sau mã hoá)

| Nhóm | Đặc trưng tiêu biểu | Xử lý |
|---|---|---|
| Hành vi VLE | `days_since_last_activity`, `n_clicks_total`, `n_activity_today` | StandardScaler |
| Kết quả đánh giá | `weighted_score_to_date`, `n_submitted` | StandardScaler |
| Nhân khẩu học | `highest_education`, `imd_band`, `age_band` | OrdinalEncoder |
| Định danh module | `code_module`, `code_presentation`, `region` | OneHotEncoder |
| Nhị phân | `gender`, `disability` | BinaryEncoder |
| Chỉ số | `not_submitted` | PassThrough |

### Mô hình được đánh giá

```
LogisticRegression · RandomForest · XGBoost* · LightGBM · ANN (MLPClassifier)

* XGBoost được chọn: recall cao nhất (0,931 @t=100%) + TreeExplainer chính xác cho cây
```

### Cân bằng lớp (RQ3)

4 chiến lược: none / class_weight / SMOTE / ADASYN
→ Chênh lệch recall tối đa **0,0069** trên mọi mô hình. Pipeline bền vững.

---

## Đánh giá theo thời gian (Dual-Cohort)

```
Mốc     Recall (toàn bộ)    Recall (còn theo học)    Ghi chú
10%         0,719                 0,631
20%         0,756                 0,647
40%         0,811                 0,678               ⚠ ranh giới
60%         0,849                 0,735               ✓ vững (toàn bộ)
80%         0,893                 0,796
100%        0,931                 0,841               ✓ vững (cả hai)
```

**Tại sao hai cột?** Recall toàn bộ bao gồm sinh viên đã rút trước mốc → kết cục đã xảy ra, không phải dự báo. Quần thể còn theo học mới là bài toán can thiệp thực tế.

Bootstrap CI (1000 resamples, student-level). Friedman p < 0,05; Wilcoxon-Holm xác nhận XGBoost vượt 4/4 mô hình còn lại về recall.

---

## Lớp XAI

### SHAP (giải thích toàn cục và cá nhân)

```
TreeExplainer (exact)  →  global importance (mean |SHAP|)
                       →  local waterfall cho từng sinh viên
                       →  stability: Jaccard top-10 = 0,69 (vs random null p99 = 0,119)
                          Spearman = 0,97 qua 5 seed
```

Top 3 đặc trưng @t=100%:

| Đặc trưng | SHAP trung bình | Ý nghĩa hành động |
|---|---|---|
| `days_since_last_activity` | 3,57 | Gửi nhắc nhở sau >14 ngày không đăng nhập |
| `weighted_score_to_date` | 2,08 | Cảnh báo khi điểm tích luỹ < 35% |
| `n_activity_today` | 1,42 | Phát hiện "crash" hoạt động đột ngột |

### LIME (cross-check cục bộ)

```
LIME (n=100 perturbations)  →  Jaccard SHAP/LIME top-10 = 0,43
                             →  Đồng thuận ở top features; LIME kém ổn định ở đuôi thứ hạng
```

---

## Phân tích bổ sung (make_ds_supplement.py)

### Rule-based baseline

Grid-search trên `days_since_last_activity` × `weighted_score_to_date`:

```
t=10%:  rule recall 0,999 vs XGBoost 0,719  ← rule thắng (withdrawn trivially detectable)
t=100%: rule recall 0,855 vs XGBoost 0,931  ← XGBoost thắng +0,075
```

**Kết luận:** Hybrid policy hợp lý — dùng rule ở t<40% (đơn giản, nhanh), dùng XGBoost ở t≥40%.

### Calibration

```
ECE: 0,018 – 0,042 (tốt)   MCE: 0,080 – 0,161 (một số bin xác suất cao bị under-predict)
→ Xác suất đầu ra đáng tin làm risk score, hạn chế đọc literal ở vùng >0,85
```

### Feature ablation

```
k=3:  recall 0,913     k=5:  recall 0,932 ← vượt full model (0,930)
k=28: recall 0,930     → Triển khai chỉ cần top 5 features
```

---

## Cấu trúc repository

```
dsp/
├── data/
│   ├── raw/                    # 7 CSV gốc (MD5-locked)
│   └── splits/                 # test_student_ids.csv (frozen)
├── src/
│   ├── data/                   # build_master_table, make_checkpoints, make_split
│   ├── features/               # preprocessing.py (ColumnTransformer)
│   ├── modeling/               # train.py, predict.py, threshold.py
│   ├── xai/                    # shap_explain, lime_explain, stability
│   └── eda/                    # plot_style, univariate, bivariate charts
├── tools/
│   ├── make_eval_analysis.py   # Friedman, Wilcoxon, bootstrap CI
│   ├── make_task4_figures.py   # headline figures cho Task 4
│   ├── make_ds_supplement.py   # rule baseline · calibration · ablation
│   ├── build_final_report.py   # assembles report FROM CSVs (không hand-edit)
│   └── renumber.sh             # tái lập toàn bộ pipeline (~36 phút)
├── models/                     # bundles: {model}_t{t}.joblib
├── reports/
│   ├── figures/                # 35+ PNG (300 dpi)
│   └── tables/                 # 50+ CSV (nguồn sự thật cho mọi con số)
├── dashboard/app.py            # Streamlit UI
├── paper/main.tex              # IEEE IEEEtran format
└── tests/                      # 21 test — pytest, all PASS
```

---

## Khởi chạy

```bash
# Môi trường
conda activate base

# Tái lập toàn bộ pipeline
bash tools/renumber.sh

# Chạy riêng phân tích bổ sung
python -m tools.make_ds_supplement

# Test
pytest tests/ -q

# Dashboard
streamlit run dashboard/app.py
```

---

## Bất biến kỹ thuật

| Bất biến | Cơ chế bảo đảm |
|---|---|
| Test set không bao giờ chạm train | Student-level split; `make_X_y` filter theo split file |
| Split không tự thay đổi | Split guard trong `make_split.py`; `--rederive` là lối duy nhất |
| Preprocessing chỉ fit trên train | `preprocess()` nhận `X_train, X_test` riêng biệt |
| SMOTE chỉ áp dụng trên train fold | `train.py` apply sau split, trước fit |
| Ngưỡng quyết định tuned trên OOF | Không dùng test set để tune threshold |
| Mọi con số xuất phát từ CSV | `build_final_report.py` đọc CSV; không hand-edit |
| Checkpoint + atomic write | Mọi script vòng lặp dài ghi `.tmp` rồi rename |
