**DSP391m Project**

# Phát hiện sớm sinh viên có nguy cơ học tập kém bằng học máy có khả năng giải thích trên bộ dữ liệu OULAD

**by**

Trần Bảo Phúc, Phạm Minh Đức, Phan Vinh Khoa,
Nguyễn Thanh Bình, Nguyễn Vũ An, Lã Quang Thiên Sơn

Nhóm 1, Sinh viên Đại học FPT
Giảng viên hướng dẫn: Nguyễn Thị Hoàng Yên

> Tài liệu này tuân theo **Data Science Capstone Project Template** (14 mục). Mọi con số truy được về `reports/tables/*.csv` (không gõ tay). Bản báo cáo học thuật dạng IEEE: `paper/main.pdf`.

---

## Tóm tắt (Abstract)

Đồ án xây dựng một hệ thống phát hiện sớm sinh viên có nguy cơ trượt hoặc bỏ học trên bộ dữ liệu OULAD, với ba yêu cầu song hành: dự báo *theo thời gian* tại sáu mốc tiến độ khóa học, *giải thích được* cho giáo viên, và *trung thực* về giới hạn. Toàn bộ quy trình được thiết kế chống rò rỉ dữ liệu: chia dữ liệu theo sinh viên và đóng băng, cắt đặc trưng theo mốc thời gian, và mọi thống kê chỉ học trên tập huấn luyện. Năm thuật toán được so tuyển; XGBoost được chọn với recall 0,930 tại cuối khóa, thứ hạng đã được kiểm định thống kê bằng Friedman và Wilcoxon-Holm.

Phát hiện trung tâm là *hiệu ứng quần thể*. Khi chấm điểm trên toàn bộ danh sách ghi danh, kết quả cảnh báo sớm bị thổi phồng bởi những sinh viên đã rút khỏi khóa học; trên quần thể *còn theo học*, tức nhóm mà giáo viên thật sự có thể can thiệp, mô hình chỉ đạt chuẩn tin cậy (recall và PR-AUC đều từ 0,80) ở cuối khóa. Khoảng cách giữa hai quần thể có khoảng tin cậy 95% loại trừ 0 ở mọi mốc, nghĩa là khác biệt có ý nghĩa thống kê. Giải thích của mô hình ổn định qua các lần chạy và dựa trên hành vi học tập, cụ thể là thời gian im lặng trên hệ thống và điểm tích lũy, chứ không dựa trên nhân khẩu học.

Báo cáo trình bày đầy đủ chuỗi công việc từ thu thập, làm sạch, phân tích khám phá, mô hình hóa, đánh giá, đến diễn giải kết quả và khuyến nghị hành động, kèm phần giới hạn nêu thẳng những điểm yếu mà một hội đồng khắt khe sẽ chất vấn.

---

## 1. Project Title (Tên đề tài)

Phát hiện sớm sinh viên có nguy cơ học tập kém (at-risk) theo thời gian bằng học máy có khả năng giải thích, đánh giá kép theo quần thể, trên bộ dữ liệu OULAD.

## 2. Team Members (Thành viên nhóm)

| Thành viên | Vai trò (dự kiến) |
|---|---|
| Trần Bảo Phúc | Nhóm trưởng, điều phối |
| Phạm Minh Đức | Dữ liệu & tiền xử lý |
| Phan Vinh Khoa | Mô hình & đánh giá |
| Nguyễn Thanh Bình | XAI (SHAP/LIME) |
| Nguyễn Vũ An | EDA & trực quan hóa |
| Lã Quang Thiên Sơn | Báo cáo & văn liệu |

Tất cả thành viên đều là sinh viên Đại học FPT. *(Phân công chi tiết theo `final_exl_4.xlsx` / `Model_Task_Work_Division.docx`.)*

## 3. Introduction and Background (Giới thiệu và Bối cảnh)

**Objective (Mục tiêu).** Xây dựng hệ thống dự báo nhị phân `at_risk` = {Fail, Withdrawn} tại 6 mốc tiến độ khóa học (10-100%), có khả năng giải thích, để nhà trường phát hiện và hỗ trợ sinh viên **trước** khi quá muộn.

