DSP391m · Nhóm 1
# Kịch bản thuyết trình — đọc từng từ (bộ slide Beamer **Data Tasks**, 38 trang)

**Đề tài:** Học máy có khả năng giải thích, nhận biết theo thời gian, để phát hiện sớm sinh viên có nguy cơ học tập kém trên bộ dữ liệu OULAD.
**Phần trình bày:** *Data Tasks* — Thu thập, Làm sạch, Biến đổi, Chia tập & Phân tích dữ liệu (Báo cáo 2).

Bám sát đúng bộ slide. Slide **tiếng Anh** — lời nói **tiếng Việt**; vừa nói vừa chỉ vào mục/bảng/biểu đồ tương ứng. Thứ tự tuần tự: mỗi người nói liền một mạch rồi mời người sau (**Khoa** mở đầu rồi quay lại **chốt** ở slide 37–38).

> Bộ slide có **38 trang** đánh số theo chân slide, trong đó **8 trang tự sinh** (1 bìa, 1 Mục lục, 6 trang **Outline** đầu mỗi phần) — những trang này chỉ **lướt qua**, không đọc. Còn lại **30 trang nội dung** là phần đọc.
> Ba slide phân tích sâu — **14–15 (Outliers), 24 (Chống rò rỉ), 32–33 (Hiệu ứng & tương quan)** — không đọc cứng, mà nói theo **HƯỚNG DẪN NÓI**: nêu đủ 5 ý (Vấn đề · Input/Output · Pipeline · Đánh giá · Gap/Chốt) kèm câu mẫu và một đoạn nói liền mạch. Tổng thời lượng ≈ **17–19 phút**.
> Slide **6 (Working at Scale — ClickHouse)** là slide MỚI: cho giám khảo thấy nhóm **thực sự hiểu** dữ liệu 10,6 triệu dòng bằng cách query, không chỉ đọc kết quả. Bản chạy tay là `notebooks/00_data_understanding.ipynb`; giải thích đầy đủ ở `reports/guide/DataTask_Process_Guide.pdf`.

---

## 1. Thứ tự trình bày

Phân lượt theo 6 phần của bài toán dữ liệu:

| Lượt | Người | Phần | Trang (chân slide) |
|---|---|---|---|
| 1 | **Khoa** | Mở đầu + **Dữ liệu cần thiết** + **Làm việc ở quy mô lớn** | 1–7 |
| 2 | **Sơn** | **Phương pháp thu thập** | 8–10 |
| 3 | **Phúc** | **Làm sạch dữ liệu** *(sâu: 14–15)* | 11–15 |
| 4 | **Bình** | **Biến đổi & Chuẩn hóa** | 16–20 |
| 5 | **Đức** | **Chia tập & Chống rò rỉ** *(sâu: 24)* | 21–25 |
| 6 | **An** | **Phân tích khám phá — EDA** *(sâu: 32–33)* | 26–36 |
| — | round-robin | **Tổng kết** (slide 37) — mỗi người đọc 1 dòng của phần mình | 37 |
| chốt | **Khoa** | **Cảm ơn** (slide 38) | 38 |

Các trang **Outline** (3, 8, 11, 16, 21, 26) và **Mục lục** (2): không đọc — chỉ lướt, dùng làm nhịp chuyển phần.

---

## 2. Kịch bản (tuần tự theo lượt nói)

### Khoa — Mở đầu, Dữ liệu cần thiết & Làm việc ở quy mô lớn
*Nói slide 1, 2, (3 lướt), 4, 5, 6, 7 — sau đó mời Sơn.*

**Slide 1 — Trang bìa & giới thiệu**
Em chào thầy/cô và các bạn. Chúng em là Nhóm 1, hôm nay xin trình bày phần **Data Tasks** — tức là toàn bộ công việc với dữ liệu — cho đồ án DSP391m, đề tài “Học máy có khả năng giải thích, nhận biết theo thời gian, để phát hiện sớm sinh viên có nguy cơ trên bộ dữ liệu OULAD”. Em là Khoa, em xin mở đầu bằng phần dữ liệu mà bài toán cần. Sau đó các bạn trong nhóm sẽ lần lượt trình bày cách thu thập, làm sạch, biến đổi, chia tập, và cuối cùng là những gì dữ liệu cho ta thấy qua phân tích khám phá.

**Slide 2 — Mục lục**
Phần trình bày của nhóm em gồm sáu mục, đúng theo yêu cầu của bài toán dữ liệu: một, dữ liệu cần thiết; hai, phương pháp thu thập; ba, chiến lược làm sạch; bốn, biến đổi và chuẩn hóa; năm, chia tập huấn luyện/kiểm tra và chống rò rỉ; và sáu, phân tích khám phá dữ liệu. Mỗi thành viên phụ trách một mục. Trước hết, em xin nói về dữ liệu mà nghiên cứu cần.

**Slide 4 — Dữ liệu cần thiết → nguồn trong OULAD**
*(chỉ vào bảng 3 cột: Requirement · Why required · OULAD source)*
Mục tiêu dự đoán của nhóm em là một nhãn nhị phân “nguy cơ”, và để dựng được nhãn đó cùng các đặc trưng quanh nó, nhóm em cần năm thứ. **Thứ nhất**, chính cái nhãn — lấy từ cột `final_result` trong bảng studentInfo. **Thứ hai**, dữ liệu tương tác có mốc thời gian — đó là clickstream `studentVle`, khoảng **10,6 triệu** dòng. **Thứ ba**, kết quả học tập từ `studentAssessment`. **Thứ tư**, bối cảnh nhân khẩu từ studentInfo và studentRegistration. Và **thứ năm**, dòng thời gian khóa học từ bảng courses — nó cho phép quy một ngày lịch về phần trăm tiến độ khóa học. Mỗi dòng dữ liệu cuối cùng là một sinh viên trong một lượt mở môn — cho ra **32.593 dòng, 28.785 sinh viên, trên 22 lượt mở môn**.

