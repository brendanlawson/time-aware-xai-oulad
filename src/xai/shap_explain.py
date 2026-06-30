"""SHAP explanations for the trained checkpoint models.

Produces local (per-student) attributions and global feature importance, plus the
summary/bar plots used in the report. Operates on the SAME transformed feature
space the model saw, using feat_names recovered from the fitted ColumnTransformer.

See guide section "xai/shap_explain.py".
"""

from __future__ import annotations

from loguru import logger
import numpy as np
import pandas as pd

from src.config import FIGURES_DIR, RANDOM_SEED

# at-risk is the positive class (label 1) in every checkpoint model.
POSITIVE_CLASS = 1

# Substrings used to route an estimator to the right SHAP explainer family.
_TREE_MARKERS = (
    "randomforest",
    "extratrees",
    "extratree",
    "decisiontree",
    "gradientboosting",
    "histgradientboosting",
    "xgb",
    "lgbm",
    "lightgbm",
    "catboost",
    "boost",
    "tree",
)
_LINEAR_MARKERS = (
    "logistic",
    "linear",
    "ridge",
    "lasso",
    "elasticnet",
    "sgd",
    "perceptron",
)


def _model_family(model) -> str:
    """Best-effort routing of ``model`` into ``'tree'`` / ``'linear'`` / ``'other'``."""
    name = type(model).__name__.lower()
    if (
        any(marker in name for marker in _TREE_MARKERS)
        or hasattr(model, "estimators_")
        or hasattr(model, "tree_")
    ):
        return "tree"
    if any(marker in name for marker in _LINEAR_MARKERS) or hasattr(model, "coef_"):
        return "linear"
    return "other"


def _summarize_background(X_background, k: int = 50):
    """Shrink a background set to <=``k`` representatives for KernelExplainer speed."""
    import shap

    n = len(X_background)
    if n <= k:
        return X_background
    try:
        return shap.kmeans(X_background, k)
    except Exception:  # pragma: no cover - kmeans needs dense numeric data
        rng = np.random.RandomState(RANDOM_SEED)
        idx = rng.choice(n, size=k, replace=False)
        if hasattr(X_background, "iloc"):
            return X_background.iloc[idx]
        return np.asarray(X_background)[idx]


def build_explainer(model, X_background):
    """Return a SHAP explainer matched to the model family.

    Tree models use ``shap.TreeExplainer``, linear models use
    ``shap.LinearExplainer``, and anything else falls back to
    ``shap.KernelExplainer`` over ``model.predict_proba``. Works for logreg / rf /
    gboost; if the preferred explainer cannot be constructed (e.g. a model SHAP's
    tree path does not support) it degrades gracefully to the kernel fallback.
    """
    import shap

    family = _model_family(model)
    if family == "tree":
        try:
            return shap.TreeExplainer(model)
        except Exception as exc:  # pragma: no cover - depends on model internals
            logger.warning(f"TreeExplainer unavailable ({exc}); using KernelExplainer.")
    elif family == "linear":
        try:
            return shap.LinearExplainer(model, X_background)
        except Exception as exc:  # pragma: no cover - depends on model internals
            logger.warning(f"LinearExplainer unavailable ({exc}); using KernelExplainer.")

    predict_fn = model.predict_proba if hasattr(model, "predict_proba") else model.predict
    return shap.KernelExplainer(predict_fn, _summarize_background(X_background))


def _select_positive_class(values, class_index: int = POSITIVE_CLASS) -> np.ndarray:
    """Normalise any SHAP return shape to a 2-D ``(n_samples, n_features)`` array."""
    if isinstance(values, list):  # legacy per-class list of arrays
        idx = class_index if len(values) > class_index else len(values) - 1
        return np.asarray(values[idx])
    values = np.asarray(values)
    if values.ndim == 3:  # (n_samples, n_features, n_classes)
        idx = class_index if values.shape[2] > class_index else values.shape[2] - 1
        return values[:, :, idx]
    return values  # already (n_samples, n_features)


def compute_shap_values(explainer, X):
    """Return SHAP values for X (the positive/at-risk class).

    Calls the explainer (``.shap_values`` when available, else the callable API);
    when it returns per-class output the at-risk class is selected. Always returns
    an array shaped ``(n_samples, n_features)``.
    """
    if hasattr(explainer, "shap_values"):
        values = explainer.shap_values(X)
    else:
        values = explainer(X).values
    return _select_positive_class(values)


def global_importance(shap_values, feature_names: list[str]) -> pd.DataFrame:
    """Mean(|SHAP|) per feature, sorted descending.

    Returns a tidy ``DataFrame[feature, importance]`` sorted descending. This
    ranking is the input to the stability analysis.
    """
    values = _select_positive_class(shap_values)
    importance = np.abs(values).mean(axis=0)
    importance = np.asarray(importance).ravel()
    if len(importance) != len(feature_names):
        raise ValueError(
            f"shap_values has {len(importance)} features but received "
            f"{len(feature_names)} feature_names."
        )
    out = pd.DataFrame({"feature": list(feature_names), "importance": importance})
    return out.sort_values("importance", ascending=False, ignore_index=True)


def save_summary_plot(shap_values, X, feature_names, name: str) -> "object":
    """Render ``shap.summary_plot`` for X and save it to ``FIGURES_DIR/<name>.png``.

    Returns the path to the saved figure. Forces the Agg backend so the figure can
    be written headlessly.
    """
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
    import shap

    values = _select_positive_class(shap_values)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = FIGURES_DIR / f"{name}.png"

    plt.figure()
    shap.summary_plot(values, X, feature_names=list(feature_names), show=False)
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close("all")
    return out_path
