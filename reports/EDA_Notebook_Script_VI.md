---
title: "Kịch bản trình bày EDA — chạy trực tiếp trên notebook `02_eda.ipynb`"
subtitle: "OULAD · Time-Aware Explainable Early At-Risk Prediction — DSP391m, Nhóm 1"
author: "Người trình bày: Đức"
---

> **Cách dùng tài liệu này.** KHÔNG dùng slide. Mở thẳng `notebooks/02_eda.ipynb`
> (đã `Run All`, mọi hình/bảng hiển thị sẵn), rồi cuộn **từng ô (cell) theo đúng thứ tự**
> và nói theo kịch bản dưới. Mỗi mục dưới đây ứng **1–1 với một ô trong notebook**
> (số ô khớp với thanh `In[ ]` / tiêu đề Markdown).
>
> Mỗi ô được trình bày theo 4 lớp:
> **(a) Làm gì** — thao tác của ô · **(b) Cách làm** — phương pháp & vì sao chọn ·
> **(c) Đọc gì** — chỉ vào con số/biểu đồ nào · **(d) → Build model** — bước này
> phục vụ gì cho giai đoạn dựng mô hình (RQ1/RQ2/RQ3).
>
> Toàn bộ hình & bảng do module đã kiểm thử `src/eda/eda.py` sinh ra — **notebook chỉ
> gọi hàm và hiển thị**, nên những gì khán giả thấy đúng bằng code, không vẽ tay.
> Câu chốt xuyên suốt: *"EDA ở đây không để trang trí — mỗi phát hiện đều ràng vào một
> quyết định khi dựng mô hình."*

---

## Mở đầu (trước khi cuộn — 30 giây)

> "Phần này em trình bày **trực tiếp trên notebook**, không qua slide, để cả nhóm thấy
> rõ *cách chúng em thực sự làm EDA* chứ không chỉ kết quả. Em sẽ đi từ trên xuống:
> hiểu cấu trúc dữ liệu → từng biến → biến số với nhãn → tương quan & rò rỉ → và cuối
> cùng là phân tích **theo thời gian** — phần quan trọng nhất, vì nó quyết định *bao giờ*
> mô hình có thể cảnh báo sớm. Mỗi bước em sẽ nói luôn nó **phục vụ gì cho việc dựng mô hình**."

---

## Ô 0 — Markdown: Tiêu đề

**Nói:** "Đây là notebook EDA trên bộ OULAD. EDA chạy **sau khi làm sạch**, trên bảng
`master_raw` đã sẵn sàng phân tích — **32.593 sinh viên × 33 cột**. Đây là một mắt xích
trong pipeline: cleaning → **EDA** → feature/leakage → mô hình theo checkpoint."

→ **Build model:** đặt mốc — mọi thứ phía dưới là *đầu vào quyết định* cho khâu feature
engineering và lịch huấn luyện.

---

## Ô 1 — Markdown: Executive summary

**(a) Làm gì.** Tóm tắt 5 phát hiện chốt trước khi chứng minh.

**(c) Đọc gì — đọc lướt 5 dòng, không sa đà:**
1. Nhãn `at_risk` **52,8%** — mất cân bằng *nhẹ* (tỉ lệ 1,12).
2. Đặc trưng **hành vi** (clicks, ngày hoạt động, ngày nhàn rỗi) phân tách rất mạnh
   theo nhãn — Cohen's *d* tới **2,55**.
3. Đặc trưng **nhân khẩu** (giới, IMD, tuổi…) tín hiệu **yếu** — Cramér's V ≤ 0,15.
4. **Không có rò rỉ**: không cặp nào |r| ≥ 0,95 với nhãn.
5. Theo thời gian: tín hiệu **dùng được từ rất sớm** — đạt mức "mạnh" (*d* ≥ 0,8)
   ngay từ mốc **10%** học kỳ.

**Nói:** "Đây là bức tranh tổng. Năm điều này em sẽ chứng minh từng cái ở các ô dưới."

→ **Build model:** đây chính là 5 ràng buộc thiết kế — (1)→chọn metric & resample,
(2)→ưu tiên feature hành vi, (3)→giữ nhân khẩu cho fairness chứ không để dự đoán,
(4)→an toàn đánh giá, (5)→lịch checkpoint RQ1.

---

## Ô 2 — Markdown: §0 Mục tiêu & phương pháp thống kê

**(b) Cách làm — đây là ô "khai báo phương pháp", nói kỹ vì cả notebook dựa vào đây:**

