# Các nghiên cứu nền: Đối chiếu quy trình tiền xử lý OULAD

**Phụ đề:** So sánh thu thập, làm sạch, tạo đặc trưng và phân chia dữ liệu giữa bốn nghiên cứu nền để lập luận cho các lựa chọn của nhóm.

**DSP391m – Nhóm 1 · Báo cáo 2 (Tác vụ dữ liệu), Chương 3 · Hạng mục STT 24 (Sơn)**

---

> **Ghi chú kiểm chứng.** Các ô dưới đây đã được đối chiếu với bản gốc: toàn văn cho [1], [2] và [4]; phần tóm tắt cùng các bài trích dẫn độc lập cho [5] (toàn văn nhà xuất bản bị giới hạn). Những ô nguồn không nêu rõ được đánh dấu *"không nêu rõ"* thay vì suy đoán.

---

## 1. Giới thiệu

Bộ dữ liệu Open University Learning Analytics Dataset (OULAD) — mô tả bởi Kuzilek và cộng sự [3] — gồm bảy bảng quan hệ bao phủ 32.593 lượt đăng ký sinh viên, gồm hồ sơ nhân khẩu học, tương tác clickstream trên môi trường học ảo (VLE) và kết quả đánh giá. Vì nhiều nhóm nghiên cứu đã dùng bộ dữ liệu này, các quyết định tiền xử lý của họ là cơ sở thực tiễn cho dự án. Chương này khảo sát bốn nghiên cứu và rút ra bài học định hướng pipeline của nhóm.

---

## 2. Bảng đối chiếu quy trình tiền xử lý của các nghiên cứu nền

| Nghiên cứu | **Thu thập** | **Làm sạch** | **Tạo đặc trưng** | **Phân chia / Kiểm định** |
|---|---|---|---|---|
| **[1] Adnan và cộng sự (2021)** | Toàn bộ OULAD (22 môn–kỳ, 32.593 sinh viên); bảng nhân khẩu học, clickstream VLE và đánh giá [1] | Giá trị ngày khuyết được điền bằng **trung bình**; giữ Withdrawn như một lớp; không nêu lọc sinh viên không hoạt động [1] | Ba nhóm đặc trưng (nhân khẩu học; sum/mean click; điểm, điểm tương đối, số bài nộp muộn) tính tích luỹ tại **đầu khoá và 20/40/60/80/100%** thời lượng [1] | **CV 10-fold** cho mô hình ML, **chia 85/15** cho mô hình học sâu; xử lý mất cân bằng bằng **gộp lớp** (Pass+Distinction; Fail+Withdrawn), *không* tái lấy mẫu; chỉ số: accuracy, precision, recall, F-score, AUC [1] |
| **[2] Tomasevic và cộng sự (2020)** | OULAD master table; thực nghiệm dùng **tập con môn DDD** (DDD_2013J + DDD_2014B) → **3.166 sinh viên** sau khi loại SV không thi cuối kỳ [2] | **Loại mọi dòng có giá trị khuyết** (NaN = bài đánh giá/thi không làm); đặc trưng **co giãn/chuẩn hoá về [0,1]** [2] | Ba nhóm — nhân khẩu học; tương tác (click VLE hàng ngày); kết quả (6 điểm đánh giá trung gian, điểm thi cuối, số lần thi); còn phân tích tích luỹ sau mỗi bài đánh giá. Phát hiện: **tương tác + kết quả** chiếm ưu thế; nhân khẩu học "không ảnh hưởng đáng kể" [2] | **Chia ngẫu nhiên 80:20** (train:test), hoặc **60:20:20** có tập validation cho ANN; **k-fold CV cho ANN** (không cho cây quyết định); F1 (phân loại) / RMSE (hồi quy), trung bình hoá qua **10 lần chạy** [2] |
| **[4] Gunasekara & Saarela (2025)** | **Chỉ** OULAD, một **tập con 3 môn (AAA/BBB/CCC)** → 14 đặc trưng, 17.091 mẫu (Pass 5.963 / Fail 7.128); dùng làm benchmark minh hoạ XAI [4] | Loại dòng/cột khuyết quá nhiều; chuẩn hoá biến số về ~0–1; gộp lớp (Pass+Distinction; Fail+Withdrawn) [4] | **14 thuộc tính chọn/tổng hợp** từ OULAD (ví dụ `sum_click`, `assessment_count`, `delay`, `score` + nhân khẩu học); SHAP/LIME áp dụng hậu kỳ [4] | **CV 5-fold lặp 50 lần** (+ một lần chia train/test); **ANN vs Cây quyết định**; SHAP+LIME, chủ yếu giải thích cục bộ định tính [4] |
| **[5] Liu và cộng sự (2023)** | OULAD; `studentInfo` ghép với clickstream `studentVle`; **5.341 sinh viên** sau làm sạch [5] | **Loại 180 sinh viên không có click** (→ 5.341); các bước khác *không nêu rõ* [5] | Số click trên **12 trang học (learning sites)**, tổng hợp theo **tuần và tháng** (ảnh hưởng nhất: content, subpage, homepage, quiz) [5] | Nhị phân pass/fail; **LSTM vs 1D-CNN vs ML truyền thống** (LSTM tốt nhất, ≈90%); độ chính xác tăng theo kỳ; tỉ lệ train/test và xử lý mất cân bằng *không nêu rõ* [5] |

