# Từ điển dữ liệu bảng hợp nhất OULAD (đầy đủ)

*Bao phủ 100% cột của master_raw. Tự sinh từ bảng hợp nhất.*

**DSP391m – Nhóm 1 · Báo cáo 2 · STT 29 (An)**

Tổng số biến: **33**

## Identifier

| # | Biến | Kiểu | Nguồn gốc | Mô tả | Ví dụ / Khoảng |
|---|---|---|---|---|---|
| 1 | `code_module` | Danh định (ID) | Original | Mã môn học; thuộc khoá tổng hợp. | 7 unique |
| 2 | `code_presentation` | Danh định (ID) | Original | Mã kỳ học (B=tháng 2, J=tháng 10); thuộc khoá tổng hợp. | 4 unique |
| 3 | `id_student` | Danh định (ID) | Original | Mã sinh viên duy nhất; khoá nhóm cho GroupKFold (không là đặc trưng). | min 3733, max 2.7168e+06 |

## Demographic

| # | Biến | Kiểu | Nguồn gốc | Mô tả | Ví dụ / Khoảng |
|---|---|---|---|---|---|
| 4 | `gender` | Nhị phân | Original | Giới tính; mã hoá M=1, F=0. | 2 unique |
| 5 | `region` | Danh định | Original | Vùng của Anh/Ireland (13 giá trị); mã hoá one-hot. | 13 unique |
| 6 | `highest_education` | Thứ bậc | Original | Trình độ học vấn cao nhất; thứ bậc 0..4. | 5 unique |
| 7 | `imd_band` | Thứ bậc | Original | Chỉ số nghèo khó (IMD) theo vùng; thứ bậc; 1.111 khuyết -> 'Unknown'. | 10 unique |
| 8 | `age_band` | Thứ bậc | Original | Nhóm tuổi; thứ bậc 0..2. | 3 unique |
| 9 | `num_of_prev_attempts` | Định lượng (rời rạc) | Original | Số lần học lại môn trước đó. | min 0, max 6 |
| 10 | `studied_credits` | Định lượng (rời rạc) | Original | Tổng số tín chỉ đang học. | min 30, max 655 |
| 11 | `disability` | Nhị phân | Original | Khai báo khuyết tật; mã hoá Y=1, N=0. | 2 unique |

## Engagement

| # | Biến | Kiểu | Nguồn gốc | Mô tả | Ví dụ / Khoảng |
|---|---|---|---|---|---|
| 12 | `total_clicks` | Định lượng (liên tục) | Derived | Tổng lượt click VLE tới mốc; lệch phải -> log1p. | min 0, max 24139 |
| 13 | `n_days_active` | Định lượng (rời rạc) | Derived | Số ngày có hoạt động (distinct) tới mốc. | min 0, max 286 |
| 14 | `max_clicks_single_day` | Định lượng (liên tục) | Derived | Số click tối đa trong một ngày tới mốc; lệch phải mạnh -> log1p. | min 0, max 6988 |
| 15 | `clicks_forumng` | Định lượng (liên tục) | Derived | Click loại 'forumng' tới mốc. | min 0, max 13154 |
| 16 | `clicks_oucontent` | Định lượng (liên tục) | Derived | Click loại 'oucontent' tới mốc. | min 0, max 9308 |
| 17 | `clicks_resource` | Định lượng (liên tục) | Derived | Click loại 'resource' tới mốc. | min 0, max 5147 |
| 18 | `clicks_homepage` | Định lượng (liên tục) | Derived | Click loại 'homepage' tới mốc. | min 0, max 7277 |
| 19 | `clicks_oucollaborate` | Định lượng (liên tục) | Derived | Click loại 'oucollaborate' tới mốc. | min 0, max 316 |
| 20 | `clicks_quiz` | Định lượng (liên tục) | Derived | Click loại 'quiz' tới mốc. | min 0, max 13032 |
| 21 | `clicks_subpage` | Định lượng (liên tục) | Derived | Click loại 'subpage' tới mốc. | min 0, max 4345 |
| 22 | `clicks_url` | Định lượng (liên tục) | Derived | Click loại 'url' tới mốc. | min 0, max 2134 |
| 23 | `mean_clicks_per_active_day` | Định lượng (liên tục) | Derived | total_clicks / n_days_active (0 nếu không có ngày hoạt động); lệch phải -> log1p. | min 0, max 221.2 |
| 24 | `days_since_last_activity` | Định lượng (liên tục) | Derived | Số ngày từ lần hoạt động cuối tới ngày mốc (lớn khi mất tương tác). | min 0, max 292 |

## Performance

| # | Biến | Kiểu | Nguồn gốc | Mô tả | Ví dụ / Khoảng |
|---|---|---|---|---|---|
| 25 | `n_assessments_submitted` | Định lượng (rời rạc) | Derived | Số bài đánh giá đã nộp (không banked) tới mốc. | min 0, max 14 |
| 26 | `mean_score_to_date` | Định lượng (liên tục) | Derived | Điểm trung bình các bài đã nộp tới mốc [0-100]; 0 nếu chưa nộp. | min 0, max 100 |
| 27 | `weighted_score_to_date` | Định lượng (liên tục) | Derived | Tổng score x weight/100 các bài đã nộp tới mốc. | min 0, max 200 |
| 28 | `not_submitted` | Nhị phân (chỉ báo) | Derived | 1 nếu sinh viên bỏ lỡ >=1 bài đã quá hạn nộp; tín hiệu nguy cơ. | min 0, max 1 |

## Temporal

| # | Biến | Kiểu | Nguồn gốc | Mô tả | Ví dụ / Khoảng |
|---|---|---|---|---|---|
| 29 | `date_registration` | Định lượng (liên tục) | Original | Ngày đăng ký tương đối so với ngày bắt đầu (có thể âm); 45 khuyết -> trung vị train. | min -322, max 167 |
| 30 | `date_unregistration` | Định lượng (liên tục) | Original | Ngày rút môn; NaN nếu không rút. Dùng để phân tích Withdrawn, không là đặc trưng. | min -365, max 444 |
| 31 | `module_presentation_length` | Định lượng (rời rạc) | Original | Độ dài môn-kỳ tính bằng ngày; dùng để quy đổi mốc sang ngày. | min 234, max 269 |

## Target (raw)

| # | Biến | Kiểu | Nguồn gốc | Mô tả | Ví dụ / Khoảng |
|---|---|---|---|---|---|
| 32 | `final_result` | Danh định (gốc) | Original | Kết quả gốc (Pass/Distinction/Fail/Withdrawn); nguồn của nhãn. | 4 unique |

## Target

| # | Biến | Kiểu | Nguồn gốc | Mô tả | Ví dụ / Khoảng |
|---|---|---|---|---|---|
| 33 | `at_risk` | Nhị phân (mục tiêu) | Derived | 1 nếu final_result thuộc {Fail, Withdrawn}, ngược lại 0. Cố định qua các mốc. | min 0, max 1 |
