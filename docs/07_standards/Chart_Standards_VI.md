# Tiêu Chuẩn Trình Bày Biểu Đồ

**Hướng dẫn trực quan hóa thống nhất cho mọi hình vẽ EDA và báo cáo**

DSP391m – Group 1 · Report 2 (Data Tasks) · Work item STT 40-bis / STT 39 (Binh)

---

## 1. Kiểu chữ (Typography) & Kích thước

Tất cả hình vẽ phải sử dụng một họ phông chữ (font family) duy nhất, đa nền tảng, để đảm bảo hiển thị giống nhau trên máy của mọi thành viên và trong bản PDF cuối cùng.

| Thuộc tính | Giá trị |
|---|---|
| Họ phông chữ (font family) | `DejaVu Sans` |
| Cỡ chữ cơ sở (base font size) | 12 pt |
| Tiêu đề hình (figure title) | 14 pt, đậm |
| Nhãn trục (axis labels) | 12 pt |
| Nhãn vạch chia (tick labels) | 10 pt |
| Chú thích (legend text) | 10 pt |
| Kích thước hình mặc định (figure size) | 8 × 5 inch |
| Kích thước hình nhiệt đồ (heatmap) | 10 × 8 inch |
| Độ phân giải xuất (export DPI) | 150 |

Hình rộng (ví dụ: biểu đồ đường nhiều mốc kiểm tra) có thể dùng 12 × 5 inch. Không được dùng dưới 6 × 4 inch vì ảnh PNG xuất ra sẽ không đọc được.

---

## 2. Màu sắc (Colour)

### 2.1 Bảng màu chung (General palette)

Sử dụng bảng màu `"colorblind"` của seaborn làm chu kỳ màu mặc định. Bảng màu này an toàn với các dạng khiếm thị màu sắc phổ biến nhất và phù hợp với nền trắng hoặc xám nhạt.

```
sns.set_palette("colorblind")
```

Đối với thang màu liên tục (heatmap, ma trận tương quan), dùng `"coolwarm"` với `center=0`.

### 2.2 Màu lớp cố định (Fixed class colours) — bắt buộc

Mọi biểu đồ phân biệt hai lớp mục tiêu (target classes) **phải** sử dụng đúng cùng một giá trị hex. Nghiêm cấm dùng màu khác nhau cho cùng một lớp trên các hình vẽ khác nhau.

| Lớp (Class) | Nhãn (Label) | Hex | Mô tả |
|---|---|---|---|
| 0 | Không có nguy cơ (Pass / Distinction) | `#2166AC` | Xanh thép trầm |
| 1 | Có nguy cơ (Fail / Withdrawn) | `#D6604D` | Cam đất ấm |

Khai báo một lần ở đầu mỗi notebook:

```python
CLASS_COLOURS = {0: "#2166AC", 1: "#D6604D"}
CLASS_LABELS  = {0: "Not-at-risk", 1: "At-risk"}
```

---

## 3. Quy tắc trục & nhãn (Axis & Labelling Rules)

1. **Mọi trục phải có nhãn.** Ghi đơn vị khi cần (ví dụ: `"Tổng số lần nhấp (lượt)"`, `"Điểm trung bình (0–100)"`, `"Độ dài khóa học (%)"`, `"Ngày"`).
2. **Tiêu đề hình vẽ** theo mẫu: *Biến — phân nhóm theo Lớp Mục Tiêu* (ví dụ: `"Phân phối Tổng số lần nhấp theo Lớp Mục Tiêu"`).
3. **Dấu phân cách hàng nghìn (thousands separators)**: bất kỳ trục đếm nào ≥ 1 000 phải dùng định dạng dấu phẩy. Áp dụng bằng: `ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))`.
4. **Nhãn danh mục dài** (> 6 ký tự) trên trục x phải xoay 45° và căn phải: `plt.xticks(rotation=45, ha="right")`.
5. **Chú thích (legend)** bắt buộc trên tất cả biểu đồ nhiều chuỗi; đặt vị trí `loc="best"` trừ khi che dữ liệu thì dùng `loc="upper left"` hoặc `bbox_to_anchor`.

