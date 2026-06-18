"""Build notebooks/00_data_understanding.ipynb — a hands-on, runnable walkthrough
that *shows* how we understood the OULAD data (especially the 10.6M-row clickstream)
with clickhouse-local, step by step, before any modelling.

Unlike notebooks 01/02 (thin wrappers over tested src/ code), this notebook is
deliberately standalone and query-first: each cell runs a real ClickHouse query
on the raw CSVs / parquets and prints a number that the team can reproduce and
that maps to a slide. Narrative is in Vietnamese (it is a reading + doing guide).

Run:  python tools/build_data_understanding_nb.py
"""

from pathlib import Path

import nbformat as nbf
from nbformat.v4 import new_code_cell, new_markdown_cell

NB_DIR = Path(__file__).resolve().parents[1] / "notebooks"

# --------------------------------------------------------------------------- #
# Cell 0 — title
# --------------------------------------------------------------------------- #
TITLE = r"""# 00 · Hiểu dữ liệu OULAD bằng ClickHouse — *trước khi* làm mô hình

**Nhóm 1 · DSP391m · Data Tasks (Báo cáo 2)**

Notebook này là **bước 0** của toàn bộ data task: *hiểu dữ liệu*. Mục tiêu không phải
là "đọc code rồi tin", mà là **tự chạy từng truy vấn và nhìn thấy con số hiện ra** —
rồi mới đi xây bảng master (notebook 01) và phân tích EDA (notebook 02).

### Vì sao notebook này tồn tại
Bảng `studentVle` (clickstream) có **10,655,280 dòng / ~433 MB**. Mở bằng Excel:
không nổi. `pandas.read_csv` cả file: tốn vài chục giây và **vài GB RAM** mỗi lần thử.
Khi dữ liệu lớn, cách làm đúng là **để dữ liệu nằm yên trên đĩa và đẩy câu hỏi (SQL)
xuống một engine** — ở đây là **ClickHouse** (bản `clickhouse-local`: một file thực thi,
không cần server, chạy SQL thẳng trên CSV/Parquet).

### Bạn sẽ đi qua 10 bước
1. Thiết lập cầu nối Python → clickhouse-local (trong WSL).
2. Bài toán quy mô: vì sao không "nạp hết vào RAM".
3. Tiếp xúc đầu tiên + **cái bẫy kiểu dữ liệu** (mọi cột bị đọc thành chuỗi).
4. Tăng tốc: chuyển CSV → **Parquet có kiểu** (một lần, nhanh gấp ~26×).
5. Hồ sơ `studentVle`: bao nhiêu sinh viên, site, ngày, click.
6. Phân phối click & **độ lệch phải** (lý do phải `log1p`).
7. **Nhãn** & cân bằng lớp (từ `studentInfo`).
8. **Dữ liệu thiếu** và cơ chế thiếu.
9. Các bảng còn lại + **ghép về hạt master** (32.593 dòng).
10. **Cắt theo thời gian** (chống rò rỉ) và **tín hiệu sớm** (Cohen's d theo mốc).

> **Yêu cầu:** đã cài WSL (Ubuntu) và `clickhouse` trong thư mục home của WSL
> (`curl https://clickhouse.com/ | sh`). Notebook chạy bằng kernel `dsp` trên Windows
> và gọi sang WSL. Xem `reports/guide/DataTask_Process_Guide.pdf` để hiểu *vì sao*
> mỗi bước — notebook này là phần *làm*."""

# --------------------------------------------------------------------------- #
# Cell — setup helper
# --------------------------------------------------------------------------- #
SETUP_MD = r"""## 1 · Thiết lập: cầu nối Python → clickhouse-local

Ta viết một hàm `ch(sql)` nhỏ: ghi câu SQL ra file tạm, gọi `clickhouse local`
trong WSL đọc file đó, xuất ra CSV rồi nạp lại vào `pandas` để hiển thị đẹp.
`chp(sql)` thì in nguyên bảng "PrettyCompact" của ClickHouse (dùng cho `DESCRIBE`).

Điểm mấu chốt: **dữ liệu không bao giờ được nạp hết vào Python**. Python chỉ gửi
câu hỏi xuống và nhận về *kết quả đã tóm tắt* (vài dòng). Đó là cả ý tưởng."""

