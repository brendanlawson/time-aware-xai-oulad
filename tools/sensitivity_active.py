"""Sensitivity analysis: does the model PREDICT at-risk, or just DETECT the gone?

Motivation
----------
59% of at-risk students are Withdrawn, and many have already formally unregistered
by the early checkpoints (48% by t=10%, 73% by t=40%). Flagging a student who has
already left is not "early prediction" — you cannot intervene on them. This script
re-scores the *already-trained* model on only the ACTIONABLE subgroup at each
checkpoint: students who are still enrolled (not yet unregistered at the cutoff
day). The gap between "full test" and "still-active" recall is the honest measure
of how much of the headline performance is real early prediction.

It does NOT retrain anything — it loads each saved bundle (models/{model}_t{t}.joblib)
and evaluates it on (a) the whole test split and (b) the still-active slice.

Run:
    python -m tools.sensitivity_active                 # default model: xgb (the best)
    python -m tools.sensitivity_active --model lgbm
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from src.config import CHECKPOINT_MAP_PATH, CHECKPOINTS, RAW_DATA_DIR, TABLES_DIR
from src.evaluation.make_split import load_checkpoint_split
from src.features.preprocessing import make_X_y
from src.modeling.predict import load_bundle, predict

KEY = ["code_module", "code_presentation", "id_student"]
PRES = ["code_module", "code_presentation"]


def _metrics(y, pred, proba) -> dict:
    """Headline metrics for one slice; AUCs need both classes present."""
    y, pred, proba = np.asarray(y), np.asarray(pred), np.asarray(proba)
    both = len(np.unique(y)) > 1
    return {
        "n": int(len(y)),
        "at_risk_rate": round(float(y.mean()), 3),
        "recall": round(float(recall_score(y, pred, zero_division=0)), 4),
        "precision": round(float(precision_score(y, pred, zero_division=0)), 4),
        "pr_auc": round(float(average_precision_score(y, proba)), 4) if both else None,
        "roc_auc": round(float(roc_auc_score(y, proba)), 4) if both else None,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="xgb", help="saved model name (default: xgb)")
    args = ap.parse_args(argv)

    # date_unregistration tells us WHEN a student left; checkpoint_map gives the
    # cutoff day per presentation at each t%. A student is "still active at t" if
    # they have not unregistered on or before that cutoff day.
    reg = pd.read_csv(RAW_DATA_DIR / "studentRegistration.csv")[KEY + ["date_unregistration"]]
    cmap = pd.read_csv(CHECKPOINT_MAP_PATH)

    rows = []
    for t in CHECKPOINTS:
        # 1. The held-out TEST split for this checkpoint (same frozen test students).
        _, test_df = load_checkpoint_split(t)
        X, y = make_X_y(test_df)

        # 2. Score it with the model trained at this checkpoint (no retraining).
        out = predict(load_bundle(args.model, t), X)
        y = y.to_numpy()
        pred = out["pred"].to_numpy()
        proba = out["proba"].to_numpy()

        # 3. Per test row, is the student still enrolled at this cutoff day?
        cut = cmap.loc[cmap.t_percent == t, PRES + ["cutoff_day"]]
        td = test_df[KEY].merge(reg, on=KEY, how="left").merge(cut, on=PRES, how="left")
        active = (
            td["date_unregistration"].isna() | (td["date_unregistration"] > td["cutoff_day"])
        ).to_numpy()

        full = _metrics(y, pred, proba)
        act = _metrics(y[active], pred[active], proba[active])
        rows.append(
            {
                "t_percent": t,
                **{f"full_{k}": v for k, v in full.items()},
                **{f"active_{k}": v for k, v in act.items()},
                "withdrawn_already_gone": int((~active).sum()),
            }
        )

    res = pd.DataFrame(rows)
    out_path = TABLES_DIR / f"sensitivity_active_{args.model}.csv"
    res.to_csv(out_path, index=False)

    view = res[
        [
            "t_percent",
            "full_n",
            "active_n",
            "full_at_risk_rate",
            "active_at_risk_rate",
            "full_recall",
            "active_recall",
            "full_pr_auc",
            "active_pr_auc",
        ]
    ]
    print(f"Model: {args.model}  (full test vs still-active-at-checkpoint)\n")
    print(view.to_string(index=False))
    print(f"\nSaved -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
