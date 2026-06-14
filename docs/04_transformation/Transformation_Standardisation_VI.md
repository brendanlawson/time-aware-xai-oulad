# Chuẩn Hóa và Biến Đổi Dữ Liệu: Phân Loại Biến, Mã Hóa và Chiến Lược Thang Đo

**DSP391m – Nhóm 1 · Báo cáo 2 (Nhiệm vụ Dữ liệu), Chương 3 · Nhiệm vụ 3.4 — Chuẩn hóa & Biến đổi**

---

## Tóm tắt (Abstract)

Báo cáo này ghi lại danh mục phân loại biến, các quyết định mã hóa (encoding) và chiến lược chuẩn hóa thang đo (standardisation) được triển khai trong `src/features/preprocessing.py` thuộc dự án học phần DSP391m (Nhóm 1). Tập dữ liệu, được trích xuất từ bộ dữ liệu phân tích học tập của Đại học Mở Anh (OULAD), chứa 28 đặc trưng thô và phái sinh bao gồm tương tác nhấp chuột (clickstream), thuộc tính nhân khẩu học và chỉ số kết quả học tập. Mỗi đặc trưng được gán vào một trong năm danh mục kiểu — định lượng (numeric), thứ bậc (ordinal), danh định (nominal), nhị phân (binary) hoặc chỉ báo (indicator) — và được xử lý bởi transformer tương ứng tương thích với sklearn trong một `ColumnTransformer` duy nhất. Một quy trình phòng tránh rò rỉ thông tin (anti-leakage) nghiêm ngặt quy định trình tự các bước: toàn bộ bộ mã hóa và `StandardScaler` chỉ được khớp (fit) trên tập huấn luyện và sau đó áp dụng cho cả tập huấn luyện lẫn tập kiểm tra. Giai đoạn biến đổi tạo ra ma trận đặc trưng dày đặc (dense) 49 cột, được xác minh không có giá trị khuyết (NaN), với tên đặc trưng được giữ nguyên theo chuẩn `snake_case` phục vụ phân tích diễn giải mô hình (explainability) bằng SHAP và LIME ở các bước tiếp theo.

---

## 1. Giới thiệu

Một pipeline học máy (machine learning) hiệu quả đòi hỏi các giá trị đặc trưng thô phải được chuyển đổi thành biểu diễn số vừa phù hợp về mặt toán học với từng lớp mô hình, vừa không bị nhiễm thông tin rò rỉ từ dữ liệu kiểm tra chưa thấy. Trong bài toán dự đoán sinh viên có nguy cơ (at-risk) của DSP391m, các đặc trưng bắt nguồn từ ba thang đo khác nhau: số đếm liên tục và rời rạc từ nhật ký nhấp chuột VLE, thuộc tính phân loại có thứ tự thu thập khi đăng ký học, và định danh phân loại không có thứ tự. Áp dụng một chiến lược mã hóa duy nhất cho tất cả các đặc trưng — ví dụ như dùng `OneHotEncoder` cho biến thứ bậc — sẽ loại bỏ thông tin thứ hạng nội tại của các danh mục như trình độ học vấn hay dải tước đoạt, làm phình to số chiều không gian đặc trưng mà không tăng thêm giá trị thông tin. Ngược lại, áp dụng mã số nguyên cho biến danh định như `region` sẽ áp đặt một quan hệ thứ tự sai lệch. Mục 2 liệt kê danh mục phân loại biến giải quyết các phân biệt này. Mục 3 trình bày chi tiết từng phương pháp mã hóa và căn cứ kỹ thuật. Mục 4 mô tả bước chuẩn hóa và cách triển khai phòng tránh rò rỉ. Mục 5 trình bày trình tự pipeline biến đổi. Mục 6 báo cáo các thuộc tính đầu ra đã được xác minh.

---

## 2. Danh mục Phân loại Biến

28 đặc trưng đầu vào (loại trừ biến mục tiêu `at_risk` và các cột định danh `id_student`, `code_module`, `code_presentation`) được chia thành năm kiểu. Việc phân loại kiểu biến quyết định lựa chọn transformer trong `ColumnTransformer` tiếp theo.

**Bảng 1. Phân loại biến và gán bộ mã hóa / chuẩn hóa**

