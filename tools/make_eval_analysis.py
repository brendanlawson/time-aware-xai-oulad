"""Generate the supplementary model-evaluation artifacts (Phase 2-3 extras).

Fills the gaps flagged in the project review — confusion matrix, decision-threshold
tuning, and statistical significance tests comparing the benchmark models — all
built on the already-trained checkpoint bundles and the repeated-CV scores.

Writes:
  - reports/figures/confusion_default_t{t}.png   default 0.5 cut
  - reports/figures/confusion_tuned_t{t}.png     tuned (target-recall) cut
  - reports/figures/threshold_tuning.png         P/R/F1 vs threshold
  - reports/tables/threshold_tuning.csv          per-policy P/R/F1
  - reports/tables/model_friedman.csv            Friedman test per metric
  - reports/tables/model_pairwise_wilcoxon.csv   post-hoc Wilcoxon (Holm)

CLI:
    python -m tools.make_eval_analysis                       # best model by recall @ t=100
    python -m tools.make_eval_analysis --model xgb --t 100 --target-recall 0.9
"""

from __future__ import annotations

import argparse

from loguru import logger
import pandas as pd

from src import plots
from src.config import TABLES_DIR
from src.evaluation import stat_tests
from src.modeling import threshold as thr
from src.modeling.predict import predict_checkpoint

# CV is only run at t=100 (see train.cross_validate_all default), so the model
# comparison tests always use the t=100 fold scores.
CV_CHECKPOINT = 100


def _best_model(t_percent: int) -> str:
    """Model with the highest held-out recall at checkpoint t (headline pick)."""
    m = pd.read_csv(TABLES_DIR / "model_metrics.csv")
    sub = m[m["t_percent"] == t_percent].sort_values("recall", ascending=False)
    return str(sub.iloc[0]["model"])


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Confusion matrix + threshold tuning + stat tests.")
    p.add_argument("--model", default=None, help="model to analyse (default: best recall @ t)")
    p.add_argument("--t", type=int, default=100, help="checkpoint %% to analyse (default 100)")
    p.add_argument("--target-recall", type=float, default=0.9, help="target at-risk recall")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    model = args.model or _best_model(args.t)
    logger.info(f"eval extras: model={model} t={args.t} target_recall={args.target_recall}")

    out = predict_checkpoint(model, args.t)
    y_true, y_proba = out["y_true"], out["proba"]

    # 1. Threshold tuning: sweep + per-policy table + curve figure.
    sweep, chosen = thr.tune(y_true, y_proba, args.target_recall)
    table = thr.policy_table(sweep, chosen, model, args.t)
    thr._write_csv_atomic(table, thr.THRESHOLD_TABLE_PATH)
    plots.threshold_curve(sweep, chosen, name="threshold_tuning")

    # 2. Confusion matrices: naive 0.5 vs the tuned target-recall cut, side by side.
    tuned_key = next(k for k in chosen if k.startswith("recall"))
    tuned_thr = chosen[tuned_key]
    plots.confusion_matrix_plot(
        y_true,
        (y_proba >= 0.5).astype(int),
        name=f"confusion_default_t{args.t}",
        title=f"{model} @ t={args.t}% — default threshold 0.50",
    )
    plots.confusion_matrix_plot(
        y_true,
        (y_proba >= tuned_thr).astype(int),
        name=f"confusion_tuned_t{args.t}",
        title=f"{model} @ t={args.t}% — tuned {tuned_thr:.2f} ({tuned_key})",
    )

    # 3. Statistical significance across models on the paired CV folds.
    fried, pair = stat_tests.run_all(t_percent=CV_CHECKPOINT)
    stat_tests._write_csv_atomic(fried, stat_tests.FRIEDMAN_PATH)
    stat_tests._write_csv_atomic(pair, stat_tests.PAIRWISE_PATH)

    logger.info("threshold policy table:\n" + table.to_string(index=False))
    logger.info("friedman per metric:\n" + fried.to_string(index=False))
    logger.info(
        "pairwise wilcoxon (recall):\n" + pair[pair["metric"] == "recall"].to_string(index=False)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
