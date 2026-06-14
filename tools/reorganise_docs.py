"""One-time: reorganise docs/ into a scientific structure mapped to Task 3.

Folders follow the five Task-3 deliverable categories plus supporting material:
  01_data_specification, 02_collection, 03_cleaning, 04_transformation,
  05_splitting, 06_references, 07_standards, 08_agreements (signed PDFs).

Moves preserve git history (git mv for tracked files). Run once:
    python tools/reorganise_docs.py
"""

import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

TRACKED = set(
    subprocess.run(
        ["git", "ls-files", "docs/"], cwd=ROOT, capture_output=True, text=True
    ).stdout.split()
)

FOLDERS = [
    "01_data_specification",
    "02_collection",
    "03_cleaning",
    "04_transformation",
    "05_splitting",
    "06_references",
    "07_standards",
    "08_agreements",
]

# (old base relative to docs/, new path relative to docs/) — bilingual .md + .docx.
BILINGUAL = [
    (
        "01_TargetVariable_Definition",
        "01_data_specification/Target_Variable_Definition",
    ),
    ("DataDictionary", "01_data_specification/Data_Dictionary"),  # _EN/_VI variants
    (
        "Data_Specification",
        "01_data_specification/Data_Specification",
    ),  # .md only (new)
    ("03_DataCollection_Methods", "02_collection/Data_Collection_Methods"),
    ("Cleaning_Methods", "03_cleaning/Cleaning_Methods"),  # .md only (new)
    ("02_LeakagePrevention_Rules", "03_cleaning/Leakage_Prevention_Rules"),
    (
        "Transformation_Standardisation",
        "04_transformation/Transformation_Standardisation",
    ),  # .md only (new)
    ("07_Preprocessing_Sequence", "04_transformation/Preprocessing_Sequence"),
    ("09_Feature_Naming_Convention", "04_transformation/Feature_Naming_Convention"),
    ("06_SplitStrategy_Analysis", "05_splitting/Split_Strategy_Analysis"),
    (
        "04_BaseStudies_Preprocessing_Comparison",
        "06_references/Base_Studies_Comparison",
    ),
    ("05_Method_Justification", "06_references/Method_Justification"),
    ("08_Chart_Standards", "07_standards/Chart_Standards"),
    ("10_Reproducibility", "07_standards/Reproducibility"),
]

# Single files (src rel docs/, dst rel docs/).
SINGLES = [
    ("DataSource_License_Ethics.md", "02_collection/Data_Source_License_Ethics_EN.md"),
    (
        "DataSource_License_Ethics.docx",
        "02_collection/Data_Source_License_Ethics_EN.docx",
    ),
    (
        "DataSource_License_Ethics_VI.md",
        "02_collection/Data_Source_License_Ethics_VI.md",
    ),
    (
        "DataSource_License_Ethics_VI.docx",
        "02_collection/Data_Source_License_Ethics_VI.docx",
    ),
    ("variable_typing.xlsx", "01_data_specification/Variable_Typing.xlsx"),
    ("BienBan_Buoc0_Nhom1_1.pdf", "08_agreements/Step0_Agreement_Nhom1.pdf"),
    (
        "QuyTac_PhongTranhRoRi_STT12_Nhom1.pdf",
        "08_agreements/Leakage_Rules_Signed_Nhom1.pdf",
    ),
]

REMOVE = [
    "00_Deliverables_Index_EN.md",
    "00_Deliverables_Index_EN.docx",
    "00_Deliverables_Index_VI.md",
    "00_Deliverables_Index_VI.docx",
    "DataDictionary.md",
    "DataDictionary.xlsx",  # incomplete; superseded by Data_Dictionary_{EN,VI}
]


def move(src_rel: str, dst_rel: str) -> None:
    src, dst = DOCS / src_rel, DOCS / dst_rel
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if f"docs/{src_rel}" in TRACKED:
        subprocess.run(["git", "mv", "-f", str(src), str(dst)], cwd=ROOT, check=True)
    else:
        shutil.move(str(src), str(dst))
    print("moved", src_rel, "->", dst_rel)


def main() -> None:
    for f in FOLDERS:
        (DOCS / f).mkdir(parents=True, exist_ok=True)
    for old, new in BILINGUAL:
        for lang in ("_EN", "_VI"):
            for ext in (".md", ".docx"):
                move(f"{old}{lang}{ext}", f"{new}{lang}{ext}")
    for src, dst in SINGLES:
        move(src, dst)
    for f in REMOVE:
        p = DOCS / f
        if f"docs/{f}" in TRACKED:
            subprocess.run(["git", "rm", "-f", str(p)], cwd=ROOT, check=True)
        elif p.exists():
            os.remove(p)
        print("removed", f)
    print("done")


if __name__ == "__main__":
    main()