| Kiểu | Số lượng | Biến | Bộ mã hóa / Chuẩn hóa |
|------|---------|------|------------------------|
| Định lượng (Numeric) | 19 | `num_of_prev_attempts`, `studied_credits`, `date_registration`, `total_clicks`, `n_days_active`, `clicks_forumng`, `clicks_oucontent`, `clicks_resource`, `clicks_homepage`, `clicks_oucollaborate`, `clicks_quiz`, `clicks_subpage`, `clicks_url`, `max_clicks_single_day`, `mean_clicks_per_active_day`, `days_since_last_activity`, `mean_score_to_date`, `n_assessments_submitted`, `weighted_score_to_date` | `StandardScaler` (một số đặc trưng được log1p / winsorize trước ở giai đoạn xử lý ngoại lai) |
| Thứ bậc (Ordinal) | 3 | `highest_education`, `imd_band`, `age_band` | `OrdinalEncoder` với thứ tự danh mục cố định, tường minh |
| Danh định (Nominal) | 3 | `region`, `code_module`, `code_presentation` | `OneHotEncoder` |
| Nhị phân (Binary) | 2 | `gender`, `disability` | Ánh xạ 0/1 trực tiếp qua `BinaryEncoder` tùy chỉnh |
| Chỉ báo (Indicator) | 1 | `not_submitted` | Passthrough (đã là 0/1 từ bước feature engineering) |

**Ghi chú về phân nhóm con trong biến định lượng.** Trong 19 biến định lượng, các số đếm nhấp chuột VLE (`total_clicks`, `n_days_active`, và toàn bộ tám cột `clicks_<type>`, cùng với `max_clicks_single_day` và `mean_clicks_per_active_day`) có phân phối lệch phải mạnh và được biến đổi trước bằng `log1p` trước khi áp dụng `StandardScaler`. Các biến `studied_credits`, `num_of_prev_attempts`, `weighted_score_to_date` và `days_since_last_activity` được winsorize ở phân vị thứ 1 và thứ 99. Ba biến — `mean_score_to_date`, `n_assessments_submitted` và `date_registration` — không nhận bất kỳ biến đổi ngoại lai nào.

---

## 3. Các Phương pháp Mã hóa và Căn cứ Kỹ thuật

### 3.1 OrdinalEncoder (biến thứ bậc)

Biến thứ bậc (ordinal) có thứ tự xếp hạng nội tại mang thông tin dự đoán. Mã hóa chúng thành các số nguyên 0, 1, 2, … k−1 bảo toàn thứ tự này mà không làm tăng số chiều. `OneHotEncoder` sẽ phá hủy quan hệ thứ hạng; do đó nó được loại trừ tường minh cho các biến này.

Thứ tự danh mục chính xác được cố định trong `ORDINAL_ORDERS` là:

- `highest_education`: `No Formal quals` < `Lower Than A Level` < `A Level or Equivalent` < `HE Qualification` < `Post Graduate Qualification`
- `imd_band`: `Unknown` < `0-10%` < `10-20` < `20-30%` < `30-40%` < `40-50%` < `50-60%` < `60-70%` < `70-80%` < `80-90%` < `90-100%`
- `age_band`: `0-35` < `35-55` < `55<=`

Cấu hình `handle_unknown='use_encoded_value'` kết hợp `unknown_value=-1` đảm bảo rằng mọi danh mục xuất hiện trong tập kiểm tra nhưng vắng mặt trong tập huấn luyện sẽ được gán mã −1 thay vì gây lỗi ngoại lệ (exception). Các mô hình dựa trên cây (Random Forest, XGBoost, LightGBM) xử lý giá trị sentinel này mà không gặp vấn đề.

### 3.2 OneHotEncoder (biến danh định)

Biến danh định (nominal) — `region`, `code_module`, `code_presentation` — không có thứ tự nội tại. Việc gán mã số nguyên sẽ áp đặt một thứ hạng sai lệch, ví dụ ngụ ý một vùng địa lý "lớn hơn" vùng khác. `OneHotEncoder` tạo ra một cột nhị phân cho mỗi giá trị danh mục, làm cho phép mã hóa bất biến với hoán vị.

