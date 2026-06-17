# Phần nói chi tiết — KHỐI EDA (Bình) · Slide 18–22

**Đề tài:** Time-Aware Explainable ML on OULAD · **DSP391m · Nhóm 1**
**Người nói:** Bình · **Thời lượng mục tiêu:** ~4,5–5 phút · **Hình dùng:** univariate_hist_kde / bivariate_effect_sizes / corr_with_target / time_discrimination_curve / withdrawn_activity_decay

> Ký hiệu: *(in nghiêng)* = chỉ dẫn diễn xuất, không nói ra · **in đậm** = nhấn giọng · ⏸ = dừng một nhịp.
> Mạch 5 slide: **mục tiêu → từng biến (univariate) → biến theo nhãn (bivariate) → các biến với nhau (multivariate + rò rỉ) → theo thời gian (RQ1)**.

---

## Câu mở khối EDA *(nối tiếp ngay sau Slide 17 — gộp bảng)*

"Dữ liệu đến đây đã sạch. Nhưng sạch thôi chưa đủ — trước khi xây mô hình, nhóm em cần **hiểu dữ liệu đang nói lên điều gì**. Đó là việc của phần Phân tích khám phá — gọi tắt là EDA — mà em sẽ trình bày qua bốn góc nhìn nối tiếp nhau: nhìn từng biến một, rồi nhìn biến theo nhãn nguy cơ, rồi nhìn các biến trong mối quan hệ với nhau, và cuối cùng là nhìn theo thời gian."

---

## [Slide 18 — Mục tiêu EDA] · ~35 giây

"Phần EDA của nhóm em có **ba mục tiêu**, và em xin nói rõ ngay từ đầu vì nó định hướng mọi biểu đồ phía sau.

**Thứ nhất là hiểu dữ liệu** — chúng em có hơn **32 nghìn** bản ghi, **33** biến, chia làm ba nhóm: nhân khẩu học, tương tác, và điểm số.

**Thứ hai là kiểm tra chất lượng** — phân phối, thiếu dữ liệu, ngoại lai.

**Thứ ba — và quan trọng nhất** với một đề tài phát hiện *sớm* — là **tìm ra những biến phân biệt được** sinh viên nguy cơ với sinh viên an toàn. ⏸

Em muốn nhấn mạnh: EDA với nhóm em **không phải để trang trí**. Mỗi biểu đồ đều dẫn tới một quyết định cụ thể — hoặc là *chọn đặc trưng nào đưa vào mô hình*, hoặc là *kiểm chứng dữ liệu không bị rò rỉ*. Hai quyết định đó là kim chỉ nam của cả phần này."

---

## [Slide 19 — Univariate: phân tích từng biến] · ~60 giây
*(Hình: univariate_hist_kde.png — chỉ vào các biểu đồ click)*

"Góc nhìn đầu tiên là **từng biến một**. Với mỗi biến số, chúng em vẽ histogram kèm đường mật độ, và biểu đồ hộp để soi ngoại lai.

*(chỉ hình)* Phát hiện nổi bật nhất là **phần lớn các biến click bị lệch phải rất mạnh**. Em lấy một ví dụ cụ thể: biến `clicks_resource` có độ lệch — skew — lên tới **34,7**, và độ nhọn — kurtosis — hơn **hai nghìn một trăm**. Để dễ hình dung: với phân phối chuẩn thì skew bằng 0; con số 34 nghĩa là phân phối *cực kỳ* lệch. ⏸ Diễn giải bằng lời thường: **đại đa số sinh viên chỉ click vài chục lần, nhưng có một nhóm nhỏ click tới hàng nghìn lần**, kéo theo một cái đuôi rất dài về bên phải.

Và đây là điểm em muốn làm rõ: những giá trị cực lớn đó **là ngoại lai thật, phản ánh hành vi học thật**, chứ không phải lỗi nhập liệu. Vì vậy nhóm em **không xóa** chúng — như Phần 3 đã trình bày — mà xử lý bằng phép biến đổi log và chuẩn hóa.

Phân phối lệch mạnh như vậy còn dẫn tới một quyết định *phương pháp*: vì dữ liệu **vi phạm giả định phân phối chuẩn**, nên ở các bước so sánh tiếp theo, chúng em dùng **kiểm định phi tham số** — Mann–Whitney — thay cho t-test, để kết luận không bị sai lệch bởi cái đuôi đó."

---

## [Slide 20 — Bivariate: biến theo nhãn] · ~75 giây
*(Hình: bivariate_effect_sizes.png — chỉ vào thanh xếp hạng)*

"Góc nhìn thứ hai, và là phần quan trọng nhất: **so sánh từng biến theo nhãn nguy cơ**. Câu hỏi đặt ra là: *biến nào thật sự phân biệt được hai nhóm sinh viên?*

