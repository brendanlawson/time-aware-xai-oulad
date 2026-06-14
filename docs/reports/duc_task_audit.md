# Audit phần nhiệm vụ của Đức trong repo

Ngày kiểm tra: 2026-06-14

## Kết luận nhanh

Trong zip, file `src/features/preprocessing.py` đã gom phần code cho Đức từ Task 16 đến Task 20 và Task 22. Riêng STT20 đã có code và đã được smoke test thành công. Repo trước khi bổ sung chưa có thư mục `reports`, vì vậy phần báo cáo chương cho STT20 được bổ sung tại `reports/data_tasks/stt20_scaling_report.md`.

## Trạng thái từng task

| STT | Nội dung | Trạng thái trong zip | Bằng chứng |
| --- | --- | --- | --- |
| 16 | Phân loại kiểu biến | Đã có | `NUMERIC_FEATURES`, `ORDINAL_FEATURES`, `NOMINAL_FEATURES`, `BINARY_FEATURES`, `ORDINAL_ORDERS` trong `preprocessing.py`; output trước đó có `variable_typing.xlsx`. |
| 17 | Xử lý giá trị khuyết | Đã có | `log_missing()` và `handle_missing()`, có log và assert không còn missing. |
| 18 | Xử lý ngoại lai | Đã có | `OUTLIER_STRATEGY`, `log_outliers()`, `handle_outliers()`, không xoá bản ghi tuỳ tiện. |
| 19 | Mã hoá biến phân loại | Đã có | `BinaryEncoder`, `build_ordinal_encoder()`, `build_onehot_encoder()`, `ColumnTransformer`. |
| 20 | Chuẩn hoá thang đo | Đã có và đã kiểm thử | `build_scaler()`, nhánh `num` trong `ColumnTransformer`, `fit_transform_train()`, `transform_test()`, smoke test đạt. |
| 21 | Phân tích chiến lược phân chia dữ liệu | Chưa thấy trong `preprocessing.py` | Task này thường thuộc `split_harness.py`/báo cáo phân chia; không nằm trong module preprocessing của zip. |
| 22 | Trình tự pipeline anti-leakage | Đã có | `preprocess()` ghi rõ missing -> outlier -> fit train -> transform test; note resampling chỉ trên train. |

## Kết quả smoke test STT20

Lệnh đã chạy:

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe .\src\features\preprocessing.py
```

Kết quả:

- `X_train_proc shape`: `(200, 38)`
- `X_test_proc shape`: `(50, 38)`
- `n_features`: `38`
- Không còn NaN sau transform.
- `scaler.mean_[:4] = [2.045, 330.935, -9.63, 7.5868]`, chỉ tính từ X_train.
- Module in kết luận: tất cả kiểm tra đạt.

## Việc đã bổ sung trong lần này

- Tạo `reports/data_tasks/stt20_scaling_report.md`: phần báo cáo chương cho STT20.
- Tạo `reports/data_tasks/duc_task_audit.md`: audit trạng thái các task của Đức trong zip.

## Việc còn thiếu nếu muốn hoàn tất toàn bộ phần Đức

- STT21 cần một file riêng về chiến lược phân chia dữ liệu nếu giáo viên yêu cầu Đức phụ trách mục này. Hiện zip chưa có artifact rõ ràng cho STT21 trong `src/features/preprocessing.py`.
