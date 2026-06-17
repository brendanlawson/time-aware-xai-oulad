# Kịch bản thuyết trình chi tiết — TASK 3 (theo từng người)

**Đề tài:** Time-Aware Explainable ML for Early At-Risk Student Prediction on OULAD
**DSP391m · Nhóm 1 · Đại học FPT · GVHD: Nguyễn Thị Hoàng Yến**
**Gắn với file:** `reports/Task3_Presentation.pptx` (33 slide nội dung) — số slide trong kịch bản trùng số trang trên slide.

---

## Hướng dẫn dùng kịch bản

- Văn nói ngôi thứ nhất, đọc tự nhiên (không đọc nguyên văn từng chữ — nắm ý rồi nói).
- Ký hiệu: **[Slide N]** = chuyển sang trang N · *(in nghiêng)* = chỉ dẫn hành động (chỉ vào biểu đồ, dừng nhịp), không nói ra.
- **»» Chuyển giao** = câu bàn giao cho người tiếp theo.
- Tổng thời lượng mục tiêu: **~18–20 phút** + Q&A.

| Người | Phần | Slide | Thời lượng |
|---|---|---|---|
| **An** | Mở đầu + Kết luận | 1–3 · 32–33 | ~3 phút |
| **Sơn** | Phần 1 — Xác định dữ liệu | 4–7 | ~3 phút |
| **Phúc** | Phần 2 — Thu thập dữ liệu | 8–11 | ~3,5 phút |
| **Bình** | Phần 3 — Làm sạch + Khối EDA | 12–22 | ~7 phút |
| **Đức** | Phần 4 — Chuẩn hoá & biến đổi | 23–27 | ~3,5 phút |
| **Khoa** | Phần 5 — Tách train/test | 28–31 | ~3,5 phút |

---

# 👤 AN — Mở đầu (Slide 1–3) · ~1,5 phút

**[Slide 1 — Trang bìa]**
"Em xin kính chào cô và các bạn. Nhóm 1 chúng em xin trình bày báo cáo Task 3 — *Thu thập và Tiền xử lý dữ liệu* — của đề tài *Phát hiện sớm sinh viên có nguy cơ học kém trên bộ dữ liệu OULAD, bằng học máy có khả năng giải thích*. Nhóm gồm sáu thành viên: Sơn, Khoa, An, Đức, Phúc và Bình; giảng viên hướng dẫn là cô Nguyễn Thị Hoàng Yến. Em là An, em xin mở đầu."

**[Slide 2 — Mục lục]**
"Bài báo cáo gồm năm phần đúng theo yêu cầu: xác định dữ liệu cần có, phương pháp thu thập, làm sạch dữ liệu, chuẩn hoá và biến đổi, và tách tập train/test. Ngoài ra nhóm bổ sung một khối Phân tích khám phá dữ liệu — EDA — đặt ngay sau phần làm sạch. *(nhấn)* Một điểm em xin lưu ý trước: mỗi mục chúng em đều trình bày theo ba ý — **làm gì, vì sao làm, và kết quả đầu ra là gì**."

**[Slide 3 — Bức tranh tổng thể]**
"Đây là bức tranh tổng thể của toàn bộ pipeline dữ liệu, em sẽ dùng làm slide 'neo' để cả nhóm và người nghe luôn biết đang ở bước nào. *(chỉ vào sơ đồ)* Chúng em đi từ bảy bảng OULAD thô — trong đó có hơn mười triệu dòng clickstream — gộp lại thành một bảng master 32.593 dòng, 33 cột; sau đó cắt dữ liệu theo sáu mốc thời gian của khóa học; tiền xử lý theo một trình tự chống rò rỉ; rồi tách train/test. Đầu ra cuối cùng là **sáu bộ dữ liệu theo mốc thời gian** và một **tập kiểm tra cố định**, và toàn bộ được **mười sáu kiểm thử tự động** xác nhận là không rò rỉ dữ liệu."

**»» Chuyển giao:** "Để bắt đầu, em xin mời bạn Sơn trình bày Phần 1 — Xác định dữ liệu cần có."

---

# 👤 SƠN — Phần 1: Xác định dữ liệu cần có (Slide 4–7) · ~3 phút

*(Nhận sân khấu)* "Cảm ơn An. Em là Sơn, em xin trình bày phần đầu tiên: chúng ta cần những dữ liệu gì cho đề tài này."

**[Slide 4 — Bài toán & mục tiêu]**
"Trước hết là mục tiêu. **Làm gì** — đề tài giải quyết bài toán phát hiện *sớm* những sinh viên có nguy cơ học kém trong môi trường học trực tuyến, và quan trọng không kém là phải *giải thích được* vì sao mô hình lại cảnh báo một sinh viên. **Vì sao** lại đặt vấn đề như vậy: vì các nghiên cứu trước có ba điểm yếu lặp đi lặp lại — mô hình mạnh thì là hộp đen nên giảng viên không tin để hành động; đa số chỉ dự đoán ở cuối khóa, lúc đó can thiệp đã muộn; và lớp sinh viên nguy cơ là thiểu số nên mô hình hay bỏ sót. **Kết quả** — vì thế dữ liệu của Task 3 phải đủ để trả lời ba câu hỏi nghiên cứu: dự đoán sớm tới mức nào (RQ1), giải thích có ổn định không (RQ2), và xử lý mất cân bằng thế nào (RQ3)."

