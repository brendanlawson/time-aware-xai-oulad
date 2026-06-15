# Chiến lược phân chia dữ liệu: Phân tích và lựa chọn

*So sánh các chiến lược phân chia và lập luận cho thiết kế phù hợp dữ liệu theo thời gian, mất cân bằng và có nhóm*

**DSP391m – Nhóm 1 · Báo cáo 2 (Tác vụ dữ liệu), Chương 3 · Hạng mục STT 21 (Đức)**

---

## 1. Vì sao việc phân chia cần thận trọng

Ba đặc tính của dữ liệu ràng buộc cách phân chia:

- **Có nhóm (grouped)** — một sinh viên (`id_student`) có thể xuất hiện ở nhiều môn–kỳ, nên các bản ghi không độc lập. Phân chia theo dòng một cách ngây thơ có thể đưa cùng một sinh viên vào cả train và test (*rò rỉ theo nhóm*).
- **Mất cân bằng (nhẹ)** — lớp at-risk chiếm ~52,8%; phân chia ngẫu nhiên vẫn có thể làm lệch tỉ lệ tập kiểm tra và gây sai lệch đánh giá.
- **Theo thời gian (time-aware)** — sáu mốc dùng chung một trục so sánh (RQ1), nên tập kiểm tra phải **đồng nhất** qua các mốc, nếu khác thì đường cong hiệu năng không so sánh được.

## 2. Các chiến lược được so sánh

| Chiến lược | Cách hoạt động | Ưu điểm | Nhược điểm |
|---|---|---|---|
| Hold-out đơn | Một lần cắt train/test | Đơn giản, nhanh | Phương sai cao; phụ thuộc một lần phân chia |
| k-fold CV | k fold kiểm định luân phiên | Dùng hết dữ liệu; phương sai thấp hơn | Chi phí k lần; một seed vẫn phụ thuộc phân chia |
| k-fold lặp lại | k-fold lặp qua nhiều seed | Trung bình ± độ lệch ổn định; không phụ thuộc seed | Chi phí cao nhất |
| Nested CV | CV trong để tinh chỉnh, ngoài để ước lượng | Ước lượng không thiên lệch khi có tinh chỉnh | Rất tốn kém; phức tạp |

## 3. Thiết kế lựa chọn (theo đề cương)

**Hold-out 20% tập kiểm tra + kiểm định chéo 5-fold lặp qua 5 seed trên tập huấn luyện.**

- **Tập kiểm tra 20% cố định một lần**, theo `id_student`, và dùng lại ở mọi mốc (STT 8) để sáu điểm so sánh được.
- Trên 80% còn lại, CV **5-fold × 5 seed** giảm phương sai do một lần phân chia; chỉ số báo cáo dạng **trung bình ± độ lệch chuẩn** qua 25 lần khớp.
- Cả phân chia kiểm tra lẫn các fold CV đều **bảo toàn nhóm (theo `id_student`) và phân tầng (theo `at_risk`)** qua `StratifiedGroupKFold` (xem `src/evaluation/split_harness.py`).

Thiết kế này cân bằng độ ổn định và chi phí: k-fold lặp cho ước lượng ổn định, còn một tập kiểm tra hold-out cố định giữ khả năng so sánh qua các mốc. Nested CV được đánh giá là quá tốn kém so với phạm vi dự kiến.

## 4. Quy ước báo cáo chỉ số

Vì lớp dương (at-risk) là lớp không được bỏ sót, chỉ số chính là **PR-AUC** và **recall trên lớp at-risk**, báo cáo dạng **trung bình ± độ lệch** qua các fold/seed. Accuracy chỉ báo cáo như chỉ số phụ (dễ gây hiểu nhầm khi có mất cân bằng).

## 5. Thuộc tính đã kiểm chứng (trên dữ liệu này)

Dùng phân chia 20% cố định trên `master_raw` (32.593 dòng): **0 sinh viên trùng** giữa train và test, và tỉ lệ at-risk được bảo toàn (train ≈ 0,53, test ≈ 0,52, chênh lệch ≤ 0,02). Các kiểm tra này được khẳng định trong `tests/test_leakage.py`.

## 6. Phân chia đã vật chất hoá và dữ liệu nằm ở đâu

Phép phân chia được định nghĩa **một lần** và lưu lại bởi `src/evaluation/make_split.py`:

| Sản phẩm | Vị trí | Có commit? |
|---|---|---|
| Danh sách `id_student` tập test (5.756 SV) | `data/splits/test_student_ids.csv` | có |
| Báo cáo kiểm chứng (theo từng dataset) | `reports/tables/split_report.csv` | có |
| Dữ liệu train/test đã tạo (master + từng mốc) | `data/splits/*_train.parquet`, `*_test.parquet` | git bỏ qua, tái tạo được |

Báo cáo phân chia xác nhận thiết kế trên `master_raw` và **cả sáu mốc**: train **26.104** dòng · test **6.489** dòng (5.756 SV) · at-risk **0,530 / 0,520** · **0 trùng** — y hệt ở mọi mốc. Giai đoạn mô hình nạp phân chia của một mốc bằng một lệnh:

```python
from src.evaluation.make_split import load_checkpoint_split
X_train, X_test = load_checkpoint_split(40)   # train/test tại mốc 40%
```

## Tài liệu tham khảo

1. M. Adnan và cộng sự, *IEEE Access*, vol. 9, tr. 7519–7539, 2021.
2. N. Tomasevic, N. Gvozdenovic, S. Vranes, *Computers & Education*, vol. 143, art. 103676, 2020.
