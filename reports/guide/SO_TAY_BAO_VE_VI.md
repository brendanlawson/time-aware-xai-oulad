# Sổ tay bảo vệ — Nhóm 1 DSP391m (đọc là hiểu, hiểu là nói được)

> Dành cho cả 6 người: **Phúc, Đức, Khoa, Bình, An, Sơn**. Mục tiêu: đọc xong bạn **kể lại được toàn bộ dự án** và **trả lời được cô Yến** đúng mảng của mình — không cần mở code. Mọi con số trong đây là **số thật** trích từ `reports/tables/*.csv` của repo (đường dẫn ghi kèm từng chỗ), không có số nào bịa. Bản chi tiết riêng cho phần model: `HIEU_PHAN_MODEL_TASK4.md` (cùng thư mục). Nhật ký thô của phiên khắc phục audit: `_process_log_2026-07-12.md`.
>
> Cách dùng nhanh: ai bận thì đọc **mục 1** (câu chuyện chung) + **mục 3** (7 vũ khí trung thực) + **phần của mình trong mục 4**. Vậy là đủ ra trận.

---

## Mục lục

1. [Câu chuyện 5 phút](#1-câu-chuyện-5-phút)
2. [Bản đồ repo cho người mới](#2-bản-đồ-repo-cho-người-mới)
3. [7 "vũ khí trung thực"](#3-7-vũ-khí-trung-thực--nói-ra-được-điểm-không-phải-giấu)
4. [Tủ câu hỏi theo vai](#4-tủ-câu-hỏi-theo-vai)
5. [Nhật ký khắc phục 2026-07-12](#5-nhật-ký-khắc-phục-2026-07-12-tóm-tắt)
6. [Checklist "chạy chốt" trước khi nộp báo cáo cuối](#6-checklist-chạy-chốt-renumber-trước-khi-nộp-báo-cáo-cuối)
7. [Việc còn lại & phân công](#7-việc-còn-lại--phân-công)

---

## 1. Câu chuyện 5 phút

### Dự án làm gì?

Dạy máy **nhìn hồ sơ học tập của sinh viên trên hệ thống học online (OULAD) rồi cảnh báo sớm em nào có nguy cơ Trượt hoặc Bỏ học** — cảnh báo **sớm cỡ nào thì còn tin được**, và **giải thích được vì sao** máy cảnh báo (SHAP/LIME), để giảng viên kịp can thiệp.

Pipeline một dòng:

> 7 bảng CSV OULAD → master table **32.593 lượt ghi danh × 33 cột** → cắt tại **6 mốc** 10/20/40/60/80/100% thời lượng khóa → **split cố định theo sinh viên** (test 5.756 SV) → benchmark **5 model** (LR/RF/XGBoost/LightGBM/ANN) → **XGBoost** thắng → chọn ngưỡng trên validation → giải thích SHAP/LIME + đo độ ổn định → kiểm fairness → (đang làm) dashboard Streamlit.

Hai con số nền phải thuộc: **32.593 là lượt ghi danh môn–kỳ** (sinh viên duy nhất là **28.785** — một bạn học nhiều môn); nhãn **at-risk = Fail + Withdrawn chiếm 52,8%** (17.208 lượt = 7.052 Fail + 10.156 Withdrawn) — tức là lớp **đa số nhẹ**, không phải thiểu số.

### Ba câu hỏi nghiên cứu và câu trả lời hiện tại

| RQ | Hỏi gì | Trả lời hiện tại (số thật) |
|---|---|---|
| **RQ1** | Model nào tốt nhất, đoán sớm tới đâu thì tin được? | XGBoost dẫn đầu (CV 5-fold × 5-seed + Friedman/Wilcoxon trên train). **Nói theo kiểu kép (dual-cohort):** trên **toàn bộ lượt ghi danh**, recall đạt ngưỡng tin cậy 0,80 **từ mốc 40%** (0.81 → 0.93 tại t=100); trên nhóm **còn-đang-học** — nhóm can thiệp được — chỉ đạt **ở t=100** (0.68 / 0.75 / 0.78 / 0.84 tại 40/60/80/100). Báo cáo cả hai, không chọn một. |
| **RQ2** | SHAP và LIME có nhất quán, ổn định không? | Ổn định **theo seed cao**: Jaccard top-10 = **0.69**, Spearman = **0.97**. Đồng thuận **SHAP↔LIME một phần**: Jaccard = **0.43** (đo trên n=100 dòng — đã nâng từ 30 ở lần chạy chốt). Top-10 dịch chuyển **dần và có trật tự** theo mốc thời gian (Spearman các mốc liền kề 0.87–0.93). |
| **RQ3** | Xử lý mất cân bằng ảnh hưởng gì tới accuracy VÀ giải thích? | Gần như không: 4 chiến lược (none/class_weight/SMOTE/ADASYN) chênh nhau **≤0,007** trên các chỉ số chính; về giải thích, Spearman importance **≈0,97 ở mọi cặp chiến lược**, Jaccard top-10 giữa các cặp 0,54–0,82 (chỉ xáo phần đuôi danh sách). Twist tự phát hiện: vì at-risk là **đa số 52,8%**, SMOTE mặc định thực chất **tăng mẫu lớp not-at-risk**. |

🎤 **Câu tổng khi cô bảo "tóm tắt đề tài":** *"Bọn em dự đoán sinh viên nguy cơ Trượt/Bỏ học trên OULAD tại 6 mốc tiến độ khóa, benchmark 5 thuật toán với split cố định theo sinh viên và cross-validation lặp; XGBoost tốt nhất, tin cậy từ mốc 40% trên toàn bộ lượt ghi danh — và bọn em trung thực báo cáo thêm nhóm còn-đang-học, nơi bài toán khó hơn. Mỗi dự đoán đều được giải thích bằng SHAP/LIME và bọn em đo luôn độ ổn định của chính lời giải thích đó."*

---

## 2. Bản đồ repo cho người mới

Nguyên tắc: **mọi bảng số nằm ở `reports/tables/*.csv`, mọi hình ở `reports/figures/`** — slide và báo cáo đều đọc từ đó, nên chạy lại tool là số tự khớp. Môi trường chạy chuẩn: conda **base** (Python 3.13 · scikit-learn 1.8.0 · numpy 2.3.5 — `environment.yml` đã pin đúng bộ này; xem `SETUP_VI.md`).

| Thư mục / file | Chứa gì | Chủ mảng | Lệnh chạy lại (từ gốc repo) |
|---|---|---|---|
| `data/raw/` | 7 CSV OULAD gốc (git-ignored) | Phúc | tải về rồi `python setup_raw_data.py` (đối chiếu MD5 với `data/oulad_md5_reference.txt` đã commit) |
| `data/interim/`, `data/checkpoints/` | master table + 6 dataset theo mốc (git-ignored, tái sinh được) | Phúc | `python -m src.data.time_utils` → `python -m src.data.build_master_table` → `python -m src.data.make_checkpoints` |
| `data/splits/` | **`test_student_ids.csv` — BẤT KHẢ XÂM PHẠM (đã commit)** + parquet train/test | Phúc | `python -m src.evaluation.make_split --materialise` (an toàn: mặc định chỉ LOAD danh sách id đã commit, không bao giờ tự tính lại) |
| `src/data/`, `src/features/` | pipeline đặc trưng (engagement, performance, master, checkpoint, preprocessing) | Phúc | (được các lệnh trên gọi) |
| `src/evaluation/` | split harness, make_split (có guard `--rederive`), Friedman/Wilcoxon | Phúc (+Khoa phần stat_tests) | — |
| `src/eda/` | tính toán EDA + style hình | Phúc | `python -m src.eda.eda` |
| `src/modeling/` | train 5 model × 6 mốc, predict, threshold | Đức (train/imbalance) + Khoa (time-aware/threshold) | `python -m src.modeling.train` (held-out) · `python -m src.modeling.train --cv` (CV 5×5 tại t=100) |
| `src/xai/` | SHAP (TreeExplainer cho model cây), LIME, stability (Jaccard/std) | Bình | (được tools gọi) |
| `tests/test_leakage.py` | **21 test tự động** (leakage, split, guard, banked) | Phúc chủ trì, cả nhóm hưởng | `pytest tests/` |
| `tools/` | ~19 script sinh bảng/hình/slide/docx một-phát-ăn-ngay | theo mảng (xem mục 6) | `python -m tools.<tên_script>` |
| `models/` | bundle `{model, ct, feat_names, stats}` dạng `*.joblib` (git-ignored) | An (đóng gói/deploy) | sinh bởi `python -m src.modeling.train` |
| `reports/tables/`, `reports/figures/` | **nguồn sự thật duy nhất** cho mọi con số/hình | Khoa tổng hợp | từng tool ở mục 6 |
| `reports/slides/`, `reports/guide/` | deck PDF (Beamer) + sổ tay (file này) | Khoa | `python -m tools.build_progress_deck` |
| `docs/` | bộ tài liệu Task 3 song ngữ (01_data_specification … 08_agreements); `docs/README_EN.md` là bản đồ 40 đầu việc STT | cả nhóm | `python -m tools.build_docx` |
| `notebooks/00…06` | bản notebook chạy được của từng chương | 00–04 Phúc · 05 Đức/Khoa · 06 Bình | Restart & Run All |

**Ai hỏi "kết quả X nằm đâu":** benchmark → `model_metrics.csv`, `cv_summary.csv`, `time_aware_best.csv`; RQ1 kép → `sensitivity_active_xgb.csv` / `_lgbm.csv` + hình `sensitivity_active_recall_xgb.png`; RQ3 → `imbalance_comparison.csv` + `xai_stability_strategies.csv`; RQ2 → `xai_stability_seeds.csv`, `xai_shap_vs_lime.csv`, `xai_stability_checkpoints.csv`; ngưỡng → `threshold_validation.csv`; fairness → `fairness_subgroups.csv` + `fairness_gaps.csv`; split → `split_report.csv`.

---

## 3. 7 "vũ khí trung thực" — nói ra ĐƯỢC điểm, không phải giấu

Cả 7 chuyện dưới đây đều là **nhóm tự phát hiện, tự đo, tự văn bản hóa**. Trước cô, kể chủ động — đó là bằng chứng nhóm hiểu sâu. Tuyệt đối không nói kiểu "bị phát hiện ra lỗi".

### Vũ khí 1 — Dual-cohort: tách nhóm còn-đang-học (RQ1)

**Hiện tượng:** nhãn at-risk gồm cả Withdrawn, mà 59% nhóm nguy cơ là Bỏ học và nhiều em rút **rất sớm** — ngay mốc 10% đã có 4.833/32.593 lượt ghi danh rút trước cutoff (923 trong test). "Đoán" các em đã nghỉ thì không phải tài, và cũng không can thiệp được nữa.

**Con số thật** (`sensitivity_active_xgb.csv`, test, XGBoost):

| Mốc | Recall toàn bộ | Recall còn-đang-học | Số đã rút trước mốc (test) |
|---|---|---|---|
| 40% | 0.8107 | **0.6782** | 1.437 |
| 60% | 0.8703 | **0.7490** | 1.687 |
| 80% | 0.8969 | **0.7792** | 1.859 |
| 100% | 0.9298 | **0.8412** | 1.953 |

LightGBM cho hình dạng y hệt (active t=100 = 0.8363) → kết luận không phụ thuộc một model. Có hình vẽ sẵn: `reports/figures/sensitivity_active_recall_xgb.png` (2 đường + vạch 0,80). Khung lý thuyết: `docs/01_data_specification/Target_Variable_Definition_EN.md` §5 — hai estimand: *phân loại kết cục cuối khóa* (so được với văn liệu, Adnan/Tomasevic cũng giữ full cohort) và *cảnh báo sớm để can thiệp* (chỉ có nghĩa trên nhóm còn học). Đây là **vấn đề định nghĩa quần thể, không phải leakage** — nhãn không hề lọt vào đặc trưng.

🎤 *"Bọn em phát hiện nhãn nguy cơ bị chi phối bởi nhóm đã bỏ học sớm, nên báo cáo song song hai cohort: toàn bộ lượt ghi danh để so với văn liệu — đạt recall 0,80 từ mốc 40% — và nhóm còn-đang-học là nhóm can thiệp được — chỉ đạt ở cuối khóa. Mọi phát biểu 'tin cậy từ 40%' của bọn em đều ghi rõ cohort."*

### Vũ khí 2 — SMOTE đảo chiều (RQ3)

**Hiện tượng:** với mapping {Fail, Withdrawn} = at-risk, lớp at-risk chiếm **52,8%** — là **đa số nhẹ** (tỷ lệ mất cân bằng chỉ 1,12). Hệ quả ít ai để ý: SMOTE/ADASYN mặc định oversample lớp thiểu số, tức ở đây chúng **tăng mẫu lớp not-at-risk** — ngược với hình dung "SMOTE cứu lớp nguy cơ hiếm" trong slide môn học (con số 68/32 trên slide chỉ là minh họa, không phải OULAD).

**Con số thật** (`imbalance_comparison.csv`, XGBoost @t=100, test): recall none 0.9307 · SMOTE 0.9298 · class_weight 0.9295 · ADASYN 0.9292; F1 từ 0.9486 đến 0.9508 — **mọi chiến lược chênh nhau cỡ ≤0,007**. Kết luận: pipeline chuẩn (model_metrics, đường cong RQ1) giữ đúng bước SMOTE của proposal — so sánh Phase 4 chứng minh lựa chọn này không ảnh hưởng gì; deck Phase-2 trình bày hàng baseline không-resample cũng vì thế. RQ3 trở thành **câu hỏi robustness có kiểm soát**, và câu trả lời là "robust".

🎤 *"Nhãn at-risk của bọn em là 52,8% — đa số nhẹ — nên SMOTE mặc định thực chất tăng mẫu lớp not-at-risk. Bọn em phát hiện điều này, vẫn chạy đủ 4 chiến lược: chênh lệch ≤0,005, và câu chuyện giải thích cũng giữ nguyên (Spearman ≈0,97 mọi cặp) — tức kết luận không phụ thuộc cách xử lý mất cân bằng."*

### Vũ khí 3 — Ngưỡng chọn trên validation, test chỉ chấm một lần

**Hiện tượng:** giao thức cũ từng dò ngưỡng trực tiếp trên test (một dạng lạc quan hóa). Nhóm đã thay bằng giao thức sạch: chọn ngưỡng trên **out-of-fold validation 5-fold của train**, rồi mang sang test chấm **đúng một lần**.

**Con số thật** (`threshold_validation.csv`, XGBoost @t=100):

| Policy | Ngưỡng chọn trên validation | Test recall | Test precision | Test F1 |
|---|---|---|---|---|
| default | 0.50 | 0.9298 | 0.9718 | 0.9503 |
| max-F1 | **0.56** | 0.9262 | 0.9754 | 0.9502 |
| Youden | 0.56 | 0.9262 | 0.9754 | 0.9502 |
| recall ≥ 0,9 | 0.86 | 0.9002 | 0.9931 | 0.9444 |

Điểm ăn tiền: policy F1 chọn ra **0.56**, cho kết quả test **gần như y hệt ngưỡng mặc định** (F1 0.9502 vs 0.9503), và số validation chuyển sang test **gần như không lệch** → chứng minh hồi tố rằng các con số cũ không phải sản phẩm của tune-trên-test.

🎤 *"Ngưỡng được chọn trên validation out-of-fold của train; test chỉ chấm một lần ở ngưỡng đã chốt. Ngưỡng tối ưu hóa F1 ra 0,56 — kết quả trên test y hệt ngưỡng mặc định — nên kết quả trước đây không hề lạc quan hóa; và nếu trường muốn recall ≥ 0,9 kèm rất ít báo nhầm thì có sẵn ngưỡng 0,86 với precision 0,993."*

### Vũ khí 4 — Fairness: đã đo, không chỉ hứa

**Hiện tượng:** tài liệu ethics của nhóm hứa "disaggregated metrics theo nhóm nhân khẩu học" — giờ đã có bảng thật (`tools/make_fairness_report.py`).

**Con số thật** (`fairness_gaps.csv`, XGBoost @t=100, test, ngưỡng 0.5, chỉ tính nhóm n≥50): gap recall lớn nhất theo từng thuộc tính — **imd_band 6,6 điểm** (0.894–0.960, 11 mức) · region 4,1 · highest_education 3,0 · **gender 2,6** (nữ 0.915 / nam 0.941) · disability 1,7 (Y 0.945 còn *cao hơn* N 0.928) · age_band 1,6. Gap FPR mọi thuộc tính ≤5,3 điểm. Chi tiết từng nhóm: `fairness_subgroups.csv`.

🎤 *"Bọn em đo recall và false-positive-rate tách theo giới tính, vùng, mức nghèo IMD, trình độ, độ tuổi, khuyết tật. Chênh lệch lớn nhất là 6,6 điểm recall giữa các mức IMD — không có nhóm nào bị bỏ rơi nghiêm trọng, và sinh viên khuyết tật thực tế được recall cao hơn trung bình."*

### Vũ khí 5 — 787.170 dòng trùng trong studentVle: biết, giữ, và ghi rõ

**Hiện tượng:** bảng clickstream `studentVle` của OULAD **gốc** chứa 787.170 dòng trùng hoàn toàn (7,4%) — quirk của dataset nguồn (nhiều phiên click cùng ngày cùng site được ghi thành nhiều dòng giống hệt), không phải lỗi pipeline của mình.

**Quyết định** (văn bản hóa tại `docs/03_cleaning/Cleaning_Methods_EN.md` §2.1): **giữ và cộng dồn** số click — vì không có căn cứ nào để khẳng định dòng trùng là "thừa" thay vì hai lượt tương tác thật; xóa mới là can thiệp võ đoán. Giới hạn được ghi rõ trong docs.

🎤 *"Bọn em phát hiện 7,4% dòng studentVle trùng hoàn toàn ngay trong dữ liệu gốc — đã kiểm bằng MD5 file nguồn. Bọn em quyết định giữ và cộng dồn, ghi rõ quyết định và giới hạn trong tài liệu cleaning, thay vì lặng lẽ xóa dữ liệu mà không có căn cứ."*

### Vũ khí 6 — Errata "banked": 78 dòng (0,24%) và lịch chạy lại số

**Hiện tượng:** bài assessment được "bank" (bảo lưu từ kỳ trước, `is_banked=1`) trước đây không được tính là "đã bao phủ deadline", khiến **78/32.593 dòng (0,24%)** bị gắn cờ `not_submitted=1` sai ở t=100. Đã sửa trong `src/data/build_performance_features.py` + test tự động mới; banked vẫn **không** được tính vào số bài đã nộp/điểm trung bình (quyết định giữ nguyên, có ghi trong docs).

**Điều phải nói thẳng trong nhóm:** các bảng kết quả đã commit hiện tại được tính **trước** fix này. Ảnh hưởng kỳ vọng ~0,24% dòng — không đổi kết luận — nhưng **bắt buộc chạy checklist mục 6 (renumber) trước khi chốt số vào báo cáo cuối** để bảng, hình, slide đồng bộ với code đã sửa.

🎤 *(nếu cô soi ra chênh lệch nhỏ giữa hai bản bảng)* *"Đúng ạ — bọn em tự phát hiện một lỗi 0,24% dòng ở đặc trưng nộp-bài liên quan assessment được bảo lưu, đã sửa kèm test tự động, ghi errata trong tài liệu cleaning, và toàn bộ bảng số được chạy lại trước báo cáo cuối."*

### Vũ khí 7 — Split đông cứng + guard chống ghi đè

**Hiện tượng:** `data/splits/test_student_ids.csv` (5.756 SV test) là **chân lý đã commit** — mọi kết quả trên cùng một đề thi. Nguy cơ từng tồn tại: chạy lại `make_split` sẽ tự tính lại split, và do sklearn đổi phiên bản, **4.574/5.756 id sẽ đổi** — tức toàn bộ kết quả hết so sánh được. Nhóm đã thêm **guard**: chạy mặc định chỉ **LOAD** danh sách id đã commit; muốn tính lại phải cố ý gõ cờ `--rederive` (quy ước: chỉ khi cả nhóm biểu quyết). Có test tự động `test_make_split_reuses_committed_ids` canh chuyện này.

Số kiểm chứng của split (`split_report.csv`): train 26.104 dòng / test 6.489 dòng (5.756 SV), tỷ lệ at-risk 0.530/0.520, **0 sinh viên chồng lấn**, giống hệt nhau ở cả 6 mốc.

🎤 *"Tập test được định nghĩa một lần theo id_student, commit vào git, và code có guard: chạy lại pipeline không bao giờ vô tình sinh split mới. Vì thế 6 điểm trên đường cong thời gian là so sánh được — cùng một đề thi, cùng 5.756 sinh viên."*

---

## 4. Tủ câu hỏi theo VAI

Mỗi người thuộc phần mình + đọc lướt phần người khác (cô hay hỏi chéo). Đáp án viết đúng độ dài nói ra miệng.

### 4.1 Phúc — Implementation Lead (pipeline, split, leakage)

1. **"Chia train/test thế nào?"** → 🎤 *"Chia một lần theo `id_student`, stratify theo nhãn at-risk, seed 42: test 20% = 5.756 sinh viên (6.489 lượt ghi danh). Danh sách id test được commit vào git và dùng y nguyên cho cả 6 mốc — kiểm chứng trong `split_report.csv`: 0 sinh viên chồng lấn."*
2. **"Vì sao chia theo sinh viên mà không theo dòng?"** → 🎤 *"Vì 32.593 dòng chỉ có 28.785 sinh viên duy nhất — một bạn học nhiều môn. Chia theo dòng thì cùng một bạn nằm cả hai phía, model 'nhận mặt' người quen thay vì học tín hiệu — một dạng leakage."*
3. **"Chống leakage thời gian ra sao?"** → 🎤 *"Hàm cắt mốc loại mọi bản ghi có ngày sau checkpoint; encoder/scaler/imputer đều chỉ fit trên train; và có bộ 21 test tự động kiểm các luật này ở cả 6 mốc — pass hết."*
4. **"Dữ liệu gốc có gì đảm bảo không bị sửa?"** → 🎤 *"7 file CSV được đối chiếu MD5 với file tham chiếu đã commit `data/oulad_md5_reference.txt` — `python setup_raw_data.py` xác minh 7/7 khớp trước mọi lần build."*
5. **"787.170 dòng trùng trong studentVle xử lý sao?"** → xem Vũ khí 5. Thêm ý: *"trùng nằm ngay trong file gốc đã verify checksum — không phải pipeline mình tạo ra."*
6. **"Nếu ai lỡ chạy lại make_split thì sao?"** → 🎤 *"Không sao — mặc định script chỉ load danh sách test đã commit. Muốn tính lại phải gõ cờ `--rederive`, và quy ước nhóm là việc đó cần cả nhóm quyết vì nó đổi 4.574/5.756 id."*

### 4.2 Đức — Modeling Lead (5 model, imbalance, CV)

1. **"Vì sao chọn 5 thuật toán này?"** → 🎤 *"Logistic Regression làm mốc tham chiếu tuyến tính; RF/XGBoost/LightGBM là họ ensemble — chính là khoảng trống mà benchmark của Tomasevic (2020) chưa phủ; ANN là MLP của sklearn làm đối chứng phi tuyến."*
2. **"Căn cứ nào nói XGBoost tốt nhất?"** → 🎤 *"Cross-validation 5-fold × 5-seed = 25 lượt trên train tại t=100: XGBoost recall 0.9307 ± 0.0054, LightGBM 0.9294 ± 0.0056 — dẫn đầu và cực ổn định (std ~0,005). Khác biệt giữa các model được kiểm bằng Friedman rồi Wilcoxon từng cặp (`model_friedman.csv`, `model_pairwise_wilcoxon.csv`) — tất cả trên train, không đụng test."* (Thành thật kèm: ở mốc sớm t=10–20, LightGBM nhỉnh hơn một chút — `time_aware_best.csv`.)
3. **"SMOTE của em cân bằng lớp nào?"** → Vũ khí 2, thuộc lòng. Đây gần như chắc chắn là câu cô hỏi Đức.
4. **"Có tune hyperparameter không?"** → 🎤 *"Có — `tuning_results.csv`: tune XGBoost tại t=100 nâng PR-AUC từ 0.9907 lên 0.9913, tức +0.0006, trong khi recall còn giảm nhẹ. Cải thiện không bõ độ phức tạp nên bọn em giữ cấu hình chuẩn, ưu tiên tái lập được."*
5. **"Vì sao không dùng deep learning 'xịn'?"** → 🎤 *"Dữ liệu dạng bảng ~26 nghìn dòng train, 28 đặc trưng — văn liệu và kết quả của chính bọn em đều cho thấy gradient boosting là điểm mạnh nhất cho tabular cỡ này; ANN trong benchmark đã đại diện họ mạng nơ-ron và không vượt được XGBoost (F1 0.9460 vs 0.9506)."*
6. **"Imbalance ratio bao nhiêu mà phải xử lý?"** → 🎤 *"Chỉ 1,12 — rất nhẹ, vì at-risk là 52,8%. Bọn em không xử lý để 'cứu' lớp hiếm, mà chạy 4 chiến lược như một thí nghiệm robustness có kiểm soát cho RQ3 — kết quả là robust."*

### 4.3 Khoa — Methodology Lead (time-aware, RQ1, threshold, kiểm định)

1. **"Trả lời RQ1 đi."** → 🎤 *"XGBoost là model tốt nhất từ mốc 40% trở đi. Về độ sớm, bọn em trả lời kép: trên toàn bộ lượt ghi danh — khung so sánh với văn liệu — recall vượt 0,80 từ mốc 40% (0.81 lên 0.93 ở cuối khóa); trên nhóm còn-đang-học — nhóm mà nhà trường thực sự can thiệp được — recall là 0.68/0.75/0.78 tại 40/60/80% và chỉ chạm ngưỡng ở t=100 với 0.85. Cả hai đều nằm trong bảng `sensitivity_active_xgb.csv` và có hình riêng."*
2. **"Vì sao recall nhóm còn học lại thấp hơn nhiều vậy?"** → 🎤 *"Vì nhóm toàn bộ chứa những em đã rút trước mốc — riêng test tại t=40 là 1.437 em — mà các em đó gần như đoán trúng miễn phí do hành vi im lặng hoàn toàn. Loại ra thì tỷ lệ at-risk giảm từ 52% còn 38% và bài toán thành dự-báo-tương-lai thật sự. Đây là vấn đề định nghĩa quần thể, không phải leakage — nhãn không hề nằm trong đặc trưng."*
3. **"Ngưỡng 0,5 ở đâu ra, có tune trên test không?"** → Vũ khí 3, thuộc lòng cả 4 dòng bảng.
4. **"Kiểm định thống kê gì, trên dữ liệu nào?"** → 🎤 *"Friedman test trên các fold CV để hỏi 'các model có thực sự khác nhau không', rồi Wilcoxon signed-rank từng cặp. Toàn bộ trên kết quả cross-validation của train — test được niêm phong chỉ để chấm điểm cuối."*
5. **"Mốc nào model nào tốt nhất?"** → 🎤 *"t=10 và 20 là LightGBM (recall 0.71, 0.76 — chưa đạt chuẩn tin cậy), từ t=40 trở đi là XGBoost (0.81 → 0.93). Bảng `time_aware_best.csv` có cột reliable đánh dấu từ mốc nào đạt."*
6. **"So với nghiên cứu nền thì sao?"** → 🎤 *"Adnan et al. (2021) cũng dự đoán theo phần trăm thời lượng khóa trên OULAD và thấy tin cậy quãng 40–60% — kết quả full-cohort của bọn em khớp khung đó. Đóng góp thêm của bọn em là tách được nhóm còn-đang-học, điều Adnan không làm, cộng với lớp XAI và đo độ ổn định giải thích."*

### 4.4 Bình — XAI Lead (SHAP/LIME, stability)

1. **"Đặc trưng nào quan trọng nhất, có hợp lý không?"** → 🎤 *"`days_since_last_activity` — số ngày im lặng — với mean |SHAP| 3.57, bỏ xa mọi đặc trưng khác; thứ hai là `weighted_score_to_date` (2.08). Rất hợp lý sư phạm: im lặng kéo dài và điểm tích lũy thấp chính là hai tín hiệu giáo viên thật cũng nhìn."* (`xai_shap_importance.csv`)
2. **"Giải thích có ổn định không hay mỗi lần chạy một kiểu?"** → 🎤 *"Ổn định theo seed: chạy nhiều seed rồi so top-10 SHAP — Jaccard trung bình 0.75, tương quan hạng Spearman 0.97 trên 10 cặp. Câu chuyện toàn cục không đổi theo may rủi."* (`xai_stability_seeds.csv`)
3. **"SHAP và LIME đồng thuận một phần (Jaccard 0.43) — vậy tin cái nào?"** → 🎤 *"Đây là finding của RQ2 chứ không phải trục trặc: hai phương pháp khác bản chất — SHAP phân bổ đóng góp Shapley trên chính model, LIME fit hồi quy cục bộ trên dữ liệu nhiễu loạn quanh từng điểm. Bọn em nêu rõ hai giới hạn: đo trên n=100 dòng test, và LIME perturb biến one-hot như biến liên tục nên thêm nhiễu. Kết luận thực hành: dùng SHAP làm trục chính — với model cây nó là TreeExplainer tính chính xác, không phải xấp xỉ lấy mẫu — LIME làm đối chứng cục bộ."* (`xai_shap_vs_lime.csv`)
4. **"Lời giải thích có đổi theo thời gian không?"** → 🎤 *"Đổi dần và có trật tự: các mốc liền kề tương quan hạng 0.86–0.92; so mốc 10% với 100% thì Jaccard top-10 chỉ 0.18 — tức bộ tín hiệu đầu khóa và cuối khóa khác nhau thật, đúng kỳ vọng của bài toán time-aware, chứ không nhảy loạn."* (`xai_stability_checkpoints.csv`)
5. **"Cách xử lý mất cân bằng có làm đổi lời giải thích không?"** → 🎤 *"Gần như không — đây là nửa 'giải thích' của RQ3: cùng 1.500 dòng test, Jaccard top-10 giữa none và class_weight là 1.00 tuyệt đối; SMOTE↔ADASYN thấp nhất cũng 0.54; còn tương quan hạng toàn cục thì 0.97 ở mọi cặp. Resampling tổng hợp chỉ xáo nhẹ phần đuôi top-10."* (`xai_stability_strategies.csv`)
6. **"Jaccard top-k là gì?"** → 🎤 *"Lấy 10 đặc trưng quan trọng nhất của hai lần giải thích, chia kích thước phần giao cho phần hợp — 1.0 là trùng khít, 0 là không chung đặc trưng nào. Bọn em kèm Spearman trên toàn bộ bảng xếp hạng để không phụ thuộc mỗi ngưỡng top-10."*

### 4.5 An — Backend & Dashboard Lead (đóng gói, version, dashboard)

1. **"Model được đóng gói thế nào cho dashboard?"** → 🎤 *"Mỗi (model × mốc) là một bundle joblib tự-đủ trong `models/`: gồm model, bộ tiền xử lý ColumnTransformer đã fit, danh sách tên đặc trưng và thống kê đi kèm — dashboard chỉ cần load một file là dự đoán được trên dữ liệu thô, không lắp ráp thủ công."*
2. **"Vì sao phải pin phiên bản thư viện?"** → 🎤 *"Bọn em kiểm chứng thực tế: bundle train bằng scikit-learn 1.8 thì env sklearn 1.5 không load được ANN (lỗi unpickle MT19937), các model khác load kèm warning. Nên `environment.yml` pin đúng bộ đã kiểm chứng — Python 3.13, scikit-learn 1.8.0 — và dashboard bắt buộc chạy đúng env đó. Đây cũng là nguyên tắc Đức–An đã thống nhất trong kế hoạch phân công."*
3. **"Vì sao joblib mà không phải pickle?"** → 🎤 *"Quy ước kỹ thuật nhóm chốt từ đầu: joblib xử lý mảng numpy lớn trong model cây hiệu quả hơn, load nhanh hơn cho Streamlit."*
4. **"Dashboard sẽ hiển thị gì?"** → 🎤 *"Danh sách sinh viên được gắn cờ tại mốc đang chọn với xác suất nguy cơ ở ngưỡng đã chốt trên validation, kèm giải thích SHAP cục bộ cho từng em — giáo viên thấy được 'vì sao em này bị cờ' — đúng thiết kế Phase 6 trong proposal."*
5. **"Model đâu, sao repo không có file model?"** → 🎤 *"`models/` git-ignore vì là artifact tái sinh được: `python -m src.modeling.train` dựng lại từ dữ liệu đã verify MD5 với seed cố định. Cái được commit là thứ đảm bảo tái lập: danh sách test, checksum dữ liệu, và code."*

### 4.6 Sơn — Literature Review Lead (bối cảnh văn liệu)

1. **"Đề tài đứng ở đâu trong văn liệu?"** → 🎤 *"Bọn em rà 27 bài tiêu biểu 2019–2026 theo concept matrix (corpus đầy đủ 30 bài trong phụ lục proposal): ba dòng — dự đoán time-aware, XAI, và xử lý mất cân bằng — đều đã được nghiên cứu riêng lẻ nhưng chưa từng tích hợp đồng thời trên OULAD. Đề tài nhắm đúng ô trống đó."*
2. **"Adnan 2021 làm gì, khác gì các em?"** → 🎤 *"Adnan et al. (IEEE Access 2021) dự đoán at-risk tại các phần trăm thời lượng khóa trên OULAD, thấy tin cậy quãng 40–60% — bọn em khớp khung đó trên full cohort. Khác biệt: Adnan không tách nhóm còn-đang-học, không đo độ ổn định giải thích — hai thứ bọn em bổ sung."*
3. **"Tomasevic 2020 thì sao?"** → 🎤 *"Tomasevic et al. (Computers & Education 2020) so sánh các kỹ thuật supervised trên OULAD nhưng không có họ ensemble — đóng góp số 2 của bọn em là thêm Random Forest, XGBoost, LightGBM vào đúng benchmark đó."*
4. **"OULAD là dataset gì, có đáng tin không?"** → 🎤 *"Dataset công khai của Open University Anh, công bố trên Scientific Data (Kuzilek et al., 2017): 32.593 lượt ghi danh, 22 module-presentation, 7 bảng quan hệ, đã ẩn danh tại nguồn, giấy phép CC-BY 4.0 — dataset chuẩn mực nhất của learning analytics."*
5. **"Trích dẫn theo chuẩn nào?"** → 🎤 *"IEEE, đúng yêu cầu môn; khung viết lit review theo Webster & Watson (2002) — concept-centric chứ không liệt kê từng bài."*

---

## 5. Nhật ký khắc phục 2026-07-12 (tóm tắt)

Phiên làm việc xuất phát từ **hai bản audit độc lập**; mọi phát hiện được **tái lập bằng code trên dữ liệu thật trước khi sửa**. Chi tiết thô: `_process_log_2026-07-12.md`.

| # | Phát hiện | Đã làm gì | Bằng chứng / file |
|---|---|---|---|
| 1 | Cohort chứa SV đã rút làm recall sớm đẹp hơn thực chất (923 SV test đã rút trước t=10) | Phân tích dual-cohort cho cả xgb lẫn lgbm + hình + viết §5 Target doc (2 estimand) + sửa README/RQ1 | `sensitivity_active_{xgb,lgbm}.csv`, `sensitivity_active_recall_*.png` |
| 2 | at-risk 52,8% là **đa số nhẹ** → SMOTE mặc định tăng not-at-risk, ngược tiền đề README cũ | Sửa README (minority→majority); giữ so sánh 4 chiến lược; đo thêm tác động lên giải thích | `imbalance_comparison.csv`, `xai_stability_strategies.csv` |
| 3 | Ngưỡng từng được dò trực tiếp trên test | Tool mới chọn ngưỡng trên OOF validation 5-fold, test chấm 1 lần; kết quả chứng minh số cũ không lạc quan hóa | `tools/make_threshold_validation.py` → `threshold_validation.csv` |
| 4 | Bug banked: 78/32.593 dòng (0,24%) gắn `not_submitted=1` sai ở t=100 | Fix `build_performance_features.py` + test mới + errata trong Cleaning doc; **cần renumber trước báo cáo cuối** | test `test_banked_assessment_covers_its_deadline` PASS |
| 5 | `make_split` chạy lại sẽ ghi đè split (sklearn drift đổi 4.574/5.756 id) | Guard: mặc định chỉ LOAD id đã commit; thêm cờ `--rederive`; test mới; sửa mọi docs từng hướng dẫn lệnh nguy hiểm | test `test_make_split_reuses_committed_ids` PASS |
| 6 | studentVle có 787.170 dòng trùng hoàn toàn (7,4%) từ nguồn | Văn bản hóa quyết định giữ + cộng dồn | `docs/03_cleaning/Cleaning_Methods_EN.md` §2.1 |
| 7 | Env `dsp` cũ (sklearn 1.5) không load được ANN bundle, crash savefig/fit | `environment.yml` viết lại pin bộ đã kiểm chứng (py3.13 · sklearn 1.8.0 · numpy 2.3.5); SETUP_VI thêm mục tương thích bundle | test load trực tiếp |
| 8 | Thiếu LICENSE; pyproject đòi Python ~=3.14; Makefile trỏ file không tồn tại | LICENSE MIT mới; `requires-python >=3.10`; Makefile trỏ pipeline thật | ls/pip |
| 9 | Ethics doc hứa fairness metrics nhưng chưa có | Tool + bảng mới | `tools/make_fairness_report.py` → `fairness_{subgroups,gaps}.csv` |
| 10 | RQ3 mới trả lời nửa "accuracy", thiếu nửa "giải thích" | Tool SHAP-per-strategy | `tools/make_xai_by_strategy.py` → `xai_stability_strategies.csv` |
| 11 | README ghi "Students: 32,593" (thực ra là lượt ghi danh); Step0 PDF trống ngày+chữ ký; xlsx phân công lỗi thời | README sửa thành "Enrolments 32,593 (28,785 students)"; việc ký Step 0 + cập nhật xlsx đưa vào mục 7 | `pypdf`/`pandas` kiểm chứng |
| 12 | SHAP↔LIME đo trên mẫu LIME giới hạn; LIME perturb one-hot như biến liên tục | Nâng LIME 30→100 dòng ở lần chạy chốt (Jaccard 0.25→0.43); giới hạn one-hot ghi rõ trong docs; đáp án chuẩn ở mục 4.4 câu 3 | `xai_shap_vs_lime.csv` |
| — | Provenance dữ liệu chỉ tự-ghi manifest, chưa có chuẩn đối chiếu | Commit `data/oulad_md5_reference.txt` (7 MD5); `setup_raw_data.py` giờ đối chiếu với reference; đã chạy lại 7/7 khớp | `data/oulad_md5_reference.txt` |
| — | Suite test 19 → **21** (2 test mới ở #4, #5) | Toàn bộ pass trên env base | `pytest tests/` |

---

## 6. Checklist "chạy chốt" (renumber) trước khi nộp báo cáo cuối

> ✅ **Đã thực thi lần đầu 2026-07-12** bằng `bash tools/renumber.sh` (36 phút, 21/21 test PASS, LIME nâng 30→100 dòng). Nếu code/data còn thay đổi thì chạy lại trước khi nộp; xoá `.renumber_stamps/` để chạy lại từ đầu.

**Vì sao phải chạy:** fix banked (#4) nằm trong code nhưng các bảng đã commit tính từ **trước** fix. Chạy chốt một lượt để bảng ↔ code ↔ báo cáo khớp nhau 100%. **Chỉ chạy khi cả nhóm sẵn sàng chốt số** — bước train lại tốn ~1–2 giờ. Mọi bảng/hình/deck/docx đều đọc từ CSV nên sau khi chạy xong, số mới tự lan tới slide và báo cáo khi rebuild.

**Điều kiện:** đúng env đã kiểm chứng (conda **base**: py3.13 · sklearn 1.8.0 · numpy 2.3.5 — hoặc env tạo từ `environment.yml` mới). Chạy từ gốc repo `D:\dsp`.

```bash
# 0) Xác minh dữ liệu gốc: 7/7 MD5 phải khớp reference đã commit
python setup_raw_data.py

# 1) Dựng lại pipeline dữ liệu (fix banked sẽ đổi 78 dòng đặc trưng ở t=100)
python -m src.data.time_utils
python -m src.data.build_master_table
python -m src.data.make_checkpoints

# 2) Materialise split — AN TOÀN nhờ guard: chỉ LOAD test_student_ids.csv đã commit
python -m src.evaluation.make_split --materialise

# 3) Toàn bộ test tự động phải PASS (21 test)
pytest tests/

# 4) XÓA artifact train cũ rồi train lại — BẮT BUỘC xóa, vì train.py có resume:
#    nó bỏ qua mọi (model × mốc) đã có metrics + bundle, không xóa là số cũ ở lại.
#    (PowerShell: Remove-Item models\*.joblib, reports\tables\model_metrics.csv, reports\tables\cv_metrics.csv)
python -m src.modeling.train          # 5 model × 6 mốc, ghi model_metrics.csv + bundle (~1–2h)
python -m src.modeling.train --cv     # CV 5-fold × 5-seed tại t=100 → cv_metrics/cv_summary

# 5) Sinh lại mọi bảng/hình phân tích, theo đúng thứ tự này
python -m tools.make_imbalance_comparison
python -m tools.make_xai_analysis
python -m tools.make_xai_by_strategy
python -m tools.make_threshold_validation
python -m tools.make_fairness_report
python -m tools.sensitivity_active --plot
python -m tools.sensitivity_active --model lgbm --plot
python -m tools.make_eval_analysis

# 6) Rebuild deliverables (đọc số từ CSV → tự khớp)
python -m tools.build_progress_deck
python -m tools.build_docx
```

**Sau khi chạy:** so nhanh vài số đầu bảng với bản trong sổ tay này — kỳ vọng lệch ≤ vài phần nghìn (ảnh hưởng 0,24% dòng của fix banked); nếu bảng nào lệch mạnh thì dừng lại hỏi nhau trước khi nộp. Rồi cập nhật số vào báo cáo Word/slide (Khoa) và commit trọn gói một lần.

**Tuyệt đối không:** chạy `--rederive` của make_split (đổi 4.574/5.756 id test — mất khả năng so sánh với mọi kết quả cũ); sửa tay `data/splits/test_student_ids.csv`; sửa tay số trong CSV.

---

## 7. Việc còn lại & phân công

| Việc | Ai | Ghi chú |
|---|---|---|
| ~~Streamlit dashboard (Phase 6a)~~ **ĐÃ XONG 2026-07-12**: `dashboard/app.py` — danh sách SV bị cờ theo mốc, lọc "còn đang học tại t", SHAP cục bộ gắn nhãn mốc; chạy `streamlit run dashboard/app.py`, kiểm nhanh `python dashboard/app.py --smoke` | **An** (nghiệm thu + tuỳ biến giao diện) | UI mỏng, toàn bộ logic trong `src/` đúng quy ước với Đức; smoke test khớp `active_n`=5.052 tại t=40 |
| ~~Introduction + Literature Review + References (IEEE)~~ **CÓ BẢN THẢO 2026-07-12**: `reports/final_report/1_Introduction_and_Literature_Review_EN.md` | **Sơn** (rà, chỉnh giọng, bổ sung từ concept matrix nếu muốn) | Mọi trích dẫn bám proposal + Base_Studies_Comparison đã verify; chỗ nào không chắc nguồn đã đánh TODO |
| **Lắp báo cáo Word cuối** theo Project Template + **slide tổng** | **Khoa** | Bản đồ lắp ráp từng mục → nguồn liệu: `reports/final_report/00_ASSEMBLY_MAP_VI.md`. Chỉ lắp số SAU khi chạy checklist mục 6; mọi số lấy từ `reports/tables/*.csv`, không gõ tay từ trí nhớ |
| **Chạy checklist renumber (mục 6)** | **Khoa + Phúc** (Phúc phần data/split, Khoa phần train/tools) | ~1–2h máy chạy; commit trọn gói |
| **KÝ THẬT biên bản Step 0** | **Cả 6 người** | `docs/08_agreements/Step0_Agreement_Nhom1.pdf` hiện **trống ngày + chữ ký** (cả `Leakage_Rules_Signed_Nhom1.pdf` kiểm luôn). In ra, điền ngày, ký, scan đè lại file. Nộp biên bản trống chữ ký là mất điểm miễn phí |
| **Cập nhật file xlsx phân công** (đang ghi 9/40 việc "Hoàn thành" — lỗi thời) | **Khoa** | Đối chiếu trạng thái thật theo bản đồ STT trong `docs/README_EN.md` |
| Đọc sổ tay này + thuộc phần mình ở mục 4 | **Cả 6 người** | Ai lợn cợn chỗ nào hỏi ngay trong group — đừng để tới hôm bảo vệ |

---

*Sổ tay do phiên làm việc 2026-07-12 tổng hợp; nhật ký thô: `_process_log_2026-07-12.md`; mọi số liệu trích từ `reports/tables/*.csv` — chạy lại được.*