**[Slide 5 — Biến mục tiêu]**
"Tiếp theo là biến mục tiêu. Đây là bài toán **phân loại nhị phân**: nhãn `at_risk` được suy ra từ cột kết quả cuối khóa `final_result`. Chúng em gộp **Fail và Withdrawn** — tức trượt và rút môn — thành nhóm *nguy cơ*; còn **Pass và Distinction** — qua môn và xuất sắc — thành nhóm *an toàn*. Lý do gộp như vậy là theo tiêu chí 'có cần can thiệp hay không', đúng với mục tiêu cảnh báo sớm. *(chỉ vào biểu đồ)* Về tỉ lệ: nhóm nguy cơ chiếm **52,8%**, tức 17.208 sinh viên, còn nhóm an toàn 47,2%. Em xin nhấn mạnh đây là **con số thật** của bộ dữ liệu — mất cân bằng *nhẹ* — chứ không phải tỉ lệ 68/32 mà đôi khi ta thấy trên các slide minh họa."

**[Slide 6 — Ba nhóm dữ liệu]**
"Để giải bài toán, chúng em xác định cần **ba nhóm dữ liệu đầu vào**. Nhóm thứ nhất là **nhân khẩu học** — giới tính, vùng miền, trình độ học vấn, chỉ số khó khăn khu vực, độ tuổi. Nhóm thứ hai là **tương tác** — dữ liệu clickstream ghi lại sinh viên click vào hệ thống học bao nhiêu, vào những loại tài nguyên nào, hoạt động bao nhiêu ngày. Nhóm thứ ba là **kết quả đánh giá** — điểm các bài đã nộp, số bài nộp, và cờ chưa nộp. Mỗi nhóm có một vai trò: nhân khẩu học cho *bối cảnh và phân tích công bằng*; tương tác là *tín hiệu hành vi sớm nhất*; kết quả là *bằng chứng năng lực*. Việc chia ba nhóm rõ ràng còn giúp chúng em diễn giải mô hình theo từng nhóm về sau."

**[Slide 7 — Đơn vị quan sát, phạm vi, loại trừ]**
"Cuối phần này là ba điểm về phạm vi. **Đơn vị quan sát**: mỗi dòng dữ liệu là một *sinh viên trong một môn–kỳ cụ thể* — khóa được định danh bởi mã môn, mã kỳ và mã sinh viên. **Phạm vi**: 32.593 bản ghi, trải trên 22 môn–kỳ, bảy bảng quan hệ, thuộc các kỳ năm 2013–2014 của Open University. **Dữ liệu loại trừ**: chúng em bỏ các cột định danh khỏi đặc trưng; đặc biệt *không* dùng biến ngày rút môn `date_unregistration` làm đặc trưng vì nó vừa là thông tin tương lai gây rò rỉ, vừa thiếu mang tính cấu trúc; và bỏ biến `final_result` gốc sau khi đã tạo nhãn. Việc xác định rõ đơn vị quan sát và loại trừ sớm chính là để tránh rò rỉ và nhân bản dữ liệu."

**»» Chuyển giao:** "Đó là dữ liệu chúng em cần. Vậy lấy ở đâu và lấy bằng cách nào — em xin mời bạn Phúc."

---

# 👤 PHÚC — Phần 2: Phương pháp thu thập (Slide 8–11) · ~3,5 phút

*(Nhận sân khấu)* "Cảm ơn Sơn. Em là Phúc, phụ trách phần pipeline dữ liệu, em xin trình bày phương pháp thu thập."

**[Slide 8 — Nguồn & loại dữ liệu]**
"Về nguồn: chúng em dùng bộ **Open University Learning Analytics Dataset — gọi tắt là OULAD** — công bố bởi Kuzilek và cộng sự năm 2017. Đây là **dữ liệu thứ cấp**, công khai, đã được **ẩn danh ngay tại nguồn**, và cấp phép theo chuẩn **CC-BY 4.0**. Vì là dữ liệu thứ cấp đã ẩn danh, yêu cầu về đạo đức được đáp ứng đơn giản bằng việc trích dẫn đúng quy cách; chúng em không hề xử lý dữ liệu cá nhân nhạy cảm. Kết quả là một nguồn vừa hợp pháp, vừa tái lập được, lại không tốn chi phí thu thập sơ cấp — rất phù hợp cho một đồ án học thuật."

