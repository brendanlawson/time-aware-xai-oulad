# Kế hoạch thuyết trình — TASK 3: Thu thập & Tiền xử lý dữ liệu

**Đề tài:** Time-Aware Explainable ML for Early At-Risk Student Prediction on OULAD
**Môn:** DSP391m — Đồ án Khoa học Dữ liệu · **Nhóm 1** · Đại học FPT · **GVHD:** Nguyễn Thị Hoàng Yến
**Phạm vi báo cáo:** Chương 3–4 (Thu thập, Làm sạch, Chuẩn hoá, Tách dữ liệu)

> Bản kế hoạch này là **storyboard** để dựng slide, không phải slide cuối cùng. Mỗi slide đã ghi sẵn
> nội dung theo công thức cô yêu cầu — **Làm gì · Vì sao · Kết quả đầu ra** — kèm **số liệu thật** trích
> từ `src/` và `reports/`, và **hình/bảng có sẵn** để chèn vào.

---

## A. Khung tổng thể

| Hạng mục | Quyết định |
|---|---|
| Thời lượng | **18–22 phút trình bày + 3–5 phút Q&A** |
| Số slide | **33 slide** (3 mở đầu · 28 nội dung — gồm **khối EDA 5 slide** · 2 kết) |
| Hình thức | **Cả nhóm chia 5 phần + khối EDA** (mỗi phần ≈ 2,5–3,5 phút; EDA ≈ 4 phút) |
| Thông điệp xuyên suốt | *"Chúng tôi biến 7 bảng OULAD thô (10,6 triệu dòng clickstream) thành **6 bộ dữ liệu theo mốc thời gian**, sạch — chống rò rỉ — tái lập được, sẵn sàng cho mô hình giải thích được."* |
| Nguyên tắc mỗi slide | 1 ý chính · tối đa 5 dòng chữ · ưu tiên số liệu & biểu đồ · luôn trả lời **Làm gì / Vì sao / Kết quả** |

### Phân công trình bày

| Người | Vai trò trong dự án | Phụ trách |
|---|---|---|
| **An** (Documentation Lead) | Báo cáo, tài liệu | Mở đầu (S1–S3) + Kết luận (S27–S28) |
| **Sơn** (Literature Review Lead) | Bối cảnh nghiên cứu | **Phần 1** — Xác định dữ liệu cần có (S4–S7) |
| **Phúc** (Implementation Lead) | Pipeline dữ liệu (`build_master_table`, engagement, performance) | **Phần 2** — Thu thập dữ liệu (S8–S11) |
| **Bình** (XAI Lead) | Phát hiện ngoại lai (handoff outliers) + phân tích EDA | **Phần 3** — Làm sạch (S12–S17) **+ Khối EDA** (S18–S22) |
| **Đức** (Modeling Lead) | `preprocessing.py` (Task 16–22), xử lý mất cân bằng | **Phần 4** — Chuẩn hoá & biến đổi (S23–S27) |
| **Khoa** (Methodology Lead) | Time-aware (`time_utils`, checkpoints), split harness | **Phần 5** — Tách train/test & chống rò rỉ (S28–S31) |

> ⚖️ **Lưu ý cân đối:** Bình giữ cả Làm sạch (6 slide) + EDA (5 slide) ≈ 11 slide / ~7 phút — phần dài nhất.
> EDA nối liền mạch sau Làm sạch (cùng chủ đề "chất lượng & hiểu dữ liệu"). Nếu muốn gọn hơn,
> có thể rút Phần 3 còn 4 slide (gộp S14+S15 và S15+S16) để Bình còn ~9 slide / ~6 phút.

---

## B. STORYBOARD CHI TIẾT (33 slide)

> Ký hiệu: 🟢 **Làm gì** · 🔵 **Vì sao** · 🟡 **Kết quả/đầu ra** · 📊 hình/bảng đề xuất · 🔗 nguồn trong repo · ✅ đầu việc của cô được phủ.

---

### MỞ ĐẦU — *An* (3 slide · ~2 phút)

**Slide 1 — Trang bìa**
- Tên đề tài, môn, Nhóm 1, danh sách thành viên + vai trò, GVHD, ngày báo cáo.
- 📊 logo FPT + 1 ảnh nền minh hoạ "early warning / learning analytics".

**Slide 2 — Mục lục & cách trình bày**
- 5 phần theo đúng Task 3: (1) Xác định dữ liệu → (2) Thu thập → (3) Làm sạch → (4) Chuẩn hoá & biến đổi → (5) Tách train/test.
- Nêu rõ: *"mỗi mục được trình bày theo Làm gì – Vì sao – Kết quả"* (ghi điểm với cô ngay từ đầu).
- 📊 sơ đồ 5 khối nối tiếp nhau.

**Slide 3 — Bức tranh tổng thể của pipeline (slide "neo")**
- 🟢 Một sơ đồ luồng: `7 bảng thô → gộp → master_raw (32.593×33) → cắt theo 6 mốc thời gian → tiền xử lý chống rò rỉ → train/test`.
- 🔵 Giúp người nghe luôn biết "đang ở đâu" — quay lại slide này ở đầu mỗi phần.
- 🟡 Đầu ra cuối: **6 bộ dữ liệu `dataset_t10…t100`** + tập test 20% cố định, **16/16 kiểm thử rò rỉ đạt**.
- 📊 dùng/ vẽ lại `reports/figures/preprocessing_sequence.png`. 🔗 `src/config.py` (`CHECKPOINTS=(10,20,40,60,80,100)`).

---

### PHẦN 1 — XÁC ĐỊNH DỮ LIỆU CẦN CÓ — *Sơn* (4 slide · ~3 phút)
> ✅ Phủ đầu việc **1.1 → 1.7**

