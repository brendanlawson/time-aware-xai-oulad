# Hướng dẫn tự code `src/` — Time-Aware XAI on OULAD (DSP391m, Nhóm 1)

Tài liệu này hướng dẫn bạn **tự viết toàn bộ `src/`** từ các file skeleton (khung
hàm + docstring + `TODO`). Mục tiêu: hiểu sâu từng bước, không copy-paste.

- Mỗi hàm hiện đang `raise NotImplementedError` — việc của bạn là thay phần thân.
- Hằng số/cấu hình (paths, seed, danh sách cột, bảng màu) **đã cho sẵn** vì đó là
  *dữ kiện dự án*, không phải logic cần học.
- File “đáp án” gốc nằm ở `D:\dsp\src` (không động vào) — chỉ mở khi bí, đừng chép.
- Bài test `tests/test_leakage.py` là **tiêu chí nghiệm thu**: code đúng khi test xanh.

> Quy ước import: mọi module import từ `src.config` (paths, seed, CHECKPOINTS) và
> `src.data.io_utils` (GROUP_COLS, PRESENTATION_KEY, nhãn at_risk…). KHÔNG hard-code 42
> hay đường dẫn tuyệt đối ở bất kỳ đâu.

---

## 0. Chuẩn bị

```powershell
conda env create -n time-aware-xai-oulad -f environment.yml   # hoặc dùng env dsp sẵn có
conda activate time-aware-xai-oulad
pip install -e .            # cài src ở chế độ editable -> import src... chạy được
```

Đặt 7 file CSV OULAD vào `data/raw/`:
`studentInfo, studentRegistration, studentVle, studentAssessment, assessments, vle, courses`.

Chạy test để thấy nó đỏ (chưa code gì):
```powershell
pytest tests/test_leakage.py -q
```

---

## 1. Thứ tự build (RẤT QUAN TRỌNG)

Code theo đúng thứ tự phụ thuộc dưới đây. Mỗi tầng dùng tầng trước.

| # | Module | Vai trò | Phụ thuộc |
|---|--------|---------|-----------|
| 1 | `data/io_utils.py` | I/O dùng chung, nhãn at_risk, ghi parquet atomic | — |
| 2 | `data/time_utils.py` | bản đồ checkpoint + cắt theo mốc thời gian | io_utils |
| 3 | `data/build_engagement_features.py` | gộp clickstream → đặc trưng engagement | io_utils |
| 4 | `data/build_performance_features.py` | gộp bài nộp → đặc trưng performance | io_utils |
| 5 | `data/build_master_table.py` | join tất cả → master table (t=100%) | 1–4 |
| 6 | `data/make_checkpoints.py` | 6 bộ dữ liệu time-aware (có resume) | 1–4, time_utils |
| 7 | `evaluation/split_harness.py` | nguyên thủy chia train/test chống rò rỉ | config |
| 8 | `evaluation/make_split.py` | cố định + lưu split, dùng lại mọi nơi | split_harness |
| 9 | `features/preprocessing.py` | pipeline tiền xử lý chống rò rỉ | io_utils, config |
| 10 | `eda/plot_style.py` + `eda/eda.py` | EDA có kiểm định thống kê | data |
| 11 | `modeling/train.py` + `predict.py` | huấn luyện ở mỗi checkpoint + suy luận | 8, 9 |
| 12 | `xai/shap_explain.py` + `lime_explain.py` + `stability.py` | giải thích + độ ổn định | 11 |
| 13 | `plots.py` | biểu đồ kết quả tổng hợp | eda/plot_style |

CLI chạy pipeline (sau khi code xong từng tầng):
```powershell
python -m src.data.build_engagement_features
python -m src.data.build_master_table
python -m src.data.make_checkpoints          # dài; chạy lại sẽ resume
python -m src.evaluation.make_split
python -m src.modeling.train
```

---

## 2. Bốn quy tắc CHỐNG RÒ RỈ (xương sống của đồ án)

Cả đồ án xoay quanh việc dự đoán **sớm** mà không “nhìn trộm tương lai”. Nhớ kỹ:

1. **Rò rỉ thời gian (clickstream/bài nộp):** ở checkpoint t%, chỉ giữ bản ghi có
   `date <= cutoff_day`. → `time_utils.cut_at_checkpoint`.
