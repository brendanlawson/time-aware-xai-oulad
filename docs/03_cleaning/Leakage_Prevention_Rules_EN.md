# Temporal Leakage Prevention Rules

*Rules that keep every checkpoint dataset honest about the information available at prediction time*

**DSP391m – Group 1 · Report 2 (Data Tasks), Chapter 3 · Work item STT 12 (Khoa)**
*Reference: group agreement BB-B0-N1 (Step 0). Enforced automatically by `tests/test_leakage.py`.*

---

## 1. What temporal leakage is

**Temporal (look-ahead) leakage** is the use of data generated *after* the prediction time. It inflates performance during development and disappears in deployment, where future data does not exist. Because this project predicts at six checkpoints (10–100% of course length), every feature at checkpoint *t* must be computable from data available **on or before** the checkpoint day. The checkpoint day per module-presentation is `round(module_presentation_length × t / 100)` (see `data/checkpoint_map.csv`).

## 2. The three rules

### Rule 1 — Drop assessment submissions dated after the checkpoint
Keep a submission only if `date_submitted ≤ cutoff_day`. A score handed in on day 120 cannot inform a day-100 prediction. Consequently `mean_score_to_date`, `weighted_score_to_date` and `n_assessments_submitted` accumulate **only** submissions up to the cutoff.

### Rule 2 — Drop VLE interactions dated after the checkpoint
Keep a clickstream row only if `date ≤ cutoff_day`. All engagement features (`total_clicks`, `n_days_active`, `clicks_*`, `max_clicks_single_day`, `mean_clicks_per_active_day`, `days_since_last_activity`) are aggregated from the cut clickstream. Implemented by `cut_at_checkpoint()` in `src/data/time_utils.py`.

### Rule 3 — Handle Withdrawn-before-checkpoint per Step 0 (Option A)
A student who withdrew before checkpoint *t* is **kept** and **labelled at-risk**; their features reflect only pre-withdrawal activity (Rules 1–2 already remove later events). The resulting low activity is a legitimate early-warning signal, not leakage. The label comes from `final_result` and is fixed across checkpoints, so it never leaks future outcome into the features. Keeping already-withdrawn students is nevertheless a **population choice with measurable consequences**: on the full cohort, part of the measured performance comes from re-identifying students who have already left, and at-risk recall on the still-enrolled subgroup is lower at every checkpoint. This violates no rule above — no label information enters the features — but it changes what the headline metrics mean. See the sensitivity analysis (`tools/sensitivity_active.py` → `reports/tables/sensitivity_active_xgb.csv`) and the estimand-clarification section of *Target_Variable_Definition* for the project's dual-reporting convention.

## 3. The supporting principle — fit on train only

Beyond the time axis, any component that *learns* from data (imputation statistics, encoders, scaler, resampling) must be fit on the **training fold only** and then applied to the test set (see STT 22). Fitting on the full dataset before splitting leaks test-set information into training and produces optimistic estimates.

## 4. Automated enforcement

`tests/test_leakage.py` asserts, for all six checkpoints, that no cut record has a date beyond its checkpoint day, on both the clickstream and the submissions; that record counts are non-decreasing in *t*; and that *t = 100%* retains all dated records. It also checks the split has no student overlap and preserves the class ratio, plus a test asserting the imputation median and winsorise thresholds are **learned on train only** and applied to test, plus a feature allow-list test (no leaky column reaches X) and a test that idle at *t = 100%* matches master. **Result: all automated leakage tests pass — see `tests/test_leakage.py`** (the suite is extended over time, so no fixed test count is quoted here).

## 5. Worked example (`AAA / 2013J`, length 268 days)

| t% | cutoff_day | Interactions kept (non-decreasing) |
|---|---|---|
| 10 | 27 | smallest |
| 40 | 107 | larger |
| 100 | 268 | all dated interactions |

The monotonic growth confirms the cut is applied correctly: more time elapsed ⇒ more (never fewer) records.

## References

1. M. Adnan et al., *IEEE Access*, vol. 9, pp. 7519–7539, 2021.
3. J. Kuzilek, M. Hlosta, Z. Zdrahal, *Scientific Data*, vol. 4, art. 170171, 2017.