---

## 4. Hướng dẫn chọn loại biểu đồ (Chart-Type Selection)

| Câu hỏi / Mục đích | Biểu đồ khuyến nghị | Ghi chú |
|---|---|---|
| Phân phối của một biến số đơn lẻ | Histogram + lớp phủ KDE | Dùng `kde=True` trong `sns.histplot`; vẽ đường đứt nét tại giá trị trung bình |
| So sánh nhóm của một biến số | Boxplot hoặc Violin plot | Ưu tiên Violin khi n > 200 mỗi nhóm |
| Tương quan giữa các đặc trưng số | Heatmap (nhiệt đồ) | `annot=True`, che tam giác trên, dùng `"coolwarm"` |
| Tần suất / số lượng danh mục | Biểu đồ cột (ngang nếu > 6 danh mục) | Sắp xếp cột giảm dần |
| Xu hướng theo thời gian qua các mốc kiểm tra | Biểu đồ đường có điểm đánh dấu | Mỗi lớp một đường; trục x = nhãn mốc (10%, 20%, …, 100%) |
| Bivariate: số vs. số | Biểu đồ tán xạ (scatter plot) | Dùng `alpha=0.4` để xử lý điểm chồng lên nhau |

Đối với sáu mốc kiểm tra theo thời gian (10 / 20 / 40 / 60 / 80 / 100% độ dài khóa học), luôn dùng biểu đồ đường với phần trăm mốc kiểm tra trên trục x, không dùng biểu đồ cột. Cách này giúp xu hướng thời gian hiện ra ngay lập tức.

---

## 5. Xuất file & đặt tên file (Export & File Naming)

- Lưu tất cả hình vẽ vào `reports/figures/` dưới định dạng **PNG**.
- Dùng tên theo quy ước **snake_case** với tiền tố mã hóa loại phân tích:

| Tiền tố | Loại phân tích | Ví dụ |
|---|---|---|
| `dist_` | Phân phối đơn biến (univariate distribution) | `dist_total_clicks.png` |
| `bivar_` | Hai biến / so sánh nhóm (bivariate / group comparison) | `bivar_mean_score_by_label.png` |
| `corr_` | Heatmap tương quan (correlation heatmap) | `corr_pearson.png` |
| `time_` | Xu hướng theo thời gian / mốc kiểm tra | `time_clicks_by_label.png` |
| `cat_` | Tần suất danh mục (category frequency) | `cat_module_type.png` |

Lưu bằng lệnh: `fig.savefig("reports/figures/<name>.png", dpi=150, bbox_inches="tight")`.

---

## 6. Đoạn mã rcParams (copy-paste vào mỗi notebook)

Dán khối này **một lần**, ngay sau phần import, trong mỗi notebook phân tích.

```python
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# ── DSP391m Group 1 · Chart Standards ─────────────────────────────────────
plt.rcParams.update({
    "font.family":       "DejaVu Sans",
    "font.size":         12,
    "axes.titlesize":    14,
    "axes.titleweight":  "bold",
    "axes.labelsize":    12,
    "xtick.labelsize":   10,
    "ytick.labelsize":   10,
    "legend.fontsize":   10,
    "figure.figsize":    (8, 5),
    "figure.dpi":        150,
    "savefig.dpi":       150,
    "savefig.bbox":      "tight",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "grid.alpha":        0.3,
})

sns.set_palette("colorblind")

# Fixed class colours — MUST be used in every class-split chart
CLASS_COLOURS = {0: "#2166AC", 1: "#D6604D"}
CLASS_LABELS  = {0: "Not-at-risk", 1: "At-risk"}
# ──────────────────────────────────────────────────────────────────────────
```

---

*Cập nhật lần cuối: 2026-06-14 · Nhóm 1 (DSP391m) duy trì*