**Motivation (Động lực).** Đào tạo trực tuyến/từ xa có tỷ lệ trượt và bỏ học cao. Giáo viên thiếu công cụ biết **ai** cần hỗ trợ và **vào lúc nào**. Can thiệp cuối kỳ gần như vô ích; can thiệp sớm cần dự báo đáng tin và giải thích được, để hành động đúng người và không gắn nhãn oan.

**Background (Bối cảnh).** OULAD là bộ dữ liệu học tập mở của The Open University (Anh): 32.593 lượt ghi danh, 28.785 sinh viên, 22 module-presentation, ~10,6 triệu dòng clickstream. Nhãn `at_risk` chiếm 52,8% (đa số nhẹ, tỷ lệ mất cân bằng 1,12). Phạm vi: dự báo theo thời gian, có giải thích, đánh giá công bằng. Ngoài phạm vi: dự báo điểm chi tiết, can thiệp tự động.

## 4. Literature Review (Tổng quan tài liệu)

| Nghiên cứu | Đóng góp | Khoảng trống dự án lấp |
|---|---|---|
| Tomasevic et al. 2020 | So sánh thuật toán (module DDD) | Bỏ dòng missing (loại chính sinh viên cần cảnh báo); split mức dòng; thiếu boosting |
| Adnan et al. 2021 | Dự báo theo thời gian 20-100% | Không tách sinh viên đã rút; không group-aware split; không CI |
| Alamri & Alharbi 2021; Gunasekara & Saarela 2025 | XAI trong giáo dục | Giải thích chỉ đánh giá định tính, thiếu baseline ngẫu nhiên |

**Gap tổng hợp:** không nghiên cứu nào cùng lúc (a) time-aware, (b) XAI định lượng có baseline, (c) tách quần thể đánh giá, (d) định lượng bất định. Đây là đóng góp của dự án (chi tiết `paper/main.tex` §II).

## 5. Data Description (Mô tả dữ liệu)

Dữ liệu là nền tảng của cả đồ án, nên mục này trình bày rõ ba khía cạnh: nguồn gốc và lý do lựa chọn, kích thước cùng định dạng, và danh mục đặc trưng. Phần nguồn cũng thẳng thắn đánh giá câu hỏi thường bị chất vấn nhất là có cần thu thập từ nhiều nguồn hơn hay không.

### Source (Nguồn), và đánh giá đa nguồn trung thực

**Dùng gì ban đầu và tại sao.** Dự án khởi đầu bằng **OULAD** vì: (1) đúng bài toán, có đủ 3 loại tín hiệu (hành vi VLE, kết quả đánh giá, nhân khẩu học); (2) chuẩn ngành, giấy phép CC-BY 4.0, snapshot cố định → tái lập và so sánh được với văn liệu; (3) quy mô đủ lớn để kiểm định thống kê.

**Thu thập là tích hợp đa nguồn thật sự.** OULAD gồm **7 bảng quan hệ** từ **3 hệ thống vận hành** khác nhau:

| Hệ thống nguồn | Bảng | Tín hiệu |
|---|---|---|
| Student Information System | `studentInfo`, `studentRegistration` | nhân khẩu học, ngày ghi danh/rút |
| VLE (Moodle) | `studentVle`, `vle` | 10,6 triệu dòng clickstream theo ngày |
| Assessment platform | `studentAssessment`, `assessments` | điểm, ngày nộp, trọng số |
| Course catalog | `courses` | độ dài module-presentation |

`src/data/build_master_table.py` join 3 hệ thống này thành một bảng phân tích (một dòng / lượt ghi danh), kiểm tra số dòng trước-sau mỗi join (giữ đúng 32.593 dòng, không trùng khóa). Đây chính là kỹ năng "collect from databases" mà đề cương yêu cầu.

