"""Anti-leakage preprocessing pipeline.

Covers:
  - Variable-type catalogue (numeric / ordinal / nominal / binary)
  - Missing-value handling   (learn medians on TRAIN, apply to test)
  - Outlier handling          (learn winsorize thresholds on TRAIN, apply to test)
  - Categorical encoding      (Binary / Ordinal / OneHot)
  - Scaling                   (StandardScaler, fit on TRAIN only)
  - Anti-leakage orchestration

THE GOLDEN RULE (anti-leakage)
------------------------------
  [1] train/test split happens OUTSIDE this module.
  [2] handle_missing : learn medians on TRAIN (store in stats) -> apply to test.
  [3] handle_outliers: learn [p1,p99] on TRAIN (store in stats) -> apply to test.
  [4] ColumnTransformer.fit(X_train) -> transform BOTH.
  [5] Resampling (SMOTE/ADASYN) -> ONLY on transformed X_train.

Every "learn" step must take a mutable ``stats`` dict: empty => fit (train),
populated => apply (test). That single pattern is what prevents test statistics
from leaking into training.

See guide section "features/preprocessing.py" — implement in the numbered order.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

from src.config import RANDOM_SEED  # noqa: F401  (used when you wire resampling)

# === Task 16: variable-type catalogue =========================================
# TODO: fill these from the data dictionary. Keep them as the single source of
# truth for which transformer each column goes through.
TARGET = "at_risk"
ID_COLS: list[str] = []  # GROUP_COLS etc. — dropped from X
NUMERIC_COLS: list[str] = []  # scaled
ORDINAL_COLS: list[str] = []  # e.g. highest_education, imd_band, age_band (with order)
NOMINAL_COLS: list[str] = []  # e.g. region -> one-hot
BINARY_COLS: list[str] = []  # e.g. gender, disability -> 0/1

# Columns that must NEVER reach X (the label, its raw source, the withdrawal date).
# make_X_y drops these. test_feature_frame_excludes_leaky_columns guards it.
LEAKY_COLUMNS: set[str] = {"at_risk", "final_result", "date_unregistration"}

# Per-column strategies (Task 17/18). TODO: fill from your EDA + handoff notes.
MISSING_STRATEGY: dict[str, str] = {}  # col -> {"median","zero","flag",...}
OUTLIER_STRATEGY: dict[str, str] = {}  # col -> {"winsorize","none"}


def make_X_y(df: pd.DataFrame) -> tuple[pd.DataFrame, "pd.Series | None"]:
    """Split a dataset frame into X (drop ID_COLS + TARGET) and y (TARGET or None).

    TODO: return X without ID/target columns; y = df[TARGET] if present else None.
    """
    raise NotImplementedError


# === Task 17: missing values ==================================================
def log_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Return a per-column missing-count/percentage report (for the notebook)."""
    raise NotImplementedError


def handle_missing(df: pd.DataFrame, stats: dict | None = None) -> tuple[pd.DataFrame, dict]:
    """Fill missing values; learn fill values on TRAIN, reuse on TEST.

    TODO:
      - stats is None/empty  => FIT: compute the fill (e.g. train median) per col
        per MISSING_STRATEGY, store into stats under key f"{col}_median".
      - stats populated      => APPLY: use the stored values.
      - Return (filled_df, stats). NEVER recompute medians on the test frame.
    Key convention (asserted by the test): stats["date_registration_median"] etc.
    """
    raise NotImplementedError


# === Task 18: outliers ========================================================
def _iqr_mask(s: pd.Series) -> pd.Series:
    """Boolean mask of IQR outliers (for log_outliers). TODO: Q1/Q3 +/- 1.5*IQR."""
    raise NotImplementedError


def log_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Per-column outlier-count report using _iqr_mask (for the notebook)."""
    raise NotImplementedError


def handle_outliers(df: pd.DataFrame, stats: dict | None = None) -> tuple[pd.DataFrame, dict]:
    """Winsorize per OUTLIER_STRATEGY; learn [p1,p99] on TRAIN, reuse on TEST.

    TODO: same fit/apply-via-stats pattern as handle_missing. Columns with
    strategy "none" pass through untouched.
    Key convention (asserted by the test): stats[f"winsor_{col}"] = (low, high),
    learned as the TRAIN [p1, p99]; clip both train and test to that range.
    """
    raise NotImplementedError


# === Task 19: encoders ========================================================
class BinaryEncoder(BaseEstimator, TransformerMixin):
    """Map two-value categoricals to 0/1 (sklearn-compatible transformer)."""

    def __init__(self, feature_names: list[str] | None = None):
        self.feature_names = feature_names  # TODO: store

    def fit(self, X, y=None):
        """TODO: learn the mapping (e.g. sorted categories -> 0/1) per column."""
        raise NotImplementedError

    def transform(self, X):
        """TODO: apply the learned 0/1 mapping; return a numeric array."""
        raise NotImplementedError

    def get_feature_names_out(self, input_features=None):
        """TODO: return the output column names (for get_feature_names)."""
        raise NotImplementedError


def build_ordinal_encoder() -> OrdinalEncoder:
    """TODO: OrdinalEncoder with explicit category order for ORDINAL_COLS
    (handle_unknown='use_encoded_value', unknown_value=-1)."""
    raise NotImplementedError


def build_onehot_encoder() -> OneHotEncoder:
    """TODO: OneHotEncoder(handle_unknown='ignore', sparse_output=False)."""
    raise NotImplementedError


def build_scaler() -> StandardScaler:
    """TODO: StandardScaler() for NUMERIC_COLS."""
    raise NotImplementedError


# === Task 22: assemble the ColumnTransformer ==================================
def build_column_transformer(
    numeric=None, ordinal=None, nominal=None, binary=None
) -> ColumnTransformer:
    """Wire scaler/ordinal/onehot/binary onto their column groups.

    TODO: ColumnTransformer([... ('num', scaler, NUMERIC_COLS), ...],
    remainder='drop'). Default the column groups to the module constants.
    """
    raise NotImplementedError


def fit_transform_train(X_train: pd.DataFrame) -> tuple[np.ndarray, ColumnTransformer]:
    """Fit the ColumnTransformer on TRAIN and transform it. TODO: return (Xt, ct)."""
    raise NotImplementedError


def transform_test(ct: ColumnTransformer, X_test: pd.DataFrame) -> np.ndarray:
    """Transform TEST with the already-fitted ct. TODO: ct.transform(X_test)."""
    raise NotImplementedError


def get_feature_names(ct: ColumnTransformer) -> list[str]:
    """Recover output feature names from a fitted ct (needed for SHAP/LIME).

    TODO: ct.get_feature_names_out().tolist() (strip transformer prefixes if you
    want clean names for plots).
    """
    raise NotImplementedError


def preprocess(
    X_train: pd.DataFrame, X_test: pd.DataFrame
) -> tuple[np.ndarray, np.ndarray, ColumnTransformer, list[str]]:
    """Full anti-leakage sequence in one call.

    TODO (ORDER MATTERS):
      1. m_stats = {}; X_train, m_stats = handle_missing(X_train, m_stats)
                       X_test,  _       = handle_missing(X_test,  m_stats)
      2. o_stats = {}; same fit-on-train / apply-on-test for handle_outliers.
      3. Xtr, ct = fit_transform_train(X_train); Xte = transform_test(ct, X_test)
      4. names = get_feature_names(ct)
      5. return Xtr, Xte, ct, names
    (Resampling stays OUT of here — caller does SMOTE on Xtr only.)
    """
    raise NotImplementedError
