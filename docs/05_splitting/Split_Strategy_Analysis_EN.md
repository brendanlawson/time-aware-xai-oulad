# Data Splitting Strategy: Analysis and Selection

*Comparing splitting strategies and justifying the design for time-aware, imbalanced, grouped data*

**DSP391m – Group 1 · Report 2 (Data Tasks), Chapter 3 · Work item STT 21 (Duc)**

---

## 1. Why the split needs care here

Three properties of the data constrain the split:

- **Grouped** — a student (`id_student`) can appear in several module-presentations, so rows are not independent. A naive row split can place the same student in train and test (*group leakage*).
- **Imbalanced (mildly)** — the at-risk class is ~52.8%; a random split can still drift the test-set ratio and bias evaluation.
- **Time-aware** — six checkpoints share one comparison axis (RQ1), so the test set must be **identical** across checkpoints or the performance curve is not comparable.

## 2. Strategies compared

| Strategy | How it works | Pros | Cons |
|---|---|---|---|
| Single hold-out | One train/test cut | Simple, fast | High variance; depends on one partition |
| k-fold CV | k rotating validation folds | Uses all data; lower variance | k× cost; single seed still partition-dependent |
| Repeated k-fold | k-fold repeated over several seeds | Robust mean ± std; seed-independent | Highest cost |
| Nested CV | Inner CV for tuning, outer for estimate | Unbiased estimate with tuning | Very expensive; complex |

## 3. Selected design (per the proposal)

**Hold-out 20% test set + 5-fold cross-validation repeated over 5 seeds on the training set.**

- The **20% test set is fixed once**, by `id_student`, and reused at every checkpoint (STT 8) so the six points are comparable.
- On the remaining 80%, **5-fold × 5-seed** CV reduces variance from any single partition; metrics are reported as **mean ± standard deviation** across the 25 fits.
- Both the test split and the CV folds are **group-aware (by `id_student`) and stratified (by `at_risk`)** via `StratifiedGroupKFold` (see `src/evaluation/split_harness.py`).

This balances robustness and cost: repeated k-fold gives stable estimates, while a single fixed hold-out test set preserves comparability across checkpoints. Nested CV was judged unnecessarily expensive for the planned scope.

## 4. Reporting convention

Because the positive (at-risk) class is the one we must not miss, headline metrics are **PR-AUC** and **recall on the at-risk class**, reported as **mean ± std** over folds/seeds. Accuracy is reported only as a secondary figure (it is misleading under any imbalance).

## 5. Verified properties (this dataset)

Using the fixed 20% split on `master_raw` (32,593 rows): **0 students overlap** between train and test, and the at-risk rate is preserved (train ≈ 0.53, test ≈ 0.52, gap ≤ 0.02). These checks are asserted in `tests/test_leakage.py`.

## References

1. M. Adnan et al., *IEEE Access*, vol. 9, pp. 7519–7539, 2021.
2. N. Tomasevic, N. Gvozdenovic, S. Vranes, *Computers & Education*, vol. 143, art. 103676, 2020.
