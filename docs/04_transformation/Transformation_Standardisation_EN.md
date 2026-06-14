# Data Standardisation and Transformation: Variable Typing, Encoding, and Scaling Strategy

**DSP391m – Group 1 · Report 2 (Data Tasks), Chapter 3 · Task 3.4 — Standardisation & Transformation**

---

## Abstract

This report documents the variable typing catalogue, encoding decisions, and standardisation strategy implemented in `src/features/preprocessing.py` for the DSP391m capstone project (Group 1). The dataset, derived from the Open University Learning Analytics Dataset (OULAD), contains 28 raw and engineered features spanning clickstream interactions, demographic attributes, and academic performance indicators. Each feature is assigned to one of five type categories — numeric, ordinal, nominal, binary, or indicator — and processed by the corresponding sklearn-compatible transformer within a single `ColumnTransformer`. A strict anti-leakage protocol governs the order of operations: all encoders and the `StandardScaler` are fitted exclusively on the training fold and subsequently applied to both train and test sets. The transformation stage produces a 49-column dense feature matrix, verified free of missing values, with feature names retained in `snake_case` for downstream SHAP and LIME interpretability analysis.

---

## 1. Introduction

Effective machine learning pipelines require that raw feature values be converted into a numeric representation that is both mathematically appropriate for each model class and free of information leakage from held-out data. For the at-risk student prediction task in DSP391m, features originate from three distinct measurement scales: continuous and discrete counts from VLE clickstream logs, ordered categorical attributes collected at enrolment, and unordered categorical identifiers. Treating all features with a single encoding strategy — for example, applying `OneHotEncoder` to ordinal variables — would discard the rank information embedded in categories such as qualification level or deprivation band, inflating dimensionality without informational gain. Conversely, applying integer codes to nominal variables such as `region` would impose a spurious ordinal relationship. Section 2 enumerates the variable typing catalogue that resolves these distinctions. Section 3 details each encoding method and its technical rationale. Section 4 describes the standardisation step and its anti-leakage implementation. Section 5 presents the transformation pipeline order. Section 6 reports the verified output properties.

---

## 2. Variable Typing Catalogue

The 28 input features (excluding the target `at_risk` and identifier columns `id_student`, `code_module`, `code_presentation`) are partitioned into five types. The type assignment drives the choice of transformer in the subsequent `ColumnTransformer`.

**Table 1. Variable Typing and Encoding Assignment**

| Type | Count | Variables | Encoder / Scaler |
|------|-------|-----------|-----------------|
| Numeric | 19 | `num_of_prev_attempts`, `studied_credits`, `date_registration`, `total_clicks`, `n_days_active`, `clicks_forumng`, `clicks_oucontent`, `clicks_resource`, `clicks_homepage`, `clicks_oucollaborate`, `clicks_quiz`, `clicks_subpage`, `clicks_url`, `max_clicks_single_day`, `mean_clicks_per_active_day`, `days_since_last_activity`, `mean_score_to_date`, `n_assessments_submitted`, `weighted_score_to_date` | `StandardScaler` (some features log1p / winsorize-transformed in the outlier-handling stage before scaling) |
| Ordinal | 3 | `highest_education`, `imd_band`, `age_band` | `OrdinalEncoder` with explicit, fixed category order |
| Nominal | 3 | `region`, `code_module`, `code_presentation` | `OneHotEncoder` |
| Binary | 2 | `gender`, `disability` | Direct 0/1 mapping via custom `BinaryEncoder` |
| Indicator | 1 | `not_submitted` | Passthrough (already 0/1 from feature engineering) |

**Notes on numeric sub-classifications.** Within the 19 numeric features, VLE click counts (`total_clicks`, `n_days_active`, and all eight `clicks_<type>` columns, plus `max_clicks_single_day` and `mean_clicks_per_active_day`) exhibit strong right-skew and are pre-transformed with `log1p` before `StandardScaler` is applied. The variables `studied_credits`, `num_of_prev_attempts`, `weighted_score_to_date`, and `days_since_last_activity` are winsorised at the 1st and 99th percentiles. Three variables — `mean_score_to_date`, `n_assessments_submitted`, and `date_registration` — receive no outlier transformation.

---

## 3. Encoding Methods and Rationale

### 3.1 OrdinalEncoder (ordinal features)

Ordinal variables possess an intrinsic rank ordering that carries predictive information. Encoding them as integers 0, 1, 2, … k−1 preserves this ordering with no increase in dimensionality. `OneHotEncoder` would destroy the rank relationship; therefore it is explicitly excluded for these variables.

The exact category orders fixed in `ORDINAL_ORDERS` are:

- `highest_education`: `No Formal quals` < `Lower Than A Level` < `A Level or Equivalent` < `HE Qualification` < `Post Graduate Qualification`
- `imd_band`: `Unknown` < `0-10%` < `10-20` < `20-30%` < `30-40%` < `40-50%` < `50-60%` < `60-70%` < `70-80%` < `80-90%` < `90-100%`
- `age_band`: `0-35` < `35-55` < `55<=`

The configuration `handle_unknown='use_encoded_value'` with `unknown_value=-1` ensures that any category appearing in the test set but absent from the training set is encoded as −1 rather than raising an exception. Tree-based models (Random Forest, XGBoost, LightGBM) tolerate this sentinel value without issue.

### 3.2 OneHotEncoder (nominal features)

Nominal variables (`region`, `code_module`, `code_presentation`) carry no inherent order. Assigning integer codes would imply a false ranking — for example, suggesting one region is "greater than" another. `OneHotEncoder` creates one binary column per category value, making the encoding permutation-invariant.

