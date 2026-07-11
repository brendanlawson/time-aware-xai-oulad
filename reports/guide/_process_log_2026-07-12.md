# Nhật ký khắc phục sau audit — 2026-07-12

Nguồn: hai bản audit độc lập (Claude + bản đối chiếu), mọi phát hiện đã được
tái lập bằng code trên dữ liệu thật trước khi sửa. File này là nhật ký thô;
bản chính thức cho thành viên là `SO_TAY_BAO_VE_VI.md` (do "thư ký" tổng hợp).

## Phát hiện đã xác minh (số liệu tái lập 100%)

| # | Phát hiện | Bằng chứng |
|---|---|---|
| 1 | Cohort chứa SV đã rút môn thổi phồng kết quả: t=10 có 4.833/32.593 lượt ghi danh đã rút trước cutoff (923 thuộc test); recall active-only: t40 0.678, t80 0.783, t100 0.853 → theo tiêu chí recall≥0.80, nhóm active chỉ đạt ở t=100 | `sensitivity_active_xgb.csv` + script tái lập |
| 2 | at_risk = 52.8% là lớp ĐA SỐ nhẹ → SMOTE mặc định tăng mẫu lớp not-at-risk, ngược tiền đề README; may là 4 chiến lược chênh ≤0.005 nên kết luận không đổi | `split_report.csv`, `imbalance_comparison.csv` |
| 3 | Threshold tune trực tiếp trên y_true của test (`threshold.py`); best-per-checkpoint chọn trên test | code đọc trực tiếp |
| 4 | Bug `is_banked`: bài được bank không được tính là "đã nộp bài đến hạn" → 78/32.593 dòng (0.24%) bị gắn not_submitted=1 sai ở t=100 | script tái lập đúng 78 |
| 5 | `make_split.main()` ghi đè `test_student_ids.csv`; sklearn 1.8 đổi 4.574/5.756 id; SETUP_VI + docs README đang hướng dẫn chạy đúng lệnh đó | kiểm chứng 2026-06 |
| 6 | studentVle có 787.170 dòng trùng hoàn toàn (7.4%) — quirk của OULAD gốc, pipeline đang cộng dồn, chưa văn bản hoá quyết định | script tái lập |
| 7 | Env: mọi artifact build bằng base (py3.13, sklearn 1.8, numpy 2.3.5); env `dsp` (yml, sklearn 1.5) crash savefig/fit, ANN bundle KHÔNG load được (MT19937), xgb/logreg load kèm warning | test load trực tiếp |
| 8 | Thiếu LICENSE dù README tuyên bố MIT; pyproject đòi Python ~=3.14 làm `pip install -e .` fail trên env 3.11; Makefile trỏ src/dataset.py không tồn tại | ls/pip |
| 9 | Ethics doc hứa subgroup metrics (fairness) nhưng chưa có bảng nào | grep + ls tables |
| 10 | RQ3 mới có nửa accuracy; chưa đo tác động chiến lược cân bằng lên GIẢI THÍCH | ls tables |
| 11 | 32.593 là lượt ghi danh (28.785 SV duy nhất) nhưng README ghi "Students: 32,593"; Step0 PDF trống ngày+chữ ký; xlsx phân công 9/40 việc "Hoàn thành" (lỗi thời) | pypdf/pandas |
| 12 | LIME agreement (Jaccard 0.25) tính trên n=30 dòng — cỡ mẫu mỏng; LIME perturb one-hot như biến liên tục | code + CSV |

## Kế hoạch thực thi (phiên này)

- **Code (Claude tự làm):** guard `make_split` (+`--rederive`), fix banked→not_submitted,
  2 test mới, `tools/make_fairness_report.py`, `tools/make_threshold_validation.py`
  (chọn ngưỡng trên OOF validation, test chỉ chấm 1 lần), `tools/make_xai_by_strategy.py`
  (đóng nốt RQ3-giải-thích), `sensitivity_active.py --plot`, sửa vai trò trong deck builder.
- **4 agent song song (file không giao nhau):** ①README/LICENSE/pyproject/Makefile,
  ②SETUP_VI/environment.yml/docs README/Reproducibility, ③Cleaning/Target/Leakage docs
  (duplicates + estimand kép + errata banked), ④HIEU_PHAN guide + kịch bản slide (vai trò An/Sơn).
