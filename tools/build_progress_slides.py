"""Build the current-progress presentation (.pptx) for the DSP391m project.

Generates ``reports/slides/Progress_Report.pptx`` (16:9) — a progress deck that
stops at the modeling block owned by Đức: the data pipeline (Phase 1, Phúc), the
five-model benchmark (Phase 2), and the class-imbalance strategy comparison
(Phase 4, RQ3). The remaining phases (3 time-aware RQ1, 5 XAI, 6 dashboard) are
listed as the next steps, not detailed here.

Reuses the house style of ``build_task3_slides.py`` and embeds the real figures
from ``reports/figures``. Speaker notes go into each slide.

    python tools/build_progress_slides.py
"""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

try:
    from PIL import Image

    def _img_size(path: Path) -> tuple[int, int]:
        with Image.open(path) as im:
            return im.size
except Exception:  # pragma: no cover - PIL optional

    def _img_size(path: Path) -> tuple[int, int]:
        return (1600, 900)


ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "reports" / "figures"
OUT = ROOT / "reports" / "slides" / "Progress_Report.pptx"

# ── Palette (same as the Task 3 deck) ───────────────────────────────────────
NAVY = RGBColor(0x0F, 0x2A, 0x4F)
ACCENT = RGBColor(0xE8, 0x72, 0x2B)
GREEN = RGBColor(0x1E, 0x8E, 0x4E)
BLUE = RGBColor(0x1F, 0x6F, 0xB2)
AMBER = RGBColor(0xB9, 0x7A, 0x0C)
DARK = RGBColor(0x26, 0x2B, 0x33)
GREY = RGBColor(0x5B, 0x63, 0x70)
LIGHT = RGBColor(0xF2, 0xF4, 0xF7)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

FONT = "Calibri"
SW, SH = Inches(13.333), Inches(7.5)
LABELS = {"do": ("Làm gì", GREEN), "why": ("Vì sao", BLUE), "out": ("Kết quả", AMBER)}

prs = Presentation()
prs.slide_width = SW
prs.slide_height = SH
BLANK = prs.slide_layouts[6]


def _set(run, size, color, bold=False, italic=False, font=FONT):
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.italic = italic
    run.font.name = font


def _box(slide, left, top, width, height):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Emu(0)
    tf.margin_top = tf.margin_bottom = Emu(0)
    return tb, tf


def _rect(slide, left, top, width, height, fill, line=None):
    from pptx.enum.shapes import MSO_SHAPE

    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
    shp.shadow.inherit = False
    return shp


def _footer(slide, n, presenter=""):
    _rect(slide, 0, 0, SW, Inches(0.16), NAVY)
    _rect(slide, 0, 0, Inches(3.2), Inches(0.16), ACCENT)
    _, tf = _box(slide, Inches(0.55), Inches(7.06), Inches(9.5), Inches(0.34))
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = "DSP391m · Nhóm 1 · Báo cáo tiến độ dự án"
    _set(r, 9, GREY)
    if presenter:
        r2 = p.add_run()
        r2.text = f"   ·   {presenter}"
        _set(r2, 9, ACCENT, bold=True)
    _, tf2 = _box(slide, Inches(12.2), Inches(7.06), Inches(0.9), Inches(0.34))
    tf2.paragraphs[0].alignment = PP_ALIGN.RIGHT
    rr = tf2.paragraphs[0].add_run()
    rr.text = str(n)
    _set(rr, 10, NAVY, bold=True)


def _notes(slide, text):
    if text:
        slide.notes_slide.notes_text_frame.text = text


