"""Train at-risk models at each time checkpoint.

Pipeline per (checkpoint t, model):
  load_checkpoint_split(t) -> make_X_y -> preprocess (anti-leakage) ->
  SMOTE on train only -> fit -> evaluate on the held-out test -> persist.

The point of the project is COMPARING performance across the six checkpoints, so
metrics are collected into one tidy table (model, t_percent, auc, f1, recall, ...).

CLI:
    python -m src.modeling.train                 # all models x all checkpoints
    python -m src.modeling.train --model logreg --t 40

See guide section "modeling/train.py".
"""

from __future__ import annotations

import argparse

import pandas as pd  # noqa: F401

from src.config import CHECKPOINTS, RANDOM_SEED


def build_model(name: str, seed: int = RANDOM_SEED):
    """Return an unfitted estimator for ``name``.

    TODO: support at least {"logreg", "rf", "gboost"}:
      - logreg: LogisticRegression(max_iter=1000, class_weight=..., random_state)
      - rf    : RandomForestClassifier(random_state=seed, n_jobs=-1)
      - gboost: HistGradientBoostingClassifier(random_state=seed) or XGBClassifier
    Keep a small registry dict so the CLI can list valid names.
    """
    raise NotImplementedError


def evaluate(model, X_test, y_test) -> dict:
    """Compute the metric suite on the test set.

    TODO: predict + predict_proba; return dict with roc_auc, pr_auc (average
    precision), f1, recall, precision, balanced_accuracy, brier. Recall matters
    most here (catching at-risk students) — note it in the report.
    """
    raise NotImplementedError


def train_at_checkpoint(t_percent: int, model_name: str, seed: int = RANDOM_SEED) -> dict:
    """Full train+evaluate for one (t, model); persist the fitted pipeline.

    TODO:
      1. train_df, test_df = load_checkpoint_split(t_percent)
      2. X_train, y_train = make_X_y(train_df); X_test, y_test = make_X_y(test_df)
      3. Xtr, Xte, ct, feat_names = preprocess(X_train, X_test)
      4. SMOTE(random_state=seed).fit_resample(Xtr, y_train)  # train only
      5. model = build_model(model_name, seed).fit(Xtr_res, y_res)
      6. metrics = evaluate(model, Xte, y_test)
      7. Save {model, ct, feat_names} to MODELS_DIR/f"{model_name}_t{t}.joblib".
      8. Return {"model": model_name, "t_percent": t, **metrics}.
    """
    raise NotImplementedError


def train_all(models=("logreg", "rf", "gboost"), checkpoints=CHECKPOINTS) -> "pd.DataFrame":
    """Loop over models x checkpoints; return + save the metrics table.

    TODO: collect train_at_checkpoint rows into a DataFrame; write
    TABLES_DIR/"model_metrics.csv". (Consider resume: skip a combo whose model
    file already exists.)
    """
    raise NotImplementedError


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """TODO: --model (optional), --t (optional)."""
    raise NotImplementedError


def main(argv: list[str] | None = None) -> int:
    """TODO: parse args; train one combo or train_all(); return 0."""
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
