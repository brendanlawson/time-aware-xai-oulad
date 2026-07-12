# 5. Imbalance Handling and Explanation Stability (RQ3, RQ2)

This section reports the two analyses that extend the checkpoint benchmark of Section 4 into the project's research contribution: a controlled study of what imbalance handling does to both predictive accuracy and explanation content (RQ3, Sections 5.1–5.3), and a quantitative assessment of the explanations themselves — what drives an at-risk flag, and how stable that account remains across random seeds, across explainers, and across the six course-progress checkpoints (RQ2, Sections 5.4–5.5).

## 5.1 The Imbalance Twist: At-Risk Is a Slight Majority

Most of the at-risk prediction literature treats the positive class as a scarce minority that resampling must rescue [3], [9]. Under this project's label mapping the situation is inverted: with at-risk = {Fail, Withdrawn}, the positive class covers 52.8% of enrolments, an imbalance ratio of only 1.12 — the at-risk class is a slight *majority*. This carries a consequence that is easy to overlook: SMOTE [9] and ADASYN oversample the minority class by default, so applied off-the-shelf to this dataset they synthesise additional *not-at-risk* students — the exact opposite of the "rescue the rare at-risk class" intuition carried over from textbook settings. The project detected this inversion early and documents it explicitly rather than letting the default behaviour pass unremarked.

Imbalance handling is therefore not needed here as a remedy — there is no rare class to rescue. Instead, RQ3 is reframed as a controlled robustness question: does the choice among four training regimes — no resampling, cost-sensitive class weighting, SMOTE, and ADASYN — materially change (a) the predictive metrics and (b) the explanation a tutor would be shown? Throughout the experiment, every resampling or weighting intervention is applied to the training partition only, after preprocessing has been fitted on the training data; the held-out test set is never resampled. Because the costly error remains the false negative — a missed at-risk student — at-risk recall and PR-AUC stay the primary metrics, exactly as in Section 4.

## 5.2 Predictive Accuracy under Four Strategies

Each of the five benchmark algorithms was retrained at the t = 100% checkpoint under all four strategies and scored once on the frozen held-out test set. The table below reports the headline model, XGBoost; the figure summarises all five models.

{{TBL:imbalance_xgb}}

{{FIG:imbalance_comparison|Held-out test metrics of the five benchmark models at t = 100% under the four imbalance-handling strategies (none, class weighting, SMOTE, ADASYN).}}

The differences are negligible. Across models and strategies, the largest spread on any primary metric (at-risk recall, F1, PR-AUC) is {{VAL:IMB_MAX_SPREAD}} — of the same order as the seed-to-seed variation observed in cross-validation, with no strategy consistently ahead. This is the expected behaviour at an imbalance ratio of 1.12: with both classes abundantly represented, neither synthetic oversampling nor loss reweighting has much room to move the decision boundary. The benchmark pipeline therefore simply retains the SMOTE step specified in the project proposal — a choice this comparison shows to be immaterial — while the alternative strategies serve as robustness checks (the Phase-2 progress deck reports the no-resampling baseline rows for the same reason). The accuracy half of RQ3 is thus answered: on OULAD under this label mapping, predictive performance is robust to the imbalance-handling choice.

## 5.3 Explanations under Four Strategies

Accuracy invariance alone does not establish robustness: two models can score identically while attributing their decisions to different features, and for an early-warning tool the explanation is part of the product. The explanation half of RQ3 therefore retrains the headline model (XGBoost at t = 100%) once per strategy on the same transformed training matrix, computes global SHAP importances on an identical sample of held-out test students, and compares the four resulting rankings pairwise with the same two measures used throughout the stability analyses: Jaccard overlap of the top-10 feature sets and Spearman correlation of the full rankings.

{{TBL:xai_strategies}}

Two observations follow from the table. First, the Spearman rank correlation is close to unity for every one of the six strategy pairs: the global importance ordering — which features matter, and roughly in what order — is essentially invariant to the imbalance strategy. Second, the top-10 Jaccard overlap varies moderately across pairs, indicating that the *tail* of the top-10 list shuffles mildly from one training regime to another while the dominant features stay in place. The explanation half of RQ3 therefore agrees with the accuracy half: a tutor would be told substantially the same story under any of the four training regimes, so the conclusions of Section 5.4 do not hinge on the resampling decision.

## 5.4 What Drives an At-Risk Flag

With robustness established, we turn to the content of the explanation. Global SHAP values are computed for the headline model with TreeExplainer, which is exact for tree ensembles rather than a sampling approximation [6]; the beeswarm plot shows per-student attributions with direction, and the bar chart ranks features by mean absolute SHAP value.