- **So sánh 2 nhóm (at-risk vs not):** dùng **Mann–Whitney U** — kiểm định **phi tham số**,
  *vì* các biến hành vi lệch phải nặng (không chuẩn), nên t-test sẽ sai giả định.
- **Độ lớn hiệu ứng:** **Cohen's *d*** theo công thức nhóm dùng
  `|m₁−m₀| / √((s₁²+s₀²)/2)` (ddof=1). *Vì sao cần d:* p-value với 32 nghìn dòng gần
  như luôn "có ý nghĩa"; *d* mới cho biết khác biệt có **đáng kể trên thực tế** không.
- **Đa kiểm định:** hiệu chỉnh **Benjamini–Hochberg (FDR)** — vì test 19 biến cùng lúc,
  cần kiểm soát dương tính giả.
- **Biến phân loại × nhãn:** **Cramér's V** (chuẩn hóa từ χ²) — đo liên hệ về 0..1.
- **Tương quan:** **Pearson** (tuyến tính) + **Spearman** (đơn điệu) để bắt cả quan hệ
  phi tuyến.

**Nói:** "Điểm mấu chốt: chúng em **xếp hạng đặc trưng theo độ lớn hiệu ứng, không theo
p-value** — đó là chỗ nhiều người làm EDA hay nhầm."

→ **Build model:** chọn đúng phương pháp = bảng xếp hạng feature đáng tin → khâu chọn
feature về sau không bị p-value đánh lừa.

---

## Ô 3 — Code: Setup (nạp dữ liệu)

**(a) Làm gì.** Import, định nghĩa đường dẫn, nạp `master_raw` và **6 checkpoint dataset**.

**(b) Cách làm.** Notebook **không tính lại trong cell** — nó gọi `src/eda` (module đã có
test) và đọc bảng/hình đã sinh. "Một nguồn sự thật", tránh lệch giữa báo cáo và code.

**Nói (chỉ vào `In[ ]` chạy xong, không lỗi):** "Ô này nạp 32.593 dòng và 6 lát cắt thời
gian. Mọi ô sau chỉ gọi hàm `eda.*` và hiển thị — nên cái các bạn thấy đúng bằng code."

→ **Build model:** chính 6 checkpoint này là tập huấn luyện cho RQ1 (dự đoán sớm theo mốc
thời gian); EDA và model dùng *cùng* nguồn, không lệch.

---

## Ô 4–5 — §1 Hồ sơ dữ liệu (Markdown + Code → bảng `profile`)

**(a) Làm gì.** Ô 5 in bảng hồ sơ từng cột: `dtype`, `% thiếu`, `số giá trị duy nhất`, `skew`.

**(b) Cách làm.** "Structure-first": trước khi vẽ gì, ta **rà cấu trúc** — kiểu dữ liệu,
độ thưa, độ lệch — để quyết định cột nào cần biến đổi/mã hóa.

**(c) Đọc gì — chỉ vào:**
- Vài cột **skew rất cao** (các biến clicks): phân phối lệch phải mạnh.
- Các cột có **% thiếu** > 0 (sẽ soi kỹ ở §2).
- Cột phân loại có `n_unique` nhỏ → sẽ one-hot.

→ **Build model:** bảng này là *danh sách việc* cho preprocessing — cột nào `log1p`,
cột nào scale, cột nào encode. Quyết định ở đây vào thẳng `ColumnTransformer`.

---

## Ô 6–7 — §2 Chất lượng dữ liệu (Markdown + Code → bảng + hình missingness)

**(a) Làm gì.** `eda.data_quality()` → bảng chất lượng + hình `quality_missingness.png`.

**(c) Đọc gì.** Chỉ vào: chỉ một nhóm nhỏ cột thiếu (chủ yếu liên quan
`date_unregistration` / điểm), **cơ chế thiếu có ý nghĩa** (thiếu = chưa rút môn), và
sau xử lý **0 NaN**.

**Nói:** "Thiếu ở đây **không ngẫu nhiên** — nó mang thông tin (sinh viên chưa rút môn).
Nên ta xử lý có chủ đích, không xóa bừa."

→ **Build model:** dữ liệu sạch, 0 NaN → mô hình `fit` không vỡ; và logic impute được
**học trên train, áp cho cả hai** (chống rò rỉ) — đây là điểm ta cố tình kiểm soát.

---

## Ô 8–9 — §3 Univariate, phần số (Markdown + Code → bảng + hist/KDE)

**(a) Làm gì.** `eda.univariate()` → bảng `mean/median/skew/kurtosis` + hình
`univariate_hist_kde.png`.