**Có cần crawl/API thêm không? (đã cân nhắc kỹ).** Không, vì OULAD **ẩn danh hoàn toàn**, student ID là số thay thế, module code (AAA-GGG) và presentation code (2013J) là bí danh → **không có khóa nối thế giới thực**, dữ liệu crawl thêm không join được ở mức dòng, chỉ thêm bối cảnh chứ không thêm giá trị dự báo. Sau khi xây xong và đối chiếu lại với slide, kết luận: yêu cầu "đa nguồn" đã thỏa ở mức **tích hợp**; **acquisition** từ nguồn ngoài là hướng mở nhưng bị ẩn danh hóa giới hạn. Nếu cần minh chứng kỹ năng scraping, có thể bổ sung một script kéo **dữ liệu bối cảnh** (ghi rõ không dùng để train).

### Size and Format (Kích thước và định dạng)

7 file CSV gốc (khóa MD5), ~10,6 triệu dòng clickstream; sau ETL → bảng master 32.593 dòng × 33 đặc trưng; 6 lát cắt thời gian (t=10/20/40/60/80/100%).

### Features (Đặc trưng)

28 đặc trưng thô, 3 nhóm → 49 cột sau mã hóa:

| Nhóm | Ví dụ | Kiểu | Xử lý |
|---|---|---|---|
| Hành vi VLE (13) | `days_since_last_activity`, `total_clicks`, clicks theo 8 loại | numeric | log1p + StandardScaler |
| Kết quả đánh giá (4) | `weighted_score_to_date`, `n_assessments_submitted`, `not_submitted` | numeric/indicator | scaler/passthrough |
| Nhân khẩu học & bối cảnh (11) | `highest_education`, `imd_band`, `code_module`, `gender` | ordinal/nominal/binary | ordinal/one-hot |

Nhãn: `at_risk` ∈ {0,1}. *(Nguồn: `src/features/preprocessing.py`.)*

## 6. Data Cleaning and Preprocessing (Làm sạch & tiền xử lý)

| Vấn đề | Xử lý | Bằng chứng |
|---|---|---|
| **Trùng lặp** 787.170 dòng (7,4%) `studentVle` | Giữ + cộng dồn có tài liệu (không phân biệt được log-đúp với lặp hợp lệ); ghi nhận rủi ro over-count là limitation | `paper` §VI |
| **Lỗi nhãn banked** 78 dòng (0,24%) | Bài "banked" từ kỳ trước bị tính đến hạn nhưng chưa nộp → sửa `not_submitted`; pin bằng regression test | `tests/` |
| **Missing values** | Điểm thiếu → tín hiệu "chưa nộp" tường minh (không xóa dòng); impute bằng thống kê **fit trên train** | `preprocessing.py` |
| **Outliers** | Clickstream lệch phải → `log1p`; đuôi nặng winsorize [p1,p99] ngưỡng train (không xóa dòng nào) | `data_quality_profile.csv` |
| **Inconsistency** | Chuẩn hóa text categorical | `build_master_table.py` |
| **Normalization/scaling** | StandardScaler numeric; ordinal/one-hot categorical → 49 cột; **chỉ fit train** | `preprocessing.py` |

Thứ tự nghiêm ngặt: split → missing → outliers → encoding/scaling → resampling; mọi thống kê fit trên train. 21 test tự động phải PASS trước mọi bước mô hình.

## 7. Exploratory Data Analysis (EDA)

Đầy đủ 5 thành phần khung EDA, dùng **matplotlib + seaborn** (`src/eda/`):

- **Descriptive statistics:** mean/median/mode/std (`univariate_numeric.csv`).
- **Phân phối:** histogram+KDE (`univariate_hist_kde.png`), boxplot (`univariate_boxplots.png`), tần suất categorical.
- **Correlation:** Pearson (`corr_pearson.png`), Spearman (`corr_spearman.png`), với nhãn (`corr_with_target.png`), không biến nào chạm ngưỡng rò rỉ |r|≥0,95.
- **Univariate/bivariate/multivariate:** effect size (`bivariate_numeric_tests.csv`), scatter theo cặp (`bivariate_scatter_pairs.png`).
- **Time-aware EDA:** quỹ đạo theo mốc, suy giảm hoạt động của sinh viên rút (`withdrawn_activity_decay.png`).

