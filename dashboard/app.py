"""Instructor early-warning dashboard (Phase 6a).

Thin Streamlit UI over the trained checkpoint bundles — ALL logic lives in
``src/`` (bundle loading, anti-leakage transform, SHAP) per the team rule that
the interface stays separate from the prediction pipeline.

What it shows, per checkpoint t:
  * the frozen TEST cohort ranked by at-risk probability at a chosen threshold;
  * whether each student is still enrolled at t (an instructor cannot intervene
    on someone who already withdrew — the project's dual-cohort finding);
  * per-student local SHAP explanation, labelled with the checkpoint it uses.

Run:
    streamlit run dashboard/app.py
Smoke test (no UI, asserts the scoring path end-to-end):
    python dashboard/app.py --smoke
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt  # noqa: E402
import streamlit as st  # noqa: E402

from src.config import CHECKPOINT_MAP_PATH, CHECKPOINTS, RAW_DATA_DIR, TABLES_DIR  # noqa: E402
from src.evaluation.make_split import load_checkpoint_split  # noqa: E402
from src.features.preprocessing import (  # noqa: E402
    handle_missing,
    handle_outliers,
    make_X_y,
    transform_test,
)
from src.modeling.predict import load_bundle  # noqa: E402
from src.xai import shap_explain  # noqa: E402

KEY = ["code_module", "code_presentation", "id_student"]
PRES = ["code_module", "code_presentation"]
# Tree bundles explain in milliseconds via TreeExplainer; logreg/ann would fall
# back to the (slow) kernel explainer, so the picker stays with the leaders.
MODELS = ("xgb", "lgbm", "rf")


@st.cache_resource(show_spinner="Loading model bundle ...")
def bundle(model_name: str, t: int) -> dict:
    return load_bundle(model_name, t)


@st.cache_resource(show_spinner="Building SHAP explainer ...")
def explainer(model_name: str, t: int):
    return shap_explain.build_explainer(bundle(model_name, t)["model"], None)


@st.cache_data(show_spinner="Scoring the frozen test cohort ...")
def score_cohort(model_name: str, t: int):
    """Score the committed test split at checkpoint t.

    Returns (scores_df, X_raw, X_transformed, feat_names) — scores_df has one
    row per enrolment: ids, probability, true label and still_enrolled at t.
    """
    b = bundle(model_name, t)
    _, test_df = load_checkpoint_split(t)
    X, y = make_X_y(test_df)
    Xp = handle_missing(X.copy(), stats=dict(b["stats"]["missing"]))
    Xp = handle_outliers(Xp, stats=dict(b["stats"]["outlier"]))
    Xt = transform_test(b["ct"], Xp)
    proba = b["model"].predict_proba(Xt)[:, 1]

    reg = pd.read_csv(RAW_DATA_DIR / "studentRegistration.csv")[KEY + ["date_unregistration"]]
    cut = pd.read_csv(CHECKPOINT_MAP_PATH)
    cut = cut[cut.t_percent == t][PRES + ["cutoff_day"]]
    td = test_df[KEY].merge(reg, on=KEY, how="left").merge(cut, on=PRES, how="left")
    still = td["date_unregistration"].isna() | (td["date_unregistration"] > td["cutoff_day"])

    scores = test_df[KEY].copy()
    scores["proba"] = proba
    scores["y_true"] = y.to_numpy()
    scores["still_enrolled"] = still.to_numpy()
    return scores, X, np.asarray(Xt, dtype=float), list(b["feat_names"])


def local_shap_fig(
    model_name: str, t: int, Xt_row: np.ndarray, feat_names: list[str], top: int = 12
):
    """Signed local SHAP bar for one transformed row (red pushes toward at-risk)."""
    vals = shap_explain.compute_shap_values(explainer(model_name, t), Xt_row.reshape(1, -1))[0]
    df = pd.DataFrame({"feature": feat_names, "weight": vals})
    df = df.reindex(df["weight"].abs().sort_values(ascending=False).index).head(top)[::-1]
    fig, ax = plt.subplots(figsize=(7, 0.38 * len(df) + 1))
    ax.barh(
        df["feature"],
        df["weight"],
        color=["#C0392B" if w >= 0 else "#2166AC" for w in df["weight"]],
    )
    ax.axvline(0, color="#888888", lw=0.8)
    ax.set_xlabel(f"SHAP value at t={t}%  (red → at-risk, blue → not-at-risk)")
    fig.tight_layout()
    return fig


def threshold_presets() -> dict:
    """Validation-chosen policy thresholds (xgb @ t=100), if the table exists."""
    p = TABLES_DIR / "threshold_validation.csv"
    if not p.exists():
        return {}
    tv = pd.read_csv(p)
    return dict(zip(tv["policy"], tv["threshold"]))


def main() -> None:
    st.set_page_config(page_title="OULAD early-warning", layout="wide")
    st.title("Early-warning dashboard — at-risk students (OULAD)")

    with st.sidebar:
        model_name = st.selectbox("Model", MODELS, index=0)
        t = st.select_slider("Checkpoint (% of course)", options=list(CHECKPOINTS), value=40)
        presets = threshold_presets()
        preset = st.selectbox(
            "Threshold policy (chosen on validation, xgb@t100)",
            ["manual"] + list(presets),
            index=0,
        )
        threshold = st.slider(
            "Decision threshold", 0.0, 1.0, float(presets.get(preset, 0.5)), 0.01
        )
        only_active = st.checkbox("Only students still enrolled at t (actionable)", value=True)

    scores, X_raw, Xt, feat_names = score_cohort(model_name, t)
    view = scores[scores.still_enrolled] if only_active else scores
    flagged = view[view.proba >= threshold].sort_values("proba", ascending=False)

    tp = int(((view.proba >= threshold) & (view.y_true == 1)).sum())
    n_pos = int((view.y_true == 1).sum())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Students in view", f"{len(view):,}")
    c2.metric("Flagged at-risk", f"{len(flagged):,}")
    c3.metric("Backtest recall", f"{tp / n_pos:.3f}" if n_pos else "–")
    c4.metric("Backtest precision", f"{tp / len(flagged):.3f}" if len(flagged) else "–")
    st.caption(
        f"Frozen test cohort (5,756 students), scored with {model_name} trained at t={t}%. "
        "Backtest metrics use the known final results; in deployment these are unknown. "
        "Predictions and explanations are only valid *as of* this checkpoint."
    )
    if not only_active:
        gone = int((~scores.still_enrolled).sum())
        st.warning(
            f"{gone:,} enrolments in this view already withdrew before the t={t}% cutoff — "
            "they can be *recorded*, not *helped*. Untick to include them anyway."
        )

    left, right = st.columns([1, 1])
    with left:
        st.subheader("Ranked at-risk list")
        st.dataframe(
            flagged.assign(proba=flagged.proba.round(3)).reset_index(drop=True),
            use_container_width=True,
            height=430,
        )
    with right:
        st.subheader("Why is this student flagged?")
        if flagged.empty:
            st.info("No student clears the current threshold.")
            return
        pick = st.selectbox(
            "Student (id · module · presentation)",
            flagged.index,
            format_func=lambda i: (
                f"{scores.loc[i, 'id_student']} · {scores.loc[i, 'code_module']} · "
                f"{scores.loc[i, 'code_presentation']}  (p={scores.loc[i, 'proba']:.3f})"
            ),
        )
        st.pyplot(local_shap_fig(model_name, t, Xt[pick], feat_names))
        with st.expander("Feature values as of this checkpoint"):
            st.dataframe(X_raw.loc[pick].to_frame("value"), use_container_width=True)


def smoke() -> None:
    """End-to-end scoring check without the UI (fails loudly if the path breaks)."""
    # Cached funcs run as plain functions outside the Streamlit runtime.
    scores, X_raw, Xt, feat_names = score_cohort("xgb", 40)
    assert len(scores) == len(X_raw) == Xt.shape[0] > 6000
    assert Xt.shape[1] == len(feat_names)
    assert scores["proba"].between(0, 1).all()
    assert scores["still_enrolled"].dtype == bool and 0 < scores["still_enrolled"].sum() < len(
        scores
    )
    vals = shap_explain.compute_shap_values(
        shap_explain.build_explainer(load_bundle("xgb", 40)["model"], None), Xt[:1]
    )
    assert vals.shape == (1, len(feat_names))
    print(
        f"SMOKE OK: {len(scores):,} rows scored | {int(scores.still_enrolled.sum()):,} still enrolled "
        f"| top proba {scores.proba.max():.3f} | shap row shape {vals.shape}"
    )


try:
    from streamlit.runtime.scriptrunner import get_script_run_ctx

    _IN_STREAMLIT = get_script_run_ctx(suppress_warning=True) is not None
except Exception:  # pragma: no cover - very old streamlit
    _IN_STREAMLIT = False

if _IN_STREAMLIT:
    main()
elif __name__ == "__main__":
    if "--smoke" in sys.argv:
        smoke()
    else:
        print("Run the UI with:  streamlit run dashboard/app.py   (or --smoke for a check)")