**(b) Cách làm.** **Skew** = mô-men chuẩn hóa bậc 3; |skew| > 1 coi là lệch mạnh.
So `mean` với `median`: lệch phải thì `mean ≫ median`.

**(c) Đọc gì — chỉ vào hình:**
- Các biến clicks **dồn sát 0, đuôi phải rất dài** (skew của `clicks_resource` ~ **34,7**).
- `days_idle` (ngày nhàn rỗi) có dạng **lưỡng đỉnh** — nhóm hoạt động đều vs nhóm bỏ bê.

**Nói:** "Vì lệch nặng như này nên (1) ta dùng kiểm định **phi tham số** ở phần sau, và
(2) ta sẽ **log1p** các biến clicks."

→ **Build model:** xác nhận **biến đổi `log1p`** cho biến clicks — giúp mô hình tuyến tính
và mô hình dựa khoảng cách ổn định; đồng thời chốt dùng thống kê phi tham số để xếp hạng.

---

## Ô 10 — Code: §3 Boxplots (hình `univariate_boxplots.png`)

**(c) Đọc gì.** Đuôi phải dày, nhiều điểm ngoài râu (giá trị cực đại tới ~6.988 clicks).

**Nói:** "Đây là ngoại lai **thật** (sinh viên siêu chăm), không phải lỗi nhập liệu."

→ **Build model:** chốt **winsorize / cắt ngưỡng** (không xóa dòng) để giữ mẫu mà giảm
ảnh hưởng đuôi — ngưỡng **học từ train**.

---

## Ô 11–12 — §3 Univariate phần phân loại (Markdown + Code → freq)

**(c) Đọc gì.** ~**83%** sinh viên ở mức học vấn A-Level trở xuống; các mức
Post-Graduate / No-Formal **hiếm**.

→ **Build model:** mức hiếm → **one-hot với `handle_unknown='ignore'`** để mô hình không
vỡ khi gặp giá trị lạ trong tập test/triển khai.

---

## Ô 13–14 — §4 Phân phối nhãn & mất cân bằng (Markdown + Code → bảng + hình)

**(a) Làm gì.** `eda.target_distribution()` → đếm `final_result` + hình `target_distribution.png`.

**(b) Cách làm.** `at_risk = final_result ∈ {Fail, Withdrawn}` (nhị phân hóa).

**(c) Đọc gì.** **At-risk 52,8% (17.208)** vs **không 47,2% (15.385)**, tỉ lệ **1,12** —
mất cân bằng *nhẹ*. **Withdrawn** là lớp đơn lớn nhất.

**Nói:** "Vì chỉ lệch nhẹ nên ta **không** cần resample mạnh tay; nhưng vẫn ưu tiên metric
nhạy với lớp dương."

→ **Build model:** quyết định **metric = PR-AUC + recall lớp at-risk** (RQ3) và chiến lược
imbalance vừa phải (SMOTE/ADASYN **chỉ trên train**).

---

## Ô 15–16 — §5 Bivariate số × nhãn (Markdown + Code → bảng effect size + hình)

**(a) Làm gì.** `eda.numeric_vs_target()` → bảng test sắp theo **Cohen's *d* giảm dần** +
hình `bivariate_effect_sizes.png`.

**(b) Cách làm.** Với mỗi biến: Mann–Whitney (p) → BH (q) → Cohen's *d* (độ lớn).
**Sắp xếp theo *d***, không theo p.

**(c) Đọc gì.** Top là các biến **hành vi**: tổng clicks, số ngày hoạt động, `days_idle` —
*d* lên tới **2,55** (khác biệt khổng lồ). **19/19** biến có ý nghĩa sau BH, nhưng điều
quan trọng là **độ lớn**, không phải "có ý nghĩa".

**Nói (phòng hiểu nhầm):** "*d* = 2,55 **không phải rò rỉ** — đây là biến hành vi hợp lệ
quan sát *trong* kỳ; ô §7 sẽ kiểm chứng không có rò rỉ."

→ **Build model:** đây là **bảng ưu tiên feature**. Ta kỳ vọng đúng nhóm này đứng đầu
**SHAP** khi giải thích mô hình (RQ2) — EDA và giải thích mô hình phải khớp nhau.

---

## Ô 17 — Code: §5 Top boxplots (hình `bivariate_top_boxplots.png`)

**(c) Đọc gì.** 6 biến mạnh nhất: hộp của nhóm at-risk **lệch hẳn** so với nhóm không —
trực quan hóa cái *d* lớn vừa nói.

