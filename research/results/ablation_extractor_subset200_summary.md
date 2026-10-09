# PRELIMINARY SMOKE TEST (--subset 200 pools per split)

Test pools unless noted. Values: mean over JD pools [95% cluster-bootstrap CI over pools, 1000 resamples]. Gaps: |score change| / SD of the pool's original scores, over CHANGED bios. Signed gaps: + = favours the female-coded (communal / target) version.

## Ranking accuracy (test)

| Scorer | nDCG@10 | MRR | P@5 | P@10 | pairs with entities |
|---|---|---|---|---|---|
| ex_noun_chunk | 0.491 [0.462, 0.523] | 0.753 [0.704, 0.803] | 0.492 [0.451, 0.535] | 0.381 [0.354, 0.410] | 1.000 [1.000, 1.000] |
| ex_esco | 0.378 [0.344, 0.411] | 0.562 [0.510, 0.610] | 0.381 [0.338, 0.420] | 0.312 [0.282, 0.342] | 0.693 [0.680, 0.704] |
| ex_jobbert_ft | 0.327 [0.300, 0.354] | 0.617 [0.565, 0.669] | 0.328 [0.291, 0.362] | 0.245 [0.221, 0.270] | 0.373 [0.362, 0.382] |
| ex_union | 0.443 [0.411, 0.474] | 0.662 [0.612, 0.714] | 0.438 [0.395, 0.479] | 0.357 [0.328, 0.387] | 0.764 [0.753, 0.772] |

## Counterfactual |gap| (normalised, changed bios)

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| ex_noun_chunk | 0.162 [0.151, 0.172] | 0.031 [0.029, 0.033] | 0.032 [0.030, 0.035] | 0.029 [0.027, 0.031] | 0.147 [0.098, 0.207] | 0.052 [0.044, 0.060] | 0.163 [0.152, 0.173] |
| ex_esco | 0.000 [0.000, 0.000] | 0.007 [0.004, 0.009] | 0.002 [0.001, 0.003] | 0.002 [0.001, 0.003] | 0.000 [0.000, 0.000] | 0.565 [0.493, 0.643] | 0.002 [0.001, 0.002] |
| ex_jobbert_ft | 0.160 [0.155, 0.166] | 0.068 [0.059, 0.076] | 0.111 [0.099, 0.124] | 0.102 [0.091, 0.114] | 0.000 [0.000, 0.001] | 0.156 [0.119, 0.195] | 0.169 [0.163, 0.175] |
| ex_union | 0.069 [0.066, 0.073] | 0.041 [0.035, 0.046] | 0.054 [0.047, 0.061] | 0.052 [0.044, 0.060] | 0.000 [0.000, 0.001] | 0.447 [0.387, 0.503] | 0.074 [0.071, 0.078] |

## Signed gap (normalised, changed bios; + favours female/communal/target)

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| ex_noun_chunk | 0.152 [0.142, 0.163] | -0.002 [-0.005, -0.000] | -0.002 [-0.005, -0.000] | -0.005 [-0.007, -0.003] | -0.128 [-0.192, -0.076] | 0.026 [0.016, 0.035] | 0.151 [0.141, 0.162] |
| ex_esco | 0.000 [-0.000, 0.000] | 0.006 [0.003, 0.009] | 0.001 [0.000, 0.002] | -0.002 [-0.003, -0.001] | 0.000 [0.000, 0.000] | -0.561 [-0.638, -0.487] | 0.001 [0.001, 0.002] |
| ex_jobbert_ft | -0.117 [-0.123, -0.110] | -0.022 [-0.031, -0.013] | -0.026 [-0.039, -0.013] | -0.036 [-0.047, -0.025] | -0.000 [-0.001, 0.000] | -0.024 [-0.067, 0.016] | -0.119 [-0.125, -0.112] |
| ex_union | -0.043 [-0.046, -0.040] | -0.009 [-0.015, -0.003] | -0.016 [-0.024, -0.009] | -0.018 [-0.024, -0.011] | -0.000 [-0.001, 0.000] | -0.418 [-0.475, -0.358] | -0.043 [-0.047, -0.040] |

## Mean |rank shift| in the pool (changed bios)

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| ex_noun_chunk | 4.343 [4.056, 4.637] | 0.843 [0.773, 0.911] | 0.877 [0.816, 0.945] | 0.802 [0.734, 0.866] | 4.593 [2.644, 6.934] | 1.337 [1.060, 1.663] | 4.371 [4.087, 4.659] |
| ex_esco | 0.005 [0.001, 0.010] | 0.141 [0.090, 0.197] | 0.048 [0.022, 0.081] | 0.048 [0.022, 0.081] | 0.000 [0.000, 0.000] | 18.354 [16.200, 20.629] | 0.034 [0.023, 0.047] |
| ex_jobbert_ft | 3.747 [3.574, 3.925] | 1.554 [1.313, 1.783] | 2.660 [2.353, 2.976] | 2.417 [2.119, 2.704] | 0.000 [0.000, 0.000] | 3.736 [2.732, 4.841] | 3.951 [3.773, 4.130] |
| ex_union | 2.229 [2.122, 2.342] | 1.209 [1.036, 1.373] | 1.571 [1.356, 1.780] | 1.561 [1.339, 1.803] | 0.000 [0.000, 0.000] | 13.799 [12.270, 15.397] | 2.388 [2.274, 2.500] |