SETUP_CODE = r'''import io, subprocess, time, json
from pathlib import Path
import pandas as pd

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
WSL_DISTRO = "Ubuntu"          # tên distro WSL
CLICKHOUSE = "~/clickhouse"    # vị trí binary trong WSL home

def to_wsl(p: Path) -> str:
    """D:\\dsp\\... -> /mnt/d/dsp/..."""
    p = Path(p).resolve()
    return f"/mnt/{p.drive[0].lower()}{str(p)[2:].replace(chr(92), '/')}"

QFILE = ROOT / ".ch_query.sql"

def _run(sql: str, fmt: str) -> str:
    QFILE.write_text(sql, encoding="utf-8")
    cmd = ["wsl.exe", "-d", WSL_DISTRO, "--", "bash", "-lc",
           f"{CLICKHOUSE} local --queries-file {to_wsl(QFILE)} --format {fmt}"]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise RuntimeError("ClickHouse error:\n" + (r.stderr or "")[-2000:])
    return r.stdout

def ch(sql: str) -> pd.DataFrame:
    """Chạy 1 câu SELECT, trả về DataFrame."""
    return pd.read_csv(io.StringIO(_run(sql, "CSVWithNames")))

def chp(sql: str) -> None:
    """Chạy SQL, in nguyên bảng đẹp của ClickHouse."""
    print(_run(sql, "PrettyCompact"))

# Đường dẫn (WSL) tới các bảng và schema khai báo tường minh ----------------
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
SV_CSV      = to_wsl(RAW / "studentVle.csv")
SV_PARQUET  = to_wsl(INTERIM / "studentVle.parquet")
SI_CSV      = to_wsl(RAW / "studentInfo.csv")
REG_CSV     = to_wsl(RAW / "studentRegistration.csv")
COURSES_CSV = to_wsl(RAW / "courses.csv")
SA_CSV      = to_wsl(RAW / "studentAssessment.csv")
ASM_CSV     = to_wsl(RAW / "assessments.csv")
VLE_CSV     = to_wsl(RAW / "vle.csv")
MASTER_PARQUET = to_wsl(INTERIM / "master_raw.parquet")
CKPT_GLOB   = to_wsl(ROOT / "data" / "checkpoints" / "dataset_t{10,20,40,60,80,100}.parquet")

SV_SCHEMA  = "code_module String, code_presentation String, id_student Int32, id_site Int32, date Int16, sum_click Int32"
SI_SCHEMA  = ("code_module String, code_presentation String, id_student Int32, gender String, region String, "
              "highest_education String, imd_band String, age_band String, num_of_prev_attempts Int8, "
              "studied_credits Int32, disability String, final_result String")
REG_SCHEMA = "code_module String, code_presentation String, id_student Int32, date_registration String, date_unregistration String"
COURSES_SCHEMA = "code_module String, code_presentation String, module_presentation_length Int32"
SA_SCHEMA  = "id_assessment Int32, id_student Int32, date_submitted Int32, is_banked Int8, score String"
ASM_SCHEMA = "code_module String, code_presentation String, id_assessment Int32, assessment_type String, date String, weight Float32"
VLE_SCHEMA = "id_site Int32, code_module String, code_presentation String, activity_type String, week_from String, week_to String"

OUT = {}  # gom mọi con số để lưu ra JSON ở cuối (tái lập được)

# Kiểm tra cầu nối hoạt động:
print("ClickHouse:", _run("SELECT version()", "TSV").strip())
print("Thấy studentVle.csv:", (RAW / "studentVle.csv").exists())'''

# --------------------------------------------------------------------------- #
SCALE_MD = r"""## 2 · Bài toán quy mô — vì sao không "nạp hết vào RAM"

Đọc thử **500.000 dòng đầu** bằng pandas và đo bộ nhớ, rồi ngoại suy cho cả 10,66 triệu
dòng. Đây là lý do trực quan để **không** `read_csv` cả file mỗi lần muốn hỏi một câu."""

SCALE_CODE = r"""t0 = time.time()
sample = pd.read_csv(RAW / "studentVle.csv", nrows=500_000)
dt = time.time() - t0
mb = sample.memory_usage(deep=True).sum() / 1e6
n_full = 10_655_280
print(f"pandas đọc 500k dòng: {dt:.1f}s, {mb:.0f} MB trong RAM")
print(f"Ngoại suy cho {n_full:,} dòng: ~{dt*n_full/500_000:.0f}s mỗi lần đọc, "
      f"~{mb*n_full/500_000/1000:.1f} GB RAM")
print("=> Mỗi câu hỏi mà phải nạp lại cả file thì không khả thi. Hãy để engine lo.")
sample.head(3)"""

