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
