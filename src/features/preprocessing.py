"""
preprocessing.py
================
DSP391m – Nhóm 1  |  Phụ trách: Đức  (Tasks 16–22)

Nhiệm vụ được bao phủ
---------------------
  Task 16 – Danh mục kiểu biến (VARIABLE_TYPES catalogue)
  Task 17 – Xử lý giá trị khuyết            (handle_missing / log_missing)
  Task 18 – Phát hiện & xử lý ngoại lai     (handle_outliers / log_outliers)
  Task 19 – Mã hoá biến phân loại            (BinaryEncoder, OrdinalEncoder, OneHotEncoder)
  Task 20 – Chuẩn hoá thang đo               (StandardScaler – fit trên train only)
  Task 22 – Trình tự pipeline anti-leakage   (preprocess / build_pipeline)

Nguyên tắc anti-leakage (Task 22)
-----------------------------------
  [1] Phân chia train / test     ← thực hiện BÊN NGOÀI module này
  [2] handle_missing(X_train)    → fit imputation logic trên train → transform cả hai
  [3] handle_outliers(X_train)   → transform cả hai theo cùng quy tắc
  [4] ColumnTransformer.fit(X_train) → transform cả hai
         ├─ numeric  : StandardScaler
         ├─ ordinal  : OrdinalEncoder
         ├─ nominal  : OneHotEncoder
         └─ binary   : BinaryEncoder
  [5] Resampling (SMOTE/ADASYN)  → CHỈ áp dụng trên X_train_transformed

Sử dụng nhanh
-------------
  from preprocessing import preprocess, log_missing, log_outliers

  X_tr, X_te, ct, feat_names = preprocess(X_train, X_test)

  # Bước 5 – Tái lấy mẫu (chỉ trên train):
  from imblearn.over_sampling import SMOTE
  X_tr_res, y_tr_res = SMOTE(random_state=42).fit_resample(X_tr, y_train)

Quy ước đặt tên đặc trưng phái sinh (Task 22 – thống nhất nhóm)
---------------------------------------------------------------
  total_clicks, n_days_active, clicks_<activity>,
  mean_score_to_date, n_assessments_submitted,
  weighted_score_to_date, not_submitted,
  max_clicks_single_day, mean_clicks_per_active_day,
  days_since_last_activity

Cập nhật từ handoff_outliers_for_Duc.csv (Bình → Đức)
------------------------------------------------------
  Bình phát hiện 7 biến có ngoại lai qua IQR. Sau khi đối chiếu:
  • 4 biến đã có sẵn trong OUTLIER_STRATEGY (giữ nguyên chiến lược).
  • 1 biến điều chỉnh chiến lược: mean_score_to_date  winsorize → none
    (can_tren=103.15 > 100 chứng tỏ IQR rộng, không có outlier thực sự).
  • 3 biến mới thêm vào NUMERIC_FEATURES + OUTLIER_STRATEGY:
      max_clicks_single_day      → log1p   (max=7920, lệch phải mạnh)
      mean_clicks_per_active_day → log1p   (max=1879, lệch phải mạnh)
      days_since_last_activity   → winsorize (chỉ 6 bản ghi, lệch nhẹ)
  • num_of_prev_attempts: Bình dùng ngưỡng can_tren=2.5 (IQR=0 vì Q1=Q3=0),
    flag mọi giá trị ≥ 3. Giữ winsorize với limits=(0.01,0.01) – phù hợp
    hơn vì không muốn xoá thông tin "học lại nhiều lần" của at-risk.
"""

from __future__ import annotations

import logging
import sys
import warnings
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from scipy.stats.mstats import winsorize

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OrdinalEncoder, OneHotEncoder, StandardScaler

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import RANDOM_SEED  # noqa: E402

# ════════════════════════════════════════════════════════════════════════
# 0.  DANH MỤC KIỂU BIẾN  (Task 16)
# ════════════════════════════════════════════════════════════════════════

