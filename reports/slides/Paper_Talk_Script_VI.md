# Kịch bản thuyết trình — Paper_Talk_EN (tiếng Việt)

**Bài:** Time-Aware At-Risk Student Prediction on OULAD
**Slide:** `reports/slides/Paper_Talk_EN.pdf` (17 slide, style hội thảo khoa học)
**Thời lượng mục tiêu:** 15–18 phút nói + 5 phút hỏi đáp.

> Mục đích tài liệu này: (1) cho bạn biết **nói gì** ở mỗi slide, (2) **giải thích bản chất** để bạn thật sự hiểu dự án (không chỉ đọc slide), (3) chuẩn bị **câu hỏi hội đồng** hay hỏi. Đọc kỹ phần 💡 — đó là chỗ bạn cần nắm để trả lời khi bị hỏi ngoài slide.

**Nguyên tắc trình bày kiểu quốc tế:** mỗi slide một ý; nói chậm, nhìn hội đồng; slide là hình ảnh, lời giải thích nằm ở miệng bạn; đừng đọc nguyên văn slide. Câu quan trọng nhất của cả bài là **dual-cohort** (slide 8 và 10) — hãy nhấn mạnh nó.

---

## Slide 1 — Title

🗣️ **Nói (~30s):** "Kính chào hội đồng và các thầy cô. Em là [tên], nhóm 1. Hôm nay nhóm em trình bày đề tài *Dự đoán sớm sinh viên có nguy cơ học tập kém theo thời gian trên bộ dữ liệu OULAD*. Điểm khác biệt của bài là nhóm em đặt lại một câu hỏi mà hầu hết nghiên cứu trước bỏ qua: *chúng ta thật ra đang dự đoán trên nhóm sinh viên nào?*"

💡 **Hiểu:** Đây là câu "mở bài" — bạn đang bán 1 ý tưởng, không phải liệt kê. Ý tưởng bán là "population definition" (định nghĩa quần thể đánh giá). Nhớ tên đề tài và 3 từ khóa: **time-aware** (theo thời gian), **dual-cohort** (hai quần thể), **explainable** (giải thích được).

---

## Slide 2 — The problem

🗣️ **Nói (~45s):** "Trong học trực tuyến, rất nhiều sinh viên trượt hoặc bỏ học. Hỗ trợ vào cuối kỳ thì đã muộn. Giáo viên cần biết *ai* có nguy cơ và *sớm đến mức nào*, và quan trọng là biết *tại sao* để cảnh báo đáng tin và công bằng. Biểu đồ bên phải cho thấy sinh viên rút lui thường ngừng hoạt động trên hệ thống từ rất sớm."

💡 **Hiểu:** Đây là "động cơ" (motivation). Bài toán thực tế: early warning. Hình `withdrawn_activity_decay` cho thấy sinh viên at-risk "im lặng" sớm — đây cũng là manh mối cho phát hiện chính sau này.

---

## Slide 3 — The catch (điểm mấu chốt)

🗣️ **Nói (~60s):** "Đây là vấn đề nhóm em phát hiện. Các nghiên cứu trước chấm điểm mô hình tại giữa khóa, nhưng trên *toàn bộ* danh sách ghi danh — trong đó có cả những sinh viên *đã rút* rồi. Những sinh viên này gần như không còn hoạt động, nên mô hình nhận ra họ cực kỳ dễ. Nghĩa là một phần điểm 'cảnh báo sớm' thực chất chỉ là *nhận ra một kết cục đã xảy ra rồi*, chứ không phải dự báo. Câu hỏi trung tâm của bài là: *chúng ta thật ra đang dự đoán ai, và cách chọn quần thể có làm kết quả bị thổi phồng không?*"

💡 **Hiểu:** ĐÂY LÀ LINH HỒN CỦA BÀI. Nói chậm slide này. Ý: sinh viên "Withdrawn" (đã rút) vẫn nằm trong tập test, và họ có nhãn at-risk. Vì họ đã ngừng học nên feature "days_since_last_activity" rất lớn → mô hình đoán trúng dễ dàng. Nhưng đoán trúng một người đã rút thì *vô nghĩa cho việc can thiệp* — vì không còn ai để cứu. Đây không phải rò rỉ dữ liệu (nhãn không lọt vào feature), mà là "estimand mismatch" — sai lệch về *mục tiêu đo lường*.