{{FIG:shap_summary_xgb_t100|SHAP beeswarm for XGBoost at t = 100%: each point is one test student, colour encodes the feature value, and the horizontal position shows how strongly that value pushes the prediction toward (right) or away from (left) the at-risk class.}}

{{FIG:shap_importance_xgb_t100|Global SHAP feature importance (mean absolute SHAP value) for XGBoost at t = 100%.}}

One feature dominates by a wide margin: `days_since_last_activity`, the length of the student's current silence in the VLE, followed by `weighted_score_to_date`, the cumulative weighted assessment score. The beeswarm confirms the directions a teacher would predict: long silences push strongly toward an at-risk flag, while a high running score pulls away from it, and the remaining contributors — submission counts, module identity, and per-activity click features — act in similarly plausible directions. This is an encouraging sanity check: the model's strongest signals are precisely the two indicators, disengagement and weak assessment performance, that human tutors already watch.

The dominance of a silence feature also connects directly to the dual-estimand reading of the target established in Section 3. On the full enrolment cohort, part of the model's measured strength consists of *recognising students who have already disengaged or withdrawn* rather than forecasting future risk — at t = 100%, recall is {{VAL:XGB_T100_RECALL}} on the full cohort versus {{VAL:ACTIVE_T100_RECALL}} on the still-enrolled subgroup — and `days_since_last_activity` is exactly the feature through which that detection operates. The explanation thus corroborates, from the model's inside, why every headline claim in this report is stated per cohort.

Global importances do not help a tutor with an individual student, which is where LIME [7] enters: it fits an interpretable local surrogate around a single prediction, producing a per-student "why" — the form in which an explanation is actually consumed in an intervention conversation, and the form served per student by the instructor dashboard (Appendix).

{{FIG:lime_local_example|LIME local explanation for one high-confidence at-risk prediction at t = 100%: the local surrogate's weights show which of this student's feature values raise the flagged risk and which lower it.}}

## 5.5 Stability across Seeds, Explainers, and Checkpoints

An explanation can support intervention decisions only if it is reproducible. Following the quantitative-stability methodology of Section 3 — the response to the qualitative-only assessment gap noted in prior reviews [3], [8] — stability is measured along three axes.

**Stability across seeds.** The headline model was retrained under five random seeds and re-explained. Across all seed pairs, the mean top-10 Jaccard overlap is {{VAL:SEED_JACCARD}} and the mean Spearman rank correlation is {{VAL:SEED_SPEARMAN}}. The near-perfect rank correlation means the global feature story is a property of the data and the model class, not an artefact of one training run — the basic trust guarantee an early-warning explanation needs.

**Agreement between explainers.** SHAP and LIME agree only partially: the Jaccard overlap of their global top-10 sets is {{VAL:SHAPLIME_JACCARD}}, computed on a limited LIME sample of test students. This is a finding, not a defect, and it has a clear methodological mechanism: the two explainers optimise different objectives. SHAP allocates exact Shapley contributions of the trained model itself, whereas LIME fits a local linear surrogate to predictions on randomly perturbed inputs — and its perturbation treats one-hot encoded categories as continuous variables, injecting additional noise. The two methods agree on the headline drivers but diverge in the mid-ranking. The project's policy is therefore to anchor all global claims on SHAP (exact for tree models), to use LIME as a per-student local cross-check, and to report the disagreement rather than silently selecting the more flattering explainer. The limited LIME sample is acknowledged as a limitation in Section 6.2.

**Stability across time.** Finally, explanations drift as the course progresses — and they should: early checkpoints contain little behaviour, so demographic and registration priors carry relatively more weight, while later checkpoints are dominated by engagement and performance signals. The figure below traces the drift across the six checkpoints.

{{FIG:xai_stability_drift|Explanation drift across the six checkpoints: top-10 Jaccard overlap and Spearman rank correlation for consecutive checkpoint pairs and for each checkpoint against the full-course (t = 100%) reference.}}

The drift is smooth and ordered: adjacent checkpoints correlate strongly, while the earliest views share only a small fraction of the full-course top-10. The explanation evolves gradually rather than jumping — evidence of a coherent underlying signal — but the early-course and end-of-course stories genuinely differ. The operational consequence is a presentation rule that the instructor dashboard already implements: every explanation shown to a tutor is labelled with the checkpoint at which it was computed, and explanations are never transferred across checkpoints.

Taken together, these results answer RQ2: explanations are highly stable to training randomness, partially consistent across explainers for identifiable methodological reasons, and smoothly time-varying — trustworthy, provided they are anchored on SHAP and carry their checkpoint label.

<!-- Drafted 2026-07-12 (owner: Khoa/Bình). All volatile metrics are {{...}} placeholders resolved by tools/build_final_report.py from reports/tables/*.csv after the renumber run; do not hand-type numbers here. -->
