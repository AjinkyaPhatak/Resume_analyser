# PRELIMINARY SMOKE TEST (--subset 200 pools per split)

Test pools unless noted. Values: mean over JD pools [95% cluster-bootstrap CI over pools, 1000 resamples]. Gaps: |score change| / SD of the pool's original scores, over CHANGED bios. Signed gaps: + = favours the female-coded (communal / target) version.

## Ranking accuracy (test)

| Scorer | nDCG@10 | MRR | P@5 | P@10 | pairs with entities |
|---|---|---|---|---|---|
| agg_maxsim_mean | 0.443 [0.411, 0.474] | 0.662 [0.612, 0.714] | 0.438 [0.395, 0.479] | 0.357 [0.328, 0.387] | 0.764 [0.753, 0.772] |
| agg_hungarian | 0.266 [0.241, 0.291] | 0.467 [0.415, 0.516] | 0.265 [0.231, 0.301] | 0.212 [0.190, 0.235] | 0.764 [0.753, 0.772] |
| agg_idf_weighted | 0.453 [0.421, 0.483] | 0.676 [0.629, 0.727] | 0.445 [0.402, 0.487] | 0.365 [0.336, 0.394] | 0.764 [0.753, 0.772] |

## Counterfactual |gap| (normalised, changed bios)

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| agg_maxsim_mean | 0.069 [0.066, 0.073] | 0.041 [0.035, 0.046] | 0.054 [0.047, 0.061] | 0.052 [0.044, 0.060] | 0.000 [0.000, 0.001] | 0.447 [0.387, 0.503] | 0.074 [0.071, 0.078] |
| agg_hungarian | 0.100 [0.097, 0.104] | 0.052 [0.046, 0.057] | 0.075 [0.068, 0.081] | 0.070 [0.064, 0.078] | 0.003 [0.000, 0.009] | 0.450 [0.415, 0.489] | 0.107 [0.104, 0.111] |
| agg_idf_weighted | 0.069 [0.066, 0.073] | 0.041 [0.035, 0.046] | 0.054 [0.047, 0.062] | 0.052 [0.044, 0.060] | 0.000 [0.000, 0.001] | 0.436 [0.378, 0.490] | 0.075 [0.071, 0.078] |

## Signed gap (normalised, changed bios; + favours female/communal/target)

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| agg_maxsim_mean | -0.043 [-0.046, -0.040] | -0.009 [-0.015, -0.003] | -0.016 [-0.024, -0.009] | -0.018 [-0.024, -0.011] | -0.000 [-0.001, 0.000] | -0.418 [-0.475, -0.358] | -0.043 [-0.047, -0.040] |
| agg_hungarian | -0.072 [-0.075, -0.068] | -0.015 [-0.020, -0.010] | -0.011 [-0.019, -0.004] | -0.031 [-0.038, -0.023] | -0.003 [-0.009, 0.000] | -0.416 [-0.459, -0.375] | -0.074 [-0.077, -0.070] |
| agg_idf_weighted | -0.044 [-0.047, -0.040] | -0.009 [-0.015, -0.003] | -0.016 [-0.024, -0.009] | -0.018 [-0.025, -0.012] | -0.000 [-0.001, 0.000] | -0.406 [-0.462, -0.347] | -0.044 [-0.048, -0.040] |

## Mean |rank shift| in the pool (changed bios)

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| agg_maxsim_mean | 2.229 [2.122, 2.342] | 1.209 [1.036, 1.373] | 1.571 [1.356, 1.780] | 1.561 [1.339, 1.803] | 0.000 [0.000, 0.000] | 13.799 [12.270, 15.397] | 2.388 [2.274, 2.500] |
| agg_hungarian | 2.498 [2.385, 2.610] | 1.260 [1.104, 1.423] | 1.743 [1.523, 1.961] | 1.667 [1.450, 1.898] | 0.033 [0.000, 0.100] | 13.348 [11.886, 14.813] | 2.671 [2.555, 2.779] |
| agg_idf_weighted | 2.215 [2.109, 2.329] | 1.192 [1.021, 1.360] | 1.581 [1.358, 1.793] | 1.559 [1.333, 1.792] | 0.000 [0.000, 0.000] | 13.324 [11.790, 14.897] | 2.370 [2.256, 2.487] |

