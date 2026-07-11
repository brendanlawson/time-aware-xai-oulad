# Hướng dẫn cài đặt cho thành viên

Tài liệu này hướng dẫn **từ lúc clone repo về đến khi có đủ toàn bộ dữ liệu** (`data/interim/`, `data/checkpoints/`, `data/splits/`) để bắt đầu làm việc.

> **Vì sao phải làm các bước này?**
> Dữ liệu **không** được commit vào git (vì file lớn, vì giấy phép CC-BY của OULAD không cho phát tán lại, và vì mọi file `.parquet` đều **tự sinh lại được** từ code + dữ liệu gốc). Bạn tải dữ liệu gốc một lần, rồi chạy pipeline để sinh ra các file còn lại — ai chạy cũng ra kết quả **giống hệt nhau**.

---

## Tóm tắt nhanh (TL;DR)

```powershell
# 1. Cài môi trường
conda env create -f environment.yml
conda activate dsp

# 2. Tải 7 file OULAD vào data/raw/  (xem Bước 2 bên dưới), rồi kiểm tra:
python setup_raw_data.py

# 3. Chạy pipeline sinh dữ liệu (3 lệnh, đúng thứ tự)
python -m src.data.build_master_table      # -> data/interim/
python -m src.data.make_checkpoints        # -> data/checkpoints/
python -m src.evaluation.make_split        # -> data/splits/

# 4. Kiểm tra
pytest tests/
```

Xong bước trên là bạn có đầy đủ dữ liệu. Chi tiết từng bước ở dưới.

---

## Bước 1 — Cài môi trường

Yêu cầu: **Python 3.13** (env đã kiểm chứng — xem `environment.yml`). Khuyến nghị dùng **conda** (cài sẵn các thư viện nặng như pyarrow, xgboost, lightgbm dạng binary, không cần trình biên dịch).

### Cách A — Conda (khuyến nghị)

```powershell
conda env create -f environment.yml
conda activate dsp
```

### Cách B — venv + pip