**Phát hiện chính:** (1) hành vi + kết quả đánh giá áp đảo tín hiệu, nhân khẩu học yếu → cảnh báo dựa trên hành vi; (2) sinh viên rút sớm gần như 0 click → gốc của hiệu ứng dual-cohort; (3) at-risk 52,8% → cân bằng lớp là câu hỏi độ bền.

## 8. Methodology (Phương pháp luận)

**Model Selection (Chọn mô hình).** Benchmark 5 thuật toán phủ 3 họ: Logistic Regression (tuyến tính), Random Forest (bagging), XGBoost & LightGBM (boosting), ANN/MLP (phi tuyến), để kết quả không phải artefact của một inductive bias. Metric chính: **recall** trên lớp at-risk (chi phí bỏ sót > báo nhầm).

**Data Splitting Strategy (Chia dữ liệu).** Split **group-aware, stratified 20% hold-out theo `id_student`** (sinh viên không xuyên train/test), đóng băng vào git (`test_student_ids.csv`): 26.104 train / 6.489 test / 5.756 sinh viên test. Xác minh 0 overlap, giữ tỷ lệ lớp ở cả 6 mốc.

**Feature Engineering and Selection (Kỹ thuật đặc trưng).**
- *Creation:* `build_engagement_features.py` + `build_performance_features.py` tạo đặc trưng phái sinh từ 10,6M dòng clickstream (không có sẵn trong OULAD).
- *Transformation:* log1p, winsorize, scaling, ordinal/one-hot → 49 cột.
- *Selection:* xếp hạng SHAP + ablation → top 5 đặc trưng đủ (§11).

## 9. Model Development (Phát triển mô hình)

**Model Architecture (Kiến trúc).** Mỗi mô hình là một bundle self-contained: ColumnTransformer (tiền xử lý fit trên train) + estimator, lưu qua joblib theo `{model}_t{t}.joblib`. XGBoost cấu hình near-default (hist tree), ANN 2 lớp ẩn (64,32) early stopping.

**Training Procedure (Quy trình huấn luyện).** Với mỗi (mốc t, mô hình): `load_checkpoint_split → make_X_y → preprocess (fit train) → SMOTE chỉ trên train fold → fit → evaluate trên test niêm phong → persist`. Atomic write, resumable (`src/modeling/train.py`). 5 mô hình × 6 mốc = 30 bundle.

## 10. Model Evaluation and Fine-Tuning (Đánh giá & tinh chỉnh)

**Evaluation Metrics.** Đầy đủ accuracy/precision/recall/F1 + PR-AUC/ROC-AUC/Brier/balanced-acc (`model_metrics.csv`). Benchmark @t=100%:

| Mô hình | Recall | F1 | PR-AUC | ROC-AUC | Brier |
|---|---|---|---|---|---|
| **XGBoost** ← chọn | **0,9298** | 0,9503 | 0,9902 | 0,9872 | 0,0391 |
| LightGBM | 0,9295 | 0,9511 | 0,9913 | 0,9889 | 0,0368 |
| ANN | 0,9259 | 0,9477 | 0,9897 | 0,9868 | 0,0404 |
| Logistic Reg. | 0,9171 | 0,9464 | 0,9890 | 0,9857 | 0,0414 |
| Random Forest | 0,9165 | 0,9466 | 0,9896 | 0,9868 | 0,0405 |

Chọn XGBoost: recall cao nhất + TreeExplainer chính xác cho SHAP.

**Hyperparameter Tuning.** `tools/tune_models.py`, **RandomizedSearchCV** (40 cấu hình, StratifiedGroupKFold, SMOTE trong fold) cho xgb/lgbm. Kết quả (`tuning_results.csv`): cải thiện PR-AUC biên, **không cải thiện recall** → giữ near-default; tín hiệu đặc trưng (không phải cấu hình) là ràng buộc chính.

