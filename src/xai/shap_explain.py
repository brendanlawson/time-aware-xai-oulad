"""SHAP explanations for the trained checkpoint models.

Produces local (per-student) attributions and global feature importance, plus the
summary/bar plots used in the report. Operates on the SAME transformed feature
space the model saw, using feat_names recovered from the fitted ColumnTransformer.

See guide section "xai/shap_explain.py".
"""

from __future__ import annotations

import numpy as np  # noqa: F401
import pandas as pd

from src.config import FIGURES_DIR  # noqa: F401


def build_explainer(model, X_background):
    """Return a SHAP explainer matched to the model family.

    TODO: tree models -> shap.TreeExplainer(model); linear -> shap.LinearExplainer;
    fallback -> shap.Explainer(model.predict_proba, X_background). Keep it generic
    so it works for logreg/rf/gboost.
    """
    raise NotImplementedError


def compute_shap_values(explainer, X):
    """Return SHAP values for X (the positive/at-risk class).

    TODO: call the explainer; if it returns per-class values, select the at-risk
    class. Return an array shaped (n_samples, n_features).
    """
    raise NotImplementedError


def global_importance(shap_values, feature_names: list[str]) -> pd.DataFrame:
    """Mean(|SHAP|) per feature, sorted descending.

    TODO: return DataFrame[feature, importance] sorted desc. This ranking is the
    input to the stability analysis.
    """
    raise NotImplementedError


def save_summary_plot(shap_values, X, feature_names, name: str) -> "object":
    """TODO: shap.summary_plot(...); savefig to FIGURES_DIR/<name>.png; return path."""
    raise NotImplementedError
