"""Generate the Task-4 (modeling) figures + the RQ1 time-aware summary.

Reads the tables written by ``src.modeling.train``:
  - ``reports/tables/model_metrics.csv``  held-out benchmark across the six checkpoints
  - ``reports/tables/cv_summary.csv``     repeated 5x5 CV at t=100 (optional)

and writes:
  - ``reports/figures/time_aware_{recall,pr_auc,roc_auc,f1}.png``  RQ1 curves
  - ``reports/figures/model_benchmark.png``                        Phase-2 bar (t=100)
  - ``reports/tables/time_aware_best.csv``  best model per checkpoint + earliest reliable t

Run: python -m tools.make_task4_figures
"""

from __future__ import annotations

import pandas as pd

from src import plots
from src.config import TABLES_DIR

# "Reliable enough for an instructor to act on" thresholds for RQ1. Recall is the
# binding one here (catching at-risk students); PR-AUC guards against a recall that
# only comes from predicting everyone at-risk.
RELIABLE_RECALL = 0.80
RELIABLE_PRAUC = 0.80


def main() -> int:
    metrics = pd.read_csv(TABLES_DIR / "model_metrics.csv")

    # RQ1: performance-vs-progress curves, one line per model.
    for m in ("recall", "pr_auc", "roc_auc", "f1"):
        plots.metric_vs_checkpoint(metrics, metric=m, name=f"time_aware_{m}")
    # Phase-2 benchmark: compare the algorithms at the full-course checkpoint.
    plots.model_comparison_bar(metrics, t_percent=100, name="model_benchmark")

    # Best model (by recall) at each checkpoint + whether it clears the reliability bar.
    best = (
        metrics.sort_values("recall", ascending=False)
        .groupby("t_percent", as_index=False)
        .first()[["t_percent", "model", "recall", "pr_auc", "roc_auc", "f1"]]
        .sort_values("t_percent")
        .reset_index(drop=True)
    )
    best["reliable"] = (best["recall"] >= RELIABLE_RECALL) & (best["pr_auc"] >= RELIABLE_PRAUC)
    best.to_csv(TABLES_DIR / "time_aware_best.csv", index=False)

    reliable_ts = best.loc[best["reliable"], "t_percent"]
    print("Best model per checkpoint (RQ1):")
    print(best.to_string(index=False))
    if len(reliable_ts):
        print(
            f"\nEarliest reliable checkpoint (recall>={RELIABLE_RECALL} & "
            f"PR-AUC>={RELIABLE_PRAUC}): t={int(reliable_ts.min())}% of course length."
        )
    else:
        print("\nNo checkpoint meets the reliability bar with the current models.")

    cv_path = TABLES_DIR / "cv_summary.csv"
    if cv_path.exists():
        cv = pd.read_csv(cv_path)
        print("\nPhase-2 CV benchmark @ t=100 (mean +/- std across 5x5 folds):")
        print(cv.to_string(index=False))

        # Uncertainty made visible (2026-07 audit gap): mean +/- 1 std error bars
        # per model, so the report shows variance, not only point estimates.
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt

        from src.eda.plot_style import apply_style, savefig

        apply_style()
        cvs = cv.sort_values("recall_mean", ascending=False).reset_index(drop=True)
        xs = list(range(len(cvs)))
        fig, ax = plt.subplots(figsize=(8.5, 4.8))
        for off, (metric, colour) in enumerate(
            [("recall", "#C0392B"), ("f1", "#0F4C81"), ("pr_auc", "#2E7D32")]
        ):
            ax.errorbar(
                [x + (off - 1) * 0.22 for x in xs],
                cvs[f"{metric}_mean"],
                yerr=cvs[f"{metric}_std"],
                fmt="o",
                capsize=4,
                label=metric.replace("_", "-").upper(),
                color=colour,
            )
        ax.set_xticks(xs)
        ax.set_xticklabels(cvs["model"])
        ax.set_ylabel("Score (mean ± 1 std over 25 CV folds)")
        ax.set_title("Cross-validated performance with uncertainty (5-fold × 5 seeds, t = 100%)")
        ax.legend()
        savefig(fig, "cv_uncertainty")
        plt.close(fig)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
