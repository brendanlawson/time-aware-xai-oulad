# Đặc tả Dữ liệu cho Học máy Có Nhận thức Thời gian và Khả năng Giải thích trên OULAD

**DSP391m – Nhóm 1 · Báo cáo 2 (Nhiệm vụ Dữ liệu), Chương 3 · Nhiệm vụ 3.1 — Đặc tả Dữ liệu**

---

## Tóm tắt

Tài liệu này đặc tả các yêu cầu dữ liệu cho đề tài "Học máy Có Nhận thức Thời gian và Khả năng Giải thích (Time-Aware Explainable ML) để Dự đoán Sớm Sinh viên Có Nguy cơ trên OULAD." Ba câu hỏi nghiên cứu điều hướng quá trình đặc tả: (CH1) xác định mốc tiến độ khóa học sớm nhất có thể dự đoán tin cậy và thuật toán hiệu quả nhất tại mốc đó; (CH2) đánh giá độ ổn định của các giải thích hậu nghiệm SHAP/LIME qua các cửa sổ thời gian; và (CH3) đánh giá ảnh hưởng của các chiến lược xử lý mất cân bằng lớp—SMOTE, ADASYN, và điều chỉnh trọng số lớp (class-weight)—lên độ chính xác dự đoán và tính nhất quán của giải thích. Mỗi yêu cầu được suy diễn trực tiếp từ ít nhất một câu hỏi nghiên cứu và được ánh xạ tới bảng cụ thể trong Bộ dữ liệu Phân tích Học tập Trường Đại học Mở (Open University Learning Analytics Dataset — OULAD) [3]. Phân tích xác nhận rằng OULAD cung cấp đầy đủ các nhóm dữ liệu cần thiết—ngữ cảnh nhân khẩu học, hành vi tương tác có dấu thời gian, và thành tích học tập theo chiều dọc—ở quy mô và độ chi tiết thời gian đủ để hỗ trợ cả ba câu hỏi nghiên cứu.

---

## 1. Giới thiệu

Nhận dạng sớm sinh viên có nguy cơ là một thách thức trọng tâm trong lĩnh vực phân tích học tập (learning analytics). Can thiệp trước khi sinh viên mất kết nối hoặc thất bại đòi hỏi các mô hình dự đoán vừa chính xác tại các mốc tiến độ sớm vừa có thể giải thích được cho cố vấn học tập. Đề tài này hiện thực hóa bài toán trên OULAD [3], bộ dữ liệu quan hệ công khai do Trường Đại học Mở (The Open University, UK) phát hành. Trước khi tiến hành bất kỳ công việc mô hình hóa nào, dữ liệu cần thiết phải được xác định chặt chẽ và biện hộ dựa trên các câu hỏi nghiên cứu. Tài liệu này thực hiện nghĩa vụ đó trong vai trò Nhiệm vụ 3.1 trong chuỗi bàn giao capstone DSP391m.

---

## 2. Câu hỏi Nghiên cứu và Nhu cầu Dữ liệu

Ba câu hỏi nghiên cứu đặt ra các yêu cầu dữ liệu riêng biệt:

- **CH1** (Mốc tin cậy sớm nhất): đòi hỏi hồ sơ có chỉ số thời gian về hành vi và thành tích của từng sinh viên để các đặc trưng có thể được tính toán tại nhiều ngưỡng tiến độ rời rạc (ví dụ: 20%, 40%, 60%, 80% độ dài khóa học). Điều này đòi hỏi cả sự kiện clickstream (luồng nhấp chuột) lẫn bài nộp kiểm tra mang thông tin ngày tháng, cùng với tổng thời lượng khóa học làm cơ sở tính phần trăm tiến độ.

- **CH2** (Độ ổn định giải thích): đòi hỏi cùng các vectơ đặc trưng dùng cho dự đoán phải có mặt tại mỗi mốc kiểm tra để giá trị phân bổ SHAP và LIME có thể được so sánh theo thời gian. Không cần thêm bảng nào ngoài những bảng phục vụ CH1, nhưng điều này củng cố yêu cầu về các cột đặc trưng nhất quán và được định nghĩa rõ ràng.

- **CH3** (Xử lý mất cân bằng): đòi hỏi nhãn kết quả nhị phân và thông tin về phân phối biên của nó trong toàn bộ tập dữ liệu. Cả SMOTE/ADASYN (tổng hợp mẫu lớp thiểu số) lẫn điều chỉnh trọng số lớp đều hoạt động trên cột nhãn và toàn bộ ma trận đặc trưng. Điều này làm cho biến kết quả và toàn bộ tập đặc trưng đều cần thiết.

---

## 3. Yêu cầu Dữ liệu Ánh xạ tới Các Bảng OULAD

Bảng 1 trình bày từng yêu cầu dữ liệu, câu hỏi nghiên cứu mà nó phục vụ, và bảng nguồn OULAD cung cấp dữ liệu đó.

