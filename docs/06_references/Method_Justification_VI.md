# Luận Giải Dựa Trên Bằng Chứng Cho Các Lựa Chọn Phương Pháp Nghiên Cứu

**Phụ đề:** Cơ sở lý luận cho các quyết định thiết kế chính trong quy trình dự đoán sinh viên có nguy cơ bỏ học

**DSP391m – Nhóm 1 · Báo cáo 2 (Nhiệm vụ Dữ liệu), Chương 3 · Hạng mục công việc STT 25 (Sơn)**

---

## 1. Tại Sao Các Điểm Kiểm Tra Ở Mức 40–60% Độ Dài Khóa Học Là Thời Điểm Dự Đoán Sớm Đáng Tin Cậy

Một trong những quyết định quan trọng nhất của hệ thống cảnh báo sớm là *thời điểm* thực hiện dự đoán. Can thiệp quá muộn mang lại ít lợi ích; dự đoán quá sớm lại dẫn đến độ không chắc chắn cao. Adnan và cộng sự [1] đã đánh giá có hệ thống độ chính xác dự đoán tại nhiều thời điểm khác nhau trong suốt tiến trình khóa học và phát hiện rằng khoảng thời gian từ 40–60% độ dài khóa học thể hiện sự cân bằng thực tiễn tối ưu: đã tích lũy đủ dữ liệu hoạt động của sinh viên để tạo ra các dự đoán ổn định, đồng thời vẫn còn đủ thời gian để giảng viên triển khai hỗ trợ có ý nghĩa. Do đó, quy trình của nhóm xác định **sáu** điểm kiểm tra nhận thức thời gian (time-aware checkpoint) — 10 / 20 / 40 / 60 / 80 / 100% độ dài khóa học — và lấy **vùng 40–60%** làm điểm đánh giá chính, khả thi nhất cho can thiệp sớm. Lựa chọn này trực tiếp trả lời **RQ1** (điểm kiểm tra sớm nhất đáng tin cậy và thuật toán tốt nhất) bằng cách neo lịch kiểm tra vào bằng chứng thực nghiệm thay vì các ngày tùy ý trên lịch.

*Tài liệu tham khảo hỗ trợ: [1]*

---

## 2. Tại Sao Đặc Trưng Mức Độ Tương Tác Và Kết Quả Đánh Giá Được Ưu Tiên Hơn Đặc Trưng Nhân Khẩu Học

Lựa chọn đặc trưng (feature selection) trong khai thác dữ liệu giáo dục phải được hướng dẫn bởi bằng chứng về tính giá trị dự đoán. Tomasevic và cộng sự [2] đã so sánh nhiều kỹ thuật học máy (machine learning) có giám sát để dự đoán kết quả học tập sinh viên trên OULAD và phát hiện rằng các chỉ số mức độ tương tác — đặc biệt là nhật ký tương tác với Môi trường Học tập Ảo (VLE — Virtual Learning Environment), tức dữ liệu luồng nhấp chuột (clickstream) — và điểm số đánh giá trung gian mang tín hiệu dự đoán cao. Ngược lại, các thuộc tính nhân khẩu học (demographic) như nhóm tuổi, khu vực và trình độ học vấn cao nhất trước đây đóng góp tương đối ít giá trị dự đoán bổ sung khi các đặc trưng hành vi và kết quả học tập đã được đưa vào mô hình.

Trong dự án này, bộ dữ liệu OULAD [3] cung cấp bản ghi clickstream VLE phong phú (tổng số và số lượng theo ngày của các tương tác tài nguyên) và kết quả đánh giá (TMA/CMA). Đây là các nhóm đặc trưng cốt lõi, trong khi các trường nhân khẩu học được giữ lại nhưng không được ưu tiên. Thiết kế này tránh xây dựng mô hình mà các quyết định của nó dựa vào các đặc điểm được bảo vệ, thay vào đó neo các dự đoán vào các hành động của người học có thể quan sát trực tiếp và có ý nghĩa giáo dục.

*Tài liệu tham khảo hỗ trợ: [2], [3]*

---