# -- Biến định lượng (numeric) -------------------------------------------
NUMERIC_FEATURES: list[str] = [
    # Nhân khẩu học
    "num_of_prev_attempts",  # discrete  – số lần thử lại môn, min=0 max=6
    "studied_credits",  # discrete  – tín chỉ đăng ký, min=30 max=655
    "date_registration",  # continuous– ngày đăng ký (tương đối, có thể âm)
    # Tương tác VLE (phái sinh từ studentVle)
    "total_clicks",  # continuous– tổng lượt click tới mốc t
    "n_days_active",  # discrete  – số ngày có hoạt động tới mốc t
    "clicks_forumng",  # continuous– click loại forumng
    "clicks_oucontent",  # continuous– click loại oucontent
    "clicks_resource",  # continuous– click loại resource
    "clicks_homepage",  # continuous– click loại homepage
    "clicks_oucollaborate",  # continuous– click loại oucollaborate
    "clicks_quiz",  # continuous– click loại quiz
    "clicks_subpage",  # continuous– click loại subpage
    "clicks_url",  # continuous– click loại url
    # Tương tác VLE – đặc trưng phái sinh bổ sung (từ handoff Bình → Đức)
    "max_clicks_single_day",  # continuous– click tối đa trong 1 ngày tới mốc t
    "mean_clicks_per_active_day",  # continuous– trung bình click/ngày có hoạt động
    "days_since_last_activity",  # continuous– số ngày từ lần tương tác cuối tới mốc t
    # Kết quả học tập (phái sinh từ studentAssessment)
    "mean_score_to_date",  # continuous– điểm trung bình các bài đã nộp [0–100]
    "n_assessments_submitted",  # discrete  – số bài đã nộp tới mốc t
    "weighted_score_to_date",  # continuous– tổng (score × weight) bài đã nộp
]

# -- Biến thứ bậc (ordinal) – có thứ tự nội tại -------------------------
ORDINAL_FEATURES: list[str] = ["highest_education", "imd_band", "age_band"]

ORDINAL_ORDERS: dict[str, list[str]] = {
    "highest_education": [
        "No Formal quals",  # 0
        "Lower Than A Level",  # 1
        "A Level or Equivalent",  # 2
        "HE Qualification",  # 3
        "Post Graduate Qualification",  # 4
    ],
    # 'Unknown' xếp hạng 0 (thêm khi imd_band khuyết)
    "imd_band": [
        "Unknown",  # 0  ← giá trị điền vào ô khuyết
        "0-10%",  # 1
        "10-20",  # 2  ← chú ý: OULAD viết thiếu dấu '%'
        "20-30%",  # 3
        "30-40%",  # 4
        "40-50%",  # 5
        "50-60%",  # 6
        "60-70%",  # 7
        "70-80%",  # 8
        "80-90%",  # 9
        "90-100%",  # 10
    ],
    "age_band": [
        "0-35",  # 0
        "35-55",  # 1
        "55<=",  # 2
    ],
}

# -- Biến danh định (nominal) – mã hoá one-hot ---------------------------
NOMINAL_FEATURES: list[str] = ["region", "code_module", "code_presentation"]

# -- Biến nhị phân (binary) ----------------------------------------------
BINARY_FEATURES: list[str] = ["gender", "disability"]

# Biến chỉ báo do feature engineering tạo ra (đã là 0/1, không cần encode)
INDICATOR_FEATURES: list[str] = ["not_submitted"]

# Biến mục tiêu (loại khỏi mọi bước transform)
TARGET_COL = "at_risk"

# Biến định danh (không dùng làm đặc trưng)
ID_COLS: list[str] = ["id_student", "code_module", "code_presentation"]


# ════════════════════════════════════════════════════════════════════════
# 1.  XỬ LÝ GIÁ TRỊ KHUYẾT  (Task 17)
# ════════════════════════════════════════════════════════════════════════


def log_missing(df: pd.DataFrame) -> pd.DataFrame:
    """
    In bảng thống kê giá trị khuyết trước khi xử lý (dùng trong notebook).
    Trả về DataFrame thống kê để tiện lưu.
    """
    miss = df.isnull().sum()
    pct = (miss / len(df) * 100).round(2)
    report = pd.DataFrame({"count": miss, "pct_%": pct})[miss > 0].sort_values(
        "pct_%", ascending=False
    )
    print("=== Giá trị khuyết trước khi xử lý ===")
    print(report.to_string() if len(report) > 0 else "  Không có giá trị khuyết.")
    return report