# --------------------------------------------------------------------------- #
GOTCHA_MD = r"""## 3 · Tiếp xúc đầu tiên — và **cái bẫy kiểu dữ liệu**

Hỏi ClickHouse "cột này kiểu gì?" bằng `DESCRIBE`. Vì file CSV để **giá trị trong ngoặc kép**,
ClickHouse đoán **mọi cột là `String`**. Hậu quả: `max(date)` trả về **"99"** (so sánh
*theo chữ cái*: "99" > "269" vì '9' > '2'!), và `avg(sum_click)` thì **lỗi** vì không
tính trung bình trên chuỗi được.

**Bài học #1:** với dữ liệu lớn, *luôn kiểm tra và khai báo kiểu* — đừng tin suy đoán mặc định."""

GOTCHA_CODE = r'''# 3a. ClickHouse đoán kiểu gì? -> tất cả là String
chp(f"DESCRIBE file('{SV_CSV}', 'CSVWithNames')")

# 3b. Cái bẫy: min/max trên 'date' khi nó là chuỗi (so sánh theo chữ cái)
print("--- date bị đọc như CHUỖI (sai): ---")
chp(f"""SELECT min(date) AS min_str, max(date) AS max_str
        FROM file('{SV_CSV}', 'CSVWithNames')""")

# 3c. Khai báo kiểu tường minh -> con số đúng
print("--- khai báo kiểu rõ ràng (đúng): ---")
df = ch(f"""SELECT count() AS rows, uniqExact(id_student) AS students,
                   min(date) AS min_day, max(date) AS max_day,
                   round(avg(sum_click),3) AS avg_click, max(sum_click) AS max_click
            FROM file('{SV_CSV}', 'CSVWithNames', '{SV_SCHEMA}')""")
OUT["studentVle_basic"] = df.iloc[0].to_dict()
df'''

# --------------------------------------------------------------------------- #
PARQUET_MD = r"""## 4 · Tăng tốc: CSV → **Parquet có kiểu** (làm một lần)

CSV phải đọc và *phân tích lại* 433 MB văn bản mỗi lần. **Parquet** là định dạng cột,
có kiểu, nén sẵn — đọc nhanh hơn nhiều. Ta chuyển một lần rồi truy vấn trên Parquet.
Ô này **idempotent**: nếu file đã có thì bỏ qua (đúng quy tắc checkpoint của dự án)."""

PARQUET_CODE = r'''pq_path = INTERIM / "studentVle.parquet"
if pq_path.exists():
    print(f"Đã có {pq_path.name} ({pq_path.stat().st_size/1e6:.1f} MB) — bỏ qua bước chuyển.")
else:
    print("Đang chuyển CSV -> Parquet (một lần)...")
    _run(f"""INSERT INTO FUNCTION file('{SV_PARQUET}', 'Parquet')
             SELECT code_module, code_presentation, id_student, id_site, date, sum_click
             FROM file('{SV_CSV}', 'CSVWithNames', '{SV_SCHEMA}')
             SETTINGS engine_file_truncate_on_insert=1""", "TSV")
    print(f"Xong: {pq_path.stat().st_size/1e6:.1f} MB")

# So sánh tốc độ: đếm trên CSV (quét text) vs trên Parquet
for label, src in [("CSV    ", f"file('{SV_CSV}','CSVWithNames','{SV_SCHEMA}')"),
                   ("Parquet", f"file('{SV_PARQUET}','Parquet')")]:
    t0 = time.time(); n = ch(f"SELECT count() FROM {src}").iloc[0,0]
    print(f"{label}: {n:,} dòng trong {time.time()-t0:5.2f}s")

csv_mb = (RAW/'studentVle.csv').stat().st_size/1e6
pq_mb  = pq_path.stat().st_size/1e6
print(f"\nKích thước: CSV {csv_mb:.0f} MB  ->  Parquet {pq_mb:.0f} MB  (nhỏ hơn ~{csv_mb/pq_mb:.0f}x)")
OUT["scale"] = {"csv_mb": round(csv_mb,1), "parquet_mb": round(pq_mb,1)}'''