**Slide 4 — Bài toán & mục tiêu đề tài** ✅1.1
- 🟢 Phát hiện **sớm** sinh viên có nguy cơ học kém trong môi trường học trực tuyến (VLE), và **giải thích được** mỗi dự đoán.
- 🔵 Ba khoảng trống của nghiên cứu trước: *opacity* (hộp đen), *lateness* (dự đoán quá muộn), *class imbalance*. Ba hướng time-aware + XAI + xử lý mất cân bằng chưa từng được tích hợp đồng thời trên OULAD.
- 🟡 Phạm vi dữ liệu của Task 3 phải phục vụ 3 câu hỏi RQ1 (dự đoán sớm), RQ2 (ổn định giải thích), RQ3 (mất cân bằng).
- 🔗 `README.md` §1–2.

**Slide 5 — Biến mục tiêu** ✅1.2
- 🟢 Bài toán **phân loại nhị phân**: `at_risk` suy ra từ `final_result`.
- 🔵 Gộp **Fail + Withdrawn = at-risk (1)** vs **Pass + Distinction = not-at-risk (0)** — gom theo "có cần can thiệp hay không", đúng mục tiêu cảnh báo sớm.
- 🟡 Phân bố thật: **at-risk 52,8%** (Fail 7.052 + Withdrawn 10.156 = 17.208) vs not-at-risk 47,2% (Pass 12.361 + Distinction 3.024 = 15.385). *Nhấn mạnh: 52,8% là số thật, không phải con số minh hoạ 68/32.*
- 📊 `reports/figures/target_distribution.png`. 🔗 `Target_Variable_Definition` (biên bản BB-B0-N1).

**Slide 6 — Ba nhóm dữ liệu đầu vào & vai trò** ✅1.3 ✅1.4
- 🟢 Ba nhóm đặc trưng:
  1. **Nhân khẩu học** (gender, region, highest_education, imd_band, age_band, disability, studied_credits, num_of_prev_attempts)
  2. **Tương tác/VLE** (clickstream — tổng/loại click, số ngày hoạt động…)
  3. **Kết quả đánh giá** (điểm bài nộp, số bài nộp, cờ chưa nộp).
- 🔵 Vai trò: nhân khẩu học = bối cảnh & phân tích **công bằng**; tương tác = **tín hiệu hành vi sớm**; kết quả = **bằng chứng năng lực**. (EDA sau này xác nhận hành vi/kết quả mạnh hơn hẳn nhân khẩu học.)
- 🟡 Bộ đặc trưng chia 3 nhóm rõ ràng → thuận tiện cho diễn giải SHAP/LIME theo nhóm.
- 📊 bảng 3 cột (Nhóm · Ví dụ biến · Vai trò).

**Slide 7 — Đơn vị quan sát, phạm vi & dữ liệu loại trừ** ✅1.5 ✅1.6 ✅1.7
- 🟢 **Đơn vị quan sát:** 1 dòng = **1 sinh viên–môn–kỳ** (khoá `code_module` × `code_presentation` × `id_student`).
- 🟢 **Phạm vi:** 32.593 bản ghi · 22 môn–kỳ · 7 bảng quan hệ · các kỳ 2013–2014 của Open University.
- 🟢 **Loại trừ:** bỏ cột định danh khỏi đặc trưng (`id_student`…); **không dùng `date_unregistration` làm đặc trưng** (rò rỉ tương lai + thiếu mang tính cấu trúc); bỏ `final_result` gốc sau khi đã tạo nhãn.
- 🔵 Tách đơn vị quan sát & loại trừ sớm để tránh **rò rỉ** và nhân bản dữ liệu.
- 🟡 Khung dữ liệu cố định: cùng một danh sách sinh viên dùng lại qua mọi mốc thời gian (Phương án A).
- 🔗 `src/features/preprocessing.py` (`ID_COLS`, `TARGET_COL`), `build_master_table.py`.

---

### PHẦN 2 — PHƯƠNG PHÁP THU THẬP DỮ LIỆU — *Phúc* (4 slide · ~3,5 phút)
> ✅ Phủ đầu việc **2.1 → 2.9**

**Slide 8 — Nguồn & loại dữ liệu** ✅2.1 ✅2.2
- 🟢 **Nguồn:** Open University Learning Analytics Dataset (OULAD), Kuzilek và cộng sự (2017) — `analyse.kmi.open.ac.uk/open_dataset` (+ mirror Kaggle).
- 🔵 Là **dữ liệu thứ cấp công khai**, đã **ẩn danh tại nguồn**, giấy phép **CC-BY 4.0** → đáp ứng đạo đức bằng trích dẫn đúng quy cách, không xử lý dữ liệu cá nhân nhạy cảm.
- 🟡 Phù hợp môi trường học thuật: hợp pháp, tái lập, không cần thu thập sơ cấp.
- 🔗 `docs/02_collection/Data_Source_License_Ethics`.

**Slide 9 — Cách thu thập & cấu trúc 7 bảng** ✅2.3 ✅2.4
- 🟢 Tải 7 CSV → đặt vào `data/raw/` → **xác minh toàn vẹn bằng MD5** (`data/data_manifest.txt`).
- 🟢 7 bảng: `studentInfo`, `courses`, `studentRegistration`, `studentVle` (**10.655.280** dòng), `vle`, `assessments`, `studentAssessment`.
- 🔵 Tách bảng nền (studentInfo) khỏi bảng nặng (studentVle) → xử lý bộ nhớ theo *chunk* (đọc 500k dòng/lần).
- 🟡 Dữ liệu thô được "đóng băng" + có checksum → mọi thành viên dùng đúng một bản.
- 📊 bảng liệt kê 7 file (tên · số dòng · vai trò). 🔗 `src/data/build_engagement_features.py` (`load_student_vle`).

**Slide 10 — Mối liên hệ giữa các bảng (lược đồ quan hệ)** ✅2.5
- 🟢 Khoá liên kết:
  - **(code_module, code_presentation, id_student)** nối studentInfo ↔ registration ↔ VLE-agg ↔ performance.
  - **id_site** nối `studentVle` ↔ `vle` (lấy loại hoạt động).
  - **id_assessment** nối `studentAssessment` ↔ `assessments` (lấy trọng số/hạn nộp).
