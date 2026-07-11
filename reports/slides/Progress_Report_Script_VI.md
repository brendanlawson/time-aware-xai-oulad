DSP391m · Nhóm 1
# Kịch bản thuyết trình — đọc từng từ (bộ slide **Báo cáo tiến độ · Phase 2 Benchmarking**, `progress_report.html`)

**Đề tài:** Học máy có khả năng giải thích, nhận biết theo thời gian, để phát hiện sớm sinh viên có nguy cơ học tập kém trên bộ dữ liệu OULAD.
**Phạm vi:** trọng tâm là **phần model của Đức — Phase 2 (Benchmarking)**, trình bày theo đúng hai mục báo cáo Đức phụ trách: *Methodology (Model Selection)* và *Model Development (Architecture, Training Procedure)*. Phần dữ liệu đã trình bày trọn ở Task 3 — chỉ neo một câu "test cố định, không rò rỉ", không nhắc lại.

Mở `reports/slides/progress_report.html` bằng trình duyệt (**F** = toàn màn hình, **Space** = slide kế). Vừa nói vừa chỉ vào bảng/biểu đồ. Người trình bày: **Đức**. Tổng thời lượng ≈ **9–11 phút**.

> Bộ slide **12 trang**: 1 bìa, 2 trang tiêu đề phần (lướt, không đọc), **9 trang nội dung** (3–9, 11, 12).
> Mọi con số sinh trực tiếp từ CSV: `imbalance_comparison.csv` (baseline no-resample), `cv_summary.csv` (CV 5×5), `model_friedman.csv` + `model_pairwise_wilcoxon.csv` (kiểm định). Tái lập: `python tools/build_revealjs_report.py`.

---

## Kịch bản (Đức nói liền một mạch)

**Slide 1 — Trang bìa**
Em chào thầy/cô và các bạn. Em là Đức, Modeling Lead của Nhóm 1. Ở Task 3 nhóm đã trình bày trọn phần dữ liệu; hôm nay em báo cáo tiến độ bước kế tiếp do em phụ trách — **Phase 2: huấn luyện và so tuyển các mô hình ứng viên**. Em sẽ đi theo bốn phần: vì sao chọn năm thuật toán này; cấu hình và quy trình huấn luyện; kết quả so tuyển; và hai lớp kiểm chứng độ tin cậy của kết quả. Cuối cùng là kế hoạch các pha còn lại của nhóm.

*(Slide 2 — tiêu đề phần "Phase 2 — Benchmarking": lướt qua)*

**Slide 3 — Lựa chọn mô hình: vì sao 5 thuật toán này?**
*(chỉ theo từng hàng của bảng)*
Trước hết là câu hỏi *Model Selection* — vì sao lại là năm thuật toán này. **Logistic Regression** là baseline tuyến tính chuẩn, hệ số đọc được trực tiếp nên tự nó đã giải thích được. **Random Forest** đại diện họ bagging cây — bền với nhiễu và ngoại lai, gần như không phải tinh chỉnh. **XGBoost** là boosting cây — hiện vẫn là lựa chọn hàng đầu cho dữ liệu dạng bảng, và quan trọng với đề tài của nhóm: nó hỗ trợ **SHAP TreeExplainer** nên tính giải thích rất tốt. **LightGBM** cùng họ boosting nhưng tối ưu tốc độ — làm đối chứng trong cùng một họ. Và **ANN**, mạng nơ-ron hai lớp ẩn, là đại diện phi tuyến *khác họ cây*. Như hai gạch đầu dòng cuối: năm thuật toán phủ **ba họ mô hình** khác nhau nên kết luận không lệ thuộc vào một họ; và cả năm đều xuất hiện trong các nghiên cứu nền trên OULAD, nên kết quả của nhóm **so sánh được với văn liệu**.

**Slide 4 — Kiến trúc & cấu hình huấn luyện**
*(chỉ vào cột cấu hình)*
Về *Model Architecture*: nguyên tắc của em là **cấu hình gốc, tối thiểu can thiệp**. Logistic Regression chỉ nâng `max_iter` lên một nghìn để hội tụ. Random Forest giữ mặc định, chạy song song. XGBoost dùng `tree_method=hist` cho nhanh và `eval_metric=logloss`. LightGBM giữ mặc định. ANN dùng hai lớp ẩn **sáu tư và ba hai** nơ-ron, tối đa năm trăm epoch kèm **early-stopping** chống quá khớp. Hai điểm nhấn: **mọi model dùng chung seed bốn hai** — công bằng và tái lập được; và giai đoạn này em **chưa tinh chỉnh siêu tham số** — triết lý là so tuyển ở cấu hình gốc trước, chọn xong ứng viên rồi mới tinh chỉnh, tránh thiên vị model nào được chăm kỹ hơn.

**Slide 5 — Quy trình huấn luyện**
*(chỉ theo bốn bước)*
Về *Training Procedure*, mỗi model đi qua đúng bốn bước. **Một**: nạp split cố định của mốc một trăm phần trăm — chính là split đã chốt ở Task 3, không có sinh viên nào nằm ở cả train lẫn test, mười chín trên mười chín kiểm thử rò rỉ đạt. **Hai**: tiền xử lý **fit trên train** rồi mới transform test — trung vị, ngưỡng winsorize, encoder, scaler đều chỉ học từ train. **Ba**: fit trên train, dự đoán trên test giữ riêng. **Bốn**: chấm **bảy chỉ số**, xếp hạng theo recall lớp nguy cơ. Lưu ý quan trọng: đây là kết quả **baseline, chưa tái lấy mẫu** — Phase 4 ngay sau sẽ áp bốn kỹ thuật cân bằng lớp lên đúng quy trình này, nên hai phần so sánh trước–sau được với nhau. Và vì bỏ sót một sinh viên nguy cơ đắt hơn nhiều một cảnh báo nhầm, chỉ số trọng tâm là **recall** và **PR-AUC**, không phải accuracy.