→ **Build model:** bằng chứng trực quan để bảo vệ lựa chọn feature trước hội đồng.

---

## Ô 18–19 — §6 Bivariate phân loại × nhãn, Cramér's V (Markdown + Code)

**(a) Làm gì.** `eda.categorical_vs_target()` → bảng V + hình `bivariate_categorical_rate.png`.

**(c) Đọc gì.** Mọi biến nhân khẩu có **Cramér's V ≤ 0,15** — liên hệ **yếu**. Tỉ lệ at-risk
chênh nhẹ giữa các nhóm nhưng không nhóm nào "định đoạt".

**Nói:** "Nhân khẩu **yếu** — đây là tin tốt về **đạo đức/công bằng**: mô hình sẽ dựa vào
*hành vi* (can thiệp được) chứ không phải *bạn là ai*."

→ **Build model:** vẫn **giữ** biến nhân khẩu trong mô hình, nhưng dùng để **giám sát
fairness** (RQ2/ethics), không kỳ vọng chúng là feature dự đoán chính.

---

## Ô 20–21 — §7 Multivariate: tương quan, đa cộng tuyến, rò rỉ (Markdown + Code)

**(a) Làm gì.** `eda.correlation()` → in **cặp tương quan mạnh (|r|≥0,6)**, **tương quan với
nhãn**, + ma trận `corr_pearson.png`.

**(b) Cách làm.** Pearson (tuyến tính) + Spearman (đơn điệu). **Quy tắc rò rỉ:** không
feature nào được |r| ≥ **0,95** với nhãn (ngưỡng đó = nghi "lộ đề").

**(c) Đọc gì.** Vài cặp feature **đa cộng tuyến** (|r| ≥ 0,8, ví dụ các biến clicks liên
quan); `days_idle` tương quan với nhãn **+0,78** (mạnh nhưng **< 0,95** → hợp lệ).

→ **Build model:** đánh **cờ đa cộng tuyến** — cặp tương quan cao làm SHAP **kém ổn định**
(tín dụng bị chia đôi); ta lưu ý khi diễn giải RQ2 (có thể gộp/chọn 1 trong cặp).

---

## Ô 22 — Code: §7 Tương quan với nhãn (hình `corr_with_target.png`)

**(c) Đọc gì.** Thanh tương quan với nhãn — **không thanh nào chạm 0,95**.

**Nói (câu quan trọng):** "Đây là **bằng chứng không rò rỉ**. Nó ăn khớp với bộ test rò rỉ
**19/19 pass** trong `tests/test_leakage.py` — EDA và test nói cùng một điều."

→ **Build model:** đảm bảo điểm số trên tập test **đáng tin**, không phải ảo do lộ nhãn —
nền tảng để mọi con số mô hình sau này có giá trị.

---

## Ô 23–24 — §8 Phân tích theo thời gian (RQ1) — *phần quan trọng nhất*

**(a) Làm gì.** `eda.time_aware(checkpoints)` → bảng **độ phân biệt theo 6 mốc** +
hình `time_discrimination_curve.png`.

**(b) Cách làm.** Tại mỗi mốc t ∈ {10, 20, 40, 60, 80, 100}% học kỳ: cắt dữ liệu **đúng
đến thời điểm đó** (không nhìn tương lai), rồi tính **Cohen's *d*** giữa at-risk vs không
trên đặc trưng tích lũy. Đường cong = *d* tăng theo thời gian.

**(c) Đọc gì.** Tín hiệu **đạt mức "mạnh" (*d* ≥ 0,8) ngay từ mốc 10%** và tăng dần. Tức là
chỉ với 1/10 đầu học kỳ, hành vi đã phân tách rõ nhóm nguy cơ.

**Nói (chốt cả bài):** "Đây là câu trả lời cho RQ1: **bao giờ cảnh báo được?** — câu trả
lời là **rất sớm**. Đây là lý do toàn bộ pipeline được thiết kế *time-aware*."

→ **Build model:** **đây là phần trực tiếp định hình mô hình nhất.** Nó đặt **lịch
checkpoint huấn luyện** cho RQ1 — ta huấn luyện/đánh giá mô hình tại từng mốc, và biết
ngay từ 10% đã có thể cảnh báo có ích → giá trị can thiệp sớm.

---

## Ô 25 — Code: §8 Quỹ đạo trung bình (hình `time_mean_trajectory.png`)

**(c) Đọc gì.** Đường trung bình của 2 nhóm **doãng dần** theo thời gian — khoảng cách
nới rộng = vì sao *d* tăng.