**Cross-Validation.** 5-fold × 5-seed = 25 fit/mô hình, StratifiedGroupKFold theo sinh viên, preprocessing fit lại trong mỗi fold. XGBoost recall CV = **0,9309 ± 0,0047** (`cv_summary.csv`); xếp hạng CV trùng held-out. Friedman p<0,05 + Wilcoxon-Holm xác nhận XGBoost dẫn recall.

**Overfitting/Underfitting & Bias-Variance.** `tools/make_bias_variance.py`:
- Khoảng cách train-test theo mốc **thu hẹp đều** 0,125 (t=10%) → **0,057** (t=100%) → variance giảm dần, không overfit (`bias_variance_gap.csv`).
- Learning curve: train ≈ 1,0, CV hội tụ ~0,93 (`bias_variance_learning_curve.png`).
- Underfitting = khoảng cách vài điểm giữa Logistic Regression (bias cao) và boosting.

## 11. Results Interpretation and Visualization (Diễn giải & trực quan hóa)

Mục này diễn giải kết quả theo hướng hành động được cho giáo viên, không dừng lại ở con số. Trước hết là câu hỏi vì sao một sinh viên bị gắn cờ, thông qua độ quan trọng của đặc trưng. Tiếp theo là độ tin cậy của chính giải thích đó, đo bằng độ ổn định so với một mốc ngẫu nhiên. Cuối cùng là ba phát hiện mang tính chiến lược có ý nghĩa triển khai trực tiếp: hiệu ứng quần thể, luật nền đơn giản, và tính tiết kiệm đặc trưng.

**Feature importance (SHAP + LIME).** Top SHAP: `days_since_last_activity` > `weighted_score_to_date` > đặc trưng nộp bài (`xai_shap_importance.csv`); hướng khớp trực giác giáo viên. Ổn định: Jaccard top-10 qua 5 seed = 0,69; Spearman 0,97, vượt phân vị 99 mốc ngẫu nhiên (mean 0,119, p99 0,333). SHAP vs LIME Jaccard = 0,43.

**Uncertainty.** Bootstrap CI mức sinh viên (`bootstrap_ci.csv`) + `cv_uncertainty.png` (mean±std qua 25 fit).

**Heatmap.** `corr_pearson.png` / `corr_spearman.png` + confusion matrix (`confusion_default_t100.png`).

**Calibration.** ECE 0,018 (t=100) → 0,042 (t=20); MCE tới 0,16 (`calibration_metrics.csv`) → xác suất dùng được làm dải rủi ro, hạn chế đọc literal >0,85.

**Ba phát hiện chiến lược (insights):**

1. **Dual-cohort**, recall cao ở mốc sớm phần lớn do nhận diện sinh viên **đã rút** (kết cục đã xảy ra). Trên quần thể **còn theo học** (can thiệp được), chỉ đạt chuẩn ≥0,80 ở cuối khóa:

| Mốc | Recall toàn bộ | Recall còn theo học | Khoảng cách |
|---|---|---|---|
| 40% | 0,811 | 0,678 | 0,133 |
| 100% | 0,930 | 0,841 | 0,089 |

Khoảng cách có CI loại trừ 0 ở mọi mốc (`bootstrap_ci.csv`).

2. **Rule-based baseline**, luật 2 đặc trưng đạt recall **0,999** @t=10% (vượt XGBoost 0,719, vì sinh viên rút bị gắn cờ tầm thường); nhưng cuối khóa XGBoost (0,930) vượt luật (0,855) → **chính sách lai**: luật sàng lọc sớm, ML từ giữa khóa (`rule_baseline.csv`).

3. **Ablation**, chỉ **5 đặc trưng** đạt recall 0,932 = mô hình đầy đủ 0,930 → triển khai & giải thích chỉ cần 5 đặc trưng (`ablation_results.csv`).

## 12. Conclusion and Recommendations (Kết luận & Khuyến nghị)