def add_title(title, subtitle, meta, presenters):
    s = prs.slides.add_slide(BLANK)
    _rect(s, 0, 0, SW, SH, NAVY)
    _rect(s, 0, Inches(2.55), SW, Inches(0.07), ACCENT)
    _, tf = _box(s, Inches(0.9), Inches(2.7), Inches(11.5), Inches(2.2))
    r = tf.paragraphs[0].add_run()
    r.text = title
    _set(r, 33, WHITE, bold=True)
    p2 = tf.add_paragraph()
    r2 = p2.add_run()
    r2.text = subtitle
    _set(r2, 16, RGBColor(0xCF, 0xDC, 0xEC), italic=True)
    p2.space_before = Pt(10)
    _, tk = _box(s, Inches(0.9), Inches(1.5), Inches(11.0), Inches(0.7))
    rk = tk.paragraphs[0].add_run()
    rk.text = "BÁO CÁO TIẾN ĐỘ"
    _set(rk, 15, ACCENT, bold=True)
    _, tm = _box(s, Inches(0.9), Inches(5.3), Inches(11.5), Inches(1.7))
    for i, line in enumerate(meta):
        pp = tm.paragraphs[0] if i == 0 else tm.add_paragraph()
        rr = pp.add_run()
        rr.text = line
        _set(rr, 13, RGBColor(0xD7, 0xE0, 0xEC))
        pp.space_after = Pt(2)
    pp = tm.add_paragraph()
    rr = pp.add_run()
    rr.text = presenters
    _set(rr, 12.5, WHITE, bold=True)
    pp.space_before = Pt(6)


def _add_heading(s, kicker, title):
    _, tk = _box(s, Inches(0.55), Inches(0.32), Inches(12), Inches(0.4))
    rk = tk.paragraphs[0].add_run()
    rk.text = kicker
    _set(rk, 12, ACCENT, bold=True)
    _, tt = _box(s, Inches(0.55), Inches(0.66), Inches(12.2), Inches(0.95))
    rt = tt.paragraphs[0].add_run()
    rt.text = title
    _set(rt, 25, NAVY, bold=True)
    _rect(s, Inches(0.55), Inches(1.62), Inches(12.2), Inches(0.025), RGBColor(0xD8, 0xDF, 0xE8))


def _render_bullets(tf, items):
    first = True
    for it in items:
        kind = it[0]
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.space_after = Pt(7)
        p.line_spacing = 1.04
        if kind in LABELS:
            label, col = LABELS[kind]
            dot = p.add_run()
            dot.text = "● "
            _set(dot, 13, col, bold=True)
            lab = p.add_run()
            lab.text = f"{label}: "
            _set(lab, 14.5, col, bold=True)
            txt = p.add_run()
            txt.text = it[1]
            _set(txt, 14.5, DARK)
        elif kind == "p":
            dot = p.add_run()
            dot.text = "▪ "
            _set(dot, 12, NAVY, bold=True)
            txt = p.add_run()
            txt.text = it[1]
            _set(txt, 14.5, DARK)
        elif kind == "s":
            p.level = 1
            dot = p.add_run()
            dot.text = "– "
            _set(dot, 12, GREY)
            txt = p.add_run()
            txt.text = it[1]
            _set(txt, 12.5, GREY)
            p.space_after = Pt(4)
        elif kind == "key":
            bar = p.add_run()
            bar.text = "▶ Số liệu chốt:  "
            _set(bar, 13.5, ACCENT, bold=True)
            txt = p.add_run()
            txt.text = it[1]
            _set(txt, 13.5, NAVY, bold=True)
            p.space_before = Pt(6)
        elif kind == "note":
            txt = p.add_run()
            txt.text = it[1]
            _set(txt, 12, GREY, italic=True)
            p.space_before = Pt(4)


def _add_image(s, path: Path, left, top, max_w, max_h, caption=""):
    w, h = _img_size(path)
    ratio = min(max_w / w, max_h / h)
    iw, ih = int(w * ratio), int(h * ratio)
    pic_left = left + (max_w - iw) // 2
    s.shapes.add_picture(str(path), pic_left, top, width=Emu(iw), height=Emu(ih))
    if caption:
        _, tf = _box(s, left, top + Emu(ih) + Inches(0.05), Emu(max_w), Inches(0.4))
        tf.paragraphs[0].alignment = PP_ALIGN.CENTER
        r = tf.paragraphs[0].add_run()
        r.text = caption
        _set(r, 9.5, GREY, italic=True)


