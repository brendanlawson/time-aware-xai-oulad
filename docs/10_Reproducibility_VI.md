# Hướng Dẫn Tái Tạo Kết Quả

**Phụ đề:** Toàn bộ những gì người đọc bên ngoài cần để tái tạo bảng tổng hợp và các sản phẩm dữ liệu phái sinh

_DSP391m – Nhóm 1 · Báo cáo 2 (Data Tasks), Chương 3 · Hạng mục STT 31 (An)_

---

## 1. Mục Đích

Khả năng tái tạo kết quả (reproducibility) là yêu cầu bậc nhất trong công việc khoa học dữ liệu. Hướng dẫn này ghi lại các bước chính xác, môi trường (environment) và các biện pháp kiểm soát nguồn gốc dữ liệu (data provenance) để bất kỳ người đọc bên ngoài nào — bao gồm thành viên nhóm trong tương lai và người đánh giá — đều có thể tái tạo mọi sản phẩm đầu ra của pipeline này, từng bit một, bắt đầu từ bộ dữ liệu thô OULAD đã tải về.

---

## 2. Tính Tất Định

Một hạt giống ngẫu nhiên toàn cục (global random seed) duy nhất được sử dụng xuyên suốt tất cả các script, notebook và trường hợp kiểm thử:

```python
RANDOM_SEED = 42
```

Mọi lệnh gọi đến `numpy.random`, `random`, các bộ chia dữ liệu (splitters) của `sklearn` và bất kỳ hàm lấy mẫu nào đều phải dùng hằng số này. Hằng số được định nghĩa một lần trong `src/config.py` và được nhập (import) ở mọi nơi khác; tuyệt đối không được hard-code cục bộ.

---

## 3. Nguồn Gốc Dữ Liệu

### 3.1 Tệp Kê Khai Dữ Liệu Thô

Tệp `data/raw/data_manifest.txt` được tạo tự động bởi `setup_raw_data.py` và ghi lại các trường sau cho mỗi trong bảy tệp CSV của OULAD:

| Trường | Mô tả |
|---|---|
| Tên tệp (Filename) | Tên tệp chính xác (ví dụ: `studentInfo.csv`) |
| Mã băm MD5 (MD5 hash) | Chuỗi hex của tệp đã tải về chưa qua chỉnh sửa |
| Kích thước (Size, MB) | Dung lượng tệp làm tròn hai chữ số thập phân |
| Ngày tải về (Download date) | Ngày tải tệp theo định dạng ISO-8601 |

Bảy tệp được bao gồm: `courses.csv`, `assessments.csv`, `vle.csv`, `studentInfo.csv`, `studentRegistration.csv`, `studentAssessment.csv`, `studentVle.csv`.

### 3.2 Bảo Vệ Chỉ Đọc

Sau khi tệp kê khai được ghi, `setup_raw_data.py` đặt mỗi tệp CSV thô thành chỉ đọc (read-only) (`chmod 444` trên Linux/macOS; `attrib +R` trên Windows), ngăn ngừa ghi đè vô ý.

### 3.3 Xác Minh Tính Toàn Vẹn

Để xác minh tính toàn vẹn dữ liệu (data integrity) vào bất kỳ thời điểm nào, hãy chạy lại `setup_raw_data.py`. Script sẽ tính lại MD5 của mỗi tệp và so sánh với tệp kê khai đã lưu. Bất kỳ sự không khớp nào sẽ làm dừng chương trình với ngoại lệ (exception) trước khi bất kỳ bước nào ở hạ nguồn được thực thi.

---

## 4. Môi Trường

- **Phiên bản Python:** 3.11 (quản lý qua Conda)
- **Ghim phiên bản phụ thuộc (Dependency pinning):** `requirements.txt` (cài đặt qua pip, phiên bản chính xác) và `environment.yml` (toàn bộ môi trường Conda, bao gồm các gói ngoài Python)
- **Lưu ý về vẽ biểu đồ:** Việc tạo hình ảnh bằng Matplotlib yêu cầu môi trường có bộ phông chữ/freetype hoạt động được. Trên các máy chủ headless tối giản, hãy cài `libfreetype6-dev` (Debian/Ubuntu) hoặc tương đương trước khi chạy bước EDA.

Để tái tạo môi trường:

```bash
conda env create -f environment.yml
conda activate dsp391m
```

Hoặc chỉ dùng pip:

```bash
pip install -r requirements.txt
```

---