- 🔵 Hiểu khoá là điều kiện để **gộp không nhân bản** (dùng `validate="many_to_one"`).
- 🟡 Một lược đồ ERD rút gọn — nền tảng cho bước gộp ở Phần 3.
- 📊 sơ đồ ERD 7 bảng + đường khoá. 🔗 `build_master_table.py` (`GROUP_COLS`, `PRESENTATION_KEY`).

**Slide 11 — Đánh giá nguồn: phù hợp · ưu điểm · hạn chế · rủi ro** ✅2.6 ✅2.7 ✅2.8 ✅2.9
- 🟢 Bảng 4 ô:
  - **Phù hợp (2.6):** có đủ 3 nhóm đặc trưng + **dấu thời gian** (`date`) → cho phép dự đoán *time-aware*; quy mô 32k đủ lớn.
  - **Ưu điểm (2.7):** chuẩn benchmark quốc tế, ẩn danh, tái lập, miễn phí.
  - **Hạn chế (2.8):** dữ liệu thứ cấp 1 trường (khó tổng quát hoá); click chỉ là *số đếm*, không có nội dung; kỳ 2013–2014.
  - **Rủi ro (2.9):** mất cân bằng nhẹ; thiếu mang tính cấu trúc; phân phối lệch phải mạnh; **đa cộng tuyến**; nguy cơ **rò rỉ thời gian** nếu không cắt mốc.
- 🟡 Mỗi rủi ro đã có phương án xử lý ở Phần 3–5 (báo trước để tạo mạch).
- 🔗 `docs/02_collection/Data_Collection_Methods`, Report 2 §3.1.

---

### PHẦN 3 — LÀM SẠCH DỮ LIỆU — *Bình* (6 slide · ~4 phút)
> ✅ Phủ đầu việc **3.1 → 3.14**

**Slide 12 — Kiểm tra tổng quan dữ liệu thô** ✅3.1
- 🟢 Sau gộp: **32.593 dòng × 33 cột**; rà kiểu dữ liệu & cấu trúc.
- 🔵 Bước "khám tổng quát" trước khi can thiệp — biết quy mô & loại biến.
- 🟡 Ảnh chụp `df.info()` / bảng tóm tắt số dòng–cột–kiểu.
- 🔗 `master_raw.parquet`, `build_master_table.py`.

**Slide 13 — Dữ liệu thiếu: phát hiện & phương án** ✅3.2 ✅3.3
- 🟢 **Chỉ 3 cột thiếu:**
  | Cột | Số thiếu | Bản chất | Xử lý |
  |---|---|---|---|
  | `date_unregistration` | 22.521 | **Cấu trúc** (đa số không rút môn) | Không dùng làm đặc trưng |
  | `imd_band` | 1.111 | MAR/MCAR | Điền `"Unknown"` (thành 1 nhóm riêng) |
  | `date_registration` | 45 | Ngẫu nhiên | Điền **trung vị của train** |
  - Điểm/số bài nộp thiếu do **chưa nộp** → điền **0** + tạo cờ `not_submitted`.
- 🔵 Mỗi loại thiếu có cơ chế khác nhau (MCAR/MAR/MNAR) → xử lý khác nhau; thiếu do "chưa nộp" là **tín hiệu**, không phải nhiễu.
- 🟡 Sau xử lý: 0 giá trị khuyết ở mọi cột đặc trưng.
- 📊 `reports/figures/quality_missingness.png`. 🔗 `preprocessing.py::handle_missing`.

**Slide 14 — Trùng lặp & chuẩn hoá định dạng** ✅3.4 ✅3.5 ✅3.6 ✅3.7
- 🟢 **Trùng:** kiểm tra theo khoá (code_module, code_presentation, id_student) → `drop_duplicates` → **0 khoá trùng**.
- 🟢 **Kiểu dữ liệu:** lập **danh mục kiểu biến** — numeric / ordinal / nominal / binary / indicator (`VARIABLE_TYPES`).
- 🟢 **Chuẩn hoá định dạng:** `str.strip()` nhãn phân loại; đối chiếu từ điển dữ liệu (region **13**, education **5**, imd_band **10**, age_band **3**, gender/disability **2**).
- 🔵 Nhận diện đúng kiểu là điều kiện để mã hoá đúng ở Phần 4; chuẩn hoá để tránh "Y " ≠ "Y".
- 🟡 Bộ dữ liệu nhất quán về định dạng & kiểu.
- 🔗 `build_master_table.py::_clean`, `preprocessing.py` (Task 16).

**Slide 15 — Giá trị bất thường & ngoại lai: phát hiện** ✅3.8 ✅3.10
- 🟢 Dò bất thường logic (vd điểm phải ∈ [0–100]) + dò ngoại lai bằng **quy tắc IQR** (`log_outliers`).
- 🔵 Đặc trưng clickstream **lệch phải rất mạnh** — `clicks_resource` skew ≈ 35, kurtosis ≈ 2.125; `max_clicks_single_day` max = 7.920.
- 🟡 Bảng 7 biến nghi ngoại lai (do Bình bàn giao cho Đức qua `handoff_outliers_for_Duc.csv`).
- 📊 `reports/figures/univariate_boxplots.png`. 🔗 `preprocessing.py::log_outliers` (Task 18).

**Slide 16 — Xử lý bất thường & ngoại lai** ✅3.9 ✅3.11
- 🟢 Chiến lược theo từng biến: **`log1p`** cho 12 biến click lệch mạnh · **`winsorize` (cắt 1% hai đầu)** cho biến lệch vừa · **`none`** cho biến trong phạm vi tự nhiên (vd `mean_score_to_date`: cận trên IQR 103,15 > 100 ⇒ không có ngoại lai thật).
- 🔵 **Quan trọng — KHÔNG loại bỏ dòng nào**: giá trị cực trị của sinh viên at-risk (vd học lại nhiều lần) là *tín hiệu cần giữ*; chỉ biến đổi giá trị.
- 🟡 Mọi biến số đưa về dạng phân phối "thuần" hơn mà vẫn giữ nguyên 32.593 dòng.
- 🔗 `preprocessing.py::handle_outliers`, `OUTLIER_STRATEGY`.