**[Slide 9 — Cách thu thập & 7 bảng]**
"Cách thu thập gồm ba bước: tải bảy file CSV, đặt vào thư mục `data/raw`, và **xác minh tính toàn vẹn bằng mã băm MD5** ghi trong file manifest — để chắc chắn không ai tải nhầm hay tải thiếu. Bảy bảng đó là: thông tin sinh viên, thông tin khóa học, đăng ký, *bảng tương tác studentVle* với hơn **10,6 triệu dòng**, bảng mô tả tài nguyên, bảng đánh giá, và bảng bài nộp. *(nhấn)* Vì bảng tương tác rất nặng, chúng em đọc theo từng khối 500 nghìn dòng để tránh tràn bộ nhớ. Điểm mấu chốt: dữ liệu thô được 'đóng băng' kèm checksum, nên cả nhóm dùng đúng *một* bản như nhau."

**[Slide 10 — Mối liên hệ giữa các bảng]**
"Bảy bảng này liên kết với nhau bằng ba loại khóa. *(chỉ sơ đồ)* Khóa chính là bộ ba *mã môn, mã kỳ, mã sinh viên* — nó nối bảng thông tin sinh viên với bảng đăng ký, bảng tương tác đã tổng hợp, và bảng kết quả. Thứ hai, `id_site` nối bảng tương tác với bảng tài nguyên, để biết mỗi cú click thuộc *loại hoạt động* nào. Thứ ba, `id_assessment` nối bài nộp với bảng đánh giá, để lấy *trọng số* và *hạn nộp*. Hiểu đúng các khóa này là điều kiện để bước gộp ở phần sau không bị nhân bản dòng — trong code chúng em ràng buộc bằng tham số `validate='many_to_one'`."

**[Slide 11 — Đánh giá nguồn]**
"Cuối cùng em đánh giá nguồn theo bốn khía cạnh. **Phù hợp**: bộ dữ liệu có đủ cả ba nhóm đặc trưng *và* có dấu thời gian, nên cho phép làm dự đoán theo mốc; quy mô 32 nghìn là đủ lớn. **Ưu điểm**: là chuẩn benchmark quốc tế, đã ẩn danh, tái lập, miễn phí. **Hạn chế**: là dữ liệu thứ cấp của một trường nên khó tổng quát hóa; click chỉ là *số đếm*, không có nội dung; và dữ liệu thuộc năm 2013–2014. **Rủi ro**: mất cân bằng nhẹ, thiếu mang tính cấu trúc, phân phối lệch phải mạnh, đa cộng tuyến, và nguy cơ rò rỉ thời gian — nhưng mỗi rủi ro này đều đã có phương án xử lý ở các phần tiếp theo."

**»» Chuyển giao:** "Dữ liệu thô đã sẵn sàng. Bước làm sạch và khám phá, em xin mời bạn Bình."

---

# 👤 BÌNH — Phần 3: Làm sạch + Khối EDA (Slide 12–22) · ~7 phút

*(Nhận sân khấu)* "Cảm ơn Phúc. Em là Bình, em phụ trách phần làm sạch dữ liệu và phân tích khám phá."

### Phần 3 — Làm sạch (Slide 12–17)

**[Slide 12 — Tổng quan dữ liệu thô]**
"Sau khi gộp, bảng master có **32.593 dòng và 33 cột**. Việc đầu tiên là khám tổng quát: kiểm tra số dòng, số cột, và kiểu của từng biến — coi như 'khám sức khỏe' tổng thể trước khi can thiệp, để biết chính xác mình đang xử lý dữ liệu loại gì."

**[Slide 13 — Dữ liệu thiếu]**
"Về giá trị thiếu, may mắn là **chỉ có ba cột** bị thiếu. *(chỉ bảng)* `date_unregistration` thiếu tới 22.521 dòng, nhưng đây là thiếu *mang tính cấu trúc* — đa số sinh viên không rút môn thì làm gì có ngày rút — nên chúng em không dùng nó làm đặc trưng. `imd_band` thiếu 1.111 dòng, chúng em điền 'Unknown' thành một nhóm riêng. `date_registration` thiếu 45 dòng, điền bằng trung vị của tập train. Một điểm quan trọng: điểm số và số bài nộp thiếu là do sinh viên *chưa nộp* tới thời điểm xét, nên chúng em điền 0 *kèm thêm một cờ* `not_submitted`. **Vì sao** phải làm vậy: vì 'chưa nộp' là một *tín hiệu nguy cơ thật*, không phải nhiễu. Sau xử lý, không còn giá trị khuyết ở bất kỳ cột đặc trưng nào."

**[Slide 14 — Trùng lặp & chuẩn hoá định dạng]**
"Tiếp theo là trùng lặp và định dạng. Chúng em kiểm tra trùng theo khóa sinh viên–môn–kỳ và kết quả là **không có dòng nào trùng**. Về kiểu dữ liệu, chúng em lập một *danh mục* phân loại biến thành năm loại: định lượng, thứ bậc, danh định, nhị phân và chỉ báo — đây là cơ sở để mã hóa đúng ở Phần 4. Về chuẩn hóa định dạng, chúng em cắt khoảng trắng thừa trong nhãn phân loại và đối chiếu số giá trị với từ điển dữ liệu — ví dụ vùng miền phải đúng 13 giá trị, học vấn 5, để 'Y' có dấu cách không bị tính khác 'Y'."