def _add_table(s, headers, rows, left, top, width, col_w=None, fontsize=11):
    nrows, ncols = len(rows) + 1, len(headers)
    height = Inches(0.36 * nrows)
    gtbl = s.shapes.add_table(nrows, ncols, left, top, width, height)
    tbl = gtbl.table
    if col_w:
        for i, cw in enumerate(col_w):
            tbl.columns[i].width = cw
    for j, htext in enumerate(headers):
        c = tbl.cell(0, j)
        c.fill.solid()
        c.fill.fore_color.rgb = NAVY
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
        c.margin_top = c.margin_bottom = Pt(2)
        r = c.text_frame.paragraphs[0].add_run()
        r.text = htext
        _set(r, fontsize, WHITE, bold=True)
    for i, row in enumerate(rows, start=1):
        for j, val in enumerate(row):
            c = tbl.cell(i, j)
            c.fill.solid()
            c.fill.fore_color.rgb = WHITE if i % 2 else LIGHT
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.margin_top = c.margin_bottom = Pt(1)
            r = c.text_frame.paragraphs[0].add_run()
            r.text = str(val)
            _set(r, fontsize, NAVY if j == 0 else DARK, bold=(j == 0))
    return gtbl


def add_content(
    n,
    kicker,
    title,
    items,
    notes="",
    presenter="",
    image=None,
    caption="",
    table=None,
    text_w=12.2,
):
    s = prs.slides.add_slide(BLANK)
    _footer(s, n, presenter)
    _add_heading(s, kicker, title)
    if image:
        text_w = 6.85
    _, tf = _box(s, Inches(0.6), Inches(1.85), Inches(text_w), Inches(5.0))
    tf.vertical_anchor = MSO_ANCHOR.TOP
    _render_bullets(tf, items)
    if image:
        _add_image(s, image, Inches(7.7), Inches(1.95), Inches(5.15), Inches(4.6), caption)
    if table:
        _add_table(
            s,
            table["headers"],
            table["rows"],
            Inches(table.get("left", 0.6)),
            Inches(table["top"]),
            Inches(table.get("width", 9.5)),
            col_w=table.get("col_w"),
            fontsize=table.get("fs", 11),
        )
    _notes(s, notes)
    return s


# ════════════════════════════════════════════════════════════════════════
# SLIDES  (báo cáo đến hết Phase 2 Benchmarking; phần sau = việc sắp tới)
# ════════════════════════════════════════════════════════════════════════

add_title(
    "Time-Aware Explainable ML — phát hiện sớm sinh viên nguy cơ (OULAD)",
    "Báo cáo tiến độ: Dữ liệu (Phase 1) → So tuyển mô hình (Phase 2 · Benchmarking)",
    [
        "DSP391m · Đồ án Khoa học Dữ liệu · Nhóm 1 · Đại học FPT",
        "GVHD: Nguyễn Thị Hoàng Yến  ·  Cập nhật: 02/07/2026",
    ],
    "Khối thực nghiệm: Phúc (Phase 1) · Đức (Phase 2)",
)

add_content(
    2,
    "TỔNG QUAN",
    "Phạm vi báo cáo & lộ trình",
    [
        (
            "note",
            "Báo cáo trình bày đến hết Phase 2 (so tuyển mô hình); phần còn lại là việc sắp tới.",
        ),
    ],
    notes="Báo cáo tiến độ lần này trình bày đến hết Phase 2 — so tuyển năm thuật toán ứng viên ở mốc "
    "100%, đứng trên nền pipeline dữ liệu Phase 1 của Phúc. Toàn bộ phần sau (xử lý mất cân bằng, chạy "
    "6 mốc thời gian, giải thích XAI, dashboard, báo cáo cuối) là các việc sắp tới để hoàn thiện.",
    table={
        "headers": ["Pha / Nhiệm vụ", "Người", "Trạng thái"],
        "rows": [
            ["Phase 1 — Data prep & harness", "Phúc", "✅ Hoàn thành"],
            ["Phase 2 — Benchmark 5 model @100%", "Đức", "✅ Hoàn thành"],
            ["Phase 4 — Xử lý mất cân bằng (RQ3)", "Đức", "▶ Sắp tới"],
            ["Phase 3 — Time-aware 6 mốc (RQ1)", "Khoa", "▶ Sắp tới"],
            ["Phase 5 — SHAP/LIME + độ ổn định (RQ2)", "Bình", "▶ Sắp tới"],
            ["Phase 6a — Streamlit dashboard", "Sơn", "▶ Sắp tới"],
            ["Phase 6b — Viết báo cáo & trực quan", "An", "▶ Sắp tới"],
        ],
        "top": 2.05,
        "width": 12.2,
        "col_w": [Inches(7.4), Inches(1.9), Inches(2.9)],
        "fs": 12,
    },
)

