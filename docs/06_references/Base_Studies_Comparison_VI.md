# Các Nghiên Cứu Nền: So Sánh Quy Trình Tiền Xử Lý Dữ Liệu OULAD

**Phụ đề:** So sánh thu thập dữ liệu, làm sạch, kỹ thuật đặc trưng và phân chia tập dữ liệu qua bốn nghiên cứu tiên khởi nhằm củng cố cơ sở lựa chọn thiết kế của nhóm.

**DSP391m – Nhóm 1 · Báo cáo 2 (Nhiệm vụ Dữ liệu), Chương 3 · Hạng mục công việc STT 24 (Sơn)**

---

> **Lưu ý:** Các con số chính xác, ngưỡng giá trị và kết quả trích dẫn từ mỗi nghiên cứu cần được nhóm tự đối chiếu với tài liệu gốc trước khi nộp bài cuối.

---

## 1. Giới thiệu

Bộ dữ liệu phân tích học tập của Đại học Mở — Open University Learning Analytics Dataset (OULAD) — được Kuzilek và cộng sự mô tả trong [3] — cung cấp bảy bảng quan hệ bao gồm 32.593 lượt đăng ký học, hồ sơ nhân khẩu học (demographic), nhật ký tương tác với Môi trường Học tập Ảo (Virtual Learning Environment — VLE), và hồ sơ kiểm tra đánh giá (assessment). Do nhiều nhóm nghiên cứu đã sử dụng bộ dữ liệu này để dự đoán bỏ học và kết quả học tập, các quyết định tiền xử lý (preprocessing) của họ tạo thành một mốc tham chiếu thực tiễn cho dự án của nhóm. Chương này khảo sát bốn nghiên cứu tiêu biểu và rút ra những bài học phương pháp luận có thể áp dụng trực tiếp vào quy trình của chúng ta.

---

## 2. Bảng So Sánh: Quy Trình Tiền Xử Lý Qua Các Nghiên Cứu Nền

| Nghiên cứu | **Thu thập dữ liệu** | **Làm sạch** | **Kỹ thuật đặc trưng** | **Phân chia tập dữ liệu** |
|---|---|---|---|---|
| **[1] Adnan và cộng sự (2021)** | OULAD đầy đủ; gộp ba bảng nhân khẩu học, nhật ký VLE và đánh giá theo từng sinh viên và từng học phần [1] | Loại bỏ hoặc nội suy giá trị thiếu; loại các lượt đăng ký có hoạt động quá ít [1] | Đặc trưng cắt ngưỡng theo thời gian tại nhiều mốc phần trăm độ dài khóa học (10–100%); kết hợp nhân khẩu học + mức độ tương tác tích lũy + điểm đánh giá liên tục [1] | Áp dụng ngưỡng thời gian (temporal cut-off) cho từng mốc; phân chia train/test để ngăn rò rỉ sự kiện tương lai; mất cân bằng lớp (class imbalance) xử lý bằng tái lấy mẫu [1] |
| **[2] Tomasevic và cộng sự (2020)** | OULAD; tập trung vào bảng tương tác VLE và đánh giá; nhân khẩu học được xem là đầu vào phụ [2] | Loại bỏ bản ghi thiếu nhãn kết quả; mã hóa trường phân loại; kiểm tra bản ghi có số lượt nhấp bất thường [2] | Tổng hợp luồng nhấp (clickstream) thành số lượt tương tác; điểm đánh giá lịch sử dùng làm đặc trưng trực tiếp; đặc trưng nhân khẩu học đóng góp ít [2] | Phân chia hold-out hoặc kiểm định chéo (cross-validation) tiêu chuẩn; không có ngưỡng thời gian tường minh; phân chia theo tầng (stratified) trên nhãn đỗ/trượt [2] |
| **[4] Gunasekara & Saarela (2025)** | OULAD (trong số các bộ dữ liệu giáo dục khác); chủ yếu dùng làm chuẩn mực đánh giá khả năng giải thích (XAI) [4] | Làm sạch tiêu chuẩn theo quy trình thượng nguồn; chi tiết tiền xử lý là thứ yếu so với mục tiêu đánh giá XAI [4] | Tập đặc trưng kế thừa từ nghiên cứu trước; ít kỹ thuật mới; SHAP/LIME áp dụng hậu nghiệm (post-hoc) sau huấn luyện [4] | Phân chia train/test theo quy ước; phương pháp phân chia không phải đóng góp chính của nghiên cứu [4] |
| **[5] Nghiên cứu clickstream (2023)** | Toàn bộ nhật ký tương tác VLE (~10 triệu hàng); gộp với bảng nhân khẩu học và đánh giá [5] | Lọc bản ghi hoạt động thấp; loại trùng lặp; loại sự kiện có ngày ngoài phạm vi [5] | Tổng hợp luồng nhấp theo từng sinh viên thành: tổng số lượt nhấp, số ngày hoạt động, số lượt theo từng loại hoạt động; tạo véc-tơ đặc trưng gọn nhẹ [5] | Phân chia ngẫu nhiên hoặc phân tầng trên nhãn cuối; tổng hợp thực hiện trước khi phân chia để tránh rò rỉ ở mức hàng [5] |