**[Slide 15 — Phát hiện ngoại lai]**
"Đây là phần em trực tiếp làm. Chúng em dò bất thường logic — ví dụ điểm phải nằm trong khoảng 0 đến 100 — và dò ngoại lai bằng quy tắc IQR. *(chỉ boxplot)* Phát hiện rõ nhất là các biến click *lệch phải rất mạnh*: ví dụ `clicks_resource` có độ lệch khoảng 35 và biến `max_clicks_single_day` có giá trị lớn nhất gần 7.000. Em đã tổng hợp bảy biến nghi ngoại lai và bàn giao cho bạn Đức để thống nhất chiến lược xử lý."

**[Slide 16 — Xử lý ngoại lai]**
"Cách xử lý theo từng biến: với 12 biến click lệch mạnh dùng phép biến đổi **log1p**; với biến lệch vừa dùng **winsorize** cắt 1% ở hai đầu; còn biến nằm trong phạm vi tự nhiên thì *giữ nguyên*. **Nguyên tắc quan trọng nhất**: chúng em **không xóa bất kỳ dòng nào**. Lý do là giá trị cực trị của sinh viên nguy cơ — chẳng hạn học lại môn nhiều lần — chính là *tín hiệu* cần giữ, chứ không phải lỗi. Kết quả là mọi biến số có phân phối 'thuần' hơn mà vẫn giữ nguyên đủ 32.593 dòng."

**[Slide 17 — Gộp bảng & bộ sạch cuối]**
"Khép lại phần làm sạch là bước gộp. *(chỉ bảng)* Chúng em gộp bằng *left join* lên bảng nền là thông tin sinh viên, lần lượt nối đăng ký, tương tác, kết quả và khóa học. Nhật ký số dòng *trước và sau* mỗi phép gộp đều giữ nguyên 32.593 — chứng minh không nhân bản, không thất thoát. Đầu ra là bảng **master sạch, 32.593 dòng 33 cột**, mỗi dòng một sinh viên–môn–kỳ."

### Khối EDA — Phân tích khám phá (Slide 18–22)

*(Chuyển nhịp — chậm lại)* "Dữ liệu đến đây đã sạch. Nhưng sạch thôi chưa đủ — trước khi xây mô hình, nhóm em cần **hiểu dữ liệu đang nói lên điều gì**. Đó là việc của phần Phân tích khám phá — gọi tắt là EDA — mà em sẽ trình bày qua bốn góc nhìn nối tiếp nhau: nhìn từng biến một, rồi nhìn biến theo nhãn nguy cơ, rồi nhìn các biến trong mối quan hệ với nhau, và cuối cùng là nhìn theo thời gian."

**[Slide 18 — Mục tiêu EDA]**
"Phần EDA của nhóm em có **ba mục tiêu**, em xin nói rõ ngay vì nó định hướng mọi biểu đồ phía sau. **Thứ nhất, hiểu dữ liệu** — hơn **32 nghìn** bản ghi, **33** biến, ba nhóm: nhân khẩu học, tương tác và điểm số. **Thứ hai, kiểm tra chất lượng** — phân phối, thiếu dữ liệu, ngoại lai. **Thứ ba — và quan trọng nhất** với một đề tài phát hiện *sớm* — là **tìm ra những biến phân biệt được** sinh viên nguy cơ với sinh viên an toàn. *(dừng nhịp)* Em muốn nhấn mạnh: EDA với nhóm em **không phải để trang trí**. Mỗi biểu đồ đều dẫn tới một quyết định cụ thể — hoặc *chọn đặc trưng nào đưa vào mô hình*, hoặc *kiểm chứng dữ liệu không bị rò rỉ*. Hai quyết định đó là kim chỉ nam của cả phần này."

**[Slide 19 — Univariate: phân tích từng biến]**
"Góc nhìn đầu tiên là **từng biến một**. Với mỗi biến số, chúng em vẽ histogram kèm đường mật độ, và biểu đồ hộp để soi ngoại lai. *(chỉ hình)* Phát hiện nổi bật nhất: **phần lớn các biến click bị lệch phải rất mạnh**. Em lấy một ví dụ cụ thể — `clicks_resource` có độ lệch, tức skew, lên tới **34,7**, và độ nhọn, tức kurtosis, hơn **hai nghìn một trăm**. Để dễ hình dung: với phân phối chuẩn thì skew bằng 0, nên con số 34 nghĩa là phân phối *cực kỳ* lệch. *(dừng nhịp)* Nói bằng lời thường: **đại đa số sinh viên chỉ click vài chục lần, nhưng một nhóm nhỏ click tới hàng nghìn lần**, kéo theo một cái đuôi rất dài về bên phải. Điểm em muốn làm rõ: những giá trị cực lớn đó **là ngoại lai thật, phản ánh hành vi học thật**, chứ không phải lỗi nhập liệu — nên nhóm em **không xóa**, mà xử lý bằng phép biến đổi log và chuẩn hóa. Phân phối lệch mạnh còn dẫn tới một quyết định *phương pháp*: vì dữ liệu **vi phạm giả định phân phối chuẩn**, ở các bước so sánh tiếp theo chúng em dùng **kiểm định phi tham số Mann–Whitney** thay cho t-test, để kết luận không bị sai lệch bởi cái đuôi đó."