**Slide 17 — Gộp bảng & bộ dữ liệu sạch cuối cùng** ✅3.12 ✅3.13 ✅3.14
- 🟢 **Gộp:** `studentInfo` (nền) ← **left join** ← registration ← engagement ← performance ← courses.
- 🟢 **Kiểm tra sau gộp (nhật ký trước/sau):**
  | Bước | rows_before | rows_after |
  |---|---|---|
  | studentInfo (nền) | 32.593 | 32.593 |
  | + registration / engagement / performance | 32.593 | 32.593 |
  → **không nhân bản, không thất thoát** (`validate="many_to_one"`).
- 🟡 **Đầu ra:** `master_raw = 32.593 × 33` — bộ dữ liệu sạch, một dòng một sinh viên–môn–kỳ.
- 🔗 `master_join_log.csv`, `build_master_table.py`.

---

### KHỐI EDA — PHÂN TÍCH KHÁM PHÁ DỮ LIỆU — *Bình* (5 slide · ~4 phút)
> Đặt **ngay sau Làm sạch**: đã sạch dữ liệu → khám phá để (1) biện minh cách biến đổi ở Phần 4 (skew→log1p),
> (2) xác nhận **không rò rỉ**, (3) trả lời sớm RQ1 (tín hiệu xuất hiện khi nào).
> **Mỗi slide có 3 phần: (A) chữ lên slide · (B) lời thoại · (C) số liệu chốt.** Mọi số đã đối chiếu `reports/tables/` + `eda_findings.json`.

**Slide 18 — Mục tiêu EDA**
- **(A) Chữ lên slide**
  - Hiểu dữ liệu: 32.593 sinh viên, 33 biến (nhân khẩu học · tương tác · điểm số).
  - Kiểm tra chất lượng: thiếu dữ liệu, kiểu dữ liệu, ngoại lai.
  - Tìm tín hiệu phân biệt sinh viên at-risk vs not-at-risk.
  - Phục vụ 2 quyết định: **chọn đặc trưng** và **chống rò rỉ (leakage)**.
- **(B) Lời thoại:** *"EDA của nhóm có 3 mục tiêu. Một là hiểu dữ liệu — hơn 32 nghìn bản ghi, 33 biến chia 3 nhóm: nhân khẩu học, tương tác (clickstream) và điểm số. Hai là kiểm tra chất lượng — thiếu, phân phối, ngoại lai. Ba, quan trọng nhất với đề tài phát hiện sớm, là tìm biến phân biệt được sinh viên nguy cơ. Mọi kết luận EDA phục vụ trực tiếp cho hai việc phía sau: chọn đặc trưng và đảm bảo không rò rỉ dữ liệu."*
- **(C) Số liệu chốt:** 32.593 bản ghi · 33 cột · 3 nhóm biến.
- 📊 không cần hình (slide dẫn nhập). 🔗 `src/eda/eda.py`.

**Slide 19 — Phân tích phân phối (Univariate)**
- **(A) Chữ lên slide**
  - Công cụ: histogram + KDE, boxplot cho mỗi biến số.
  - Phần lớn biến clickstream **lệch phải mạnh** (right-skewed).
  - Đuôi nặng → nhiều ngoại lai **thật** (sinh viên siêu tích cực), **không xoá**.
  - Hệ quả: cần **biến đổi log + chuẩn hoá**, và dùng **kiểm định phi tham số**.
- **(B) Lời thoại:** *"Ở phân phối đơn biến, nhóm vẽ histogram kèm KDE và boxplot cho từng biến số. Rõ nhất là các biến đếm click lệch phải rất mạnh: `clicks_resource` có độ lệch (skew) tới 34,7 và độ nhọn (kurtosis) hơn 2.100 — đa số click ít, nhưng một nhóm nhỏ hoạt động cực nhiều tạo đuôi dài. Đây là ngoại lai thật, phản ánh hành vi học thật chứ không phải lỗi, nên nhóm không xoá mà xử lý bằng `log1p` và chuẩn hoá. Vì dữ liệu không chuẩn, các bước sau nhóm dùng kiểm định phi tham số Mann–Whitney thay cho t-test."*
- **(C) Số liệu chốt:** `clicks_resource` skew **34,71** · kurtosis **2.125,45** → lệch phải, đuôi nặng.
- 📊 `reports/figures/univariate_hist_kde.png` + `univariate_boxplots.png`. 🔗 `reports/tables/univariate_numeric.csv`.

**Slide 20 — Phân tích theo nhãn at-risk (Bivariate)**
- **(A) Chữ lên slide**
  - Phân phối lớp: at-risk **52,8%** vs not-at-risk 47,2% → mất cân bằng nhẹ.
  - So sánh 2 nhóm bằng **Cohen's d** + **Mann–Whitney** (hiệu chỉnh BH).
  - Top biến phân biệt: `days_since_last_activity` **d=2,55** · `n_assessments_submitted` **2,05** · `weighted_score_to_date` **1,96**.
  - **19/19** biến số có ý nghĩa thống kê (q < 0,05).
- **(B) Lời thoại:** *"Phân phối nhãn: at-risk chiếm 52,8% — mất cân bằng nhẹ, là con số thật của bộ dữ liệu. Để tìm biến phân biệt tốt, với mỗi biến số nhóm so sánh hai nhóm bằng Cohen's d kèm Mann–Whitney, hiệu chỉnh đa kiểm định Benjamini–Hochberg. Ba biến mạnh nhất thuộc nhóm tương tác và điểm: số ngày kể từ lần hoạt động cuối (d≈2,5 — rất lớn), số bài đã nộp, điểm có trọng số. Cụ thể, sinh viên at-risk trung bình **171 ngày** không hoạt động so với chỉ **14 ngày** ở nhóm còn lại; nộp trung bình **2,3 bài** so với **8,6 bài**. Toàn bộ 19/19 biến đều có ý nghĩa. Kết luận: tín hiệu nguy cơ nằm ở hành vi và điểm, không phải nhân khẩu học."*
- **(C) Số liệu chốt:** 52,8% at-risk · `days_since` d=2,55 (**171 vs 14 ngày**) · `n_assessments` (**2,3 vs 8,6 bài**) · 19/19 ý nghĩa.
- 📊 `reports/figures/bivariate_effect_sizes.png` + `bivariate_top_boxplots.png`. 🔗 `bivariate_numeric_tests.csv`.
- 💡 *Nếu hỏi nhân khẩu học:* yếu — Cramér's V cao nhất chỉ ≈ 0,15 (`highest_education`), sẽ nói ở Slide 21.

