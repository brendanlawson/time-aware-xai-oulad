# Hiểu phần Model (Task 4) trong 15 phút — không cần biết code

> Dành cho Khoa. Mục tiêu: đọc xong bạn **kể lại được câu chuyện** và **trả lời được giảng viên**, không cần hiểu code. Mọi con số dưới đây là kết quả thật của dự án mình.

---

## 0. Một câu tóm tắt cả phần model
> Mình dạy máy tính **nhìn hồ sơ học tập của sinh viên rồi đoán em đó có nguy cơ trượt/bỏ học không** — và kiểm tra xem **đoán sớm cỡ nào thì còn đáng tin** để giảng viên kịp giúp.

Nếu chỉ nhớ 1 câu, nhớ câu đó.

---

## 1. Bài toán là gì?

Với **mỗi sinh viên**, máy đưa ra 1 trong 2 nhãn:
- **Nguy cơ (1)** = kết quả cuối là **Trượt (Fail)** hoặc **Bỏ học (Withdrawn)**
- **Không nguy cơ (0)** = **Qua (Pass)** hoặc **Giỏi (Distinction)**

Đây gọi là **phân loại nhị phân** (binary classification) — giống lọc email *spam / không spam*, hay bác sĩ sàng lọc *cần chú ý / bình thường*.

**Số liệu của mình:** 32.593 lượt ghi danh môn–kỳ (28.785 sinh viên duy nhất — một bạn có thể học nhiều môn). **52.8% là "nguy cơ"** (gần một nửa). Trong nhóm nguy cơ đó: **59% là Bỏ học, 41% là Trượt** — nhớ con số này, mục 9 sẽ cần.

> 🎤 *GV hỏi "bài toán loại gì?"* → "Phân loại nhị phân: nguy cơ hay không, dựa trên final_result."

---

## 2. Máy nhìn vào cái gì để đoán? (đặc trưng / features)

Mình cho máy xem **hồ sơ mỗi sinh viên** gồm 3 nhóm thông tin:

| Nhóm | Là gì | Ví dụ |
|---|---|---|
| **Nhân khẩu học** | thông tin nền | giới tính, vùng, trình độ học vấn, độ tuổi |
| **Tương tác (engagement)** | hành vi học online | tổng số click, số ngày có học, **bao lâu rồi không hoạt động** |
| **Kết quả (performance)** | điểm số | điểm trung bình các bài đã nộp, đã nộp đủ chưa |

Tổng cộng **28 đặc trưng**. Máy học mối liên hệ giữa các đặc trưng này và việc "nguy cơ hay không".

> 🎤 *"Dùng đặc trưng gì?"* → "3 nhóm: nhân khẩu học, tương tác VLE, và kết quả đánh giá."

---

## 3. "Time-aware" là gì? (ĐÂY là điểm đặc biệt của đề tài)

Vấn đề thực tế: **đoán ở cuối khóa thì vô dụng** — sinh viên trượt rồi, giúp không kịp. Nên mình cắt dữ liệu ở **6 mốc thời gian** trong khóa học:

```
10%  →  20%  →  40%  →  60%  →  80%  →  100% (thời lượng khóa)
```

Tại mỗi mốc, mình **giả vờ chỉ biết dữ liệu tới đó** rồi cho máy đoán. Ví dụ mốc 20% = "mới học được 1/5 khóa, đoán được chưa?".

→ Mục đích: tìm **thời điểm sớm nhất mà dự đoán còn đáng tin** (chính là câu hỏi **RQ1** của đề tài).

> 🎤 *"Time-aware nghĩa là sao?"* → "Bọn em đánh giá mô hình ở 6 mốc tiến độ khóa học, để biết can thiệp sớm cỡ nào thì còn chính xác."

---

## 4. Tại sao thử 5 thuật toán?

Không biết trước cái nào tốt → **thử nhiều rồi chọn**. 5 cái trong đề xuất:

| Thuật toán | Hiểu nôm na |
|---|---|
| **Logistic Regression** | đơn giản nhất, kẻ một "đường ranh giới" → làm **mốc tham chiếu** |
| **Random Forest** | hỏi ý kiến **rất nhiều cây quyết định** rồi lấy số đông |
| **XGBoost** | rừng cây "thông minh", sửa lỗi dần — **mạnh nhất hiện nay** |
| **LightGBM** | giống XGBoost nhưng nhanh hơn |
| **ANN** (mạng nơ-ron) | bắt chước "mạng thần kinh", bản nhẹ |

