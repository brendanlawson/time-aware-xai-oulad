# Định nghĩa biến mục tiêu và quy ước xử lý Withdrawn theo thời gian

*Nhãn nhị phân at-risk cho bài toán phát hiện sớm sinh viên nguy cơ trên OULAD*

**DSP391m – Nhóm 1 · Báo cáo 2 (Tác vụ dữ liệu), Chương 3 · Hạng mục STT 1 (cả nhóm) & STT 26 (Sơn)**
*Tham chiếu: biên bản thống nhất nhóm BB-B0-N1 (Bước 0).*

---

## 1. Phát biểu bài toán

Đề tài là bài toán **phân loại nhị phân** (binary classification): tại mỗi mốc tiến độ khoá học, dự đoán sinh viên có **nguy cơ (at-risk)** hay không. Không thực hiện hồi quy điểm; chỉ sử dụng OULAD. Nhãn được suy ra từ trường `final_result` trong bảng `studentInfo` và **cố định xuyên suốt sáu mốc thời gian**.

## 2. Ánh xạ `final_result` sang nhãn nhị phân

| `final_result` | Ý nghĩa | Nhóm | Nhãn (mã) |
|---|---|---|---|
| Distinction | Đạt loại giỏi | Đạt | not-at-risk (0) |
| Pass | Đạt | Đạt | not-at-risk (0) |
| Fail | Trượt môn | Nguy cơ | at-risk (1) |
| Withdrawn | Rút môn | Nguy cơ | at-risk (1) |

```python
df["at_risk"] = df["final_result"].isin(["Fail", "Withdrawn"]).astype(int)
# 1 = at-risk (lớp dương cần phát hiện); 0 = not-at-risk
```

**Hợp nhất Distinction vào Pass.** Bài toán là nhị phân; Distinction là kết quả *tốt hơn* Pass và không thuộc đối tượng cần can thiệp. Việc hợp nhất giúp định nghĩa lớp rõ ràng, tránh tạo thêm một lớp quá nhỏ, và bám đúng mục tiêu *phát hiện nguy cơ* thay vì *xếp hạng mức độ đạt*.

## 3. Phân phối lớp thực tế (không dùng số liệu minh hoạ trên slide)

Đo trên 32.593 bản ghi sinh viên–môn–kỳ của `studentInfo`:

| Lớp | Giá trị `final_result` | Số lượng | Tỉ lệ |
|---|---|---|---|
| not-at-risk (0) | Pass (12.361) + Distinction (3.024) | 15.385 | 47,2% |
| at-risk (1) | Fail (7.052) + Withdrawn (10.156) | 17.208 | **52,8%** |

Như vậy lớp at-risk là **lớp đa số nhẹ** (≈52,8%); mức **mất cân bằng là nhẹ**. Con số "68/32" đôi khi xuất hiện trên slide chỉ **mang tính minh hoạ** và không được trích dẫn như số liệu của bộ dữ liệu. Dù mất cân bằng nhẹ, việc đánh giá vẫn dùng **PR-AUC và recall trên lớp at-risk**, vì bỏ sót một sinh viên nguy cơ là sai lầm tốn kém nhất (xem STT 25).

## 4. Quy ước xử lý Withdrawn theo thời gian — Phương án A (đã chọn)

Tại mốc *t%*, một sinh viên Withdrawn có thể rút môn **trước** hoặc **sau** ngày mốc. Nhóm chọn **Phương án A — nhãn cố định, giữ nguyên quần thể**:

1. Nhãn của mỗi sinh viên **cố định** theo `final_result` tại mọi mốc (nhãn không đổi theo *t*).
2. Tập sinh viên **đồng nhất** qua cả sáu mốc và tập kiểm tra, đáp ứng yêu cầu tập kiểm tra cố định (STT 8).
3. Sinh viên Withdrawn rút trước mốc *t* vẫn được **giữ** trong dữ liệu mốc *t* và vẫn **gán nhãn at-risk**. Đặc trưng của họ chỉ phản ánh hoạt động tới ngày rút nên rất thấp — và chính **sự suy giảm hoạt động này là tín hiệu cảnh báo sớm**, không phải lỗi dữ liệu.
4. Hàm cắt theo thời gian (STT 11) tự động loại mọi sự kiện có ngày vượt mốc, nên **không phát sinh rò rỉ thời gian**.

**Hạn chế cần ghi nhận.** Ở các mốc muộn, sinh viên rút sớm gần như không còn hoạt động nên mô hình dễ phát hiện, có thể khiến recall và PR-AUC lạc quan hơn thực tế. Báo cáo nêu rõ hạn chế này và, nếu tiến độ cho phép, kiểm chứng bằng phân tích độ nhạy theo *Phương án B (kiểm duyệt theo mốc)*.

## 5. Hệ quả cho các bước phía sau

Mọi hạng mục phụ thuộc "Bước 0" đều kế thừa định nghĩa này: quy tắc phòng rò rỉ (STT 12), khảo sát lược đồ và bảng quy đổi mốc (STT 9, 10), thiết kế phân chia (STT 21), và tài liệu nguồn gốc/đạo đức (STT 30). Tên cột mục tiêu là `at_risk`; `final_result` chỉ được giữ lại như nguồn gốc thô của nhãn.

## Tài liệu tham khảo

1. M. Adnan và cộng sự, "Predicting at-Risk Students at Different Percentages of Course Length for Early Intervention," *IEEE Access*, vol. 9, tr. 7519–7539, 2021.
2. N. Tomasevic, N. Gvozdenovic, S. Vranes, "An overview and comparison of supervised data mining techniques for student exam performance prediction," *Computers & Education*, vol. 143, art. 103676, 2020.
3. J. Kuzilek, M. Hlosta, Z. Zdrahal, "Open University Learning Analytics dataset," *Scientific Data*, vol. 4, art. 170171, 2017.
