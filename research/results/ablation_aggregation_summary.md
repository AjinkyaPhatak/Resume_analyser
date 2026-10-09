# Main results

Test pools unless noted. Values: mean over JD pools [95% cluster-bootstrap CI over pools, 1000 resamples]. Gaps: |score change| / SD of the pool's original scores, over CHANGED bios. Signed gaps: + = favours the female-coded (communal / target) version.

## Ranking accuracy (test)

| Scorer | nDCG@10 | MRR | P@5 | P@10 | pairs with entities |
|---|---|---|---|---|---|
| agg_maxsim_mean | 0.441 [0.412, 0.471] | 0.662 [0.617, 0.710] | 0.436 [0.398, 0.474] | 0.356 [0.328, 0.383] | 0.765 [0.755, 0.772] |
| agg_hungarian | 0.267 [0.245, 0.288] | 0.468 [0.421, 0.515] | 0.259 [0.230, 0.290] | 0.214 [0.194, 0.235] | 0.765 [0.755, 0.772] |
| agg_idf_weighted | 0.452 [0.422, 0.481] | 0.674 [0.630, 0.717] | 0.443 [0.406, 0.482] | 0.365 [0.338, 0.393] | 0.765 [0.755, 0.772] |

## Counterfactual |gap| (normalised, changed bios)

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| agg_maxsim_mean | 0.070 [0.067, 0.073] | 0.040 [0.035, 0.046] | 0.052 [0.045, 0.058] | 0.052 [0.044, 0.060] | 0.000 [0.000, 0.001] | 0.450 [0.397, 0.503] | 0.075 [0.072, 0.078] |
| agg_hungarian | 0.101 [0.099, 0.104] | 0.052 [0.047, 0.058] | 0.074 [0.067, 0.082] | 0.071 [0.065, 0.079] | 0.003 [0.000, 0.008] | 0.447 [0.410, 0.480] | 0.108 [0.106, 0.111] |
| agg_idf_weighted | 0.070 [0.067, 0.073] | 0.040 [0.035, 0.046] | 0.052 [0.045, 0.058] | 0.052 [0.044, 0.060] | 0.000 [0.000, 0.001] | 0.439 [0.387, 0.491] | 0.075 [0.072, 0.078] |

## Signed gap (normalised, changed bios; + favours female/communal/target)

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| agg_maxsim_mean | -0.043 [-0.047, -0.040] | -0.009 [-0.014, -0.003] | -0.016 [-0.023, -0.009] | -0.019 [-0.026, -0.012] | -0.000 [-0.001, 0.000] | -0.422 [-0.479, -0.368] | -0.044 [-0.047, -0.040] |
| agg_hungarian | -0.073 [-0.076, -0.070] | -0.015 [-0.020, -0.010] | -0.011 [-0.018, -0.004] | -0.032 [-0.039, -0.025] | -0.003 [-0.008, 0.000] | -0.413 [-0.448, -0.374] | -0.075 [-0.078, -0.071] |
| agg_idf_weighted | -0.044 [-0.047, -0.041] | -0.009 [-0.014, -0.003] | -0.016 [-0.023, -0.009] | -0.019 [-0.026, -0.013] | -0.000 [-0.001, 0.000] | -0.409 [-0.465, -0.356] | -0.044 [-0.048, -0.041] |

## Mean |rank shift| in the pool (changed bios)

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| agg_maxsim_mean | 2.259 [2.163, 2.368] | 1.200 [1.059, 1.363] | 1.516 [1.331, 1.707] | 1.566 [1.367, 1.785] | 0.000 [0.000, 0.000] | 13.739 [12.302, 15.117] | 2.417 [2.316, 2.523] |
| agg_hungarian | 2.514 [2.424, 2.614] | 1.244 [1.113, 1.396] | 1.676 [1.507, 1.855] | 1.674 [1.494, 1.876] | 0.029 [0.000, 0.088] | 13.261 [12.023, 14.520] | 2.689 [2.600, 2.787] |
| agg_idf_weighted | 2.242 [2.147, 2.349] | 1.183 [1.040, 1.342] | 1.517 [1.336, 1.717] | 1.563 [1.359, 1.784] | 0.000 [0.000, 0.000] | 13.270 [11.892, 14.591] | 2.398 [2.296, 2.507] |

