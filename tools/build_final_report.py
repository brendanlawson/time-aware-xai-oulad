"""Assemble the final report: stitch the section drafts, inject live numbers.

Prose lives in ``reports/final_report/{1..8}_*_EN.md``. Volatile numbers are
NEVER hand-typed there — sections use placeholders that this builder resolves
from the committed result CSVs at build time, so a renumber run automatically
propagates into the report:

    {{VAL:key}}            -> scalar from a CSV (see SCALARS registry)
    {{TBL:key}}            -> markdown table rendered from a CSV (TABLES registry)
    {{FIG:name|Caption}}   -> embedded reports/figures/<name>.png with caption

Outputs:
    reports/final_report/Final_Report_DSP391m_Group1_EN.md    (stitched source)
    reports/final_report/Final_Report_DSP391m_Group1_EN.docx  (pandoc, with TOC)

Run:
    python -m tools.build_final_report
    python -m tools.build_final_report --tables-dir <dir>   # test against a snapshot
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "final_report"
FIGURES_DIR = ROOT / "reports" / "figures"
OUT_MD = REPORT_DIR / "Final_Report_DSP391m_Group1_EN.md"
OUT_DOCX = OUT_MD.with_suffix(".docx")

SECTION_GLOB = sorted(REPORT_DIR.glob("[1-8]_*_EN.md"))


def _fmt(x, nd=3):
    return f"{float(x):.{nd}f}"


def load_scalars(tab: Path) -> dict:
    """Every {{VAL:...}} key, computed from the result CSVs."""
    mm = pd.read_csv(tab / "model_metrics.csv").set_index(["model", "t_percent"])
    cv = pd.read_csv(tab / "cv_summary.csv").set_index(["model", "t_percent"])
    sa = pd.read_csv(tab / "sensitivity_active_xgb.csv").set_index("t_percent")
    tv = pd.read_csv(tab / "threshold_validation.csv").set_index("policy")
    sl = pd.read_csv(tab / "xai_shap_vs_lime.csv").iloc[0]
    ss = pd.read_csv(tab / "xai_stability_seeds.csv").iloc[0]
    fg = pd.read_csv(tab / "fairness_gaps.csv")
    imb = pd.read_csv(tab / "imbalance_comparison.csv")
    spread = imb.groupby("model")[["recall", "f1", "pr_auc"]].agg(lambda s: s.max() - s.min())
    r90 = next(p for p in tv.index if p.startswith("recall>="))
    return {
        "XGB_T100_RECALL": _fmt(mm.loc[("xgb", 100), "recall"]),
        "XGB_T100_PRAUC": _fmt(mm.loc[("xgb", 100), "pr_auc"]),
        "XGB_T40_RECALL": _fmt(mm.loc[("xgb", 40), "recall"]),
        "CV_XGB_RECALL": f"{_fmt(cv.loc[('xgb', 100), 'recall_mean'], 4)} ± "
        f"{_fmt(cv.loc[('xgb', 100), 'recall_std'], 4)}",
        "ACTIVE_T40_RECALL": _fmt(sa.loc[40, "active_recall"]),
        "ACTIVE_T80_RECALL": _fmt(sa.loc[80, "active_recall"]),
        "ACTIVE_T100_RECALL": _fmt(sa.loc[100, "active_recall"]),
        "GONE_T10_TEST": f"{int(sa.loc[10, 'withdrawn_already_gone']):,}",
        "THR_F1": _fmt(tv.loc["f1", "threshold"], 2),
        "THR_R90": _fmt(tv.loc[r90, "threshold"], 2),
        "THR_R90_TEST_PRECISION": _fmt(tv.loc[r90, "test_precision"]),
        "SHAPLIME_JACCARD": _fmt(sl["jaccard"], 2),
        "SEED_JACCARD": _fmt(ss["mean_jaccard"], 2),
        "SEED_SPEARMAN": _fmt(ss["mean_spearman"], 2),
        "FAIR_MAX_GAP_PP": _fmt(fg["recall_gap"].max() * 100, 1),
        "FAIR_MAX_GAP_ATTR": fg.sort_values("recall_gap", ascending=False).iloc[0]["attribute"],
        "IMB_MAX_SPREAD": _fmt(spread.max().max(), 4),
    }


def load_tables(tab: Path) -> dict:
    """Every {{TBL:...}} key -> (DataFrame, float-format ndigits)."""
    mm = pd.read_csv(tab / "model_metrics.csv")
    cv = pd.read_csv(tab / "cv_summary.csv")
    sa = pd.read_csv(tab / "sensitivity_active_xgb.csv")
    return {
        "benchmark_t100": mm[mm.t_percent == 100].drop(columns="t_percent"),
        "time_aware_best": pd.read_csv(tab / "time_aware_best.csv"),
        "cv_summary": cv[
            [
                "model",
                "recall_mean",
                "recall_std",
                "f1_mean",
                "f1_std",
                "pr_auc_mean",
                "pr_auc_std",
            ]
        ],
        "friedman": pd.read_csv(tab / "model_friedman.csv").drop(columns=["t_percent"]),
        "dual_cohort": sa[
            [
                "t_percent",
                "full_recall",
                "active_recall",
                "full_pr_auc",
                "active_pr_auc",
                "withdrawn_already_gone",
            ]
        ],
        "imbalance_xgb": pd.read_csv(tab / "imbalance_comparison.csv")
        .query("model == 'xgb'")
        .drop(columns="model"),
        "threshold_validation": pd.read_csv(tab / "threshold_validation.csv").drop(
            columns=["model", "t_percent"]
        ),
        "xai_strategies": pd.read_csv(tab / "xai_stability_strategies.csv"),
        "fairness_gaps": pd.read_csv(tab / "fairness_gaps.csv"),
        "tuning": pd.read_csv(tab / "tuning_results.csv").drop(columns="best_params"),
    }


def render(text: str, scalars: dict, tables: dict) -> str:
    def val(m):
        return scalars[m.group(1)]

    def tbl(m):
        df = tables[m.group(1)]
        return df.to_markdown(index=False, floatfmt=".4f")

    def fig(m):
        name, caption = m.group(1), m.group(2)
        path = FIGURES_DIR / f"{name}.png"
        if not path.exists():
            raise FileNotFoundError(path)
        return f"![{caption}]({path.as_posix()})"

    text = re.sub(r"\{\{VAL:([A-Z0-9_]+)\}\}", val, text)
    text = re.sub(r"\{\{TBL:([a-z0-9_]+)\}\}", tbl, text)
    text = re.sub(r"\{\{FIG:([a-z0-9_]+)\|([^}]+)\}\}", fig, text)
    leftovers = re.findall(r"\{\{[A-Z]+:[^}]+\}\}", text)
    if leftovers:
        raise KeyError(f"unresolved placeholders: {leftovers}")
    return text


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tables-dir", default=str(ROOT / "reports" / "tables"))
    ap.add_argument("--skip-docx", action="store_true")
    args = ap.parse_args(argv)
    tab = Path(args.tables_dir)

    scalars, tables = load_scalars(tab), load_tables(tab)
    if not SECTION_GLOB:
        sys.exit("no section files found under reports/final_report/")
    parts = [
        "% Time-Aware Explainable Machine Learning for Early At-Risk Student "
        "Prediction on OULAD\n% DSP391m — Group 1, FPT University · "
        "Supervisor: Nguyễn Thị Hoàng Yến\n"
    ]
    parts.append(
        "## Team Members\n\n"
        "Group 1, DSP391m - FPT University. Supervisor: Nguyễn Thị Hoàng Yến.\n\n"
        "| Member | Role | Responsibility |\n|---|---|---|\n"
        "| Khoa | Methodology Lead & Report Coordinator | Time-aware prediction (RQ1), evaluation, report assembly |\n"
        "| Đức | Modeling Lead | Model development, class-imbalance handling (RQ3) |\n"
        "| Bình | XAI Lead | SHAP/LIME explanations, explanation stability (RQ2) |\n"
        "| Phúc | Implementation Lead | Data pipeline, split harness, leakage tests |\n"
        "| An | Backend & Dashboard Lead | Model packaging, Streamlit dashboard |\n"
        "| Sơn | Literature Review Lead | Introduction, literature review, references |\n"
    )
    for f in SECTION_GLOB:
        print("section:", f.name)
        parts.append(render(f.read_text(encoding="utf-8"), scalars, tables))
    OUT_MD.write_text("\n\n---\n\n".join(parts), encoding="utf-8", newline="")
    print("wrote", OUT_MD.relative_to(ROOT))

    if not args.skip_docx:
        subprocess.run(
            [
                "pandoc",
                str(OUT_MD),
                "-o",
                str(OUT_DOCX),
                "--toc",
                "--number-sections=false",
                "--resource-path",
                str(FIGURES_DIR),
            ],
            check=True,
        )
        print("wrote", OUT_DOCX.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