**[Slide 20 — Bivariate: biến theo nhãn]**
"Góc nhìn thứ hai, và là phần quan trọng nhất: **so sánh từng biến theo nhãn nguy cơ** — câu hỏi đặt ra là *biến nào thật sự phân biệt được hai nhóm sinh viên?* Nhắc lại, nhóm nguy cơ chiếm **52,8%**. Với mỗi biến số, chúng em đo **độ lớn khác biệt** giữa hai nhóm bằng **Cohen's d** — nói nôm na, d cho biết trung bình hai nhóm cách nhau **bao nhiêu độ lệch chuẩn**, quy ước d trên 0,8 đã là khác biệt *lớn* — kèm kiểm định Mann–Whitney và hiệu chỉnh Benjamini–Hochberg. *(chỉ ba thanh trên cùng)* Ba biến phân biệt mạnh nhất đều thuộc nhóm **tương tác và điểm**: **số ngày kể từ lần hoạt động cuối** d bằng **2,55** — một con số rất lớn; **số bài đã nộp** **2,05**; và **điểm có trọng số** **1,96**. Em đưa con số thật cho dễ cảm nhận: sinh viên nguy cơ trung bình **171 ngày** không hoạt động, trong khi nhóm an toàn chỉ **14 ngày** — chênh hơn mười lần; và chỉ nộp trung bình **2,3 bài** so với **8,6 bài**. *(dừng nhịp)* Một lưu ý về thống kê: **cả 19 trên 19 biến số đều có ý nghĩa** — nhưng điều đó *không* nghĩa là biến nào cũng tốt. Khi cỡ mẫu lớn tới 32 nghìn thì p-value gần như luôn nhỏ; **vì vậy chúng em xếp hạng bằng độ lớn hiệu ứng, chứ không bằng p-value**. Kết luận của slide này — cũng là một thông điệp chính của cả báo cáo: **tín hiệu nguy cơ nằm ở hành vi và kết quả học tập, chứ không phải ở đặc điểm nhân khẩu học**."
*(Nếu cô hỏi nhân khẩu học:)* "Nhóm nhân khẩu học liên hệ với nhãn rất yếu — chỉ số Cramér's V cao nhất chỉ khoảng **0,15** ở biến trình độ học vấn, còn giới tính gần như bằng 0. Nên chúng em **giữ chúng để phân tích công bằng**, chứ không kỳ vọng dùng để dự đoán."

**[Slide 21 — Multivariate: tương quan & kiểm tra rò rỉ]**
"Góc nhìn thứ ba: nhìn **các biến trong mối quan hệ với nhau**. Chúng em dùng cả **Pearson** cho quan hệ tuyến tính và **Spearman** cho quan hệ đơn điệu — Spearman quan trọng ở đây vì dữ liệu lệch. Có hai phát hiện. **Phát hiện thứ nhất — tương quan với nhãn.** *(chỉ hình)* Biến số ngày không hoạt động đạt **cộng 0,78**; số bài nộp và điểm tương quan **âm** khoảng 0,71 đến 0,72 — dấu âm nghĩa là nộp càng nhiều, điểm càng cao thì nguy cơ càng *thấp*, hoàn toàn hợp lý. Điều đáng nói là danh sách này **khớp đúng** với kết quả Cohen's d ở slide trước. *(dừng nhịp)* Tức là **hai phương pháp độc lập cho ra cùng một kết luận** — đó là dấu hiệu kết quả rất đáng tin. **Phát hiện thứ hai — và đây là bước bắt buộc của đề tài: kiểm tra rò rỉ dữ liệu.** Logic của chúng em là: nếu một biến tương quan *gần như hoàn hảo* với nhãn — em đặt ngưỡng từ **0,95** trở lên — thì rất đáng nghi rằng nó vô tình chứa sẵn đáp án. Kết quả: **không có biến nào vượt ngưỡng**; mạnh nhất chỉ 0,78, một mức hợp lý về mặt giáo dục chứ không phải rò rỉ. Một điểm phụ nhưng cần nêu: có **hai cặp biến đa cộng tuyến cao** — ví dụ tổng click và số ngày hoạt động tương quan 0,84. Điều này chúng em **ghi nhận để dành cho RQ2**, vì các biến trùng lặp thông tin có thể làm phần *giải thích mô hình kém ổn định* — đúng cái mà đề tài muốn đo."