## Entity scorers: |gap| restricted to pairs where both sides have entities

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| ex_esco | 0.000 [0.000, 0.000] | 0.002 [0.001, 0.003] | 0.001 [0.001, 0.002] | 0.001 [0.001, 0.002] | 0.000 [0.000, 0.000] | 0.288 [0.249, 0.335] | 0.000 [0.000, 0.001] |
| ex_jobbert_ft | 0.159 [0.152, 0.165] | 0.070 [0.061, 0.080] | 0.092 [0.082, 0.103] | 0.083 [0.073, 0.094] | 0.001 [0.000, 0.003] | 0.118 [0.085, 0.153] | 0.170 [0.163, 0.177] |
| ex_union | 0.058 [0.056, 0.061] | 0.028 [0.024, 0.032] | 0.037 [0.033, 0.042] | 0.034 [0.030, 0.039] | 0.000 [0.000, 0.001] | 0.262 [0.227, 0.300] | 0.062 [0.060, 0.065] |

## TPR gender gap (threshold chosen on dev; test; TPR_F - TPR_M over JD occupations)

| Scorer | threshold (z) | mean gap | RMS gap |
|---|---|---|---|
| ex_noun_chunk | 1.32 | 0.045 [0.003, 0.087] | 0.111 [0.106, 0.176] |
| ex_esco | 1.02 | -0.000 [-0.042, 0.043] | 0.075 [0.078, 0.155] |
| ex_jobbert_ft | 1.47 | -0.028 [-0.065, 0.007] | 0.073 [0.075, 0.147] |
| ex_union | 1.16 | -0.002 [-0.043, 0.037] | 0.088 [0.083, 0.163] |

## Top-10 exposure (female share - 0.5; pools are 50/50)

| Scorer | top-10 share | discounted exposure |
|---|---|---|
| ex_noun_chunk | 0.072 [0.053, 0.090] | 0.084 [0.063, 0.104] |
| ex_esco | -0.004 [-0.024, 0.015] | -0.002 [-0.023, 0.020] |
| ex_jobbert_ft | -0.013 [-0.033, 0.006] | -0.014 [-0.037, 0.007] |
| ex_union | 0.015 [-0.005, 0.034] | 0.019 [-0.002, 0.041] |

## Paired permutation tests: ex_union vs baselines (10000 sign flips, Holm within each row family)

| condition | metric | baseline | mean diff (ours - baseline) | p | p (Holm) | pools |
|---|---|---|---|---|---|---|
| original | ndcg@10 | ex_esco | 0.0653 | 0.0001 | 0.0003 | 200 |
| original | ndcg@10 | ex_jobbert_ft | 0.1157 | 0.0001 | 0.0003 | 200 |
| original | ndcg@10 | ex_noun_chunk | -0.0479 | 0.0061 | 0.0061 | 200 |
| pronoun_swap | abs_gap_norm_changed | ex_esco | 0.0692 | 0.0001 | 0.0003 | 198 |
| pronoun_swap | abs_gap_norm_changed | ex_jobbert_ft | -0.0908 | 0.0001 | 0.0003 | 194 |
| pronoun_swap | abs_gap_norm_changed | ex_noun_chunk | -0.0915 | 0.0001 | 0.0003 | 199 |
| name_swap_us | abs_gap_norm_changed | ex_esco | 0.0344 | 0.0001 | 0.0003 | 198 |
| name_swap_us | abs_gap_norm_changed | ex_jobbert_ft | -0.0264 | 0.0001 | 0.0003 | 194 |
| name_swap_us | abs_gap_norm_changed | ex_noun_chunk | 0.0099 | 0.0016 | 0.0016 | 199 |
| name_swap_in | abs_gap_norm_changed | ex_esco | 0.0527 | 0.0001 | 0.0003 | 198 |
| name_swap_in | abs_gap_norm_changed | ex_jobbert_ft | -0.0562 | 0.0001 | 0.0003 | 194 |
| name_swap_in | abs_gap_norm_changed | ex_noun_chunk | 0.0220 | 0.0001 | 0.0003 | 199 |
| name_in_same_gender | abs_gap_norm_changed | ex_esco | 0.0502 | 0.0001 | 0.0003 | 198 |
| name_in_same_gender | abs_gap_norm_changed | ex_jobbert_ft | -0.0506 | 0.0001 | 0.0003 | 194 |
| name_in_same_gender | abs_gap_norm_changed | ex_noun_chunk | 0.0226 | 0.0001 | 0.0003 | 199 |
| affiliation_swap | abs_gap_norm_changed | ex_esco | 0.0003 | 1.0000 | 1.0000 | 45 |
| affiliation_swap | abs_gap_norm_changed | ex_jobbert_ft | -0.0001 | 1.0000 | 1.0000 | 45 |
| affiliation_swap | abs_gap_norm_changed | ex_noun_chunk | -0.1464 | 0.0001 | 0.0003 | 45 |
| agentic_communal | abs_gap_norm_changed | ex_esco | -0.1183 | 0.0001 | 0.0003 | 188 |
| agentic_communal | abs_gap_norm_changed | ex_jobbert_ft | 0.2998 | 0.0001 | 0.0003 | 184 |
| agentic_communal | abs_gap_norm_changed | ex_noun_chunk | 0.3944 | 0.0001 | 0.0003 | 189 |
| gender_full | abs_gap_norm_changed | ex_esco | 0.0730 | 0.0001 | 0.0003 | 198 |
| gender_full | abs_gap_norm_changed | ex_jobbert_ft | -0.0946 | 0.0001 | 0.0003 | 194 |
| gender_full | abs_gap_norm_changed | ex_noun_chunk | -0.0873 | 0.0001 | 0.0003 | 199 |

Scoring wall-clock (s): ex_noun_chunk 339, ex_esco 119, ex_jobbert_ft 96, ex_union 129
