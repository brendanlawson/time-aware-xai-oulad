# Phương Pháp Làm Sạch Dữ Liệu: Phân Tích và Luận Giải

**DSP391m – Nhóm 1 · Báo cáo 2 (Nhiệm vụ Dữ liệu), Chương 3 · Task 3.3 — Phương Pháp Làm Sạch Dữ Liệu**

---

## Tóm Tắt

Chương này trình bày phân tích bốn vấn đề làm sạch dữ liệu được xử lý trong pipeline của Nhóm 1 DSP391m: bản ghi trùng lặp (duplicate records), không nhất quán danh mục (categorical inconsistency), giá trị khuyết (missing values) và ngoại lai (outliers). Một vấn đề thứ năm — rò rỉ thông tin thời gian (temporal leakage) do bản ghi có ngày trong tương lai — được coi là bước làm sạch đồng thời là bước ngăn rò rỉ (leakage-prevention). Với mỗi vấn đề, bài viết trình bày mục đích, cơ chế phát hiện, quyết định cho từng biến và kết quả sau làm sạch được kiểm chứng. Toàn bộ logic làm sạch nằm trong hai module: `src/data/build_master_table.py` (tính toàn vẹn cấu trúc, trùng lặp, nhất quán) và `src/features/preprocessing.py` (giá trị khuyết, ngoại lai). Mọi quyết định đều có khả năng tái tạo: tham số được học từ tập huấn luyện (training split) duy nhất, và mọi hàng được biến đổi đều được giữ lại trong bộ dữ liệu.

---

## 1. Giới Thiệu

Dữ liệu thô được tổng hợp từ việc nối bảy bảng OULAD chứa các lỗi, nếu không được sửa, sẽ làm lệch quá trình huấn luyện mô hình hoặc vô hiệu hóa các chỉ số đánh giá. Bốn loại lỗi được xử lý có hệ thống trước khi phân chia train/test và lại trong trình tự tiền xử lý (preprocessing) chống rò rỉ. Thứ tự thực hiện là: (1) làm sạch cấu trúc lúc xây dựng bảng, (2) điền giá trị khuyết được học từ tập train, (3) biến đổi ngoại lai được học từ tập train, (4) mã hóa và chuẩn hóa được học từ tập train.

---

## 2. Bản Ghi Trùng Lặp

**Mục đích.** Mỗi hàng trong bảng master được thiết kế để biểu diễn một bộ ba duy nhất (sinh viên, module, học kỳ). Các khóa tổng hợp bị trùng lặp sẽ làm tăng số lượng bản ghi của một số sinh viên và làm sai lệch các thống kê tổng hợp.

**Phương pháp.** Hàm `_clean` trong `build_master_table.py` gọi `pandas.DataFrame.drop_duplicates` trên khóa tổng hợp `(code_module, code_presentation, id_student)`, tương ứng với hằng số `GROUP_COLS`. Bảng sau khi khử trùng lặp được đánh chỉ số lại từ đầu.

**Kết quả.** Kiểm tra sau làm sạch xác nhận không còn khóa trùng lặp. Số lượng được ghi vào `data/interim/master_cleaning_log.csv` dưới mục `duplicate_keys_removed`. Nhật ký nối bảng (join log) ghi riêng số lượng hàng ở mỗi bước merge để phát hiện ngay lập tức khi số hàng tăng bất thường.

### 2.1 Dòng clickstream trùng lặp toàn phần — quyết định được văn bản hoá

**Quan sát.** File thô `studentVle.csv` có 10.655.280 dòng, trong đó 787.170 dòng (7,4%) trùng lặp toàn phần (giống hệt trên mọi cột) với một dòng khác. Đây là đặc điểm có sẵn của chính bản phân phối OULAD: bảng này không có khóa duy nhất, và một dòng biểu diễn tương tác của một sinh viên với một tài nguyên VLE trong một ngày, với `sum_click` đã được cộng gộp từ nguồn. Vì vậy, chỉ dựa vào lược đồ, hai dòng giống hệt nhau không thể phân biệt với một bản ghi tổng hợp lặp lại hợp lệ.

**Quyết định — giữ và cộng dồn.** Pipeline giữ nguyên các dòng này; bước tổng hợp theo mốc (`groupby` + `sum` trên `sum_click`) cộng dồn chúng vào các đặc trưng tương tác. Căn cứ: (i) trung thành với bộ dữ liệu như được công bố — khi không có khóa duy nhất, việc xóa một bản sao sẽ là phỏng đoán không kiểm chứng được về việc bản ghi nào là "thật"; (ii) nhất quán với các nghiên cứu nền (Adnan và cộng sự 2021; Tomasevic và cộng sự 2020), vốn làm việc trên các bảng OULAD gốc mà không khử trùng lặp clickstream, nhờ đó các đặc trưng từ click của chúng tôi vẫn so sánh được.