```powershell
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

> ⚠️ **Bắt buộc có `pyarrow`** thì mới đọc/ghi được file `.parquet`. Cả hai cách trên đều đã bao gồm. Nếu bạn dùng Python hệ thống mà gặp lỗi `Unable to find a usable engine ... pyarrow`, nghĩa là bạn đang chạy sai môi trường — hãy `conda activate dsp` (hoặc kích hoạt venv) trước.

### Lưu ý tương thích bundle

Các bundle mô hình `.joblib` trong `models/` được build bằng **scikit-learn 1.8 / numpy 2.x** — phải dùng đúng env đã pin trong `environment.yml`. Nếu dùng env cũ (Python 3.11 / sklearn 1.5 / numpy < 2): bundle ANN (`models/ann_t100.joblib`) load **fail** (lỗi `MT19937 is not a known BitGenerator`), các model còn lại load được nhưng kèm `InconsistentVersionWarning` (rủi ro sai lệch kết quả).

---

## Bước 2 — Tải dữ liệu gốc OULAD

Tải **7 file CSV** từ một trong hai nguồn:

- Nguồn chính thức: <https://analyse.kmi.open.ac.uk/open_dataset>
- Kaggle mirror: <https://www.kaggle.com/datasets/anlgrbz/student-demographics-online-education-dataoulad>

Đặt cả 7 file vào thư mục `data/raw/`:

```
data/raw/
├── assessments.csv
├── courses.csv
├── studentAssessment.csv
├── studentInfo.csv
├── studentRegistration.csv
├── studentVle.csv          (~433 MB — file lớn nhất)
└── vle.csv
```

> 📌 Thư mục `data/raw/` đã bị git bỏ qua (ignored) nên bạn sẽ không thấy nó được commit — đó là điều bình thường.

### Kiểm tra tính toàn vẹn

Chạy script để xác nhận bạn tải **đúng phiên bản dữ liệu** (đối chiếu MD5 với manifest) và khóa file ở chế độ chỉ-đọc:

```powershell
python setup_raw_data.py
```

Nếu thành công sẽ in: `QUY TRÌNH HOÀN TẤT: 7 tệp đã được kiểm tra...`. So sánh với checksum gốc trong `data/raw/data_manifest.txt` (ví dụ `studentVle.csv` phải là `b8aae6f4ffd1523319aeb56d66b17f72`). Nếu MD5 lệch → bạn tải thiếu/sai file, hãy tải lại.

---

## Bước 3 — Chạy pipeline sinh dữ liệu

Chạy **3 lệnh theo đúng thứ tự** dưới đây (mỗi bước phụ thuộc kết quả của bước trước). Các thư mục đầu ra **tự được tạo**, bạn không cần `mkdir`.

### 3.1 — Master table → `data/interim/`

```powershell
python -m src.data.build_master_table
```

- **Đọc:** 7 file trong `data/raw/` (gom ~10.6 triệu dòng clickstream VLE)
- **Sinh ra:**
  - `data/interim/engagement_agg.parquet` — đặc trưng tương tác đã tổng hợp theo sinh viên
  - `data/interim/master_raw.parquet` — **bảng master** (32.593 dòng × 33 cột), 1 dòng / 1 sinh viên + nhãn at-risk
  - các file log: `master_join_log.csv`, `master_cleaning_log.csv`

### 3.2 — Cắt dữ liệu theo mốc thời gian → `data/checkpoints/`

```powershell
python -m src.data.make_checkpoints
```

- **Đọc:** `data/raw/` + bảng master
- **Sinh ra:** 6 file `data/checkpoints/dataset_t{10,20,40,60,80,100}.parquet`
  (mỗi file chỉ giữ dữ liệu đến mốc 10% / 20% / ... / 100% thời lượng khóa học — phục vụ dự đoán **sớm**)

### 3.3 — Chia train/test → `data/splits/`

```powershell
python -m src.evaluation.make_split
```

- **Đọc:** `data/interim/master_raw.parquet` + `data/checkpoints/*.parquet` + `data/splits/test_student_ids.csv`
  (file `test_student_ids.csv` **có sẵn trong git** — đảm bảo cả nhóm dùng **chung một tập test cố định**, tránh rò rỉ dữ liệu)
- **Sinh ra:**
  - `data/splits/master_train.parquet`, `master_test.parquet`
  - `data/splits/dataset_t{XX}_train.parquet`, `dataset_t{XX}_test.parquet` (12 file)
  - đây là **dữ liệu cuối cùng để huấn luyện mô hình**

> 📌 **Guard an toàn:** nếu `test_student_ids.csv` đã tồn tại, lệnh trên chỉ **nạp lại** danh sách test đã commit chứ không tính lại phép chia — chạy lại bao nhiêu lần cũng an toàn. Muốn tách lại từ đầu phải thêm cờ `--rederive`, nhưng **đừng tự ý làm**: khác phiên bản sklearn sẽ đổi 4.574/5.756 id và vô hiệu mọi số liệu đã công bố (chỉ dùng khi cả nhóm cùng quyết định).

---

## Sơ đồ phụ thuộc

```
data/raw/*.csv                        ← bạn tự tải (Bước 2)
   │  python -m src.data.build_master_table
   ▼
data/interim/master_raw.parquet
data/interim/engagement_agg.parquet
   │  python -m src.data.make_checkpoints
   ▼
data/checkpoints/dataset_t{10..100}.parquet   (6 file)
   │  python -m src.evaluation.make_split   (+ test_student_ids.csv từ git)
   ▼
data/splits/*.parquet                 ← dữ liệu cuối để train model (12 file)
```

---

## Bước 4 — Kiểm tra

```powershell
pytest tests/
```

Bộ test rò rỉ dữ liệu (`tests/test_leakage.py`, 19 test) phải **PASS**. Nếu pass nghĩa là pipeline của bạn đã chạy đúng và dữ liệu khớp với cả nhóm.

### Kiểm tra nhanh bằng mắt (tùy chọn)

```python
import pandas as pd
print(pd.read_parquet("data/interim/master_raw.parquet").shape)   # mong đợi (32593, 33)
print(pd.read_parquet("data/splits/dataset_t20_train.parquet").head())
```

---

## Câu hỏi thường gặp

**Q: Mình clone về mà không thấy folder `data/interim`, `data/checkpoints`, `data/splits`?**
Bình thường. Chúng bị git ignore và được sinh ra ở **Bước 3**. Cứ chạy 3 lệnh pipeline là có.

**Q: Lỗi `Unable to find a usable engine ... pyarrow` khi đọc parquet?**
Bạn đang chạy sai môi trường Python. Chạy `conda activate dsp` (hoặc kích hoạt venv) rồi thử lại.

**Q: Có cần ClickHouse / Spark để đọc dữ liệu không?**
Không. Dữ liệu chỉ ~450 MB (1 file lớn 433 MB), pandas + pyarrow xử lý dư sức. Nếu muốn query nhanh bằng SQL trên CSV/parquet, dùng `duckdb` (`pip install duckdb`) — nhẹ, không cần server.

**Q: Mình lỡ sửa file trong `data/raw/` thì sao?**
Các file raw được khóa chỉ-đọc bởi `setup_raw_data.py` để giữ "nguồn sự thật bất biến". Nếu cần làm lại, tải lại file gốc và chạy lại `python setup_raw_data.py`.

**Q: Chạy lại pipeline có an toàn không (idempotent)?**
Có. Các script ghi file theo kiểu atomic (ghi file tạm rồi đổi tên) và sinh lại cùng kết quả với cùng `RANDOM_SEED = 42`. Chạy lại nhiều lần không gây hỏng.
