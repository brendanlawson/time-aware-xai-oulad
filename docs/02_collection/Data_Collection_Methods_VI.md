# Phương pháp Thu thập Dữ liệu và Lựa chọn Nguồn Dữ liệu

**Lý giải việc sử dụng bộ dữ liệu công khai OULAD cho bài toán dự đoán sinh viên có nguy cơ học tập**

DSP391m – Nhóm 1 · Báo cáo 2 (Nhiệm vụ Dữ liệu), Chương 3 · Hạng mục công việc STT 23 (Sơn)

---

## 1. Tổng quan

Mọi dự án khoa học dữ liệu đều bắt đầu bằng quyết định về nguồn và phương thức thu thập dữ liệu. Chương này phân tích các loại nguồn dữ liệu chính, đánh giá ưu nhược điểm của từng loại, và từ đó lập luận tại sao Bộ dữ liệu Phân tích Học tập của Đại học Mở (Open University Learning Analytics Dataset – OULAD) là lựa chọn phù hợp cho dự án *"Dự đoán sinh viên có nguy cơ học tập sớm theo phương pháp Học máy có thể giải thích và nhận biết thời gian trên OULAD"*.

---

## 2. Các loại nguồn dữ liệu và sự đánh đổi

Trong các dự án khai thác dữ liệu giáo dục và phân tích học tập, bốn loại nguồn dữ liệu chính thường được xem xét.

### 2.1 Cơ sở dữ liệu nội bộ của tổ chức

Hệ thống thông tin sinh viên (Student Information System – SIS), nhật ký hệ thống quản lý học tập (LMS) và hồ sơ điểm số của một trường đại học là nguồn dữ liệu phong phú nhất cho một bối cảnh cụ thể. Thiết kế thu thập được kiểm soát hoàn toàn, định nghĩa trường dữ liệu được biết chính xác và việc liên kết các bảng dữ liệu là đơn giản.

**Sự đánh đổi:** Dữ liệu không thể truy cập công khai; nghiên cứu bên ngoài đòi hỏi phê duyệt đạo đức và ký kết thỏa thuận chia sẻ dữ liệu. Kết quả mang tính đặc thù theo tổ chức và khó tái lập hay so sánh giữa các nghiên cứu khác nhau.

### 2.2 Giao diện lập trình ứng dụng (API)

Nhiều nền tảng học tập (Canvas, Moodle, edX) cung cấp API REST cho phép trích xuất tự động dữ liệu hoạt động khóa học, bài đăng diễn đàn và điểm số. API cung cấp dữ liệu cập nhật, có cấu trúc rõ ràng và có thể tự động hóa quy trình thu thập.

**Sự đánh đổi:** Truy cập API đòi hỏi thông tin xác thực và sự cho phép của tổ chức. Giới hạn tốc độ và thay đổi lược đồ có thể làm gián đoạn quá trình thu thập dài hạn. Thông tin nhận dạng cá nhân (Personally Identifiable Information – PII) thường hiện diện trong dữ liệu thô, đòi hỏi bước ẩn danh hóa riêng biệt trước khi phân tích. Khả năng tái lập thấp vì trạng thái nền tảng thay đổi theo thời gian.

### 2.3 Thu thập dữ liệu từ web (Web scraping)

Danh mục khóa học công khai, đánh giá của sinh viên hoặc diễn đàn thảo luận có thể được thu thập bằng kỹ thuật cào web để bổ sung dữ liệu có cấu trúc. Phương pháp này có thể tiếp cận thông tin không được cung cấp qua API.

**Sự đánh đổi:** Tính hợp pháp và đạo đức khác nhau tùy theo pháp luật và điều khoản dịch vụ từng quốc gia. Cấu trúc HTML thay đổi thường xuyên khiến các trình thu thập dễ bị hỏng. Chất lượng dữ liệu không đồng đều và PII có thể vô tình bị thu thập. Khả năng tái lập thấp vì nội dung web thay đổi liên tục.

### 2.4 Bộ dữ liệu công khai / Dữ liệu thứ cấp (Secondary data)