**Slide 6 — Kết quả so tuyển @ mốc 100%**
*(đứng ở biểu đồ, chỉ vào nhóm cột XGBoost)*
Đây là bức tranh kết quả. Mỗi nhóm cột là một model với bốn chỉ số chính. Có thể thấy các mô hình **cây** — XGBoost, LightGBM, Random Forest — bám nhau rất sát và đều rất cao; **XGBoost** dẫn đầu về recall, cột đỏ đầu tiên. Logistic Regression thấp nhất nhưng cũng không kém xa, cho thấy tín hiệu trong đặc trưng của nhóm là mạnh và tuyến tính bắt được phần lớn.

**Slide 7 — Bảng hiệu năng đầy đủ, 7 chỉ số**
*(chỉ vào bốn thẻ số, rồi đọc hàng đầu bảng)*
Bảng đầy đủ, sinh trực tiếp từ file CSV kết quả. **XGBoost** đứng đầu: recall **không phẩy chín ba ba**, F1 **không phẩy chín năm mốt**, PR-AUC **không phẩy chín chín không**, và Brier — chỉ số chất lượng xác suất, càng thấp càng tốt — không phẩy không ba chín. **LightGBM** ngay sau: recall không phẩy chín ba mốt nhưng **nhỉnh nhất về PR-AUC** không phẩy chín chín mốt. ANN đạt không phẩy chín hai ba, Random Forest không phẩy chín hai mốt, Logistic Regression không phẩy chín một tám. Khoảng cách giữa các model là **nhỏ** — vậy câu hỏi tự nhiên là: chênh lệch nhỏ thế thì có đáng tin không, hay chỉ là may rủi của một lần chia dữ liệu? Hai slide tiếp theo trả lời đúng câu đó.

**Slide 8 — Độ tin cậy: CV 5-fold × 5 seed**
*(chỉ vào cột μ ± σ)*
Lớp kiểm chứng thứ nhất: đánh giá chéo **năm fold, lặp qua năm seed** — tức hai lăm lần fit cho mỗi model, và tiền xử lý được lặp lại **bên trong từng fold** để không rò rỉ. Kết quả: độ lệch chuẩn của recall chỉ khoảng **không phẩy không không năm** — cực kỳ ổn định, nghĩa là con số không ăn may theo cách chia fold. Và thứ hạng trong CV **khớp** với thứ hạng trên test giữ riêng: XGBoost và LightGBM vẫn dẫn đầu. Baseline của em là đáng tin.

**Slide 9 — Xếp hạng có ý nghĩa thống kê không?**
*(chỉ vào cột p-value)*
Lớp kiểm chứng thứ hai: kiểm định thống kê trên hai lăm fold ghép cặp. Kiểm định **Friedman** cho từng chỉ số — cột p-value toàn bộ nhỏ hơn mười mũ trừ mười hai, tức khác biệt giữa các model là **thật**, không phải nhiễu. Đi sâu bằng post-hoc **Wilcoxon có hiệu chỉnh Holm** trên recall: XGBoost thắng **bốn trên bốn** cặp so sánh một cách có ý nghĩa. Bức tranh cuối cùng: **XGBoost dẫn recall, LightGBM dẫn các chỉ số tổng hợp** — và vì bài toán của nhóm là cảnh báo sớm đặt recall lên trước, cộng thêm yêu cầu giải thích được bằng TreeExplainer cho Phase 5, em chốt **XGBoost là ứng viên chính** đi tiếp.

*(Slide 10 — tiêu đề phần "Kế hoạch & Kết luận": lướt qua)*

**Slide 11 — Các việc sắp tới để hoàn thiện bài làm**
*(chỉ vào từng dòng của bảng lộ trình)*
Kế hoạch tiếp theo của nhóm, theo đúng luồng phân công. **Một** — em làm Phase 4: áp bốn kỹ thuật xử lý mất cân bằng — **no-resample, class-weight, SMOTE, ADASYN** — lên chính năm mô hình này, vẽ biểu đồ trước–sau, trả lời RQ3. **Hai** — bạn Khoa chạy thực nghiệm qua **sáu mốc thời gian** dựng đường cong hiệu năng, trả lời RQ1. **Ba** — bạn Bình làm lớp giải thích **SHAP/LIME** và đo độ ổn định giải thích cho RQ2. **Bốn** — bạn **An** dựng **Streamlit dashboard** đóng gói mô hình. **Năm** — bạn **Sơn** viết phần Introduction/Literature Review và danh mục tài liệu tham khảo; báo cáo cuối do Khoa tổng hợp.

**Slide 12 — Kết luận**
Tóm lại, Phase 2 của em đã hoàn thành với bốn ý chính. Năm thuật toán phủ ba họ mô hình được so tuyển **công bằng** — cùng split, cùng tiền xử lý, cùng seed, cấu hình gốc. **XGBoost** dẫn đầu recall không phẩy chín ba ba ngay ở baseline. Kết quả được kiểm chứng **hai lớp** — CV hai lăm fold ổn định và kiểm định Friedman–Wilcoxon xác nhận xếp hạng có ý nghĩa. Toàn bộ mã, bảng và biểu đồ nằm trong repo, chạy lại được bằng một script. Bước kế tiếp của em là Phase 4 xử lý mất cân bằng. Em xin cảm ơn thầy/cô và các bạn — em sẵn sàng trả lời câu hỏi.