**Key findings.** XGBoost recall 0,930 @t=100% (đã kiểm định); mốc tin cậy: toàn quần thể từ t=40% (ranh giới)/t=60% (vững), còn-theo-học chỉ t=100%; giải thích ổn định (Spearman 0,97); bền cân bằng lớp (Δrecall ≤ 0,007).

**Actionable recommendations.**
1. Cảnh báo dựa trên im lặng VLE: nhắc khi `days_since_last_activity` > 14 ngày, kể cả trước khi có điểm.
2. Chỉ can thiệp trên quần thể còn theo học (dashboard lọc sẵn), đúng nhóm, tránh ảo tưởng recall.
3. Chính sách lai: t<40% dùng luật inactivity; t≥40% dùng XGBoost.
4. Chọn ngưỡng theo chính sách: recall≥0,90 (ngưỡng 0,86, precision 0,993) khi ưu tiên không bỏ sót.
5. Triển khai gọn 5 đặc trưng, đơn giản pipeline & giải thích.

**Implementation & Monitoring.**

| Khía cạnh | Chiến lược |
|---|---|
| Data drift | Theo dõi phân phối `days_since_last_activity`/`weighted_score_to_date` hàng tuần; cảnh báo lệch >2σ so với train |
| Performance drift | Đo lại recall/precision trên quần thể còn theo học mỗi kỳ; retrain khi recall giảm >5pp |
| Fairness | Đo lại khoảng cách recall theo IMD/region/disability mỗi kỳ (ngưỡng 10pp) |
| Calibration | Theo dõi ECE; recalibrate (Platt/Isotonic) nếu ECE >0,05 |
| Retrain cadence | Theo presentation, split đóng băng mới, giữ quy trình leakage-safe |
| Human-in-the-loop | Mô hình đề xuất, giáo viên quyết định |

**Giới hạn học thuật (nêu thẳng).** Nhóm em nêu bốn giới hạn mà một hội đồng khắt khe chắc chắn sẽ hỏi, và trả lời thẳng thay vì né tránh. Thứ nhất, nhãn `at_risk` gộp hai hiện tượng khác nhau: sinh viên *rút lui* (nhận diện dễ qua hành vi im lặng) và sinh viên *học tới cùng nhưng trượt* (khó hơn nhiều); ca dễ có thể lấn át và làm kết quả trông tốt hơn thực chất, nên tách Fail và Withdrawn là hướng phát triển ưu tiên. Thứ hai, đặc trưng mạnh nhất là số ngày im lặng gần như là hệ quả cơ học của việc đã rút, nên một phần hiệu năng là *đọc ra* kết cục chứ không phải *dự báo* nó; đây chính là lý do nhóm em báo cáo kép và coi con số trên quần thể còn theo học (0,841) là con số trung thực. Thứ ba, phân tích còn-theo-học chấm lại mô hình huấn luyện trên toàn roster, chưa huấn luyện riêng cho từng mốc. Thứ tư, kiểm định Friedman và Wilcoxon áp trên các fold chồng lấn của một dataset duy nhất, nên p-value nên được hiểu là cận trên của độ tin, không phải một suy luận tổng thể mạnh.

**Reflection & Future work.** Recall 0,930 phản ánh chất lượng OULAD (dataset đồng nhất một tổ chức); triển khai thực tế từ nhiều LMS sẽ thấp hơn ~10-15pp, **cần nói rõ khi bảo vệ**. Hướng phát triển: (1) censoring theo mốc thành thiết kế chính; (2) tách Fail vs Withdrawn (competing risks); (3) kiểm chứng ngoài OULAD, feature điểm tôn trọng độ trễ chấm; (4) hình thức hóa chính sách lai rule/ML; (5) tùy chọn script crawl bối cảnh.

## 13. References (Tài liệu tham khảo)

*Danh sách khớp với bản báo cáo IEEE (`paper/main.pdf`, 37 tài liệu). Số trang cần rà lại trên IEEE Xplore/Google Scholar trước khi nộp cuối.*