**Bảng 1. Yêu cầu Dữ liệu và Nguồn OULAD**

| Yêu cầu | Mục đích / Lý do cần thiết | Bảng nguồn OULAD | Cột chính |
|---|---|---|---|
| Nhãn kết quả nhị phân (at-risk) | Định nghĩa mục tiêu dự đoán; cần thiết cho cả ba CH | `studentInfo` | `final_result` (Pass/Distinction → không nguy cơ; Fail/Withdrawn → có nguy cơ) |
| Hành vi tương tác có dấu thời gian | CH1 cần tín hiệu có nhận thức thời gian để xây dựng đặc trưng tại mốc kiểm tra; CH2 cần đặc trưng tương tác nhất quán | `studentVle` (~10,6 triệu hàng), `vle` | `date`, `sum_clicks`, `id_site`, `activity_type` |
| Thành tích học tập theo chiều dọc | Tín hiệu điểm số sớm cho đặc trưng tại mốc kiểm tra (CH1, CH2); đóng góp vào cấu trúc lớp (CH3) | `studentAssessment`, `assessments` | `date_submitted`, `score`, `is_banked`, `assessment_type`, `weight`, `date` (hạn chót) |
| Ngữ cảnh nhân khẩu học | Đặc trưng thứ cấp phục vụ phân tích công bằng và đầu vào mô hình (tất cả CH) | `studentInfo` | `gender`, `region`, `highest_education`, `imd_band`, `age_band`, `num_of_prev_attempts`, `studied_credits`, `disability` |
| Lịch đăng ký của sinh viên | Ghi nhận đăng ký muộn và hủy đăng ký sớm như tín hiệu hành vi (CH1) | `studentRegistration` | `date_registration`, `date_unregistration` |
| Lịch trình / thời lượng khóa học | Chuyển đổi ngày sự kiện thô thành phần trăm tiến độ khóa học (CH1) | `courses` | `module_presentation_length` |

---

## 4. Nhóm Đặc trưng và Biến Mục tiêu

Ba nhóm đặc trưng được xây dựng từ các bảng đã xác định, cùng với biến mục tiêu:

**4.1 Đặc trưng Nhân khẩu học (Demographic Features)**
Lấy từ `studentInfo` và `studentRegistration`. Bao gồm giới tính, khu vực, trình độ học vấn cao nhất trước đó, chỉ số thiệt thòi IMD (IMD deprivation band), nhóm tuổi, số lần thử trước đó, số tín chỉ đăng ký, tình trạng khuyết tật, ngày đăng ký, và (nếu có) ngày hủy đăng ký. Đặc trưng nhân khẩu học là tĩnh theo từng bản ghi sinh viên-học phần-đợt trình bày và đóng vai trò là biến hiệp biến nền.

**4.2 Đặc trưng Tương tác (VLE — Virtual Learning Environment)**
Lấy từ `studentVle` (sự kiện tương tác) kết nối với `vle` (siêu dữ liệu loại hoạt động). Dữ liệu clickstream thô (~10.655.280 tương tác) được tổng hợp theo sinh viên, học phần-đợt trình bày, và mốc tiến độ khóa học để tạo ra số lượng và tốc độ hoạt động theo từng loại (ví dụ: `oucontent`, `quiz`, `resource`, `forumng`). Cột `date` trong `studentVle` là thiết yếu: đây là neo thời gian cho phép đặc trưng được cắt ngắn tại mỗi ngưỡng mốc kiểm tra.

**4.3 Đặc trưng Thành tích (Assessment — Kiểm tra)**
Lấy từ `studentAssessment` (hồ sơ nộp bài) kết nối với `assessments` (siêu dữ liệu kiểm tra). Đặc trưng bao gồm điểm trung bình có trọng số lũy tích, tỷ lệ bài kiểm tra nộp đúng hạn, và việc có bài kiểm tra nào được lưu ngân hàng (banked) hay không. Cột `date_submitted` trong `studentAssessment` cho phép cắt ngắn theo thời gian tương tự như cách tiếp cận đối với đặc trưng tương tác VLE.

**4.4 Biến Mục tiêu**
Nhãn nhị phân được suy diễn từ `final_result` trong `studentInfo`. Các bản ghi với `final_result` ∈ {Fail, Withdrawn} được gán nhãn có nguy cơ (lớp dương = 1); các bản ghi {Pass, Distinction} được gán nhãn không nguy cơ (0). Tỷ lệ có nguy cơ quan sát được trong toàn bộ tập dữ liệu xấp xỉ 52,8%, cho thấy mất cân bằng lớp nhẹ, là động lực cho CH3.

---

## 5. Hạt nhân Dữ liệu và Khóa Tổng hợp

