"""Inference with a saved checkpoint model.

Loads the persisted {model, ct, feat_names} bundle, applies the SAME fitted
ColumnTransformer to new rows, and returns labels + probabilities.

CLI:
    python -m src.modeling.predict --model logreg --t 40

See guide section "modeling/predict.py".
"""

from __future__ import annotations

import argparse

import pandas as pd


def load_bundle(model_name: str, t_percent: int):
    """Load MODELS_DIR/f"{model_name}_t{t}.joblib".

    TODO: joblib.load(path); return the dict {model, ct, feat_names}.
    """
    raise NotImplementedError


def predict(bundle: dict, X: pd.DataFrame) -> pd.DataFrame:
    """Apply the fitted ct + model to X; return frame with pred + proba.

    TODO: Xt = transform_test(bundle["ct"], X); proba = model.predict_proba(Xt)[:,1];
    pred = (proba >= 0.5). Return DataFrame(pred, proba).
    """
    raise NotImplementedError


def predict_checkpoint(model_name: str, t_percent: int) -> pd.DataFrame:
    """Convenience: load the test split for t, predict, attach ids + truth.

    TODO: _, test_df = load_checkpoint_split(t); X, y = make_X_y(test_df);
    out = predict(load_bundle(...), X); attach id_student + y_true. Return out.
    """
    raise NotImplementedError


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """TODO: --model, --t."""
    raise NotImplementedError


def main(argv: list[str] | None = None) -> int:
    """TODO: parse args; predict_checkpoint; print/save predictions; return 0."""
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