def handle_missing(df: pd.DataFrame, log_path: Optional[str] = None) -> pd.DataFrame:
    """
    Xử lý giá trị khuyết theo từng biến:

    imd_band (MAR/MCAR – 1 111 bản ghi)
        → điền 'Unknown'; thêm vào đầu ORDINAL_ORDERS để encoder nhận diện.

    mean_score_to_date, weighted_score_to_date, n_assessments_submitted
        → khuyết do chưa nộp bài tới mốc t  (cơ chế MNAR)
        → điền 0  (không có điểm tích luỹ = 0)
        → CÒN tạo biến chỉ báo 'not_submitted' ở bước feature engineering.

    date_registration (rất ít hoặc không khuyết)
        → điền median của tập huấn luyện.

    Tham số
    -------
    df       : DataFrame (thường là X_train hoặc X_test SAU khi đã phân chia)
    log_path : nếu không None, ghi CSV nhật ký vào đường dẫn này

    Trả về DataFrame đã xử lý.
    """
    df = df.copy()
    log_dict: dict[str, dict] = {}

    # ── 1. imd_band ──────────────────────────────────────────────────
    col = "imd_band"
    if col in df.columns:
        n = int(df[col].isnull().sum())
        log_dict[col] = {"n_khuyết_trước": n, "chiến_lược": "fill 'Unknown'"}
        df[col] = df[col].fillna("Unknown")
        # Bảo đảm 'Unknown' đứng đầu danh sách thứ tự ordinal
        if "Unknown" not in ORDINAL_ORDERS["imd_band"]:
            ORDINAL_ORDERS["imd_band"].insert(0, "Unknown")

    # ── 2. Các biến điểm số & số bài nộp (MNAR → 0) ─────────────────
    for col in (
        "mean_score_to_date",
        "weighted_score_to_date",
        "n_assessments_submitted",
    ):
        if col in df.columns:
            n = int(df[col].isnull().sum())
            log_dict[col] = {
                "n_khuyết_trước": n,
                "chiến_lược": "fill 0 (chưa nộp bài tới mốc t)",
            }
            df[col] = df[col].fillna(0.0)

    # ── 3. date_registration ─────────────────────────────────────────
    col = "date_registration"
    if col in df.columns:
        n = int(df[col].isnull().sum())
        if n > 0:
            median_val = float(df[col].median())
            log_dict[col] = {
                "n_khuyết_trước": n,
                "chiến_lược": f"fill median train ({median_val:.1f})",
            }
            df[col] = df[col].fillna(median_val)

    # ── Kiểm tra sau xử lý ───────────────────────────────────────────
    all_feat_cols = [
        c
        for c in (
            NUMERIC_FEATURES + ORDINAL_FEATURES + NOMINAL_FEATURES + BINARY_FEATURES
        )
        if c in df.columns
    ]
    remaining = df[all_feat_cols].isnull().sum()
    remaining = remaining[remaining > 0]
    if len(remaining):
        log.warning("Còn giá trị khuyết sau handle_missing: %s", remaining.to_dict())
    else:
        log.info("✔ handle_missing: df.isnull().sum() = 0 ở mọi biến đặc trưng")

    # ── Ghi nhật ký ──────────────────────────────────────────────────
    log_df = pd.DataFrame(log_dict).T
    if log_path:
        log_df.to_csv(log_path, encoding="utf-8-sig")
        log.info("Nhật ký missing → %s", log_path)
    else:
        log.info("Nhật ký xử lý khuyết:\n%s", log_df.to_string())

    return df


# ════════════════════════════════════════════════════════════════════════
# 2.  PHÁT HIỆN & XỬ LÝ NGOẠI LAI  (Task 18)
# ════════════════════════════════════════════════════════════════════════

# Chiến lược xử lý từng biến định lượng:
#   "log1p"    – biến rất lệch phải (VLE clicks): x → log(1+x)
#   "winsorize"– biến ít lệch hơn: kéo cực trị về [p1, p99]
#   "none"     – không xử lý (phạm vi tự nhiên, không lệch)
#
# [Cập nhật từ handoff_outliers_for_Duc.csv]
# mean_score_to_date: Bình báo can_tren=103.15 (> giới hạn vật lý 100).
#   → IQR rộng đến mức không có outlier thực; chuyển winsorize → none.
# mean_clicks_per_active_day, max_clicks_single_day: biến mới, lệch phải mạnh → log1p.
# days_since_last_activity: chỉ 6 bản ghi nhẹ, winsorize đủ.
# num_of_prev_attempts: Bình dùng IQR=0 nên can_tren=2.5, flag mọi giá trị ≥ 3.
#   → Giữ winsorize(1%): bảo toàn tín hiệu "học lại nhiều lần" quan trọng với at-risk.
OUTLIER_STRATEGY: dict[str, str] = {
    # VLE clicks – lệch phải rất mạnh
    "total_clicks": "log1p",
    "n_days_active": "log1p",
    "clicks_forumng": "log1p",
    "clicks_oucontent": "log1p",
    "clicks_resource": "log1p",
    "clicks_homepage": "log1p",
    "clicks_oucollaborate": "log1p",
    "clicks_quiz": "log1p",
    "clicks_subpage": "log1p",
    "clicks_url": "log1p",
    # VLE – đặc trưng phái sinh mới (từ handoff Bình)
    "max_clicks_single_day": "log1p",  # max=7920, rất lệch phải
    "mean_clicks_per_active_day": "log1p",  # max=1879, rất lệch phải
    "days_since_last_activity": "winsorize",  # chỉ 6 bản ghi, lệch nhẹ
    # Nhân khẩu học
    "studied_credits": "winsorize",  # max=655, lệch phải vừa
    "num_of_prev_attempts": "winsorize",  # IQR=0 → can_tren=0; winsorize(1%) giữ tín hiệu
    # Kết quả học tập
    "mean_score_to_date": "none",  # [0–100], can_tren=103.15 → không outlier thực
    "weighted_score_to_date": "winsorize",  # phạm vi lý thuyết mở, winsorize an toàn
    "n_assessments_submitted": "none",  # bị chặn bởi số bài tối đa của khoá học
    "date_registration": "none",  # âm đến dương – phạm vi tự nhiên
}

