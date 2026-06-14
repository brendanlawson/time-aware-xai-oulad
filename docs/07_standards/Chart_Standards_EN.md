# Chart Presentation Standards

**Uniform visualization guidelines for every EDA and report figure**

DSP391m – Group 1 · Report 2 (Data Tasks) · Work item STT 40-bis / STT 39 (Binh)

---

## 1. Typography & Sizing

All figures must use a single, cross-platform font family to ensure identical rendering on every team member's machine and in the final PDF.

| Property | Value |
|---|---|
| Font family | `DejaVu Sans` |
| Base font size | 12 pt |
| Figure title | 14 pt, bold |
| Axis labels | 12 pt |
| Tick labels | 10 pt |
| Legend text | 10 pt |
| Figure size (default) | 8 × 5 inches |
| Figure size (heatmap) | 10 × 8 inches |
| Export DPI | 150 |

Wide figures (e.g., multi-checkpoint line charts) may use 12 × 5 inches. Never go below 6 × 4 or the exported PNG will be unreadable.

---

## 2. Colour

### 2.1 General palette

Use the seaborn `"colorblind"` palette as the default cycle. This palette is safe for the most common forms of colour-vision deficiency and pairs well with white or light-grey backgrounds.

```
sns.set_palette("colorblind")
```

For continuous colour scales (heatmaps, correlation matrices), use `"coolwarm"` with `center=0`.

### 2.2 Fixed class colours (mandatory)

Every chart that distinguishes the two target classes **must** use the exact same hex values. Using different colours for the same class across figures is not permitted.

| Class | Label | Hex | Appearance |
|---|---|---|---|
| 0 | Not-at-risk (Pass / Distinction) | `#2166AC` | Calm steel-blue |
| 1 | At-risk (Fail / Withdrawn) | `#D6604D` | Warm terracotta-orange |

Define these once at the top of every notebook:

```python
CLASS_COLOURS = {0: "#2166AC", 1: "#D6604D"}
CLASS_LABELS  = {0: "Not-at-risk", 1: "At-risk"}
```

---

## 3. Axis & Labelling Rules

1. **Every axis must be labelled.** Include units where applicable (e.g., `"Total Clicks (count)"`, `"Mean Score (0–100)"`, `"Course Length (%)"`, `"Date"`).
2. **Figure titles** follow the pattern: *Variable — grouped by Target Class* (e.g., `"Distribution of Total Clicks by Target Class"`).
3. **Thousands separators**: any count axis ≥ 1 000 must use comma formatting. Apply with `ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))`.
4. **Long category labels** (> 6 characters) on the x-axis must be rotated 45° and right-aligned: `plt.xticks(rotation=45, ha="right")`.
5. A **legend** is required on all multi-series charts; position it with `loc="best"` unless it obscures data, in which case use `loc="upper left"` or `bbox_to_anchor`.

---

## 4. Chart-Type Selection

| Question / Purpose | Recommended chart | Notes |
|---|---|---|
| Distribution of a single numeric variable | Histogram + KDE overlay | Use `kde=True` in `sns.histplot`; show mean as a vertical dashed line |
| Group comparison of a numeric variable | Boxplot or Violin plot | Violin preferred when n > 200 per group |
| Correlation between all numeric features | Heatmap | `annot=True`, mask upper triangle, use `"coolwarm"` |
| Category frequency / count | Bar chart (horizontal if > 6 categories) | Sort bars descending |
| Time-aware trend across checkpoints | Line chart with markers | One line per class; x-axis = checkpoint label (10%, 20%, …, 100%) |
| Bivariate numeric vs. numeric | Scatter plot | Apply `alpha=0.4` for overplotting |

For the six time-aware checkpoints (10 / 20 / 40 / 60 / 80 / 100 % of course length), always use a line chart with the checkpoint percentage on the x-axis, not a bar chart. This makes temporal trends immediately visible.

---

## 5. Export & File Naming

- Save all figures to `reports/figures/` as **PNG**.
- Use **snake_case** names with a prefix that encodes the analysis type:

| Prefix | Analysis type | Example |
|---|---|---|
| `dist_` | Univariate distribution | `dist_total_clicks.png` |
| `bivar_` | Bivariate / group comparison | `bivar_mean_score_by_label.png` |
| `corr_` | Correlation heatmap | `corr_pearson.png` |
| `time_` | Time-aware / checkpoint trend | `time_clicks_by_label.png` |
| `cat_` | Category frequency | `cat_module_type.png` |

Save with: `fig.savefig("reports/figures/<name>.png", dpi=150, bbox_inches="tight")`.

---

## 6. rcParams Snippet (copy-paste into every notebook)

Paste this block **once**, immediately after imports, in every analysis notebook.

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

*Last updated: 2026-06-14 · Maintained by Group 1 (DSP391m)*