**Bài toán, dữ liệu & lĩnh vực (learning analytics / EDM)**
1. Kuzilek J., Hlosta M., Zdrahal Z. (2017). *Open University Learning Analytics dataset.* Scientific Data, 4, 170171.
2. Tomasevic N., Gvozdenovic N., Vranes S. (2020). *An overview and comparison of supervised data mining techniques for student exam performance prediction.* Computers & Education, 143, 103676.
3. Adnan M. et al. (2021). *Predicting at-risk students at different percentages of course length for early intervention using machine learning models.* IEEE Access, 9, 7519-7539.
4. Wolff A., Zdrahal Z., Nikolov A., Pantucek M. (2013). *Improving retention: Predicting at-risk students by analysing clicking behaviour in a VLE.* LAK, 145-149.
5. Hlosta M., Zdrahal Z., Zendulka J. (2017). *Ouroboros: Early identification of at-risk students without models based on legacy data.* LAK, 6-15.
6. Romero C., Ventura S. (2010). *Educational data mining: A review of the state of the art.* IEEE Trans. SMC-C, 40(6), 601-618.
7. Romero C., Ventura S. (2013). *Data mining in education.* WIREs Data Mining and Knowledge Discovery, 3(1), 12-27.
8. Baker R. S. J. d., Yacef K. (2009). *The state of educational data mining in 2009: A review and future visions.* JEDM, 1(1), 3-17.
9. Webster J., Watson R. T. (2002). *Analyzing the past to prepare for the future: Writing a literature review.* MIS Quarterly, 26(2), xiii-xxiii.

**Mô hình & học máy**
10. Chen T., Guestrin C. (2016). *XGBoost: A scalable tree boosting system.* ACM SIGKDD, 785-794.
11. Ke G. et al. (2017). *LightGBM: A highly efficient gradient boosting decision tree.* NeurIPS, 3149-3157.
12. Breiman L. (2001). *Random forests.* Machine Learning, 45(1), 5-32.
13. Friedman J. H. (2001). *Greedy function approximation: A gradient boosting machine.* Annals of Statistics, 29(5), 1189-1232.
14. Hastie T., Tibshirani R., Friedman J. (2009). *The Elements of Statistical Learning*, 2nd ed. Springer.
15. Pedregosa F. et al. (2011). *Scikit-learn: Machine learning in Python.* JMLR, 12, 2825-2830.

**Mất cân bằng lớp**
16. Chawla N. V. et al. (2002). *SMOTE: Synthetic minority over-sampling technique.* JAIR, 16, 321-357.
17. He H., Bai Y., Garcia E. A., Li S. (2008). *ADASYN: Adaptive synthetic sampling approach for imbalanced learning.* IJCNN, 1322-1328.
18. He H., Garcia E. A. (2009). *Learning from imbalanced data.* IEEE Trans. KDE, 21(9), 1263-1284.
19. Fernandez A., Garcia S., Herrera F., Chawla N. V. (2018). *SMOTE for learning from imbalanced data: Progress and challenges, marking the 15-year anniversary.* JAIR, 61, 863-905.

**Đánh giá, kiểm định & hiệu chỉnh**
20. Demsar J. (2006). *Statistical comparisons of classifiers over multiple data sets.* JMLR, 7, 1-30.
21. Holm S. (1979). *A simple sequentially rejective multiple test procedure.* Scandinavian J. Statistics, 6(2), 65-70.
22. Bergstra J., Bengio Y. (2012). *Random search for hyper-parameter optimization.* JMLR, 13, 281-305.
23. Kohavi R. (1995). *A study of cross-validation and bootstrap for accuracy estimation and model selection.* IJCAI, 1137-1143.
24. Davis J., Goadrich M. (2006). *The relationship between precision-recall and ROC curves.* ICML, 233-240.
25. Saito T., Rehmsmeier M. (2015). *The precision-recall plot is more informative than the ROC plot on imbalanced datasets.* PLoS ONE, 10(3), e0118432.
26. Efron B., Tibshirani R. J. (1993). *An Introduction to the Bootstrap.* Chapman & Hall/CRC.
27. Niculescu-Mizil A., Caruana R. (2005). *Predicting good probabilities with supervised learning.* ICML, 625-632.
28. Guo C., Pleiss G., Sun Y., Weinberger K. Q. (2017). *On calibration of modern neural networks.* ICML, 1321-1330.

