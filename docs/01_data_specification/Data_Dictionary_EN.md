# OULAD Master-Table Data Dictionary (complete)

*Covers 100% of the master_raw columns. Auto-generated from the master table.*

**DSP391m – Group 1 · Report 2 · STT 29 (An)**

Total variables: **33**

## Identifier

| # | Variable | Type | Origin | Description | Example / Range |
|---|---|---|---|---|---|
| 1 | `code_module` | Nominal (ID) | Original | Module code; part of the composite key. | 7 unique |
| 2 | `code_presentation` | Nominal (ID) | Original | Presentation code (B=Feb, J=Oct); part of the composite key. | 4 unique |
| 3 | `id_student` | Nominal (ID) | Original | Unique student id; the group key for GroupKFold (not a feature). | min 3733, max 2.7168e+06 |

## Demographic

| # | Variable | Type | Origin | Description | Example / Range |
|---|---|---|---|---|---|
| 4 | `gender` | Binary | Original | Gender; encoded M=1, F=0. | 2 unique |
| 5 | `region` | Nominal | Original | Region of the UK/Ireland (13 values); one-hot encoded. | 13 unique |
| 6 | `highest_education` | Ordinal | Original | Highest education level; ordinal 0..4. | 5 unique |
| 7 | `imd_band` | Ordinal | Original | Index of Multiple Deprivation band; ordinal; 1,111 missing -> 'Unknown'. | 10 unique |
| 8 | `age_band` | Ordinal | Original | Age band; ordinal 0..2. | 3 unique |
| 9 | `num_of_prev_attempts` | Numeric (discrete) | Original | Number of previous attempts at the module. | min 0, max 6 |
| 10 | `studied_credits` | Numeric (discrete) | Original | Total credits the student is studying. | min 30, max 655 |
| 11 | `disability` | Binary | Original | Declared disability; encoded Y=1, N=0. | 2 unique |

## Engagement

| # | Variable | Type | Origin | Description | Example / Range |
|---|---|---|---|---|---|
| 12 | `total_clicks` | Numeric (continuous) | Derived | Total VLE clicks up to the checkpoint; right-skewed -> log1p. | min 0, max 24139 |
| 13 | `n_days_active` | Numeric (discrete) | Derived | Number of distinct active days up to the checkpoint. | min 0, max 286 |
| 14 | `max_clicks_single_day` | Numeric (continuous) | Derived | Maximum clicks on any single day up to the checkpoint; strongly right-skewed -> log1p. | min 0, max 6988 |
| 15 | `clicks_forumng` | Numeric (continuous) | Derived | Clicks on 'forumng' activities up to the checkpoint. | min 0, max 13154 |
| 16 | `clicks_oucontent` | Numeric (continuous) | Derived | Clicks on 'oucontent' activities up to the checkpoint. | min 0, max 9308 |
| 17 | `clicks_resource` | Numeric (continuous) | Derived | Clicks on 'resource' activities up to the checkpoint. | min 0, max 5147 |
| 18 | `clicks_homepage` | Numeric (continuous) | Derived | Clicks on 'homepage' activities up to the checkpoint. | min 0, max 7277 |
| 19 | `clicks_oucollaborate` | Numeric (continuous) | Derived | Clicks on 'oucollaborate' activities up to the checkpoint. | min 0, max 316 |
| 20 | `clicks_quiz` | Numeric (continuous) | Derived | Clicks on 'quiz' activities up to the checkpoint. | min 0, max 13032 |
| 21 | `clicks_subpage` | Numeric (continuous) | Derived | Clicks on 'subpage' activities up to the checkpoint. | min 0, max 4345 |
| 22 | `clicks_url` | Numeric (continuous) | Derived | Clicks on 'url' activities up to the checkpoint. | min 0, max 2134 |
| 23 | `mean_clicks_per_active_day` | Numeric (continuous) | Derived | total_clicks / n_days_active (0 when no active day); right-skewed -> log1p. | min 0, max 221.2 |
| 24 | `days_since_last_activity` | Numeric (continuous) | Derived | Days from the last activity to the checkpoint day (large when disengaged). | min 0, max 292 |

## Performance

| # | Variable | Type | Origin | Description | Example / Range |
|---|---|---|---|---|---|
| 25 | `n_assessments_submitted` | Numeric (discrete) | Derived | Assessments submitted (not banked) up to the checkpoint. | min 0, max 14 |
| 26 | `mean_score_to_date` | Numeric (continuous) | Derived | Mean score of submissions up to the checkpoint [0-100]; 0 if none. | min 0, max 100 |
| 27 | `weighted_score_to_date` | Numeric (continuous) | Derived | Sum of score x weight/100 of submissions up to the checkpoint. | min 0, max 200 |
| 28 | `not_submitted` | Binary (indicator) | Derived | 1 if the student missed >=1 assessment whose deadline had passed; a risk signal. | min 0, max 1 |

## Temporal

| # | Variable | Type | Origin | Description | Example / Range |
|---|---|---|---|---|---|
| 29 | `date_registration` | Numeric (continuous) | Original | Registration day relative to course start (can be negative); 45 missing -> train median. | min -322, max 167 |
| 30 | `date_unregistration` | Numeric (continuous) | Original | Withdrawal day; NaN if not withdrawn. Used for Withdrawn analysis, not a feature. | min -365, max 444 |
| 31 | `module_presentation_length` | Numeric (discrete) | Original | Length of the module-presentation in days; used to convert checkpoints to days. | min 234, max 269 |

## Target (raw)

| # | Variable | Type | Origin | Description | Example / Range |
|---|---|---|---|---|---|
| 32 | `final_result` | Nominal (raw) | Original | Raw outcome (Pass/Distinction/Fail/Withdrawn); source of the label. | 4 unique |

## Target

| # | Variable | Type | Origin | Description | Example / Range |
|---|---|---|---|---|---|
| 33 | `at_risk` | Binary (target) | Derived | 1 if final_result in {Fail, Withdrawn}, else 0. Fixed across checkpoints. | min 0, max 1 |
