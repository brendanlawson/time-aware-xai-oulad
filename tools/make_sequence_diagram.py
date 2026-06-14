"""Render the preprocessing-sequence flow diagram for STT 22.

Output: reports/figures/preprocessing_sequence.png
Run with a Python whose matplotlib has a working font stack:
    python tools/make_sequence_diagram.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = (
    Path(__file__).resolve().parents[1]
    / "reports"
    / "figures"
    / "preprocessing_sequence.png"
)
BLUE, ORANGE, GREY = "#2166AC", "#D6604D", "#5b6770"

steps = [
    ("master_raw / dataset_t", GREY),
    ("1. SPLIT  (group-aware + stratified by id_student; fixed 20% test)", BLUE),
    ("2. handle_missing  (impute logic learned on TRAIN, applied to both)", BLUE),
    ("3. handle_outliers  (log1p / winsorize; thresholds from TRAIN)", BLUE),
    ("4. ColumnTransformer.fit(TRAIN)  (scaler + ordinal + one-hot + binary)", BLUE),
    ("4b. transform(TRAIN) and transform(TEST)", BLUE),
    ("5. RESAMPLE (SMOTE / ADASYN)  ->  TRAIN ONLY", ORANGE),
    ("model.fit(TRAIN_resampled)  ;  evaluate on TEST", GREY),
]

fig, ax = plt.subplots(figsize=(11, 9))
ax.set_xlim(0, 10)
ax.set_ylim(0, len(steps) * 1.25)
ax.axis("off")

y = len(steps) * 1.25 - 0.8
dy = 1.25
centers = []
for text, colour in steps:
    box = FancyBboxPatch(
        (0.6, y - 0.42),
        8.8,
        0.84,
        boxstyle="round,pad=0.04,rounding_size=0.12",
        linewidth=1.5,
        edgecolor=colour,
        facecolor=colour + "22",
    )
    ax.add_patch(box)
    ax.text(5.0, y, text, ha="center", va="center", fontsize=11, color="black")
    centers.append(y)
    y -= dy

for y0, y1 in zip(centers[:-1], centers[1:]):
    ax.add_patch(
        FancyArrowPatch(
            (5.0, y0 - 0.42),
            (5.0, y1 + 0.42),
            arrowstyle="-|>",
            mutation_scale=16,
            linewidth=1.4,
            color=GREY,
        )
    )

ax.set_title(
    "Anti-leakage preprocessing sequence (Task 22)", fontsize=13, fontweight="bold"
)
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, dpi=150, bbox_inches="tight")
print("wrote", OUT)