Các bộ dữ liệu được tổ chức nghiên cứu hoặc cơ quan chính phủ phát hành cho phép tải xuống, đã được ẩn danh hóa, và đi kèm với lược đồ được ghi chép rõ ràng cùng giấy phép sử dụng. Dữ liệu thứ cấp (secondary data) là dữ liệu được thu thập bởi bên thứ ba cho mục đích có thể khác với mục tiêu của nhà nghiên cứu hiện tại.

**Sự đánh đổi:** Không có quyền kiểm soát thiết kế thu thập ban đầu (công cụ đo lường, thời điểm thu thập, lựa chọn đặc trưng). Tuy nhiên, tính sẵn có là ngay lập tức, việc ẩn danh hóa được thực hiện tại nguồn, và cùng một bộ dữ liệu có thể được sử dụng bởi nhiều nghiên cứu độc lập, tạo điều kiện so sánh trực tiếp.

### 2.5 Bảng so sánh tổng hợp

| Tiêu chí | CSDL nội bộ | API | Web scraping | Công khai / Thứ cấp |
|---|---|---|---|---|
| Kiểm soát thiết kế thu thập | Cao | Trung bình | Thấp | Không có |
| Sẵn có ngay lập tức | Thấp | Trung bình | Trung bình | **Cao** |
| Yêu cầu ẩn danh hóa | Có | Có | Có | **Đã thực hiện sẵn** |
| Khả năng tái lập | Thấp | Thấp | Rất thấp | **Cao** |
| Khả năng so sánh với nghiên cứu trước | Thấp | Thấp | Thấp | **Cao** |
| Mức độ phức tạp về pháp lý/đạo đức | Cao | Trung bình | Cao | **Thấp (giấy phép CC)** |

---

## 3. Tiêu chí lựa chọn nguồn dữ liệu cho dự án

Dự án yêu cầu một bộ dữ liệu đồng thời thỏa mãn tất cả các điều kiện sau:

1. **Có thể truy cập công khai** — bộ dữ liệu phải được tải xuống tự do mà không cần thỏa thuận truy cập của tổ chức, đảm bảo kết quả có thể được tái lập hoàn toàn bởi các nhà nghiên cứu độc lập.
2. **Có đủ ba nhóm đặc trưng cần thiết** — (a) *nhân khẩu học sinh viên* (nhóm tuổi, trình độ học vấn cao nhất, tình trạng khuyết tật, khu vực địa lý, chỉ số IMD), (b) *mức độ tương tác / dòng nhấp chuột VLE* (số lần tương tác hàng ngày với tài nguyên môi trường học tập ảo), và (c) *kết quả đánh giá học tập* (điểm số và ngày nộp bài kiểm tra và thi cử).
3. **Có biến mục tiêu có nhãn** — trường `final_result` phải tồn tại với các giá trị Pass, Distinction, Fail hoặc Withdrawn, để có thể trực tiếp xây dựng nhãn phân loại nhị phân `at_risk = {Fail, Withdrawn}`.
4. **Được sử dụng bởi các nghiên cứu nền tảng** — để cho phép so sánh phương pháp luận trực tiếp, bộ dữ liệu phải là bộ dữ liệu được sử dụng trong các nghiên cứu tham chiếu chính [1] và [2].

---

## 4. Lý do OULAD phù hợp với dự án này

Bộ dữ liệu Phân tích Học tập của Đại học Mở (OULAD) [3] được phát hành bởi The Open University (Vương quốc Anh) và được lưu trữ công khai tại https://analyse.kmi.open.ac.uk/open_dataset cùng với một bản sao trên Kaggle.

**Các đặc điểm chính:**