---

## 3. Thảo Luận

### 3.1 Thu Thập Dữ Liệu

Cả bốn nghiên cứu đều sử dụng OULAD [3] ở dạng đã công bố mà không thu thập thêm dữ liệu bên ngoài. Sự khác biệt chính nằm ở việc nhấn mạnh bảng nào: Adnan và cộng sự [1] tích hợp cả ba nhóm đặc trưng một cách tường minh; Tomasevic và cộng sự [2] coi tương tác VLE và điểm đánh giá là chính, nhân khẩu học là phụ; nghiên cứu clickstream [5] tập trung hẹp vào nhật ký tương tác VLE và thực hiện tổng hợp quy mô lớn; trong khi Gunasekara & Saarela [4] xử lý bộ dữ liệu như một chuẩn mực sẵn có.

### 3.2 Làm Sạch

Cách tiếp cận xử lý giá trị thiếu và ngoại lệ nhìn chung nhất quán: loại bỏ hoặc nội suy nhãn kết quả bị thiếu, lọc các lượt đăng ký rõ ràng không hoạt động, và mã hóa nhân khẩu học phân loại. Không nghiên cứu nào báo cáo phương pháp làm sạch thực sự mới; sự đồng thuận là OULAD tương đối sạch, và gánh nặng làm sạch chính là quyết định đưa vào tập con module-presentations nào.

### 3.3 Kỹ Thuật Đặc Trưng

Sự biến thiên đáng kể nhất xảy ra ở đây. Adnan và cộng sự [1] giới thiệu ý tưởng then chốt về **cắt ngưỡng nhận thức thời gian (time-aware truncation)**: đặc trưng được tính lại tại mỗi mốc kiểm tra (checkpoint) để mô hình chỉ nhìn thấy thông tin có sẵn đến thời điểm đó trong khóa học. Nghiên cứu clickstream [5] chứng minh cách nhật ký tương tác thô có thể được nén lại thành véc-tơ đặc trưng gọn nhẹ theo từng sinh viên. Tomasevic và cộng sự [2] cung cấp bằng chứng thực nghiệm rằng đặc trưng mức độ tương tác và đánh giá chiếm ưu thế, trong khi đặc trưng nhân khẩu học đóng góp tương đối ít sức mạnh dự đoán.

### 3.4 Phân Chia Tập Dữ Liệu

Adnan và cộng sự [1] áp dụng ngưỡng thời gian căn chỉnh với từng mốc độ dài khóa học — đây là phương pháp chặt chẽ nhất để tránh rò rỉ dữ liệu (data leakage). Các nghiên cứu khác sử dụng phân chia phân tầng hoặc ngẫu nhiên thông thường. Không có nghiên cứu nào trong số này sử dụng phân chia nhận biết nhóm (group-aware split) — đảm bảo một sinh viên không xuất hiện đồng thời trong tập train và test qua nhiều lần đăng ký — đây là một cải tiến mà quy trình của nhóm ta áp dụng.

