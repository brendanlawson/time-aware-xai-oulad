"""Dashboard cảnh báo sớm cho giảng viên (Phase 6a) — XAI làm trung tâm.

UI mỏng trên các bundle đã huấn luyện — TOÀN BỘ logic nằm trong ``src/``
(load bundle, transform chống rò rỉ, SHAP) theo quy ước tách interface của nhóm.

Điểm nhấn thiết kế (bản 2 — thân thiện với giảng viên):
  * Tiếng Việt toàn bộ; tên đặc trưng dịch sang ngôn ngữ sư phạm
    ("Số ngày im lặng", "Điểm tích lũy có trọng số"...).
  * Giải thích từng sinh viên bằng CÂU CHỮ: top lý do kèm giá trị thật của em đó
    so với trung vị của lớp — không bắt giảng viên đọc biểu đồ kỹ thuật.
  * Lọc "còn đang học tại mốc t" bật mặc định (phát hiện dual-cohort của đề tài:
    không dẫn giảng viên đi liên hệ sinh viên đã rút môn).
  * Tab "Bức tranh toàn cục" cho câu chuyện XAI mức toàn khóa.

Chạy:
    streamlit run dashboard/app.py
Kiểm tra nhanh không cần UI (fail to nếu đường ống hỏng):
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

from src.config import (  # noqa: E402
    CHECKPOINT_MAP_PATH,
    CHECKPOINTS,
    FIGURES_DIR,
    RAW_DATA_DIR,
    TABLES_DIR,
)
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
MODELS = {"xgb": "XGBoost (khuyên dùng)", "lgbm": "LightGBM", "rf": "Random Forest"}

# --- Tên đặc trưng thân thiện (ngôn ngữ giảng viên) ---------------------------
FRIENDLY = {
    "days_since_last_activity": "Số ngày im lặng (không hoạt động)",
    "weighted_score_to_date": "Điểm tích lũy có trọng số",
    "mean_score_to_date": "Điểm trung bình các bài đã nộp",
    "n_assessments_submitted": "Số bài đã nộp",
    "not_submitted": "Từng bỏ hạn nộp bài",
    "total_clicks": "Tổng lượt truy cập VLE",
    "n_days_active": "Số ngày có học",
    "max_clicks_single_day": "Ngày học nhiều nhất (lượt click)",
    "mean_clicks_per_active_day": "Cường độ học mỗi ngày",
    "clicks_forumng": "Truy cập diễn đàn",
    "clicks_oucontent": "Truy cập bài giảng",
    "clicks_resource": "Truy cập tài liệu",
    "clicks_homepage": "Truy cập trang môn học",
    "clicks_quiz": "Làm quiz",
    "clicks_subpage": "Duyệt mục lục môn",
    "clicks_url": "Mở liên kết ngoài",
    "clicks_oucollaborate": "Học trực tuyến (collaborate)",
    "num_of_prev_attempts": "Số lần học lại môn",
    "studied_credits": "Tín chỉ đang đăng ký",
    "date_registration": "Ngày ghi danh (so với khai giảng)",
    "highest_education": "Trình độ đầu vào",
    "imd_band": "Mức khó khăn kinh tế (IMD)",
    "age_band": "Nhóm tuổi",
    "gender": "Giới tính",
    "disability": "Khuyết tật",
    "region": "Vùng",
    "code_module": "Môn học",
    "code_presentation": "Học kỳ",
}
# Các đặc trưng "nhiều hơn = học tốt hơn" (dùng để diễn giải cao/thấp)
COUNT_LIKE = {
    "total_clicks",
    "n_days_active",
    "clicks_forumng",
    "clicks_oucontent",
    "clicks_resource",
    "clicks_homepage",
    "clicks_quiz",
    "clicks_subpage",
    "clicks_url",
    "clicks_oucollaborate",
    "max_clicks_single_day",
    "mean_clicks_per_active_day",
    "n_assessments_submitted",
    "weighted_score_to_date",
    "mean_score_to_date",
}


def raw_feature_of(transformed: str) -> tuple[str, str | None]:
    """'num__total_clicks' -> ('total_clicks', None); 'nominal__code_module_DDD'
    -> ('code_module', 'DDD'). Trả (cột thô, giá trị one-hot nếu có)."""
    prefix, _, rest = transformed.partition("__")
    if prefix == "nominal":
        for col in ("code_module", "code_presentation", "region"):
            if rest.startswith(col + "_"):
                return col, rest[len(col) + 1 :]
        return rest, None
    return rest, None


def friendly_name(transformed: str) -> str:
    col, onehot = raw_feature_of(transformed)
    base = FRIENDLY.get(col, col)
    return f"{base} = {onehot}" if onehot else base


# --- Tầng dữ liệu (cache) ------------------------------------------------------
@st.cache_resource(show_spinner="Đang nạp mô hình ...")
def bundle(model_name: str, t: int) -> dict:
    return load_bundle(model_name, t)


@st.cache_resource(show_spinner="Đang dựng bộ giải thích SHAP ...")
def explainer(model_name: str, t: int):
    return shap_explain.build_explainer(bundle(model_name, t)["model"], None)


@st.cache_data(show_spinner="Đang chấm điểm toàn bộ lớp (chỉ chậm lần đầu) ...")
def score_cohort(model_name: str, t: int):
    """Chấm test split cố định tại mốc t. Trả (scores, X_raw, Xt, feat_names, medians)."""
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
    medians = X.median(numeric_only=True)  # trung vị lớp (giá trị thô) để so sánh
    return scores, X, np.asarray(Xt, dtype=float), list(b["feat_names"]), medians


def shap_row(model_name: str, t: int, Xt_row: np.ndarray, feat_names) -> pd.DataFrame:
    vals = shap_explain.compute_shap_values(explainer(model_name, t), Xt_row.reshape(1, -1))[0]
    df = pd.DataFrame({"feature": feat_names, "shap": vals})
    return df.reindex(df["shap"].abs().sort_values(ascending=False).index)


def reason_sentence(feat: str, shap_val: float, student_raw: pd.Series, medians: pd.Series) -> str:
    """Một câu tiếng Việt cho một lý do: giá trị của em đó vs trung vị lớp."""
    col, onehot = raw_feature_of(feat)
    name = FRIENDLY.get(col, col)
    up = shap_val > 0  # đẩy về phía NGUY CƠ
    arrow = "🔺 tăng nguy cơ" if up else "🟢 giảm nguy cơ"
    if onehot is not None:
        return f"**{name}: {student_raw.get(col, '?')}** — đặc thù môn/kỳ này {arrow}."
    val = student_raw.get(col, None)
    if col in medians.index and val is not None and pd.notna(val):
        med = medians[col]
        v = f"{val:,.0f}" if float(val) == int(float(val)) else f"{val:,.1f}"
        m = f"{med:,.0f}" if float(med) == int(float(med)) else f"{med:,.1f}"
        if col == "not_submitted":
            desc = "đã từng bỏ hạn nộp bài" if val >= 1 else "chưa bỏ hạn nộp bài nào"
            return f"**{name}**: {desc} — {arrow}."
        comp = "cao hơn" if val > med else ("thấp hơn" if val < med else "bằng")
        return f"**{name}**: {v} ({comp} trung vị lớp {m}) — {arrow}."
    return f"**{name}**: {val} — {arrow}."


def reasons_chart(top: pd.DataFrame) -> plt.Figure:
    d = top.iloc[::-1]
    labels = [friendly_name(f) for f in d["feature"]]
    fig, ax = plt.subplots(figsize=(6.5, 0.45 * len(d) + 0.8))
    ax.barh(labels, d["shap"], color=["#C0392B" if v >= 0 else "#2E7D32" for v in d["shap"]])
    ax.axvline(0, color="#888888", lw=0.8)
    ax.set_xlabel("Ảnh hưởng tới dự đoán  (đỏ → nguy cơ · xanh → an toàn)")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    return fig


@st.cache_data
def policy_presets() -> dict:
    """policy -> (threshold, val_precision, val_recall) cho XGBoost, điểm vận hành cuối khóa."""
    p = TABLES_DIR / "threshold_validation.csv"
    if not p.exists():
        return {}
    tv = pd.read_csv(p)
    tv = tv[tv.model == "xgb"]
    tv = tv[tv.t_percent == tv.t_percent.max()]  # ngưỡng hiệu chỉnh tại t=100
    return {
        r.policy: (float(r.threshold), float(r.val_precision), float(r.val_recall))
        for r in tv.itertuples()
    }


@st.cache_data
def reliability_row(t: int) -> dict:
    """recall/pr_auc điểm + 95% CI cho full / still-enrolled(active) / gap tại mốc t (xgb)."""
    p = TABLES_DIR / "bootstrap_ci.csv"
    if not p.exists():
        return {}
    ci = pd.read_csv(p)
    ci = ci[(ci.model == "xgb") & (ci.t_percent == t)]
    out = {}
    for cohort in ("full", "active", "gap"):
        for metric in ("recall", "pr_auc"):
            r = ci[(ci.cohort == cohort) & (ci.metric == metric)]
            if not r.empty:
                out[(cohort, metric)] = (
                    float(r.point.iloc[0]),
                    float(r.ci_lo.iloc[0]),
                    float(r.ci_hi.iloc[0]),
                )
    return out


@st.cache_data
def calibration_ece(t: int) -> float | None:
    p = TABLES_DIR / "calibration_metrics.csv"
    if not p.exists():
        return None
    c = pd.read_csv(p)
    r = c[c.t_percent == t]
    return float(r.ece.iloc[0]) if not r.empty else None


@st.cache_data
def parsimony5() -> tuple[list[str], float]:
    """Top-5 đặc trưng (theo ablation) và recall đạt được — câu chuyện gọn-để-vận-hành."""
    a = pd.read_csv(TABLES_DIR / "ablation_results.csv")
    r = a[a.k == 5].iloc[0]
    feats = [f.strip() for f in str(r["top_features"]).split(",")]
    return feats, float(r["recall"])


# --- Giao diện -----------------------------------------------------------------
def main() -> None:
    st.set_page_config(page_title="Cảnh báo sớm OULAD", page_icon="🎓", layout="wide")
    st.title("🎓 Cảnh báo sớm sinh viên nguy cơ — kèm giải thích")

    with st.sidebar:
        st.header("Thiết lập")
        st.markdown("**Mô hình vận hành: XGBoost** ✅")
        st.caption(
            "Đã chọn qua benchmark có kiểm định (Friedman + Wilcoxon-Holm trên 25 fit CV): "
            "dẫn đầu recall và cho SHAP chính xác trên cây."
        )
        model_name = "xgb"
        t = st.select_slider(
            "Tiến độ khóa học đã quan sát",
            options=list(CHECKPOINTS),
            value=40,
            format_func=lambda v: f"{v}%",
        )
        pol = policy_presets()
        nice = {
            "manual": "Tự chỉnh ngưỡng",
            "default(0.5)": "Mặc định (0.50)",
            "f1": "Cân bằng nhất (F1)",
            "youden": "Youden",
            "recall>=0.9": "Vét ≥90% SV nguy cơ (ưu tiên không bỏ sót)",
        }
        options = list(pol) + ["manual"]
        default_policy = "f1" if "f1" in pol else options[0]
        preset = st.selectbox(
            "Chính sách cảnh báo",
            options,
            index=options.index(default_policy),
            format_func=lambda k: nice.get(k, k),
            help="Ngưỡng được chọn trên tập validation (không đụng test), hiệu chỉnh tại cuối khóa.",
        )
        if preset == "manual":
            threshold = st.slider("Ngưỡng thủ công", 0.0, 1.0, 0.5, 0.01)
        else:
            threshold, vp, vr = pol[preset]
            st.caption(
                f"Ngưỡng **{threshold:.2f}** · trên validation: precision **{vp:.1%}**, "
                f"recall **{vr:.1%}** (không rò rỉ test)."
            )
        only_active = st.toggle("Chỉ hiện SV còn đang học (can thiệp được)", value=True)
        st.caption(
            "Tắt để xem cả những em đã rút môn trước mốc này — nhóm chỉ *ghi nhận* "
            "được chứ không *giúp* được nữa."
        )
        with st.expander("🔬 Chế độ nghiên cứu — đối chứng mô hình"):
            alt = st.selectbox(
                "Xem mô hình khác (không phải bản vận hành)",
                list(MODELS),
                format_func=MODELS.get,
                index=0,
            )
            if alt != "xgb":
                model_name = alt
                st.warning(
                    f"Đang xem **{MODELS[alt]}** để đối chứng — bản vận hành vẫn là XGBoost."
                )

    scores, X_raw, Xt, feat_names, medians = score_cohort(model_name, t)
    view = scores[scores.still_enrolled] if only_active else scores
    flagged = view[view.proba >= threshold].sort_values("proba", ascending=False)

    tab1, tab2 = st.tabs(["🧑‍🏫 Từng sinh viên (XAI cục bộ)", "🌍 Bức tranh toàn cục"])

    with tab1:
        tp = int(((view.proba >= threshold) & (view.y_true == 1)).sum())
        n_pos = int((view.y_true == 1).sum())
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("SV trong danh sách", f"{len(view):,}")
        c2.metric("Bị gắn cờ nguy cơ", f"{len(flagged):,}")
        c3.metric("Bắt đúng (backtest)", f"{tp / n_pos:.0%}" if n_pos else "–")
        c4.metric("Cờ chính xác (backtest)", f"{tp / len(flagged):.0%}" if len(flagged) else "–")

        rel = reliability_row(t) if model_name == "xgb" else {}
        if rel:

            def _mark(v: float) -> str:
                return "✅" if v >= 0.80 else "⚠️"

            st.markdown(
                "###### Độ tin cậy tại mốc này — backtest, 95% CI · chuẩn đạt khi recall ≥ 0.80"
            )
            k1, k2, k3 = st.columns(3)
            if ("active", "recall") in rel:
                p, lo, hi = rel[("active", "recall")]
                k1.metric(
                    f"{_mark(p)} Recall · nhóm còn học (số trung thực)",
                    f"{p:.3f}",
                    f"CI [{lo:.3f}, {hi:.3f}]",
                    delta_color="off",
                )
            if ("full", "recall") in rel:
                p, lo, hi = rel[("full", "recall")]
                k2.metric(
                    f"{_mark(p)} Recall · toàn bộ ghi danh",
                    f"{p:.3f}",
                    f"CI [{lo:.3f}, {hi:.3f}]",
                    delta_color="off",
                )
            if ("gap", "recall") in rel:
                p, lo, hi = rel[("gap", "recall")]
                k3.metric(
                    "Chênh do dân số (gap)",
                    f"{p:.3f}",
                    f"CI [{lo:.3f}, {hi:.3f}] · loại trừ 0",
                    delta_color="off",
                )

        if not only_active:
            gone = int((~scores.still_enrolled).sum())
            st.warning(
                f"⚠️ {gone:,} em trong danh sách đã rút môn trước mốc {t}% — "
                "chỉ ghi nhận được, không can thiệp được nữa."
            )

        left, right = st.columns([1, 1.3], gap="large")
        with left:
            st.subheader("Danh sách ưu tiên liên hệ")
            nice_tbl = flagged.head(300).copy()
            nice_tbl["Xác suất nguy cơ"] = nice_tbl["proba"]
            nice_tbl = nice_tbl.rename(
                columns={"id_student": "Mã SV", "code_module": "Môn", "code_presentation": "Kỳ"}
            )
            st.dataframe(
                nice_tbl[["Mã SV", "Môn", "Kỳ", "Xác suất nguy cơ"]],
                use_container_width=True,
                height=460,
                hide_index=True,
                column_config={
                    "Xác suất nguy cơ": st.column_config.ProgressColumn(
                        format="%.2f", min_value=0.0, max_value=1.0
                    )
                },
            )
            st.caption(f"Hiển thị tối đa 300 em đầu danh sách · mô hình huấn luyện tại mốc {t}%.")
            export = flagged.rename(
                columns={
                    "id_student": "ma_sv",
                    "code_module": "mon",
                    "code_presentation": "ky",
                    "proba": "xac_suat_nguy_co",
                }
            )[["ma_sv", "mon", "ky", "xac_suat_nguy_co"]]
            st.download_button(
                "⬇️ Tải danh sách ưu tiên (CSV)",
                data=export.to_csv(index=False).encode(
                    "utf-8-sig"
                ),  # utf-8-sig: Excel đọc tiếng Việt
                file_name=f"canh_bao_som_xgb_t{t}.csv",
                mime="text/csv",
                disabled=flagged.empty,
                use_container_width=True,
            )

        with right:
            st.subheader("Vì sao em này bị gắn cờ?")
            if flagged.empty:
                st.info("Không sinh viên nào vượt ngưỡng hiện tại.")
            else:
                pick = st.selectbox(
                    "Chọn sinh viên (gõ mã để tìm)",
                    flagged.index,
                    format_func=lambda i: f"SV {scores.loc[i, 'id_student']} · "
                    f"{scores.loc[i, 'code_module']}/{scores.loc[i, 'code_presentation']} "
                    f"· p={scores.loc[i, 'proba']:.2f}",
                )
                p = float(scores.loc[pick, "proba"])
                level = (
                    "🔴 NGUY CƠ CAO — nên liên hệ trong tuần"
                    if p >= 0.8
                    else "🟠 CẦN THEO DÕI — nhắc nhở sớm"
                    if p >= threshold
                    else "🟢 TẠM ỔN"
                )
                st.markdown(f"### {level}")
                st.progress(p, text=f"Xác suất nguy cơ: {p:.0%} (tính tại mốc {t}% khóa học)")

                sr = shap_row(model_name, t, Xt[pick], feat_names)
                student_raw = X_raw.loc[pick]
                st.markdown("**Lý do chính (so với mặt bằng lớp):**")
                for _, r in sr.head(4).iterrows():
                    st.markdown(
                        "- " + reason_sentence(r["feature"], r["shap"], student_raw, medians)
                    )
                st.pyplot(reasons_chart(sr.head(8)), use_container_width=True)
                st.caption(
                    f"Giải thích SHAP tính riêng cho em này, chỉ dùng dữ liệu tới mốc {t}%. "
                    "Đỏ = yếu tố đẩy về phía nguy cơ, xanh = kéo về phía an toàn."
                )
                with st.expander("Hồ sơ chi tiết (giá trị gốc)"):
                    prof = student_raw.rename(index=lambda c: FRIENDLY.get(c, c)).to_frame(
                        "Giá trị"
                    )
                    st.dataframe(prof, use_container_width=True)

    with tab2:
        st.subheader("Điều gì quyết định nguy cơ trên toàn khóa?")
        g1, g2 = st.columns([1.1, 1])
        with g1:
            imp = pd.read_csv(TABLES_DIR / "xai_shap_importance.csv").head(8)
            imp["Đặc trưng"] = imp["feature"].map(friendly_name)
            fig, ax = plt.subplots(figsize=(6.5, 4))
            d = imp.iloc[::-1]
            ax.barh(d["Đặc trưng"], d["importance"], color="#0F4C81")
            ax.set_xlabel("Mức ảnh hưởng trung bình (|SHAP|)")
            for spine in ("top", "right"):
                ax.spines[spine].set_visible(False)
            fig.tight_layout()
            st.pyplot(fig, use_container_width=True)
        with g2:
            st.markdown(
                """