❓ **Có thể bị hỏi:** *"Đây có phải data leakage không?"* → "Không ạ. Nhãn không bao giờ đi vào đặc trưng. Việc sinh viên đã rút ngừng hoạt động là hành vi *thật* được quan sát. Vấn đề nằm ở *chọn quần thể đánh giá*, không phải rò rỉ."

---

## Slide 4 — Research questions

🗣️ **Nói (~45s):** "Bài trả lời 3 câu hỏi. RQ1: mô hình nào tốt nhất ở mỗi mốc thời gian, và *sớm đến mức nào* thì dự đoán đủ tin cậy — tiêu chí là recall và PR-AUC đều ≥ 0,80. RQ2: giải thích của mô hình có *ổn định* không. RQ3: xử lý mất cân bằng lớp có ảnh hưởng gì không — lưu ý ở đây lớp at-risk chiếm 52,8%, tức là *đa số nhẹ*, không phải thiểu số."

💡 **Hiểu:**
- *Recall* = trong số sinh viên thực sự at-risk, mô hình bắt được bao nhiêu %. Đây là metric quan trọng nhất vì bỏ sót một em cần giúp là mất cơ hội can thiệp.
- *PR-AUC* = chất lượng xếp hạng trên lớp dương, không phụ thuộc ngưỡng.
- *52,8%* — nhớ con số này: nó khiến RQ3 trở thành câu hỏi "độ bền", không phải "cứu lớp hiếm".

---

## Slide 5 — Contributions

🗣️ **Nói (~50s):** "Bài có 4 đóng góp: (1) *định lượng* mức thổi phồng do chọn quần thể — khoảng tin cậy 95% của khoảng cách loại trừ 0 ở mọi mốc; (2) một benchmark theo thời gian *đã được kiểm định thống kê*; (3) đánh giá độ ổn định của giải thích *có so với một mốc ngẫu nhiên*; (4) một *quy tắc báo cáo kép* và một dashboard cho giáo viên."

💡 **Hiểu:** "Contributions" = phần hội đồng chấm điểm cao nhất. 4 ý này là "cái mới". Nếu chỉ nhớ 1: đó là số (1) — dual-cohort. "CI loại trừ 0" nghĩa là khác biệt *có ý nghĩa thống kê*, không phải ngẫu nhiên.

---

## Slide 6 — Data (OULAD)

🗣️ **Nói (~50s):** "Dữ liệu là OULAD của Đại học Mở Anh: hơn 32 nghìn lượt ghi danh, gần 29 nghìn sinh viên. Điểm quan trọng: nó gồm 7 bảng quan hệ từ *3 hệ thống* khác nhau — hệ thống thông tin sinh viên, log tương tác trên hệ thống học trực tuyến khoảng 10,6 triệu dòng, và hệ thống chấm bài. Nhóm em *tích hợp* 3 nguồn này thành một bảng phân tích. Nhãn at-risk chiếm 52,8%."

💡 **Hiểu:** Nếu bị hỏi "sao chỉ dùng 1 dataset / không crawl nhiều nguồn?" → trả lời: "Thu thập ở đây là *tích hợp 7 bảng từ 3 hệ thống vận hành* — đó chính là kỹ năng thu thập từ database. OULAD đã *ẩn danh hoàn toàn* nên không có khóa để nối thêm dữ liệu ngoài; crawl thêm sẽ không ghép được ở mức dòng, chỉ thêm bối cảnh." (Đây là câu trả lời đã chuẩn bị — học thuộc ý.)

❓ **Có thể bị hỏi:** *"Kết quả cao vậy có đáng tin không?"* → "Kết quả phản ánh chất lượng của OULAD — dataset nghiên cứu đồng nhất từ một tổ chức. Triển khai thực tế từ nhiều hệ thống không đồng nhất sẽ cho recall thấp hơn khoảng 10–15 điểm phần trăm. Nhóm em nêu rõ điều này ở phần giới hạn."

---

## Slide 7 — Method (pipeline)