Configuration: `handle_unknown='ignore'` (unseen test categories produce an all-zero row, preventing runtime errors); `sparse_output=False` (dense array for pipeline compatibility); `drop=None` (all columns retained). The `drop=None` choice is intentional: dropping a reference column would prevent SHAP waterfall plots and LIME explanations from attributing importance to the dropped category, reducing post-hoc interpretability.

### 3.3 BinaryEncoder (binary features)

Two features take exactly two values:

- `gender`: M → 1, F → 0
- `disability`: Y → 1, N → 0

A custom `BinaryEncoder` class (sklearn-compatible `BaseEstimator` / `TransformerMixin`) implements this fixed lookup table. No fitting is required since the mapping is a project-defined constant; the `fit` method is a no-op retained for `ColumnTransformer` compatibility.

### 3.4 Passthrough (indicator feature)

The `not_submitted` flag is produced by feature engineering as a 0/1 integer and requires no further transformation. It is passed through the `ColumnTransformer` via the `'passthrough'` transformer to preserve its presence in the output feature matrix.

---

## 4. Standardisation (Scaling)

### 4.1 StandardScaler

All 19 numeric features are standardised to zero mean and unit variance using sklearn's `StandardScaler` (z-score normalisation: x′ = (x − μ) / σ). After the log1p or winsorise transformations applied in the outlier-handling stage, each numeric column is independently shifted and scaled so that its training-set distribution has mean 0 and standard deviation 1.

### 4.2 Rationale

VLE click counts range from zero to several thousand; score variables span 0 to 100. Without standardisation, models that compute distances or gradient magnitudes (Logistic Regression, Artificial Neural Networks) are dominated by the high-magnitude clickstream variables. Although tree-based models (Random Forest, XGBoost, LightGBM) split on feature thresholds and are theoretically scale-invariant, `StandardScaler` is applied uniformly across all numeric features to ensure pipeline consistency: a single `preprocess()` call produces a feature matrix valid for any model class without further intervention.

### 4.3 Anti-Leakage Implementation

The scaler is fitted exclusively on the training fold. The fitted parameters (`scaler.mean_` and `scaler.var_`) are computed solely from training observations. The `.transform()` method — which applies the stored mean and variance — is then called on both the training and test arrays. The `.fit_transform()` shorthand is never called on the full dataset. This prevents any statistical information from the test set from influencing the transformation applied to training data, which would constitute data leakage and produce over-optimistic generalisation estimates.

**Table 2. Encoding and Scaling Summary**

| Transformer | Features | Key Configuration |
|-------------|----------|------------------|
| `StandardScaler` | 19 numeric | Fit on train only; `scaler.mean_` from train |
| `OrdinalEncoder` | 3 ordinal | Explicit category lists; `handle_unknown='use_encoded_value'`, `unknown_value=-1` |
| `OneHotEncoder` | 3 nominal | `handle_unknown='ignore'`, `sparse_output=False`, `drop=None` |
| `BinaryEncoder` (custom) | 2 binary | Fixed lookup: M/Y→1, F/N→0 |
| `passthrough` | 1 indicator | No transformation |

---

## 5. Transformation Pipeline Order

The full anti-leakage pipeline order, as implemented in `preprocess()`, is:

1. **Train/test split** — performed outside this module, prior to any fitting.
2. **`handle_missing(X_train)`** — imputation logic derived from training data; the same rules are applied to the test set without re-fitting.
3. **`handle_outliers(X_train)`** — log1p and winsorise transformations applied; test set is transformed with the same deterministic rules.
4. **`ColumnTransformer.fit(X_train)`** — all transformers (StandardScaler, OrdinalEncoder, OneHotEncoder, BinaryEncoder) are fitted on the training fold only.
5. **`ColumnTransformer.transform(X_train)` and `.transform(X_test)`** — the fitted transformer is applied to both sets.
6. **Resampling (SMOTE/ADASYN)** — applied exclusively to the transformed training array; the test array is never resampled.

This sequence is cross-referenced in the Preprocessing Sequence document (Document 07).

---

## 6. Output Properties

The fitted `ColumnTransformer` is serialised to `scaler.pkl` via `joblib.dump()` for reproducibility and deployment. The `preprocess()` function returns four objects: the transformed training array, the transformed test array, the fitted transformer, and a list of feature names obtained from `ct.get_feature_names_out()`.

Verified output properties:

- **Column count**: 49 columns after encoding (19 numeric + 3 ordinal + one-hot expansion of region/code_module/code_presentation + 2 binary + 1 indicator).
- **Missing values**: zero NaN values in either output array after transformation.
- **Feature names**: fully retained in `snake_case` prefixed by transformer name (e.g., `num__total_clicks`, `nominal__region_East Anglian Region`) for unambiguous attribution in SHAP waterfall plots and LIME feature importance displays.

---

## 7. Feature Naming and Downstream Explainability

The consistent use of descriptive `snake_case` column names throughout `preprocessing.py` (e.g., `mean_clicks_per_active_day`, `weighted_score_to_date`, `days_since_last_activity`) ensures that SHAP and LIME outputs are self-documenting. When the `ColumnTransformer` is configured with `verbose_feature_names_out=True`, each output column carries a transformer-prefix that identifies its origin, enabling analysts to trace any individual feature importance value back to its raw source variable without consulting a separate data dictionary. This design choice directly supports the interpretability requirements of the at-risk prediction use case, in which educators and advisors must understand which student behaviours or demographic attributes drive individual risk flags.

---

*Prepared by DSP391m Group 1. All transformation logic references `src/features/preprocessing.py`, committed to the project repository (branch: main).*