## 3. Tại Sao PR-AUC Và Recall Được Chọn Thay Cho Accuracy Làm Chỉ Số Chính

Biến mục tiêu trong dự án này là `at_risk` (có nguy cơ), được định nghĩa là những sinh viên có kết quả cuối kỳ là *Fail* (Trượt) hoặc *Withdrawn* (Rút lui), đối lập với *Pass* (Đạt) hoặc *Distinction* (Xuất sắc) (không có nguy cơ). Dựa trên bộ dữ liệu OULAD, tỷ lệ `at_risk` quan sát được là khoảng **52,8%**, khiến sự mất cân bằng lớp (class imbalance) là nhẹ chứ không nghiêm trọng. Vì cả hai lớp được đại diện ở mức gần tương đương, Accuracy (Độ chính xác tổng thể) sẽ không gây hiểu lầm nghiêm trọng theo nghĩa tổng quan; tuy nhiên, nó vẫn là một chỉ số sơ cấp không phù hợp cho trường hợp sử dụng này vì một lý do khái niệm: một âm tính giả (dự đoán *không có nguy cơ* trong khi sinh viên thực sự sẽ trượt hoặc rút lui) mang chi phí sư phạm lớn hơn nhiều so với một dương tính giả. Chi phí can thiệp của việc đưa ra cảnh báo không cần thiết là thấp; chi phí bỏ lỡ một sinh viên đang gặp khó khăn là cao.

Recall (Độ nhạy — Sensitivity) định lượng tỷ lệ sinh viên `at_risk` thực sự được xác định thành công, ánh xạ trực tiếp vào mục tiêu vận hành. PR-AUC (Diện tích dưới đường cong Precision-Recall) tóm tắt sự đánh đổi qua tất cả các ngưỡng quyết định và là chỉ số được khuyến nghị khi lớp dương — dù chỉ là lớp thiểu số nhẹ — là lớp được quan tâm [6]. Sử dụng accuracy làm chỉ số sơ cấp sẽ cho phép một mô hình trông có vẻ tốt trong khi vẫn bỏ lỡ nhiều sinh viên có nguy cơ.

Mặc dù sự mất cân bằng là nhẹ, **RQ3** vẫn điều tra rõ ràng liệu các kỹ thuật lấy mẫu lại như SMOTE (Synthetic Minority Over-sampling Technique), ADASYN (Adaptive Synthetic Sampling) và điều chỉnh trọng số lớp (class-weighting) có cải thiện thêm Recall và PR-AUC hay không. Phát hiện về sự mất cân bằng nhẹ không loại bỏ sự cần thiết phải nghiên cứu các kỹ thuật này; nó chỉ có nghĩa là lợi ích cận biên của chúng có thể nhỏ hơn so với các thiết lập bị lệch nghiêm trọng — một kết quả đáng báo cáo bằng thực nghiệm. Chawla và cộng sự [6] giới thiệu SMOTE như một kỹ thuật lấy mẫu quá mức (over-sampling) có nguyên tắc, đó là lý do tại sao nó đóng vai trò là kỹ thuật tham chiếu trong RQ3.

*Tài liệu tham khảo hỗ trợ: [6]*

---

## 4. Tại Sao Cần Phân Chia Dữ Liệu Có Nhận Thức Nhóm, Phân Tầng Với Tập Kiểm Tra Cố Định

Các bản ghi sinh viên trong OULAD chứa nhiều lần trình bày mô-đun (module presentation) trên mỗi sinh viên (`id_student`). Nếu các bản ghi của cùng một sinh viên xuất hiện trong cả tập huấn luyện và tập kiểm tra, mô hình có thể học các đặc điểm riêng lẻ thay vì các quy luật tổng quát hóa — một dạng *rò rỉ nhóm* (group leakage) làm tăng giả tạo hiệu suất trên tập dữ liệu giữ lại. Để ngăn chặn điều này, việc phân chia huấn luyện/xác nhận/kiểm tra phải được thực hiện ở cấp độ sinh viên (nhóm theo `id_student`) sao cho tất cả các bản ghi của một sinh viên nhất định nằm hoàn toàn trong một phân vùng.