**Giới hạn được ghi nhận.** Nếu một phần các dòng trùng này là lỗi ghi kép từ nguồn, các tổng click (`total_clicks`, `clicks_*`) sẽ bị đếm trội cho những ngày-sinh viên bị ảnh hưởng. Điều này được chấp nhận và văn bản hoá như một giới hạn của dữ liệu nguồn thay vì "sửa" bằng cách xóa. Lưu ý sự tương phản với bước khử trùng lặp bảng master ở trên, nơi khóa tổng hợp cho phép nhận diện chắc chắn bản ghi trùng thực sự.

---

## 3. Nhất Quán và Chuẩn Hóa

**Mục đích.** Các cột chuỗi phân loại (categorical string) được lấy từ CSV có thể chứa khoảng trắng đầu hoặc cuối, khiến các danh mục giống nhau về ngữ nghĩa xuất hiện như các giá trị riêng biệt trong thao tác groupby hay encoder.

**Phương pháp.** Đối với mỗi cột trong `CATEGORICAL_COLS` — `gender`, `region`, `highest_education`, `imd_band`, `age_band`, `disability` — pipeline áp dụng `str.strip()` sau khi nối bảng. Không thực hiện chuẩn hóa chữ hoa/thường hay hợp nhất từ đồng nghĩa; mục đích là chuẩn hóa tối thiểu, có thể đảo ngược.

**Lực lượng số (cardinality) đã kiểm chứng sau làm sạch.**

| Biến | Số giá trị phân biệt |
|---|---|
| `region` | 13 |
| `highest_education` | 5 |
| `imd_band` | 10 |
| `age_band` | 3 |
| `gender` | 2 |
| `disability` | 2 |

**Đặc điểm OULAD: giá trị `"10-20"` trong `imd_band`.** Dữ liệu gốc OULAD bỏ sót ký hiệu `%` ở dải thứ hai, ghi là `"10-20"` thay vì `"10-20%"`. Pipeline giữ nguyên giá trị này. Bộ mã hóa thứ bậc (ordinal encoder) định nghĩa trong `preprocessing.py` liệt kê rõ ràng `"10-20"` ở thứ hạng 2 trong chuỗi `ORDINAL_ORDERS["imd_band"]`. Việc tự động ghi đè danh mục thô sẽ tạo ra sự không khớp giữa dữ liệu nguồn và cấu hình encoder, đồng thời làm phức tạp việc kiểm tra khả năng tái tạo.

---

## 4. Giá Trị Khuyết

**Mục đích.** Giá trị khuyết không được xử lý sẽ ngăn các estimator của sklearn huấn luyện và, nếu được điền một cách thô sơ, có thể gây rò rỉ thông tin (leakage) hoặc làm méo tín hiệu suy diễn.

**Phương pháp.** Hàm `handle_missing` trong `preprocessing.py` áp dụng các chiến lược theo từng biến. Các thống kê điền giá trị (median của `date_registration` trên tập huấn luyện) được tính chỉ từ tập train và sau đó áp dụng đồng nhất cho tập test, đáp ứng yêu cầu chống rò rỉ.

**Bảng 1: Phân tích giá trị khuyết.**

| Biến | # Khuyết | Cơ chế giả định | Chiến lược |
|---|---|---|---|
| `imd_band` | 1.111 | MAR / MCAR | Điền `'Unknown'`; chèn làm danh mục thứ hạng 0 trong `ORDINAL_ORDERS["imd_band"]` |
| `mean_score_to_date` | thiếu khi chưa nộp bài | MNAR | Điền `0`; chỉ báo nhị phân (binary indicator) `not_submitted` đã được tạo trong bước feature engineering |
| `weighted_score_to_date` | thiếu khi chưa nộp bài | MNAR | Điền `0`; cùng chỉ báo `not_submitted` |
| `n_assessments_submitted` | thiếu khi chưa nộp bài | MNAR | Điền `0`; cùng chỉ báo `not_submitted` |
| `date_registration` | 45 | MCAR | Điền median của tập huấn luyện (học từ train) |
| `date_unregistration` | 22.521 | Vắng mặt theo cấu trúc | Không điền; không dùng làm đặc trưng |