**[Slide 22 — Time-aware & kết luận EDA (RQ1)]**
"Góc nhìn cuối, và là phần gắn trực tiếp với câu hỏi nghiên cứu số một: **tín hiệu nguy cơ xuất hiện từ giai đoạn nào của khóa học?** Để trả lời, chúng em tính lại Cohen's d cho từng biến **tại cả sáu mốc tiến độ**, từ 10% đến 100%. *(chỉ các đường đi lên)* Kết quả là **khả năng phân biệt tăng dần đều theo thời gian** — ví dụ điểm có trọng số tăng từ **0,61** ở mốc 10% lên gần **1,96** ở cuối khóa; số bài nộp tăng từ **0,67** lên **2,05**. Càng về sau dữ liệu càng tích lũy, tín hiệu càng rõ — điều này hợp trực giác. Nhưng điểm mấu chốt cho *phát hiện sớm* là: **tín hiệu xuất hiện rất sớm**. Ngay từ mốc **10%**, biến số ngày hoạt động đã đạt mức phân biệt mạnh; và đến mốc **20%**, cả điểm lẫn số bài nộp đều đã mạnh. *(dừng nhịp)* Nghĩa là **chỉ với khoảng một phần năm đầu khóa học, mô hình đã có đủ tín hiệu để cảnh báo** — đúng mục tiêu của đề tài. Em xin đưa thêm một minh chứng cho cách nhóm xử lý nhãn rút môn. *(nhắc hình withdrawn)* Sinh viên rút môn có **trung vị 233 ngày** không hoạt động và chỉ **89 cú click**, so với **1.425 click** ở nhóm an toàn. Sự **sụp đổ hoạt động** này chính là thứ làm cho phát hiện sớm trở nên khả thi — nó là tín hiệu, không phải nhiễu. *(chốt, chậm lại)* Tóm lại, phần EDA cho nhóm em **ba kết luận**: một, tín hiệu nằm ở nhóm tương tác và điểm — nên đó là các đặc trưng được ưu tiên; hai, dữ liệu **không có rò rỉ**; ba, **dự đoán sớm là khả thi từ khoảng 20% tiến độ khóa học**. Ba kết luận này chính là cơ sở để nhóm bước sang giai đoạn biến đổi dữ liệu và xây mô hình."
*(⚠️ Tránh bẫy nhất quán: KHÔNG nói "days_since đạt 1,56 ở mốc 100%" cạnh "d = 2,55" của Slide 20 — hai số tính trên hai bộ khác nhau; xem Q&A #6.)*

**»» Chuyển giao:** "Đã hiểu dữ liệu nói gì, bước biến đổi để mô hình đọc được — em xin mời bạn Đức trình bày Phần 4."

---

# 👤 ĐỨC — Phần 4: Chuẩn hoá & biến đổi (Slide 23–27) · ~3,5 phút

*(Nhận sân khấu)* "Cảm ơn Bình. Em là Đức, em phụ trách module tiền xử lý, em xin trình bày phần chuẩn hóa và biến đổi dữ liệu."

**[Slide 23 — Mã hoá biến phân loại]**
"Đầu tiên là mã hóa biến phân loại — chuyển chữ thành số để mô hình đọc được. Chúng em dùng **bốn chiến lược tùy bản chất biến**. *(chỉ bảng)* Biến *thứ bậc* như trình độ học vấn, chỉ số khó khăn, độ tuổi dùng **OrdinalEncoder** với thứ tự cố định, để giữ thứ tự nội tại. Biến *danh định* như vùng miền, mã môn, mã kỳ dùng **OneHotEncoder**. Biến *nhị phân* như giới tính, khuyết tật dùng mã 0/1. Biến *chỉ báo* `not_submitted` thì giữ nguyên vì đã là 0/1. **Vì sao** phải phân biệt: nếu mã hóa sai — chẳng hạn dùng one-hot cho biến thứ bậc — ta sẽ *xóa mất thông tin thứ tự*, làm mô hình kém đi."

**[Slide 24 — Biến đổi lệch (log1p)]**
"Như phần EDA đã chỉ ra, các biến click lệch phải rất mạnh. Vì vậy chúng em áp dụng phép biến đổi **log1p** — tức lấy logarit của một cộng giá trị — cho các biến này. **Vì sao**: log1p kéo cái đuôi nặng về, giúp ổn định các mô hình tuyến tính và các mô hình dựa trên khoảng cách. Bằng chứng thực nghiệm chính là độ lệch từ 13 đến 35 mà phần EDA đã đo. Kết quả là các đặc trưng click có phân phối cân đối hơn, mà vẫn không mất dòng nào."

**[Slide 25 — Chuẩn hoá thang đo]**
"Tiếp theo là chuẩn hóa thang đo bằng **StandardScaler** — đưa mỗi biến số về trung bình 0 và độ lệch chuẩn 1. **Vì sao** cần thiết: tổng số click có thể lên tới hàng nghìn, trong khi điểm số chỉ từ 0 đến 100 — nếu để nguyên thì biến click sẽ *áp đảo* về biên độ, đặc biệt gây hại cho Logistic Regression và mạng nơ-ron. **Điểm mấu chốt chống rò rỉ**: chúng em **chỉ `fit` trên tập train**, rồi *transform* cho cả train lẫn test — nghĩa là trung bình và độ lệch chuẩn chỉ học từ train. Đây là cầu nối sang Phần 5 của bạn Khoa."

**[Slide 26 — Tạo đặc trưng mới]**
"Phần này là feature engineering — tạo đặc trưng mới. *(chỉ hình)* Từ clickstream chúng em tạo: tổng click, số ngày hoạt động, click theo từng loại tài nguyên, và đặc biệt *số ngày kể từ lần hoạt động cuối*. Từ bài nộp chúng em tạo: điểm trung bình, *điểm có trọng số*, số bài nộp, và cờ *chưa nộp*. Mỗi đặc trưng gắn với một giả thuyết rõ ràng — ví dụ 'ngừng hoạt động lâu hoặc bỏ nộp bài thì nguy cơ cao'. Và **ý nghĩa của chúng đã được kiểm chứng** bằng Cohen's d ở phần EDA: số ngày không hoạt động đạt 2,55, số bài nộp 2,05, điểm có trọng số 1,96 — tức các đặc trưng mới này phân biệt hai lớp *rất mạnh*. Đồng thời chúng em loại các biến thừa như cột định danh và biến nhãn gốc."

**[Slide 27 — Mất cân bằng]**
"Cuối cùng là mất cân bằng. Như đã nói, nhóm nguy cơ 52,8% so với an toàn 47,2% — tỷ số mất cân bằng chỉ **1,12**, tức *nhẹ*. **Vì sao** vẫn phải quan tâm: vì bỏ sót một sinh viên nguy cơ là sai lầm *đắt nhất*, nên chỉ số đánh giá chính của chúng em là **PR-AUC và recall trên lớp nguy cơ**, chứ không phải độ chính xác tổng thể. **Phương án** cho câu hỏi RQ3: chúng em sẽ so sánh bốn chiến lược — không tái lấy mẫu, gán trọng số lớp, SMOTE, và ADASYN — và lưu ý là *chỉ tái lấy mẫu trên tập train sau khi đã transform*, tuyệt đối không đụng vào test."

**»» Chuyển giao:** "Vậy làm sao chia dữ liệu và đảm bảo không rò rỉ — em xin mời bạn Khoa."

---

# 👤 KHOA — Phần 5: Tách train/test & chống rò rỉ (Slide 28–31) · ~3,5 phút

*(Nhận sân khấu)* "Cảm ơn Đức. Em là Khoa, phụ trách phần thời gian và chia dữ liệu, em xin trình bày phần cuối."

**[Slide 28 — Mục đích, tỷ lệ, phương pháp]**
"Mục đích thì rõ: train để huấn luyện, test để đánh giá khách quan. Chúng em chia theo tỷ lệ **80% train, 20% test**. Phương pháp là **StratifiedGroupKFold** — vừa *phân tầng theo nhãn* để giữ đúng tỷ lệ nguy cơ ở cả hai tập, vừa *gom nhóm theo mã sinh viên*. **Vì sao** phải gom theo sinh viên: vì một sinh viên có thể học nhiều môn–kỳ; nếu chia theo dòng thì cùng một người sẽ xuất hiện ở *cả train lẫn test*, gây rò rỉ nhóm. Kết quả: tập test khoảng 6.489 dòng tương ứng 6,5 nghìn sinh viên, train khoảng 26.104 dòng."

**[Slide 29 — Kiểm soát rò rỉ: 2 trục]**
"Rò rỉ được kiểm soát theo **hai trục**. *Trục thời gian*: hàm `cut_at_checkpoint` chỉ giữ những sự kiện xảy ra *tại hoặc trước* ngày mốc; ngày mốc được tính bằng công thức *làm tròn của độ dài khóa nhân với phần trăm tiến độ*, cho sáu mốc 10 đến 100%. Có ba quy tắc: loại bài nộp sau mốc, loại click sau mốc, và giữ sinh viên rút môn trước mốc là nguy cơ. *Trục đặc trưng*: mọi bộ học — encoder, scaler, tái lấy mẫu — đều *chỉ fit trên train*. **Vì sao**: để mô phỏng đúng thông tin có được *tại thời điểm dự đoán*, không nhìn vào tương lai. *(chỉ đường cong)* Kết quả là sáu bộ dữ liệu theo mốc, dùng chung một danh sách sinh viên, nhãn cố định 52,8% qua các mốc — chỉ đặc trưng thay đổi theo thời gian."

**[Slide 30 — Trình tự tiền xử lý]**
"Trình tự tiền xử lý là *bắt buộc* và đúng thứ tự: **chia train/test trước**, rồi mới điền khuyết, xử lý ngoại lai, mã hóa và chuẩn hóa, và cuối cùng tái lấy mẫu. Mọi tham số — trung vị để điền, ngưỡng winsorize, trung bình và độ lệch chuẩn của scaler, danh mục của encoder — đều *học từ train* rồi áp lên test. **Vì sao** quan trọng: nếu fit trên toàn bộ dữ liệu *trước khi* chia, thì thông tin của test đã rò rỉ vào train, cho kết quả ảo cao một cách giả tạo. Sau khi chia, tỷ lệ nhãn của train là 0,53 và test là 0,52 — chênh nhau dưới 0,02, đạt yêu cầu phân tầng."

**[Slide 31 — Lưu & kiểm tra lại]**
"Cuối cùng là lưu và kiểm tra lại. Định nghĩa tập test được lưu *cố định* trong file `test_student_ids.csv` và commit vào repo, kèm báo cáo chia tách. Kiểm tra lại cho thấy **0 sinh viên trùng** giữa train và test, không lệch kiểu hay cột, nhãn cân đối. **Vì sao** lưu cố định: vì tập test giữ y hệt qua *cả sáu mốc*, nên sáu điểm hiệu năng mới *so sánh được* với nhau để vẽ đường dự đoán theo thời gian. *(nhấn)* Và bằng chứng mạnh nhất: bộ kiểm thử tự động `test_leakage.py` cho kết quả **16 trên 16 đạt** — khẳng định không có rò rỉ."

**»» Chuyển giao:** "Em xin hết Phần 5. Em mời bạn An tổng kết."

---

# 👤 AN — Kết luận (Slide 32–33) · ~1,5 phút

*(Nhận sân khấu)* "Cảm ơn Khoa. Em là An, em xin tổng kết lại Task 3."

**[Slide 32 — Tóm tắt Task 3]**
"Năm mục của Task 3 đều đã hoàn thành với sản phẩm và số liệu cụ thể. *(lướt bảng)* Một, *xác định dữ liệu*: nhãn nhị phân nguy cơ 52,8%, ba nhóm đặc trưng, đơn vị là sinh viên–môn–kỳ. Hai, *thu thập*: nguồn OULAD cấp phép CC-BY 4.0, bảy bảng, 10,6 triệu click, có xác minh MD5. Ba, *làm sạch*: không trùng, biến đổi log1p và winsorize mà *không xóa dòng nào*, ra bảng master 32.593 nhân 33. Bốn, *chuẩn hóa và biến đổi*: mã hóa đầy đủ, chuẩn hóa, đặc trưng mạnh tới d bằng 2,55, và phương án cho RQ3. Năm, *tách train/test*: 80/20 gom nhóm và phân tầng, sáu mốc thời gian, 16 trên 16 kiểm thử đạt."

**[Slide 33 — Đầu ra & bước tiếp]**
"Về đầu ra: Task 3 cho ra bảng master, *sáu bộ dữ liệu theo mốc thời gian*, một tập test cố định, và một pipeline **tái lập hoàn toàn** — cùng một seed, có manifest MD5, notebook chạy lại từ đầu là ra đúng kết quả. Bước tiếp theo của nhóm: benchmark mô hình tại từng mốc để trả lời RQ1, xử lý mất cân bằng cho RQ3, rồi thêm lớp giải thích SHAP và LIME cùng đo độ ổn định cho RQ2. *(chốt)* Phần trình bày của Nhóm 1 đến đây là hết. Chúng em cảm ơn cô và các bạn đã lắng nghe, và nhóm sẵn sàng nhận câu hỏi ạ."

---

## Phụ lục — Câu hỏi Q&A & người trả lời

| # | Câu hỏi dự kiến | Người trả lời | Ý chính |
|---|---|---|---|
| 1 | Sao gộp Withdrawn vào nguy cơ thay vì bỏ? | Sơn/Bình | Rút môn là tín hiệu thật: trung vị 233 ngày không hoạt động, click giảm 1.425→89. |
| 2 | 52,8% sao gọi mất cân bằng? | Đức | Mất cân bằng *nhẹ* (ratio 1,12); báo trung thực; RQ3 định lượng SMOTE/ADASYN. |
| 3 | Điền điểm thiếu bằng 0 có sai lệch? | Bình | Không — kèm cờ `not_submitted` phân biệt "chưa nộp" với "chưa tới hạn". |
| 4 | Chắc chắn không rò rỉ thời gian thế nào? | Khoa | `cut_at_checkpoint` chỉ giữ sự kiện ≤ mốc; 16/16 kiểm thử đạt. |
| 5 | Sao chia theo `id_student`? | Khoa | Một SV nhiều môn–kỳ; chia theo dòng → rò rỉ nhóm. |
| 6 | `days_since` slide 20 là 2,55 mà slide 22 là 1,56? | Bình | Hai bộ khác nhau: master (2,55) vs dataset_t100 đã cắt click sau mốc (1,56); 5 biến còn lại khớp tuyệt đối. |
| 7 | `days_since` r=0,78 có phải leakage? | Bình | Không — ngưỡng nghi là 0,95; 0,78 hợp lý về giáo dục; hàm cắt thời gian không nhìn tương lai. |
| 8 | Sao dùng Mann–Whitney & Spearman? | Bình | Dữ liệu lệch mạnh (skew 34,7) vi phạm giả định chuẩn của t-test/Pearson. |
| 9 | 19/19 biến có ý nghĩa — biến nào cũng tốt? | Bình | Không — n lớn nên p luôn nhỏ; xếp hạng bằng Cohen's d, nhân khẩu học d ≤ 0,28. |
