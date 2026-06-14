# DSP391m – Nhóm 1
## Báo cáo 3 – Nhiệm vụ 3 | Thu thập, Làm sạch & Phân tích Dữ liệu
### Nguồn Dữ liệu, Giấy phép & Các Cân nhắc Đạo đức

---

> **Sản phẩm cần nộp (Bước 30)**
> Một phần văn bản trình bày: (1) nguồn gốc và xuất xứ (provenance) của bộ dữ liệu OULAD, (2) giấy phép và điều khoản sử dụng áp dụng, và (3) các cân nhắc đạo đức chi phối việc sử dụng bộ dữ liệu trong dự án này. Sẽ được tích hợp vào Mục 3.1 của Báo cáo 2 (Chương 3). Yêu cầu trích dẫn: Kuzilek và cộng sự (2017) và liên kết giấy phép CC-BY 4.0.

---

## 1. Nguồn gốc & Xuất xứ Dữ liệu

### 1.1. Tổng quan về Bộ dữ liệu

Bộ dữ liệu Phân tích Học tập Đại học Mở (Open University Learning Analytics Dataset – OULAD) là một bộ dữ liệu giáo dục công khai được phát hành bởi Viện Truyền thông Tri thức (Knowledge Media Institute – KMi) thuộc Đại học Mở (The Open University – OU), Vương quốc Anh. Bộ dữ liệu được công bố chính thức vào năm 2017 bởi Kuzilek, Hlosta và Zdrahal dưới dạng một bài mô tả dữ liệu (data descriptor) trên tạp chí *Scientific Data* (thuộc Nhà xuất bản Nature).

OULAD là một trong những bộ dữ liệu mở được trích dẫn rộng rãi nhất trong các cộng đồng nghiên cứu Phân tích Học tập (Learning Analytics) và Khai thác Dữ liệu Giáo dục (Educational Data Mining – EDM). Tính đến năm 2025, bài báo mô tả dữ liệu gốc đã tích lũy được hàng trăm lượt trích dẫn trên các ấn phẩm của IEEE, ACM, Springer và Elsevier.

### 1.2. Bối cảnh Thu thập

Bộ dữ liệu được xây dựng từ Môi trường Học tập Ảo (Virtual Learning Environment – VLE) của Đại học Mở, nơi tổ chức các khóa học đào tạo từ xa cho hàng chục nghìn sinh viên mỗi năm. Dữ liệu được lấy từ các năm học 2013 và 2014, bao gồm bảy học phần (module) được chọn, trình bày qua nhiều học kỳ khác nhau.

OU hoạt động theo mô hình đào tạo từ xa hoàn toàn, nghĩa là toàn bộ tương tác giữa sinh viên và khóa học diễn ra theo phương thức kỹ thuật số thông qua VLE. Điều này khiến bộ dữ liệu đặc biệt phù hợp cho nghiên cứu phân tích học tập: mọi hành động của sinh viên — đọc tài liệu, nộp bài kiểm tra, duyệt tài nguyên — đều được ghi lại dưới dạng mục nhật ký (log entry) có dấu thời gian.

### 1.3. Thành phần Bộ dữ liệu

| Bảng | Nội dung | Kích thước xấp xỉ |
|---|---|---|
| `studentInfo.csv` | Thông tin nhân khẩu học của sinh viên và kết quả cuối kỳ (`final_result`) | 32,593 bản ghi |
| `studentRegistration.csv` | Ngày đăng ký học phần và ngày rút môn của từng sinh viên | 32,593 bản ghi |
| `studentAssessment.csv` | Ngày nộp bài kiểm tra và điểm số | ~173,000 bản ghi |
| `studentVle.csv` | Nhật ký nhấp chuột hàng ngày (tương tác với các hoạt động trên VLE) | ~10,6 triệu bản ghi |
| `assessments.csv` | Siêu dữ liệu bài kiểm tra: loại, trọng số, thời hạn | ~173 mục |
| `vle.csv` | Danh mục các loại hoạt động trên VLE | ~465 mục |
| `courses.csv` | Thời lượng học phần (tính bằng ngày) theo từng học kỳ | 22 bản ghi |

**Thống kê chính:** 32,593 sinh viên • 22 tổ hợp học phần–học kỳ • 7 bảng CSV • 10,655,280 lượt tương tác trên VLE

### 1.4. Trích dẫn Chính thức