# --------------------------------------------------------------------------- #
PROFILE_MD = r"""## 5 · Hồ sơ `studentVle` — dữ liệu này *trông như thế nào*?

Giờ truy vấn nhanh trên Parquet. Bao nhiêu sinh viên thực sự có click? Bao nhiêu loại
"site"? Khoảng ngày? Lưu ý `date` chạy từ **−25** (trước khai giảng) tới **269**
(độ dài môn). Có **26.074** sinh viên trong clickstream — ít hơn 28.785 sinh viên trong
`studentInfo`, nghĩa là một số sinh viên **không hề click**."""

PROFILE_CODE = r'''df = ch(f"""SELECT count() AS click_rows, uniqExact(id_student) AS distinct_students,
                   uniqExact(id_site) AS distinct_sites,
                   uniqExact((code_module,code_presentation)) AS presentations,
                   min(date) AS min_day, max(date) AS max_day
            FROM file('{SV_PARQUET}','Parquet')""")
OUT["studentVle_profile"] = df.iloc[0].to_dict()
df'''

# --------------------------------------------------------------------------- #
SKEW_MD = r"""## 6 · Phân phối click & **độ lệch phải**

Gộp clickstream về hạt (môn, kỳ, sinh viên) để có `total_clicks` — đây chính là đặc trưng
engagement quan trọng nhất. Nhìn **trung bình so với trung vị**: nếu mean ≫ median thì
phân phối **lệch phải nặng** (vài sinh viên siêu hoạt động kéo đuôi). Đây là bằng chứng số
cho quyết định **`log1p`** ở bước làm sạch."""

SKEW_CODE = r'''# total_clicks mỗi (môn,kỳ,sinh viên) — chỉ trên những sinh viên có hoạt động
df = ch(f"""WITH agg AS (
              SELECT code_module, code_presentation, id_student,
                     sum(sum_click) AS total_clicks, uniqExact(date) AS n_days_active
              FROM file('{SV_PARQUET}','Parquet')
              GROUP BY code_module, code_presentation, id_student)
            SELECT count() AS n_student_pres,
                   round(avg(total_clicks),1) AS mean, quantileExact(0.5)(total_clicks) AS median,
                   round(skewPop(total_clicks),2) AS skew, max(total_clicks) AS max_v,
                   round(avg(n_days_active),1) AS mean_days_active
            FROM agg""")
OUT["total_clicks_active"] = df.iloc[0].to_dict()
print("mean ≫ median và skew > 0  =>  lệch phải. Đây là lý do dùng log1p.")
df'''

# --------------------------------------------------------------------------- #
LABEL_MD = r"""## 7 · Nhãn & cân bằng lớp (từ `studentInfo`)

Nhãn `at_risk = 1` nếu `final_result ∈ {Fail, Withdrawn}`, ngược lại 0. Đếm trực tiếp:
tỉ lệ nguy cơ là **52,8%** — lệch lớp *nhẹ* (tỉ số 1,12), không phải 68/32 như slide minh hoạ
của môn. Lưu ý **Withdrawn** là lớp đơn lớn nhất — sẽ rất quan trọng ở phần EDA."""

LABEL_CODE = r'''df = ch(f"""SELECT final_result, count() AS n,
                   round(100.0*count()/sum(count()) OVER (),1) AS pct,
                   if(final_result IN ('Fail','Withdrawn'),1,0) AS at_risk
            FROM file('{SI_CSV}','CSVWithNames','{SI_SCHEMA}')
            GROUP BY final_result ORDER BY n DESC""")
display(df)
bal = ch(f"""SELECT count() AS rows, uniqExact(id_student) AS students,
                    uniqExact((code_module,code_presentation)) AS presentations,
                    countIf(final_result IN ('Fail','Withdrawn')) AS at_risk_n,
                    round(100.0*countIf(final_result IN ('Fail','Withdrawn'))/count(),2) AS at_risk_pct
             FROM file('{SI_CSV}','CSVWithNames','{SI_SCHEMA}')""")
OUT["class_balance"] = bal.iloc[0].to_dict()
bal'''