- **Compute nền (env base):** fairness → threshold-validation → XAI-by-strategy →
  sensitivity lgbm + hình → rebuild deck + docx → pytest toàn bộ.
- **Thư ký (agent cuối):** viết `reports/guide/SO_TAY_BAO_VE_VI.md` cho 6 thành viên.
- **Không đụng:** `data/splits/test_student_ids.csv` (bất khả xâm phạm), các bảng kết quả
  đã commit (giữ nguyên — renumber toàn bộ để checklist chạy 1 lệnh trước báo cáo cuối).

## Diễn biến

- 00:05 Xác minh chéo bản audit thứ hai: 923/4.833/78/787.170 đều tái lập chính xác.
- 00:20 Thu thập version env base + pandoc 3.8 OK. Tạo nhật ký này.
- 00:21 Phóng 4 agent docs song song. Bắt đầu sửa code.
- 00:30 **Code fix 1 — split guard:** `make_split.py` thêm `resolve_test_ids()` + cờ
  `--rederive`; chạy lại mặc định chỉ LOAD `test_student_ids.csv` đã commit, không bao
  giờ tự tính lại. Test mới `test_make_split_reuses_committed_ids` PASS.
- 00:32 **Code fix 2 — banked bug:** `build_performance_features.py` — bài `is_banked=1`
  giờ được tính là "đã bao phủ deadline" (trước đó 78/32.593 dòng bị gắn not_submitted=1
  sai ở t=100). Banked vẫn KHÔNG tính vào n_assessments_submitted/điểm (quyết định giữ).
  Test mới `test_banked_assessment_covers_its_deadline` PASS. Suite: 19 → 21 test.
- 00:40 **3 tool mới:** `tools/make_fairness_report.py` (subgroup metrics — trả nợ lời hứa
  trong ethics doc), `tools/make_threshold_validation.py` (chọn ngưỡng trên OOF validation
  5-fold, test chỉ chấm 1 lần — sửa lỗi giao thức tune-trên-test),
  `tools/make_xai_by_strategy.py` (SHAP importance per chiến lược cân bằng — đóng nốt nửa
  "giải thích" của RQ3). `sensitivity_active.py` thêm `--plot` (hình dual-cohort recall).
- 00:45 **Provenance:** commit `data/oulad_md5_reference.txt` (7 MD5 chuẩn, format
  `md5sum -c`); `setup_raw_data.py` giờ ĐỐI CHIẾU download với reference thay vì chỉ
  tự ghi manifest. README trỏ về reference committed.
- 00:50 4 agent docs hoàn tất (báo cáo chi tiết trong phần "Kết quả agent" dưới).
  Vá nốt các điểm agent bàn giao: requirements.txt sync với env đã kiểm chứng (bỏ
  tensorflow/optuna — không được import ở đâu), "(19 tests)" hardcode → viết không gắn
  số đếm (README.md, docs/README_EN+VI), guide dòng 22 "32.593 sinh viên" → "lượt ghi
  danh (28.785 SV)", roles trong deck builder (An=dashboard, Sơn=lit review).
- 00:55 Phóng chuỗi compute nền: setup_raw_data (verify) → fairness → threshold-OOF →
  XAI-by-strategy → sensitivity lgbm/xgb + hình → rebuild deck reveal.js.

## Kết quả compute mới (2026-07-12, env base, mọi bảng ghi atomic)

- **threshold_validation.csv** (xgb@t100, ngưỡng chọn trên OOF 5-fold của TRAIN, test chấm
  đúng 1 lần): default 0.5 → test R/P/F1 = 0.9348/0.9735/0.9538; policy f1 chọn 0.49 (gần
  như trùng default); policy recall≥0.9 chọn ngưỡng 0.86 trên validation → test recall
  0.9008 / precision 0.9941. Ý nghĩa bảo vệ: ngưỡng chọn không-đụng-test chuyển sang test
  hầu như không lệch → số cũ không phải lạc quan hoá, và giao thức giờ đã sạch.
- **xai_stability_strategies.csv** (SHAP top-10, xgb@t100, cùng mẫu 1.500 dòng test):
  none↔class_weight Jaccard=1.00; none↔ADASYN 0.82; none↔SMOTE 0.67; SMOTE↔ADASYN 0.54;
  Spearman toàn cục 0.969–0.978 ở MỌI cặp. → Trả lời nốt RQ3-giải-thích: chiến lược cân
  bằng ảnh hưởng không đáng kể tới accuracy (≤0.005) và tới câu chuyện giải thích toàn
  cục (rank correlation ~0.97), chỉ xáo trộn nhẹ thành phần top-10 khi dùng resampling
  tổng hợp (SMOTE/ADASYN).