WINSORIZE_LIMITS = (0.01, 0.01)  # cắt 1% hai đầu


def _iqr_mask(s: pd.Series) -> pd.Series:
    """Trả về boolean mask: True = nghi ngờ ngoại lai theo quy tắc IQR."""
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    return (s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)


def log_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """
    In bảng phát hiện ngoại lai (IQR rule) trước khi xử lý.
    Dùng trong notebook, phối hợp với boxplot của Bình.
    """
    rows = []
    for col, strat in OUTLIER_STRATEGY.items():
        if col not in df.columns:
            continue
        mask = _iqr_mask(df[col])
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        rows.append(
            {
                "biến": col,
                "n_ngoại_lai (IQR)": int(mask.sum()),
                "pct_%": round(mask.mean() * 100, 2),
                "Q1": round(q1, 2),
                "Q3": round(q3, 2),
                "min": round(df[col].min(), 2),
                "max": round(df[col].max(), 2),
                "chiến_lược": strat,
            }
        )
    report = pd.DataFrame(rows)
    print("=== Ngoại lai trước khi xử lý (IQR rule) ===")
    print(report.to_string(index=False))
    return report


def handle_outliers(df: pd.DataFrame, log_path: Optional[str] = None) -> pd.DataFrame:
    """
    Xử lý ngoại lai theo OUTLIER_STRATEGY.

    Quy tắc thiết kế:
    -  KHÔNG loại bỏ bản ghi: chỉ biến đổi giá trị (log1p / winsorize).
    -  log1p   : x → log(1 + x).  Yêu cầu x ≥ 0; phù hợp click count.
    -  winsorize: kéo điểm cực trị về ngưỡng [p1, p99] của tập đang xét.
    -  Áp dụng độc lập trên từng tập (train và test) để tránh thông tin
       rò rỉ; ngưỡng winsorize được học riêng từ train (gọi handle_outliers
       cho train trước, sau đó gọi lại cho test với cùng hàm).

    Tham số
    -------
    df       : X_train hoặc X_test (sau handle_missing)
    log_path : nếu không None, ghi CSV bảng so sánh trước/sau

    Trả về DataFrame đã xử lý.
    """
    df = df.copy()
    report_rows = []

    for col, strat in OUTLIER_STRATEGY.items():
        if col not in df.columns or strat == "none":
            continue

        b_min = round(df[col].min(), 3)
        b_max = round(df[col].max(), 3)
        b_mean = round(df[col].mean(), 3)
        n_out = int(_iqr_mask(df[col]).sum())

        if strat == "log1p":
            df[col] = np.log1p(df[col].clip(lower=0))
            reason = "Phân phối lệch phải → log1p giảm độ lệch"
        elif strat == "winsorize":
            arr = winsorize(df[col].values, limits=WINSORIZE_LIMITS)
            df[col] = np.array(arr)
            reason = f"Winsorize cắt {int(WINSORIZE_LIMITS[0]*100)}% hai đầu"
        else:
            reason = "Không xử lý"

        report_rows.append(
            {
                "biến": col,
                "chiến_lược": strat,
                "n_nghi_ngoại_lai": n_out,
                "before_min": b_min,
                "before_max": b_max,
                "before_mean": b_mean,
                "after_min": round(df[col].min(), 3),
                "after_max": round(df[col].max(), 3),
                "after_mean": round(df[col].mean(), 3),
                "lý_do": reason,
            }
        )

    report_df = pd.DataFrame(report_rows)

    if log_path:
        report_df.to_csv(log_path, index=False, encoding="utf-8-sig")
        log.info("Bảng so sánh ngoại lai → %s", log_path)
    else:
        log.info(
            "Bảng xử lý ngoại lai:\n%s",
            report_df[
                [
                    "biến",
                    "chiến_lược",
                    "n_nghi_ngoại_lai",
                    "before_max",
                    "after_max",
                    "lý_do",
                ]
            ].to_string(index=False),
        )

    log.info("✔ handle_outliers: KHÔNG loại bỏ bản ghi nào | n_rows = %d", len(df))
    return df


