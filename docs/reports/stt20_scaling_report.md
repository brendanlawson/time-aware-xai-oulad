# STT20 - Chuẩn hoá thang đo trên tập huấn luyện

## 1. Mục tiêu

Phần STT20 thực hiện chuẩn hoá các biến định lượng trong pipeline tiền xử lý OULAD. Mục tiêu là đưa các đặc trưng có biên độ rất khác nhau về cùng thang đo, đồng thời đảm bảo không rò rỉ thông tin từ tập kiểm tra sang tập huấn luyện. Trong bài toán dự đoán sinh viên có nguy cơ, các biến như tổng lượt click có thể nằm ở thang hàng nghìn, trong khi điểm đánh giá nằm trong khoảng 0-100 và số lần học lại chỉ nằm ở thang đơn vị. Nếu không chuẩn hoá, các mô hình nhạy với thang đo như Logistic Regression và ANN có thể bị chi phối bởi những biến có biên độ lớn.

## 2. Biến được chuẩn hoá

Danh sách biến numeric được khai báo trong `src/features/preprocessing.py` tại `NUMERIC_FEATURES`. Nhóm biến này bao gồm:

| Nhóm biến | Ví dụ biến | Lý do cần chuẩn hoá |
| --- | --- | --- |
| Nền học tập | `num_of_prev_attempts`, `studied_credits`, `date_registration` | Các biến có đơn vị và biên độ khác nhau. |
| Tương tác VLE | `total_clicks`, `n_days_active`, `clicks_forumng`, `clicks_oucontent`, `clicks_resource`, `clicks_homepage`, `clicks_oucollaborate`, `clicks_quiz`, `clicks_subpage`, `clicks_url` | Clickstream thường lệch phải và có giá trị lớn hơn điểm số nhiều lần. |
| Đặc trưng VLE phái sinh | `max_clicks_single_day`, `mean_clicks_per_active_day`, `days_since_last_activity` | Cần đưa về cùng thang với các biến số khác sau khi xử lý ngoại lai. |
| Kết quả học tập | `mean_score_to_date`, `n_assessments_submitted`, `weighted_score_to_date` | Kết hợp biến điểm, biến đếm và điểm có trọng số. |

Trước khi vào bước chuẩn hoá, pipeline đã xử lý missing values và outliers. Các biến click lệch phải được biến đổi `log1p` trong bước xử lý ngoại lai, sau đó mới được đưa vào `StandardScaler`.

## 3. Phương pháp thực hiện

Pipeline sử dụng `StandardScaler` của scikit-learn, biến đổi mỗi biến numeric theo công thức:

```text
z = (x - mean_train) / std_train
```

Trong đó `mean_train` và `std_train` chỉ được tính trên tập huấn luyện. Việc này được hiện thực trong các hàm:

| Thành phần | Vị trí | Vai trò |
| --- | --- | --- |
| `build_scaler()` | `src/features/preprocessing.py` | Khởi tạo `StandardScaler`. |
| `build_column_transformer()` | `src/features/preprocessing.py` | Gắn nhánh `("num", build_scaler(), numeric_cols)` cho các biến định lượng. |
| `fit_transform_train()` | `src/features/preprocessing.py` | Gọi `ct.fit_transform(X_train)` và lưu minh chứng `scaler.mean_`. |
| `transform_test()` | `src/features/preprocessing.py` | Chỉ gọi `ct.transform(X_test)`, không fit lại trên test. |
| `preprocess()` | `src/features/preprocessing.py` | Điều phối đúng thứ tự: missing -> outlier -> fit train -> transform test. |

## 4. Kiểm soát rò rỉ dữ liệu

Nguyên tắc quan trọng của STT20 là scaler không được học từ toàn bộ dữ liệu. Nếu tính trung bình và độ lệch chuẩn trên cả train và test, thông tin phân phối của tập test sẽ bị đưa vào quá trình tiền xử lý, làm đánh giá mô hình lạc quan giả tạo.

Quy trình đúng trong repo:

1. Chia train/test bên ngoài module preprocessing.
2. Gọi `fit_transform_train(X_train)` để fit `ColumnTransformer` trên train.
3. Lấy `ct.named_transformers_["num"].mean_` làm minh chứng tham số scaler chỉ đến từ train.
4. Gọi `transform_test(ct, X_test)` để biến đổi test bằng transformer đã fit.
5. Nếu cần SMOTE/ADASYN, chỉ áp dụng sau preprocessing và chỉ trên `X_train_proc`.

## 5. Kết quả kiểm thử

Smoke test được chạy bằng lệnh:

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe .\src\features\preprocessing.py
```

Kết quả chính:

| Hạng mục kiểm tra | Kết quả |
| --- | --- |
| Kích thước train sau transform | `(200, 38)` |
| Kích thước test sau transform | `(50, 38)` |
| Số feature sau mã hoá + chuẩn hoá | `38` |
| NaN sau transform | Không còn NaN |
| Minh chứng scaler | `scaler.mean_[:4] = [2.045, 330.935, -9.63, 7.5868]`, chỉ tính từ `X_train` |
| Kết luận smoke test | Tất cả kiểm tra đạt |

## 6. Nội dung đưa vào báo cáo Chương 3

Trong giai đoạn chuẩn bị dữ liệu, nhóm chuẩn hoá các biến định lượng bằng `StandardScaler` sau khi đã xử lý giá trị khuyết và ngoại lai. Cách làm này đưa các đặc trưng về phân phối có trung bình 0 và độ lệch chuẩn 1, giúp các mô hình nhạy với thang đo như Logistic Regression và ANN không bị chi phối bởi các biến có biên độ lớn, đặc biệt là nhóm clickstream. Các mô hình cây như Random Forest, XGBoost và LightGBM ít nhạy với thang đo hơn, nhưng việc giữ một pipeline chuẩn hoá thống nhất giúp so sánh mô hình và tích hợp SHAP/LIME thuận tiện hơn.

Để tránh rò rỉ dữ liệu, scaler chỉ được fit trên tập huấn luyện. Tập kiểm tra và các tập checkpoint chỉ được biến đổi bằng transformer đã học tham số từ train. Pipeline trong `preprocessing.py` thực hiện rõ thứ tự này: xử lý khuyết, xử lý ngoại lai, fit-transform train, transform test; các bước học tham số như scaler, encoder và resampling không bao giờ được fit trên tập kiểm tra. Smoke test của module xác nhận sau tiền xử lý không còn NaN, train và test có cùng số đặc trưng sau biến đổi, và tham số `scaler.mean_` chỉ được tính từ tập huấn luyện.

## 7. Kết luận nghiệm thu STT20

STT20 đã đạt các tiêu chí nghiệm thu:

- Có hàm tạo scaler và tích hợp trong `ColumnTransformer`.
- Scaler được fit trên train và áp dụng transform cho test.
- Có minh chứng `scaler.mean_` chỉ tính từ train.
- Smoke test pipeline chạy thành công, không còn NaN sau transform.
- Trình tự preprocessing phù hợp yêu cầu anti-leakage của README.