**Căn cứ quyết định.**

- `imd_band`: Sự vắng mặt có thể có tính chất hành chính hơn là liên quan đến kết quả học tập (MAR hoặc MCAR). Tạo danh mục `"Unknown"` riêng bảo toàn thang đo thứ bậc của 10 giá trị còn lại mà không phải ước tính một giá trị kinh tế-xã hội giả tạo.
- Biến điểm số (MNAR): Điểm khuyết tại mốc thời gian *t* có nghĩa là sinh viên chưa nộp bài nào tính đến ngày đó. Điều này bản thân nó là tín hiệu dự đoán mạnh về trạng thái có nguy cơ (at-risk). Điền bằng 0 làm tín hiệu trở nên rõ ràng; chỉ báo nhị phân `not_submitted` nắm bắt riêng sự kiện vắng mặt, ngăn số 0 bị nhầm với bài nộp đạt điểm 0 thực sự.
- `date_registration`: Chỉ 45 bản ghi bị ảnh hưởng và sự vắng mặt có vẻ không liên quan đến kết quả (MCAR). Điền median học từ tập huấn luyện đơn giản và gây ra sai lệch không đáng kể.
- `date_unregistration`: Đa số sinh viên hoàn thành mà không hủy đăng ký, nên 22.521 giá trị khuyết là không tránh khỏi về mặt cấu trúc. Đưa cột này vào làm đặc trưng sẽ đòi hỏi điền ngày hủy đăng ký giả tưởng cho phần lớn sinh viên, điều này không có cơ sở.

**Kết quả kiểm chứng.** Sau `handle_missing`, `df.isnull().sum()` bằng 0 trên mọi cột đặc trưng ở cả tập train lẫn tập test, được xác nhận bằng phép kiểm tra (assertion) trong smoke test của pipeline.

**Errata (2026-07-12): bài đánh giá được bảo lưu (banked) & `not_submitted`.** Một lỗi được phát hiện và sửa ngày 2026-07-12 trong `src/data/build_performance_features.py`: các bài đánh giá được bảo lưu điểm từ lần học trước ("banked", `is_banked = 1`) bị loại khỏi tập bài "đã nộp", nhưng chính các bài đó vẫn bị tính là "đã đến hạn" tại mốc kiểm tra — khiến chỉ báo `not_submitted` bị gán 1 sai cho những sinh viên đã bảo lưu bài. Ảnh hưởng đo được: 78 trên 32.593 bản ghi ghi danh (0,24%) tại *t* = 100%. Code hiện đã tính bài bảo lưu là đã bao phủ hạn nộp của nó. Các bảng kết quả đã commit trước ngày này được tính bằng code trước khi sửa và sẽ được tính lại toàn bộ trong lần chạy chốt báo cáo cuối (danh mục cập nhật số liệu được theo dõi trong sổ tay bảo vệ).

---

## 5. Ngoại Lai

**Mục đích.** Các giá trị cực đoan trong các đặc trưng tương tác (engagement features) bị lệch phải mạnh sẽ làm sai lệch các mô hình dựa trên khoảng cách và thổi phồng ước lượng phương sai trong các mô hình cây. Mục tiêu là giảm ảnh hưởng của giá trị cực đoan mà không loại bỏ bản ghi sinh viên nào.

**Phát hiện.** Quy tắc IQR (interquartile range) được áp dụng: một giá trị được đánh dấu là nghi ngờ ngoại lai khi nằm dưới Q1 − 1,5 × IQR hoặc trên Q3 + 1,5 × IQR. Ngưỡng được tính từ tập huấn luyện. Không có hàng nào bị xóa.

**Các chiến lược biến đổi.**

- `log1p`: Áp dụng cho các đặc trưng clickstream (dữ liệu click) lệch phải mạnh. Phép biến đổi `x → log(1 + x)` nén đuôi phải dài trong khi ánh xạ số 0 về số 0, điều này quan trọng vì nhiều sinh viên không có hoạt động trong một loại tương tác nhất định.
- `winsorize` (cắt ngưỡng): Áp dụng ở giới hạn 1% (đầu và cuối 1%). Các giá trị dưới phân vị thứ nhất hoặc trên phân vị thứ 99 được kẹp vào giá trị biên đó, bảo toàn thứ hạng thứ tự của mọi quan sát.
- `none` (không xử lý): Áp dụng khi biến bị chặn tự nhiên hoặc khi phân tích IQR không phát hiện ngoại lai thực sự.

