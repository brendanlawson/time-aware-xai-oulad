"""Inference with a saved checkpoint model.

Loads the persisted {model, ct, feat_names} bundle, applies the SAME fitted
ColumnTransformer to new rows, and returns labels + probabilities.

CLI:
    python -m src.modeling.predict --model logreg --t 40

See guide section "modeling/predict.py".
"""

from __future__ import annotations

import argparse
import os

import joblib
from loguru import logger
import pandas as pd
from sklearn.metrics import recall_score

from src.config import MODELS_DIR, TABLES_DIR
from src.evaluation.make_split import load_checkpoint_split
from src.features.preprocessing import (
    handle_missing,
    handle_outliers,
    make_X_y,
    transform_test,
)


def load_bundle(model_name: str, t_percent: int):
    """Load MODELS_DIR/f"{model_name}_t{t}.joblib".

    TODO: joblib.load(path); return the dict {model, ct, feat_names}.
    """
    path = MODELS_DIR / f"{model_name}_t{int(t_percent)}.joblib"
    if not path.exists():
        raise FileNotFoundError(
            f"no saved model at {path}; train it first with "
            f"`python -m src.modeling.train --model {model_name} --t {t_percent}`"
        )
    return joblib.load(path)


def predict(bundle: dict, X: pd.DataFrame) -> pd.DataFrame:
    """Apply the fitted ct + model to X; return frame with pred + proba.

    Raw checkpoint rows carry NaNs (imd_band, date_registration). If the bundle
    carries the train-learned preprocessing stats, impute/winsorize X with those
    TRAIN params first so the saved model is self-contained — no NaN reaches the
    encoders/scaler, and no test statistic leaks in.
    """
    stats = bundle.get("stats")
    if stats:
        X = handle_missing(X.copy(), stats=dict(stats["missing"]))
        X = handle_outliers(X, stats=dict(stats["outlier"]))
    # Reuse the ct fitted at train time — transform only, never refit.
    Xt = transform_test(bundle["ct"], X)
    proba = bundle["model"].predict_proba(Xt)[:, 1]
    pred = (proba >= 0.5).astype(int)
    return pd.DataFrame({"pred": pred, "proba": proba})


def predict_checkpoint(model_name: str, t_percent: int) -> pd.DataFrame:
    """Convenience: load the test split for t, predict, attach ids + truth.

    TODO: _, test_df = load_checkpoint_split(t); X, y = make_X_y(test_df);
    out = predict(load_bundle(...), X); attach id_student + y_true. Return out.
    """
    _, test_df = load_checkpoint_split(t_percent)
    X, y = make_X_y(test_df)
    out = predict(load_bundle(model_name, t_percent), X)
    # Positional alignment: X keeps test_df row order, so .to_numpy() lines up.
    out.insert(0, "id_student", test_df["id_student"].to_numpy())
    if y is not None:
        out["y_true"] = y.to_numpy()
    return out


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """TODO: --model, --t."""
    p = argparse.ArgumentParser(description="Score a checkpoint test split with a saved model.")
    p.add_argument("--model", required=True, help="model name used at training (e.g. logreg)")
    p.add_argument("--t", type=int, required=True, help="checkpoint %% whose saved model to load")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """TODO: parse args; predict_checkpoint; print/save predictions; return 0."""
    args = parse_args(argv)
    out = predict_checkpoint(args.model, args.t)
    out_path = TABLES_DIR / f"predictions_{args.model}_t{args.t}.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    out.to_csv(tmp, index=False)
    os.replace(tmp, out_path)  # atomic write
    msg = f"{len(out)} predictions -> {out_path}"
    if "y_true" in out.columns:
        rec = recall_score(out["y_true"], out["pred"], zero_division=0)
        msg += f" | recall(at-risk=1)={rec:.4f}"
    logger.info(msg)
    logger.info("\n" + out.head(10).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
