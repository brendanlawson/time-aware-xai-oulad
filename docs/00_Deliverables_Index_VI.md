# Báo cáo 2 (Tác vụ dữ liệu) — Mục lục sản phẩm bàn giao

**DSP391m – Nhóm 1 · Ánh xạ mỗi hạng mục công việc (STT 1–40) tới sản phẩm trong kho mã nguồn này.**

Tài liệu được cung cấp ở cả định dạng Markdown (`.md`) và Word (`.docx`), mỗi loại có bản tiếng Anh (`_EN`) và tiếng Việt (`_VI`). Dữ liệu phái sinh (`*.parquet`) bị git bỏ qua và được tái tạo bằng pipeline; biểu đồ được lưu trong `reports/figures/`.

| STT | Thành viên | Hạng mục | Sản phẩm bàn giao |
|---|---|---|---|
| 1 | Cả nhóm | Định nghĩa biến mục tiêu & quy ước Withdrawn | `docs/01_TargetVariable_Definition_{EN,VI}.md/.docx`, `docs/BienBan_Buoc0_Nhom1_1.pdf` |
| 2 | Phúc | Thu thập & lưu trữ bất biến OULAD | `data/raw/`, `data/raw/data_manifest.txt`, `setup_raw_data.py` |
| 3 | Phúc | Tổng hợp clickstream VLE | `src/data/build_engagement_features.py` → `engagement_agg.parquet` |
| 4 | Phúc | Xây dựng bảng hợp nhất | `src/data/build_master_table.py` → `master_raw.parquet`, `master_join_log.csv` |
| 5 | Phúc | Loại trùng & chuẩn hoá | `src/data/build_master_table.py` (`_clean`), `master_cleaning_log.csv` |
| 6 | Phúc | Notebook tái lập | `notebooks/01_build_master_table.ipynb` |
| 7 | Phúc | Phân chia bảo toàn nhóm | `src/evaluation/split_harness.py` |
| 8 | Phúc | Tập kiểm tra cố định qua các mốc | `src/evaluation/split_harness.py` (`make_fixed_test_ids`) |
| 9 | Khoa | Khảo sát lược đồ & khoá | `notebooks/schema_survey.ipynb` |
| 10 | Khoa | Bảng quy đổi mốc (ngày) | `src/data/time_utils.py` → `data/checkpoint_map.csv` |
| 11 | Khoa | `cut_at_checkpoint` | `src/data/time_utils.py` |
| 12 | Khoa | Quy tắc phòng rò rỉ | `docs/02_LeakagePrevention_Rules_{EN,VI}.md/.docx`, `docs/QuyTac_PhongTranhRoRi_STT12_Nhom1.pdf` |
| 13 | Khoa | Sáu bộ dữ liệu theo mốc | `src/data/make_checkpoints.py` → `data/checkpoints/`, `checkpoint_summary.csv` |
| 14 | Khoa | Kiểm thử rò rỉ tự động | `tests/test_leakage.py` (16 kiểm thử) |
| 15 | Khoa | Phân chia phân tầng | `src/evaluation/split_harness.py` |
| 16 | Đức | Phân loại kiểu biến | `docs/variable_typing.xlsx` |
| 17 | Đức | Xử lý giá trị khuyết | `src/features/preprocessing.py` (`handle_missing`) |
| 18 | Đức | Xử lý ngoại lai | `src/features/preprocessing.py` (`handle_outliers`) |
| 19 | Đức | Mã hoá biến phân loại | `src/features/preprocessing.py` (encoders) |
| 20 | Đức | Chuẩn hoá (khớp trên train) | `src/features/preprocessing.py` (`build_scaler`) |
| 21 | Đức | Phân tích chiến lược phân chia | `docs/06_SplitStrategy_Analysis_{EN,VI}.md/.docx` |
| 22 | Đức | Trình tự tiền xử lý | `docs/07_Preprocessing_Sequence_{EN,VI}.md/.docx`, `reports/figures/preprocessing_sequence.png` |
| 23 | Sơn | Phân tích phương pháp thu thập | `docs/03_DataCollection_Methods_{EN,VI}.md/.docx` |
| 24 | Sơn | Đối chiếu nghiên cứu nền | `docs/04_BaseStudies_Preprocessing_Comparison_{EN,VI}.md/.docx` |
| 25 | Sơn | Lập luận căn cứ phương pháp | `docs/05_Method_Justification_{EN,VI}.md/.docx` |
| 26 | Sơn | Định nghĩa biến mục tiêu + căn cứ | `docs/01_TargetVariable_Definition_{EN,VI}.md/.docx` |
| 27 | Sơn | Phân phối lớp & mất cân bằng | `src/eda/eda.py`, `reports/figures/dist_class_distribution.png` |
| 28 | Sơn | Thống kê mô tả | `src/eda/eda.py`, `reports/eda_descriptive_stats.csv` |
| 29 | An | Từ điển dữ liệu | `docs/DataDictionary.md`, `docs/DataDictionary.xlsx` |
| 30 | An | Nguồn / giấy phép / đạo đức | `docs/DataSource_License_Ethics.md/.docx` |
| 31 | An | Khả năng tái lập | `docs/10_Reproducibility_{EN,VI}.md/.docx`, `README.md`, `requirements.txt` |
| 32 | An | Tổng hợp Chương 4 (EDA) | `reports/Report2_DataTasks_{EN,VI}` §4 |
| 33 | An | Bản thảo Báo cáo 2 (Ch 3–4) | `reports/Report2_DataTasks_{EN,VI}.md/.docx` |
| 34 | An | Kiểm chứng phân chia | `src/evaluation/split_harness.py` (`build_split_report`), báo cáo §3.6 |
| 35 | Bình | Biểu đồ phân phối | `src/eda/eda.py`, `reports/figures/dist_numeric_*.png` |
| 36 | Bình | Phân tích song biến | `src/eda/eda.py`, `reports/figures/bivar_*.png` |
| 37 | Bình | Phân tích tương quan | `src/eda/eda.py`, `reports/figures/corr_*.png` |
| 38 | Bình | EDA theo thời gian | `src/eda/eda.py`, `reports/figures/time_trends_by_label.png` |
| 39 | Bình | Quy chuẩn biểu đồ | `docs/08_Chart_Standards_{EN,VI}.md/.docx`, `src/eda/plot_style.py` |
| 40 | Bình | Quy ước đặt tên đặc trưng | `docs/09_Feature_Naming_Convention_{EN,VI}.md/.docx` |

## Cách tái tạo toàn bộ

```bash
python setup_raw_data.py                 # kiểm tra CSV gốc + manifest
python -m src.data.time_utils            # checkpoint_map.csv
python -m src.data.build_master_table    # master_raw.parquet (+ nhật ký)
python -m src.data.make_checkpoints      # sáu bộ dữ liệu theo mốc
python -m src.eda.eda                    # biểu đồ + eda_findings.json
pytest tests/test_leakage.py             # 16 kiểm thử rò rỉ/phân chia
```

Xem `docs/10_Reproducibility_VI.md` để biết chi tiết.