## Entity scorers: |gap| restricted to pairs where both sides have entities

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| agg_maxsim_mean | 0.059 [0.057, 0.062] | 0.028 [0.025, 0.032] | 0.037 [0.033, 0.041] | 0.034 [0.030, 0.038] | 0.000 [0.000, 0.001] | 0.268 [0.235, 0.303] | 0.063 [0.061, 0.066] |
| agg_hungarian | 0.123 [0.119, 0.126] | 0.059 [0.053, 0.066] | 0.086 [0.078, 0.095] | 0.080 [0.072, 0.087] | 0.004 [0.000, 0.011] | 0.444 [0.407, 0.479] | 0.131 [0.128, 0.135] |
| agg_idf_weighted | 0.060 [0.058, 0.062] | 0.029 [0.025, 0.032] | 0.037 [0.033, 0.042] | 0.034 [0.030, 0.038] | 0.000 [0.000, 0.001] | 0.262 [0.229, 0.297] | 0.064 [0.062, 0.067] |

## TPR gender gap (threshold chosen on dev; TPR_F - TPR_M over JD occupations)

| Scorer | threshold (z) | mean gap | RMS gap |
|---|---|---|---|
| agg_maxsim_mean | 1.16 | -0.009 [-0.044, 0.027] | 0.089 (no CI: bootstrap invalid for RMS here) |
| agg_hungarian | 0.56 | -0.021 [-0.057, 0.016] | 0.102 (no CI: bootstrap invalid for RMS here) |
| agg_idf_weighted | 1.10 | -0.007 [-0.045, 0.029] | 0.082 (no CI: bootstrap invalid for RMS here) |

## Top-10 exposure (female share - 0.5; pools are 50/50)

| Scorer | top-10 share | discounted exposure |
|---|---|---|
| agg_maxsim_mean | 0.007 [-0.010, 0.026] | 0.014 [-0.006, 0.034] |
| agg_hungarian | -0.036 [-0.053, -0.019] | -0.043 [-0.062, -0.023] |
| agg_idf_weighted | 0.005 [-0.013, 0.023] | 0.010 [-0.010, 0.030] |

## Paired permutation tests: agg_maxsim_mean vs baselines (10000 sign flips, Holm within each row family)

| condition | metric | baseline | mean diff (ours - baseline) | p | p (Holm) | pools |
|---|---|---|---|---|---|---|
| original | ndcg@10 | agg_hungarian | 0.1742 | 0.0001 | 0.0002 | 234 |
| original | ndcg@10 | agg_idf_weighted | -0.0105 | 0.0002 | 0.0002 | 234 |
| pronoun_swap | abs_gap_norm_changed | agg_hungarian | -0.0317 | 0.0001 | 0.0002 | 233 |
| pronoun_swap | abs_gap_norm_changed | agg_idf_weighted | -0.0003 | 0.0064 | 0.0064 | 233 |
| name_swap_us | abs_gap_norm_changed | agg_hungarian | -0.0120 | 0.0001 | 0.0002 | 233 |
| name_swap_us | abs_gap_norm_changed | agg_idf_weighted | 0.0002 | 0.2324 | 0.2324 | 233 |
| name_swap_in | abs_gap_norm_changed | agg_hungarian | -0.0228 | 0.0001 | 0.0002 | 233 |
| name_swap_in | abs_gap_norm_changed | agg_idf_weighted | -0.0003 | 0.0360 | 0.0360 | 233 |
| name_in_same_gender | abs_gap_norm_changed | agg_hungarian | -0.0195 | 0.0001 | 0.0002 | 233 |
| name_in_same_gender | abs_gap_norm_changed | agg_idf_weighted | -0.0001 | 0.5298 | 0.5298 | 233 |
| affiliation_swap | abs_gap_norm_changed | agg_hungarian | -0.0024 | 1.0000 | 1.0000 | 51 |
| affiliation_swap | abs_gap_norm_changed | agg_idf_weighted | 0.0001 | 1.0000 | 1.0000 | 51 |
| agentic_communal | abs_gap_norm_changed | agg_hungarian | 0.0032 | 0.8931 | 0.8931 | 223 |
| agentic_communal | abs_gap_norm_changed | agg_idf_weighted | 0.0111 | 0.0001 | 0.0002 | 223 |
| gender_full | abs_gap_norm_changed | agg_hungarian | -0.0335 | 0.0001 | 0.0002 | 233 |
| gender_full | abs_gap_norm_changed | agg_idf_weighted | -0.0002 | 0.0194 | 0.0194 | 233 |

Scoring wall-clock (s): agg_maxsim_mean 78, agg_hungarian 69, agg_idf_weighted 67
