"""LIME explanations for individual at-risk predictions.

LIME perturbs around one instance and fits a local linear surrogate, giving a
per-student "why" that complements SHAP. We compare SHAP vs LIME agreement and
feed both into the stability analysis.

See guide section "xai/lime_explain.py".
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import RANDOM_SEED

# LIME explains the positive (at-risk) class by default.
POSITIVE_LABEL = 1


def build_explainer(X_train, feature_names: list[str], class_names=("not_at_risk", "at_risk")):
    """Create a LimeTabularExplainer over the TRANSFORMED training matrix.

    Wraps ``lime.lime_tabular.LimeTabularExplainer`` with the model's feature and
    class names, ``discretize_continuous=True`` and the project ``RANDOM_SEED`` so
    the perturbations are reproducible.
    """
    from lime.lime_tabular import LimeTabularExplainer

    return LimeTabularExplainer(
        np.asarray(X_train, dtype=float),
        feature_names=list(feature_names),
        class_names=list(class_names),
        mode="classification",
        discretize_continuous=True,
        random_state=RANDOM_SEED,
    )


def _explained_label(exp, positive: int = POSITIVE_LABEL) -> int:
    """Pick the at-risk label from a LIME explanation (fallback: first available)."""
    available = list(exp.as_map().keys())
    return positive if positive in available else available[0]


def explain_instance(explainer, model, x_row, num_features: int = 10) -> pd.DataFrame:
    """Explain ONE instance; return a tidy (feature, weight) frame.

    Runs ``explainer.explain_instance(x_row, model.predict_proba, ...)`` for the
    at-risk class and converts ``exp.as_list()`` into a ``DataFrame[feature, weight]``.
    """
    x = np.asarray(x_row, dtype=float).ravel()
    exp = explainer.explain_instance(x, model.predict_proba, num_features=num_features)
    pairs = exp.as_list(label=_explained_label(exp))
    return pd.DataFrame(pairs, columns=["feature", "weight"])


def local_importance_vector(explainer, model, X, feature_names, num_features=None) -> pd.DataFrame:
    """Stack per-instance LIME weights into a (n_samples x n_features) frame.

    Explains each row and aligns its signed LIME weights to ``feature_names`` (by
    feature index), filling unselected features with 0. This aligned matrix is what
    stability.py compares across seeds/checkpoints (typically via mean |weight|).
    """
    X = np.asarray(X, dtype=float)
    if X.ndim == 1:
        X = X.reshape(1, -1)
    names = list(feature_names)
    n_features = len(names)
    k = n_features if num_features is None else min(num_features, n_features)

    rows = []
    for i in range(X.shape[0]):
        exp = explainer.explain_instance(X[i], model.predict_proba, num_features=k)
        weights = dict(exp.as_map()[_explained_label(exp)])  # {feature_idx: weight}
        rows.append([weights.get(j, 0.0) for j in range(n_features)])
    return pd.DataFrame(rows, columns=names)