**Kết quả: XGBoost thắng** (nhỉnh hơn chút, LightGBM bám sát).

> 🎤 *"Sao chọn XGBoost?"* → "Bọn em benchmark cả 5; XGBoost cho recall và PR-AUC cao nhất ổn định."

---

## 5. Huấn luyện & chống "gian lận" (cực quan trọng khi bảo vệ)

**Train/Test split:** chia sinh viên làm 2 phần:
- **Train (80%)** = máy *học* trên đây.
- **Test (20%, 5.756 SV)** = *đề thi* máy chưa từng thấy, để chấm khách quan.

Ba nguyên tắc chống gian lận (**leakage** — máy "xem trước đáp án"), GV rất hay hỏi:
1. **Chia theo sinh viên**, không theo dòng → một SV không nằm cả train lẫn test (như không cho thí sinh xem trước đề).
2. **Cắt thời gian nghiêm** → ở mốc 20%, máy *không được* thấy dữ liệu sau mốc đó.
3. **Mọi xử lý (chuẩn hóa, cân bằng) chỉ học từ train**, không đụng test.

→ Bọn mình có **hơn 20 bài kiểm thử tự động** canh đúng các luật này (đều PASS).

> 🎤 *"Làm sao chắc không bị leakage?"* → "Chia theo id_student, cắt thời gian, mọi thứ fit trên train; có hơn 20 test tự động kiểm tra, pass hết."

---

## 6. Các chỉ số đánh giá (chỉ cần hiểu 3 cái)

Hình dung 4 trường hợp khi máy đoán:

|  | Máy nói "nguy cơ" | Máy nói "ổn" |
|---|---|---|
| **SV thật sự nguy cơ** | ✅ Bắt đúng | ❌ **Bỏ sót** (tệ nhất!) |
| **SV thật sự ổn** | ⚠️ Báo nhầm | ✅ Đúng |

- **Recall** = *Bắt đúng / (Bắt đúng + Bỏ sót)* → **trong 100 SV nguy cơ thật, máy tóm được mấy người.** Quan trọng nhất, vì **bỏ sót = một em không được giúp**.
- **Precision** = trong những em bị gắn cờ, bao nhiêu là đúng (không báo nhầm thừa).
- **PR-AUC / ROC-AUC** = máy **xếp hạng** "ai nguy hơn ai" giỏi tới đâu. Thang **0.5 = đoán mò**, **1.0 = hoàn hảo**.

> 🎤 *"Sao lấy recall làm chính?"* → "Vì mục tiêu là không bỏ sót sinh viên cần giúp; bỏ sót nguy hiểm hơn báo nhầm."

---

## 7. Cross-validation (vì sao chạy đi chạy lại)

Sợ kết quả **ăn may** một lần → mình thi thử nhiều lần: **5-fold × 5 lần xáo = 25 lượt**, rồi lấy trung bình ± độ lệch.

Kết quả ở mốc 100%: XGBoost & LightGBM dẫn đầu (recall ~0.93), **độ lệch chỉ ~0.005** → rất ổn định, không ăn may.

> 🎤 *"Cross-validation để làm gì?"* → "Để chắc kết quả không phụ thuộc một lần chia may rủi; bọn em lặp 5×5 và báo cáo trung bình ± độ lệch."

---

## 8. Kết quả chính & trả lời RQ1

Bảng **recall theo thời gian** (XGBoost — đọc từ trái sang phải):

| Mốc | 10% | 20% | **40%** | 60% | 80% | 100% |
|---|---|---|---|---|---|---|
| Recall | 0.71 | 0.76 | **0.81** | 0.87 | 0.90 | 0.93 |

**Đọc ra:** càng học nhiều, máy đoán càng chuẩn (recall tăng đều). Nếu lấy mốc "đáng tin" = recall ≥ 0.80, thì **đạt từ mốc 40%** → đúng với các bài báo nền (Adnan: 40–60%).

> 🎤 **Câu trả lời RQ1:** "XGBoost tốt nhất; trên toàn bộ lượt ghi danh, dự đoán đạt ngưỡng tin cậy từ **~40% khoá học**; trên nhóm còn-đang-học — nhóm can thiệp được — ngưỡng đó chỉ đạt ở **cuối khoá**, nên bọn em báo cáo cả hai."

