# DSP391m – Group 1
## Step 29 — Data Dictionary (OULAD)

> **29 variables** across **7 source tables** · **3 feature groups + 1 target** · **13 original + 16 derived**

---

## 1. Variables by Feature Group

### 🔑 Identifiers

| # | Variable | Source Table | Type | Values / Order | Origin | Notes |
|---|----------|-------------|------|---------------|--------|-------|
| 1 | `id_student` | `studentInfo` | Nominal (ID) | Số nguyên định danh duy nhất mỗi sinh viên | Gốc | Không dùng làm đặc trưng; dùng làm khoá phân chia nhóm (GroupKFold) |
| 2 | `code_module` | `studentInfo` | Nominal (ID) | AAA | BBB | CCC | DDD | EEE | FFF | GGG | Gốc | Mã môn học; dùng kèm code_presentation làm khoá tổng hợp |
| 3 | `code_presentation` | `studentInfo` | Nominal (ID) | 2013B | 2013J | 2014B | 2014J | Gốc | Mã kỳ học; B = tháng 2, J = tháng 10 |

### 👤 Demographic

| # | Variable | Source Table | Type | Values / Order | Origin | Notes |
|---|----------|-------------|------|---------------|--------|-------|
| 4 | `gender` | `studentInfo` | Binary | F | M | Gốc | Mã hoá nhị phân: M=1, F=0 |
| 5 | `region` | `studentInfo` | Nominal | 13 vùng của Anh Quốc & Ireland (không có thứ bậc) | Gốc | Mã hoá One-Hot; 13 giá trị → 13 cột nhị phân |
| 6 | `highest_education` | `studentInfo` | Ordinal | 0: No Formal quals · 1: Lower Than A Level · 2: A Level or Equivalent · 3: HE Qualification · 4: Post Graduate Qualification | Gốc | Mã hoá thứ bậc 0–4 theo thứ tự trình độ tăng dần |
| 7 | `imd_band` | `studentInfo` | Ordinal | 0: 0-10% · 1: 10-20 · 2: 20-30% · 3: 30-40% · 4: 40-50% · 5: 50-60% · 6: 60-70% · 7: 70-80% · 8: 80-90% · 9: 90-100% | Gốc | Index of Multiple Deprivation – tỉ lệ nghèo đói theo vùng. Có 1111 giá trị khuyết → điền 'Unknown' |
| 8 | `age_band` | `studentInfo` | Ordinal | 0: 0-35 · 1: 35-55 · 2: 55<= | Gốc | Mã hoá thứ bậc 0–2 theo độ tuổi tăng dần |
| 9 | `disability` | `studentInfo` | Binary | N | Y | Gốc | Mã hoá nhị phân: Y=1, N=0 |
| 10 | `num_of_prev_attempts` | `studentInfo` | Numeric (discrete) | Nguyên, min=0, max=6 | Gốc | Số lần học lại; cần kiểm tra ngoại lai |
| 11 | `studied_credits` | `studentInfo` | Numeric (discrete) | Nguyên, min=30, max=655 | Gốc | Tín chỉ đăng ký; phân phối lệch phải |
| 12 | `date_registration` | `studentRegistration` | Numeric (continuous) | Số ngày tương đối so với ngày bắt đầu môn (có thể âm) | Gốc | Ngày âm = đăng ký trước khi môn bắt đầu |
| 13 | `date_unregistration` | `studentRegistration` | Numeric (continuous) | Số ngày; NaN nếu không rút môn | Gốc | Dùng để tạo biến chỉ báo is_withdrawn; bản thân cột này không đưa vào đặc trưng |

### 📊 Engagement (VLE)

