"""Convert the bilingual Markdown deliverables to .docx via pandoc.

Every report-document deliverable is authored in Markdown (English `_EN`, Vietnamese
`_VI`) and converted here, so the .md and .docx versions never drift. Images are
resolved relative to each file's directory.

Requires pandoc on PATH.  Run:  python tools/build_docx.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

targets = (
    sorted(ROOT.glob("docs/*_EN.md"))
    + sorted(ROOT.glob("docs/*_VI.md"))
    + sorted(ROOT.glob("reports/Report2_DataTasks_*.md"))
)

failed = 0
for md in targets:
    docx = md.with_suffix(".docx")
    try:
        subprocess.run(
            [
                "pandoc",
                str(md),
                "-o",
                str(docx),
                "--resource-path",
                str(md.parent),
                "--toc",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        print("wrote", docx.relative_to(ROOT))
    except subprocess.CalledProcessError as e:
        failed += 1
        print("FAILED", md.name, e.stderr[:300])

print(f"\n{len(targets) - failed}/{len(targets)} converted")
sys.exit(1 if failed else 0)