**Cách đọc:** hai tín hiệu áp đảo là **số ngày im lặng** và **điểm tích lũy** —
đúng trực giác sư phạm: im lặng kéo dài + điểm thấp là cặp dấu hiệu giảng viên
thật cũng nhìn.

**Công bằng theo thiết kế:** không đặc trưng nhân khẩu học nào ở nhóm dẫn đầu
→ cảnh báo dựa trên **hành vi học tập**, không dựa lý lịch sinh viên.

**Độ tin cậy của giải thích** (đo định lượng trong đề tài):
- Ổn định khi đổi seed huấn luyện (Spearman ≈ 0.97).
- Không đổi câu chuyện theo cách xử lý mất cân bằng.
- Giải thích **thay đổi dần theo mốc thời gian** → mọi giải thích ở app này
  đều được gắn nhãn mốc t.
                """
            )
        feats5, rec5 = parsimony5()
        ece = calibration_ece(t)
        names5 = ", ".join(FRIENDLY.get(f, f) for f in feats5)
        st.info(
            f"**Gọn để vận hành:** chỉ **5 đặc trưng** ({names5}) đã đạt recall "
            f"{rec5:.3f} ≈ mô hình đầy đủ 49 cột → pipeline nhẹ, giải thích dễ hiểu."
        )
        if ece is not None:
            st.caption(
                f"Xác suất đã **hiệu chỉnh** (ECE tại mốc {t}% = {ece:.3f}): đọc được như "
                "mức rủi ro thực, không chỉ là thứ hạng — nền tảng cho các dải rủi ro 🔴🟠🟢 ở tab bên."
            )

        curve = FIGURES_DIR / "sensitivity_active_recall_xgb.png"
        if curve.exists():
            st.divider()
            st.subheader("Đoán sớm tới đâu thì tin được? (RQ1 — báo cáo kép)")
            st.image(str(curve), width="stretch")
            st.caption(
                "Đường trên: recall trên toàn bộ lượt ghi danh (đạt chuẩn 0.80 từ mốc 40%). "
                "Đường dưới: chỉ tính SV còn đang học — nhóm can thiệp được (chỉ đạt chuẩn ở cuối khóa). "
                "Dashboard này mặc định làm việc với nhóm dưới."
            )


def smoke() -> None:
    """Kiểm tra end-to-end đường ống chấm điểm + giải thích, không cần UI."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # ponytail: console Windows không vỡ tiếng Việt
    except Exception:
        pass
    scores, X_raw, Xt, feat_names, medians = score_cohort("xgb", 40)
    assert len(scores) == len(X_raw) == Xt.shape[0] > 6000
    assert Xt.shape[1] == len(feat_names)
    assert scores["proba"].between(0, 1).all()
    assert 0 < scores["still_enrolled"].sum() < len(scores)
    sr = shap_row("xgb", 40, Xt[0], feat_names)
    assert len(sr) == len(feat_names)
    sent = reason_sentence(sr.iloc[0]["feature"], sr.iloc[0]["shap"], X_raw.iloc[0], medians)
    assert sent and "**" in sent
    # mọi đặc trưng transformed phải dịch được sang tên thân thiện
    unfriendly = [f for f in feat_names if friendly_name(f) == f]
    assert not unfriendly, f"thiếu tên thân thiện: {unfriendly[:5]}"
    # các quyết định nghiên cứu đã wire vào UI phải có dữ liệu thật
    assert policy_presets().get("f1"), "thiếu chính sách ngưỡng validation"
    assert reliability_row(40).get(("active", "recall")), "thiếu bootstrap CI nhóm còn học"
    assert reliability_row(40).get(("gap", "recall")), "thiếu CI của gap dân số"
    ece = calibration_ece(100)
    assert ece is not None and 0 < ece < 0.1, "ECE hiệu chỉnh bất thường"
    f5, r5 = parsimony5()
    assert len(f5) == 5 and r5 > 0.9, "câu chuyện parsimony 5-đặc-trưng hỏng"
    print(
        f"SMOKE OK: {len(scores):,} rows | {int(scores.still_enrolled.sum()):,} còn học | "
        f"lý do mẫu: {sent[:80]}..."
    )


try:
    from streamlit.runtime.scriptrunner import get_script_run_ctx

    _IN_STREAMLIT = get_script_run_ctx(suppress_warning=True) is not None
except Exception:  # pragma: no cover
    _IN_STREAMLIT = False

if _IN_STREAMLIT:
    main()
elif __name__ == "__main__":
    if "--smoke" in sys.argv:
        smoke()
    else:
        print("Chạy UI:  streamlit run dashboard/app.py   (hoặc --smoke để kiểm tra nhanh)")