🗣️ **Nói (~55s):** "Quy trình: từ 7 bảng thô, nhóm em *chia dữ liệu theo sinh viên* và đóng băng — một sinh viên không bao giờ xuất hiện ở cả tập huấn luyện lẫn tập kiểm tra. Sau đó cắt thành 6 mốc thời gian từ 10% đến 100% khóa học. Tại mỗi mốc, chỉ dữ liệu *trước hoặc bằng* mốc đó được dùng — không nhìn trộm tương lai. Mọi phép biến đổi chỉ *học trên tập train*. Và 21 test tự động phải pass trước khi chạy mô hình."

💡 **Hiểu:** Đây là phần "leakage-safe" — chống rò rỉ dữ liệu. 3 ý cốt lõi:
1. **Chia theo sinh viên** (không theo dòng): vì một sinh viên học nhiều môn, nếu chia theo dòng thì cùng một người lọt cả train lẫn test → mô hình "học thuộc" người đó → điểm ảo.
2. **Cắt theo thời gian**: tại mốc 40%, chỉ dùng click/điểm tính đến ngày đó.
3. **Fit-on-train**: scaler, encoder, SMOTE… chỉ tính trên train rồi áp lên test.

❓ **Có thể bị hỏi:** *"Vì sao chia theo sinh viên chứ không random?"* → "Vì một sinh viên xuất hiện ở nhiều module. Chia random theo dòng sẽ để cùng một sinh viên ở cả hai phía, mô hình học đặc điểm cá nhân đó và điểm bị thổi lên. Chia theo nhóm sinh viên loại bỏ rò rỉ này."

---

## Slide 8 — Two estimands (ý tưởng chính)

🗣️ **Nói (~60s):** "Đây là ý tưởng trung tâm. Cùng một nhãn nhưng có *hai câu hỏi khác nhau*. Bên trái — *toàn bộ quần thể*: 'lượt ghi danh này có kết thúc bằng trượt/bỏ học không?' — đúng cho mọi sinh viên, và là cách nghiên cứu trước dùng, nhưng bao gồm cả người đã rút. Bên phải — *quần thể còn theo học*: 'giáo viên nên liên hệ ai *bây giờ*?' — chỉ những sinh viên còn có thể can thiệp. Nhóm em chấm *cùng một dự đoán* trên cả hai và báo cáo cả hai."

💡 **Hiểu:** "Estimand" = đại lượng ta muốn ước lượng. Cùng mô hình, cùng dự đoán, nhưng đo trên 2 nhóm người khác nhau cho 2 con số khác nhau. Nhóm "còn theo học" = đã bỏ đi những sinh viên rút trước mốc. Đây mới là bài toán can thiệp thật.

---

## Slide 9 — Result 1: Benchmark

🗣️ **Nói (~45s):** "Ở mốc cuối khóa, XGBoost dẫn đầu về recall với 0,93; ba mô hình cây gradient boosting bám sát nhau. Quan trọng: nhóm em *kiểm định* thứ hạng bằng test Friedman và Wilcoxon-Holm trên 25 lần chạy chéo — nên khác biệt là có hệ thống, không phải may rủi. Hồi quy logistic chỉ kém vài điểm, nghĩa là *đặc trưng* mới là thứ mang tín hiệu, chứ không phải chọn thuật toán nào."

💡 **Hiểu:**
- 5 mô hình: Logistic Regression, Random Forest, XGBoost, LightGBM, ANN.
- Chọn XGBoost vì recall cao nhất + SHAP TreeExplainer chính xác cho cây.
- Friedman/Wilcoxon = kiểm định thống kê xác nhận "XGBoost hơn thật", không phải hơn do ngẫu nhiên.
- Điểm tinh tế: các mô hình gần bằng nhau → chứng tỏ feature engineering tốt, bài toán đã "hội tụ". (Đừng nói mô hình gần bằng nhau là "dở" — ngược lại.)

❓ **Có thể bị hỏi:** *"XGBoost và LightGBM gần bằng nhau, sao chọn XGBoost?"* → "Recall XGBoost nhỉnh hơn và TreeExplainer cho giải thích SHAP chính xác. Khác biệt nhỏ giữa hai mô hình là dấu hiệu tốt: nó cho thấy tín hiệu nằm ở đặc trưng, đã được kiểm định thống kê."