## 5. Các Bước Tái Tạo Chính Xác

Chạy tất cả lệnh từ **thư mục gốc của dự án (project root)** theo thứ tự dưới đây. Mỗi bước là idempotent (tức là chạy lại nhiều lần vẫn cho cùng kết quả).

```
1. python setup_raw_data.py
```
Xác minh bảy tệp CSV thô với tệp kê khai, ghi `data/raw/data_manifest.txt` nếu chưa có, và đặt các tệp thành chỉ đọc.

```
2. python -m src.data.time_utils
```
Xây dựng `data/checkpoint_map.csv` và chạy tự kiểm tra (self-check) để xác nhận các mốc checkpoint (checkpoint boundaries) đúng về mặt thời gian (không rò rỉ dữ liệu tương lai tại bất kỳ checkpoint nào).

```
3. python -m src.data.build_master_table
```
Tạo ra:
- `data/interim/master_raw.parquet` — bảng tổng hợp (32.593 hàng × 33 cột)
- `data/interim/master_join_log.csv` — số hàng sau mỗi bước kết hợp bảng trái (left-join)
- `data/interim/master_cleaning_log.csv` — hồ sơ ghi lại mọi quyết định làm sạch dữ liệu

```
4. python -m src.data.make_checkpoints
```
Tạo ra:
- `data/checkpoints/dataset_t10.parquet` đến `dataset_t100.parquet` (sáu tệp tại các mốc 10 %, 30 %, 50 %, 70 %, 90 %, 100 % của module)
- `data/checkpoints/checkpoint_summary.csv`

Bước này **có thể tiếp tục sau gián đoạn (resumable)**: nếu bị dừng giữa chừng, chạy lại sẽ bỏ qua các tệp checkpoint đã ghi và tiếp tục từ chỗ dừng.

```
5. python -m src.eda.eda
```
Tạo ra:
- `reports/figures/*.png` — toàn bộ hình ảnh phân tích khám phá dữ liệu (EDA figures)
- `reports/eda_findings.json` — thống kê tóm tắt dạng machine-readable

Yêu cầu bộ phông chữ/freetype hoạt động được (xem Mục 4).

```
6. pytest tests/test_leakage.py
```
Chạy kiểm tra rò rỉ thời gian (temporal-leakage checks) và kiểm tra tính toàn vẹn phân chia dữ liệu (split-integrity tests). Tất cả bài kiểm thử phải vượt qua trước khi bắt đầu bất kỳ công việc mô hình hóa nào.

---

## 6. Các Đảm Bảo Về Tính Tái Tạo

| Thuộc tính | Đảm bảo |
|---|---|
| Thực thi notebook | Tất cả notebook chạy từ đầu đến cuối (top-to-bottom) không có lỗi khi thực hiện qua Restart & Run All |
| Các bước chạy lâu | Bước 3 và 4 được lưu checkpoint và có thể tiếp tục sau gián đoạn; một lần chạy bị ngắt không bao giờ làm hỏng đầu ra |
| Ghi nguyên tử (Atomic writes) | Tất cả tệp Parquet được ghi vào đường dẫn tạm thời rồi đổi tên vào vị trí cuối cùng; nếu bị dừng giữa quá trình ghi, tệp trước đó vẫn còn nguyên |
| Sử dụng seed | `RANDOM_SEED = 42` được dùng cho mọi phép toán ngẫu nhiên |

---

## 7. Các Thực Tế Đã Được Xác Minh

Các thực tế sau được thiết lập trong lần chạy chuẩn (canonical run) và phải đúng sau bất kỳ lần tái tạo nào:

- `master_raw.parquet` chứa **32.593 hàng × 33 cột**.
- Tất cả phép kết hợp bảng trái trong `build_master_table` bảo toàn đúng **32.593 hàng** — không có hàng nào bị trùng lặp và không có hàng nào bị mất.
- Bảng tổng hợp chứa **0 khóa trùng lặp (duplicate keys)** (xác minh bởi `pytest tests/test_leakage.py`).
- Tỷ lệ có nguy cơ (at-risk rate) trong bảng tổng hợp là **52,8 %**.
- Sáu tập dữ liệu checkpoint chia sẻ danh sách sinh viên (roster) giống hệt nhau gồm **32.593 sinh viên** — không có sinh viên nào xuất hiện ở một checkpoint mà không có ở checkpoint khác.

---

_Nhóm 1 DSP391m. Cập nhật lần cuối: 2026-06-14._