**Slide 5 — Cấu trúc OULAD (7 bảng quan hệ)**
*(chỉ vào cột Rows và cột “Time?”)*
OULAD gồm bảy bảng quan hệ. studentInfo chứa nhân khẩu và kết quả cuối. studentRegistration có ngày đăng ký và ngày rút môn. studentVle là bảng lớn nhất — hơn **mười triệu rưỡi** dòng click theo ngày. studentAssessment có ngày nộp và điểm; assessments và vle là bảng tra cứu; còn courses cho độ dài môn học tính theo ngày. Điểm mấu chốt là **hai cột ngày** — `studentVle.date` và `studentAssessment.date_submitted` — vì chính chúng cho phép mọi lát cắt theo thời gian sau này.

**Slide 6 — Làm việc ở quy mô lớn: hiểu 10,6 triệu dòng bằng ClickHouse** *(slide MỚI — đây là phần “show cách làm”)*
*(chỉ: khối “The problem” bên trái, bảng tốc độ CSV→Parquet bên phải, khối “Profiled in one pass”)*
Trước khi đi tiếp, em xin dừng một nhịp ở chính bảng lớn nhất — clickstream `studentVle`, **mười triệu sáu trăm năm mươi lăm nghìn** dòng, **bốn trăm ba mươi ba megabyte**. Đây là chỗ nhóm em muốn cho thầy cô thấy **cách chúng em thật sự hiểu dữ liệu**, chứ không chỉ đọc kết quả. Một file mười triệu dòng thì Excel mở không nổi, còn nạp cả file vào pandas mỗi lần hỏi một câu thì tốn vài GB RAM. Nên nhóm em dùng **clickhouse-local** — một engine SQL gọn nhẹ: để dữ liệu nằm yên trên đĩa và **đẩy câu hỏi xuống**, chứ không kéo dữ liệu lên. Ngay bước đầu đã có một bài học hay: nếu để mặc định, mọi cột bị đọc thành **chuỗi**, và `max` của cột ngày trả về **“99”** — vì nó so sánh theo chữ cái; phải **khai báo kiểu** thì mới ra đúng khoảng ngày từ **âm 25 đến 269**. Sau đó nhóm em chuyển CSV sang **Parquet** — như bảng bên phải: từ 433 MB còn **22,9 MB**, và truy vấn nhanh hơn khoảng **26 lần**, dưới một giây cho cả mười triệu dòng. Chỉ trong một lượt quét, nhóm em đã biết: chỉ **26 nghìn** sinh viên thực sự có click trên tổng 28 nghìn — tức nhiều em gần như không hoạt động; và phân phối click **lệch phải rất mạnh**, chính là lý do cho phép biến đổi `log1p` mà bạn Phúc sẽ nói ngay sau. Điểm cốt lõi em muốn nhấn: **mọi con số trên các slide sau đều tái lập được** bằng một notebook truy vấn. Trên nền dữ liệu đã hiểu rõ đó, em xin nói về biến mục tiêu.

**Slide 7 — Biến mục tiêu & cân bằng lớp**
*(chỉ vào bảng đếm 4 lớp và biểu đồ thanh)*
Đây là cách nhóm em định nghĩa nhãn. `final_result` có bốn giá trị: Pass và Distinction là **không nguy cơ**; Fail và Withdrawn là **nguy cơ**. Tỉ lệ nguy cơ là **52,8%** — tỉ số mất cân bằng chỉ 1,12, nên mức lệch là **nhẹ**. Xin lưu ý: **Withdrawn** — hơn mười nghìn sinh viên — là lớp đơn lớn nhất; điều này sẽ rất quan trọng ở phần phân tích. Vì lớp nguy cơ là lớp không được phép bỏ sót, nhóm em chọn chỉ số trọng tâm là **PR-AUC** và **recall** trên lớp nguy cơ, chứ không phải accuracy. Tiếp theo, em xin mời bạn Sơn nói về cách thu thập dữ liệu.

---

### Sơn — Phương pháp thu thập
*Nói slide (8 lướt), 9, 10 — sau đó mời Phúc.*

**Slide 9 — Chọn nguồn dữ liệu**
*(chỉ vào bảng so sánh: Internal DB · API · Scraping · Public)*
Em cảm ơn Khoa. Em là Sơn. Có bốn cách thực tế để lấy dữ liệu giáo dục: cơ sở dữ liệu nội bộ của trường, API của nền tảng, cào web, hoặc dùng **bộ dữ liệu công khai thứ cấp**. Nhóm em so sánh trên các tiêu chí quan trọng với một đồ án cần tái lập. Dữ liệu nội bộ cho nhiều quyền kiểm soát nhất nhưng cần thỏa thuận đạo đức và không chia sẻ được. API và cào web đều dính dữ liệu cá nhân, dễ hỏng theo thời gian, và khó tái lập. Dữ liệu công khai thắng ở chỗ sẵn có ngay, đã ẩn danh, tái lập hoàn toàn, và — quan trọng nhất — **so sánh được với nghiên cứu trước**. Nên nhóm em chọn dữ liệu công khai thứ cấp: đánh đổi quyền kiểm soát thiết kế thu thập để lấy tính tái lập và khả năng so sánh trực tiếp với hai bài nền — Adnan 2021 và Tomasevic 2020.