---

## 3. Thảo luận

### 3.1 Thu thập

Cả bốn nghiên cứu dùng OULAD [3] không thu thập thêm, nhưng phạm vi khác nhau: Adnan và cộng sự [1] dùng toàn bộ và tích hợp cả ba nhóm đặc trưng; Tomasevic và cộng sự [2] kết hợp tương tác, kết quả và nhân khẩu học; Liu và cộng sự [5] tập trung clickstream VLE ghép với `studentInfo`; còn Gunasekara & Saarela [4] cố ý chỉ dùng **tập con 3 môn** làm benchmark XAI. Pipeline của nhóm, như [1], dùng toàn bộ 32.593 bản ghi với cả ba nhóm đặc trưng.

### 3.2 Làm sạch

Làm sạch nhìn chung nhẹ, nhưng các nghiên cứu khác nhau ở dữ liệu khuyết: Adnan và cộng sự [1] điền trung bình ngày khuyết; Tomasevic và cộng sự [2] **loại mọi dòng có giá trị khuyết** (bài không làm) và chuẩn hoá đặc trưng về [0,1]; Gunasekara & Saarela [4] loại dòng/cột khuyết nhiều, chuẩn hoá và gộp lớp; Liu và cộng sự [5] loại 180 sinh viên không click. Đáng chú ý, **không bài nào coi "chưa nộp bài" là tín hiệu thông tin** — thậm chí [2] loại bỏ đúng những sinh viên đó — khoảng trống mà pipeline của nhóm lấp bằng cờ `not_submitted` thay vì loại bỏ họ.

### 3.3 Tạo đặc trưng

Đây là nơi khác biệt nhất. Adnan và cộng sự [1] giới thiệu **cắt theo thời gian** — tính lại đặc trưng tích luỹ tại các mốc phần trăm thời lượng cố định — là cơ sở trực tiếp cho thiết kế mốc của nhóm (họ dùng 20–100% còn nhóm thêm mốc 10%). Liu và cộng sự [5] cho thấy cách nén click thô thành số đếm theo trang/tuần/tháng. Tomasevic và cộng sự [2] cung cấp cơ sở thực nghiệm cho việc ưu tiên tương tác và kết quả hơn nhân khẩu học.

### 3.4 Phân chia / Kiểm định