---

## Slide 10 — Result 2: Dual-cohort (slide quan trọng nhất)

🗣️ **Nói (~70s):** "Đây là kết quả chính. Đường trên là recall trên toàn bộ quần thể, đường dưới là trên quần thể còn theo học. Toàn bộ quần thể vượt ngưỡng 0,80 từ mốc 40%. Nhưng nhóm *còn theo học* — nhóm can thiệp được — chỉ vượt ngưỡng ở *cuối khóa*. Ở mốc 40%: 0,811 so với 0,678. Ở mốc cuối: 0,930 so với 0,841. Khoảng cách này có khoảng tin cậy 95% *loại trừ 0 ở mọi mốc* — tức là khác biệt thật, không phải nhiễu. Kết luận: câu trả lời 'dự đoán tin cậy từ khi nào' *thay đổi hẳn* tùy bạn chấm trên nhóm nào."

💡 **Hiểu:** Nhấn mạnh slide này nhất. Thông điệp: nếu chỉ nhìn đường trên (như nghiên cứu cũ) bạn tưởng "tin cậy từ 40%". Nhưng thực tế can thiệp (đường dưới) chỉ đạt chuẩn ở 100%. Khoảng cách hai đường = phần "thổi phồng" do đếm cả sinh viên đã rút. "CI loại trừ 0" = chắc chắn về mặt thống kê.

❓ **Có thể bị hỏi:** *"Vậy mô hình có vô dụng ở giữa khóa?"* → "Không vô dụng, nhưng chưa đạt chuẩn tin cậy 0,80 trên nhóm còn theo học. Nó vẫn cung cấp thông tin xếp hạng rủi ro; và nhóm em đề xuất chính sách lai — dùng luật đơn giản sàng lọc sớm, dùng mô hình từ giữa khóa."

---

## Slide 11 — Result 3: SHAP

🗣️ **Nói (~50s):** "Vì sao một sinh viên bị gắn cờ? SHAP cho thấy đặc trưng số một là *số ngày kể từ lần hoạt động cuối* trên hệ thống, rồi đến *điểm tích lũy có trọng số*. Không có đặc trưng nhân khẩu học nào trong nhóm dẫn đầu — nghĩa là cảnh báo dựa trên *hành vi*, không dựa trên hoàn cảnh cá nhân. Điều này biến thành hành động cụ thể: nhắc sinh viên sau hơn 14 ngày im lặng, ngay cả khi chưa có điểm."

💡 **Hiểu:** SHAP = phương pháp giải thích, cho biết mỗi đặc trưng đẩy dự đoán theo hướng nào và mạnh bao nhiêu. Điểm hay: feature quan trọng nhất (im lặng VLE) đúng bằng cơ chế gây "thổi phồng" ở slide 10 — vì sinh viên đã rút thì im lặng, nên mô hình bắt họ qua chính feature này. Không dùng nhân khẩu học ở top = tốt cho công bằng.

---

## Slide 12 — Result 4: Stability

🗣️ **Nói (~50s):** "Giải thích chỉ đáng tin nếu *lặp lại được*. Qua 5 hạt giống ngẫu nhiên, độ trùng top-10 (Jaccard) là 0,69 và tương quan hạng Spearman 0,97 — cao hơn hẳn mốc ngẫu nhiên là 0,12. Giữa SHAP và LIME, độ trùng là 0,43: hai phương pháp đồng thuận ở các đặc trưng dẫn đầu, khác nhau ở phần đuôi. Và giải thích thay đổi *mượt* theo thời gian, nên mỗi giải thích luôn đi kèm mốc thời gian của nó."

💡 **Hiểu:** Điểm phương pháp luận: một con số trùng khớp 0,43 hay 0,69 *tự nó vô nghĩa* nếu không so với ngẫu nhiên. Nhóm em dựng "null baseline" bằng Monte-Carlo: rút ngẫu nhiên hai top-10 thì trùng trung bình 0,12. Vì 0,69 >> 0,12 nên ổn định là *thật*. Đây là cái mà nhiều bài XAI thiếu (họ chỉ nhìn bằng mắt).

