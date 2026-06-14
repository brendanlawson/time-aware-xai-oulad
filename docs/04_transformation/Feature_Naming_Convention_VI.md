# Quy Tắc Đặt Tên Đặc Trưng Dẫn Xuất

**Phụ đề:** Đảm bảo khả năng đọc hiểu kết quả SHAP/LIME thông qua tên đặc trưng nhất quán

_DSP391m – Nhóm 1 · Báo cáo 2 (Data Tasks) · Hạng mục STT 40 (Bình)_

---

## 1. Mục đích

Các công cụ giải thích học máy (machine learning explainability) như SHAP và LIME hiển thị tên đặc trưng (feature name) nguyên văn trong kết quả đầu ra. Nếu một đặc trưng được đặt tên là `f_017` hay `x3`, giảng viên đọc giải thích sẽ không thể xác định ý nghĩa của con số đó mà không tra cứu bảng riêng. Tài liệu này thiết lập một quy tắc đặt tên bắt buộc cho mọi đặc trưng dẫn xuất (derived feature) được tạo ra trong dự án, nhằm đảm bảo các giải thích có thể được hiểu ngay lập tức.

Quy tắc đã được toàn bộ thành viên Nhóm 1 xem xét và thông qua, áp dụng cho mọi đặc trưng bổ sung vào bảng tổng hợp (master table) và các tập dữ liệu checkpoint (checkpoint datasets) về sau.

---

## 2. Quy Tắc Đặt Tên

Tất cả tên đặc trưng tuân theo định dạng **snake\_case** (chữ thường, chữ số và dấu gạch dưới — không dùng khoảng trắng, camelCase hay dấu gạch ngang).

### 2.1 Ý nghĩa của các tiền tố và hậu tố

| Mẫu | Ý nghĩa | Ví dụ |
|---|---|---|
| `n_...` | Số nguyên đếm số lượng (integer count) | `n_days_active`, `n_assessments_submitted` |
| `clicks_<activity_type>` | Số lần nhấp cho một loại hoạt động VLE cụ thể | `clicks_forumng`, `clicks_quiz` |
| `..._to_date` | Giá trị tích lũy **chỉ** từ dữ liệu đến checkpoint hiện tại (không rò rỉ dữ liệu tương lai) | `mean_score_to_date`, `weighted_score_to_date` |
| `total_...` | Tổng cộng (sum aggregation) được thể hiện rõ ràng | `total_clicks` |
| `max_...` | Giá trị lớn nhất (maximum aggregation) được thể hiện rõ ràng | `max_clicks_single_day` |
| `mean_...` | Trung bình cộng (arithmetic mean aggregation) được thể hiện rõ ràng | `mean_clicks_per_active_day` |

### 2.2 Quy tắc chung

1. Tên phải mô tả **cái gì** được đo lường, không phải **cách** tính toán.
2. Phần loại hoạt động trong `clicks_<activity_type>` phải khớp chính xác với chuỗi trong cột `activity_type` của tệp `vle.csv` thuộc bộ dữ liệu OULAD (ví dụ: `forumng`, `oucontent`, `resource`).
3. Cột nhị phân (boolean/binary) dùng dạng tính từ hoặc quá khứ phân từ (`at_risk`, `not_submitted`).
4. Tên không được vượt quá 40 ký tự.

---

## 3. Danh Sách Đặc Trưng Chuẩn

Bảng dưới đây là nguồn tham chiếu duy nhất (single source of truth) cho tất cả đặc trưng dùng trong mô hình hóa. Bất kỳ đặc trưng mới nào cũng phải tuân theo quy tắc này và được bổ sung vào đây.

