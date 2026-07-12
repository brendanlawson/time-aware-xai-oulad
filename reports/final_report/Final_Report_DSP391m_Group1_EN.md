% Time-Aware Explainable Machine Learning for Early At-Risk Student Prediction on OULAD
% DSP391m — Group 1, FPT University · Supervisor: Nguyễn Thị Hoàng Yến


---

# 1. Introduction and Background

Virtual Learning Environments (VLEs) now mediate a large share of higher-education teaching, and every action a student takes — opening a resource, submitting an assessment, visiting a forum — leaves a digital trace. Failure and drop-out nevertheless remain persistent problems in online and distance education, while the behavioural data captured by learning management systems is still largely under-used for timely intervention. Educational Data Mining and Learning Analytics have responded with a rich body of work on student performance prediction, typically framed as binary at-risk classification, from systematic comparisons of supervised algorithms [1] to prediction at multiple points of course length [2].

Existing predictive models, however, exhibit three recurring limitations. The first is opacity: the strongest models — ensembles and deep neural networks — behave as black boxes, so instructors cannot see why a student is flagged and cannot act with confidence; systematic reviews of explainable student-performance prediction identify this as a central obstacle to adoption [3]. The second is lateness: most studies predict at or near the end of the course, when intervention is no longer effective [2]. The third is class imbalance, where this project adds an honest qualification. In the literature the at-risk class is usually a minority that models drift away from; under this project's label mapping ({Fail, Withdrawn} versus {Pass, Distinction}), the at-risk class is in fact a slight majority on OULAD — 52.8% of enrolments, an imbalance ratio of 1.12 — so imbalance handling is studied here as a controlled robustness question (RQ3), not as the rescue of a rare class.

The study is conducted on the Open University Learning Analytics Dataset (OULAD) [4], a public, anonymised benchmark released by The Open University. OULAD comprises 32,593 enrolments (student × module-presentation records from 28,785 distinct students) across 22 module-presentations, organised in seven relational tables that cover three feature groups: demographics, engagement (a VLE clickstream of approximately 10.6 million rows), and performance (assessment records). The binary target maps final_result to at-risk = {Fail, Withdrawn} against not-at-risk = {Pass, Distinction}. Features are computed cumulatively at six course-progress checkpoints (10/20/40/60/80/100% of course length), and five algorithms — Logistic Regression, Random Forest, XGBoost, LightGBM, and an artificial neural network (ANN) — are benchmarked at every checkpoint.

Three research questions guide the work:

- RQ1. At different course-progress checkpoints (10–100% of course length), which algorithm gives the best at-risk prediction on OULAD, and how early can a prediction be considered reliable?
- RQ2. How consistent are the explanations produced by SHAP and LIME for the same model, and how does their stability change across time and across imbalance-handling strategies?
- RQ3. How does imbalance handling (SMOTE / ADASYN / class weighting) affect both predictive accuracy and explanation quality?

These questions target an empty cell exposed by the group's concept-centric literature review [5] of 27 representative papers (2019–2026): time-aware prediction, explainable AI, and imbalance handling have each been studied in isolation, but never simultaneously on OULAD. The project makes four contributions: (i) an integrated time-aware XAI framework that couples checkpoint-based prediction with SHAP [6] and LIME [7] explanations at each checkpoint, not previously done end-to-end on OULAD; (ii) an extended OULAD benchmark that adds ensemble methods (Random Forest, XGBoost, LightGBM) to the comparison that Tomasevic et al. [1] did not include; (iii) a quantitative explanation-stability methodology (Jaccard top-k agreement, Spearman rank correlation, and the standard deviation of feature importances across seeds), addressing the qualitative-only gap noted in prior reviews [3], [8]; and (iv) an optional instructor dashboard that turns the predictions into a practical early-warning tool. Because the fixed end-of-course label supports two distinct estimands, every headline result is reported on both the full enrolment cohort (the frame comparable with prior literature) and the still-enrolled cohort at each checkpoint (the frame in which an intervention can actually reach the student).

The remainder of this report is organised as follows. Section 2 reviews the related literature and derives the research gap. Section 3 describes the dataset, the target definition, and the time-aware, leakage-safe experimental methodology. Section 4 reports the benchmarking and time-aware prediction results (RQ1). Section 5 presents the imbalance-handling and explanation-stability analyses (RQ3, RQ2). Section 6 discusses limitations and concludes.

# 2. Literature Review

This review is organised around four concepts rather than individual authors, following the concept-centric approach of Webster and Watson [5]: at-risk prediction on OULAD, explainable AI in education, class-imbalance handling, and the research gap at their intersection.

## 2.1 At-Risk Prediction on OULAD

OULAD itself was published as a dataset paper by Kuzilek et al. [4]: seven relational tables covering 32,593 student registrations on 22 module-presentations of The Open University, with demographic profiles, VLE clickstream interactions, and summative assessment records, anonymised at source and released under an open licence. Its public availability has made it the most widely used benchmark for reproducible at-risk prediction studies.

Tomasevic et al. [1] carried out a systematic comparison of supervised data-mining techniques for exam performance prediction on OULAD, using a subset of the DDD module (the DDD_2013J and DDD_2014B presentations, 3,166 students after excluding non-exam-takers). Their central findings are that an ANN achieved the highest accuracy when engagement (VLE clicks) and performance (assessment scores) data were combined, and that demographic attributes did not show significant additional influence once behavioural and performance features were available — a result that directly informs our feature prioritisation. Methodologically, rows with missing values were dropped and evaluation used random 80:20 (or 60:20:20) splits; notably, the comparison did not include gradient-boosted ensemble methods, a gap our benchmark closes.

Adnan et al. [2] provide the template for time-aware prediction: on the full OULAD, they trained models on cumulative demographic, clickstream, and assessment features computed at course start and at 20/40/60/80/100% of course length, evaluated with 10-fold cross-validation (an 85/15 split for their deep model) using accuracy, precision, recall, F-score, and AUC. Their key result is that predictions reach acceptable reliability from roughly 40–60% of course length — early enough for intervention — which is the empirical basis of our checkpoint schedule (we add a 10% checkpoint). For imbalance they merged classes (Pass with Distinction, Fail with Withdrawn) rather than resampling.

Across these base studies a shared methodological weakness is worth noting: none applies a group-aware split keyed on the student identifier, so the same student can appear in both training and test data; our pipeline removes this leakage risk with a student-level stratified split.

## 2.2 Explainable AI in Education

The two dominant post-hoc explanation techniques are SHAP and LIME. SHAP (Lundberg and Lee [6]) unifies several additive feature-attribution methods on a Shapley-value foundation, yielding both global feature importance and local per-prediction attributions with consistency guarantees. LIME (Ribeiro et al. [7]) explains an individual prediction by fitting an interpretable surrogate model in the local neighbourhood of the instance, independently of the underlying classifier.

In education, Alamri and Alharbi [3] systematically reviewed explainable student-performance prediction models and found SHAP and LIME to be the dominant techniques, while observing that most studies assess their explanations only qualitatively — typically by visually inspecting feature-importance plots. Gunasekara and Saarela [8] applied both techniques to an ANN and a decision tree on a three-module OULAD subset (AAA/BBB/CCC; 17,091 samples described by 14 aggregated attributes), evaluated with 5-fold cross-validation repeated 50 times; their assessment of the resulting local explanations, however, likewise remains mainly qualitative. The gap these works leave open is precisely the one RQ2 addresses: a rigorous quantitative measure of explanation stability — how consistently an explainer reproduces the same importance ranking across seeds, time points, or training regimes — is largely absent from the educational literature. Purely visual inspection cannot detect the subtle instabilities that would undermine an instructor's trust in an early-warning explanation.

## 2.3 Class-Imbalance Handling