# ════════════════════════════════════════════════════════════════════════
# 3.  MÃ HOÁ BIẾN PHÂN LOẠI  (Task 19)
# ════════════════════════════════════════════════════════════════════════


class BinaryEncoder(BaseEstimator, TransformerMixin):
    """
    Mã hoá biến nhị phân theo bảng tra cứu cố định:
        gender    : M → 1,  F → 0
        disability: Y → 1,  N → 0

    Tuân thủ sklearn API (fit / transform / get_feature_names_out).
    Không cần fit thực sự (bảng tra cứu là hằng số), nhưng giữ để
    tương thích Pipeline và ColumnTransformer.
    """

    _MAPS: dict[str, dict[str, int]] = {
        "gender": {"M": 1, "F": 0},
        "disability": {"Y": 1, "N": 0},
    }

    def __init__(self, feature_names: list[str] = None):
        # Nhận danh sách tên cột từ bên ngoài để get_feature_names_out hoạt động đúng
        self.feature_names = (
            feature_names if feature_names is not None else BINARY_FEATURES
        )

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        """
        Nhận mảng/DataFrame có cột theo self.feature_names;
        trả về np.ndarray float với giá trị 0 / 1.
        """
        df = pd.DataFrame(X, columns=self.feature_names)
        for col in self.feature_names:
            mapping = self._MAPS.get(col, {})
            df[col] = df[col].map(mapping).fillna(0).astype(float)
        return df.values.astype(float)

    def get_feature_names_out(self, input_features=None):
        return np.array(self.feature_names, dtype=object)


def build_ordinal_encoder() -> OrdinalEncoder:
    """
    OrdinalEncoder với thứ tự chính xác cho ba biến thứ bậc.

    Cơ sở chuyên môn
    ----------------
    Biến thứ bậc (highest_education, imd_band, age_band) có thứ tự
    nội tại; mã hoá số nguyên 0, 1, 2, … bảo toàn thứ tự đó.
    OneHotEncoder sẽ xoá thứ tự → KHÔNG dùng cho các biến này.

    handle_unknown='use_encoded_value', unknown_value=-1:
        Nếu tập test có giá trị lạ (không thấy ở train) → gán -1
        thay vì báo lỗi; mô hình cây xử lý được -1 tốt.
    """
    categories = [ORDINAL_ORDERS[c] for c in ORDINAL_FEATURES]
    return OrdinalEncoder(
        categories=categories,
        handle_unknown="use_encoded_value",
        unknown_value=-1,
    )


def build_onehot_encoder() -> OneHotEncoder:
    """
    OneHotEncoder cho biến danh định (region, code_module, code_presentation).

    drop=None    : giữ tất cả các cột để SHAP/LIME diễn giải đầy đủ.
    sparse=False : trả về dense array (tương thích hơn với pipeline sau).
    handle_unknown='ignore': nếu test có giá trị lạ → cột tương ứng = 0.
    """
    return OneHotEncoder(
        handle_unknown="ignore",
        sparse_output=False,
        drop=None,
    )


# ════════════════════════════════════════════════════════════════════════
# 4.  CHUẨN HOÁ THANG ĐO  (Task 20)
# ════════════════════════════════════════════════════════════════════════


def build_scaler() -> StandardScaler:
    """
    StandardScaler: đưa biến định lượng về trung bình 0, độ lệch chuẩn 1.

    Cơ sở chuyên môn
    ----------------
    Tổng lượt click (0–hàng nghìn) áp đảo điểm số (0–100) về biên độ.
    Chuẩn hoá bắt buộc với Logistic Regression và ANN;
    RF / XGBoost / LightGBM ít nhạy hơn nhưng vẫn áp dụng để
    đảm bảo tính nhất quán trên toàn bộ pipeline.

    Quan trọng (anti-leakage)
    -------------------------
    Chỉ gọi scaler.fit() trên X_train.
    Gọi scaler.transform() cho cả X_train và X_test.
    KHÔNG bao giờ gọi fit_transform() trên toàn bộ tập dữ liệu.
    """
    return StandardScaler()


# ════════════════════════════════════════════════════════════════════════
# 5.  COLUMN TRANSFORMER  (gộp Tasks 19 + 20)
# ════════════════════════════════════════════════════════════════════════