## Entity scorers: |gap| restricted to pairs where both sides have entities

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| agg_maxsim_mean | 0.058 [0.056, 0.061] | 0.028 [0.024, 0.032] | 0.037 [0.033, 0.042] | 0.034 [0.030, 0.039] | 0.000 [0.000, 0.001] | 0.262 [0.227, 0.300] | 0.062 [0.060, 0.065] |
| agg_hungarian | 0.121 [0.117, 0.125] | 0.058 [0.051, 0.065] | 0.086 [0.077, 0.094] | 0.079 [0.071, 0.087] | 0.004 [0.000, 0.013] | 0.448 [0.410, 0.488] | 0.129 [0.125, 0.133] |
| agg_idf_weighted | 0.059 [0.057, 0.062] | 0.028 [0.025, 0.032] | 0.038 [0.033, 0.043] | 0.035 [0.030, 0.039] | 0.000 [0.000, 0.001] | 0.256 [0.222, 0.295] | 0.063 [0.061, 0.066] |

## TPR gender gap (threshold chosen on dev; test; TPR_F - TPR_M over JD occupations)

| Scorer | threshold (z) | mean gap | RMS gap |
|---|---|---|---|
| agg_maxsim_mean | 1.16 | -0.002 [-0.043, 0.037] | 0.088 [0.083, 0.163] |
| agg_hungarian | 0.56 | -0.026 [-0.067, 0.013] | 0.104 [0.098, 0.173] |
| agg_idf_weighted | 1.10 | -0.005 [-0.046, 0.035] | 0.078 [0.081, 0.156] |

## Top-10 exposure (female share - 0.5; pools are 50/50)

| Scorer | top-10 share | discounted exposure |
|---|---|---|
| agg_maxsim_mean | 0.015 [-0.005, 0.034] | 0.019 [-0.002, 0.041] |
| agg_hungarian | -0.032 [-0.049, -0.011] | -0.035 [-0.056, -0.013] |
| agg_idf_weighted | 0.013 [-0.006, 0.033] | 0.015 [-0.006, 0.039] |

## Paired permutation tests: agg_maxsim_mean vs baselines (10000 sign flips, Holm within each row family)

| condition | metric | baseline | mean diff (ours - baseline) | p | p (Holm) | pools |
|---|---|---|---|---|---|---|
| original | ndcg@10 | agg_hungarian | 0.1772 | 0.0001 | 0.0002 | 200 |
| original | ndcg@10 | agg_idf_weighted | -0.0096 | 0.0021 | 0.0021 | 200 |
| pronoun_swap | abs_gap_norm_changed | agg_hungarian | -0.0311 | 0.0001 | 0.0002 | 199 |
| pronoun_swap | abs_gap_norm_changed | agg_idf_weighted | -0.0003 | 0.0143 | 0.0143 | 199 |
| name_swap_us | abs_gap_norm_changed | agg_hungarian | -0.0107 | 0.0001 | 0.0002 | 199 |
| name_swap_us | abs_gap_norm_changed | agg_idf_weighted | 0.0002 | 0.1781 | 0.1781 | 199 |
| name_swap_in | abs_gap_norm_changed | agg_hungarian | -0.0206 | 0.0001 | 0.0002 | 199 |
| name_swap_in | abs_gap_norm_changed | agg_idf_weighted | -0.0003 | 0.0299 | 0.0299 | 199 |
| name_in_same_gender | abs_gap_norm_changed | agg_hungarian | -0.0189 | 0.0001 | 0.0002 | 199 |
| name_in_same_gender | abs_gap_norm_changed | agg_idf_weighted | -0.0000 | 0.8475 | 0.8475 | 199 |
| affiliation_swap | abs_gap_norm_changed | agg_hungarian | -0.0027 | 1.0000 | 1.0000 | 45 |
| affiliation_swap | abs_gap_norm_changed | agg_idf_weighted | 0.0001 | 1.0000 | 1.0000 | 45 |
| agentic_communal | abs_gap_norm_changed | agg_hungarian | -0.0035 | 0.8937 | 0.8937 | 189 |
| agentic_communal | abs_gap_norm_changed | agg_idf_weighted | 0.0103 | 0.0001 | 0.0002 | 189 |
| gender_full | abs_gap_norm_changed | agg_hungarian | -0.0328 | 0.0001 | 0.0002 | 199 |
| gender_full | abs_gap_norm_changed | agg_idf_weighted | -0.0002 | 0.0304 | 0.0304 | 199 |

Scoring wall-clock (s): agg_maxsim_mean 141, agg_hungarian 126, agg_idf_weighted 129