add_content(
    3,
    "PHASE 1 · DỮ LIỆU (PHÚC)",
    "Pipeline dữ liệu chống rò rỉ + khung thực nghiệm",
    [
        (
            "do",
            "7 bảng OULAD → master (32.593 × 33) → cắt 6 mốc 10–100% → tiền xử lý fit-on-train.",
        ),
        ("do", "Harness: chia 80/20 (StratifiedGroupKFold theo id_student) + CV 5-fold × 5 seed."),
        ("why", "Toàn bộ khâu huấn luyện đứng trên tập test cố định + pipeline chống rò rỉ này."),
        ("key", "6 bộ dataset_t10…t100 · test 20% cố định · 19/19 kiểm thử rò rỉ ĐẠT."),
    ],
    presenter="Phúc",
    notes="Nền tảng là pipeline dữ liệu của Phúc: gộp 7 bảng thành master 32.593 dòng, cắt theo 6 mốc "
    "tiến độ, tiền xử lý fit-on-train chống rò rỉ, cùng khung thực nghiệm chia 80/20 gom nhóm theo "
    "sinh viên và cross-validation 5-fold lặp 5 seed. 19 kiểm thử tự động xác nhận không rò rỉ.",
    image=(FIG / "preprocessing_sequence.png"),
    caption="Trình tự pipeline tiền xử lý",
)

add_content(
    4,
    "PHASE 2 · BENCHMARK (ĐỨC)",
    "So tuyển 5 thuật toán ứng viên (mốc 100%)",
    [
        (
            "do",
            "Huấn luyện & so sánh 5 model ứng viên: LR · RF · XGBoost · LightGBM · ANN @ mốc 100%.",
        ),
        (
            "why",
            "Bỏ sót SV nguy cơ là sai lầm đắt nhất → recall & PR-AUC lớp at-risk là chỉ số chính.",
        ),
        ("out", "Các model tree bám sát nhau; XGB dẫn đầu recall, LightGBM nhỉnh về PR-AUC."),
        ("key", "XGB @100 (baseline): recall 0,933 · F1 0,951 · PR-AUC 0,990."),
    ],
    presenter="Đức",
    notes="Phase 2 so tuyển năm thuật toán tại mốc 100% (baseline, CHƯA xử lý mất cân bằng — đó là "
    "Phase 4 sắp tới). Vì bỏ sót sinh viên nguy cơ là tốn kém nhất, chỉ số chính là recall và PR-AUC "
    "lớp at-risk. XGBoost dẫn đầu recall 0,933, LightGBM nhỉnh nhất về PR-AUC.",
    image=(FIG / "model_benchmark_baseline.png"),
    caption="So tuyển 5 model @ t=100% (baseline, no-resample)",
)

add_content(
    5,
    "PHASE 2 · KẾT QUẢ",
    "Bảng hiệu năng 5 model (baseline, tập test, mốc 100%)",
    [
        ("do", "Đánh giá trên tập test giữ riêng; sắp xếp theo recall lớp at-risk."),
        ("note", "Chênh lệch giữa các model nhỏ → chọn theo recall + khả năng giải thích được."),
    ],
    presenter="Đức",
    notes="Bảng hiệu năng năm model trên tập test tại mốc 100%, sắp theo recall. XGBoost đứng đầu "
    "recall, LightGBM đứng đầu PR-AUC; khoảng cách nhỏ nên nhóm chọn theo recall và tính giải thích "
    "được của mô hình.",
    table={
        "headers": ["Model", "Recall", "F1", "PR-AUC", "ROC-AUC"],
        "rows": [
            ["XGBoost", "0,933", "0,951", "0,990", "0,987"],
            ["LightGBM", "0,931", "0,952", "0,991", "0,989"],
            ["ANN (MLP)", "0,923", "0,947", "0,990", "0,987"],
            ["Random Forest", "0,921", "0,949", "0,990", "0,987"],
            ["Logistic Reg.", "0,918", "0,946", "0,989", "0,986"],
        ],
        "top": 2.9,
        "width": 11.0,
        "col_w": [Inches(3.4), Inches(1.9), Inches(1.9), Inches(1.9), Inches(1.9)],
        "fs": 13,
    },
)

