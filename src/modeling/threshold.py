"""Decision-threshold tuning for the at-risk classifier.

The default 0.5 cut-off is arbitrary for an imbalanced early-warning task where a
missed at-risk student (false negative) costs more than a false alarm. This module
sweeps the probability threshold on the held-out test predictions and selects
operating points under three transparent policies:

* ``f1``            - the threshold maximising F1 (balanced precision/recall);
* ``youden``        - Youden's J = recall + specificity - 1 (best single ROC cut);
* ``recall>=target``- the *highest* threshold still reaching a target recall, i.e.
                      catch >= target%% of at-risk students at the best precision
                      that budget allows.

CLI:
    python -m src.modeling.threshold --model xgb --t 100 --target-recall 0.9

See guide section "modeling/threshold.py".
"""

from __future__ import annotations

import argparse
import os

from loguru import logger
import numpy as np
import pandas as pd

from src.config import TABLES_DIR

THRESHOLD_TABLE_PATH = TABLES_DIR / "threshold_tuning.csv"


def sweep_thresholds(y_true, y_proba, n: int = 101) -> pd.DataFrame:
    """Precision / recall / F1 / specificity over an evenly-spaced threshold grid.

    Returns one row per threshold in ``linspace(0, 1, n)`` with the at-risk
    (positive-class) precision, recall, F1 and specificity — the tidy input for
    :func:`src.plots.threshold_curve` and the policy pickers below.
    """
    y_true = np.asarray(y_true).astype(int)
    y_proba = np.asarray(y_proba, dtype=float)
    pos = y_true == 1
    n_pos = int(pos.sum())
    n_neg = int((~pos).sum())
    rows = []
    for thr in np.linspace(0.0, 1.0, n):
        pred = y_proba >= thr
        tp = int(np.sum(pred & pos))
        fp = int(np.sum(pred & ~pos))
        tn = n_neg - fp
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / n_pos if n_pos else 0.0
        specificity = tn / n_neg if n_neg else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        rows.append(
            {
                "threshold": round(float(thr), 4),
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": round(f1, 4),
                "specificity": round(specificity, 4),
            }
        )
    return pd.DataFrame(rows)


def _metrics_at(sweep: pd.DataFrame, thr: float) -> dict:
    """Nearest-grid-row precision/recall/f1 at threshold ``thr`` (for reporting)."""
    i = (sweep["threshold"] - thr).abs().idxmin()
    r = sweep.loc[i]
    return {
        "threshold": float(r["threshold"]),
        "precision": float(r["precision"]),
        "recall": float(r["recall"]),
        "f1": float(r["f1"]),
    }


def pick_by_f1(sweep: pd.DataFrame) -> float:
    """Threshold maximising F1 (ties -> lowest threshold, i.e. higher recall)."""
    return float(sweep.loc[sweep["f1"].idxmax(), "threshold"])


def pick_by_youden(sweep: pd.DataFrame) -> float:
    """Threshold maximising Youden's J = recall + specificity - 1."""
    j = sweep["recall"] + sweep["specificity"] - 1.0
    return float(sweep.loc[j.idxmax(), "threshold"])


def pick_by_target_recall(sweep: pd.DataFrame, target: float = 0.9) -> float:
    """Highest threshold whose recall is still >= ``target`` (best precision at target).

    Falls back to threshold 0.0 (recall maximised) if no cut reaches the target.
    """
    ok = sweep[sweep["recall"] >= target]
    return float(ok["threshold"].max()) if not ok.empty else 0.0


def tune(y_true, y_proba, target_recall: float = 0.9):
    """Sweep + pick under all three policies; return ``(sweep_df, chosen_dict)``.

    ``chosen_dict`` maps policy -> threshold; feed it straight to
    :func:`src.plots.threshold_curve` and :func:`policy_table`.
    """
    sweep = sweep_thresholds(y_true, y_proba)
    chosen = {
        "f1": pick_by_f1(sweep),
        "youden": pick_by_youden(sweep),
        f"recall>={target_recall:g}": pick_by_target_recall(sweep, target_recall),
    }
    return sweep, chosen


def policy_table(
    sweep: pd.DataFrame, chosen: dict, model_name: str, t_percent: int
) -> pd.DataFrame:
    """One row per policy (plus the naive 0.5 default) with the resulting P/R/F1."""
    default = _metrics_at(sweep, 0.5)
    default["policy"] = "default(0.5)"
    rows = [default]
    for policy, thr in chosen.items():
        m = _metrics_at(sweep, thr)
        m["policy"] = policy
        rows.append(m)
    df = pd.DataFrame(rows)
    df.insert(0, "model", model_name)
    df.insert(1, "t_percent", int(t_percent))
    return df[["model", "t_percent", "policy", "threshold", "precision", "recall", "f1"]]


def tune_checkpoint(model_name: str, t_percent: int, target_recall: float = 0.9):
    """Load checkpoint predictions and tune the threshold on them.

    Returns ``(sweep_df, chosen_dict, policy_table_df)`` using the held-out test
    predictions from :func:`src.modeling.predict.predict_checkpoint`.
    """
    from src.modeling.predict import predict_checkpoint

    out = predict_checkpoint(model_name, t_percent)
    sweep, chosen = tune(out["y_true"], out["proba"], target_recall)
    table = policy_table(sweep, chosen, model_name, t_percent)
    return sweep, chosen, table


def _write_csv_atomic(df: pd.DataFrame, path) -> None:
    """Write a CSV via temp file + os.replace (atomic on the same filesystem)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    df.to_csv(tmp, index=False)
    os.replace(tmp, path)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI: --model / --t (which saved model to tune) and --target-recall."""
    p = argparse.ArgumentParser(description="Tune the decision threshold for a saved model.")
    p.add_argument("--model", required=True, help="model name used at training (e.g. xgb)")
    p.add_argument("--t", type=int, required=True, help="checkpoint %% whose saved model to load")
    p.add_argument("--target-recall", type=float, default=0.9, help="target at-risk recall")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Tune one (model, t); write threshold_tuning.csv and log the policy table."""
    args = parse_args(argv)
    _sweep, _chosen, table = tune_checkpoint(args.model, args.t, args.target_recall)
    _write_csv_atomic(table, THRESHOLD_TABLE_PATH)
    logger.info(f"threshold policies -> {THRESHOLD_TABLE_PATH}\n" + table.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