Các nghiên cứu dựa vào hold-out ngẫu nhiên hoặc k-fold tiêu chuẩn (10-fold ở [1]; chia ngẫu nhiên 80:20 / 60:20:20 kèm k-fold cho ANN ở [2]; 5-fold ×50 ở [4]); chỉ [1] áp dụng cắt theo thời gian theo từng mốc. Quan trọng, **không bài nào dùng phân chia bảo toàn nhóm** theo sinh viên, nên một sinh viên có nhiều môn–kỳ có thể nằm ở cả train lẫn test — rủi ro rò rỉ mà pipeline của nhóm loại bỏ (mục "Những điều kế thừa").

---

## 4. Những điều nhóm kế thừa

- **Dự đoán theo mốc thời gian** [1]: nhóm áp dụng cắt đặc trưng tích luỹ tại các mốc phần trăm thời lượng. Adnan dùng 20/40/60/80/100%; nhóm thêm mốc 10% (10/20/40/60/80/100%) và lấy **40–60%** làm vùng dự đoán sớm đáng tin mà họ báo cáo.

- **Ưu tiên nhóm đặc trưng** [2]: theo phát hiện rằng tương tác và kết quả chiếm ưu thế còn nhân khẩu học đóng góp ít, nhóm tập trung vào nhóm hành vi và kết quả; nhân khẩu học giữ để phân tích công bằng, không dựa vào để dự đoán.

- **Tổng hợp clickstream** [5]: như Liu và cộng sự, nhóm nén clickstream ~10,6 triệu dòng thành đặc trưng/sinh viên gọn (tổng click, ngày hoạt động, số click theo loại, cùng các tỉ lệ phái sinh), nhưng tính **theo từng mốc** cho bối cảnh time-aware.

- **Phòng rò rỉ** [1]: bộ mã hoá, chuẩn hoá và điền khuyết chỉ khớp trên fold huấn luyện, và mọi sự kiện sau mốc bị loại trước khi dựng đặc trưng tại mốc đó — mở rộng kỷ luật thời gian của [1].

- **Phân chia phân tầng bảo toàn nhóm (đóng góp của nhóm)**: khác mọi nghiên cứu khảo sát, nhóm giữ toàn bộ bản ghi của một `id_student` hoàn toàn ở train hoặc test, với tập kiểm tra 20% cố định dùng lại qua các mốc và CV 5-fold × 5 seed trên tập huấn luyện — lấp khoảng trống rò rỉ cấp sinh viên mà các phân chia theo dòng của họ để ngỏ.

- **Định lượng độ ổn định giải thích** [4]: Gunasekara & Saarela đánh giá SHAP/LIME chủ yếu định tính; nhóm thêm chỉ số ổn định định lượng (Jaccard top-*k* + độ lệch chuẩn độ quan trọng đặc trưng), vượt qua đánh giá định tính của họ.

---

## Tài liệu tham khảo

[1] M. Adnan và cộng sự, "Predicting at-Risk Students at Different Percentages of Course Length for Early Intervention Using Machine Learning Models," *IEEE Access*, tập 9, tr. 7519–7539, 2021.

[2] N. Tomasevic, N. Gvozdenovic, và S. Vranes, "An overview and comparison of supervised data mining techniques for student exam performance prediction," *Computers & Education*, tập 143, art. 103676, 2020.

[3] J. Kuzilek, M. Hlosta, và Z. Zdrahal, "Open University Learning Analytics dataset," *Scientific Data*, tập 4, art. 170171, 2017.

[4] S. Gunasekara và M. Saarela, "Explainable AI in Education: Techniques and Qualitative Assessment," *Applied Sciences*, tập 15, số 3, art. 1239, 2025.

[5] Y. Liu, S. Fan, S. Xu, A. Sajjanhar, S. Yeom, và Y. Wei, "Predicting Student Performance Using Clickstream Data and Machine Learning," *Education Sciences*, tập 13, số 1, art. 17, 2023.