- **fairness_subgroups.csv + fairness_gaps.csv** (xgb@t100, test, ngưỡng 0.5, chỉ tính
  level n≥50): recall gap lớn nhất theo thuộc tính = imd_band 6,2 điểm (0.900–0.962);
  highest_education 4,6; region 4,5; gender 2,3 (F 0.922 / M 0.945); disability 1,4
  (Y 0.947 cao hơn N 0.933); age_band 0,9. FPR gap ≤5,3 điểm. → Trả xong lời hứa
  "disaggregated metrics" trong ethics doc; không thấy chênh lệch nghiêm trọng.
- **sensitivity_active_lgbm.csv**: khớp mô hình xgb (active recall t100 = 0.836 vs xgb
  0.853) → kết luận dual-cohort không phụ thuộc một model.
- **Hình mới:** `sensitivity_active_recall_xgb.png`, `sensitivity_active_recall_lgbm.png`
  (đường full vs still-enrolled + vạch 0.80).
- **Deck reveal.js** rebuild với vai trò đúng (An dashboard / Sơn lit review).
- **setup_raw_data.py** chạy lại: 7/7 file khớp checksum chuẩn committed
  (`data/oulad_md5_reference.txt`).

## Kiểm định cuối phiên

- **pytest tests/ → 21/21 PASS** (2:14, env base) — 19 test cũ + 2 test mới
  (banked-covers-deadline, split-guard).
- **Chứng minh guard bằng chạy thật:** `python -m src.evaluation.make_split` (không cờ)
  in "Reusing committed test ids (frozen split)"; MD5 của `test_student_ids.csv` và
  `split_report.csv` **y hệt trước/sau** (fab86596… / 8dd20e26…); bảng report in ra khớp
  đúng số đã công bố (26.104/6.489/5.756 · 0.5299/0.5203 · gap 0.0096 · overlap 0).
- **build_docx.py → 32/32 docx** tái sinh từ markdown mới (hết docx-drift).
- **setup_raw_data.py → 7/7 file khớp** `data/oulad_md5_reference.txt`.

## Kết quả agent (tóm tắt bàn giao)

- **Agent Docs-Root:** LICENSE (MIT, mới) · README.md (minority→majority 52,8%; bảng
  Dataset "Enrolments 32,593 (28,785 students)"; cây repo viết lại đúng thực tế; team
  table An/Sơn đúng vai; Project Status thêm đoạn dual-cohort RQ1 + đoạn Phase 4–5
  artifacts) · pyproject requires-python ">=3.10" · Makefile: target `data` trỏ pipeline
  thật, PYTHON_VERSION 3.13.
- **Agent Docs-Env:** environment.yml viết lại theo bộ version đã kiểm chứng 2026-07-12
  (py3.13, sklearn PIN 1.8.0, bỏ tensorflow/optuna) · SETUP_VI: py3.13 + mục "tương thích
  bundle" (ANN/MT19937) + blockquote guard split · docs/README_EN+VI: bỏ tham chiếu
  Report2 đã xoá, thêm câu guard · Reproducibility_EN+VI: mục 4.1 "Verified Environment"
  + sửa luôn lỗi có sẵn `conda activate dsp391m`→`dsp`.
- **Agent Docs-Method:** Cleaning_Methods_EN+VI: §2.1 quyết định duplicates (787.170 dòng,
  giữ + cộng dồn, giới hạn ghi rõ) + Errata banked (78 dòng, 0,24%) · Target_Variable_
  Definition_EN+VI: §5 "Hai khung đọc estimand" (benchmark toàn bộ ghi danh vs can-thiệp
  còn-đang-học; quy tắc báo cáo kép) · Leakage_Rules_EN+VI: Rule 3 nêu hệ quả population
  choice + bỏ "19/19" hardcode.
- **Agent Guide:** HIEU_PHAN mục 8 (câu RQ1 kép), mục 9 (bảng 4 mốc 0.68/0.75/0.78/0.85),
  mục 10 thêm Q&A #7 SMOTE-đảo-chiều, #8 threshold-trên-validation, #9 enrolments-vs-
  students · Progress_Report_Script_VI slide 11 đổi vai An/Sơn.