Cấu hình: `handle_unknown='ignore'` (danh mục lạ trong tập kiểm tra tạo ra hàng toàn số không, tránh lỗi runtime); `sparse_output=False` (mảng dày đặc để tương thích pipeline); `drop=None` (giữ lại tất cả các cột). Lựa chọn `drop=None` là chủ ý: việc loại bỏ một cột tham chiếu sẽ ngăn SHAP waterfall plot và LIME gán tầm quan trọng (importance) cho danh mục bị loại bỏ đó, làm giảm khả năng diễn giải sau thực nghiệm (post-hoc interpretability).

### 3.3 BinaryEncoder (biến nhị phân)

Hai đặc trưng chỉ nhận đúng hai giá trị:

- `gender`: M → 1, F → 0
- `disability`: Y → 1, N → 0

Một lớp `BinaryEncoder` tùy chỉnh (kế thừa `BaseEstimator` / `TransformerMixin` của sklearn) triển khai bảng tra cứu cố định này. Không cần bước fit thực sự vì ánh xạ là hằng số được định nghĩa trong dự án; phương thức `fit` là no-op được giữ lại để tương thích với `ColumnTransformer`.

### 3.4 Passthrough (đặc trưng chỉ báo)

Cờ `not_submitted` được tạo ra bởi bước feature engineering dưới dạng số nguyên 0/1 và không cần biến đổi thêm. Nó được chuyển qua `ColumnTransformer` thông qua transformer `'passthrough'` để bảo toàn sự hiện diện trong ma trận đặc trưng đầu ra.

---

## 4. Chuẩn hóa Thang đo (Standardisation / Scaling)

### 4.1 StandardScaler

Toàn bộ 19 biến định lượng được chuẩn hóa về trung bình bằng không và phương sai đơn vị sử dụng `StandardScaler` của sklearn (chuẩn hóa z-score: x′ = (x − μ) / σ). Sau các biến đổi log1p hoặc winsorize đã áp dụng trong giai đoạn xử lý ngoại lai, mỗi cột định lượng được dịch chuyển và thu phóng độc lập sao cho phân phối trên tập huấn luyện có trung bình 0 và độ lệch chuẩn 1.

### 4.2 Căn cứ

Số đếm nhấp chuột VLE dao động từ không đến vài nghìn; biến điểm số trải dài từ 0 đến 100. Không có chuẩn hóa, các mô hình tính khoảng cách hoặc độ lớn gradient (Logistic Regression, Mạng nơ-ron nhân tạo / Artificial Neural Network) sẽ bị thống trị bởi các biến clickstream có biên độ cao. Mặc dù các mô hình dựa trên cây (Random Forest, XGBoost, LightGBM) phân chia trên ngưỡng đặc trưng và về lý thuyết không nhạy cảm với thang đo, `StandardScaler` được áp dụng đồng nhất trên toàn bộ đặc trưng định lượng để đảm bảo tính nhất quán của pipeline: một lần gọi `preprocess()` tạo ra ma trận đặc trưng hợp lệ cho mọi lớp mô hình mà không cần can thiệp thêm.

### 4.3 Triển khai Phòng tránh Rò rỉ (Anti-Leakage)

Bộ chuẩn hóa (scaler) chỉ được khớp (fit) trên tập huấn luyện. Các tham số đã khớp (`scaler.mean_` và `scaler.var_`) được tính toán hoàn toàn từ các quan sát huấn luyện. Phương thức `.transform()` — áp dụng trung bình và phương sai đã lưu — sau đó được gọi trên cả mảng huấn luyện và kiểm tra. Hàm tắt `.fit_transform()` không bao giờ được gọi trên toàn bộ tập dữ liệu. Điều này ngăn chặn bất kỳ thông tin thống kê nào từ tập kiểm tra ảnh hưởng đến phép biến đổi áp dụng lên dữ liệu huấn luyện, vốn sẽ cấu thành rò rỉ dữ liệu (data leakage) và tạo ra ước lượng khả năng tổng quát hóa quá lạc quan.

**Bảng 2. Tóm tắt mã hóa và chuẩn hóa**

| Transformer | Đặc trưng | Cấu hình chính |
|-------------|-----------|----------------|
| `StandardScaler` | 19 biến định lượng | Fit trên train only; `scaler.mean_` tính từ train |
| `OrdinalEncoder` | 3 biến thứ bậc | Danh sách danh mục tường minh; `handle_unknown='use_encoded_value'`, `unknown_value=-1` |
| `OneHotEncoder` | 3 biến danh định | `handle_unknown='ignore'`, `sparse_output=False`, `drop=None` |
| `BinaryEncoder` (tùy chỉnh) | 2 biến nhị phân | Bảng tra cứu cố định: M/Y→1, F/N→0 |
| `passthrough` | 1 biến chỉ báo | Không biến đổi |