**Slide 21 — Tương quan & kiểm tra rò rỉ (Multivariate)**
- **(A) Chữ lên slide**
  - Heatmap **Pearson** (tuyến tính) + **Spearman** (đơn điệu, hợp dữ liệu lệch).
  - Tương quan với nhãn: `days_since` **+0,78** · `n_assessments` **−0,72** · `weighted_score` **−0,71**.
  - Đa cộng tuyến: 2 cặp |r| ≥ 0,8 (`n_days_active`–`total_clicks`=0,84; `days_since`–`n_assessments`=−0,83).
  - **Kiểm tra leakage:** không biến nào |r| ≥ 0,95 với nhãn → **không rò rỉ**.
  - Biến phân loại liên hệ yếu: **Cramér's V ≤ 0,15**.
- **(B) Lời thoại:** *"Bước đa biến dùng cả Pearson và Spearman — Spearman quan trọng vì dữ liệu lệch. Hai phát hiện chính. Một, tương quan với nhãn: `days_since_last_activity` +0,78 (càng lâu không hoạt động càng nguy cơ), số bài nộp và điểm tương quan âm khoảng 0,71–0,72 — khớp đúng kết quả Cohen's d ở slide trước, hai phương pháp độc lập cho cùng kết luận. Hai, kiểm tra rò rỉ — bước bắt buộc của đề tài: nhóm đặt ngưỡng nếu biến nào |r|≥0,95 với nhãn thì nghi leakage; kết quả không biến nào vượt — mạnh nhất chỉ 0,78, hợp lý về giáo dục chứ không phải rò rỉ. Ngoài ra có 2 cặp đa cộng tuyến cao nên ở mô hình tuyến tính nhóm sẽ cân nhắc gộp/bỏ bớt. Biến phân loại liên hệ với nhãn đều yếu, Cramér's V cao nhất 0,15."*
- **(C) Số liệu chốt:** r(nhãn) max = **0,78** · leakage ≥0,95: **0 biến** · đa cộng tuyến: **2 cặp** ≥0,8 · Cramér's V ≤ **0,15**.
- 📊 `reports/figures/corr_pearson.png` · `corr_spearman.png` · `corr_with_target.png`. 🔗 `correlation_with_target.csv`, `eda_findings.json`.

