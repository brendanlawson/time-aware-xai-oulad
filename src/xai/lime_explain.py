"""LIME explanations for individual at-risk predictions.

LIME perturbs around one instance and fits a local linear surrogate, giving a
per-student "why" that complements SHAP. We compare SHAP vs LIME agreement and
feed both into the stability analysis.

See guide section "xai/lime_explain.py".
"""

from __future__ import annotations

import numpy as np  # noqa: F401
import pandas as pd  # noqa: F401


def build_explainer(X_train, feature_names: list[str], class_names=("not_at_risk", "at_risk")):
    """Create a LimeTabularExplainer over the TRANSFORMED training matrix.

    TODO: lime.lime_tabular.LimeTabularExplainer(X_train, feature_names=...,
    class_names=..., discretize_continuous=True, random_state=RANDOM_SEED).
    """
    raise NotImplementedError


def explain_instance(explainer, model, x_row, num_features: int = 10) -> pd.DataFrame:
    """Explain ONE instance; return a tidy (feature, weight) frame.

    TODO: exp = explainer.explain_instance(x_row, model.predict_proba,
    num_features=num_features); convert exp.as_list() to a DataFrame.
    """
    raise NotImplementedError


def local_importance_vector(explainer, model, X, feature_names, num_features=None) -> pd.DataFrame:
    """Stack per-instance LIME weights into a (n_samples x n_features) frame.

    TODO: loop explain_instance over rows, align weights to feature_names. This
    aligned matrix is what stability.py compares across seeds/checkpoints.
    """
    raise NotImplementedError