| Đặc trưng | Ý nghĩa | Nhóm |
|---|---|---|
| `total_clicks` | Tổng số lần nhấp VLE của sinh viên đến checkpoint | Tương tác (Engagement) |
| `n_days_active` | Số ngày riêng biệt có ít nhất một lần nhấp | Tương tác |
| `clicks_forumng` | Số lần nhấp vào loại hoạt động Forum-NG | Tương tác |
| `clicks_oucontent` | Số lần nhấp vào loại hoạt động OUContent | Tương tác |
| `clicks_resource` | Số lần nhấp vào loại hoạt động Resource | Tương tác |
| `clicks_homepage` | Số lần nhấp vào loại hoạt động Homepage | Tương tác |
| `clicks_oucollaborate` | Số lần nhấp vào loại hoạt động OUCollaborate | Tương tác |
| `clicks_quiz` | Số lần nhấp vào loại hoạt động Quiz | Tương tác |
| `clicks_subpage` | Số lần nhấp vào loại hoạt động Subpage | Tương tác |
| `clicks_url` | Số lần nhấp vào loại hoạt động URL | Tương tác |
| `max_clicks_single_day` | Số lần nhấp tối đa được ghi nhận trong một ngày bất kỳ | Tương tác |
| `mean_clicks_per_active_day` | Trung bình số lần nhấp mỗi ngày hoạt động (`total_clicks / n_days_active`) | Tương tác |
| `days_since_last_activity` | Số ngày từ lần nhấp cuối cùng đến checkpoint hiện tại | Tương tác |
| `mean_score_to_date` | Điểm trung bình bài kiểm tra từ các lần nộp đến checkpoint | Kết quả học tập (Performance) |
| `weighted_score_to_date` | Điểm có trọng số theo tỷ lệ bài kiểm tra, đến checkpoint | Kết quả học tập |
| `n_assessments_submitted` | Số bài kiểm tra đã nộp đến checkpoint | Kết quả học tập |
| `not_submitted` | Số bài kiểm tra đã đến hạn nhưng chưa nộp đến checkpoint | Kết quả học tập |
| `at_risk` | **Biến mục tiêu (target variable)** — 1 nếu sinh viên bỏ học hoặc trượt, 0 nếu ngược lại | Mục tiêu (Target) |

---

## 4. Tại Sao Điều Này Quan Trọng Với Khả Năng Giải Thích

Biểu đồ tóm tắt SHAP (SHAP summary plot) và giải thích bảng của LIME (LIME tabular explanation) hiển thị tên đặc trưng dưới dạng nhãn trục hoặc hàng bảng. Tên như `mean_score_to_date` cho giảng viên biết ngay mô hình đang phản ứng với điểm trung bình của sinh viên tính đến thời điểm hiện tại, trong khi `weighted_score_to_date` báo hiệu rằng các bài kiểm tra có trọng số cao đang tạo ra tín hiệu chính. Hậu tố `_to_date` đặc biệt quan trọng: nó chứng minh cho người đánh giá rằng đặc trưng là an toàn về mặt thời gian (temporal safety), tức là chỉ được tính từ dữ liệu quá khứ tại thời điểm dự đoán.

Giảng viên nhận cảnh báo sớm sẽ đọc những tên này mà không có nền tảng về học máy. Tên rõ ràng giảm tải nhận thức khi diễn giải dự đoán và tăng khả năng hệ thống được tin tưởng và hành động theo.

---

## 5. Tuân Thủ và Kiểm Soát

- Mọi đặc trưng mới thêm vào pipeline phải tuân theo quy tắc này trước khi pull request (yêu cầu hợp nhất mã nguồn) được chấp nhận.
- Bộ kiểm thử CI (continuous integration) bao gồm kiểm tra định dạng tên (`pytest tests/test_feature_names.py`) sẽ từ chối bất kỳ cột nào không khớp với các mẫu đã được phê duyệt.
- Bất kỳ trường hợp ngoại lệ nào đều cần có văn bản giải trình và sự phê duyệt của cả nhóm.

---

_Được phê duyệt bởi Nhóm 1 DSP391m. Cập nhật lần cuối: 2026-06-14._