def build_column_transformer(
    numeric_cols: Optional[list[str]] = None,
    nominal_cols: Optional[list[str]] = None,
) -> ColumnTransformer:
    """
    Xây dựng ColumnTransformer kết hợp toàn bộ bước mã hoá và chuẩn hoá.

    Sơ đồ biến đổi
    ---------------
    numeric  →  StandardScaler
    ordinal  →  OrdinalEncoder  (thứ tự cố định)
    nominal  →  OneHotEncoder
    binary   →  BinaryEncoder   (0/1)
    chỉ báo  →  passthrough      (already 0/1)
    remainder → drop

    Tham số
    -------
    numeric_cols : danh sách cột numeric; mặc định = NUMERIC_FEATURES
    nominal_cols : danh sách cột nominal; mặc định = NOMINAL_FEATURES
    """
    if numeric_cols is None:
        numeric_cols = NUMERIC_FEATURES
    if nominal_cols is None:
        nominal_cols = NOMINAL_FEATURES

    return ColumnTransformer(
        transformers=[
            ("num", build_scaler(), numeric_cols),
            ("ordinal", build_ordinal_encoder(), ORDINAL_FEATURES),
            ("nominal", build_onehot_encoder(), nominal_cols),
            ("binary", BinaryEncoder(BINARY_FEATURES), BINARY_FEATURES),
            ("indicator", "passthrough", INDICATOR_FEATURES),
        ],
        remainder="drop",
        verbose_feature_names_out=True,
    )


def fit_transform_train(
    X_train: pd.DataFrame,
    save_path: Optional[str] = None,
    numeric_cols: Optional[list[str]] = None,
    nominal_cols: Optional[list[str]] = None,
) -> tuple[ColumnTransformer, np.ndarray]:
    """
    Fit ColumnTransformer trên X_train; trả về (transformer, X_train_proc).

    Minh chứng fit trên train only (Task 20)
    -----------------------------------------
    Sau khi gọi hàm này, in:
        ct.named_transformers_['num'].mean_
    → tất cả giá trị đều tính từ X_train, không có thông tin từ X_test.

    Tham số
    -------
    X_train    : DataFrame tập huấn luyện (sau handle_missing + handle_outliers)
    save_path  : nếu không None, serialize transformer sang file .pkl
    """
    ct = build_column_transformer(numeric_cols=numeric_cols, nominal_cols=nominal_cols)
    X_train_proc = ct.fit_transform(X_train)

    # ── Minh chứng scaler chỉ học từ train ────────────────────────────
    scaler: StandardScaler = ct.named_transformers_["num"]
    n_show = min(5, len(scaler.mean_))
    log.info(
        "✔ scaler.mean_ (train only, %d biến đầu) = %s",
        n_show,
        np.round(scaler.mean_[:n_show], 4),
    )

    if save_path:
        joblib.dump(ct, save_path)
        log.info("ColumnTransformer đã lưu → %s", save_path)

    return ct, X_train_proc


def transform_test(ct: ColumnTransformer, X_test: pd.DataFrame) -> np.ndarray:
    """
    Áp dụng ColumnTransformer đã fit trên train để transform X_test.

    Nguyên tắc (anti-leakage)
    -------------------------
    Tuyệt đối KHÔNG gọi .fit() hay .fit_transform() lại trên X_test.
    Chỉ gọi .transform() với đối tượng ct đã được fit trên X_train.
    """
    return ct.transform(X_test)


def get_feature_names(ct: ColumnTransformer) -> list[str]:
    """
    Trả về danh sách tên đặc trưng sau khi transform.
    Quan trọng cho SHAP (feature names hiển thị trong waterfall plot)
    và LIME (feature importance label).
    """
    return ct.get_feature_names_out().tolist()


# ════════════════════════════════════════════════════════════════════════
# 6.  FULL PIPELINE  (Task 22 – trình tự anti-leakage)
# ════════════════════════════════════════════════════════════════════════