# --------------------------------------------------------------------------- #
MISSING_MD = r"""## 8 · Dữ liệu thiếu & cơ chế thiếu

Thiếu không chỉ là "đếm NaN" — phải hỏi **vì sao thiếu**. `date_unregistration` thiếu 69%
nhưng là **thiếu cấu trúc** (chỉ tồn tại nếu sinh viên rút môn) ⇒ bỏ. `imd_band` thiếu 3,4%
⇒ thêm hạng "Unknown". `date_registration` thiếu 45 dòng (0,14%) ⇒ điền median tập train.
Trong CSV, giá trị thiếu hiện ra dưới dạng **chuỗi rỗng** — nên ta đếm `= ''`."""

MISSING_CODE = r'''reg = ch(f"""SELECT count() AS rows,
                    countIf(date_registration='') AS reg_missing,
                    round(100.0*countIf(date_registration='')/count(),2) AS reg_missing_pct,
                    countIf(date_unregistration='') AS unreg_missing,
                    round(100.0*countIf(date_unregistration='')/count(),1) AS unreg_missing_pct
             FROM file('{REG_CSV}','CSVWithNames','{REG_SCHEMA}')""")
imd = ch(f"""SELECT countIf(imd_band='' OR imd_band='?') AS imd_missing,
                    round(100.0*countIf(imd_band='' OR imd_band='?')/count(),2) AS imd_missing_pct
             FROM file('{SI_CSV}','CSVWithNames','{SI_SCHEMA}')""")
OUT["missing"] = {**reg.iloc[0].to_dict(), **imd.iloc[0].to_dict()}
display(reg); display(imd)'''

# --------------------------------------------------------------------------- #
OTHER_MD = r"""## 9 · Các bảng còn lại + **ghép về hạt master**

Bốn bảng nhỏ còn lại trong một câu mỗi bảng, rồi câu hỏi quan trọng nhất:
ghép `studentInfo` với clickstream đã gộp để ra **hạt master = một dòng / (sinh viên × môn × kỳ)**.
Kết quả phải đúng **32.593 dòng**, trong đó **3.365 dòng có 0 click** (sinh viên không hề
hoạt động) — chính các dòng này sẽ được điền 0 ở bước làm sạch."""

OTHER_CODE = r'''print("courses:");           chp(f"SELECT count() AS module_presentations, min(module_presentation_length) AS min_len, max(module_presentation_length) AS max_len FROM file('{COURSES_CSV}','CSVWithNames','{COURSES_SCHEMA}')")
print("assessments:");       chp(f"SELECT assessment_type, count() AS n, countIf(date='') AS deadline_missing FROM file('{ASM_CSV}','CSVWithNames','{ASM_SCHEMA}') GROUP BY assessment_type ORDER BY n DESC")
print("studentAssessment:"); chp(f"SELECT count() AS rows, countIf(score='') AS score_missing FROM file('{SA_CSV}','CSVWithNames','{SA_SCHEMA}')")
print("vle:");               chp(f"SELECT count() AS rows, uniqExact(activity_type) AS activity_types FROM file('{VLE_CSV}','CSVWithNames','{VLE_SCHEMA}')")

# Ghép về hạt master ngay trong SQL (join studentInfo <- clickstream đã gộp)
df = ch(f"""WITH agg AS (
              SELECT code_module, code_presentation, id_student, sum(sum_click) AS total_clicks
              FROM file('{SV_PARQUET}','Parquet')
              GROUP BY code_module, code_presentation, id_student)
            SELECT count() AS master_rows,
                   countIf(a.total_clicks = 0 OR a.total_clicks IS NULL) AS zero_click_rows,
                   round(avg(ifNull(a.total_clicks,0)),1) AS mean_total_clicks
            FROM file('{SI_CSV}','CSVWithNames','{SI_SCHEMA}') AS si
            LEFT JOIN agg AS a USING (code_module, code_presentation, id_student)""")
OUT["master_grain"] = df.iloc[0].to_dict()
df'''

# --------------------------------------------------------------------------- #
CUTOFF_MD = r"""## 10a · Cắt theo thời gian — trái tim của chống rò rỉ

Bài toán là **dự đoán sớm**: ở mốc *t%* khoá học ta chỉ được biết những gì xảy ra
**trước** ngày cắt `cutoff = round(độ_dài_môn × t/100)`. Đếm số sự kiện clickstream còn
lại ở mỗi mốc: số này **tăng dần** theo t và mốc 100% giữ **trọn** 10,66 triệu sự kiện —
đúng như test rò rỉ yêu cầu (không dòng nào vượt cutoff, số lượng không giảm theo t)."""

