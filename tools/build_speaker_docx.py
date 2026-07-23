"""Build the unified Task-3 speaker script Word .docx (via pandoc).

Source of truth is a single hand-authored markdown file that maps 1:1 to the
33 numbered content slides of ``reports/Task3_Presentation.pptx`` (correct
presenter order: An · Sơn · Phúc · Bình · Đức · Khoa), with three deep-dive
call-outs and a Q&A appendix.

Output: reports/Task3_Speaker_Script_Merged.docx   (requires pandoc on PATH)

    python tools/build_speaker_docx.py
"""

from __future__ import annotations

from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_MD = ROOT / "reports" / "Task3_Speaker_Script_Merged.md"
OUT = ROOT / "reports" / "Task3_Speaker_Script_Merged.docx"
PANDOC = "pandoc"  # resolved from PATH, like build_docx.py / build_final_report.py


def main() -> int:
    if not SCRIPT_MD.exists():
        raise SystemExit(f"missing source script: {SCRIPT_MD}")
    subprocess.run(
        [
            PANDOC,
            str(SCRIPT_MD),
            "-o",
            str(OUT),
            "--from",
            "markdown+pipe_tables",
            "--toc",
            "--toc-depth=2",
            "-V",
            "lang=vi",
        ],
        check=True,
    )
    print("wrote", OUT, f"({OUT.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