**Slide 10 — Vì sao chọn OULAD + Giấy phép & Đạo đức**
*(chỉ vào hai khối: Fit to the project · License & ethics)*
Cụ thể, bộ dữ liệu đó là OULAD. Nó đáp ứng mọi yêu cầu: tải công khai nên ai cũng tái lập được; có đủ ba nhóm đặc trưng — nhân khẩu, tương tác VLE, và đánh giá; có sẵn nhãn `final_result`; là **cùng bộ dữ liệu** mà hai bài nền dùng, nên số liệu của nhóm em so sánh được trực tiếp; và là **ảnh chụp tĩnh**, ai tải cũng ra file y hệt. Về đạo đức: phát hành theo **CC-BY 4.0**, chỉ cần trích dẫn. Đã ẩn danh tại nguồn — không định danh, vị trí ở mức vùng, tuổi và mức thiệt thòi đều chia khoảng. Nhóm em không tái định danh, không liên kết dữ liệu ngoài, và giữ file CSV gốc ở chế độ chỉ-đọc kèm kiểm tra md5. Nhóm em trích dẫn Kuzilek và cộng sự, 2017. Tiếp theo, em xin mời bạn Phúc nói về làm sạch dữ liệu.

---

### Phúc — Làm sạch dữ liệu
*Nói slide (11 lướt), 12, 13 — rồi **phân tích sâu 14–15** — sau đó mời Bình.*