Nhắc lại, nhóm nguy cơ chiếm **52,8%**. Với mỗi biến số, chúng em đo **độ lớn khác biệt** giữa hai nhóm bằng **Cohen's d**. Nói nôm na, Cohen's d cho biết trung bình hai nhóm cách nhau **bao nhiêu độ lệch chuẩn** — quy ước d trên 0,8 đã là khác biệt *lớn*. Đi kèm là kiểm định Mann–Whitney và hiệu chỉnh đa kiểm định Benjamini–Hochberg.

*(chỉ ba thanh trên cùng)* Ba biến phân biệt mạnh nhất đều thuộc nhóm **tương tác và điểm số**:
- **Số ngày kể từ lần hoạt động cuối** — d bằng **2,55**, một con số rất lớn;
- **Số bài đã nộp** — d bằng **2,05**;
- **Điểm có trọng số** — d bằng **1,96**.

Em đưa ra con số thật cho dễ cảm nhận: sinh viên nguy cơ trung bình **171 ngày** không hoạt động, trong khi nhóm an toàn chỉ **14 ngày** — chênh hơn mười lần. Và họ chỉ nộp trung bình **2,3 bài**, so với **8,6 bài** ở nhóm an toàn. ⏸

Một lưu ý về thống kê: **cả 19 trên 19 biến số đều có ý nghĩa** — nhưng điều đó *không* có nghĩa biến nào cũng tốt. Khi cỡ mẫu lớn tới 32 nghìn thì p-value gần như luôn nhỏ; **vì vậy chúng em xếp hạng bằng độ lớn hiệu ứng, chứ không bằng p-value**.

Kết luận của slide này — cũng là một thông điệp chính của cả báo cáo: **tín hiệu nguy cơ nằm ở hành vi và kết quả học tập, chứ không phải ở đặc điểm nhân khẩu học**."

*(Nếu cô hỏi về nhân khẩu học:)* "Nhóm nhân khẩu học liên hệ với nhãn rất yếu — chỉ số Cramér's V cao nhất chỉ khoảng **0,15** ở biến trình độ học vấn, còn giới tính gần như bằng 0. Nên chúng em **giữ chúng để phân tích công bằng**, chứ không kỳ vọng chúng dự đoán tốt."

---

## [Slide 21 — Multivariate: tương quan & kiểm tra rò rỉ] · ~70 giây
*(Hình: corr_with_target.png hoặc heatmap — chỉ vào cột tương quan với nhãn)*

"Góc nhìn thứ ba: nhìn **các biến trong mối quan hệ với nhau**. Chúng em dùng cả hai loại tương quan — **Pearson** cho quan hệ tuyến tính, và **Spearman** cho quan hệ đơn điệu; Spearman quan trọng ở đây vì dữ liệu lệch mạnh. Có hai phát hiện.

**Phát hiện thứ nhất — tương quan với nhãn.** *(chỉ hình)* Biến số ngày không hoạt động đạt **cộng 0,78**; số bài nộp và điểm tương quan **âm** khoảng 0,71 đến 0,72 — dấu âm tức là nộp càng nhiều, điểm càng cao thì nguy cơ càng *thấp*, hoàn toàn hợp lý. Điều đáng nói là danh sách này **khớp đúng** với kết quả Cohen's d ở slide trước. ⏸ Tức là **hai phương pháp độc lập cho ra cùng một kết luận** — đó là dấu hiệu kết quả rất đáng tin.

**Phát hiện thứ hai — và đây là một bước bắt buộc của đề tài: kiểm tra rò rỉ dữ liệu.** Logic của chúng em là: nếu một biến tương quan *gần như hoàn hảo* với nhãn — em đặt ngưỡng từ **0,95** trở lên — thì rất đáng nghi rằng biến đó vô tình chứa sẵn đáp án, tức là rò rỉ. Kết quả: **không có biến nào vượt ngưỡng**; mạnh nhất chỉ 0,78, một mức hợp lý về mặt giáo dục chứ không phải rò rỉ.

Một điểm phụ nhưng cần nêu: có **hai cặp biến đa cộng tuyến cao** — ví dụ tổng click và số ngày hoạt động tương quan 0,84. Điều này chúng em **ghi nhận để dành cho RQ2**, vì các biến trùng lặp thông tin có thể làm cho phần *giải thích mô hình kém ổn định* — đúng cái mà đề tài muốn đo."

---

## [Slide 22 — Time-aware & kết luận EDA (RQ1)] · ~80 giây
*(Hình: time_discrimination_curve.png — chỉ vào các đường đi lên; có thể nhắc withdrawn_activity_decay)*

"Góc nhìn cuối, và là phần gắn trực tiếp với câu hỏi nghiên cứu số một: **tín hiệu nguy cơ xuất hiện từ giai đoạn nào của khóa học?**

Để trả lời, chúng em tính lại Cohen's d cho từng biến **tại cả sáu mốc tiến độ**, từ 10% đến 100%. *(chỉ đường cong đi lên)* Kết quả là **khả năng phân biệt tăng dần đều theo thời gian**. Ví dụ, điểm có trọng số tăng từ **0,61** ở mốc 10% lên gần **1,96** ở cuối khóa; số bài nộp tăng từ **0,67** lên **2,05**. Càng về sau, dữ liệu càng tích lũy, tín hiệu càng rõ — điều này hợp trực giác.