**Slide 22 — Phân tích theo thời gian & kết luận EDA (RQ1)**
- **(A) Chữ lên slide**
  - Đo độ phân biệt (Cohen's d) từng biến tại **6 mốc**: 10% → 100%.
  - Tín hiệu **mạnh dần đều** theo tiến độ. Mốc đầu tiên đạt d ≥ 0,8:
    `n_days_active` từ **10%** · `mean_score` · `n_assessments` · `weighted_score` từ **20%** · `days_since` từ **40%**.
  - Tín hiệu rút môn: Withdrawn ngừng hoạt động sớm — median **233 ngày** không hoạt động & **89 click** vs **11 ngày** & **1.425 click** (not-at-risk).
  - **Kết luận:** dự đoán sớm khả thi từ ~**20%** khóa học; ưu tiên đặc trưng **tương tác + điểm**.
- **(B) Lời thoại:** *"Phần này gắn trực tiếp với RQ1: tín hiệu xuất hiện từ giai đoạn nào? Nhóm tính lại Cohen's d cho từng biến tại cả 6 mốc. Khả năng phân biệt tăng dần đều theo thời gian — ví dụ `weighted_score_to_date` tăng từ **0,61** ở mốc 10% lên gần **1,96** ở cuối khóa, và `n_assessments_submitted` từ **0,67** lên **2,05**, đúng bằng giá trị ở slide bivariate. Quan trọng cho phát hiện sớm: ngay mốc 10%, `n_days_active` đã đạt mức phân biệt mạnh; đến mốc 20%, cả điểm và số bài nộp đều mạnh — chỉ với một phần nhỏ đầu khóa đã đủ tín hiệu cảnh báo. Một minh chứng nữa cho cách xử lý nhãn Withdrawn: sinh viên rút môn có median 233 ngày không hoạt động và chỉ 89 click, so với 1.425 click ở nhóm an toàn — sự sụp đổ hoạt động chính là tín hiệu sớm, không phải lỗi dữ liệu. Tóm lại EDA cho ba kết luận: tín hiệu nằm ở tương tác và điểm nên ưu tiên các đặc trưng này; không có rò rỉ; và dự đoán sớm khả thi từ khoảng 20% tiến độ — cơ sở để sang giai đoạn chọn đặc trưng và xây mô hình."*
- **(C) Số liệu chốt:** d tăng đều 10%→100% · `n_days_active` mạnh từ **10%**, điểm/bài nộp từ **20%** · Withdrawn **233 ngày & 89 click** vs **11 ngày & 1.425 click**.
- 📊 `reports/figures/time_discrimination_curve.png` · `time_mean_trajectory.png` · `withdrawn_activity_decay.png`. 🔗 `discrimination_by_checkpoint.csv`.
- ⚠️ **Lưu ý nhất quán:** dùng `weighted_score`/`n_assessments` làm ví dụ quỹ đạo (kết thúc đúng bằng d ở Slide 20). **Tránh** trích "days_since 1,56 ở mốc 100%" vì Slide 20 đã nói d=2,55 — hai số tính trên hai bộ khác nhau (master vs dataset_t100), dễ gây mâu thuẫn (xem Q&A mục D).

---

### PHẦN 4 — CHUẨN HOÁ & BIẾN ĐỔI DỮ LIỆU — *Đức* (5 slide · ~3,5 phút)
> ✅ Phủ đầu việc **4.1 → 4.14**

**Slide 23 — Mã hoá biến phân loại** ✅4.1 ✅4.2 ✅4.3
- 🟢 4 chiến lược theo bản chất biến:
  | Loại | Biến | Phương pháp | Vì sao |
  |---|---|---|---|
  | Thứ bậc | highest_education, imd_band, age_band | **OrdinalEncoder** (thứ tự cố định) | Giữ thứ tự nội tại |
  | Danh định | region, code_module, code_presentation | **OneHotEncoder** (`drop=None`) | Không có thứ tự; giữ đủ cột cho SHAP/LIME |
  | Nhị phân | gender, disability | **BinaryEncoder** (0/1) | Hai trạng thái |
  | Chỉ báo | not_submitted | passthrough | Đã là 0/1 |
- 🔵 Mã hoá sai (dùng one-hot cho biến thứ bậc) sẽ **xoá thông tin thứ tự**.
- 🟡 Biến chữ → số, mô hình & XAI đọc được.
- 🔗 `preprocessing.py` (Task 19), `ORDINAL_ORDERS`.

**Slide 24 — Biến đổi phân phối lệch (log1p)** ✅4.7 ✅4.8
- 🟢 Áp **`log1p`** cho các biến click lệch phải mạnh (đã nêu ở Phần 3).
- 🔵 Giảm đuôi nặng → ổn định mô hình tuyến tính & khoảng cách; bằng chứng thực nghiệm là skew ~13–35 ở EDA đơn biến.
- 🟡 Đặc trưng click có phân phối cân đối hơn, không mất dòng.
- 📊 `reports/figures/univariate_hist_kde.png`. 🔗 `OUTLIER_STRATEGY` (= "log1p").

**Slide 25 — Chuẩn hoá thang đo (StandardScaler)** ✅4.4 ✅4.5 ✅4.6
- 🟢 `StandardScaler` đưa biến số về **trung bình 0, độ lệch chuẩn 1**.
- 🔵 Tổng click (0–hàng nghìn) **áp đảo** điểm số (0–100) về biên độ → bắt buộc cho Logistic Regression & ANN; cây quyết định ít nhạy nhưng vẫn áp dụng cho **nhất quán pipeline**.
- 🟡 ⚠️ **Chỉ `fit` trên train**, `transform` cho cả train/test (minh chứng: in `scaler.mean_` chỉ tính từ train) → liên kết sang Phần 5.
- 🔗 `preprocessing.py::build_scaler / fit_transform_train` (Task 20).

**Slide 26 — Tạo đặc trưng mới & kiểm tra ý nghĩa** ✅4.9 ✅4.10 ✅4.11
- 🟢 **Đặc trưng phái sinh tiêu biểu** (feature engineering):
  - Tương tác: `total_clicks`, `n_days_active`, 8× `clicks_<loại>`, `max_clicks_single_day`, `mean_clicks_per_active_day`, **`days_since_last_activity`**.
  - Kết quả: `mean_score_to_date`, **`weighted_score_to_date`** (Σ điểm×trọng số), `n_assessments_submitted`, cờ **`not_submitted`**.
- 🟢 **Loại biến thừa (4.11):** id, `date_unregistration`, `final_result` gốc.
- 🔵 Mỗi đặc trưng gắn giả thuyết: "ngừng hoạt động lâu / bỏ nộp bài ⇒ nguy cơ cao".
- 🟡 **Kiểm tra ý nghĩa (4.10) bằng số liệu EDA** — |Cohen's d|: `days_since_last_activity` **2,55**, `n_assessments_submitted` **2,05**, `weighted_score_to_date` **1,96** → đặc trưng mới phân biệt 2 lớp rất mạnh.
- 📊 `reports/figures/bivariate_effect_sizes.png`. 🔗 `build_engagement_features.py`, `build_performance_features.py`.

**Slide 27 — Mất cân bằng dữ liệu & phương án** ✅4.12 ✅4.13 ✅4.14
- 🟢 **Kiểm tra:** at-risk 52,8% / not-at-risk 47,2% → **tỷ số mất cân bằng 1,12 (mất cân bằng nhẹ)**.
- 🔵 Nhẹ nhưng **bỏ sót sinh viên nguy cơ là sai lầm đắt nhất** → chỉ số chính là **PR-AUC & recall lớp at-risk**, không phải accuracy.
- 🟡 **Phương án (RQ3):** so sánh *no-resampling / class-weight / SMOTE / ADASYN*; **chỉ tái lấy mẫu trên tập train sau khi transform** (không đụng test).
- 🟡 **Đầu ra Phần 4:** bộ đặc trưng đã mã hoá–chuẩn hoá–biến đổi, **sẵn sàng cho mô hình**.
- 🔗 `preprocessing.py` (Bước 5: SMOTE chỉ trên `X_train_proc`), Report 2 §4.1.

---

### PHẦN 5 — TÁCH TRAIN/TEST & CHỐNG RÒ RỈ — *Khoa* (4 slide · ~3,5 phút)
> ✅ Phủ đầu việc **5.1 → 5.10**

**Slide 28 — Mục đích, tỷ lệ & phương pháp chia** ✅5.1 ✅5.2 ✅5.3
- 🟢 **Mục đích:** train để huấn luyện, test để đánh giá khách quan.
- 🟢 **Tỷ lệ:** **80% train / 20% test** (`TEST_SIZE = 0.2`).
- 🟢 **Phương pháp:** `StratifiedGroupKFold` — vừa **phân tầng theo `at_risk`** vừa **gom nhóm theo `id_student`**.
- 🔵 Một sinh viên học nhiều môn–kỳ ⇒ phải gom theo `id_student` để **không cho cùng một người vừa ở train vừa ở test** (rò rỉ nhóm).
- 🟡 Tập test ≈ **6.489 dòng / 6.5k sinh viên**, train ≈ **26.104 dòng**.
- 🔗 `src/evaluation/split_harness.py::make_fixed_test_ids`, `src/config.py`.

**Slide 29 — Kiểm soát rò rỉ: 2 trục** ✅5.5 ✅5.6
- 🟢 **Trục thời gian (time-aware):** `cut_at_checkpoint()` chỉ giữ sự kiện **tại/ trước ngày mốc**; `cutoff_day = round(length × t/100)` cho t ∈ {10,20,40,60,80,100}%. 3 quy tắc: bỏ bài nộp sau mốc · bỏ click sau mốc · giữ Withdrawn-trước-*t* là at-risk.
- 🟢 **Trục đặc trưng:** mọi bộ học (encoder, scaler, resampling) **chỉ fit trên train**.
- 🔵 Mô phỏng đúng "thông tin có tại thời điểm dự đoán" — không nhìn vào tương lai.
- 🟡 **6 bộ dữ liệu mốc** `dataset_t10…t100`, mỗi bộ 32.593 dòng, cùng một danh sách sinh viên; nhãn cố định 52,8% qua các mốc, chỉ đặc trưng thay đổi.
- 📊 `reports/figures/time_discrimination_curve.png` (sức phân biệt tăng dần theo mốc — RQ1). 🔗 `time_utils.py`, `make_checkpoints.py`.

**Slide 30 — Trình tự tiền xử lý đúng & áp dụng train→test** ✅5.4 ✅5.7 ✅5.8
- 🟢 **Trình tự bắt buộc:** `chia train/test → điền khuyết → ngoại lai → mã hoá/chuẩn hoá → tái lấy mẫu`.
- 🟢 Tham số (median, ngưỡng winsorize, mean/std scaler, danh mục encoder) **học từ train**, rồi **transform** lên test.
- 🔵 Nếu fit trên toàn bộ dữ liệu trước khi chia ⇒ test "rò rỉ" vào train ⇒ kết quả ảo.
- 🟡 **Phân bố nhãn sau chia (5.4):** train 0,53 / test 0,52 — **chênh ≤ 0,02**, đạt yêu cầu phân tầng.
- 🔗 `preprocessing.py` (sơ đồ anti-leakage Bước 1–5), `make_split.py` (`rate_gap ≤ 0.02`).

**Slide 31 — Lưu & kiểm tra lại: rò rỉ đã bị chặn** ✅5.9 ✅5.10
- 🟢 **Lưu:** định nghĩa test cố định `data/splits/test_student_ids.csv` (commit vào repo) + parquet train/test; `split_report.csv`.
- 🟢 **Kiểm tra lại (5.10):** **0 sinh viên trùng** giữa train/test; không lệch kiểu/cột; nhãn cân đối.
- 🔵 Test cố định, dùng lại y hệt qua **cả 6 mốc** ⇒ 6 điểm hiệu năng **so sánh được**.
- 🟡 **`tests/test_leakage.py`: 16/16 kiểm thử ĐẠT** — bằng chứng tự động chứng minh không rò rỉ.
- 🔗 `make_split.py::build_report`, `tests/test_leakage.py`.

---

### KẾT LUẬN — *An* (2 slide · ~1,5 phút)

**Slide 32 — Tóm tắt Task 3 (bảng 5 dòng)**
- Đúng bảng "Tóm tắt đầu việc chính" của cô:
  | Mục | Đầu việc trọng tâm | Kết quả của nhóm |
  |---|---|---|
  | 1. Xác định dữ liệu | mục tiêu, biến mục tiêu, nhóm dữ liệu, phạm vi | at_risk nhị phân 52,8%; 3 nhóm; 32.593 sv–môn–kỳ |
  | 2. Thu thập | nguồn, cấu trúc, ưu/nhược | OULAD CC-BY 4.0; 7 bảng; 10,6 triệu click; có MD5 |
  | 3. Làm sạch | thiếu/trùng/ngoại lai/gộp | 0 trùng; log1p+winsorize, **0 dòng bị xoá**; master 32.593×33 |
  | 4. Chuẩn hoá & biến đổi | mã hoá/chuẩn hoá/đặc trưng/mất cân bằng | Ordinal+OneHot+Binary; StandardScaler; d≤2,55; RQ3 |
  | 5. Tách train/test | tỷ lệ, phân tầng, chống rò rỉ | 80/20 group+stratified; 6 mốc; **16/16 test đạt** |

**Slide 33 — Đầu ra & bước tiếp theo + Q&A**
- 🟡 **Đầu ra Task 3:** `master_raw` + 6 bộ `dataset_t10…t100` + tập test cố định + pipeline tái lập (`RANDOM_SEED=42`, manifest MD5, *Restart & Run All*).
- ➡️ **Bước tiếp:** benchmark mô hình theo từng mốc (RQ1) → xử lý mất cân bằng (RQ3) → SHAP/LIME & độ ổn định giải thích (RQ2).
- "Cảm ơn — nhóm sẵn sàng trả lời câu hỏi." (xem **Mục D**)

---

## C. Bản đồ hình/bảng có sẵn → slide

| Tài nguyên trong repo | Dùng ở slide |
|---|---|
| `reports/figures/preprocessing_sequence.png` | S3 (sơ đồ tổng) |
| `reports/figures/target_distribution.png` | S5 (biến mục tiêu) · S20 (EDA bivariate) |
| `reports/figures/quality_missingness.png` | S13 (dữ liệu thiếu) |
| `reports/figures/univariate_boxplots.png` | S15 (ngoại lai) · **S19 (EDA univariate)** |
| `reports/figures/univariate_hist_kde.png` | **S19 (EDA univariate)** · S24 (log1p) |
| `reports/figures/bivariate_effect_sizes.png` | **S20 (EDA bivariate)** · S26 (ý nghĩa đặc trưng) |
| `reports/figures/bivariate_top_boxplots.png` | **S20 (EDA bivariate)** |
| `reports/figures/corr_pearson.png` · `corr_spearman.png` · `corr_with_target.png` | **S21 (EDA — tương quan & leakage)** |
| `reports/figures/time_discrimination_curve.png` | **S22 (EDA — RQ1)** · S29 (chống rò rỉ thời gian) |
| `reports/figures/time_mean_trajectory.png` | **S22 (EDA — RQ1)** |
| `reports/figures/withdrawn_activity_decay.png` | **S22 (EDA — Withdrawn)** · Q&A #1 |
| `data/interim/master_join_log.csv` | S17 (nhật ký gộp) |
| `reports/tables/split_report.csv` | S31 (0 overlap, rate_gap) |
| `data/checkpoint_map.csv` (22×6) | S29 (bản đồ mốc) |

> Bảng số liệu chi tiết (đối chiếu khi cô hỏi sâu): `reports/tables/univariate_numeric.csv`,
> `bivariate_numeric_tests.csv`, `data_quality_profile.csv`, `discrimination_by_checkpoint.csv`.

---

## D. Câu hỏi Q&A dự kiến (chuẩn bị trước)

1. **"Vì sao gộp Withdrawn vào at-risk thay vì loại bỏ?"** → Phương án A: rút môn là *tín hiệu thật* — trung vị số ngày không hoạt động: not-at-risk **11**, Fail **116**, Withdrawn **233**; tổng click giảm 1.425 → 89 (`withdrawn_activity_decay.png`).
2. **"52,8% — sao gọi là mất cân bằng?"** → Mất cân bằng **nhẹ** (ratio 1,12); ta báo cáo trung thực và để RQ3 định lượng tác động của SMOTE/ADASYN.
3. **"Điền điểm thiếu bằng 0 có làm sai lệch không?"** → Không, vì kèm cờ `not_submitted` phân biệt "thật sự chưa nộp" với "chưa tới hạn"; 0 ở đây có nghĩa "chưa tích luỹ điểm".
4. **"Làm sao chắc chắn không rò rỉ thời gian?"** → `cut_at_checkpoint` chỉ giữ sự kiện ≤ ngày mốc; `tests/test_leakage.py` (16 test) khẳng định không bản ghi nào vượt mốc.
5. **"Vì sao chia theo `id_student` chứ không theo dòng?"** → Một SV học nhiều môn–kỳ; chia theo dòng sẽ để cùng một người ở cả train lẫn test (rò rỉ nhóm) → `StratifiedGroupKFold`.
6. **"Đa cộng tuyến xử lý thế nào?"** → Phát hiện ở EDA (`n_days_active`–`total_clicks` r=0,84) và **để dành cho RQ2** (ảnh hưởng độ ổn định giải thích), không loại bỏ thủ công.

### Q&A riêng cho khối EDA (Bình)

7. **"`days_since_last_activity` ở Slide 20 là d=2,55, nhưng Slide 22 lại 1,56 — sao khác nhau?"** *(câu bẫy — phải nắm chắc)* → Hai chỉ số tính trên **hai bộ dữ liệu khác nhau**: Slide 20 (d=2,55) trên `master_raw` (clickstream đầy đủ cả khóa); Slide 22 (đường cong, 1,56 ở mốc 100%) trên `dataset_t100` đã **cắt click sau ngày mốc**. Riêng biến này nhạy với "ngày hoạt động cuối" nên lệch; **5 biến còn lại khớp tuyệt đối** giữa hai bảng. *Khuyến nghị: trên Slide 22 chỉ trích `weighted_score`/`n_assessments` (khớp y hệt) để tránh hiểu nhầm.*
8. **"`days_since` tương quan 0,78 với nhãn — có phải rò rỉ?"** → Không. Đã đặt ngưỡng nghi leakage |r|≥0,95; 0,78 còn xa ngưỡng và hợp lý về mặt giáo dục (ngừng học lâu → nguy cơ). Quan trọng hơn: hàm `cut_at_checkpoint` chỉ tính hoạt động **tới ngày mốc**, không nhìn tương lai → không thể rò rỉ.
9. **"Vì sao dùng Mann–Whitney & Spearman thay vì t-test & Pearson?"** → Dữ liệu lệch phải mạnh (skew tới 34,7), vi phạm giả định chuẩn của t-test/Pearson; kiểm định phi tham số bền vững hơn. Vẫn báo cả Pearson để so sánh.
10. **"19/19 biến đều có ý nghĩa — vậy biến nào cũng tốt?"** → Không. Ở n≈32.593 thì p-value gần như luôn < 0,05, nên nhóm xếp hạng bằng **độ lớn hiệu ứng (Cohen's d)** chứ không bằng p — chỉ nhóm tương tác/điểm đạt d lớn, nhân khẩu học rất nhỏ (d ≤ 0,28).

---

## E. Checklist hoàn thiện trước khi trình bày

- [ ] Mỗi slide trả lời đủ **Làm gì · Vì sao · Kết quả** (đối chiếu ký hiệu 🟢🔵🟡); riêng khối EDA giữ format **(A) chữ · (B) lời thoại · (C) số liệu chốt**.
- [ ] Toàn bộ con số khớp `reports/` & `src/` (32.593 · 33 cột · 52,8% · 10,6 triệu click · 16/16 test · skew 34,71 · d 2,55/2,05/1,96 · r max 0,78).
- [ ] Mỗi phần có **1 hình/bảng thật** (không dùng ảnh minh hoạ trống).
- [ ] **Nhất quán EDA:** Slide 22 KHÔNG trích "days_since 1,56 ở mốc 100%" cạnh "d=2,55" của Slide 20 — dùng `weighted_score`/`n_assessments` (xem Q&A #7).
- [ ] Tổng duyệt **đúng 5 phần Task 3 + khối EDA**, có slide chuyển giữa người trình bày.
- [ ] Tập đọc thử để mỗi phần ≈ đúng thời lượng (Bình ~7 phút là phần dài nhất — cân nhắc rút Phần 3 còn 4 slide).
- [ ] In sẵn Mục D (Q&A) — đặc biệt Q&A #7 (câu bẫy days_since) cho Bình.
