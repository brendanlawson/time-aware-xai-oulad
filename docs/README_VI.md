# Báo cáo 2 — Tác vụ dữ liệu · Mục lục tài liệu

**DSP391m – Nhóm 1.** Thư mục này chứa các sản phẩm Chương 3/4 cho **Task 3 (Thu thập & Tiền xử lý dữ liệu)**. Tài liệu song ngữ (`_EN` / `_VI`), có cả Markdown và Word (`.docx`); các bảng tra cứu để dạng Excel; bản gốc có chữ ký giữ ở dạng PDF trong `08_agreements/`. Mục lục tiếng Anh: [`README_EN.md`](README_EN.md).

## Bản đồ phủ Task 3

Cấu trúc thư mục bám theo năm phân tích yêu cầu của Task 3, mỗi yêu cầu ứng với một vị trí:

| Yêu cầu Task 3 | Thư mục | Tài liệu chính |
|---|---|---|
| 1 — Xác định dữ liệu cần có cho đề tài | `01_data_specification/` | `Data_Specification`, `Target_Variable_Definition`, `Data_Dictionary` (.md/.docx/.xlsx), `Variable_Typing.xlsx` |
| 2 — Phân tích phương pháp thu thập dữ liệu | `02_collection/` | `Data_Collection_Methods`, `Data_Source_License_Ethics` |
| 3 — Phân tích phương pháp làm sạch dữ liệu | `03_cleaning/` | `Cleaning_Methods`, `Leakage_Prevention_Rules` |
| 4 — Chuẩn hoá & biến đổi dữ liệu | `04_transformation/` | `Transformation_Standardisation`, `Preprocessing_Sequence`, `Feature_Naming_Convention` |
| 5 — Phân tích tách tập train/test | `05_splitting/` | `Split_Strategy_Analysis` |
| Hỗ trợ — cơ sở bằng chứng | `06_references/` | `Base_Studies_Comparison`, `Method_Justification` |
| Hỗ trợ — quy chuẩn & tái lập | `07_standards/` | `Chart_Standards`, `Reproducibility` |
| Hỗ trợ — bản gốc có chữ ký | `08_agreements/` | `Step0_Agreement_Nhom1.pdf`, `Leakage_Rules_Signed_Nhom1.pdf` |

Sản phẩm tổng hợp hiện hành là chuỗi notebook `notebooks/00…06` cùng bộ docs này (kèm slide trong `reports/slides/`); với chương này, bản thực thi tương ứng là `notebooks/01_build_master_table.ipynb` (dựng/làm sạch) và `notebooks/02_eda.ipynb` (EDA Chương 4).

## Mã nguồn, dữ liệu và kết quả (ngoài `docs/`)

| Khu vực | Vị trí |
|---|---|
| Pipeline dữ liệu | `src/data/` (tương tác, kết quả, bảng hợp nhất, mốc thời gian), `src/features/preprocessing.py` |
| Bộ phân chia | `src/evaluation/split_harness.py` |
| EDA | `src/eda/` → biểu đồ ở `reports/figures/`, bảng thống kê ở `reports/tables/` |
| Kiểm thử | `tests/test_leakage.py` (bộ kiểm thử rò rỉ/phân chia tự động) |
| Bộ sinh | `tools/` (docx, notebook, từ điển dữ liệu, phân loại biến, sơ đồ trình tự) |

## Dữ liệu train / test

Phép phân chia được định nghĩa **một lần** ở cấp sinh viên — **tập kiểm tra 20% cố định** theo `id_student` (phân tầng theo `at_risk`, seed 42) — và dùng lại đồng nhất trên `master_raw` và cả sáu mốc, để sáu điểm hiệu năng so sánh được (STT 7, 8, 15).

| Sản phẩm | Vị trí | Có commit? |
|---|---|---|
| Định nghĩa phân chia (danh sách `id_student` tập test, 5.756 SV) | `data/splits/test_student_ids.csv` | ✅ có commit |
| Báo cáo kiểm chứng phân chia (kích thước, tỉ lệ lớp, 0 trùng) | `reports/tables/split_report.csv` | ✅ có commit |
| Dữ liệu train/test đã tạo (master + từng mốc) | `data/splits/*_train.parquet`, `*_test.parquet` | git bỏ qua (tái tạo được) |

Sinh bằng `python -m src.evaluation.make_split --materialise`. Lệnh này có guard: luôn tái dùng `test_student_ids.csv` đã commit, không bao giờ tự ý tính lại phép chia (cờ `--rederive` chỉ dành cho quyết định của cả nhóm, vì tách lại sẽ đổi 4.574/5.756 id). Ở giai đoạn mô hình, nạp trực tiếp phân chia của một mốc:

```python
from src.evaluation.make_split import load_checkpoint_split
X_train, X_test = load_checkpoint_split(40)   # train/test cho mốc 40%
```

Đã kiểm chứng: train ≈ 26.104 dòng · test ≈ 6.489 dòng (5.756 SV) · at-risk 0,530 / 0,520 · **0 sinh viên trùng** — đồng nhất qua cả sáu mốc.

## Tái tạo toàn bộ

```bash
python setup_raw_data.py                 # kiểm tra 7 CSV gốc + manifest
python -m src.data.time_utils            # data/checkpoint_map.csv
python -m src.data.build_master_table    # master_raw.parquet (+ nhật ký join/làm sạch)
python -m src.data.make_checkpoints      # sáu bộ dữ liệu theo mốc
python -m src.evaluation.make_split --materialise  # phân chia train/test cố định (+ báo cáo)
python -m src.eda.eda                    # biểu đồ + bảng + eda_findings.json
pytest tests/test_leakage.py             # kiểm thử rò rỉ/phân chia tự động
```

> Lưu ý: việc sinh biểu đồ matplotlib cần môi trường có font hoạt động (xem `MEMORY`/tài liệu tái lập). Dữ liệu phái sinh `*.parquet` bị git bỏ qua và được pipeline tái tạo.