**Giải thích được (XAI) & công bằng**
29. Lundberg S. M., Lee S.-I. (2017). *A unified approach to interpreting model predictions.* NeurIPS, 4768-4777.
30. Lundberg S. M. et al. (2020). *From local explanations to global understanding with explainable AI for trees.* Nature Machine Intelligence, 2, 56-67.
31. Ribeiro M. T., Singh S., Guestrin C. (2016). *"Why should I trust you?" Explaining the predictions of any classifier.* ACM SIGKDD, 1135-1144.
32. Alamri H., Alharbi B. (2021). *Explainable student performance prediction models: A systematic review.* IEEE Access, 9, 33132-33143.
33. Gunasekara S., Saarela M. (2025). *Explainable AI in education: Techniques and qualitative assessment.* Applied Sciences, 15(3), 1239.
34. Guidotti R. et al. (2018). *A survey of methods for explaining black box models.* ACM Computing Surveys, 51(5), art. 93.
35. Adadi A., Berrada M. (2018). *Peeking inside the black-box: A survey on explainable AI (XAI).* IEEE Access, 6, 52138-52160.
36. Molnar C. (2022). *Interpretable Machine Learning*, 2nd ed. (christophm.github.io/interpretable-ml-book).
37. Mehrabi N. et al. (2021). *A survey on bias and fairness in machine learning.* ACM Computing Surveys, 54(6), art. 115.

## 14. Appendices (Phụ lục)

### A. Ma trận phủ yêu cầu 8 slide môn học

Ký hiệu: ✅ đủ · 🟡 nói rõ khi bảo vệ · ⛔ thiếu.

| Yêu cầu | Trạng thái | Mục |
|---|---|---|
| Problem / SMART / Methodology / Lit review / Timeline | ✅ | 3,4,8 |
| Thu thập đa nguồn (DB/API/scraping) | 🟡 | 5 (tích hợp 7 bảng/3 hệ thống) |
| Missing/outlier/inconsistency + normalization | ✅ | 6 |
| Descriptive stats + hist/KDE/box + Pearson/Spearman + uni/bi/multivariate + matplotlib/seaborn | ✅ | 7 |
| Nhiều thuật toán + justify | ✅ | 8 |
| Feature creation/selection/transformation | ✅ | 8 |
| Hyperparameter tuning (random search) | ✅ | 10 |
| Cross-validation (stratified) | ✅ | 10 |
| accuracy/precision/recall/F1 | ✅ | 10 |
| Overfitting/underfitting + bias-variance | ✅ | 10 |
| Interpretability + feature importance | ✅ | 11 |
| Visualize predictions/importance/uncertainty + heatmap | ✅ | 11 |
| Calibration | ✅ | 11 |
| Conclusion + actionable recommendations | ✅ | 12 |
| Implementation + monitoring | ✅ | 12 |
| Real-world implications + limitations | ✅ | 12 |
| Final report + citations + presentation | ✅ | `paper/main.pdf`, `reports/slides/` |
| Deployment (scalability/reliability) | 🟡 | 12 (thiết kế; chưa production) |

**Tổng:** 29/31 ✅, 2 🟡, 0 ⛔.

### B. Sản phẩm kèm theo

`paper/main.pdf` (IEEE) · `reports/final_report/` (báo cáo 7 mục EN) · `reports/slides/Task4_Slides_VI.pdf` · `reports/guide/SO_TAY_BAO_VE_VI.md` · `dashboard/app.py` · `ARCHITECTURE.md` · 50+ CSV · 38 hình 300 dpi · 21 test PASS.

### C. Tái lập

`bash tools/renumber.sh` → `python -m tools.build_paper` · Test: `pytest tests/` · Bias-variance: `python -m tools.make_bias_variance` · Bổ sung: `python -m tools.make_ds_supplement`.
