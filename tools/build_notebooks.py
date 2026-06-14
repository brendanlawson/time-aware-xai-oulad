"""Generate the two deliverable notebooks from the tested src/ modules.

Keeping the notebooks thin (they call src.* functions) means the notebook and the
committed code/figures never drift. Run:  python tools/build_notebooks.py
Then execute to verify:  jupyter nbconvert --to notebook --execute <nb>
"""

from pathlib import Path

import nbformat as nbf
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

NB_DIR = Path(__file__).resolve().parents[1] / "notebooks"

BOOT = (
    "import sys\n"
    "from pathlib import Path\n"
    "ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()\n"
    "sys.path.insert(0, str(ROOT))\n"
)

# --- Notebook 01: build master table -----------------------------------------
nb01 = new_notebook()
nb01.cells = [
    new_markdown_cell(
        "# 01 · Build Master Table (reproducible)\n\n"
        "**DSP391m – Group 1 · Report 2 (Data Tasks) · STT 4, 6 (Phuc)**\n\n"
        "Thin orchestrator over `src.data.build_master_table`. *Restart & Run All* rebuilds the master "
        "table (one row per student–module–presentation) with the fixed `at_risk` label, a join log "
        "proving no duplication/loss, and a cleaning log."
    ),
    new_code_cell(
        BOOT
        + "import pandas as pd\nfrom src.data.build_master_table import build_master\nfrom src.data.io_utils import INTERIM_DIR"
    ),
    new_markdown_cell(
        "## 1. Build (uses cached engagement_agg if present; pass rebuild_engagement=True to rebuild from studentVle)"
    ),
    new_code_cell("master = build_master(rebuild_engagement=False)\nmaster.shape"),
    new_markdown_cell(
        "## 2. Join log — every left-join preserves the row count (no duplication / loss)"
    ),
    new_code_cell("pd.read_csv(INTERIM_DIR / 'master_join_log.csv')"),
    new_markdown_cell(
        "## 3. Cleaning log — duplicate keys removed and categorical cardinalities"
    ),
    new_code_cell("pd.read_csv(INTERIM_DIR / 'master_cleaning_log.csv')"),
    new_markdown_cell("## 4. Target balance and a preview"),
    new_code_cell(
        "print('rows:', len(master), '| cols:', master.shape[1])\n"
        "print('at_risk rate: {:.1%}'.format(master['at_risk'].mean()))\n"
        "print('duplicate keys:', master.duplicated(['code_module','code_presentation','id_student']).sum())\n"
        "master.head(3)"
    ),
    new_markdown_cell("## 5. Reproducibility checks"),
    new_code_cell(
        "assert len(master) == 32593\n"
        "assert master.duplicated(['code_module','code_presentation','id_student']).sum() == 0\n"
        "print('OK: 32,593 rows, no duplicate keys, at_risk fixed from final_result')"
    ),
]

# --- Notebook 02: EDA --------------------------------------------------------
nb02 = new_notebook()
nb02.cells = [
    new_markdown_cell(
        "# 02 · Exploratory Data Analysis (Chapter 4)\n\n"
        "**DSP391m – Group 1 · Report 2 (Data Tasks) · STT 27, 28, 35–38**\n\n"
        "Thin orchestrator over `src.eda.eda`. Each section runs one analysis, prints its findings and "
        "displays the figure saved under `reports/figures/`. Charts follow the team chart standard "
        "(`docs/08_Chart_Standards`)."
    ),
    new_code_cell(
        BOOT
        + "import json\nfrom IPython.display import Image, display\nfrom src.eda import eda\nfrom src.eda.plot_style import FIGURES_DIR\n"
        "master = eda.load_master()\ncheckpoints = eda.load_checkpoints()\nmaster.shape"
    ),
    new_markdown_cell("## 1. Class distribution & imbalance (STT 27)"),
    new_code_cell(
        "print(json.dumps(eda.class_distribution(master), indent=2))\ndisplay(Image(filename=str(FIGURES_DIR / 'dist_class_distribution.png')))"
    ),
    new_markdown_cell("## 2. Descriptive statistics (STT 28)"),
    new_code_cell(
        "print(json.dumps(eda.descriptive_stats(master), indent=2, ensure_ascii=False))\nmaster[eda.NUMERIC_MAIN].describe().T"
    ),
    new_markdown_cell("## 3. Distributions — histogram/KDE and boxplots (STT 35)"),
    new_code_cell(
        "eda.distribution_plots(master)\ndisplay(Image(filename=str(FIGURES_DIR / 'dist_numeric_hist_kde.png')))\ndisplay(Image(filename=str(FIGURES_DIR / 'dist_numeric_boxplots.png')))"
    ),
    new_markdown_cell(
        "## 4. Bivariate analysis vs target — discriminative features (STT 36)"
    ),
    new_code_cell(
        "print(json.dumps(eda.bivariate_analysis(master), indent=2))\ndisplay(Image(filename=str(FIGURES_DIR / 'bivar_numeric_by_label.png')))\ndisplay(Image(filename=str(FIGURES_DIR / 'bivar_atrisk_rate_by_category.png')))"
    ),
    new_markdown_cell("## 5. Correlation — Pearson, Spearman, leakage check (STT 37)"),
    new_code_cell(
        "print(json.dumps(eda.correlation_analysis(master), indent=2))\ndisplay(Image(filename=str(FIGURES_DIR / 'corr_pearson.png')))\ndisplay(Image(filename=str(FIGURES_DIR / 'corr_spearman.png')))"
    ),
    new_markdown_cell("## 6. Time-aware EDA across checkpoints (STT 38)"),
    new_code_cell(
        "print(json.dumps(eda.time_trends(checkpoints), indent=2))\ndisplay(Image(filename=str(FIGURES_DIR / 'time_trends_by_label.png')))"
    ),
]

for name, nb in [("01_build_master_table.ipynb", nb01), ("02_eda.ipynb", nb02)]:
    path = NB_DIR / name
    nbf.write(nb, path)
    print("wrote", path)