**Slide 12 — Hồ sơ chất lượng dữ liệu**
*(chỉ vào cột #Missing và % )*
Em cảm ơn Sơn. Em là Phúc. Trước khi làm sạch, nhóm em lập hồ sơ xem khuyết tật nằm ở đâu. Chỉ vài cột có giá trị thiếu. `date_unregistration` thiếu 69% — nhưng đó là thiếu **cấu trúc**: cột này chỉ tồn tại với sinh viên đã rút môn, nên nhóm em bỏ hẳn, nó không phải đặc trưng. `imd_band` — mức thiệt thòi — thiếu 3,4%. `date_registration` chỉ thiếu 0,14%, đúng 45 dòng. Ba cột điểm-đến-thời-điểm thiếu **theo thiết kế** khi chưa nộp gì. Toàn bộ 29 cột còn lại sạch hoàn toàn. **Không có dòng trùng** trên khóa tổng hợp, và sau khi điền khuyết, **không còn NaN** ở bất kỳ cột đặc trưng nào, cả train lẫn test.

**Slide 13 — Giá trị thiếu: phương pháp & lý do**
*(chỉ vào cột Strategy)*
Đây là cách xử lý từng cột và vì sao. Với `imd_band`, nhóm em thêm một hạng mục **“Unknown”** thay vì đoán bừa — giữ nguyên thang thứ bậc và không bịa ra một mức thiệt thòi cho ai cả. Với các cột điểm-đến-thời-điểm, nhóm em điền 0 **nhưng kèm một cờ `not_submitted`** — vì điểm thiếu tự nó là tín hiệu “chưa nộp gì”, và cái cờ ngăn mô hình hiểu nhầm số 0 đó là một điểm thấp thật. Với `date_registration` — 45 dòng, thiếu hoàn toàn ngẫu nhiên — nhóm em dùng **median của tập train**. Còn `date_unregistration` thì bỏ. Nguyên tắc vàng xuyên suốt: mọi thống kê đều học **chỉ trên tập huấn luyện** rồi áp lên test — để tránh rò rỉ.

> #### ★ Phân tích sâu — Slide 14–15: “Vì sao đuôi lệch phải làm hỏng mô hình & cách xử lý outliers”
> *Phúc tự diễn đạt, nhưng nêu ĐỦ 5 ý sau (vừa nói vừa chỉ: biểu đồ skewness ở slide 14, bảng phương pháp ở slide 15).*
>
> 1. **Vấn đề** — clickstream lệch phải rất nặng.
>    *Câu mẫu:* “Cột click lệch phải cực mạnh: `clicks_resource` có skewness **34,7**, kurtosis hơn hai nghìn, max **5.147** click so với median chỉ **19**; `max_clicks_single_day` đạt **6.988** so với median 74.”
> 2. **Input → Output** — vào gì, ra gì.
>    *Câu mẫu:* “Đầu vào là cột đếm thô có đuôi dài; đầu ra là cột đã nén đuôi nhưng **giữ nguyên thứ hạng**, và **không xóa dòng nào**.”
> 3. **Pipeline / cách làm** — hai chiến lược + lưu ý.
>    *Câu mẫu:* “`log1p` cho mọi biến đếm click (ánh xạ 0→0, hợp với nhiều sinh viên không hoạt động); **winsorise 1%** cho biến có chặn như điểm, tín chỉ, số lần thi lại; biến nào không có outlier thật thì để nguyên; **ngưỡng học theo từng fold train**.”
> 4. **Đánh giá** — căn cứ định lượng.
>    *Câu mẫu:* “Đánh giá bằng skew/kurtosis trước–sau và quy tắc IQR; bằng chứng là biên trên IQR của `mean_score` còn cao hơn cả max 100 ⇒ cột đó **không** có outlier thật.”
> 5. **Chốt** — vì sao quan trọng.
>    *Câu mẫu:* “Giữ toàn bộ dữ liệu, chỉ **biến đổi** chứ không cắt — nếu để nguyên, vài điểm cực đoan sẽ lấn át gradient và khoảng cách, làm phồng phương sai và lệch mô hình.”
>
> **Mẫu nói liền mạch (≈ 1 phút):**
> *Ở đây em xin mổ xẻ kỹ vấn đề outliers. Như biểu đồ bên trái, dữ liệu click của nhóm em lệch phải rất nặng — một biến cân đối có skewness gần 0, còn ở đây `clicks_resource` lên tới 34,7, kurtosis hơn hai nghìn, có sinh viên click tới 5.147 lần trong khi median chỉ 19. Nếu để nguyên, vài giá trị khổng lồ này sẽ lấn át gradient khi học và lấn át khoảng cách khi tính tương đồng, khiến mô hình lệch. Nhưng nhóm em **không xóa dòng nào** — xóa là mất dữ liệu thật. Thay vào đó, như bảng bên phải: với mọi biến đếm click nhóm em dùng `log1p` để nén đuôi, và nó ánh xạ 0 về 0 nên hợp với rất nhiều sinh viên không hoạt động; với các biến có chặn như điểm hay tín chỉ thì winsorise 1% — cắt 1% cực trị nhưng giữ thứ hạng, an toàn hơn lấy log của một điểm số; còn biến nào không có outlier thật, ví dụ `mean_score` có biên IQR còn vượt cả mức tối đa, thì để nguyên. Mọi ngưỡng đều học trên tập train. Tóm lại: nhóm em chỉ biến đổi, giữ trọn dữ liệu, và chặn không cho vài điểm cực đoan thao túng mô hình.* Tiếp theo, em xin mời bạn Bình.

---

### Bình — Biến đổi & Chuẩn hóa
*Nói slide (16 lướt), 17, 18, 19, 20 — sau đó mời Đức.*

**Slide 17 — Phân loại biến: 28 đặc trưng, 5 kiểu**
*(chỉ vào cột Type và cột Encoder/scaler)*
Em cảm ơn Phúc. Em là Bình, phụ trách phần biến đổi. Sau làm sạch, nhóm em có 28 đặc trưng, chia thành **năm kiểu** — vì kiểu biến quyết định cách mã hóa. **19 biến số** — click, điểm, tín chỉ — dùng StandardScaler. **3 biến thứ bậc** — học vấn, mức thiệt thòi, nhóm tuổi — dùng OrdinalEncoder giữ đúng thứ tự. **3 biến danh nghĩa** — vùng, mã môn, mã kỳ — dùng one-hot. **2 biến nhị phân** — giới tính và khuyết tật. Và **1 biến chỉ báo** — cờ `not_submitted` — đi thẳng qua. Sai kiểu là trả giá: coi thứ bậc thành danh nghĩa thì **mất thứ tự**; coi danh nghĩa thành thứ bậc thì **bịa ra một thứ tự sai**.

**Slide 18 — Mã hóa: phương pháp & lý do**
*(chỉ vào cột cấu hình)*
Chi tiết hơn về bộ mã hóa. OrdinalEncoder dùng thứ tự tường minh — ví dụ “No Formal” nhỏ hơn … cho đến “Post Graduate” — và ánh xạ giá trị lạ về −1; giữ thứ hạng mà không phình chiều. OneHotEncoder bỏ qua hạng mục lạ và **cố ý giữ mọi cột** — nhóm em đặt `drop=None` có chủ đích. BinaryEncoder dùng ánh xạ cố định, tất định, không cần học. Vì sao giữ mọi cột one-hot thay vì bỏ một cột tham chiếu? Vì đây là đồ án **giải thích được** — bỏ một hạng mục tham chiếu sẽ **giấu** hạng mục đó khỏi giải thích SHAP và LIME. Nên lựa chọn mã hóa được dẫn dắt bởi tính giải thích, chứ không chỉ bởi mô hình.

**Slide 19 — Chuẩn hóa: Trước → Sau**
*(chỉ vào hai cột Before · After)*
Slide này cho thấy toàn bộ biến đổi từ đầu đến cuối. Nhãn: từ tên lớp thành nhị phân 1/0. Biến hạng mục: từ chữ thành số. Biến số: từ giá trị thô, lệch, trải từ 0 đến hai mươi tư nghìn, thành đã log-hoặc-winsorise rồi z-score — trung bình 0, độ lệch chuẩn 1. Ma trận lớn lên từ 28 cột lệch thang thành **49 cột đặc, không NaN**, tên chuẩn hóa snake_case kèm tiền tố bộ biến đổi. Chi tiết then chốt: scaler **fit chỉ trên train** — trung bình lấy từ tập train — còn tập test chỉ được `.transform()`, **không bao giờ** `.fit_transform()`.

**Slide 20 — Trình tự tiền xử lý: chỉ fit trên train**
*(chỉ vào sơ đồ 5 bước và khối “Anti-leakage reasons”)*
Và đây là trình tự chạy — bản thân nó cũng là một thiết kế chống rò rỉ. Đầu tiên **chia tập** — theo nhóm và phân tầng, test cố định 20%. Rồi xử lý thiếu, rồi outliers, rồi fit ColumnTransformer — tất cả trên train. Sau đó transform cả train và test. Và chỉ ở **bước cuối** mới **tái lấy mẫu SMOTE/ADASYN — chỉ trên train**, để tập test luôn giữ tỉ lệ lớp thật. Chia trước nghĩa là không thống kê nào chảy ngược từ test về train, và điều này phản chiếu đúng cách lát cắt thời gian hoạt động. Tiếp theo, em xin mời bạn Đức nói về phần chia tập.

---

### Đức — Chia tập & Chống rò rỉ
*Nói slide (21 lướt), 22, 23 — rồi **phân tích sâu 24** — rồi 25 — sau đó mời An.*

**Slide 22 — Vì sao việc chia tập cần thận trọng**
*(chỉ vào ba khối: Grouped · Imbalanced · Time-aware, rồi bảng số bên dưới)*
Em cảm ơn Bình. Em là Đức. Việc chia tập của nhóm em phải tôn trọng đồng thời ba tính chất của dữ liệu. **Một — dữ liệu theo nhóm:** một sinh viên có thể xuất hiện ở nhiều lượt mở môn, nên phải chia theo `id_student`, nếu không cùng một sinh viên rơi vào cả train lẫn test — đó là rò rỉ theo nhóm. **Hai — mất cân bằng** khoảng 52,8% nguy cơ, nên phải **phân tầng** để tỉ lệ test không trôi. **Ba — theo thời gian:** sáu mốc dùng chung một trục so sánh, nên tập test phải **giống hệt** ở mọi mốc. Kết quả, kiểm trên cả 32.593 dòng: **26.104 dòng train, 6.489 dòng test, 5.756 sinh viên test**, tỉ lệ nguy cơ 0,53 và 0,52, và **0 sinh viên trùng** — giống hệt nhau ở cả sáu mốc.

**Slide 23 — So sánh các chiến lược chia tập**
*(chỉ vào cột Pros · Cons)*
Nhóm em so sánh bốn chiến lược. Hold-out đơn giản nhưng phương sai cao — phụ thuộc một lần chia. k-fold dùng hết dữ liệu, giảm phương sai, nhưng vẫn phụ thuộc seed. Repeated k-fold cho trung bình ± độ lệch chuẩn ổn định, không phụ thuộc seed, đổi lại tốn hơn. Nested CV không thiên lệch khi có tinh chỉnh nhưng rất đắt. Nhóm em chọn **hold-out 20% cố định + 5-fold lặp 5 seed** — tức `StratifiedGroupKFold` — vừa ổn định vừa giữ test so sánh được qua các mốc. Báo cáo trung bình ± độ lệch chuẩn của PR-AUC và recall trên 25 lần fit.

> #### ★ Phân tích sâu — Slide 24: “Chống rò rỉ theo thời gian — và nó được kiểm thử tự động”
> *Đức tự diễn đạt, nêu ĐỦ 5 ý sau (chỉ vào ba luật thời gian và khối exampleblock “19/19 tests pass”).*
>
> 1. **Vấn đề** — thiết kế theo thời gian rất dễ rò rỉ tương lai.
>    *Câu mẫu:* “Khi cắt khóa học theo mốc, rủi ro lớn nhất là để thông tin **sau** thời điểm dự đoán lọt vào dữ liệu huấn luyện.”
> 2. **Input → Output** — vào gì, ra gì.
>    *Câu mẫu:* “Đầu vào là dữ liệu tại mốc *t* với cutoff = `round(độ_dài_môn × t/100)`; đầu ra là tập **chỉ chứa sự kiện ≤ cutoff**.”
> 3. **Pipeline / cách làm** — ba luật + nguyên tắc fit-on-train.
>    *Câu mẫu:* “Một, bỏ bài nộp sau cutoff. Hai, bỏ tương tác VLE sau cutoff. Ba, sinh viên rút **trước** *t* vẫn giữ và gán nhãn nguy cơ — hoạt động thấp là tín hiệu, không phải rò rỉ. Cộng thêm: mọi learner — imputer, encoder, scaler, resampler — đều **fit trên train**.”
> 4. **Đánh giá** — không chỉ tuyên bố mà kiểm chứng.
>    *Câu mẫu:* “`tests/test_leakage.py` chạy tự động: **19/19 pass** — không bản ghi nào vượt cutoff, số lượng **không giảm** theo *t*, mốc 100% giữ tất cả, 0 overlap, tỉ lệ lớp được bảo toàn, và **median điền khuyết lẫn ngưỡng winsorize chỉ học trên train**.”
> 5. **Chốt** — ý nghĩa.
>    *Câu mẫu:* “Chống rò rỉ ở đây không phải lời hứa suông — nó là một thuộc tính **được kiểm thử**, nên kết quả ở các mốc sớm là đáng tin.”
>
> **Mẫu nói liền mạch (≈ 1 phút):**
> *Ở đây em xin nói kỹ về chống rò rỉ, vì đây là rủi ro lớn nhất của một thiết kế theo thời gian. Ý tưởng đơn giản: tại mỗi mốc *t*, ta đặt một mốc cắt bằng *t* phần trăm độ dài môn, và bất cứ thứ gì xảy ra sau mốc đó đều không được phép biết. Cụ thể nhóm em áp ba luật: bỏ mọi bài nộp sau cutoff; bỏ mọi tương tác VLE sau cutoff; và với sinh viên đã rút trước *t* thì vẫn giữ lại và gán nhãn nguy cơ — vì hoạt động gần như bằng không của họ là tín hiệu thật, không phải rò rỉ. Bên cạnh đó, mọi bộ học — điền khuyết, mã hóa, scaler, tái lấy mẫu — đều chỉ fit trên train. Và nhóm em không dừng ở việc tin: bộ kiểm thử `test_leakage.py` tự động kiểm tra và **19 trên 19 test đều pass** — không bản ghi nào vượt mốc cắt, số sự kiện chỉ tăng chứ không giảm theo *t*, mốc 100% giữ trọn dữ liệu, không sinh viên nào trùng, tỉ lệ lớp được giữ nguyên, và cả median điền khuyết lẫn ngưỡng winsorize đều chỉ học trên train rồi áp cho test. Nhờ vậy, các con số ở những mốc sớm — phần khó nhất — là đáng tin.*

**Slide 25 — Mốc thời gian: tín hiệu lớn dần theo thời gian**
*(chỉ vào bảng “Earliest checkpoint” bên trái và biểu đồ figure thật bên phải)*
Cuối cùng, dữ liệu sớm có thực sự mang tín hiệu không? Nhóm em đo sức phân biệt của từng đặc trưng — Cohen’s *d* — tại sáu mốc: 10, 20, 40, 60, 80 và 100 phần trăm. Đường cong bên phải, lấy từ chính code của nhóm, cho thấy sức phân biệt tăng dần; nhưng bảng bên trái mới là điểm nhấn: `n_days_active` đã đạt hiệu ứng lớn, *d* bằng 0,8, ngay từ mốc **10%** — cùng với số ngày bặt vô âm tín (`days_since_last_activity`) cũng đạt mốc đó ở **10%**; nhóm điểm ở **20%**. Nói cách khác, tín hiệu hữu ích tồn tại **rất sớm** — và đó chính là cơ sở cho can thiệp sớm. Tiếp theo, em xin mời bạn An nói về phân tích khám phá.

---

### An — Phân tích khám phá (EDA)
*Nói slide (26 lướt), 27, 28, 29, 30, 31 — rồi **phân tích sâu 32–33** — rồi 34, 35, 36 — sau đó mời cả nhóm vào phần tổng kết.*

**Slide 27 — Lộ trình EDA**
*(chỉ vào sơ đồ 5 bước)*
Em cảm ơn Đức. Em là An. EDA của nhóm em đi theo năm bước — thống kê mô tả, kiểu biến, dữ liệu thiếu, outliers, và tương quan — và làm ở ba mức: **đơn biến**, từng biến một; **song biến**, từng biến với nhãn; và **đa biến**, các biến với nhau. Mục tiêu là đi từ dữ liệu thô, đến quy luật, đến kết luận dẫn đường cho mô hình.

**Slide 28 — Thống kê mô tả (đơn biến, biến số)**
*(chỉ vào cột Mean, Median, Skew)*
Bắt đầu bằng các con số, quy luật rõ nhất là **độ lệch**. Với clickstream, trung bình cao hơn hẳn median — `total_clicks` trung bình 1.215 nhưng median chỉ 602 — đó là dấu vân tay của lệch phải, xác nhận bằng skewness 3,0, lên tới 10,6 ở `max_clicks_single_day`. Với `mean_score` thì ngược lại: median 70 cao hơn trung bình 57 — lệch trái. Và chỗ nào độ lệch chuẩn xấp xỉ hoặc lớn hơn trung bình thì độ phân tán rất cao. Chính bảng này là lý do cho mọi quyết định làm sạch vừa nghe.

**Slide 29 — Đơn biến: phân bố (Histogram + KDE)**
*(chỉ vào hình — figure thật)*
Hình này lấy thẳng từ code của nhóm em. Mỗi ô là phân bố của một đặc trưng. Nhìn là thấy: các biến click dồn về gần 0 với đuôi dài sang phải; điểm bị chặn trong khoảng 0 đến 100; còn `days_idle` thì **lưỡng đỉnh** — hai bướu — đây là hình dạng quan trọng nhất trong dữ liệu.

**Slide 30 — Đơn biến: box plot**
*(chỉ vào ba hộp)*
Box plot củng cố điểm về độ trải. `mean_score` có hộp hẹp, median bị đẩy lên sát tứ phân vị trên — lệch trái. `n_days_active` rộng và lệch phải. Nhưng hãy nhìn `days_idle`: khoảng tứ phân vị chạy từ 11 đến 207 — trải khổng lồ — vì nó lưỡng đỉnh: sinh viên tích cực nằm gần 0 ngày nghỉ, còn sinh viên rút môn nằm xa tít bên phải. Thời gian-nhàn-rỗi lưỡng đỉnh là cấu trúc cảnh báo sớm rõ nhất ta có.

**Slide 31 — Đơn biến: tần suất hạng mục (Học vấn)**
*(chỉ vào biểu đồ thanh)*
Về phía biến hạng mục, đây là học vấn cao nhất. **83%** sinh viên có trình độ A-Level trở xuống. Post-Graduate và No-Formal mỗi loại dưới 1,1% — rất hiếm. Chính sự hiếm này là lý do nhóm em one-hot với `handle_unknown=ignore` thay vì bỏ các mức đó — không muốn mất một hạng mục chỉ vì nó nhỏ. Vậy hình dạng của biến hạng mục trực tiếp dẫn dắt lựa chọn mã hóa.

> #### ★ Phân tích sâu — Slide 32–33: “Yếu tố nào thực sự phân biệt nguy cơ?”
> *An tự diễn đạt, nêu ĐỦ 5 ý sau (chỉ: biểu đồ Cohen’s d ở slide 32, heatmap tương quan ở slide 33).*
>
> 1. **Vấn đề** — đặc trưng nào tách nhóm nguy cơ, và có dư thừa/rò rỉ không.
>    *Câu mẫu:* “Ta cần biết biến nào phân biệt mạnh nhất giữa nguy cơ và không nguy cơ, đồng thời kiểm xem có cặp biến nào trùng lặp đến mức gây rò rỉ.”
> 2. **Input → Output** — vào gì, ra gì.
>    *Câu mẫu:* “Đầu vào là đặc trưng + nhãn; đầu ra là **effect size Cohen’s *d*** cho từng biến số và **ma trận tương quan** Pearson giữa các biến.”
> 3. **Pipeline / cách làm** — đo và hiệu chỉnh.
>    *Câu mẫu:* “Tính Cohen’s *d* cho từng biến, kiểm định ý nghĩa có **hiệu chỉnh đa kiểm định** (q < 0,05); và tính |r| để soi đa cộng tuyến.”
> 4. **Đánh giá / đọc số** — ý nghĩa con số.
>    *Câu mẫu:* “`days_since_last_activity` *d* = **2,55** (14 ngày so với 171 ngày); **cả 19** biến đều có ý nghĩa; cặp tương quan mạnh nhất 0,84 và −0,83, nhưng **không cặp nào ≥ 0,95** ⇒ không nghi rò rỉ.”
> 5. **Chốt** — kết luận cho mô hình.
>    *Câu mẫu:* “**Hành vi áp đảo nhân khẩu** — *d* tới 2,5 so với Cramér’s V ≤ 0,15 — nên ưu tiên đặc trưng hành vi, và chỉ đánh dấu hai cặp cộng tuyến để đọc SHAP cho cẩn thận.”
>
> **Mẫu nói liền mạch (≈ 1 phút):**
> *Ở đây em xin đi sâu vào câu hỏi: yếu tố nào thực sự phân biệt sinh viên nguy cơ? Như biểu đồ bên trái, nhóm em đo effect size Cohen’s d cho từng biến số — khoảng cách giữa hai nhóm tính theo độ lệch chuẩn. Các khác biệt rất lớn: số ngày kể từ lần hoạt động cuối trung bình 14 ngày ở nhóm không nguy cơ so với 171 ngày ở nhóm nguy cơ, cho d tới 2,55; nhóm nguy cơ nộp 2,3 bài so với 8,6 bài, điểm có trọng số 15 so với 85. Cả mười chín biến số đều có ý nghĩa thống kê sau hiệu chỉnh. Sang slide bên phải là ma trận tương quan, cũng từ code của nhóm: nó vừa xác nhận điều trên — days_idle tương quan +0,78 với nhãn — vừa kiểm tra dư thừa. Có hai cặp cộng tuyến trên 0,8, là số-ngày-hoạt-động với tổng-click 0,84 và days_idle với số-bài −0,83, nhưng không cặp nào chạm 0,95, nên không có nghi vấn rò rỉ; nhóm em chỉ đánh dấu để khi đọc SHAP thì quy công cho đúng. Kết luận quan trọng nhất: hành vi áp đảo nhân khẩu — d tới 2,5 so với Cramér’s V chỉ 0,15 — tức là cái sinh viên LÀM quan trọng hơn nhiều việc họ LÀ AI.*

**Slide 34 — Song biến: yếu tố nhân khẩu (Cramér’s V)**
*(chỉ vào cột Cramér’s V và p)*
Để công bằng, nhóm em cũng kiểm nhân khẩu bằng Cramér’s V. Mọi yếu tố đều có ý nghĩa thống kê — với cỡ mẫu này thì gần như cái gì cũng vậy — nhưng liên hệ đều **yếu**: học vấn và mức thiệt thòi mạnh nhất cũng chỉ khoảng 0,15, còn giới tính gần như không đáng kể, 0,02. So với effect size hành vi tới 2,5 vừa thấy. Vậy nhân khẩu quan trọng kém xa hành vi — và điều đó cho biết nên canh **công bằng** ở đâu: ở mức thiệt thòi và học vấn, không phải giới tính.

**Slide 35 — Quy luật theo thời gian: tín hiệu “Withdrawn”**
*(chỉ vào biểu đồ cột và bảng median)*
Slide này là một lưu ý trung thực. Nhìn median số ngày nhàn rỗi theo kết quả: nhóm không nguy cơ 11 ngày, nhóm trượt 116 ngày, nhóm rút môn **233** ngày — gần như không click. Vì sinh viên rút môn gần như bất hoạt, họ trở nên **dễ tách** một cách tầm thường ở các mốc **muộn** — nên recall và PR-AUC có thể trông cao một cách lạc quan vào cuối khóa. Đó là hạn chế đã biết của lựa chọn gán nhãn, và chính vì vậy phép thử thật sự của mô hình là ở các mốc **sớm**, không phải mốc muộn.

**Slide 36 — EDA: các phát hiện chính**
*(đọc lướt các gạch đầu dòng)*
Tóm tắt phân tích: phân bố lệch phải mạnh, tới 34,7, dẫn tới quyết định `log1p`; `days_idle` lưỡng đỉnh — chữ ký của sự mất gắn kết; tương tác và kết quả phân tách nhóm nguy cơ rất mạnh, Cohen’s *d* tới 2,55, cả 19 biến đều có ý nghĩa; liên hệ nhân khẩu yếu, V ≤ 0,15; có hai cặp cộng tuyến nhưng không cặp nào trên 0,95 nên không rò rỉ; và giả thuyết cho mô hình là **mới ngừng hoạt động gần đây cộng với nộp ít bài là dấu hiệu nguy cơ sớm và đáng tin nhất.** Tiếp theo, mời cả nhóm vào phần tổng kết.

---

### Tổng kết & Lời kết

**Slide 37 — Tổng kết (round-robin, mỗi người một dòng)**
- **Khoa:** *“01 — Dữ liệu cần thiết: bảy bảng OULAD, hạt dữ liệu (sinh viên, môn, kỳ), 32.593 dòng, nguy cơ 52,8%; clickstream 10,6 triệu dòng hiểu được nhờ ClickHouse.”*
- **Sơn:** *“02 — Thu thập: dữ liệu thứ cấp công khai CC-BY 4.0, đã ẩn danh, cùng bộ với các bài nền.”*
- **Phúc:** *“03 — Làm sạch: 0 trùng lặp, xử lý thiếu theo cơ chế, skew tới 34,7 trị bằng log1p/winsorise, không xóa dòng nào.”*
- **Bình:** *“04 — Biến đổi: 28 đặc trưng, 5 kiểu, thành ma trận 49 cột, fit chỉ trên train.”*
- **Đức:** *“05 — Chia tập & rò rỉ: hold-out 20% + CV 5×5, lát cắt theo thời gian, 19/19 test rò rỉ pass.”*
- **An:** *“06 — Phân tích: hành vi áp đảo — days_idle *d* = 2,55 — nhân khẩu yếu, và lớp Withdrawn lý giải sự lạc quan ở mốc muộn.”*

**Slide 38 — Cảm ơn**
- **Khoa:** *“Đó là toàn bộ phần Data Tasks của nhóm em. Nhóm em xin chân thành cảm ơn thầy/cô và các bạn đã lắng nghe, và rất sẵn lòng trả lời câu hỏi.”*

---

## 3. Mẹo trình bày

- Tới **từ khóa quan trọng** — “theo thời gian”, “chỉ fit trên train”, “không xóa dòng nào”, “19 trên 19”, “hành vi áp đảo nhân khẩu”, “đẩy câu hỏi xuống dữ liệu” — ngắt nhẹ một nhịp; đây là những chỗ giám khảo chú ý.
- Tới **bảng hoặc biểu đồ** thì chỉ tay và đọc tên cột hoặc trục, **không** đọc hết từng ô.
- Slide **6 (ClickHouse)** là điểm gây ấn tượng “nhóm thật sự hiểu data”: nhấn vào ba ý — *không mở nổi bằng Excel → đẩy SQL xuống engine*, *bẫy kiểu dữ liệu (max = “99”)*, và *Parquet nhanh ~26×*. Nếu giám khảo hỏi sâu, dẫn sang `notebooks/00_data_understanding.ipynb` và `reports/guide/DataTask_Process_Guide.pdf`.
- Ba slide phân tích sâu (**14–15, 24, 32–33**): cứ nói theo **5 ý** trong guide, không cần thuộc lòng — miễn nêu đủ Vấn đề · Input/Output · Pipeline · Đánh giá · Gap/Chốt.
- **Con số tuyệt đối không được nói sai** (giám khảo dò): **32.593** dòng · **52,8%** nguy cơ · **0** sinh viên trùng · **19/19** test rò rỉ · Cohen’s *d* tới **2,55** · Cramér’s V ≤ **0,15** · ma trận **49** cột · clickstream **10,6 triệu** dòng · Parquet nhanh **~26×**.
- **Giữ thời lượng:** nếu chậm, cắt bớt câu ví dụ và slide box-plot (30 — ý đã có ở 29) — nhưng **đừng bao giờ bỏ** câu nói về phương pháp/đánh giá và slide 6, vì đó là trọng tâm phần dữ liệu.
- **Câu hỏi dự phòng:**
  - *“Sao không dùng accuracy?”* → “Vì dữ liệu lệch lớp và lớp nguy cơ là lớp tốn kém khi bỏ sót; PR-AUC và recall phản ánh điều đó, còn accuracy có thể cao mà vẫn bỏ sót sinh viên nguy cơ.”
  - *“52,8% gần như cân bằng mà?”* → “Đúng, mức lệch là nhẹ (tỉ số 1,12) — nên nhóm em **phân tầng** thay vì lệ thuộc tái lấy mẫu, và giữ test ở tỉ lệ thật.”
  - *“Sao mốc muộn lại lạc quan?”* → “Vì sinh viên rút môn gần như bất hoạt nên dễ tách ở cuối khóa; phép thử thật là ở các mốc sớm.”
  - *“Vì sao dùng ClickHouse mà không phải pandas/Spark?”* → “File 10,6 triệu dòng nạp cả vào pandas tốn vài GB RAM mỗi lần hỏi; ClickHouse-local chạy SQL thẳng trên đĩa, không cần server, dưới một giây; Spark thì quá nặng cho một laptop. Mọi con số đều tái lập bằng notebook.”
- **Câu chuyển người** đã có sẵn ở cuối mỗi phần; nói rõ tên người kế tiếp để mạch liền mạch. Trang **Outline** và **Mục lục**: chỉ lướt, dùng làm nhịp chuyển.