| # | Variable | Source Table | Type | Values / Order | Origin | Notes |
|---|----------|-------------|------|---------------|--------|-------|
| 14 | `total_clicks` | `studentVle (phái sinh)` | Numeric (continuous) | Tổng sum_click của sinh viên tới mốc t | Phái sinh | Tổng hợp từ studentVle theo (id_student, code_module, code_presentation); phân phối lệch phải → log1p |
| 15 | `n_days_active` | `studentVle (phái sinh)` | Numeric (discrete) | Số ngày có ít nhất 1 lượt tương tác tới mốc t | Phái sinh | Đếm distinct(date) nhóm theo sinh viên–môn–kỳ |
| 16 | `clicks_forumng` | `studentVle (phái sinh)` | Numeric (continuous) | Tổng click loại 'forumng' tới mốc t | Phái sinh | Một cột cho mỗi activity_type; phân phối lệch phải |
| 17 | `clicks_oucontent` | `studentVle (phái sinh)` | Numeric (continuous) | Tổng click loại 'oucontent' tới mốc t | Phái sinh | Tương tự clicks_forumng |
| 18 | `clicks_resource` | `studentVle (phái sinh)` | Numeric (continuous) | Tổng click loại 'resource' tới mốc t | Phái sinh | Tương tự clicks_forumng |
| 19 | `clicks_homepage` | `studentVle (phái sinh)` | Numeric (continuous) | Tổng click loại 'homepage' tới mốc t | Phái sinh | Tương tự clicks_forumng |
| 20 | `clicks_oucollaborate` | `studentVle (phái sinh)` | Numeric (continuous) | Tổng click loại 'oucollaborate' tới mốc t | Phái sinh | Tương tự clicks_forumng |
| 21 | `clicks_quiz` | `studentVle (phái sinh)` | Numeric (continuous) | Tổng click loại 'quiz' tới mốc t | Phái sinh | Tương tự clicks_forumng |
| 22 | `clicks_subpage` | `studentVle (phái sinh)` | Numeric (continuous) | Tổng click loại 'subpage' tới mốc t | Phái sinh | Tương tự clicks_forumng |
| 23 | `clicks_url` | `studentVle (phái sinh)` | Numeric (continuous) | Tổng click loại 'url' tới mốc t | Phái sinh | Tương tự clicks_forumng |

### 📝 Performance (Assessment)

| # | Variable | Source Table | Type | Values / Order | Origin | Notes |
|---|----------|-------------|------|---------------|--------|-------|
| 24 | `mean_score_to_date` | `studentAssessment (phái sinh)` | Numeric (continuous) | Trung bình điểm các bài nộp tới mốc t, [0–100] | Phái sinh | Chỉ tính bài có date_submitted ≤ ngưỡng mốc; NaN nếu chưa nộp bài nào |
| 25 | `n_assessments_submitted` | `studentAssessment (phái sinh)` | Numeric (discrete) | Số bài đánh giá đã nộp tới mốc t | Phái sinh | Đếm bài có is_banked=0 và date_submitted ≤ ngưỡng |
| 26 | `not_submitted` | `studentAssessment (phái sinh)` | Binary | 0 | 1 | Phái sinh | Biến chỉ báo: 1 nếu sinh viên có ít nhất 1 bài chưa nộp tới mốc t; tín hiệu nguy cơ quan trọng |
| 27 | `weighted_score_to_date` | `studentAssessment (phái sinh)` | Numeric (continuous) | Tổng (score × weight/100) của các bài đã nộp tới mốc t | Phái sinh | Tính theo weight từ assessments.csv |

### 🎯 Target

| # | Variable | Source Table | Type | Values / Order | Origin | Notes |
|---|----------|-------------|------|---------------|--------|-------|
| 28 | `final_result` | `studentInfo` | Nominal (raw) | Pass | Distinction | Fail | Withdrawn | Gốc | Biến gốc; chỉ dùng để tạo nhãn at_risk |
| 29 | `at_risk` | `Phái sinh từ final_result` | Binary (Target) | 0: not-at-risk (Pass, Distinction) · 1: at-risk (Fail, Withdrawn) | Phái sinh | Biến mục tiêu chính thức theo biên bản thống nhất nhóm |

---

## 2. Summary by Feature Group

