"""Hyperparameter tuning (Chapter 6: fine-tuning) via RandomizedSearchCV.

For the two strongest models (xgb, lgbm) at the key checkpoints (40%, 100%):
randomly sample `--n-iter` hyperparameter combos and score each with 5-fold
StratifiedGroupKFold (grouped by id_student, so a student never spans folds),
optimising PR-AUC. SMOTE runs INSIDE each fold (imblearn Pipeline) so no
synthetic sample leaks into validation. Then refit the best combo on the whole
train fold, evaluate on the held-out test, and compare against the default model.

Honest simplification: encoding/scaling are fit once on the full train (standard
for HP search — the search compares MODEL knobs, and per-fold rescaling barely
moves the ranking). The leakage-sensitive step (SMOTE) is still per-fold.

Outputs:
  reports/tables/tuning_results.csv   default-vs-tuned (PR-AUC, recall, F1) + best params
  models/{model}_t{t}_tuned.joblib    the tuned bundle (loadable by src.modeling.predict)

Run:
    python -m tools.tune_models                          # xgb+lgbm at t=40,100
    python -m tools.tune_models --model xgb --t 40 --n-iter 60
"""

from __future__ import annotations

import argparse
import json

from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from loguru import logger
import pandas as pd
from scipy.stats import randint, uniform
from sklearn.model_selection import RandomizedSearchCV, StratifiedGroupKFold

from src.config import MODELS_DIR, RANDOM_SEED, TABLES_DIR
from src.evaluation.make_split import load_checkpoint_split
from src.features.preprocessing import make_X_y, preprocess
from src.modeling.train import _dump_atomic, build_model, evaluate

# Step 3: the "knob spaces". Each entry is model__<param>: a distribution to
# sample from. prefix "model__" targets the estimator step inside the pipeline.
SEARCH_SPACES = {
    "xgb": {
        "model__n_estimators": randint(200, 800),
        "model__max_depth": randint(3, 10),
        "model__learning_rate": uniform(0.01, 0.29),  # [0.01, 0.30]
        "model__subsample": uniform(0.6, 0.4),  # [0.6, 1.0]
        "model__colsample_bytree": uniform(0.6, 0.4),
        "model__min_child_weight": randint(1, 8),
    },
    "lgbm": {
        "model__n_estimators": randint(200, 800),
        "model__num_leaves": randint(15, 120),
        "model__learning_rate": uniform(0.01, 0.29),
        "model__colsample_bytree": uniform(0.6, 0.4),
        "model__min_child_samples": randint(5, 60),
        "model__reg_lambda": uniform(0.0, 5.0),
    },
}


def _base(model_name: str, seed: int):
    """Single-threaded base estimator (the search parallelises across folds)."""
    if model_name == "xgb":
        from xgboost import XGBClassifier

        return XGBClassifier(
            random_state=seed, n_jobs=1, eval_metric="logloss", tree_method="hist"
        )
    if model_name == "lgbm":
        from lightgbm import LGBMClassifier

        return LGBMClassifier(random_state=seed, n_jobs=1, verbose=-1)
    raise ValueError(f"tuning not configured for {model_name!r}")


def tune_one(model_name: str, t: int, n_iter: int, seed: int = RANDOM_SEED) -> dict:
    """Tune one (model, checkpoint); return a default-vs-tuned comparison row."""
    # Steps 1-2: frozen split + preprocess (fit on train only).
    train_df, test_df = load_checkpoint_split(t)
    X_train, y_train = make_X_y(train_df)
    X_test, y_test = make_X_y(test_df)
    Xtr, Xte, ct, feat_names, stats = preprocess(
        X_train, X_test, scaler_save_path=None, return_stats=True
    )
    groups = train_df["id_student"].to_numpy()  # keep a student inside one fold

    # Steps 3-4: random search, SMOTE inside each fold, scored by PR-AUC.
    pipe = ImbPipeline([("smote", SMOTE(random_state=seed)), ("model", _base(model_name, seed))])
    cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)
    search = RandomizedSearchCV(
        pipe,
        SEARCH_SPACES[model_name],
        n_iter=n_iter,
        scoring="average_precision",  # PR-AUC
        cv=cv,
        random_state=seed,
        n_jobs=-1,
        refit=True,  # step 5: refit best combo on the whole train fold
    )
    logger.info(f"tuning {model_name} @ t={t}: {n_iter} combos x 5-fold CV ...")
    search.fit(Xtr, y_train, groups=groups)

    # Step 5: tuned model on the held-out test.
    tuned = search.best_estimator_.named_steps["model"]
    tuned_metrics = evaluate(tuned, Xte, y_test)

    # Default model (same SMOTE, default knobs) for an apples-to-apples baseline.
    Xtr_res, y_res = SMOTE(random_state=seed).fit_resample(Xtr, y_train)
    default = build_model(model_name, seed).fit(Xtr_res, y_res)
    default_metrics = evaluate(default, Xte, y_test)

    # Save the tuned bundle so it can be scored / explained later.
    bundle = {"model": tuned, "ct": ct, "feat_names": feat_names, "stats": stats}
    _dump_atomic(bundle, MODELS_DIR / f"{model_name}_t{t}_tuned.joblib")

    best_params = {k.replace("model__", ""): v for k, v in search.best_params_.items()}
    logger.info(
        f"{model_name} @ t={t}: PR-AUC default={default_metrics['pr_auc']} "
        f"-> tuned={tuned_metrics['pr_auc']} | recall {default_metrics['recall']} "
        f"-> {tuned_metrics['recall']}"
    )
    # Step 6: one comparison row.
    return {
        "model": model_name,
        "t_percent": t,
        "cv_best_pr_auc": round(float(search.best_score_), 4),
        "default_pr_auc": default_metrics["pr_auc"],
        "tuned_pr_auc": tuned_metrics["pr_auc"],
        "default_recall": default_metrics["recall"],
        "tuned_recall": tuned_metrics["recall"],
        "default_f1": default_metrics["f1"],
        "tuned_f1": tuned_metrics["f1"],
        "best_params": json.dumps(best_params),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Hyperparameter tuning for the at-risk models.")
    ap.add_argument("--model", choices=["xgb", "lgbm"], default=None, help="default: both")
    ap.add_argument("--t", type=int, default=None, help="checkpoint %% (default: 40 and 100)")
    ap.add_argument("--n-iter", type=int, default=40, help="random combos per model (default 40)")
    args = ap.parse_args(argv)

    models = [args.model] if args.model else ["xgb", "lgbm"]
    checkpoints = [args.t] if args.t is not None else [40, 100]

    # Resume: a (model, t) already in tuning_results.csv is skipped, and the table
    # is rewritten after every newly-tuned combo (kill-safe for the long search).
    out = TABLES_DIR / "tuning_results.csv"
    rows = pd.read_csv(out).to_dict("records") if out.exists() else []
    done = {(r["model"], int(r["t_percent"])) for r in rows}
    for m in models:
        for t in checkpoints:
            if (m, t) in done:
                logger.info(f"skip (resumed): {m} @ t={t}")
                continue
            rows.append(tune_one(m, t, args.n_iter))
            pd.DataFrame(rows).to_csv(out, index=False)
    res = pd.DataFrame(rows)

    show = res[
        ["model", "t_percent", "default_pr_auc", "tuned_pr_auc", "default_recall", "tuned_recall"]
    ]
    print("\nDefault vs Tuned (held-out test):")
    print(show.to_string(index=False))
    print(f"\nSaved -> {out}  | tuned bundles -> models/*_tuned.joblib")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