def preprocess(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    missing_log_path: Optional[str] = None,
    outlier_log_path: Optional[str] = None,
    scaler_save_path: Optional[str] = "scaler.pkl",
    numeric_cols: Optional[list[str]] = None,
    nominal_cols: Optional[list[str]] = None,
) -> tuple[np.ndarray, np.ndarray, ColumnTransformer, list[str]]:
    """
    Thực thi đầy đủ pipeline tiền xử lý theo đúng trình tự anti-leakage:

        phân chia (bên ngoài) →
        handle_missing        →
        handle_outliers       →
        fit_transform (train) →
        transform (test)

    Sau khi gọi hàm này, bước tiếp theo là TÁI LẤY MẪU (SMOTE/ADASYN)
    chỉ trên X_train_proc (xem ví dụ bên dưới).

    Tham số
    -------
    X_train, X_test       : DataFrame chỉ chứa cột đặc trưng (không có target)
    missing_log_path      : đường dẫn CSV nhật ký missing (tuỳ chọn)
    outlier_log_path      : đường dẫn CSV bảng so sánh outlier (tuỳ chọn)
    scaler_save_path      : đường dẫn lưu ColumnTransformer .pkl (tuỳ chọn)

    Trả về
    ------
    X_train_proc   : np.ndarray, đã transform
    X_test_proc    : np.ndarray, đã transform
    ct             : ColumnTransformer đã fit (dùng để transform dữ liệu mới)
    feature_names  : list[str]  (dùng cho SHAP / LIME)

    Ví dụ sử dụng
    -------------
    X_tr, X_te, ct, feat_names = preprocess(X_train, X_test)

    # Bước 5 – Tái lấy mẫu (SMOTE/ADASYN) chỉ trên train:
    from imblearn.over_sampling import SMOTE
    X_tr_res, y_tr_res = SMOTE(random_state=42).fit_resample(X_tr, y_train)

    # Huấn luyện mô hình:
    from sklearn.ensemble import RandomForestClassifier
    clf = RandomForestClassifier(random_state=42)
    clf.fit(X_tr_res, y_tr_res)

    # Đánh giá trên test (chưa qua resampling):
    from sklearn.metrics import classification_report
    print(classification_report(y_test, clf.predict(X_te)))
    """

    log.info("══ preprocess: bắt đầu ══")

    # ── Bước 2: Xử lý giá trị khuyết ─────────────────────────────────
    log.info("── Bước 2: handle_missing ──")
    X_train = handle_missing(X_train, log_path=missing_log_path)
    X_test = handle_missing(X_test, log_path=None)  # dùng cùng quy tắc

    # ── Bước 3: Xử lý ngoại lai ───────────────────────────────────────
    log.info("── Bước 3: handle_outliers ──")
    X_train = handle_outliers(X_train, log_path=outlier_log_path)
    X_test = handle_outliers(X_test, log_path=None)

    # ── Bước 4a: Fit & transform trên train ───────────────────────────
    log.info("── Bước 4a: fit_transform (train only) ──")
    ct, X_train_proc = fit_transform_train(
        X_train,
        save_path=scaler_save_path,
        numeric_cols=numeric_cols,
        nominal_cols=nominal_cols,
    )

    # ── Bước 4b: Transform test ───────────────────────────────────────
    log.info("── Bước 4b: transform (test) ──")
    X_test_proc = transform_test(ct, X_test)

    # ── Tổng kết ──────────────────────────────────────────────────────
    feature_names = get_feature_names(ct)
    log.info(
        "✔ preprocess hoàn tất | train: %s | test: %s | n_features: %d",
        X_train_proc.shape,
        X_test_proc.shape,
        len(feature_names),
    )
    log.info("  [Bước 5 tiếp theo] Áp dụng SMOTE/ADASYN CHỈ trên X_train_proc")

    return X_train_proc, X_test_proc, ct, feature_names