2. **Roster cố định:** danh sách sinh viên y hệt ở mọi checkpoint (Option A); chỉ
   đặc trưng theo thời gian thay đổi. → `make_checkpoints`.
3. **Split cố định theo `id_student`:** chia 1 lần, dùng lại cho master + 6
   checkpoint; một sinh viên không bao giờ ở cả train lẫn test. → `split_harness`.
4. **Học thống kê chỉ trên TRAIN:** median impute, ngưỡng winsorize, scaler,
   encoder, **và SMOTE** — tất cả fit trên train rồi áp cho test. → `preprocessing`.

Nhãn `at_risk = final_result ∈ {Fail, Withdrawn}` và **không bao giờ** đưa
`final_result` / `date_unregistration` vào X (`LEAKY_COLUMNS`).

---

## 3. Đặc tả từng module

### `data/io_utils.py`
- `add_at_risk_label`: thêm cột `at_risk` (int8) từ `final_result`. Không mutate input.
- `save_parquet_atomic`: ghi ra file `.tmp` rồi `os.replace` → an toàn khi bị kill.
- `load_raw_tables`: đọc 7 CSV → dict {tên: DataFrame}.

### `data/time_utils.py`
- `build_checkpoint_map(courses)`: với mỗi presentation × mỗi t →
  `cutoff_day = round(length * t / 100)`. Long format.
- `cut_at_checkpoint(df, t, map)`: merge cutoff theo PRESENTATION_KEY, giữ
  `date <= cutoff_day`. Quyết định rõ cách xử lý `date` NaN và ghi chú lại.
- ✅ Test `test_no_*_leakage`, `test_counts_non_decreasing_in_t`,
  `test_t100_keeps_all_dated_clicks` kiểm tra hàm này.

### `data/build_engagement_features.py`
- `aggregate_engagement` PHẢI thuần (pure): nhận clickstream → trả đặc trưng, để
  `make_checkpoints` tái dùng trên clickstream đã cắt.
- Group theo `GROUP_COLS`: total_clicks, n_days_active, clicks_<type> (8 loại
  canonical), max_clicks_single_day, mean_clicks_per_active_day, last_active_day.
- `load_student_vle`: đọc theo chunk + downcast dtype (bảng ~10.6M dòng).

### `data/build_performance_features.py`
- `aggregate_performance` thuần + theo cutoff: n_assessments_submitted,
  mean_score_to_date, weighted_score_to_date, **not_submitted**.
- `not_submitted` = sinh viên bỏ lỡ ≥1 bài đã đến hạn (deadline ≤ cutoff). Nhờ cờ
  này, downstream fill score thiếu = 0 vẫn có nghĩa.

### `data/build_master_table.py`
- Left-join: studentInfo ← registration ← engagement ← performance (cutoff = độ dài
  khóa, tức t=100%). Log số dòng trước/sau mỗi join để chứng minh không nhân bản/mất.
- `_clean`: drop trùng `GROUP_COLS`, chuẩn hóa text categorical (giữ nguyên
  `imd_band` dạng '10-20' cho ordinal encoder).

### `data/make_checkpoints.py`
- Vòng lặp 6 checkpoint. **BẮT BUỘC** checkpoint + resume (quy tắc dự án về script
  chạy lâu): ghi atomic từng `dataset_t{t}.parquet`, bỏ qua file đã có khi chạy lại,
  log “skip (resumed)” vs “newly built”.
- `days_since_last_activity = cutoff_day - last_active_day`. Lưu ý sinh viên không
  hoạt động: idle = cả cửa sổ, **không phải 0** (test `test_checkpoint_t100_idle...`).

### `evaluation/split_harness.py`
- `make_fixed_test_ids`: dùng `StratifiedGroupKFold(n_splits=round(1/test_size))`,
  lấy fold đầu làm test; group = `id_student`, stratify = `at_risk`.
- `split_by_ids`, `group_overlap` (phải = 0), `class_balance`, `build_split_report`,
  `iter_cv_folds` (CV cũng phải group-aware).
- ✅ `test_split_has_no_group_overlap`, `test_split_preserves_class_ratio`.