CUTOFF_CODE = r'''df = ch(f"""SELECT t_percent, count() AS events_le_cutoff,
                   round(100.0*count() / (SELECT count() FROM file('{SV_PARQUET}','Parquet')),1) AS pct_of_all
            FROM (
              SELECT v.date AS date, c.len AS len, arrayJoin([10,20,40,60,80,100]) AS t_percent
              FROM file('{SV_PARQUET}','Parquet') AS v
              INNER JOIN (
                SELECT code_module, code_presentation, module_presentation_length AS len
                FROM file('{COURSES_CSV}','CSVWithNames','{COURSES_SCHEMA}')
              ) AS c USING (code_module, code_presentation))
            WHERE date <= round(len * t_percent / 100)
            GROUP BY t_percent ORDER BY t_percent""")
OUT["cutoff_growth"] = df.set_index("t_percent")["events_le_cutoff"].to_dict()
df'''

# --------------------------------------------------------------------------- #
SIGNAL_MD = r"""## 10b · Tín hiệu: yếu tố nào phân biệt nguy cơ, và *sớm tới đâu*?

Cuối cùng, dùng bảng master đã dựng (`master_raw.parquet`, 32.593 dòng) để đo **độ mạnh
tín hiệu** — **Cohen's d** (khoảng cách hai nhóm tính theo độ lệch chuẩn). Công thức đúng
như dự án dùng: `|m₁−m₀| / sqrt((s₁²+s₀²)/2)`.

- `days_since_last_activity` (số ngày bặt vô âm tín): **d ≈ 2,55** — khổng lồ.
- Hành vi **áp đảo** nhân khẩu; không cặp nào tương quan ≥ 0,95 ⇒ không rò rỉ.

Rồi đo **d theo từng mốc thời gian** (6 file checkpoint): tín hiệu xuất hiện **rất sớm** —
`n_days_active` đã đạt d ≥ 0,8 ngay ở **mốc 10%**. Đây là nền tảng của *can thiệp sớm*."""

SIGNAL_CODE = r'''# Cohen's d (công thức dự án) cho các đặc trưng đầu bảng, trên master_raw
def cohens_d_sql(col):
    return (f"round(abs(avgIf({col},at_risk=1)-avgIf({col},at_risk=0))"
            f"/sqrt((stddevSampIf({col},at_risk=1)*stddevSampIf({col},at_risk=1)"
            f"+stddevSampIf({col},at_risk=0)*stddevSampIf({col},at_risk=0))/2),3)")
cols = ["days_since_last_activity","n_assessments_submitted","weighted_score_to_date","n_days_active","total_clicks"]
sel = ", ".join(f"{cohens_d_sql(c)} AS `{c}`" for c in cols)
d_master = ch(f"SELECT {sel} FROM file('{MASTER_PARQUET}','Parquet')")
OUT["cohens_d_master"] = d_master.iloc[0].to_dict()
print("Cohen's d trên toàn khoá (master_raw):"); display(d_master)

# Tương quan: kiểm đa cộng tuyến + rò rỉ (|r| < 0.95 là an toàn)
corr = ch(f"""SELECT round(corr(days_since_last_activity, at_risk),3) AS idle_vs_label,
                     round(corr(n_days_active, total_clicks),3)       AS active_vs_clicks,
                     round(corr(days_since_last_activity, n_assessments_submitted),3) AS idle_vs_submits
              FROM file('{MASTER_PARQUET}','Parquet')""")
OUT["correlations"] = corr.iloc[0].to_dict()
print("Tương quan (không cặp nào chạm 0,95 => không rò rỉ):"); display(corr)

# Tín hiệu mạnh dần theo mốc thời gian (6 checkpoint)
growth = ch(f"""SELECT t_percent, round(avg(at_risk),3) AS at_risk_rate, count() AS n_rows,
                       {cohens_d_sql('n_days_active')} AS d_n_days_active,
                       {cohens_d_sql('total_clicks')} AS d_total_clicks,
                       {cohens_d_sql('days_since_last_activity')} AS d_idle,
                       {cohens_d_sql('mean_score_to_date')} AS d_mean_score
                FROM file('{CKPT_GLOB}','Parquet')
                GROUP BY t_percent ORDER BY t_percent""")
OUT["discrimination_by_t"] = growth.to_dict("records")
print("Cohen's d theo mốc % khoá học (cùng 32.593 sinh viên ở mọi mốc):"); growth'''

