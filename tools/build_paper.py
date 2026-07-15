"""Render and compile the empirical paper from its placeholder template.

``paper/main.tex.in`` holds the prose; every volatile number is a placeholder
resolved from the committed result CSVs at build time (same contract as
``tools/build_final_report.py``, which this module reuses):

    {{VAL:KEY}}        -> scalar (report registry + bootstrap-CI + Jaccard-null keys)
    {{TEX:key}}        -> booktabs tabular, wrapped in \\resizebox{\\columnwidth}
    {{FIG:name|Cap}}   -> figure environment over reports/figures/<name>.png

Outputs:
    paper/main.tex   (rendered source, committed)
    paper/main.pdf   (compiled with Tectonic/XeTeX)

Run:
    python -m tools.build_paper
    python -m tools.build_paper --skip-pdf
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import shutil
import subprocess

import pandas as pd
from tools.build_final_report import load_scalars, load_tables

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "reports" / "tables"
PAPER_DIR = ROOT / "paper"
IN_TEX = PAPER_DIR / "main.tex.in"
OUT_TEX = PAPER_DIR / "main.tex"

TECTONIC_CANDIDATES = (
    "tectonic",
    r"C:\Users\phank\anaconda3\envs\tex\Library\bin\tectonic.exe",
)


def esc_tex(s: str) -> str:
    for a, b in (("&", r"\&"), ("%", r"\%"), ("_", r"\_"), ("#", r"\#"), (">=", r"$\geq$")):
        s = s.replace(a, b)
    return s


def _ci(point, lo, hi, nd=3) -> str:
    return f"{point:.{nd}f} (95\\% CI [{lo:.{nd}f}, {hi:.{nd}f}])"


def paper_scalars() -> dict:
    """Report registry + bootstrap-CI + Jaccard-null keys (LaTeX-safe strings)."""
    s = load_scalars(TAB)
    # LaTeX-safety for inherited report scalars: raw feature names carry
    # underscores, and the CV string uses a Unicode plus-minus.
    s["FAIR_MAX_GAP_ATTR"] = esc_tex(s["FAIR_MAX_GAP_ATTR"])
    s["CV_XGB_RECALL"] = s["CV_XGB_RECALL"].replace("±", r"$\pm$")
    ci = pd.read_csv(TAB / "bootstrap_ci.csv").set_index(["t_percent", "cohort", "metric"])

    def row(t, cohort, metric):
        r = ci.loc[(t, cohort, metric)]
        return _ci(r["point"], r["ci_lo"], r["ci_hi"])

    s.update(
        {
            "CI_RECALL_FULL_T40": row(40, "full", "recall"),
            "CI_RECALL_FULL_T100": row(100, "full", "recall"),
            "CI_RECALL_ACTIVE_T40": row(40, "active", "recall"),
            "CI_RECALL_ACTIVE_T100": row(100, "active", "recall"),
            "CI_GAP_T40": row(40, "gap", "recall"),
            "CI_GAP_T100": row(100, "gap", "recall"),
            "CI_PRAUC_FULL_T100": row(100, "full", "pr_auc"),
        }
    )
    jb = pd.read_csv(TAB / "xai_jaccard_baseline.csv").iloc[0]
    s.update(
        {
            "JB_MEAN": f"{jb['mean']:.3f}",
            "JB_P95": f"{jb['p95']:.2f}",
            "JB_P99": f"{jb['p99']:.3f}",
        }
    )
    return s


def paper_tables() -> dict:
    """TEX-table registry: the report tables plus the dual-cohort-with-CI table."""
    t = load_tables(TAB)
    ci = pd.read_csv(TAB / "bootstrap_ci.csv")
    rec = ci[ci.metric == "recall"].pivot(
        index="t_percent", columns="cohort", values=["point", "ci_lo", "ci_hi"]
    )
    rows = []
    for tp in sorted(set(ci.t_percent)):
        r = {"t (%)": int(tp)}
        for cohort, label in (
            ("full", "Full cohort"),
            ("active", "Still-enrolled"),
            ("gap", "Gap"),
        ):
            r[label] = _ci(
                rec.loc[tp, ("point", cohort)],
                rec.loc[tp, ("ci_lo", cohort)],
                rec.loc[tp, ("ci_hi", cohort)],
            )
        rows.append(r)
    t["dual_cohort_ci"] = pd.DataFrame(rows)
    return t


def latex_table(df: pd.DataFrame, nd=4) -> str:
    def fmt(v):
        if isinstance(v, float):
            return f"{v:.{nd}f}"
        return esc_tex(str(v))

    colspec = "l" + "c" * (len(df.columns) - 1)
    head = " & ".join(rf"\textbf{{{esc_tex(str(c))}}}" for c in df.columns) + r" \\"
    body = "\n".join(
        " & ".join(fmt(v) for v in row) + r" \\" for row in df.itertuples(index=False)
    )
    return (
        # \linewidth = \columnwidth in `table`, \textwidth in `table*` — fits both.
        "\\resizebox{\\linewidth}{!}{%\n"
        f"\\begin{{tabular}}{{{colspec}}}\n\\toprule\n{head}\n\\midrule\n{body}\n"
        "\\bottomrule\n\\end{tabular}}"
    )


def render(text: str, scalars: dict, tables: dict) -> str:
    text = re.sub(r"\{\{VAL:([A-Z0-9_]+)\}\}", lambda m: scalars[m.group(1)], text)
    text = re.sub(r"\{\{TEX:([a-z0-9_]+)\}\}", lambda m: latex_table(tables[m.group(1)]), text)

    def fig(m):
        name, caption = m.group(1), m.group(2)
        path = ROOT / "reports" / "figures" / f"{name}.png"
        if not path.exists():
            raise FileNotFoundError(path)
        return (
            "\\begin{figure}[t]\n\\centering\n"
            f"\\includegraphics[width=\\columnwidth]{{../reports/figures/{name}.png}}\n"
            f"\\caption{{{caption}}}\n\\label{{fig:{name}}}\n\\end{{figure}}"
        )

    text = re.sub(r"\{\{FIG:([a-z0-9_]+)\|([^}]+)\}\}", fig, text)
    leftovers = re.findall(r"\{\{[A-Z]+:[^}]+\}\}", text)
    if leftovers:
        raise KeyError(f"unresolved placeholders: {leftovers}")
    return text


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skip-pdf", action="store_true")
    args = ap.parse_args(argv)

    OUT_TEX.write_text(
        render(IN_TEX.read_text(encoding="utf-8"), paper_scalars(), paper_tables()),
        encoding="utf-8",
        newline="\n",
    )
    print("wrote", OUT_TEX.relative_to(ROOT))
    if not args.skip_pdf:
        exe = next((c for c in TECTONIC_CANDIDATES if shutil.which(c) or Path(c).exists()), None)
        if exe is None:
            raise FileNotFoundError("tectonic not found; use --skip-pdf")
        subprocess.run([exe, OUT_TEX.name], cwd=PAPER_DIR, check=True)
        pdf = OUT_TEX.with_suffix(".pdf")
        print("wrote", pdf.relative_to(ROOT), f"({pdf.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