→ **Build model:** gợi ý đặc trưng dạng **xu hướng/độ dốc theo thời gian** có thể mạnh,
không chỉ giá trị tại một mốc.

---

## Ô 26–27 — §9 Tín hiệu cảnh báo sớm của nhóm Withdrawn (Markdown + Code)

**(a) Làm gì.** `eda.withdrawn_analysis()` → bảng tóm tắt + hình `withdrawn_activity_decay.png`.

**(c) Đọc gì.** Trung vị `days_idle` tăng theo nhóm kết quả (ví dụ ~**11 / 116 / 233**
ngày) — nhóm rút môn **im lặng dần** trước khi rút chính thức.

**Nói (kèm cảnh báo trung thực):** "Có một lưu ý: ở các mốc **muộn**, vài đặc trưng phản
ánh việc đã ngừng hoạt động → dễ *lạc quan giả* nếu đánh giá ở cuối kỳ. Vì vậy ta nhấn mạnh
**đánh giá ở mốc sớm**."

→ **Build model:** (1) ủng hộ cảnh báo sớm dựa trên **suy giảm hoạt động**; (2) nhắc khâu
đánh giá **không tâng bốc** mô hình bằng các mốc muộn — chốt báo cáo bằng metric ở mốc sớm.

---

## Ô 28 — Markdown: §10 Phát hiện & hàm ý cho mô hình hóa

**(a) Làm gì.** Ô tổng kết — đọc như **bàn giao sang khâu build model**.

**Nói — gói lại bằng 5 hàm ý, mỗi cái nối về một quyết định:**
1. **Biến đổi:** `log1p` biến clicks, winsorize đuôi (ngưỡng từ train).
2. **Feature:** ưu tiên đặc trưng **hành vi**; giữ nhân khẩu để **giám sát fairness**.
3. **An toàn:** **không rò rỉ** (|r|<0,95, test 19/19) → điểm test đáng tin.
4. **Mất cân bằng:** nhẹ → resample vừa phải **chỉ trên train**; metric PR-AUC + recall.
5. **Thời gian (RQ1):** cảnh báo dùng được **từ mốc 10%** → huấn luyện/đánh giá theo
   checkpoint, ưu tiên mốc sớm.

**Nói (câu kết):** "Nói gọn: EDA cho chúng em **danh sách biến đổi, thứ tự ưu tiên feature,
một đảm bảo an toàn không rò rỉ, và một mốc thời gian để cảnh báo sớm** — đó chính là bản
thiết kế đầu vào cho phần dựng mô hình."

---

## Phụ lục — Hỏi & Đáp dự phòng

**H: Cohen's *d* = 2,55 to thế, có phải lộ đề không?**
Đ: Không. Đây là biến hành vi quan sát *trong kỳ*, hợp lệ. Ô §7 cho thấy không feature nào
|r| ≥ 0,95 với nhãn, và `tests/test_leakage.py` pass **19/19**. Khác biệt lớn là *bản chất
dữ liệu*, không phải lỗi.

**H: Sao xếp hạng feature theo *d* mà không theo p-value?**
Đ: Với 32 nghìn dòng, gần như biến nào cũng "có ý nghĩa" (p nhỏ). p chỉ nói *có khác*, *d*
nói *khác bao nhiêu*. Quyết định feature phải dựa vào độ lớn thực tế.

**H: Vì sao dùng Mann–Whitney chứ không t-test?**
Đ: Biến hành vi lệch phải nặng (xem §3, skew tới ~34), vi phạm giả định chuẩn của t-test.
Mann–Whitney là phi tham số nên an toàn.

**H: Đa cộng tuyến có làm hỏng mô hình không?**
Đ: Không hỏng dự đoán, nhưng làm **SHAP kém ổn định** (chia tín dụng giữa các biến tương
quan). Ta đã đánh cờ ở §7 và sẽ lưu ý khi diễn giải RQ2.

**H: Tại sao tin được kết quả theo thời gian?**
Đ: Mỗi mốc ta **cắt đúng đến thời điểm đó**, không nhìn tương lai, dùng cùng 6 checkpoint
mà mô hình RQ1 sẽ huấn luyện — nên *d* tại mỗi mốc phản ánh đúng thông tin sẵn có lúc dự đoán.

**H: Idle = 0 ở các mốc đầu có phải bịa số không?**
Đ: Không. Bug cũ (no-activity gán 0) đã sửa: nay `days_idle` ở t=100 **khớp master**, có
test riêng (`test_checkpoint_t100_idle_matches_master`).