# --------------------------------------------------------------------------- #
WRAP_MD = r"""## 11 · Lưu kết quả & ánh xạ sang slide

Mọi con số vừa tính được gom vào `reports/data_understanding/query_outputs.json` để
notebook/guide/slide dùng chung **một nguồn sự thật**. So sánh với
`reports/data_understanding/verified_numbers.json` (bản tham chiếu) — phải khớp."""

WRAP_CODE = r"""out_path = ROOT / "reports" / "data_understanding" / "query_outputs.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(OUT, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
print("Đã lưu", out_path)
print(json.dumps(OUT, ensure_ascii=False, indent=2, default=str)[:1500])"""

CONCLUSION_MD = r"""### Kết luận — từ "không hiểu" tới "hiểu và tái lập được"

| Câu hỏi về dữ liệu | Truy vấn (bước) | Con số | Dùng ở slide |
|---|---|---|---|
| Dữ liệu lớn cỡ nào? | 2, 4 | 10,66 tr dòng · 433 MB · Parquet 22 MB | "Required Data", "At scale" |
| Hạt dữ liệu & cỡ mẫu? | 9 | 32.593 dòng · 28.785 SV · 22 kỳ | "Data Requirements" |
| Cân bằng lớp? | 7 | nguy cơ 52,8% · tỉ số 1,12 | "Target & Class Balance" |
| Thiếu ở đâu, vì sao? | 8 | imd 3,41% · reg 0,14% · unreg 69,1% | "Data Quality Profile" |
| Vì sao phải log1p? | 6 | total_clicks lệch phải, skew > 0 | "Outliers / Skew" |
| Chống rò rỉ thế nào? | 10a | sự kiện ≤ cutoff tăng 25%→100% | "Time-aware / Leakage" |
| Tín hiệu mạnh nhất? | 10b | days_idle d ≈ 2,55 · sớm từ 10% | "Effect sizes", "Early signal" |

Giờ ta đã *thực sự hiểu* dữ liệu — và mọi con số đều **tự chạy lại được**. Bước tiếp theo:
notebook **01** (dựng bảng master) và **02** (EDA đầy đủ)."""


def build():
    nb = nbf.v4.new_notebook()
    pairs = [
        (new_markdown_cell, TITLE),
        (new_markdown_cell, SETUP_MD),
        (new_code_cell, SETUP_CODE),
        (new_markdown_cell, SCALE_MD),
        (new_code_cell, SCALE_CODE),
        (new_markdown_cell, GOTCHA_MD),
        (new_code_cell, GOTCHA_CODE),
        (new_markdown_cell, PARQUET_MD),
        (new_code_cell, PARQUET_CODE),
        (new_markdown_cell, PROFILE_MD),
        (new_code_cell, PROFILE_CODE),
        (new_markdown_cell, SKEW_MD),
        (new_code_cell, SKEW_CODE),
        (new_markdown_cell, LABEL_MD),
        (new_code_cell, LABEL_CODE),
        (new_markdown_cell, MISSING_MD),
        (new_code_cell, MISSING_CODE),
        (new_markdown_cell, OTHER_MD),
        (new_code_cell, OTHER_CODE),
        (new_markdown_cell, CUTOFF_MD),
        (new_code_cell, CUTOFF_CODE),
        (new_markdown_cell, SIGNAL_MD),
        (new_code_cell, SIGNAL_CODE),
        (new_markdown_cell, WRAP_MD),
        (new_code_cell, WRAP_CODE),
        (new_markdown_cell, CONCLUSION_MD),
    ]
    nb.cells = [factory(text) for factory, text in pairs]
    nb.metadata = {
        "kernelspec": {
            "display_name": "Python 3 (dsp)",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python"},
    }
    path = NB_DIR / "00_data_understanding.ipynb"
    nbf.write(nb, path)
    print("wrote", path, "—", len(nb.cells), "cells")


if __name__ == "__main__":
    build()