❓ **Có thể bị hỏi:** *"Jaccard 0,43 giữa SHAP và LIME là thấp mà?"* → "So với mốc ngẫu nhiên 0,12 thì vẫn là đồng thuận thật. Hai phương pháp thống nhất ở các đặc trưng dẫn đầu; khác nhau ở đuôi vì LIME xử lý biến one-hot như biến liên tục. Nhóm em neo kết luận vào SHAP và dùng LIME để đối chiếu."

---

## Slide 13 — Robustness + 4 phân tích bổ sung

🗣️ **Nói (~60s):** "Bốn phân tích củng cố. Một, *mất cân bằng*: qua 4 chiến lược, chênh lệch recall tối đa chỉ 0,007 — kết luận không phụ thuộc chiến lược. Hai, *luật đơn giản*: một luật 2 đặc trưng *thắng* XGBoost ở mốc sớm (0,999 so với 0,719) nhưng thua ở cuối khóa — gợi ý chính sách lai. Ba, *hiệu chỉnh xác suất* tốt (ECE 0,018–0,042), nên xác suất dùng được như điểm rủi ro. Bốn, *rút gọn đặc trưng*: chỉ 5 đặc trưng đã đạt bằng mô hình đầy đủ. Và khoảng cách train-test thu hẹp dần, chứng tỏ không overfit."

💡 **Hiểu:**
- **Mất cân bằng (RQ3):** SMOTE ở đây thực ra oversample nhầm lớp not-at-risk (vì at-risk là đa số). Nhưng vì chênh lệch không đáng kể (0,007) nên giữ SMOTE cũng không sao. Nếu bị hỏi "sao dùng SMOTE khi không có lớp thiểu số?" → "Đây là phép thử độ bền theo đề cương; kết quả cho thấy chiến lược cân bằng không đổi kết luận."
- **Rule baseline:** luật `im lặng > ngưỡng HOẶC điểm < ngưỡng`. Thắng sớm vì sinh viên rút bị bắt tầm thường (liên hệ slide 3, 10).
- **Calibration/ECE:** ECE = sai số hiệu chỉnh trung bình; 0,018 nghĩa là xác suất mô hình đưa ra khá khớp tần suất thực.
- **Ablation:** bỏ bớt đặc trưng, giữ top-5 vẫn đạt recall 0,932 → triển khai gọn.
- **Bias-variance:** gap train→test giảm từ 0,125 (mốc 10%) xuống 0,057 (mốc 100%) → variance giảm, không phải học vẹt.

---

## Slide 14 — Limitations

🗣️ **Nói (~45s):** "Nhóm em nêu giới hạn thẳng thắn: chỉ một dataset nên chưa kiểm chứng khả năng chuyển sang trường khác; điểm được tính vào ngày nộp nên lạc quan so với độ trễ chấm thật; ở mốc 40% khoảng tin cậy *chạm* ngưỡng 0,80; và phân tích còn-theo-học chấm lại mô hình huấn luyện trên toàn roster. Việc ẩn danh cũng chặn khả năng bổ sung dữ liệu ngoài."

💡 **Hiểu:** Nêu giới hạn KHÔNG phải điểm yếu — hội đồng đánh giá cao sự trung thực. Học thuộc 3 giới hạn đầu. Nếu hội đồng "bắt" một điểm yếu mà bạn đã tự nêu → bạn thắng.

---

## Slide 15 — Conclusion

🗣️ **Nói (~50s):** "Tóm lại: mô hình cây gradient boosting thắng một benchmark đã kiểm định, XGBoost đạt recall 0,93 cuối khóa. Nhưng 'sớm đến mức nào là tin cậy' phụ thuộc *bạn chấm trên nhóm nào* — 40% nếu tính cả người đã rút, cuối khóa nếu chỉ tính người còn theo học. Giải thích ổn định và dựa trên hành vi. Và thông điệp phương pháp — *gần như miễn phí để áp dụng*: mọi tuyên bố cảnh báo sớm nên *nêu rõ quần thể, kèm khoảng bất định, và gắn giải thích với mốc thời gian*."