---

## 4. Những Điều Chúng Ta Kế Thừa

- **Dự đoán theo mốc thời gian (checkpoint-based prediction)** [1]: Chúng ta áp dụng nguyên tắc cắt ngưỡng tính đặc trưng tại nhiều mốc phần trăm độ dài khóa học (10 / 20 / 40 / 60 / 80 / 100%). Bằng chứng từ Adnan và cộng sự cho thấy các dự đoán ổn định vào khoảng mốc 40–60%, làm cho các mốc này trở nên hữu dụng nhất cho can thiệp sớm.

- **Ưu tiên nhóm đặc trưng** [2]: Dựa trên phát hiện của Tomasevic và cộng sự rằng tương tác clickstream và điểm đánh giá tích lũy mang tín hiệu dự đoán cao nhất, kỹ thuật đặc trưng của chúng ta ưu tiên hai nhóm này. Đặc trưng nhân khẩu học vẫn được giữ lại cho phân tích công bằng (fairness analysis) nhưng không phụ thuộc vào chúng cho độ chính xác dự đoán.

- **Chiến lược tổng hợp clickstream** [5]: Chúng ta tổng hợp toàn bộ nhật ký tương tác VLE (khoảng 10 triệu hàng) thành đặc trưng tóm tắt theo từng sinh viên, từng mốc thời gian (tổng lượt nhấp, số ngày hoạt động, số lượt theo từng loại hoạt động), trực tiếp theo cách tiếp cận được chứng minh trong nghiên cứu clickstream.

- **Ngăn chặn rò rỉ dữ liệu** [1][5]: Bộ mã hóa (encoder), bộ chuẩn hóa (scaler) và bộ nội suy (imputer) chỉ được khớp trên phân vùng huấn luyện, và tất cả sự kiện được ghi nhận sau một mốc thời gian nhất định bị loại trước khi xây dựng ma trận đặc trưng của mốc đó, nhất quán với tính kỷ luật thời gian trong [1].

- **Phân chia phân tầng nhận biết nhóm**: Chúng ta mở rộng thực hành phân chia của [2] bằng cách đảm bảo toàn bộ lượt đăng ký của cùng một sinh viên (`id_student`) đều nằm hoàn toàn trong tập train hoặc test, đồng thời áp dụng kiểm định chéo 5-fold × 5-seed trên phần huấn luyện. Biện pháp bảo vệ chống rò rỉ ở cấp độ sinh viên này không có trong các nghiên cứu được khảo sát nhưng được thúc đẩy bởi các giả định ngầm kết hợp của chúng về tính độc lập của mẫu.

- **Khung XAI** [4]: Trong khi Gunasekara & Saarela [4] đánh giá khả năng giải thích (explainability) theo cách định tính, khảo sát của họ thúc đẩy việc nhóm bổ sung chỉ số ổn định giải thích (explanation-stability metric) định lượng để bổ sung cho đầu ra SHAP — vượt ra ngoài những gì bất kỳ nghiên cứu nền nào cung cấp.

---

## Tài Liệu Tham Khảo

[1] Adnan, M., và cộng sự (2021). Predicting at-Risk Students at Different Percentages of Course Length for Early Intervention Using Machine Learning Models. *IEEE Access*, 9, 7519–7539.

[2] Tomasevic, N., Gvozdenovic, N., & Vranes, S. (2020). An overview and comparison of supervised data mining techniques for student exam performance prediction. *Computers & Education*, 143, 103676.

[3] Kuzilek, J., Hlosta, M., & Zdrahal, Z. (2017). Open University Learning Analytics dataset. *Scientific Data*, 4, 170171.

[4] Gunasekara, S., & Saarela, M. (2025). Explainable AI in Education: Techniques and Qualitative Assessment. *Applied Sciences*, 15(3), art. 1239.

[5] "Predicting Student Performance Using Clickstream Data and Machine Learning," *Education Sciences*, vol. 13, no. 1, art. 17, 2023.