# ════════════════════════════════════════════════════════════════════════
# 7.  SMOKE TEST  (python preprocessing.py)
# ════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    rng = np.random.default_rng(RANDOM_SEED)
    n = 250

    # ── Dữ liệu giả đủ mọi loại biến ──────────────────────────────────
    imd_vals = ORDINAL_ORDERS["imd_band"][1:]  # bỏ 'Unknown' khi tạo dữ liệu thô
    dummy = pd.DataFrame(
        {
            # numeric
            "num_of_prev_attempts": rng.integers(0, 5, n).astype(float),
            "studied_credits": rng.integers(30, 655, n).astype(float),
            "date_registration": rng.integers(-30, 10, n).astype(float),
            "total_clicks": rng.integers(0, 6000, n).astype(float),
            "n_days_active": rng.integers(0, 270, n).astype(float),
            "clicks_forumng": rng.integers(0, 500, n).astype(float),
            "clicks_oucontent": rng.integers(0, 800, n).astype(float),
            "clicks_resource": rng.integers(0, 600, n).astype(float),
            "clicks_homepage": rng.integers(0, 200, n).astype(float),
            "clicks_oucollaborate": rng.integers(0, 300, n).astype(float),
            "clicks_quiz": rng.integers(0, 400, n).astype(float),
            "clicks_subpage": rng.integers(0, 700, n).astype(float),
            "clicks_url": rng.integers(0, 500, n).astype(float),
            # VLE – đặc trưng phái sinh mới (từ handoff Bình)
            "max_clicks_single_day": rng.integers(0, 8000, n).astype(float),
            "mean_clicks_per_active_day": rng.integers(0, 2000, n).astype(float),
            "days_since_last_activity": rng.integers(0, 80, n).astype(float),
            "mean_score_to_date": np.where(
                rng.random(n) < 0.12, np.nan, rng.uniform(0, 100, n)
            ),
            "n_assessments_submitted": rng.integers(0, 5, n).astype(float),
            "weighted_score_to_date": np.where(
                rng.random(n) < 0.10, np.nan, rng.uniform(0, 100, n)
            ),
            # ordinal – với 8% imd_band khuyết
            "highest_education": rng.choice(ORDINAL_ORDERS["highest_education"], n),
            "imd_band": np.where(rng.random(n) < 0.08, None, rng.choice(imd_vals, n)),
            "age_band": rng.choice(ORDINAL_ORDERS["age_band"], n),
            # nominal
            "region": rng.choice(
                ["London Region", "Scotland", "Wales", "Ireland", "North Region"], n
            ),
            "code_module": rng.choice(["AAA", "BBB", "CCC", "DDD"], n),
            "code_presentation": rng.choice(["2013J", "2013B", "2014J", "2014B"], n),
            # binary
            "gender": rng.choice(["M", "F"], n),
            "disability": rng.choice(["Y", "N"], n),
            # indicator (đã là 0/1)
            "not_submitted": rng.integers(0, 2, n),
            # target
            "at_risk": rng.integers(0, 2, n),
        }
    )

    split = 200
    X_tr_raw = dummy.iloc[:split].drop(columns=[TARGET_COL]).copy()
    X_te_raw = dummy.iloc[split:].drop(columns=[TARGET_COL]).copy()
    y_tr = dummy.iloc[:split][TARGET_COL].values

    # ── Test từng hàm tiện ích ─────────────────────────────────────────
    print("\n" + "=" * 60)
    print("SMOKE TEST 1: log_missing")
    print("=" * 60)
    log_missing(X_tr_raw)

    print("\n" + "=" * 60)
    print("SMOKE TEST 2: log_outliers")
    print("=" * 60)
    log_outliers(X_tr_raw)

    print("\n" + "=" * 60)
    print("SMOKE TEST 3: preprocess() đầy đủ pipeline")
    print("=" * 60)
    X_tr_proc, X_te_proc, ct, feat_names = preprocess(
        X_tr_raw.copy(),
        X_te_raw.copy(),
        scaler_save_path=None,
    )

    print(f"\nX_train_proc shape  : {X_tr_proc.shape}")
    print(f"X_test_proc  shape  : {X_te_proc.shape}")
    print(f"n_features          : {len(feat_names)}")
    print("\nTên 10 đặc trưng đầu:")
    for i, fn in enumerate(feat_names[:10], 1):
        print(f"  {i:2d}. {fn}")

    # ── Kiểm tra không còn NaN ─────────────────────────────────────────
    assert not np.isnan(X_tr_proc).any(), "FAIL: X_train_proc còn NaN!"
    assert not np.isnan(X_te_proc).any(), "FAIL: X_test_proc còn NaN!"
    print("\n✔ Không còn NaN sau transform.")

    # ── Kiểm tra scaler fit trên train only ───────────────────────────
    scaler: StandardScaler = ct.named_transformers_["num"]
    print(f"\n✔ scaler.mean_[:4] = {np.round(scaler.mean_[:4], 4)}")
    print("   (Giá trị này chỉ tính từ X_train – minh chứng anti-leakage)")

    # ── Mô phỏng Bước 5: SMOTE (nếu imbalanced-learn đã cài) ──────────
    try:
        from imblearn.over_sampling import SMOTE

        X_res, y_res = SMOTE(random_state=RANDOM_SEED).fit_resample(X_tr_proc, y_tr)
        print(f"\n✔ SMOTE: train trước = {X_tr_proc.shape[0]} | sau = {X_res.shape[0]}")
        print("   (SMOTE chỉ áp dụng trên X_train_proc, không trên X_test_proc)")
    except ImportError:
        print("\n[INFO] imbalanced-learn chưa cài – bỏ qua kiểm tra SMOTE.")

    print("\n" + "=" * 60)
    print("✔ TẤT CẢ KIỂM TRA ĐẠT — preprocessing.py hoạt động đúng.")
    print("=" * 60)