add_content(
    6,
    "KẾ HOẠCH",
    "Các việc sắp tới để hoàn thiện bài làm",
    [
        ("note", "Theo luồng quy trình phân công: Đức → Khoa → Bình → Sơn / An."),
    ],
    presenter="Nhóm",
    notes="Các việc sắp tới để hoàn thiện, theo đúng luồng phân công: Đức làm Phase 4 xử lý mất cân "
    "bằng (so sánh no-resample/class-weight/SMOTE/ADASYN, RQ3); Khoa chạy thực nghiệm 6 mốc thời gian "
    "trả lời RQ1; Bình giải thích SHAP/LIME và đo độ ổn định RQ2; Sơn dựng Streamlit dashboard; An "
    "viết báo cáo cuối và trực quan hoá.",
    table={
        "headers": ["Phase — Công việc", "Người", "Sản phẩm / RQ"],
        "rows": [
            [
                "Phase 4 — Mất cân bằng (no-resample/class-weight/SMOTE/ADASYN)",
                "Đức",
                "Biểu đồ so sánh · RQ3",
            ],
            ["Phase 3 — Chạy thực nghiệm 6 mốc thời gian", "Khoa", "Đường cong hiệu năng · RQ1"],
            ["Phase 5 — SHAP/LIME + độ ổn định giải thích", "Bình", "Giải thích mô hình · RQ2"],
            ["Phase 6a — Xây dựng Streamlit dashboard", "Sơn", "App dự đoán + đóng gói"],
            ["Phase 6b — Viết báo cáo & trực quan hoá", "An", "Báo cáo cuối + slide tổng"],
        ],
        "top": 2.2,
        "width": 12.4,
        "col_w": [Inches(7.7), Inches(1.5), Inches(3.0)],
        "fs": 12,
    },
)

s7 = add_content(
    7,
    "KẾT LUẬN",
    "Đã hoàn thành & bước kế tiếp",
    [
        ("out", "Đã xong & tái lập: pipeline dữ liệu (P1) + so tuyển 5 model ứng viên (P2)."),
        ("out", "XGB dẫn đầu recall (0,933) ngay ở baseline; khoảng cách giữa các model nhỏ."),
        (
            "do",
            "Kế tiếp: P4 mất cân bằng → P3 time-aware RQ1 → P5 XAI RQ2 → P6 dashboard & báo cáo.",
        ),
        ("note", "Nền tảng tái lập từ src/ + tools/; 19/19 kiểm thử rò rỉ ĐẠT."),
    ],
    presenter="Nhóm",
    notes="Tóm lại: đã hoàn thành và tái lập được pipeline dữ liệu và bước so tuyển năm model ứng viên. "
    "XGBoost dẫn đầu recall ngay ở baseline, khoảng cách giữa các model nhỏ. Bước kế tiếp lần lượt là "
    "xử lý mất cân bằng, chạy 6 mốc thời gian, giải thích XAI, và dashboard cùng báo cáo cuối. Cảm ơn "
    "thầy/cô và cả lớp.",
)
_, tf = _box(s7, Inches(0.6), Inches(6.1), Inches(12.2), Inches(0.8))
r = tf.paragraphs[0].add_run()
r.text = "Cảm ơn đã lắng nghe!"
_set(r, 22, ACCENT, bold=True)


OUT.parent.mkdir(parents=True, exist_ok=True)
prs.save(str(OUT))
print(f"Saved {OUT}  ({len(prs.slides._sldIdLst)} slides)")