---

## 5. Trình tự Pipeline Biến đổi

Trình tự pipeline phòng tránh rò rỉ đầy đủ, được triển khai trong `preprocess()`, là:

1. **Phân chia train/test** — thực hiện bên ngoài module này, trước mọi bước fit.
2. **`handle_missing(X_train)`** — logic điền khuyết được rút ra từ dữ liệu huấn luyện; cùng quy tắc đó được áp dụng cho tập kiểm tra mà không fit lại.
3. **`handle_outliers(X_train)`** — các biến đổi log1p và winsorize được áp dụng; tập kiểm tra được biến đổi theo cùng quy tắc xác định (deterministic).
4. **`ColumnTransformer.fit(X_train)`** — tất cả các transformer (StandardScaler, OrdinalEncoder, OneHotEncoder, BinaryEncoder) chỉ được khớp trên tập huấn luyện.
5. **`ColumnTransformer.transform(X_train)` và `.transform(X_test)`** — transformer đã khớp được áp dụng cho cả hai tập.
6. **Tái lấy mẫu (SMOTE/ADASYN)** — chỉ áp dụng trên mảng huấn luyện đã biến đổi; tập kiểm tra không bao giờ được tái lấy mẫu.

Trình tự này được tham chiếu chéo trong tài liệu Preprocessing Sequence (Tài liệu 07).

---

## 6. Thuộc tính Đầu ra

`ColumnTransformer` đã khớp được tuần tự hóa vào `scaler.pkl` thông qua `joblib.dump()` để đảm bảo khả năng tái tạo (reproducibility) và triển khai. Hàm `preprocess()` trả về bốn đối tượng: mảng huấn luyện đã biến đổi, mảng kiểm tra đã biến đổi, transformer đã khớp, và danh sách tên đặc trưng thu được từ `ct.get_feature_names_out()`.

Các thuộc tính đầu ra đã được xác minh:

- **Số cột**: 49 cột sau khi mã hóa (19 định lượng + 3 thứ bậc + kết quả mở rộng one-hot của region/code_module/code_presentation + 2 nhị phân + 1 chỉ báo).
- **Giá trị khuyết**: không có giá trị NaN trong bất kỳ mảng đầu ra nào sau khi biến đổi.
- **Tên đặc trưng**: được giữ đầy đủ theo chuẩn `snake_case` với tiền tố tên transformer (ví dụ: `num__total_clicks`, `nominal__region_East Anglian Region`) để gán nhãn tường minh trong SHAP waterfall plot và hiển thị tầm quan trọng đặc trưng của LIME.

---

## 7. Quy tắc Đặt tên Đặc trưng và Khả năng Diễn giải Sau thực nghiệm

Việc sử dụng nhất quán tên cột mô tả theo chuẩn `snake_case` xuyên suốt `preprocessing.py` (ví dụ: `mean_clicks_per_active_day`, `weighted_score_to_date`, `days_since_last_activity`) đảm bảo rằng kết quả đầu ra của SHAP và LIME tự giải thích. Khi `ColumnTransformer` được cấu hình với `verbose_feature_names_out=True`, mỗi cột đầu ra mang tiền tố transformer giúp xác định nguồn gốc, cho phép nhà phân tích truy ngược bất kỳ giá trị tầm quan trọng đặc trưng nào về biến nguồn thô tương ứng mà không cần tra cứu từ điển dữ liệu riêng biệt. Lựa chọn thiết kế này trực tiếp hỗ trợ yêu cầu khả năng diễn giải của bài toán dự đoán nguy cơ sinh viên, trong đó giáo viên và cố vấn học tập phải hiểu được hành vi sinh viên hoặc thuộc tính nhân khẩu học nào thúc đẩy từng cảnh báo nguy cơ cá nhân.

---

*Biên soạn bởi Nhóm 1 DSP391m. Toàn bộ logic biến đổi tham chiếu `src/features/preprocessing.py`, đã commit vào kho mã nguồn dự án (nhánh: main).*
