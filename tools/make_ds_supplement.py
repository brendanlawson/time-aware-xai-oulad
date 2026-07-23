"""Three supplementary data-science analyses (2026-07-20).

Addresses the three gaps identified in the project review:

1. Rule-based baseline  -- how much does XGBoost add over a two-feature
   threshold rule?  Uses days_since_last_activity and weighted_score_to_date
   directly on raw test data; sweeps thresholds and picks the combination
   that maximises F1 on the test set, then reports recall at that operating
   point alongside XGBoost's held-out recall.

2. Probability calibration -- are XGBoost's probability outputs reliable?
   Plots a reliability diagram (calibration curve) per checkpoint and
   computes ECE (Expected Calibration Error) and MCE (Maximum Calibration
   Error) so an operator knows whether the raw probability should be trusted
   as a risk score.

3. Feature ablation -- how much does each feature group contribute?
   Retrains XGBoost at t=100% using only the top-k raw features (ranked by
   mean |SHAP|) for k in {3, 5, 7, 10, 15, 20, all}.  Shows where the
   recall plateau begins, revealing whether a leaner model is viable.

Outputs:
  reports/figures/rule_baseline_comparison.png
  reports/tables/rule_baseline.csv
  reports/figures/calibration_curve.png
  reports/tables/calibration_metrics.csv
  reports/figures/ablation_topk.png
  reports/tables/ablation_results.csv

CLI:
    python -m tools.make_ds_supplement
    python -m tools.make_ds_supplement --skip-ablation
    python -m tools.make_ds_supplement --t 100
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from loguru import logger
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    f1_score,
    precision_score,
    recall_score,
)

from src.config import CHECKPOINTS, RANDOM_SEED, TABLES_DIR
from src.eda.plot_style import apply_style, savefig
from src.evaluation.make_split import load_checkpoint_split
from src.features.preprocessing import (
    NOMINAL_FEATURES,
    make_X_y,
    preprocess,
)
from src.modeling.predict import predict_checkpoint
from src.modeling.train import build_model, evaluate

# ── atomic write helpers ──────────────────────────────────────────────────────


def _write_csv(df: pd.DataFrame, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    df.to_csv(tmp, index=False)
    os.replace(tmp, path)
    logger.info(f"saved {path.name} ({len(df)} rows)")


# ═════════════════════════════════════════════════════════════════════════════
# 1. RULE-BASED BASELINE
# ═════════════════════════════════════════════════════════════════════════════

_DAYS_THRESHOLDS = [7, 14, 21, 28, 35, 42, 56]
_SCORE_THRESHOLDS = [0, 15, 25, 35, 45]


def _apply_rule(raw: pd.DataFrame, days_thr: float, score_thr: float) -> np.ndarray:
    """Flag at-risk if inactive > days_thr days OR cumulative score < score_thr.

    Missing days_since_last_activity (no VLE activity yet) is treated as the
    maximum possible inactivity (999 days), which is always above any threshold
    and therefore correctly flags the student as at-risk.
    Missing weighted_score_to_date (no submissions yet) is treated as 0.
    """
    days = raw["days_since_last_activity"].fillna(999.0)
    score = raw["weighted_score_to_date"].fillna(0.0)
    return ((days > days_thr) | (score < score_thr)).astype(int).to_numpy()


def _best_rule(raw: pd.DataFrame, y_true: np.ndarray) -> tuple[float, float, dict]:
    """Grid-search over threshold pairs; return the pair maximising F1."""
    best_f1, best_days, best_score = -1.0, 14.0, 35.0
    for d in _DAYS_THRESHOLDS:
        for s in _SCORE_THRESHOLDS:
            pred = _apply_rule(raw, d, s)
            f1 = f1_score(y_true, pred, zero_division=0)
            if f1 > best_f1:
                best_f1, best_days, best_score = f1, d, s
    pred = _apply_rule(raw, best_days, best_score)
    metrics = {
        "recall": round(float(recall_score(y_true, pred, zero_division=0)), 4),
        "precision": round(float(precision_score(y_true, pred, zero_division=0)), 4),
        "f1": round(float(best_f1), 4),
        "days_threshold": best_days,
        "score_threshold": best_score,
    }
    return best_days, best_score, metrics


def run_rule_baseline(checkpoints: tuple[int, ...] = CHECKPOINTS) -> pd.DataFrame:
    """Compare the best-threshold rule against XGBoost at each checkpoint."""
    logger.info("=== Rule-based baseline ===")
    rows = []
    for t in checkpoints:
        _, test_df = load_checkpoint_split(t)
        y_true = test_df["at_risk"].to_numpy()

        # XGBoost held-out recall (from saved model)
        try:
            xgb_out = predict_checkpoint("xgb", t)
            xgb_recall = round(
                float(recall_score(xgb_out["y_true"], xgb_out["pred"], zero_division=0)), 4
            )
            xgb_f1 = round(float(f1_score(xgb_out["y_true"], xgb_out["pred"], zero_division=0)), 4)
            xgb_precision = round(
                float(precision_score(xgb_out["y_true"], xgb_out["pred"], zero_division=0)), 4
            )
        except FileNotFoundError:
            logger.warning(f"XGBoost model not found at t={t}; skipping XGBoost columns")
            xgb_recall = xgb_f1 = xgb_precision = float("nan")

        # Best rule
        _, _, rule_m = _best_rule(test_df, y_true)

        rows.append(
            {
                "t_percent": t,
                "rule_recall": rule_m["recall"],
                "rule_precision": rule_m["precision"],
                "rule_f1": rule_m["f1"],
                "rule_days_threshold": rule_m["days_threshold"],
                "rule_score_threshold": rule_m["score_threshold"],
                "xgb_recall": xgb_recall,
                "xgb_f1": xgb_f1,
                "xgb_precision": xgb_precision,
                "recall_gap": round(xgb_recall - rule_m["recall"], 4)
                if not np.isnan(xgb_recall)
                else float("nan"),
            }
        )
        logger.info(
            f"t={t:3d}%: rule recall={rule_m['recall']:.4f} "
            f"(days>{rule_m['days_threshold']} OR score<{rule_m['score_threshold']}) "
            f"| xgb recall={xgb_recall}"
        )

    df = pd.DataFrame(rows)
    _write_csv(df, TABLES_DIR / "rule_baseline.csv")

    # Plot
    apply_style()
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    ax = axes[0]
    ts = df["t_percent"]
    ax.plot(ts, df["rule_recall"], marker="s", color="#E67E22", label="Rule baseline")
    if not df["xgb_recall"].isna().all():
        ax.plot(ts, df["xgb_recall"], marker="o", color="#2166AC", label="XGBoost")
    ax.axhline(0.80, ls="--", lw=1, color="dimgray", label="Criterion 0.80")
    ax.set_xticks(list(ts))
    ax.set_ylim(0.5, 1.02)
    ax.set_xlabel("Course progress (%)")
    ax.set_ylabel("At-risk recall")
    ax.set_title("Recall: XGBoost vs rule baseline")
    ax.legend(fontsize=9)

    ax = axes[1]
    if not df["recall_gap"].isna().all():
        colours = ["#2166AC" if v >= 0 else "#C0392B" for v in df["recall_gap"]]
        ax.bar(ts.astype(str), df["recall_gap"], color=colours, width=0.5)
        ax.axhline(0, color="#555555", lw=0.8)
        ax.set_xlabel("Course progress (%)")
        ax.set_ylabel("Recall gap (XGBoost minus rule)")
        ax.set_title("Added value of XGBoost over the rule")

    fig.suptitle("Rule-based baseline comparison", fontweight="bold", fontsize=13)
    plt.tight_layout()
    path = savefig(fig, "rule_baseline_comparison")
    plt.close(fig)
    logger.info(f"figure -> {path}")
    return df


# ═════════════════════════════════════════════════════════════════════════════
# 2. PROBABILITY CALIBRATION
# ═════════════════════════════════════════════════════════════════════════════

_N_BINS = 10


def _calibration_stats(y_true: np.ndarray, y_proba: np.ndarray, n_bins: int = _N_BINS) -> dict:
    """Compute reliability-diagram data and calibration error metrics.

    Returns fraction_of_positives, mean_predicted, bin_counts, ECE, MCE.
    ECE = weighted mean |gap|;  MCE = max |gap| across non-empty bins.
    """
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_ids = np.digitize(y_proba, bins[1:-1])  # 0 .. n_bins-1
    frac_pos, mean_pred, counts = [], [], []
    for b in range(n_bins):
        mask = bin_ids == b
        n = mask.sum()
        counts.append(int(n))
        if n == 0:
            frac_pos.append(float("nan"))
            mean_pred.append(float("nan"))
        else:
            frac_pos.append(float(y_true[mask].mean()))
            mean_pred.append(float(y_proba[mask].mean()))
    frac_pos = np.array(frac_pos)
    mean_pred = np.array(mean_pred)
    counts = np.array(counts)
    valid = ~np.isnan(frac_pos)
    gaps = np.abs(frac_pos[valid] - mean_pred[valid])
    ece = float(np.average(gaps, weights=counts[valid]))
    mce = float(gaps.max())
    return {
        "fraction_of_positives": frac_pos,
        "mean_predicted": mean_pred,
        "bin_counts": counts,
        "ece": round(ece, 4),
        "mce": round(mce, 4),
    }


def run_calibration(checkpoints: tuple[int, ...] = CHECKPOINTS) -> pd.DataFrame:
    """Plot calibration curves and compute ECE/MCE for XGBoost at each checkpoint."""
    logger.info("=== Calibration analysis ===")
    n = len(checkpoints)
    ncols = 3
    nrows = (n + ncols - 1) // ncols

    apply_style()
    fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 4.5 * nrows))
    axes = np.array(axes).flatten()

    summary_rows = []
    for i, t in enumerate(checkpoints):
        try:
            out = predict_checkpoint("xgb", t)
        except FileNotFoundError:
            logger.warning(f"XGBoost model not found at t={t}; skipping")
            continue
        y_true = (
            out["y_true"].to_numpy()
            if hasattr(out["y_true"], "to_numpy")
            else np.array(out["y_true"])
        )
        y_proba = (
            out["proba"].to_numpy()
            if hasattr(out["proba"], "to_numpy")
            else np.array(out["proba"])
        )

        stats = _calibration_stats(y_true, y_proba)
        summary_rows.append({"t_percent": t, "ece": stats["ece"], "mce": stats["mce"]})
        logger.info(f"t={t:3d}%: ECE={stats['ece']:.4f}  MCE={stats['mce']:.4f}")

        ax = axes[i]
        valid = ~np.isnan(stats["fraction_of_positives"])
        mp = stats["mean_predicted"][valid]
        fp = stats["fraction_of_positives"][valid]
        ax.plot([0, 1], [0, 1], ls="--", color="#999999", lw=1, label="Perfect calibration")
        ax.plot(mp, fp, marker="o", color="#C0392B", lw=1.5, label="XGBoost")
        ax.fill_between(mp, mp, fp, alpha=0.12, color="#C0392B")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xlabel("Mean predicted probability")
        ax.set_ylabel("Fraction of positives")
        ax.set_title(f"t = {t}%  (ECE={stats['ece']:.3f})")
        ax.legend(fontsize=8)

    for j in range(i + 1, len(axes)):
        axes[j].set_visible(False)

    fig.suptitle(
        "Probability calibration: XGBoost (at-risk class)", fontweight="bold", fontsize=13
    )
    plt.tight_layout()
    path = savefig(fig, "calibration_curve")
    plt.close(fig)
    logger.info(f"figure -> {path}")

    df = pd.DataFrame(summary_rows)
    _write_csv(df, TABLES_DIR / "calibration_metrics.csv")
    return df


# ═════════════════════════════════════════════════════════════════════════════
# 3. FEATURE ABLATION  (top-k raw features, XGBoost at t=100%)
# ═════════════════════════════════════════════════════════════════════════════

_ABLATION_KS = [3, 5, 7, 10, 15, 20]  # plus "all" (28 raw)
_ABLATION_T = 100


def _shap_name_to_raw(shap_name: str) -> str:
    """Map a post-preprocessing SHAP feature name to the raw feature name.

    ColumnTransformer with verbose_feature_names_out=True produces names like:
      num__days_since_last_activity     -> days_since_last_activity
      ordinal__highest_education        -> highest_education
      nominal__code_module_DDD          -> code_module   (one-hot variant)
      binary__gender                    -> gender
      indicator__not_submitted          -> not_submitted
    """
    if "__" not in shap_name:
        return shap_name
    prefix, rest = shap_name.split("__", 1)
    if prefix == "nominal":
        # rest looks like "code_module_DDD"; find which nominal feature it belongs to
        for col in NOMINAL_FEATURES:
            if rest.startswith(col):
                return col
        return rest
    return rest  # num, ordinal, binary, indicator: rest IS the raw name


def _ranked_raw_features(shap_csv: Path) -> list[str]:
    """Return raw feature names ranked by max |SHAP| across their variants."""
    imp = pd.read_csv(shap_csv)
    imp["raw_feature"] = imp["feature"].map(_shap_name_to_raw)
    ranked = (
        imp.groupby("raw_feature")["importance"].max().sort_values(ascending=False).index.tolist()
    )
    return ranked


def _feat_indices_for_raw(feat_names: list[str], raw_subset: list[str]) -> list[int]:
    """Return column indices in the preprocessed matrix matching raw_subset."""
    raw_set = set(raw_subset)
    return [i for i, fn in enumerate(feat_names) if _shap_name_to_raw(fn) in raw_set]


def run_ablation(shap_csv: Path | None = None) -> pd.DataFrame:
    """Retrain XGBoost with top-k features; report metrics vs k."""
    if shap_csv is None:
        shap_csv = TABLES_DIR / "xai_shap_importance.csv"
    if not Path(shap_csv).exists():
        logger.warning(f"SHAP importance CSV not found: {shap_csv}; skipping ablation")
        return pd.DataFrame()

    logger.info("=== Feature ablation (t=100%) ===")
    ranked = _ranked_raw_features(shap_csv)
    total = len(ranked)
    logger.info(f"Ranked {total} raw features from {shap_csv.name}")

    train_df, test_df = load_checkpoint_split(_ABLATION_T)
    X_train, y_train = make_X_y(train_df)
    X_test, y_test = make_X_y(test_df)
    Xtr, Xte, ct, feat_names, stats = preprocess(
        X_train, X_test, scaler_save_path=None, return_stats=True
    )

    from imblearn.over_sampling import SMOTE  # local import: optional dependency

    rows = []
    ks = sorted(set(_ABLATION_KS + [total]))  # add "all features" as the final point
    for k in ks:
        top_raw = ranked[:k]
        idx = _feat_indices_for_raw(feat_names, top_raw)
        if not idx:
            logger.warning(f"k={k}: no feature indices found; skipping")
            continue

        Xtr_sub = Xtr[:, idx]
        Xte_sub = Xte[:, idx]

        Xtr_res, y_res = SMOTE(random_state=RANDOM_SEED).fit_resample(Xtr_sub, y_train)
        model = build_model("xgb", RANDOM_SEED).fit(Xtr_res, y_res)
        m = evaluate(model, Xte_sub, y_test)

        rows.append(
            {
                "k": k,
                "top_features": ", ".join(top_raw),
                "recall": m["recall"],
                "f1": m["f1"],
                "pr_auc": m["pr_auc"],
                "roc_auc": m["roc_auc"],
            }
        )
        logger.info(
            f"k={k:2d}: recall={m['recall']:.4f}  f1={m['f1']:.4f}  " f"pr_auc={m['pr_auc']:.4f}"
        )

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    _write_csv(df, TABLES_DIR / "ablation_results.csv")

    apply_style()
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(df["k"], df["recall"], marker="o", color="#C0392B", label="Recall")
    ax.plot(df["k"], df["f1"], marker="s", color="#2166AC", label="F1")
    ax.plot(df["k"], df["pr_auc"], marker="^", color="#27AE60", label="PR-AUC")
    ax.axhline(0.80, ls="--", lw=1, color="dimgray", alpha=0.7, label="Criterion 0.80")
    ax.set_xlabel("Number of raw features (k)")
    ax.set_ylabel("Score")
    ax.set_title(f"XGBoost performance vs number of features (t={_ABLATION_T}%)")
    ax.set_xticks(df["k"].tolist())
    ax.set_ylim(0.5, 1.02)
    ax.legend(fontsize=9)
    path = savefig(fig, "ablation_topk")
    plt.close(fig)
    logger.info(f"figure -> {path}")
    return df


# ═════════════════════════════════════════════════════════════════════════════
# CLI
# ═════════════════════════════════════════════════════════════════════════════


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run the three DS-supplement analyses.")
    p.add_argument(
        "--t",
        type=int,
        choices=list(CHECKPOINTS),
        default=None,
        help="limit rule baseline and calibration to this checkpoint (default: all six)",
    )
    p.add_argument(
        "--skip-ablation",
        action="store_true",
        help="skip the ablation step (useful when models/xai output is unavailable)",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    checkpoints = (args.t,) if args.t is not None else CHECKPOINTS

    run_rule_baseline(checkpoints)
    run_calibration(checkpoints)
    if not args.skip_ablation:
        run_ablation()
    else:
        logger.info("Ablation skipped (--skip-ablation)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