Nhưng điểm mấu chốt cho *phát hiện sớm* là: **tín hiệu xuất hiện rất sớm**. Ngay từ mốc **10%**, biến số ngày hoạt động đã đạt mức phân biệt mạnh; và đến mốc **20%**, cả điểm lẫn số bài nộp đều đã mạnh. ⏸ Nghĩa là **chỉ với khoảng một phần năm đầu khóa học, mô hình đã có đủ tín hiệu để cảnh báo** — đúng mục tiêu của đề tài.

Em xin đưa thêm một minh chứng cho cách nhóm xử lý nhãn rút môn. *(nhắc hình withdrawn)* Sinh viên rút môn có **trung vị 233 ngày** không hoạt động và chỉ **89 cú click**, so với **1.425 click** ở nhóm an toàn. Sự **sụp đổ hoạt động** này chính là thứ làm cho phát hiện sớm trở nên khả thi — nó là tín hiệu, không phải nhiễu.

*(chốt, chậm lại)* Tóm lại, phần EDA cho nhóm em **ba kết luận**:
một, tín hiệu nằm ở nhóm tương tác và điểm — nên đó là các đặc trưng được ưu tiên;
hai, dữ liệu **không có rò rỉ**;
ba, **dự đoán sớm là khả thi từ khoảng 20% tiến độ khóa học**.
Ba kết luận này chính là cơ sở để nhóm bước sang giai đoạn biến đổi dữ liệu và xây mô hình."

---

## Câu chuyển giao *(sang Phần 4 — Đức)*

"Đã hiểu dữ liệu nói gì, bước tiếp theo là biến đổi nó cho mô hình đọc được — em xin mời bạn Đức trình bày Phần 4."

---

## Mẹo trình bày khối EDA

- **Mở bằng con số gây ấn tượng** nếu muốn tạo điểm nhấn: *"171 ngày không hoạt động ở nhóm nguy cơ, so với 14 ngày ở nhóm an toàn"* — rất trực quan.
- **Slide 20 ↔ 21 là cặp đôi**: nhấn câu *"hai phương pháp độc lập cho cùng kết luận → đáng tin"*. Đây là điểm cộng học thuật.
- **Đừng sa đà vào con số**: mỗi slide chỉ cần 2–3 con số "đắt"; phần còn lại nói ý.
- **Nhịp**: chậm ở Slide 20 (quan trọng nhất) và đoạn chốt Slide 22; nhanh hơn ở Slide 18–19.
- ⚠️ **Tránh bẫy nhất quán:** ở Slide 22 chỉ trích quỹ đạo của *điểm có trọng số* và *số bài nộp* (kết thúc đúng bằng d ở Slide 20). **Không** nói "days_since đạt 1,56 ở mốc 100%" vì Slide 20 đã nói d = 2,55 — xem Q&A #6.

## Q&A riêng cho khối EDA

| # | Câu hỏi | Trả lời gọn |
|---|---|---|
| 6 | `days_since` ở Slide 20 là 2,55 mà đường cong Slide 22 chỉ tới 1,56? | Hai chỉ số tính trên **hai bộ khác nhau**: Slide 20 trên `master_raw` (clickstream đầy đủ → 2,55); đường cong trên `dataset_t100` đã **cắt click sau ngày mốc** (→ 1,56). Riêng biến này nhạy với "ngày hoạt động cuối"; **5 biến còn lại khớp tuyệt đối** giữa hai bảng. |
| 7 | `days_since` tương quan 0,78 — có phải rò rỉ? | Không. Ngưỡng nghi rò rỉ là 0,95; 0,78 còn xa, và hợp lý về giáo dục. Quan trọng hơn: hàm `cut_at_checkpoint` chỉ tính hoạt động **tới ngày mốc**, không nhìn tương lai. |
| 8 | Sao dùng Mann–Whitney & Spearman, không dùng t-test & Pearson? | Vì dữ liệu lệch phải mạnh (skew tới 34,7), vi phạm giả định chuẩn của t-test/Pearson; phương pháp phi tham số bền vững hơn. Vẫn báo Pearson để so sánh. |
| 9 | 19/19 biến đều có ý nghĩa — vậy biến nào cũng tốt? | Không. n lớn nên p gần như luôn nhỏ; nhóm xếp hạng bằng **Cohen's d**, theo đó nhân khẩu học rất yếu (d ≤ 0,28). |
| — | Cohen's d là gì? | Khoảng cách giữa trung bình hai nhóm, tính theo đơn vị độ lệch chuẩn; d ≥ 0,8 là khác biệt lớn. |
| — | Cramér's V là gì? | Độ mạnh liên hệ giữa hai biến phân loại, từ 0 đến 1; ở đây ≤ 0,15 nghĩa là liên hệ yếu. |