💡 **Hiểu:** Đây là câu chốt. "Costless discipline" = đề xuất không tốn gì (chỉ cần chấm 2 lần và báo cả 2). Nói câu in đậm màu xanh thật rõ, đó là "message" bạn muốn hội đồng nhớ.

---

## Slide 16 — Thank you / Q&A

🗣️ **Nói (~15s):** "Em xin cảm ơn hội đồng. Toàn bộ pipeline, 21 test, dashboard và bài báo đều có trong repo, mọi con số truy được về file CSV. Em sẵn sàng nhận câu hỏi ạ."

💡 **Hiểu:** Nhấn "reproducible" (tái lập được) — điểm cộng lớn. Đứng thẳng, mỉm cười, chờ câu hỏi.

---

## Slide 17 — Selected references (backup)

💡 **Hiểu:** Slide dự phòng, chỉ mở khi hội đồng hỏi "dựa trên nghiên cứu nào". Nói: "Bài tham chiếu 37 tài liệu; đây là các mốc chính — OULAD gốc, nghiên cứu time-aware của Adnan, XGBoost, SHAP for trees, và Demšar cho kiểm định thống kê. Danh sách đầy đủ trong bài báo." Không cần trình bày slide này nếu không ai hỏi.

---

# Bộ câu hỏi hội đồng hay hỏi (ôn trước)

1. **"Đóng góp mới của các em là gì?"** → Dual-cohort: định lượng mức thổi phồng do chọn quần thể, có kiểm định thống kê. Chưa nghiên cứu OULAD nào tách 2 quần thể này.
2. **"Vì sao recall là metric chính?"** → Chi phí bỏ sót (không cứu được sinh viên) lớn hơn chi phí báo nhầm (một cuộc trò chuyện). Accuracy bị loại vì lớp gần cân bằng nên accuracy dễ bị thổi.
3. **"Làm sao chắc không rò rỉ dữ liệu?"** → Chia theo sinh viên + cắt theo thời gian + fit-on-train + 21 test tự động kiểm.
4. **"Kết quả có tổng quát hóa được không?"** → Chưa kiểm chứng ngoài OULAD; đó là giới hạn và hướng phát triển. Kỳ vọng recall thực tế thấp hơn.
5. **"SMOTE để làm gì khi at-risk là đa số?"** → Phép thử độ bền theo đề cương; chứng minh kết luận không phụ thuộc chiến lược cân bằng (Δ ≤ 0,007).
6. **"Tại sao tin XGBoost hơn LightGBM khi gần bằng nhau?"** → Recall nhỉnh hơn + SHAP chính xác cho cây; khác biệt nhỏ đã qua kiểm định, và cho thấy tín hiệu nằm ở đặc trưng.
7. **"Mô hình này giúp giáo viên thế nào trong thực tế?"** → Dashboard chỉ liệt kê sinh viên *còn theo học*, kèm giải thích SHAP theo mốc; cảnh báo dựa trên im lặng VLE; ngưỡng chọn theo chính sách (recall ≥ 0,9 → precision 0,993).

---

# Mẹo trình bày (chuẩn hội thảo)

- **Phân vai:** nếu trình bày nhóm, chia slide theo người: 1–5 (giới thiệu + đóng góp), 6–8 (dữ liệu + phương pháp), 9–13 (kết quả), 14–16 (giới hạn + kết luận). Người nói slide 10 phải là người nắm chắc nhất.
- **Nhịp:** ~1 phút/slide nội dung; dừng lại 2 giây sau mỗi kết quả để hội đồng kịp nhìn hình.
- **Đừng đọc slide.** Slide có chữ ít; phần giải thích (mục 💡) là thứ bạn *nói*.
- **Con số:** thuộc 4 con số vàng: recall 0,93 (cuối khóa, toàn bộ) / 0,841 (còn theo học) / khoảng cách CI loại trừ 0 / Jaccard 0,69 vs ngẫu nhiên 0,12.
- **Khi bí:** "Đây là điểm hay, nhóm em đã ghi nhận trong phần giới hạn/hướng phát triển" — luôn an toàn và trung thực.

---

*File slide: `reports/slides/Paper_Talk_EN.pdf` — build lại: `tectonic reports/slides/Paper_Talk_EN.tex`.*
