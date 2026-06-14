# Evidence-Based Justification for Methodological Choices

**Subtitle:** Rationale for Key Design Decisions in the At-Risk Student Prediction Pipeline

**DSP391m – Group 1 · Report 2 (Data Tasks), Chapter 3 · Work item STT 25 (Son)**

---

## 1. Why Checkpoints at 40–60% of Course Length Provide a Reliable Early-Prediction Point

One of the most consequential choices in an early-warning system is *when* to make a prediction. Intervening too late offers little benefit; predicting too early risks high uncertainty. Adnan et al. [1] systematically evaluated prediction accuracy at multiple points across the course timeline and found that the window spanning 40–60% of course length represents a pragmatic balance: enough student-activity data has accumulated to produce stable predictions, yet sufficient time remains for instructors to deploy meaningful support. Our pipeline therefore defines **six** time-aware checkpoints (10 / 20 / 40 / 60 / 80 / 100% of course length) and treats the **40–60% window** as the primary, most-actionable evaluation point. This choice directly answers **RQ1** (earliest reliable checkpoint and best algorithm) by grounding the checkpoint schedule in empirical evidence rather than arbitrary calendar dates.

*Supporting citation: [1]*

---

## 2. Why Engagement and Assessment Features Are Prioritised Over Demographic Features

Feature selection in educational data mining must be guided by evidence of predictive validity. Tomasevic et al. [2] compared multiple supervised machine-learning techniques for student performance prediction on OULAD and found that engagement indicators—particularly Virtual Learning Environment (VLE) interaction logs (clickstream data)—and intermediate assessment scores carry high predictive signal. In contrast, demographic attributes such as age band, region, and highest prior education level contributed comparatively little additional predictive power once behavioural and academic-performance features were available.

In our project, the OULAD dataset [3] provides rich VLE clickstream records (sum and daily counts of resource interactions) and assessment (TMA/CMA) results. These form the core feature groups, while demographic fields are retained but deprioritised. This design choice avoids building a model whose decisions rest on protected characteristics and instead anchors predictions in learner actions that are directly observable and educationally meaningful.

*Supporting citations: [2], [3]*

---

## 3. Why PR-AUC and Recall Are Chosen Over Accuracy as Primary Metrics

The target variable in this project is `at_risk`, defined as students with a final result of *Fail* or *Withdrawn*, contrasted against *Pass* or *Distinction* (not-at-risk). Based on the OULAD dataset, the observed at-risk rate is approximately **52.8%**, making the class imbalance mild rather than severe. Because both classes are represented at near-parity, overall Accuracy would not be misleading in a gross sense; however, it remains an inappropriate primary metric for this use-case for a conceptual reason: a false negative (predicting *not at risk* when the student will actually fail or withdraw) carries far greater pedagogical cost than a false positive. The intervention cost of flagging an unneeded alert is low; the cost of missing a struggling student is high.

Recall (Sensitivity) quantifies the fraction of true at-risk students successfully identified, which maps directly to the operational goal. Precision-Recall AUC (PR-AUC) summarises the trade-off across all decision thresholds and is the recommended metric when the positive class—even a mildly minority class—is the class of interest [6]. Using accuracy as a primary metric would allow a model to appear performant while still missing many at-risk students.

Although the imbalance is mild, **RQ3** explicitly investigates whether resampling techniques (SMOTE, ADASYN) and class-weighting further improve Recall and PR-AUC. The finding of mild imbalance does not eliminate the need to study these techniques; it simply means their marginal benefit may be smaller than in severely skewed settings, a result worth reporting empirically. Chawla et al. [6] introduced SMOTE as a principled over-sampling baseline, which is why it serves as the reference technique in RQ3.

*Supporting citations: [6]*

---

## 4. Why a Group-Aware Stratified Split With a Fixed Test Set Is Required

Student records in OULAD contain multiple module presentations per student (`id_student`). If records from the same student appear in both training and test sets, the model can learn individual idiosyncrasies rather than generalisable patterns—a form of *group leakage* that inflates held-out performance. To prevent this, the train/validation/test split must be performed at the student level (grouped by `id_student`) so that all records of a given student fall entirely in one partition.

Beyond leakage prevention, the project evaluates predictions at six time-aware checkpoints (10–100% of course length). Keeping the test set fixed across all checkpoints ensures that performance comparisons are made on an identical population, preserving the validity of paired statistical tests and cross-checkpoint comparisons. Stratification on the `at_risk` label within the group-level split maintains the approximately 52.8% positive rate in each partition, preventing accidental imbalance introduced by the split itself.

*This design is standard practice in grouped cross-validation literature and is required for the integrity of RQ1 and RQ2.*

---

## 5. Why Explanation Stability Requires a Quantitative Metric

SHAP and LIME are the two most widely deployed post-hoc explanation methods in educational analytics. However, Gunasekara and Saarela [4] reviewed the state of XAI in education and identified a critical gap: while qualitative comparison of feature-importance rankings is common, rigorous quantitative measurement of explanation stability—how consistently an explanation method assigns the same importance ordering across repeated runs, perturbed inputs, or similar students—is largely absent from the literature. A purely visual or ranking-based inspection cannot detect subtle instabilities that would undermine trust in explanations delivered to instructors.

**RQ2** therefore introduces a quantitative stability metric (e.g., rank-correlation of SHAP feature importance across bootstrap resamples, or Jaccard similarity of top-k LIME features) and compares SHAP against LIME on this dimension. This directly addresses the methodological gap identified in [4] and produces a result that is reproducible and comparable across future studies.

*Supporting citation: [4]*

---

## References

[1] M. Adnan et al., "Predicting at-Risk Students at Different Percentages of Course Length for Early Intervention Using Machine Learning Models," *IEEE Access*, vol. 9, pp. 7519–7539, 2021.

[2] N. Tomasevic, N. Gvozdenovic, and S. Vranes, "An overview and comparison of supervised data mining techniques for student exam performance prediction," *Computers & Education*, vol. 143, p. 103676, 2020.

[3] J. Kuzilek, M. Hlosta, and Z. Zdrahal, "Open University Learning Analytics Dataset," *Scientific Data*, vol. 4, p. 170171, 2017.

[4] S. Gunasekara and M. Saarela, "Explainable AI in Education: Techniques and Qualitative Assessment," *Applied Sciences*, vol. 15, no. 3, art. 1239, 2025.

[6] N. V. Chawla, K. W. Bowyer, L. O. Hall, and W. P. Kegelmeyer, "SMOTE: Synthetic Minority Over-sampling Technique," *Journal of Artificial Intelligence Research*, vol. 16, pp. 321–357, 2002.