Ngoài việc ngăn ngừa rò rỉ, dự án đánh giá dự đoán tại sáu điểm kiểm tra theo thời gian (10–100% độ dài khóa học). Giữ tập kiểm tra cố định qua tất cả các mốc đảm bảo rằng các so sánh hiệu suất được thực hiện trên cùng một tổng thể, bảo toàn tính hợp lệ của các kiểm định thống kê bắt cặp và so sánh xuyên điểm kiểm tra. Phân tầng (stratification) theo nhãn `at_risk` trong phân chia ở cấp độ nhóm duy trì tỷ lệ dương tính khoảng 52,8% trong mỗi phân vùng, ngăn ngừa sự mất cân bằng ngẫu nhiên do chính việc phân chia gây ra.

*Thiết kế này là thông lệ tiêu chuẩn trong tài liệu kiểm định chéo có nhóm (grouped cross-validation) và là yêu cầu bắt buộc để đảm bảo tính toàn vẹn của RQ1 và RQ2.*

---

## 5. Tại Sao Độ Ổn Định Giải Thích Cần Một Chỉ Số Định Lượng

SHAP (SHapley Additive exPlanations) và LIME (Local Interpretable Model-agnostic Explanations) là hai phương pháp giải thích hậu kỳ (post-hoc explanation) được triển khai phổ biến nhất trong phân tích học thuật giáo dục. Tuy nhiên, Gunasekara và Saarela [4] đã đánh giá tình trạng của XAI (Explainable Artificial Intelligence — Trí tuệ Nhân tạo Có thể Giải thích) trong giáo dục và xác định một khoảng trống quan trọng: trong khi so sánh định tính về xếp hạng tầm quan trọng đặc trưng là phổ biến, việc đo lường định lượng nghiêm ngặt về độ ổn định giải thích — mức độ nhất quán mà một phương pháp giải thích gán cùng một thứ tự tầm quan trọng qua các lần chạy lặp lại, đầu vào bị nhiễu, hoặc các sinh viên tương tự — phần lớn vắng mặt trong tài liệu. Một kiểm tra trực quan hoặc dựa trên xếp hạng thuần túy không thể phát hiện các bất ổn định tinh tế làm suy yếu niềm tin vào các giải thích được cung cấp cho giảng viên.

Do đó, **RQ2** giới thiệu một chỉ số ổn định định lượng (ví dụ: tương quan thứ hạng của tầm quan trọng đặc trưng SHAP qua các lần lấy mẫu bootstrap, hoặc độ tương đồng Jaccard của các đặc trưng top-k LIME) và so sánh SHAP với LIME trên chiều đó. Điều này trực tiếp giải quyết khoảng trống phương pháp được xác định trong [4] và tạo ra kết quả có thể tái tạo và so sánh được trong các nghiên cứu tương lai.

*Tài liệu tham khảo hỗ trợ: [4]*

---

## Tài Liệu Tham Khảo

[1] M. Adnan và cộng sự, "Predicting at-Risk Students at Different Percentages of Course Length for Early Intervention Using Machine Learning Models," *IEEE Access*, tập 9, tr. 7519–7539, 2021.

[2] N. Tomasevic, N. Gvozdenovic và S. Vranes, "An overview and comparison of supervised data mining techniques for student exam performance prediction," *Computers & Education*, tập 143, tr. 103676, 2020.

[3] J. Kuzilek, M. Hlosta và Z. Zdrahal, "Open University Learning Analytics Dataset," *Scientific Data*, tập 4, tr. 170171, 2017.

[4] S. Gunasekara và M. Saarela, "Explainable AI in Education: Techniques and Qualitative Assessment," *Applied Sciences*, vol. 15, no. 3, art. 1239, 2025.

[6] N. V. Chawla, K. W. Bowyer, L. O. Hall và W. P. Kegelmeyer, "SMOTE: Synthetic Minority Over-sampling Technique," *Journal of Artificial Intelligence Research*, tập 16, tr. 321–357, 2002.
