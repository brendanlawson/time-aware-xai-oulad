# Quy tắc phòng tránh rò rỉ dữ liệu theo thời gian

*Các quy tắc bảo đảm mỗi bộ dữ liệu theo mốc chỉ dùng thông tin có tại thời điểm dự đoán*

**DSP391m – Nhóm 1 · Báo cáo 2 (Tác vụ dữ liệu), Chương 3 · Hạng mục STT 12 (Khoa)**
*Tham chiếu: biên bản BB-B0-N1 (Bước 0). Được kiểm thử tự động bởi `tests/test_leakage.py`.*

---

## 1. Rò rỉ theo thời gian là gì

**Rò rỉ theo thời gian (temporal/look-ahead leakage)** là việc sử dụng dữ liệu phát sinh *sau* thời điểm dự đoán. Nó làm hiệu năng cao giả tạo khi phát triển và biến mất khi triển khai, nơi dữ liệu tương lai không tồn tại. Vì đề tài dự đoán tại sáu mốc (10–100% thời lượng khoá học), mọi đặc trưng tại mốc *t* phải tính được từ dữ liệu có **trước hoặc tại** ngày mốc. Ngày mốc cho mỗi môn–kỳ là `round(module_presentation_length × t / 100)` (xem `data/checkpoint_map.csv`).

## 2. Ba quy tắc

### Quy tắc 1 — Loại bài đánh giá nộp sau mốc
Chỉ giữ một lần nộp nếu `date_submitted ≤ cutoff_day`. Một bài nộp ngày 120 không thể phục vụ dự đoán tại ngày 100. Do đó `mean_score_to_date`, `weighted_score_to_date` và `n_assessments_submitted` **chỉ** tích luỹ các bài nộp tới ngày mốc.

### Quy tắc 2 — Loại lượt tương tác VLE có ngày vượt mốc
Chỉ giữ một dòng clickstream nếu `date ≤ cutoff_day`. Mọi đặc trưng tương tác (`total_clicks`, `n_days_active`, `clicks_*`, `max_clicks_single_day`, `mean_clicks_per_active_day`, `days_since_last_activity`) được tổng hợp từ clickstream đã cắt. Cài đặt bởi hàm `cut_at_checkpoint()` trong `src/data/time_utils.py`.

### Quy tắc 3 — Xử lý Withdrawn-trước-mốc theo Bước 0 (Phương án A)
Sinh viên rút môn trước mốc *t* vẫn được **giữ** và **gán nhãn at-risk**; đặc trưng của họ chỉ phản ánh hoạt động trước khi rút (Quy tắc 1–2 đã loại sự kiện sau đó). Mức hoạt động thấp này là tín hiệu cảnh báo sớm hợp lệ, không phải rò rỉ. Nhãn lấy từ `final_result` và cố định qua các mốc, nên không bao giờ làm rò rỉ kết quả tương lai vào đặc trưng. Tuy vậy, việc giữ lại sinh viên đã rút là một **lựa chọn quần thể có hệ quả đo được**: trên toàn quần thể, một phần hiệu năng đo được đến từ việc nhận diện lại những sinh viên đã rời đi, và recall trên lớp at-risk của nhóm còn-đang-học thấp hơn ở mọi mốc. Điều này không vi phạm quy tắc nào ở trên — không thông tin nhãn nào lọt vào đặc trưng — nhưng nó thay đổi ý nghĩa của các chỉ số công bố. Xem phân tích độ nhạy (`tools/sensitivity_active.py` → `reports/tables/sensitivity_active_xgb.csv`) và mục làm rõ estimand trong *Target_Variable_Definition* về quy ước báo cáo kép của đề tài.

## 3. Nguyên tắc hỗ trợ — chỉ khớp trên tập huấn luyện

Ngoài trục thời gian, mọi thành phần *học* từ dữ liệu (thống kê điền khuyết, bộ mã hoá, bộ chuẩn hoá, tái lấy mẫu) phải được khớp **chỉ trên fold huấn luyện** rồi áp dụng cho tập kiểm tra (xem STT 22). Khớp trên toàn bộ dữ liệu trước khi phân chia sẽ làm rò rỉ thông tin tập kiểm tra sang tập huấn luyện và cho ước lượng lạc quan sai lệch.

## 4. Kiểm thử tự động

`tests/test_leakage.py` khẳng định, cho cả sáu mốc, rằng không bản ghi đã cắt nào có ngày vượt ngày mốc, trên cả clickstream và bài nộp; số bản ghi không giảm theo *t*; và *t = 100%* giữ lại toàn bộ bản ghi có ngày. Đồng thời kiểm tra phân chia không trùng sinh viên và bảo toàn tỉ lệ lớp, và một kiểm thử khẳng định median điền khuyết cùng ngưỡng winsorize **chỉ học trên train** rồi áp cho test, cùng một test allow-list (không cột rò rỉ nào lọt vào X) và một test khẳng định idle ở *t = 100%* khớp master. **Kết quả: toàn bộ kiểm thử rò rỉ tự động đều đạt — xem `tests/test_leakage.py`** (bộ kiểm thử được bổ sung theo thời gian nên không ghi cứng số lượng ở đây).

## 5. Ví dụ minh hoạ (`AAA / 2013J`, dài 268 ngày)

| t% | cutoff_day | Số lượt tương tác giữ lại (không giảm) |
|---|---|---|
| 10 | 27 | nhỏ nhất |
| 40 | 107 | lớn hơn |
| 100 | 268 | toàn bộ lượt có ngày |

Sự tăng đơn điệu xác nhận phép cắt áp dụng đúng: thời gian trôi qua nhiều hơn ⇒ nhiều bản ghi hơn (không bao giờ ít hơn).

## Tài liệu tham khảo

1. M. Adnan và cộng sự, *IEEE Access*, vol. 9, tr. 7519–7539, 2021.
3. J. Kuzilek, M. Hlosta, Z. Zdrahal, *Scientific Data*, vol. 4, art. 170171, 2017.