**Bằng chứng về độ lệch từ phân tích dữ liệu khám phá (EDA).** Biến `max_clicks_single_day` có hệ số lệch (skewness) xấp xỉ 10,6; `total_clicks` xấp xỉ 3,0; `mean_clicks_per_active_day` xấp xỉ 1,6. Các giá trị này biện minh cho xử lý `log1p`.

**Bảng 2: Quyết định xử lý ngoại lai.**

| Biến (nhóm) | Phát hiện | Chiến lược | Lý do |
|---|---|---|---|
| `total_clicks` | IQR | `log1p` | Hệ số lệch ≈ 3,0; giá trị max lên tới hàng nghìn |
| `n_days_active` | IQR | `log1p` | Count lệch phải mạnh |
| `clicks_forumng`, `clicks_oucontent`, `clicks_resource`, `clicks_homepage`, `clicks_oucollaborate`, `clicks_quiz`, `clicks_subpage`, `clicks_url` | IQR | `log1p` | Số click theo từng loại hoạt động, cùng hình dạng phân phối |
| `max_clicks_single_day` | IQR | `log1p` | max = 7.920; hệ số lệch ≈ 10,6 |
| `mean_clicks_per_active_day` | IQR | `log1p` | max = 1.879; hệ số lệch ≈ 1,6 |
| `days_since_last_activity` | IQR | `winsorize` (1%) | Chỉ 6 bản ghi bị đánh dấu; lệch nhẹ |
| `studied_credits` | IQR | `winsorize` (1%) | max = 655; lệch phải vừa phải |
| `num_of_prev_attempts` | IQR | `winsorize` (1%) | IQR = 0, Q1 = Q3 = 0; winsorize bảo toàn tín hiệu "học lại nhiều lần" quan trọng với sinh viên at-risk |
| `weighted_score_to_date` | IQR | `winsorize` (1%) | Phạm vi lý thuyết mở; winsorize an toàn hơn log1p cho điểm số |
| `mean_score_to_date` | IQR | `none` | Cận trên 103,15 từ phân tích IQR vượt giới hạn vật lý 100, cho thấy không có ngoại lai thực sự |
| `n_assessments_submitted` | IQR | `none` | Bị chặn bởi số lượng bài kiểm tra của khóa học |
| `date_registration` | IQR | `none` | Phạm vi ký hiệu tự nhiên (âm = trước khóa học); không cần biến đổi |

---

## 6. Làm Sạch Thời Gian

**Mục đích.** Pipeline tạo nhiều snapshot đặc trưng tại các mốc kiểm tra (checkpoint) được xác định trước (ví dụ: ngày 60, ngày 90, toàn khóa). Bất kỳ bản ghi nào có ngày sau mốc *t* — dù là tương tác VLE hay nộp bài kiểm tra — đều phải bị loại trước khi tính đặc trưng cho mốc đó.

**Phương pháp.** Hàm `cut_at_checkpoint` (trong `src/data/time_utils.py`) lọc các hàng để chỉ giữ lại những hàng có ngày ≤ *t* trước khi tổng hợp đặc trưng. Bước này vừa là thao tác làm sạch dữ liệu (loại bỏ các quan sát không hợp lệ về mặt thời gian) vừa là biện pháp ngăn rò rỉ (đảm bảo không có thông tin sau ngày dự đoán ảnh hưởng đến đặc trưng). Nó được áp dụng độc lập cho từng mốc kiểm tra và từng fold của phân chia train/test.

---

## 7. Tại Sao Điều Này Quan Trọng Đối Với Mô Hình Hóa

Đầu vào sạch, nhất quán và không rò rỉ là điều kiện tiên quyết để mô hình hóa có giá trị. Các hàng trùng lặp làm tăng ảnh hưởng của một số sinh viên lên các tham số được học; các ký tự khoảng trắng thừa khiến encoder tạo ra các danh mục giả; giá trị khuyết MNAR không được xử lý làm mất tín hiệu dự đoán thay vì điền chúng; độ lệch phải chưa được xử lý khiến các estimator dựa trên gradient và khoảng cách overfit theo giá trị cực đoan; và các bản ghi có ngày trong tương lai gây rò rỉ nhãn (label leakage) làm cho các chỉ số đánh giá trở nên lạc quan một cách giả tạo. Bốn bước làm sạch được mô tả trong chương này, áp dụng theo thứ tự được thiết lập bởi trình tự pipeline chống rò rỉ, tạo ra bộ dữ liệu mà trên đó bước phân chia train/test và giai đoạn biến đổi có thể hoạt động đúng đắn và có tính tái tạo.