Nhưng con số này là trên **toàn bộ lượt ghi danh** — đọc mục 9 để biết cách nói trung thực.

---

## 9. Điểm "trung thực" — nói ra sẽ được điểm cao (đừng giấu!)

Nhớ mục 1: **59% SV nguy cơ là Bỏ học**. Mà nhiều em **bỏ học rất sớm** — 48% đã chính thức rút trước mốc 10%.

→ Vấn đề: máy "đoán" được mấy em này thì **không phải tài** — em đã nghỉ rồi, đâu cần đoán, và cũng **không can thiệp được nữa**.

Nên bọn mình làm thêm 1 phép kiểm: **chỉ tính những SV còn đang học tại mỗi mốc** (nhóm thật sự cứu được). Recall tụt:

| Mốc | Recall (tất cả) | Recall (chỉ SV còn học) |
|---|---|---|
| 40% | 0.81 | **0.68** |
| 60% | 0.87 | **0.75** |
| 80% | 0.90 | **0.78** |
| 100% | 0.93 | **0.85** |

**Ý nghĩa:** con số đẹp ban đầu có phần nhờ "bắt người đã nghỉ". Trên nhóm *còn cứu được*, bài toán **khó hơn và thật hơn**. Theo đúng tiêu chí recall ≥ 0,80 của nhóm, nhóm còn-học **chỉ đạt ở mốc 100%** — vì vậy mọi phát biểu "tin cậy từ 40%" phải kèm rõ cohort.

> 🎤 *Đây là vũ khí, không phải điểm yếu.* Nói: "Bọn em phát hiện nhãn nguy cơ bị chi phối bởi nhóm đã bỏ học, nên báo cáo tách riêng nhóm còn học để đánh giá trung thực." → GV sẽ thấy nhóm **nghiêm túc và hiểu sâu**.

---

## 10. Tủ câu hỏi nhanh (học thuộc 9 câu này là đủ tự tin)

1. **Bài toán gì?** → Phân loại nhị phân: SV nguy cơ (Trượt/Bỏ) hay không.
2. **Dữ liệu gì?** → OULAD, 3 nhóm đặc trưng: nhân khẩu học, tương tác, kết quả.
3. **Thuật toán nào, sao chọn?** → Thử 5 (LR/RF/XGBoost/LightGBM/ANN); **XGBoost** thắng về recall & PR-AUC.
4. **Đo bằng gì?** → Recall (chính), PR-AUC, ROC-AUC, F1; recall vì không được bỏ sót SV cần giúp.
5. **Chống leakage sao?** → Chia theo SV, cắt thời gian, fit trên train; hơn 20 test tự động pass.
6. **Đoán sớm được không (RQ1)?** → Tin cậy từ ~40% khóa học; và bọn em trung thực tách nhóm SV còn-đang-học.
7. **SMOTE của nhóm cân bằng lớp nào?** → "Nhãn at-risk của bọn em chiếm 52,8% — là lớp đa số nhẹ, nên SMOTE mặc định thực chất tăng mẫu lớp not-at-risk. Bọn em phát hiện điều này, so cả 4 chiến lược và khác biệt ≤0,005 → kết luận không phụ thuộc; con số chính dùng baseline không resample."
8. **Threshold chọn trên tập nào?** → "Trên validation out-of-fold của train (5-fold), test chỉ chấm một lần ở ngưỡng đã chốt — tránh lạc quan hoá."
9. **32.593 là sinh viên à?** → "Là lượt ghi danh môn–kỳ; sinh viên duy nhất là 28.785. Split theo id_student nên một SV không bao giờ nằm cả train lẫn test."

---

### Bạn cần làm gì bây giờ
1. Đọc tài liệu này 1–2 lượt.
2. Chỗ nào lợn cợn → hỏi tôi, tôi giải thích lại bằng ví dụ khác.
3. Khi thấy nắm rồi → bảo tôi, tôi viết tiếp **phần báo cáo** và **slide + tủ câu hỏi bảo vệ** (đã hẹn).

> Bạn không "vô tình" phải làm nữa — đọc xong cái này là bạn **chủ động hiểu** rồi. 💪