### `evaluation/make_split.py`
- `save_definition`: tính & ghi `data/splits/test_student_ids.csv` (commit được).
- `load_checkpoint_split(t)`: hàm mà tầng modeling gọi — đọc parquet checkpoint, chia
  bằng đúng tập id đã commit.

### `features/preprocessing.py` (xem 4 quy tắc ở mục 2)
- Mẫu fit/apply qua `stats`: dict rỗng ⇒ học trên train; dict có sẵn ⇒ áp cho test.
  - `handle_missing` → `stats["{col}_median"]`
  - `handle_outliers` → `stats[f"winsor_{col}"] = (low, high)` = [p1, p99] của train.
- `BinaryEncoder` (sklearn transformer), `build_ordinal/onehot_encoder`,
  `build_scaler`, `build_column_transformer`, `fit_transform_train`/`transform_test`,
  `get_feature_names` (cần cho SHAP/LIME).
- `preprocess(X_train, X_test)`: chạy đúng thứ tự 1→4 ở docstring; SMOTE để NGOÀI.
- `make_X_y`: bỏ `ID_COLS` + `LEAKY_COLUMNS`.
- ✅ `test_preprocessing_uses_train_only_stats`, `test_feature_frame_excludes_leaky_columns`.

### `eda/plot_style.py` + `eda/eda.py`
- `plot_style`: `apply_style` (rcParams cho sẵn), `tidy_axis`, `savefig` (300 dpi).
- `eda.py`: mỗi hàm trả dict findings + ghi figure/bảng. Điểm nhấn: `time_aware()`
  cho thấy khả năng phân tách lớp tăng dần qua 6 checkpoint (trả lời RQ1).
  Dùng kiểm định + effect size (Cohen's d, Cramér's V) và hiệu chỉnh BH.

### `modeling/train.py` + `predict.py`
- `build_model`: registry {logreg, rf, gboost}. `evaluate`: roc_auc, pr_auc, f1,
  **recall** (ưu tiên — bắt được sinh viên nguy cơ), precision, balanced_acc, brier.
- `train_at_checkpoint`: split → make_X_y → preprocess → SMOTE(train) → fit →
  evaluate → lưu bundle `{model, ct, feat_names}`.
- `train_all`: lặp model × checkpoint → `reports/tables/model_metrics.csv` (resume được).
- `predict`: dùng lại đúng `ct` đã fit để transform dữ liệu mới.

### `xai/` — phần đóng góp nghiên cứu
- `shap_explain`: explainer theo họ model, `global_importance` = mean(|SHAP|) xếp hạng.
- `lime_explain`: surrogate tuyến tính cục bộ cho từng sinh viên; gom thành ma trận
  trọng số để so sánh.
- `stability`: **trọng tâm RQ2/RQ3**. So sánh xếp hạng đặc trưng theo:
  - **seed** (đổi random_state — giải thích tốt phải ổn định) → `stability_across_seeds`
  - **checkpoint** (drift khi thấy nhiều dữ liệu hơn) → `stability_across_checkpoints`
  - SHAP vs LIME có “kể cùng một câu chuyện” không → `shap_lime_agreement`
  - Primitive: `jaccard_topk`, `spearman_rank`, `kendall_tau`.

### `plots.py`
- `metric_vs_checkpoint` (hình tiêu đề RQ1), `importance_bar`, `stability_drift`.

---

## 4. Mẹo làm việc

- **TDD:** mở `tests/test_leakage.py`, code đến khi từng test xanh. Test còn ẩn ý các
  quy ước (key của `stats`, `LEAKY_COLUMNS`, idle=full-window…).
- Code **io_utils → time_utils → engagement/performance** trước, vì test rò rỉ chỉ
  cần tới đó là chạy được (chưa cần model).
- Notebook đặt ở `notebooks/` theo thứ tự `00_…`, `01_…` để *kể chuyện* kết quả; logic
  nặng luôn nằm trong `src/` rồi import vào notebook.
- Khi bí: đối chiếu ý tưởng (không chép) với `D:\dsp\src\<cùng file>`.
- Giữ mọi randomness gắn `RANDOM_SEED` từ `src.config` để tái lập được.