| Feature Group | Count | Original | Derived |
|---|---|---|---|
| 🔑 Identifiers | 3 | 3 | 0 |
| 👤 Demographic | 10 | 10 | 0 |
| 📊 Engagement (VLE) | 10 | 0 | 10 |
| 📝 Performance (Assessment) | 4 | 0 | 4 |
| 🎯 Target | 2 | 1 | 1 |

---

## 3. Encoding Reference

All encoders are **fit on training set only** and applied (transform) to both train and test sets.

| Variable | Type | Encoding Method |
|----------|------|----------------|
| `id_student` | Nominal (ID) | No encoding — used as group key only (GroupKFold) |
| `code_module` | Nominal (ID) | No encoding — used as group key only (GroupKFold) |
| `code_presentation` | Nominal (ID) | No encoding — used as group key only (GroupKFold) |
| `gender` | Binary | Direct 0/1 mapping (e.g. M=1, F=0 / Y=1, N=0) |
| `region` | Nominal | OneHotEncoder → one binary column per category |
| `highest_education` | Ordinal | OrdinalEncoder → integer 0..N-1 per defined order |
| `imd_band` | Ordinal | OrdinalEncoder → integer 0..N-1 per defined order |
| `age_band` | Ordinal | OrdinalEncoder → integer 0..N-1 per defined order |
| `disability` | Binary | Direct 0/1 mapping (e.g. M=1, F=0 / Y=1, N=0) |
| `num_of_prev_attempts` | Numeric (discrete) | StandardScaler (fit on train only); check for outliers |
| `studied_credits` | Numeric (discrete) | StandardScaler (fit on train only); check for outliers |
| `date_registration` | Numeric (continuous) | StandardScaler (fit on train only); log1p if right-skewed |
| `date_unregistration` | Numeric (continuous) | StandardScaler (fit on train only); log1p if right-skewed |
| `total_clicks` | Numeric (continuous) | StandardScaler (fit on train only); log1p if right-skewed |
| `n_days_active` | Numeric (discrete) | StandardScaler (fit on train only); check for outliers |
| `clicks_forumng` | Numeric (continuous) | StandardScaler (fit on train only); log1p if right-skewed |
| `clicks_oucontent` | Numeric (continuous) | StandardScaler (fit on train only); log1p if right-skewed |
| `clicks_resource` | Numeric (continuous) | StandardScaler (fit on train only); log1p if right-skewed |
| `clicks_homepage` | Numeric (continuous) | StandardScaler (fit on train only); log1p if right-skewed |
| `clicks_oucollaborate` | Numeric (continuous) | StandardScaler (fit on train only); log1p if right-skewed |
| `clicks_quiz` | Numeric (continuous) | StandardScaler (fit on train only); log1p if right-skewed |
| `clicks_subpage` | Numeric (continuous) | StandardScaler (fit on train only); log1p if right-skewed |
| `clicks_url` | Numeric (continuous) | StandardScaler (fit on train only); log1p if right-skewed |
| `mean_score_to_date` | Numeric (continuous) | StandardScaler (fit on train only); log1p if right-skewed |
| `n_assessments_submitted` | Numeric (discrete) | StandardScaler (fit on train only); check for outliers |
| `not_submitted` | Binary | Direct 0/1 mapping (e.g. M=1, F=0 / Y=1, N=0) |
| `weighted_score_to_date` | Numeric (continuous) | StandardScaler (fit on train only); log1p if right-skewed |
| `final_result` | Nominal (raw) | Not used directly — mapped to `at_risk` binary target |
| `at_risk` | Binary (Target) | Target variable — no encoding applied |

---

## 4. Target Variable Definition

```python
# Derived from final_result in studentInfo.csv
df['at_risk'] = df['final_result'].isin(['Fail', 'Withdrawn']).astype(int)
# 0 = not-at-risk  (Pass, Distinction)
# 1 = at-risk       (Fail, Withdrawn)
```

> **Class imbalance note:** The at-risk class is the minority class.
> Evaluation must use PR-AUC and Recall, not accuracy.
> Resampling strategies (SMOTE, ADASYN, class-weight) to be applied on training set only.

---

*DSP391m – Group 1 – Step 29 – An (Documentation Lead)*