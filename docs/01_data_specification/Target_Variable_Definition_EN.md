# Target Variable Definition and Withdrawn-over-Time Convention

*Binary at-risk label for early student-risk prediction on OULAD*

**DSP391m – Group 1 · Report 2 (Data Tasks), Chapter 3 · Work items STT 1 (whole team) & STT 26 (Son)**
*Reference: group agreement BB-B0-N1 (Step 0).*

---

## 1. Problem framing

The project is a **binary classification** task: at each course-progress checkpoint, predict whether a student is **at-risk**. No score regression is performed; only OULAD is used. The label is derived from `final_result` in `studentInfo` and is **fixed across all six checkpoints**.

## 2. Mapping `final_result` to the binary label

| `final_result` | Meaning | Group | Label (code) |
|---|---|---|---|
| Distinction | Passed with distinction | Pass | not-at-risk (0) |
| Pass | Passed | Pass | not-at-risk (0) |
| Fail | Failed the module | At-risk | at-risk (1) |
| Withdrawn | Withdrew from the module | At-risk | at-risk (1) |

```python
df["at_risk"] = df["final_result"].isin(["Fail", "Withdrawn"]).astype(int)
# 1 = at-risk (positive class to detect); 0 = not-at-risk
```

**Merging Distinction into Pass.** The task is binary; Distinction is a *better* outcome than Pass and is not a target for intervention. Merging keeps the class definition clear, avoids creating a tiny extra class, and stays aligned with the goal of *detecting risk* rather than *ranking achievement*.

## 3. Observed class distribution (this dataset, not the illustrative slide)

Measured on the 32,593 student–module–presentation records of `studentInfo`:

| Class | `final_result` values | Count | Share |
|---|---|---|---|
| not-at-risk (0) | Pass (12,361) + Distinction (3,024) | 15,385 | 47.2% |
| at-risk (1) | Fail (7,052) + Withdrawn (10,156) | 17,208 | **52.8%** |

The at-risk class is therefore a **slight majority** (≈52.8%); imbalance is **mild**. The "68/32" figure sometimes shown on course slides is **illustrative only** and must not be quoted as the dataset statistic. Even with mild imbalance, evaluation uses **PR-AUC and recall on the at-risk class**, because missing an at-risk student is the costly error (see STT 25).

## 4. Withdrawn-over-time convention — Option A (chosen)

At a checkpoint *t%*, a Withdrawn student may have left **before** or **after** the checkpoint day. The group adopted **Option A — fixed label, fixed population**:

1. Each student's label is **fixed** by `final_result` at every checkpoint (the label does not change with *t*).
2. The **student set is identical** across all six checkpoints and the test set, satisfying the fixed-test-set requirement (STT 8).
3. A Withdrawn student who left before checkpoint *t* is **kept** in the *t* dataset and **still labelled at-risk**. Their features naturally reflect only activity up to the withdrawal day, so engagement is very low — and this **decline in activity is the early-warning signal**, not a data error.
4. The time-aware cut function (STT 11) automatically removes any event dated after the checkpoint, so **no temporal leakage** is introduced.

**Acknowledged limitation.** At late checkpoints, early-withdrawing students have almost no activity and are easy to detect, which can make recall and PR-AUC optimistic. The report quantifies this limitation with the sensitivity analysis on the still-enrolled subpopulation described in Section 5 — the evaluation-side counterpart of the alternative *Option B (per-checkpoint censoring)*.

## 5. Two reading frames of the target (estimand clarification)

The fixed label of Option A supports two distinct estimands, and every headline metric must state which one it refers to.

1. **End-of-course outcome classification — primary benchmark frame.** The question "will this enrolment end in Fail or Withdrawn?" is well defined on all 32,593 enrolment records at every checkpoint. This is the frame in which results are comparable with the baseline literature (Adnan et al., 2021; Tomasevic et al., 2020), which likewise retains the full cohort, and it is the frame of the project's primary benchmark tables.

2. **Early warning for intervention — still-enrolled frame.** An intervention can only reach students who have not yet withdrawn, so the operational question "whom should a tutor contact at checkpoint *t*?" is meaningful only on the subpopulation still enrolled at the cutoff. Already at *t* = 10%, 4,833 of 32,593 enrolments have withdrawn before the cutoff (923 of them in the test set); for these records there is nothing left to predict — only to record.

**Measured consequence.** XGBoost recall on the at-risk class at *t* = 40/80/100% is 0.81/0.90/0.93 on the full cohort but 0.678/0.779/0.841 on the still-enrolled subgroup (`reports/tables/sensitivity_active_xgb.csv`, produced by `tools/sensitivity_active.py`). Against the recall ≥ 0.80 criterion of RQ1, the full cohort qualifies from *t* = 40%, whereas the still-enrolled subgroup qualifies only at *t* = 100%. Consistently, the strongest SHAP feature is `days_since_last_activity` (mean |SHAP| 3.57): on the full cohort, part of the model's strength is *detecting students who have already left*, not only *forecasting future risk*. This is **not leakage** — the label never enters the features, and the low activity of withdrawn students is genuine behaviour — it is a **population-definition issue**.

**Reporting rule.** Any statement of the form "predictions are reliable from *t* = 40%" must state the cohort it refers to. The project therefore reports both frames side by side: full-cohort results as the primary benchmark, still-enrolled results as the intervention-oriented sensitivity analysis.

## 6. Consequences for downstream work

Every work item that depends on "Step 0" inherits this definition: leakage rules (STT 12), schema and checkpoint map (STT 9, 10), split design (STT 21), and the documentation of source/ethics (STT 30). The target column name is `at_risk`; `final_result` is retained only as the raw source of the label.

## References

1. M. Adnan et al., "Predicting at-Risk Students at Different Percentages of Course Length for Early Intervention," *IEEE Access*, vol. 9, pp. 7519–7539, 2021.
2. N. Tomasevic, N. Gvozdenovic, S. Vranes, "An overview and comparison of supervised data mining techniques for student exam performance prediction," *Computers & Education*, vol. 143, art. 103676, 2020.
3. J. Kuzilek, M. Hlosta, Z. Zdrahal, "Open University Learning Analytics dataset," *Scientific Data*, vol. 4, art. 170171, 2017.