The canonical remedy for skewed class distributions is SMOTE (Chawla et al. [9]), which synthesises new minority-class examples by interpolating between neighbouring minority instances; adaptive variants such as ADASYN concentrate the synthesis on harder regions of the minority manifold. [TODO: the proposal's reference list contains no ADASYN citation; add He et al. (2008) only if the final template permits adding references beyond the approved list.] Class weighting offers a resampling-free alternative by rescaling the loss.

The OULAD literature is inconsistent in how it treats imbalance. Adnan et al. [2] merged outcome classes (Pass+Distinction versus Fail+Withdrawn) instead of resampling; Tomasevic et al. [1] excluded non-exam-takers and rows with missing values, leaving imbalance otherwise unaddressed; and the one study in our reviewed corpus that tackles imbalance head-on — a DNN combined with SMOTE and ADASYN, reporting clearly improved minority-class detection (proposal Appendix A, item 19) — does not use OULAD at all. No study we reviewed measures what resampling does to explanations.

This project's own position is deliberately measured. Under our label mapping the at-risk class is a slight majority (52.8%), so the imbalance is mild and resampling is not needed to rescue a rare class; RQ3 instead treats SMOTE, ADASYN, and class weighting as controlled robustness interventions, measuring their effect on both predictive metrics and explanation stability. Because the costly error remains the false negative — a missed at-risk student — recall on the at-risk class and PR-AUC serve as the primary evaluation metrics throughout.

## 2.4 Research Gap and Positioning

Following Webster and Watson [5], the group surveyed 30 readings (five per member), corresponding to 27 independent papers from 2019–2026 after removing internal duplicates, and organised them into five themes: predictive modelling, time-aware prediction, XAI, data challenges, and the broader learning-analytics context. The papers were then cross-tabulated in a concept matrix whose empty cells expose the gap directly. The simplified matrix below, adapted from the proposal (Table 2, empirical studies only), shows the three axes that matter here:

| Study | OULAD | Time-aware | XAI | Imbalance handling |
| --- | --- | --- | --- | --- |
| Tomasevic et al. (2020) [1] | Yes | Yes | — | — |
| Adnan et al. (2021) [2] | Yes | Yes | — | — |
| Gunasekara & Saarela (2025) [8] | Yes | — | SHAP + LIME | — |
| DNN with resampling (corpus item 19) | — | — | — | SMOTE + ADASYN |
| This project | Yes | Yes | SHAP + LIME | SMOTE / ADASYN / class weighting |

Four gaps follow, each mapped to a research question. First, time-aware prediction and XAI have not been integrated: the time-aware studies [1], [2] provide no explanations, while the XAI study [8] considers no multiple time points (RQ1, RQ2). Second, there is no consistent comparison of ANNs and modern ensembles within a single pipeline on the same OULAD data (RQ1, RQ2). Third, explanation stability has not been evaluated quantitatively; assessments remain predominantly qualitative [3], [8] (RQ2). Fourth, the interaction between imbalance handling and explanation quality has not been studied on OULAD (RQ3). No existing work fills all three axes — time-aware prediction, post-hoc explanation, and imbalance handling — simultaneously on OULAD; this project occupies exactly that empty cell, and adds the dual-cohort reporting frame and student-level leakage-safe splitting absent from the base studies.

# References

[1] N. Tomasevic, N. Gvozdenovic, and S. Vranes, "An overview and comparison of supervised data mining techniques for student exam performance prediction," *Computers & Education*, vol. 143, art. no. 103676, 2020.

[2] M. Adnan et al., "Predicting at-risk students at different percentages of course length for early intervention using machine learning models," *IEEE Access*, vol. 9, pp. 7519–7539, 2021.

[3] H. Alamri and B. Alharbi, "Explainable student performance prediction models: A systematic review," *IEEE Access*, vol. 9, pp. 33132–33143, 2021.

[4] J. Kuzilek, M. Hlosta, and Z. Zdrahal, "Open University Learning Analytics dataset," *Scientific Data*, vol. 4, art. no. 170171, 2017.

[5] J. Webster and R. T. Watson, "Analyzing the past to prepare for the future: Writing a literature review," *MIS Quarterly*, vol. 26, no. 2, pp. xiii–xxiii, 2002.

[6] S. M. Lundberg and S.-I. Lee, "A unified approach to interpreting model predictions," in *Proc. Advances in Neural Information Processing Systems (NeurIPS)*, 2017, pp. 4768–4777.

[7] M. T. Ribeiro, S. Singh, and C. Guestrin, "'Why should I trust you?' Explaining the predictions of any classifier," in *Proc. 22nd ACM SIGKDD Int. Conf. on Knowledge Discovery and Data Mining*, 2016, pp. 1135–1144.

[8] S. Gunasekara and M. Saarela, "Explainable AI in education: Techniques and qualitative assessment," *Applied Sciences*, vol. 15, no. 3, art. no. 1239, 2025.

[9] N. V. Chawla, K. W. Bowyer, L. O. Hall, and W. P. Kegelmeyer, "SMOTE: Synthetic minority over-sampling technique," *Journal of Artificial Intelligence Research*, vol. 16, pp. 321–357, 2002.

---

Drafted 2026-07-12 for the final report (owner: Sơn); numbers cross-checked against README/docs; format: paste into the Word template.


---

# 3. Data and Methodology

This section describes the dataset (3.1), the target and its two estimands (3.2), the engineered features (3.3), the time-aware checkpointing scheme (3.4), the leakage-prevention rules (3.5), the frozen split and cross-validation design (3.6), and the preprocessing pipeline (3.7). Every design decision is documented in the repository and, wherever possible, enforced by automated tests.

## 3.1 Dataset

The study uses the Open University Learning Analytics Dataset (OULAD) [4], a public, anonymised snapshot released by The Open University under the Creative Commons Attribution 4.0 (CC-BY 4.0) licence; the fixed download guarantees that every researcher works from byte-identical files. OULAD consists of seven relational tables — studentInfo, studentRegistration, studentVle, vle, studentAssessment, assessments, and courses — covering 32,593 enrolments (28,785 distinct students) on 22 module-presentations. The unit of analysis is one enrolment, uniquely identified by the composite key (id_student, code_module, code_presentation); all tables are joined on this key, and post-join verification confirms that every left join preserves exactly 32,593 rows with zero duplicate keys. The behavioural core is the studentVle clickstream of 10,655,280 rows, each recording a student's daily interaction count with one VLE material; its date column and studentAssessment's submission dates are the architectural foundation of the time-aware design in Section 3.4.

One property of the clickstream deserves explicit documentation. The raw studentVle table has no unique key, and 787,170 rows (7.4%) are exact duplicates of another row across all columns; since each row is already a per-day aggregate, the schema cannot distinguish a double-logging artefact from a legitimately repeated record. The pipeline therefore keeps these rows and lets the checkpoint aggregation accumulate them: deleting one copy would be an unverifiable guess about which record is "real", and the baseline studies [1], [2] likewise work from the undeduplicated tables, keeping our click-derived features comparable. Possible over-counting of click totals is accepted and documented as a source-data limitation rather than silently "repaired".

## 3.2 Target Definition and the Two Estimands

The binary target maps final_result from studentInfo: at_risk = 1 for {Fail, Withdrawn} and 0 for {Pass, Distinction}. Distinction is merged into Pass because the task is risk detection, not achievement ranking. Under this mapping the at-risk class is a slight majority — 52.8% of enrolments — so imbalance is mild and is studied as a controlled robustness question (RQ3), not as the rescue of a rare class.

For withdrawal over time the group adopted Option A — fixed label, fixed population: each enrolment's label is fixed by final_result at every checkpoint, and the student set is identical across all six checkpoints. A student who withdrew before checkpoint *t* is kept in the *t* dataset and still labelled at-risk; the temporal cut removes all post-withdrawal events, so their features legitimately reflect only pre-withdrawal activity, and the resulting decline in engagement is the early-warning signal, not a data error.

This fixed label, however, supports two distinct estimands. The first is end-of-course outcome classification — "will this enrolment end in Fail or Withdrawn?" — well defined on all 32,593 enrolments at every checkpoint and comparable with the baseline literature [1], [2]. The second is early warning for intervention — "whom should a tutor contact at checkpoint *t*?" — meaningful only on the subpopulation still enrolled at the cutoff, because an intervention cannot reach a student who has already left. On the full cohort, part of any model's measured strength is detecting students who have already withdrawn rather than forecasting future risk; this is not leakage — the label never enters the features — but a population-definition issue. Hence the project's reporting rule: every reliability claim states its cohort, and each headline result is reported on both frames — the full cohort as the primary benchmark, the still-enrolled cohort as the intervention-oriented sensitivity analysis (Section 4).

## 3.3 Feature Engineering

Twenty-eight raw features are engineered per enrolment, in three groups. The demographic and context group (11 features) is static: gender, region, highest_education, imd_band, age_band, disability, num_of_prev_attempts, studied_credits, date_registration, and the presentation identifiers code_module and code_presentation. The engagement group (13 features) is aggregated from the clickstream: total_clicks, n_days_active, eight per-activity-type counts (forum, content, resource, homepage, collaboration, quiz, subpage, URL), max_clicks_single_day, mean_clicks_per_active_day, and days_since_last_activity. The performance group (4 features) is aggregated from assessment submissions: mean_score_to_date, weighted_score_to_date, n_assessments_submitted, and the binary indicator not_submitted, which flags enrolments with no submission by the cutoff so that an imputed zero score is never conflated with a genuine zero-score submission.

All time-dependent features are cutoff-driven: at checkpoint *t*, only clickstream and submission records dated on or before the checkpoint day enter the aggregation, so each feature answers "what was known about this student at *t*". One defect in this logic was found and fixed during the audit: assessments banked from a previous presentation were counted as due but not as submitted, incorrectly setting not_submitted for 78 of 32,593 enrolments (0.24%) at *t* = 100%; the fix is covered by a regression test, and all result tables are recomputed in the report-freeze renumber run (Appendix 7.2).

## 3.4 Time-Aware Checkpointing

Course lengths differ across the 22 module-presentations, so checkpoints are defined in relative course progress. For each module-presentation and each *t* in {10, 20, 40, 60, 80, 100}%, the checkpoint day is cutoff_day = round(module_presentation_length × t / 100), materialised once in a committed checkpoint map. Six checkpoint datasets are built by truncating the time-indexed tables at each cutoff and recomputing all aggregations; the roster is fixed by design — all six datasets contain the same 32,593 enrolments, so the performance curve compares identical populations that differ only in the information available. The schedule extends Adnan et al. [2] with a 10% checkpoint to probe the earliest practical warning point. Exploratory analysis confirms the premise: the class separability of the strongest features grows monotonically with course progress — precisely the earliness-reliability trade-off that RQ1 quantifies.

![Class separability (|Cohen's d|) of leading features across the six course-progress checkpoints. Discrimination grows with elapsed course time, motivating the time-aware checkpoint design and the earliness-reliability trade-off examined in RQ1.](D:/dsp/reports/figures/time_discrimination_curve.png)

## 3.5 Leakage Prevention

Four rules keep every checkpoint dataset honest about the information available at prediction time. Rule 1: an assessment submission is kept only if date_submitted ≤ cutoff_day. Rule 2: a clickstream row is kept only if date ≤ cutoff_day. Rule 3: a student who withdrew before checkpoint *t* is kept and labelled at-risk per Option A; because the label is derived solely from final_result and never enters the features, this violates no information constraint (its estimand consequences are handled in Section 3.2). Rule 4: any component that learns from data — imputation statistics, outlier thresholds, encoders, the scaler, any resampler — is fit on the training fold only and applied unchanged to the test fold.

These rules are enforced automatically rather than by discipline. The test suite (21 automated tests, run with pytest) asserts, at every checkpoint, that no retained clickstream or submission record postdates its cutoff; that record counts are non-decreasing in *t* and *t* = 100% retains all dated records; that the split has zero student overlap and preserves the class ratio; that imputation and winsorisation statistics are learned on train only; and that a feature allow-list blocks any leaky column (such as final_result or date_unregistration) from reaching the model matrix. The banked-assessment fix of Section 3.3 is pinned by its own regression test, and all tests must pass before any modelling step runs.

## 3.6 Train/Test Split and Cross-Validation Design

Three properties constrain the split: the data are grouped (a student can appear in several module-presentations, so a naive row split leaks students across the partition), mildly imbalanced, and time-aware (the test set must be identical across all six checkpoints for the performance curve to be comparable). The selected design is a fixed 20% hold-out test set plus 5-fold cross-validation repeated over 5 seeds on the remaining 80%, with metrics reported as mean ± standard deviation over the 25 fits; both the hold-out and the CV folds are group-aware by id_student and stratified by at_risk via StratifiedGroupKFold, under the global seed 42.

The split is derived once and frozen: the canonical list of 5,756 test students is committed to the repository, and the split script is guarded so that it only loads this list and never re-derives it — re-derivation under a different library version would silently change the partition and invalidate every published number. The verified properties hold identically on the master table and all six checkpoints: 26,104 training rows and 6,489 test rows (5,756 students), zero student overlap, and a preserved at-risk ratio (train ≈ 0.53, test ≈ 0.52). Because the costly error is the missed at-risk student, the headline metrics throughout are PR-AUC and recall on the at-risk class; accuracy is secondary.

## 3.7 Preprocessing

Preprocessing follows a strict split-first order — split, then missing values, then outliers, then encoding and scaling, then resampling — so that no statistic can flow from the test set into training.

![The anti-leakage preprocessing sequence: group-aware split first, then missing-value handling, outlier transformation, encoding and scaling — each fit on the training fold only — with resampling applied to the training fold alone.](D:/dsp/reports/figures/preprocessing_sequence.png)

Missing values are handled per variable: imd_band gaps become an explicit "Unknown" category at rank 0 of the ordinal scale; missing assessment aggregates are filled with 0 and flagged by not_submitted, because a missing score at *t* means "no submission yet" and is itself predictive signal; date_registration is imputed with the training-fold median. Outliers are detected by the IQR rule on the training fold and treated without deleting a single row: log1p compresses the right-skewed click counts, and winsorisation at the 1st/99th percentiles clips the remaining heavy-tailed variables. Encoding and scaling are performed by a single ColumnTransformer fitted on the training fold: a StandardScaler over the 19 numeric features, an OrdinalEncoder with fixed category orders for the 3 ordinal features, a OneHotEncoder (no dropped reference column, so SHAP and LIME can attribute importance to every category) for the 3 nominal features, a fixed 0/1 mapping for the 2 binary features, and passthrough for not_submitted — expanding 28 raw features into a 49-column dense matrix with snake_case names for downstream explainability. Every learned statistic is captured in a stats dictionary serialised with each model bundle and re-applied verbatim at inference, so training and deployment share one transformation path.

Resampling, when used, runs strictly inside the training fold after transformation; the test set always reflects the real class distribution. One direction-of-effect caveat is flagged here: because the at-risk class is a slight majority under this label mapping, a default-configured SMOTE oversamples the not-at-risk class rather than the class of interest — a consequence of the label design that the RQ3 experiments in Section 5 make explicit.


---

# 4. Model Benchmarking and Time-Aware Results (RQ1)

This section answers RQ1: which candidate algorithm gives the best at-risk prediction on OULAD, and how early a prediction can be considered reliable. A checkpoint is deemed *reliable* when the model reaches both recall ≥ 0.80 and PR-AUC ≥ 0.80 on the at-risk class of the held-out test set, and — following the reporting rule of Section 3 — every earliness claim states its cohort: the full enrolment cohort (comparable with the baseline literature) or the still-enrolled cohort (the population an intervention can actually reach).

## 4.1 Candidate Models and Configuration

Five algorithms spanning three model families were benchmarked. Logistic Regression is the standard linear reference, intrinsically interpretable through its coefficients. Random Forest represents the bagged-tree family, robust to noise and outliers with little tuning. XGBoost represents gradient-boosted trees, still the strongest general-purpose family for tabular data, and — decisive for this project — it supports exact SHAP TreeExplainer attributions [6], which the explanation layer of Section 5 requires. LightGBM is a second boosting implementation optimised for speed, a within-family control. Finally, an artificial neural network (a multilayer perceptron with two hidden layers of 64 and 32 neurons, at most 500 epochs, early stopping) represents the non-linear, non-tree family. Covering three families ensures the ranking is not an artefact of one inductive bias, and all five algorithms appear in the OULAD base studies, so the results remain comparable with the literature; in particular, adding the ensemble methods closes the gap left by the comparison of Tomasevic et al. [1].

Configuration follows a minimal-intervention principle: near-default settings for every model. Logistic Regression only raises the iteration cap to 1,000 for convergence; Random Forest and LightGBM keep library defaults; XGBoost uses the histogram tree method with log-loss as its evaluation metric. All five models share random seed 42, so the comparison is fair and exactly reproducible. No hyperparameter tuning was performed at this selection stage — tuning one candidate more carefully than another would bias the ranking toward whichever model received the most attention. Tuning is deferred to Section 4.5, after a candidate has been selected on equal terms.

## 4.2 Training and Evaluation Protocol

Every model passes through the same four-step protocol. First, the frozen student-level split of the 100% checkpoint is loaded — the committed test set of 6,489 enrolment rows from 5,756 students, with zero student overlap between train and test and the full automated leakage test suite passing. Second, all preprocessing (median imputation, winsorisation thresholds, categorical encoders, feature scaler) is fitted on the training partition only and then applied to the test partition. Third, the model is fitted on the training data and predicts on the untouched held-out test set. Fourth, seven metrics are computed — recall on the at-risk class, precision, F1, PR-AUC, ROC-AUC, balanced accuracy, and the Brier score for probability quality — and models are ranked recall-first.

The recall-first choice is a cost argument, not a convention: missing an at-risk student forfeits the chance to intervene, whereas a false alarm costs only a tutor conversation. Accuracy is deliberately demoted because, with the at-risk class a slight majority, it can flatter a trivial classifier; PR-AUC complements recall as the threshold-free summary of the precision–recall trade-off on the positive class. Finally, the headline figures reported here are the *baseline, no-resampling* results: Section 5 applies four imbalance-handling strategies to exactly this protocol, so the before–after comparison for RQ3 is well defined.

## 4.3 Benchmark at t = 100%

Table | model   |   roc_auc |   pr_auc |     f1 |   recall |   precision |   balanced_acc |   brier |
|:--------|----------:|---------:|-------:|---------:|------------:|---------------:|--------:|
| ann     |    0.9868 |   0.9897 | 0.9477 |   0.9259 |      0.9705 |         0.9477 |  0.0404 |
| lgbm    |    0.9889 |   0.9913 | 0.9511 |   0.9295 |      0.9736 |         0.9511 |  0.0368 |
| logreg  |    0.9857 |   0.9890 | 0.9464 |   0.9171 |      0.9776 |         0.9471 |  0.0414 |
| rf      |    0.9868 |   0.9896 | 0.9466 |   0.9165 |      0.9788 |         0.9475 |  0.0405 |
| xgb     |    0.9872 |   0.9902 | 0.9503 |   0.9298 |      0.9718 |         0.9503 |  0.0391 | reports the full seven-metric comparison on the held-out test set at the final checkpoint, and Figure ![Baseline benchmark of the five candidate models at t = 100% on the held-out test set (recall, F1, PR-AUC, ROC-AUC per model; no resampling, shared seed 42).](D:/dsp/reports/figures/model_benchmark_baseline.png) visualises the four principal metrics per model.

The table shows XGBoost at the top of the recall-first ranking, with recall 0.930 and PR-AUC 0.990 on the at-risk class. Two observations matter more than the winner's identity. First, the tree-based models — XGBoost, LightGBM, Random Forest — track each other closely across all seven metrics, with LightGBM marginally ahead on the composite ranking metrics; the boosting family as a whole, not one implementation, dominates the benchmark. Second, Logistic Regression, although last, remains within a few points of the leaders, indicating that the engineered features carry a strong, largely linearly separable signal on which the ensembles add a real but modest increment. Figure ![Confusion matrix of the selected model on the held-out test set at t = 100% at the default decision threshold.](D:/dsp/reports/figures/confusion_default_t100.png) shows the error profile of the leading model at the default threshold.

Because the gaps between models are small, the honest question is whether this ranking is trustworthy or an accident of one particular data split. The next subsection answers it with two layers of verification.

## 4.4 Reliability of the Ranking

The first layer is repeated cross-validation on the training partition only: 5-fold CV over 5 seeds, i.e., 25 fits per model, with the preprocessing pipeline re-fitted inside every fold to exclude fold-level leakage. Table | model   |   recall_mean |   recall_std |   f1_mean |   f1_std |   pr_auc_mean |   pr_auc_std |
|:--------|--------------:|-------------:|----------:|---------:|--------------:|-------------:|
| lgbm    |        0.9295 |       0.0060 |    0.9516 |   0.0036 |        0.9907 |       0.0008 |
| xgb     |        0.9309 |       0.0047 |    0.9507 |   0.0032 |        0.9901 |       0.0008 |
| rf      |        0.9202 |       0.0051 |    0.9489 |   0.0030 |        0.9889 |       0.0009 |
| ann     |        0.9245 |       0.0081 |    0.9463 |   0.0038 |        0.9891 |       0.0009 |
| logreg  |        0.9180 |       0.0054 |    0.9452 |   0.0033 |        0.9887 |       0.0010 | summarises the results as mean ± standard deviation per model and metric. The table shows XGBoost leading CV recall at 0.9309 ± 0.0047, with LightGBM immediately behind; the standard deviations are small across the board, and the CV ranking reproduces the held-out ranking of Table | model   |   roc_auc |   pr_auc |     f1 |   recall |   precision |   balanced_acc |   brier |
|:--------|----------:|---------:|-------:|---------:|------------:|---------------:|--------:|
| ann     |    0.9868 |   0.9897 | 0.9477 |   0.9259 |      0.9705 |         0.9477 |  0.0404 |
| lgbm    |    0.9889 |   0.9913 | 0.9511 |   0.9295 |      0.9736 |         0.9511 |  0.0368 |
| logreg  |    0.9857 |   0.9890 | 0.9464 |   0.9171 |      0.9776 |         0.9471 |  0.0414 |
| rf      |    0.9868 |   0.9896 | 0.9466 |   0.9165 |      0.9788 |         0.9475 |  0.0405 |
| xgb     |    0.9872 |   0.9902 | 0.9503 |   0.9298 |      0.9718 |         0.9503 |  0.0391 | — the single-split benchmark is not an outlier.

The second layer is statistical testing on the 25 paired CV folds. Table | metric   |   k_models |   n_blocks |   friedman_stat |   p_value | significant_0.05   | best_model   |   mean_rank_best |
|:---------|-----------:|-----------:|----------------:|----------:|:-------------------|:-------------|-----------------:|
| recall   |          5 |         25 |         73.8431 |    0.0000 | True               | xgb          |           1.4800 |
| f1       |          5 |         25 |         83.8397 |    0.0000 | True               | lgbm         |           1.3600 |
| pr_auc   |          5 |         25 |         82.6154 |    0.0000 | True               | lgbm         |           1.0800 |
| roc_auc  |          5 |         25 |         77.6761 |    0.0000 | True               | lgbm         |           1.0400 | reports the Friedman test per metric: the null hypothesis of equal performance is rejected far below the 0.05 level for every metric, so the small observed differences are systematic rather than noise. Post-hoc pairwise Wilcoxon signed-rank tests with Holm correction sharpen the picture: XGBoost is significantly better on recall than each of the other four models, while LightGBM leads the composite metrics (F1, PR-AUC, ROC-AUC). The choice follows the objective of the task: given the recall-first framing of early warning and the exact TreeExplainer attributions required by the explanation phase (Section 5), XGBoost is selected as the primary candidate for all subsequent analyses.

## 4.5 Hyperparameter Tuning

With the candidate fixed, a hyperparameter search was run at t = 100%; Table | model   |   t_percent |   cv_best_pr_auc |   default_pr_auc |   tuned_pr_auc |   default_recall |   tuned_recall |   default_f1 |   tuned_f1 |
|:--------|------------:|-----------------:|-----------------:|---------------:|-----------------:|---------------:|-------------:|-----------:|
| xgb     |          40 |           0.9485 |           0.9428 |         0.9479 |           0.8107 |         0.8042 |       0.8484 |     0.8519 |
| xgb     |         100 |           0.9910 |           0.9902 |         0.9914 |           0.9298 |         0.9274 |       0.9503 |     0.9507 |
| lgbm    |          40 |           0.9476 |           0.9473 |         0.9473 |           0.8095 |         0.8110 |       0.8543 |     0.8534 |
| lgbm    |         100 |           0.9910 |           0.9913 |         0.9910 |           0.9295 |         0.9301 |       0.9511 |     0.9517 | compares the tuned configuration against the near-default baseline. The honest conclusion is that tuning does not meaningfully improve the model: the table shows a marginal gain on the probability-ranking metric and no improvement — indeed a slight decrease — on recall, the primary metric. The gain does not justify the complexity and reduced reproducibility of a bespoke configuration, so the near-default configuration of Section 4.1 is retained for every result in this report. This is consistent with the benchmark itself: when five differently biased learners sit within a few points of one another, the feature signal, not the estimator configuration, is the binding constraint.

## 4.6 Time-Aware Performance and RQ1 — Dual-Cohort Answer

The selected protocol was then repeated at all six checkpoints (10/20/40/60/80/100% of course length) on the same frozen test students. Table |   t_percent | model   |   recall |   pr_auc |   roc_auc |     f1 | reliable   |
|------------:|:--------|---------:|---------:|----------:|-------:|:-----------|
|          10 | xgb     |   0.7192 |   0.8644 |    0.8319 | 0.7474 | False      |
|          20 | lgbm    |   0.7651 |   0.9073 |    0.8800 | 0.8001 | False      |
|          40 | xgb     |   0.8107 |   0.9428 |    0.9215 | 0.8484 | True       |
|          60 | xgb     |   0.8703 |   0.9684 |    0.9568 | 0.8964 | True       |
|          80 | lgbm    |   0.8990 |   0.9827 |    0.9768 | 0.9280 | True       |
|         100 | xgb     |   0.9298 |   0.9902 |    0.9872 | 0.9503 | True       | lists the best model per checkpoint with its test metrics and a reliability flag, and Figures ![At-risk recall of the best model per checkpoint across the six course-progress checkpoints, full test cohort; the horizontal line marks the recall ≥ 0.80 reliability criterion.](D:/dsp/reports/figures/time_aware_recall.png) and ![PR-AUC of the best model per checkpoint across the six checkpoints, full test cohort.](D:/dsp/reports/figures/time_aware_pr_auc.png) plot the corresponding curves. The table shows LightGBM narrowly ahead at the two earliest checkpoints — both below the reliability criterion — and XGBoost ahead from t = 40% onward. On the full enrolment cohort, recall crosses the 0.80 criterion at t = 40% (reaching 0.811) and rises monotonically to 0.930 at course end, with PR-AUC comfortably above its criterion over the same range. This trajectory is consistent with the 40–60% reliability window reported by Adnan et al. [2] on the same dataset.

The full cohort is, however, only one of the two estimands defined in Section 3. Because the at-risk label includes withdrawal and the enrolment population is held fixed across checkpoints, the test set at every checkpoint contains students who have already withdrawn before the cutoff — 923 test enrolments have left before the earliest checkpoint at t = 10%, and the count grows at each later cutoff. For these records the model is recording an outcome that has already happened, not forecasting one. Table |   t_percent |   full_recall |   active_recall |   full_pr_auc |   active_pr_auc |   withdrawn_already_gone |
|------------:|--------------:|----------------:|--------------:|----------------:|-------------------------:|
|     10.0000 |        0.7192 |          0.6311 |        0.8644 |          0.7546 |                 923.0000 |
|     20.0000 |        0.7604 |          0.6492 |        0.8999 |          0.7877 |                1130.0000 |
|     40.0000 |        0.8107 |          0.6782 |        0.9428 |          0.8462 |                1437.0000 |
|     60.0000 |        0.8703 |          0.7490 |        0.9684 |          0.8950 |                1687.0000 |
|     80.0000 |        0.8969 |          0.7792 |        0.9808 |          0.9235 |                1859.0000 |
|    100.0000 |        0.9298 |          0.8412 |        0.9902 |          0.9559 |                1953.0000 | therefore re-scores the same XGBoost predictions on the still-enrolled subpopulation at each checkpoint, and Figure ![XGBoost at-risk recall per checkpoint on the full test cohort versus the still-enrolled subpopulation, with the recall ≥ 0.80 criterion marked; the gap between the curves quantifies the contribution of already-withdrawn students.](D:/dsp/reports/figures/sensitivity_active_recall_xgb.png) plots the two recall curves side by side. The table shows a substantial, systematic gap: on the still-enrolled cohort, recall is 0.678 at t = 40% and 0.779 at t = 80%, and only reaches 0.841 — crossing the criterion — at t = 100%. The same qualitative shape is reproduced by LightGBM, so the finding is not specific to one model.

The dual-cohort answer to RQ1 is therefore stated in two parts, always reported together. On the full enrolment cohort — the frame in which the base studies [1], [2] operate — XGBoost is the best model from t = 40% onward and predictions are reliable from t = 40% of course length. On the still-enrolled cohort — the frame in which a tutor can still intervene — the same criterion is met only at course end, and mid-course predictions, while informative, fall short of the reliability bar.

Two clarifications guard against misreading this result. First, it is not data leakage: the label never enters the features, and the near-total inactivity of an early-withdrawn student is genuine observed behaviour. Second, it is a *population-definition* insight: part of the full-cohort performance at later checkpoints comes from recognising students who have already left — legitimate for end-of-course outcome classification, but not early forecasting. Making this distinction explicit, rather than reporting only the more flattering frame, is itself a contribution of this study, since neither base study separates the two populations.

## 4.7 Operating Threshold Chosen on Validation

A deployed early-warning system needs a decision threshold, and choosing it on the test set would optimistically bias every reported metric. The protocol here selects thresholds on out-of-fold validation predictions from 5-fold cross-validation on the training partition, freezes them, and scores the test set exactly once per frozen threshold. Table | policy       |   threshold |   val_precision |   val_recall |   val_f1 |   test_precision |   test_recall |   test_f1 |
|:-------------|------------:|----------------:|-------------:|---------:|-----------------:|--------------:|----------:|
| default(0.5) |      0.5000 |          0.9718 |       0.9301 |   0.9505 |           0.9718 |        0.9298 |    0.9503 |
| f1           |      0.5600 |          0.9766 |       0.9263 |   0.9508 |           0.9754 |        0.9262 |    0.9502 |
| youden       |      0.5600 |          0.9766 |       0.9263 |   0.9508 |           0.9754 |        0.9262 |    0.9502 |
| recall>=0.9  |      0.8600 |          0.9929 |       0.9010 |   0.9447 |           0.9931 |        0.9002 |    0.9444 | reports each policy's validation-chosen threshold with its validation and test metrics, and Figure ![Precision, recall, and F1 on the validation predictions as a function of the decision threshold, with the selected policy thresholds marked.](D:/dsp/reports/figures/threshold_tuning.png) shows the underlying validation trade-off curves.

Two results stand out. First, the F1-optimal policy selects a threshold of 0.56, nearly coinciding with the conventional default of 0.5, and the validation metrics transfer to the test set with negligible drift; this retrospectively confirms that the default-threshold results of the preceding subsections were not the product of tuning on the test set. Second, the table includes an institutional policy alternative: if a faculty mandates recall of at least 0.9 on the at-risk class, the validation-chosen threshold of 0.86 delivers that recall on the test set at a precision of 0.993 — an operating point in which flagged students are almost always genuinely at risk.

## 4.8 Subgroup Fairness

The project's ethics documentation commits to reporting disaggregated performance across demographic groups, and this subsection honours that commitment with measurements rather than assurances. For the selected model at t = 100% and the default threshold, recall and false-positive rate were computed separately for every level of six demographic attributes — gender, region, index-of-multiple-deprivation (IMD) band, highest prior education, age band, and declared disability — restricted to subgroups with at least 50 test members. Table | attribute         |   n_levels |   recall_min |   recall_max |   recall_gap |   fpr_gap |
|:------------------|-----------:|-------------:|-------------:|-------------:|----------:|
| imd_band          |         11 |       0.8941 |       0.9599 |       0.0658 |    0.0464 |
| region            |         13 |       0.9091 |       0.9502 |       0.0411 |    0.0385 |
| highest_education |          5 |       0.9264 |       0.9565 |       0.0301 |    0.0526 |
| gender            |          2 |       0.9147 |       0.9409 |       0.0262 |    0.0021 |
| disability        |          2 |       0.9279 |       0.9446 |       0.0167 |    0.0210 |
| age_band          |          2 |       0.9183 |       0.9342 |       0.0159 |    0.0070 | summarises the within-attribute range of both metrics.

The table shows that the largest recall gap across all attributes is 6.6 percentage points, observed on imd_band, with the other attributes exhibiting smaller ranges; false-positive-rate gaps are of a similarly modest order. No subgroup is severely under-served: no demographic group falls dramatically below the overall recall level, and the recall for students who declare a disability is not below that of their counterparts. These gaps are reported as observed disparities at a single checkpoint and threshold, not as a certification of fairness; a deployment should monitor the same disaggregated metrics continuously, with per-group detail retained in the repository for audit.

---

*Drafted 2026-07-12 (owner: Khoa). All model, threshold, and fairness numbers appear as VAL/TBL/FIG placeholders and are resolved from `reports/tables/*.csv` and `reports/figures/` by the report builder after the renumber checklist (SO_TAY section 6) has been run; only structural constants (5 algorithms, 6 checkpoints, seed 42, 25 CV fits, test 6,489 rows / 5,756 students, reliability criterion recall ≥ 0.80 & PR-AUC ≥ 0.80) are typed literally.*


---

# 5. Imbalance Handling and Explanation Stability (RQ3, RQ2)

This section reports the two analyses that extend the checkpoint benchmark of Section 4 into the project's research contribution: a controlled study of what imbalance handling does to both predictive accuracy and explanation content (RQ3, Sections 5.1–5.3), and a quantitative assessment of the explanations themselves — what drives an at-risk flag, and how stable that account remains across random seeds, across explainers, and across the six course-progress checkpoints (RQ2, Sections 5.4–5.5).

## 5.1 The Imbalance Twist: At-Risk Is a Slight Majority

Most of the at-risk prediction literature treats the positive class as a scarce minority that resampling must rescue [3], [9]. Under this project's label mapping the situation is inverted: with at-risk = {Fail, Withdrawn}, the positive class covers 52.8% of enrolments, an imbalance ratio of only 1.12 — the at-risk class is a slight *majority*. This carries a consequence that is easy to overlook: SMOTE [9] and ADASYN oversample the minority class by default, so applied off-the-shelf to this dataset they synthesise additional *not-at-risk* students — the exact opposite of the "rescue the rare at-risk class" intuition carried over from textbook settings. The project detected this inversion early and documents it explicitly rather than letting the default behaviour pass unremarked.

Imbalance handling is therefore not needed here as a remedy — there is no rare class to rescue. Instead, RQ3 is reframed as a controlled robustness question: does the choice among four training regimes — no resampling, cost-sensitive class weighting, SMOTE, and ADASYN — materially change (a) the predictive metrics and (b) the explanation a tutor would be shown? Throughout the experiment, every resampling or weighting intervention is applied to the training partition only, after preprocessing has been fitted on the training data; the held-out test set is never resampled. Because the costly error remains the false negative — a missed at-risk student — at-risk recall and PR-AUC stay the primary metrics, exactly as in Section 4.

## 5.2 Predictive Accuracy under Four Strategies

Each of the five benchmark algorithms was retrained at the t = 100% checkpoint under all four strategies and scored once on the frozen held-out test set. The table below reports the headline model, XGBoost; the figure summarises all five models.

| strategy     |   roc_auc |   pr_auc |     f1 |   recall |   precision |   balanced_acc |   brier |
|:-------------|----------:|---------:|-------:|---------:|------------:|---------------:|--------:|
| ADASYN       |    0.9872 |   0.9903 | 0.9486 |   0.9292 |      0.9688 |         0.9484 |  0.0386 |
| SMOTE        |    0.9872 |   0.9902 | 0.9503 |   0.9298 |      0.9718 |         0.9503 |  0.0391 |
| class_weight |    0.9877 |   0.9905 | 0.9499 |   0.9295 |      0.9712 |         0.9498 |  0.0388 |
| none         |    0.9873 |   0.9903 | 0.9508 |   0.9307 |      0.9719 |         0.9507 |  0.0385 |

![Held-out test metrics of the five benchmark models at t = 100% under the four imbalance-handling strategies (none, class weighting, SMOTE, ADASYN).](D:/dsp/reports/figures/imbalance_comparison.png)

The differences are negligible. Across models and strategies, the largest spread on any primary metric (at-risk recall, F1, PR-AUC) is 0.0069 — of the same order as the seed-to-seed variation observed in cross-validation, with no strategy consistently ahead. This is the expected behaviour at an imbalance ratio of 1.12: with both classes abundantly represented, neither synthetic oversampling nor loss reweighting has much room to move the decision boundary. The benchmark pipeline therefore simply retains the SMOTE step specified in the project proposal — a choice this comparison shows to be immaterial — while the alternative strategies serve as robustness checks (the Phase-2 progress deck reports the no-resampling baseline rows for the same reason). The accuracy half of RQ3 is thus answered: on OULAD under this label mapping, predictive performance is robust to the imbalance-handling choice.

## 5.3 Explanations under Four Strategies

Accuracy invariance alone does not establish robustness: two models can score identically while attributing their decisions to different features, and for an early-warning tool the explanation is part of the product. The explanation half of RQ3 therefore retrains the headline model (XGBoost at t = 100%) once per strategy on the same transformed training matrix, computes global SHAP importances on an identical sample of held-out test students, and compares the four resulting rankings pairwise with the same two measures used throughout the stability analyses: Jaccard overlap of the top-10 feature sets and Spearman correlation of the full rankings.

| strategy_a   | strategy_b   |   jaccard_top10 |   spearman |
|:-------------|:-------------|----------------:|-----------:|
| none         | class_weight |          0.5385 |     0.9739 |
| none         | smote        |          0.6667 |     0.9708 |
| none         | adasyn       |          0.8182 |     0.9674 |
| class_weight | smote        |          0.6667 |     0.9709 |
| class_weight | adasyn       |          0.6667 |     0.9641 |
| smote        | adasyn       |          0.8182 |     0.9744 |

Two observations follow from the table. First, the Spearman rank correlation is close to unity for every one of the six strategy pairs: the global importance ordering — which features matter, and roughly in what order — is essentially invariant to the imbalance strategy. Second, the top-10 Jaccard overlap varies moderately across pairs, indicating that the *tail* of the top-10 list shuffles mildly from one training regime to another while the dominant features stay in place. The explanation half of RQ3 therefore agrees with the accuracy half: a tutor would be told substantially the same story under any of the four training regimes, so the conclusions of Section 5.4 do not hinge on the resampling decision.

## 5.4 What Drives an At-Risk Flag

With robustness established, we turn to the content of the explanation. Global SHAP values are computed for the headline model with TreeExplainer, which is exact for tree ensembles rather than a sampling approximation [6]; the beeswarm plot shows per-student attributions with direction, and the bar chart ranks features by mean absolute SHAP value.

![SHAP beeswarm for XGBoost at t = 100%: each point is one test student, colour encodes the feature value, and the horizontal position shows how strongly that value pushes the prediction toward (right) or away from (left) the at-risk class.](D:/dsp/reports/figures/shap_summary_xgb_t100.png)

![Global SHAP feature importance (mean absolute SHAP value) for XGBoost at t = 100%.](D:/dsp/reports/figures/shap_importance_xgb_t100.png)

One feature dominates by a wide margin: `days_since_last_activity`, the length of the student's current silence in the VLE, followed by `weighted_score_to_date`, the cumulative weighted assessment score. The beeswarm confirms the directions a teacher would predict: long silences push strongly toward an at-risk flag, while a high running score pulls away from it, and the remaining contributors — submission counts, module identity, and per-activity click features — act in similarly plausible directions. This is an encouraging sanity check: the model's strongest signals are precisely the two indicators, disengagement and weak assessment performance, that human tutors already watch.

The dominance of a silence feature also connects directly to the dual-estimand reading of the target established in Section 3. On the full enrolment cohort, part of the model's measured strength consists of *recognising students who have already disengaged or withdrawn* rather than forecasting future risk — at t = 100%, recall is 0.930 on the full cohort versus 0.841 on the still-enrolled subgroup — and `days_since_last_activity` is exactly the feature through which that detection operates. The explanation thus corroborates, from the model's inside, why every headline claim in this report is stated per cohort.

Global importances do not help a tutor with an individual student, which is where LIME [7] enters: it fits an interpretable local surrogate around a single prediction, producing a per-student "why" — the form in which an explanation is actually consumed in an intervention conversation, and the form served per student by the instructor dashboard (Appendix).

![LIME local explanation for one high-confidence at-risk prediction at t = 100%: the local surrogate's weights show which of this student's feature values raise the flagged risk and which lower it.](D:/dsp/reports/figures/lime_local_example.png)

## 5.5 Stability across Seeds, Explainers, and Checkpoints

An explanation can support intervention decisions only if it is reproducible. Following the quantitative-stability methodology of Section 3 — the response to the qualitative-only assessment gap noted in prior reviews [3], [8] — stability is measured along three axes.

**Stability across seeds.** The headline model was retrained under five random seeds and re-explained. Across all seed pairs, the mean top-10 Jaccard overlap is 0.69 and the mean Spearman rank correlation is 0.97. The near-perfect rank correlation means the global feature story is a property of the data and the model class, not an artefact of one training run — the basic trust guarantee an early-warning explanation needs.

**Agreement between explainers.** SHAP and LIME agree only partially: the Jaccard overlap of their global top-10 sets is 0.43, computed on a limited LIME sample of test students. This is a finding, not a defect, and it has a clear methodological mechanism: the two explainers optimise different objectives. SHAP allocates exact Shapley contributions of the trained model itself, whereas LIME fits a local linear surrogate to predictions on randomly perturbed inputs — and its perturbation treats one-hot encoded categories as continuous variables, injecting additional noise. The two methods agree on the headline drivers but diverge in the mid-ranking. The project's policy is therefore to anchor all global claims on SHAP (exact for tree models), to use LIME as a per-student local cross-check, and to report the disagreement rather than silently selecting the more flattering explainer. The limited LIME sample is acknowledged as a limitation in Section 6.2.

**Stability across time.** Finally, explanations drift as the course progresses — and they should: early checkpoints contain little behaviour, so demographic and registration priors carry relatively more weight, while later checkpoints are dominated by engagement and performance signals. The figure below traces the drift across the six checkpoints.

![Explanation drift across the six checkpoints: top-10 Jaccard overlap and Spearman rank correlation for consecutive checkpoint pairs and for each checkpoint against the full-course (t = 100%) reference.](D:/dsp/reports/figures/xai_stability_drift.png)

The drift is smooth and ordered: adjacent checkpoints correlate strongly, while the earliest views share only a small fraction of the full-course top-10. The explanation evolves gradually rather than jumping — evidence of a coherent underlying signal — but the early-course and end-of-course stories genuinely differ. The operational consequence is a presentation rule that the instructor dashboard already implements: every explanation shown to a tutor is labelled with the checkpoint at which it was computed, and explanations are never transferred across checkpoints.

Taken together, these results answer RQ2: explanations are highly stable to training randomness, partially consistent across explainers for identifiable methodological reasons, and smoothly time-varying — trustworthy, provided they are anchored on SHAP and carry their checkpoint label.

<!-- Drafted 2026-07-12 (owner: Khoa/Bình). All volatile metrics are {{...}} placeholders resolved by tools/build_final_report.py from reports/tables/*.csv after the renumber run; do not hand-type numbers here. -->


---

# 6. Discussion, Limitations, and Conclusion

## 6.1 Answers to the Research Questions

**RQ1 — best algorithm and earliest reliable prediction.** XGBoost is the strongest model from the 40% checkpoint onward, with LightGBM marginally ahead at the earliest checkpoints, as established by the repeated cross-validation and Friedman/Wilcoxon analysis of Section 4. The answer on earliness is deliberately dual, because the fixed end-of-course label supports two estimands (Section 3). On the full enrolment cohort — the frame comparable with the baseline literature [1], [2] — at-risk recall crosses the 0.80 reliability bar from the 40% checkpoint (0.811) and rises through course end. On the still-enrolled cohort — the students an intervention can actually reach — recall at the same checkpoint is only 0.678, and the bar is reached only at course end (0.841). Both statements are correct; they answer different questions, and the report never states one without naming its cohort. The full-cohort finding is consistent with the 40–60% reliability window of Adnan et al. [2]; the still-enrolled analysis is a contribution this project adds on top of that frame.

**RQ2 — consistency and stability of explanations.** The explanations of the headline model are highly stable to training randomness — mean top-10 Jaccard 0.69 and mean Spearman 0.97 across five seeds — and they drift smoothly and interpretably across the six checkpoints, shifting from demographic priors toward engagement and performance signals as the course unfolds. Agreement between SHAP and LIME is partial (top-10 Jaccard 0.43 on a limited LIME sample), which Section 5.5 traces to the different objectives the two explainers optimise. The project therefore anchors global claims on SHAP, uses LIME as a per-student cross-check, and requires every displayed explanation to carry its checkpoint label. The quantitative-stability methodology itself — Jaccard, Spearman, and cross-seed measures applied to educational explanations — addresses the qualitative-only assessment gap identified in prior reviews [3], [8].

**RQ3 — effect of imbalance handling on accuracy and explanations.** Under this project's label mapping the at-risk class is a slight majority (52.8%, imbalance ratio 1.12), so imbalance handling was studied as a controlled robustness experiment rather than the rescue of a rare class — including the documented observation that default SMOTE/ADASYN here oversample the *not-at-risk* class. The answer is robustness on both halves: across the four strategies the largest spread on any primary accuracy metric is 0.0069, and the SHAP importance rankings remain essentially invariant, with near-unity rank correlation for every strategy pair. The project's conclusions on OULAD do not depend on the imbalance-handling choice.

## 6.2 Limitations

Six limitations are stated openly; all were identified, measured, and documented by the group itself.

1. **Population definition, not leakage.** The fixed end-of-course label (Option A) keeps students who withdrew before a checkpoint in that checkpoint's population, still labelled at-risk. Their near-total inactivity makes them easy to detect, so full-cohort metrics partly measure *detection of students already gone* rather than forecasting. The label never enters the features — this is a population-definition issue, not leakage — and it is quantified through the dual-cohort reporting used throughout.
2. **Score-availability assumption.** Performance features credit an assessment score on its `date_submitted`. In deployment, marks become available only after grading, so a live system at checkpoint *t* may see fewer scores than the features assume; checkpoint-time score features are correspondingly optimistic about what is knowable on the checkpoint day.
3. **Source-data duplicates.** The raw OULAD clickstream contains 787,170 exact duplicate rows (7.4% of `studentVle`), a quirk of the published dataset. The pipeline keeps and accumulates them — deleting indistinguishable rows would be an unverifiable guess — so click totals may be over-counted for affected student-days; the decision and its rationale are documented in the cleaning methodology.
4. **LIME sample size.** The SHAP–LIME agreement statistic is estimated on a limited LIME sample of test students, a concession to LIME's per-instance computational cost; the estimate is therefore coarse, and LIME's perturbation of one-hot encoded categories as continuous variables adds further noise.
5. **Single-dataset scope.** All findings rest on one anonymised UK distance-learning dataset. Transfer to other institutions, delivery modes, or VLE platforms is untested.
6. **Banked-assessment errata and the renumbering protocol.** A defect in the submission-coverage indicator for banked assessments — affecting 78 of 32,593 enrolment records (0.24%) at t = 100% — was found, fixed, and guarded with a regression test. Result tables committed before the fix predate it, so the complete table set is recomputed in a final freeze run before submission; every number in this report is injected from those tables at build time, so the recomputation propagates automatically.

## 6.3 Practical Implications

For an institution, the two estimands translate directly into interface and policy decisions. The instructor dashboard operationalises the still-enrolled frame: at any chosen checkpoint it lists flagged students ranked by risk with a *still-enrolled filter*, so a tutor's worklist contains only students an intervention can still reach, and each student's SHAP explanation carries its checkpoint label. Decision thresholds are equally a policy instrument: selected on out-of-fold validation and applied to the sealed test exactly once, they let an institution choose the operating point that matches its intervention budget — the default cut for a balanced workload, or a high-recall cut when the cost of missing an at-risk student outweighs the cost of additional outreach. The threshold, like the explanation, should be stated alongside every deployment of the model.

## 6.4 Future Work

Three extensions follow naturally from the limitations. First, *per-checkpoint censoring* (the Option B design) should be promoted from a sensitivity analysis to the primary estimand: training and evaluating at each checkpoint only on students still enrolled at that cutoff would make the early-warning question the native objective of the model rather than an evaluation-side reading of it. Second, the composite at-risk label should be decomposed: Fail and Withdrawn have different behavioural signatures and call for different interventions, suggesting a multi-class or competing-risks formulation with withdrawal timing as an outcome in its own right. Third, external validity needs work on several fronts: replication on datasets beyond OULAD, grading-lag-aware score features that respect deployment-time information availability, and a larger LIME sample — with additional explainers — to tighten the cross-explainer agreement estimates.

## 6.5 Conclusion

This project set out to occupy an empty cell in the learning-analytics literature: time-aware at-risk prediction, post-hoc explanation, and imbalance handling had each been studied separately, but never together on OULAD. The result is an end-to-end, leakage-safe pipeline — a frozen student-level split, cumulative features at six checkpoints, five benchmarked algorithms, validation-chosen thresholds, fairness tables, and an instructor dashboard — in which every prediction is explained and every explanation is itself evaluated for stability. The substantive findings are threefold: XGBoost delivers reliable full-cohort predictions from the 40% checkpoint while the actionable still-enrolled cohort remains harder until course end; SHAP explanations are seed-stable, smoothly time-varying, and centred on the two signals tutors already trust — silence and weak scores; and neither accuracy nor explanations depend on the imbalance-handling strategy, because the at-risk class is in fact a slight majority. Beyond the numbers, the project's central methodological message is a discipline of honest framing: an early-warning claim must name the cohort it applies to, and an explanation must carry the checkpoint it was computed at. Under those two disciplines, the pipeline presented here is accurate, interpretable, and reproducible enough to serve as the foundation of a real early-intervention workflow.

<!-- Drafted 2026-07-12 (owner: Khoa). All volatile metrics are {{...}} placeholders resolved by tools/build_final_report.py from reports/tables/*.csv after the renumber run; do not hand-type numbers here. -->


---

# 7. Appendices

## 7.1 Appendix A — Instructor Dashboard Architecture

The optional instructor dashboard (contribution iv, Section 1) is implemented as a deliberately thin Streamlit interface in `dashboard/app.py`: the UI contains no modelling logic of its own, and every substantive operation — loading a trained checkpoint bundle, applying the anti-leakage transformation, computing SHAP attributions — is delegated to the same `src/` modules used by the experiments, so the dashboard cannot drift from the evaluated pipeline. For inference, each bundle carries the statistics dictionary and fitted ColumnTransformer of Section 3.7; the frozen test cohort is transformed with these stored training-fold statistics only, exactly as during evaluation.

For a selected checkpoint *t* and model, the dashboard shows three things. First, the frozen test cohort ranked by predicted at-risk probability under an adjustable decision threshold. Second, a still-enrolled flag per student, computed by joining the registration table's unregistration dates against the checkpoint map's cutoff day — the dual-cohort finding of Section 3.2 operationalised in the interface, since an instructor cannot intervene on a student who has already withdrawn. Third, a per-student local SHAP explanation, explicitly labelled with the checkpoint it uses so that an explanation is never read as pertaining to a different point in the course. The model picker is restricted to the tree ensembles (XGBoost, LightGBM, Random Forest), which TreeExplainer explains in milliseconds; Logistic Regression and the ANN would fall back to the kernel explainer, which is too slow for interactive use.

The dashboard is launched with `streamlit run dashboard/app.py`; a headless smoke test, `python dashboard/app.py --smoke`, asserts the full scoring path end-to-end (bundle loading, transformation, prediction, SHAP) without starting the UI.

## 7.2 Appendix B — Reproducibility and the Renumber Protocol

All committed artifacts were built in a verified, pinned environment (Python 3.13.9, scikit-learn 1.8.0, numpy 2.3.5, xgboost 3.1.3, lightgbm 4.6.0, shap 0.52.0; the full set is pinned in `environment.yml` and `requirements.txt`), with a single global seed (42) defined once in `src/config.py` and consumed by every stochastic operation. Data provenance is anchored by an MD5 reference manifest: `setup_raw_data.py` records the hash, size, and download date of each of the seven raw OULAD CSVs, sets the files read-only, and on every subsequent run recomputes and compares the hashes, aborting the pipeline on any mismatch. The frozen split of Section 3.6 is protected by the committed test-student list and a guard that prevents accidental re-derivation.

Because volatile results must never be hand-maintained, the project follows a renumber protocol (documented in the team defence handbook): `tools/renumber.sh` rebuilds every derived artifact — master table, checkpoint datasets, split materialisation, EDA figures, the full test suite, model training, cross-validation, statistical tests, and all analysis tables and figures — from the raw CSVs in a fixed order, with stamp-based resume so an interrupted run continues rather than restarts. This run is mandatory before the final number freeze, since the banked-assessment fix (Section 3.3) postdates some previously committed tables. The report itself closes the loop: `tools/build_final_report.py` stitches the section sources and resolves every volatile number, table, and figure from placeholder references to the committed result CSVs at build time, so no model metric in this document is hand-typed and a renumber run propagates into the report automatically.

## 7.3 Appendix C — Ethics and Fairness Compliance Note

OULAD is secondary data, anonymised at source by The Open University and released under CC-BY 4.0; the project's obligations — correct citation, no re-identification attempts, no linkage with external data, and licence acknowledgement — are documented in full in the project's data-source, licence, and ethics statement, and no additional institutional ethics approval is required for this coursework use of a publicly released, anonymised dataset. Beyond compliance, the project audits its own model behaviour for disparate performance: Section 4 reports the fairness table of subgroup metrics and gaps across gender, disability, age band, IMD deprivation band, highest education, and region on the held-out test set. Consistent with the intervention framing, predictions are positioned as decision support for instructors — a ranked list with explanations — rather than as automated decisions about students.