Đơn vị phân tích là một bản ghi trên mỗi bộ ba **(id\_student, code\_module, code\_presentation)**. Vì một sinh viên có thể đăng ký nhiều học phần-đợt trình bày, khóa tổng hợp (composite key) gồm ba cột này là bắt buộc để xác định duy nhất mỗi quan sát. Tất cả các bảng đặc trưng được kết nối theo khóa tổng hợp này trước khi tiến hành mô hình hóa. Tập dữ liệu phân tích cuối cùng chứa **32.593** bản ghi như vậy, lấy từ **28.785** sinh viên duy nhất trên **22** đợt trình bày học phần.

---

## 6. Vai trò của Từng Bảng OULAD

Bảng 2 tóm tắt lý do tất cả bảy bảng OULAD đều cần thiết và chỉ ra bảng nào có chỉ số thời gian.

**Bảng 2. Vai trò Các Bảng OULAD**

| Bảng | Vai trò trong Nghiên cứu này | Có chỉ số thời gian? |
|---|---|---|
| `studentInfo` | Cung cấp nhãn kết quả và tất cả đặc trưng nhân khẩu học | Không |
| `studentRegistration` | Cung cấp ngày đăng ký và ngày hủy đăng ký theo từng lần ghi danh | Một phần (`date_registration`, `date_unregistration`) |
| `studentVle` | Nguồn chính của hành vi tương tác; ~10,6 triệu sự kiện clickstream | Có (`date`) |
| `vle` | Ánh xạ `id_site` tới `activity_type`; cần để tạo đặc trưng tương tác theo loại | Không |
| `studentAssessment` | Hồ sơ nộp bài kiểm tra với ngày nộp và điểm số | Có (`date_submitted`) |
| `assessments` | Cung cấp loại kiểm tra, trọng số, và ngày hạn chót; cần để tính đặc trưng thành tích có trọng số | Một phần (`date` là hạn chót) |
| `courses` | Cung cấp `module_presentation_length` để chuyển đổi ngày sự kiện thành phần trăm tiến độ | Không |

Các cột có chỉ số thời gian—`studentVle.date` và `studentAssessment.date_submitted`—là nền tảng kiến trúc của yêu cầu có nhận thức thời gian. Nếu thiếu chúng, việc cắt ngắn theo mốc kiểm tra (thiết yếu cho CH1 và CH2) không thể thực hiện được.

---

## 7. Quy mô Dữ liệu và Tính Đầy đủ

Các thống kê quy mô sau đây xác nhận OULAD đủ điều kiện cho nghiên cứu dự kiến:

- **32.593** bản ghi sinh viên-học phần-đợt trình bày (hạt nhân phân tích)
- **28.785** sinh viên duy nhất
- **22** đợt trình bày học phần (7 khóa học × nhiều năm trình bày)
- **7** bảng quan hệ
- **10.655.280** hàng tương tác VLE
- **173.912** hàng nộp bài kiểm tra
- **~52,8%** tỷ lệ có nguy cơ (mất cân bằng nhẹ; biện hộ cho CH3 nhưng không hạn chế nghiêm trọng việc mô hình hóa)

Quy mô tập dữ liệu đủ để huấn luyện và đánh giá nhiều bộ phân loại tại mỗi ngưỡng mốc kiểm tra, tạo ra các phân bổ SHAP/LIME ổn định, và so sánh ba chiến lược xử lý mất cân bằng. Độ chi tiết thời gian (độ phân giải hàng ngày trong cả `studentVle` và `studentAssessment`) đủ để hiện thực hóa các ngưỡng mốc kiểm tra tại các khoảng cách tinh tế.

---

## 8. Kết luận về Tính Đầy đủ của Dữ liệu

OULAD cung cấp tất cả các nhóm dữ liệu yêu cầu bởi CH1–CH3: nhãn kết quả nhị phân, hành vi tương tác có dấu thời gian, thành tích kiểm tra theo chiều dọc, và ngữ cảnh nhân khẩu học. Khóa tổng hợp `(id_student, code_module, code_presentation)` đảm bảo liên kết không mơ hồ qua tất cả bảy bảng. Với hơn 32.000 bản ghi phân tích, hơn 10,6 triệu sự kiện tương tác có dấu thời gian, và độ phân giải thời gian một ngày, tập dữ liệu cung cấp quy mô và độ chi tiết đủ để hỗ trợ mô hình hóa mốc kiểm tra có nhận thức thời gian, phân tích độ ổn định giải thích, và thử nghiệm xử lý mất cân bằng. Không cần nguồn dữ liệu bên ngoài nào để giải quyết ba câu hỏi nghiên cứu.

---

## Tài liệu Tham khảo

[3] J. Kuzilek, M. Hlosta, Z. Zdrahal, "Open University Learning Analytics dataset," *Scientific Data*, vol. 4, art. 170171, 2017.