> J. Kuzilek, M. Hlosta, and Z. Zdrahal, "Open University Learning Analytics dataset," *Scientific Data*, vol. 4, p. 170171, Nov. 2017, doi: [10.1038/sdata.2017.171](https://doi.org/10.1038/sdata.2017.171).

**Trang chủ bộ dữ liệu chính thức:**
https://analyse.kmi.open.ac.uk/open_dataset

**Nguồn tải xuống:**
- [Kaggle — Open University Learning Analytics Dataset](https://www.kaggle.com/datasets/rocki37/open-university-learning-analytics-dataset)
- [UCI Machine Learning Repository — OULAD](https://archive.ics.uci.edu/dataset/349/open+university+learning+analytics+dataset)

---

## 2. Giấy phép & Điều khoản Sử dụng

### 2.1. Loại Giấy phép

OULAD được phát hành theo **Giấy phép Quốc tế Creative Commons Attribution 4.0 (CC-BY 4.0)**. Đây là một trong những giấy phép mở cho phép nhiều quyền nhất hiện có và được sử dụng rộng rãi trong việc xuất bản dữ liệu khoa học.

Tham chiếu giấy phép: https://creativecommons.org/licenses/by/4.0/

### 2.2. Những Điều CC-BY 4.0 Cho phép

| Quyền | Chi tiết |
|---|---|
| **Chia sẻ** | Sao chép và phân phối lại bộ dữ liệu dưới bất kỳ định dạng hay phương tiện nào. |
| **Điều chỉnh** | Phối lại, chuyển đổi và xây dựng dựa trên bộ dữ liệu cho bất kỳ mục đích nào, kể cả mục đích thương mại. |
| **Sử dụng trong nghiên cứu** | Tự do sử dụng trong các dự án nghiên cứu học thuật và ứng dụng mà không bị hạn chế. |
| **Tái tạo trong ấn phẩm** | Đưa các đoạn trích dữ liệu, bảng biểu và kết quả dẫn xuất vào các báo cáo và bài báo học thuật. |

### 2.3. Nghĩa vụ Theo CC-BY 4.0

Yêu cầu duy nhất theo CC-BY 4.0 là ghi công (attribution) đúng cách. Dự án này thực hiện nghĩa vụ này bằng cách:

1. Trích dẫn bài báo mô tả dữ liệu gốc (Kuzilek và cộng sự, 2017) trong tất cả các phần có tham chiếu đến bộ dữ liệu.
2. Bao gồm trích dẫn đầy đủ theo định dạng IEEE trong tài liệu này và trong danh mục tài liệu tham khảo của báo cáo cuối cùng.
3. Nêu rõ loại giấy phép (CC-BY 4.0) trong phần đạo đức này và trong tài liệu tái tạo (reproducibility documentation) (Bước 31).

### 2.4. Không Có Hạn chế Bổ sung

Bộ dữ liệu không có điều khoản phi thương mại, không yêu cầu chia sẻ tương tự (share-alike), và không có hạn chế cấm tạo tác phẩm phái sinh. OU không đặt thêm điều khoản sử dụng nào ngoài giấy phép CC-BY 4.0. Do đó, bộ dữ liệu có thể được tự do sử dụng, xử lý và báo cáo trong phạm vi dự án luận văn tốt nghiệp học thuật này.

---

## 3. Các Cân nhắc Đạo đức

### 3.1. Ẩn danh hóa tại Nguồn

OULAD đã được Đại học Mở ẩn danh hóa (anonymisation) trước khi phát hành công khai. Quá trình ẩn danh hóa được áp dụng tại tổ chức nguồn và được mô tả trong bài báo mô tả dữ liệu gốc (Kuzilek và cộng sự, 2017). Cụ thể:

- Tất cả các định danh cá nhân trực tiếp (tên, địa chỉ email, mã số sinh viên) đã được xóa và thay thế bằng các khóa số tùy ý.
- Dữ liệu địa lý chỉ được báo cáo ở cấp độ vùng (region), không bao gồm mã bưu chính hay địa chỉ cụ thể.
- Các chỉ số kinh tế-xã hội (`imd_band`) được báo cáo dưới dạng khoảng phân vị, không phải giá trị chính xác.
- Tuổi được báo cáo theo nhóm tuổi (0–35, 35–55, 55+), không phải ngày sinh cụ thể.

Do đó, không có sinh viên nào có thể bị tái nhận dạng (re-identification) từ bộ dữ liệu đã công bố trong điều kiện bình thường. Dự án này không thực hiện bất kỳ nỗ lực tái nhận dạng nào và không kết hợp OULAD với bất kỳ bộ dữ liệu bên ngoài nào có thể cho phép tái nhận dạng.

### 3.2. Tuân thủ Các Nguyên tắc Bảo vệ Dữ liệu

| Nguyên tắc | Cách Dự án này Tuân thủ |
|---|---|
| **Tính hợp pháp & minh bạch** | Bộ dữ liệu công khai theo CC-BY 4.0; không yêu cầu quyền truy cập đặc biệt. |
| **Giới hạn mục đích** | Dữ liệu chỉ được sử dụng cho nghiên cứu học thuật trong DSP391m; không dùng cho mục đích thương mại hay giám sát. |
| **Tối thiểu hóa dữ liệu** | Chỉ sử dụng bảy bảng CSV gốc; không thực hiện thu thập dữ liệu bổ sung. |
| **Tính chính xác** | Dữ liệu nguồn được lưu trữ ở chế độ chỉ đọc (`/data/raw`) với xác minh băm md5 để ngăn chỉnh sửa ngoài ý muốn. |
| **Giới hạn lưu trữ** | Dữ liệu chỉ được lưu giữ trong suốt thời gian dự án; không chia sẻ ngoài nhóm dự án. |
| **Không xử lý dữ liệu nhạy cảm** | Không có dữ liệu thuộc danh mục đặc biệt (sức khỏe, tôn giáo, quan điểm chính trị) nào hiện diện hoặc được xử lý. |

### 3.3. Không Cần Yêu cầu Sự đồng ý

Vì OULAD là dữ liệu thứ cấp (secondary data) — được thu thập và ẩn danh hóa bởi bên thứ ba (Đại học Mở) theo khung đạo đức thể chế riêng của họ — dự án này không bắt buộc phải lấy sự đồng ý cá nhân từ các sinh viên được đại diện trong bộ dữ liệu. Việc thu thập dữ liệu ban đầu được thực hiện theo quy trình đạo đức nội bộ của OU, và việc phát hành công khai theo CC-BY 4.0 cấu thành sự ủy quyền của OU cho việc sử dụng nghiên cứu phái sinh.

### 3.4. Cam kết Sử dụng có Trách nhiệm

Ngoài các yêu cầu pháp lý tối thiểu, dự án này cam kết thực hiện các biện pháp sử dụng có trách nhiệm sau:

1. Bộ dữ liệu chỉ được sử dụng để xây dựng các mô hình dự đoán nhằm hỗ trợ thành công của sinh viên, không nhằm mục đích trừng phạt, giám sát hay phân biệt đối xử với bất kỳ nhóm nào.
2. Kết quả đầu ra của mô hình sẽ được diễn giải với nhận thức về sai lệch thuật toán (algorithmic bias) tiềm ẩn, đặc biệt liên quan đến các biến nhân khẩu học như `imd_band`, `region` và tình trạng `disability`.
3. Không có nỗ lực nào được thực hiện nhằm suy luận danh tính cá nhân, liên hệ với sinh viên hay chia sẻ các dự đoán ở cấp độ cá nhân ngoài bối cảnh học thuật của dự án này.
4. Tất cả các kết quả đầu ra dẫn xuất (bảng đã xử lý, mô hình đã huấn luyện, biểu đồ EDA) sẽ được lưu trữ an toàn và chỉ được truy cập bởi các thành viên trong nhóm dự án.

### 3.5. Các Rủi ro Đạo đức Tiềm ẩn & Biện pháp Giảm thiểu

| Rủi ro | Khả năng xảy ra | Biện pháp giảm thiểu |
|---|---|---|
| Sai lệch thuật toán đối với các nhóm kinh tế-xã hội hoặc nhân khẩu học | Trung bình | Đánh giá hiệu suất mô hình riêng biệt theo từng nhóm nhân khẩu học; báo cáo các chỉ số phân tách. |
| Lạm dụng dự đoán sinh viên có nguy cơ để trừng phạt thay vì hỗ trợ | Thấp (bối cảnh học thuật) | Xác định rõ ràng tất cả kết quả đầu ra là công cụ hỗ trợ quyết định, không phải quyết định tự động. |
| Tái nhận dạng thông qua kết hợp dữ liệu | Rất thấp (dữ liệu đã được ẩn danh hóa) | Không có nguồn dữ liệu bên ngoài nào được kết hợp với OULAD trong dự án này. |
| Rò rỉ dữ liệu hoặc truy cập trái phép | Thấp | Dữ liệu được lưu trữ cục bộ với quyền chỉ đọc; không tải lên các kho lưu trữ công khai. |

---

## 4. Tóm tắt

> **Tóm tắt Mục 3.1 cho Báo cáo 2**
>
> Bộ dữ liệu OULAD (Kuzilek và cộng sự, 2017) được Đại học Mở thu thập từ Môi trường Học tập Ảo trong các năm học 2013–2014, bao gồm 32,593 sinh viên trên 22 tổ hợp học phần–học kỳ. Bộ dữ liệu được công bố theo giấy phép Creative Commons Attribution 4.0 International (CC-BY 4.0), cho phép sử dụng, điều chỉnh và phân phối lại không hạn chế miễn là có ghi công. Trước khi phát hành công khai, OU đã ẩn danh hóa tất cả các định danh cá nhân tại nguồn; không có sinh viên nào có thể bị tái nhận dạng từ các bảng đã công bố. Dự án này sử dụng bộ dữ liệu chỉ dành cho nghiên cứu học thuật trong DSP391m, không áp dụng thu thập dữ liệu bổ sung, và cam kết thực hiện các biện pháp sử dụng có trách nhiệm nhằm ưu tiên phúc lợi của sinh viên và phòng ngừa sai lệch thuật toán.

---

*DSP391m – Nhóm 1*