- **Quy mô:** 32.593 bản ghi sinh viên-module-kỳ học; 28.785 sinh viên duy nhất; 22 kết hợp module-kỳ học trong 7 bảng quan hệ.
- **Phạm vi đặc trưng:** Cả ba nhóm đặc trưng cần thiết đều có mặt — `studentInfo` (nhân khẩu học), `studentVle` (số lần nhấp chuột VLE hàng ngày), và `studentAssessment` / `assessments` (điểm số và thời hạn nộp bài).
- **Nhãn phân loại:** Cột `final_result` trong `studentInfo` cho phép xây dựng trực tiếp nhãn nhị phân có nguy cơ.
- **Tải xuống tĩnh:** Bộ dữ liệu là một ảnh chụp cố định, nghĩa là mọi nhà nghiên cứu đều tải xuống tệp hoàn toàn giống nhau. Điều này đảm bảo khả năng tái lập hoàn toàn của các quy trình tiền xử lý và mô hình hóa.
- **Ẩn danh hóa tại nguồn:** The Open University đã ẩn danh hóa tất cả các bản ghi trước khi phát hành. Dự án này không cần thực hiện thêm bước xử lý PII nào.
- **Phù hợp với nghiên cứu trước:** Cả hai nghiên cứu nền tảng [1] và [2] đều sử dụng OULAD. Sử dụng cùng bộ dữ liệu cho phép so sánh trực tiếp các chỉ số hiệu suất mô hình và phương pháp luận — đây là mục tiêu rõ ràng của dự án.
- **Giấy phép:** CC-BY 4.0 — chỉ cần trích dẫn đúng cách, không có hạn chế đối với tái sử dụng học thuật hay thương mại.

---

## 5. Lưu ý về dữ liệu thứ cấp

OULAD là dữ liệu thứ cấp (secondary data): dữ liệu được The Open University thu thập và quản lý cho mục đích vận hành và nghiên cứu của chính họ, sau đó được phát hành công khai. Điều này kéo theo một sự đánh đổi mà nhóm dự án thừa nhận.

**Ưu điểm:** Dữ liệu có thể sử dụng ngay lập tức, đã được ẩn danh hóa và ổn định. Bất kỳ nhóm nghiên cứu nào trên thế giới đều có thể tái lập hoàn toàn cùng một thí nghiệm.

**Nhược điểm:** Dự án không có quyền kiểm soát các đặc trưng nào đã được ghi lại, cách thiết kế môi trường VLE, loại hình đánh giá nào được sử dụng, hay cách định nghĩa tình trạng rút khỏi khóa học. Khả năng tổng quát hóa sang các tổ chức khác phụ thuộc vào mức độ tương đồng giữa môi trường học tập của họ với The Open University.

Với mục tiêu đã được tuyên bố của dự án — phát triển và đánh giá chuẩn mực một mô hình nhận biết thời gian, có thể giải thích — những hạn chế này là chấp nhận được. Lợi ích về khả năng tái lập và so sánh với các nghiên cứu trước vượt trội hơn việc thiếu quyền kiểm soát thiết kế thu thập.

---

## 6. Quyền riêng tư dữ liệu, đạo đức và tuân thủ pháp lý

OULAD được ẩn danh hóa tại nguồn bởi The Open University. Không có tên sinh viên, địa chỉ email hay mã số định danh quốc gia nào xuất hiện trong bất kỳ bảng dữ liệu nào. Bộ dữ liệu được phát hành theo giấy phép Creative Commons Attribution 4.0 International (CC-BY 4.0).

Nghĩa vụ của dự án do đó chỉ bao gồm:

- Trích dẫn bộ dữ liệu đúng cách theo [3].
- Không cố gắng tái nhận dạng cá nhân từ dữ liệu.
- Ghi nhận giấy phép trong tất cả các ấn phẩm và bài nộp.

Không cần xin phê duyệt đạo đức của tổ chức cho việc phân tích bộ dữ liệu đã được ẩn danh hóa và phát hành công khai này trong phạm vi đồ án học thuật.

---

## Tài liệu tham khảo

[1] M. Adnan, A. Yousaf, M. Zafar và M. Shafique, "Predicting at-Risk Students at Different Percentages of Course Length for Early Intervention Using Machine Learning Models," *IEEE Access*, vol. 9, pp. 7519–7539, 2021.

[2] N. Tomasevic, N. Gvozdenovic và S. Vranes, "An overview and comparison of supervised data mining techniques for student exam performance prediction," *Computers & Education*, vol. 143, art. 103676, 2020.

[3] J. Kuzilek, M. Hlosta và Z. Zdrahal, "Open University Learning Analytics dataset," *Scientific Data*, vol. 4, art. 170171, 2017.
