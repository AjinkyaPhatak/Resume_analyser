# Main results

Test pools unless noted. Values: mean over JD pools [95% cluster-bootstrap CI over pools, 1000 resamples]. Gaps: |score change| / SD of the pool's original scores, over CHANGED bios. Signed gaps: + = favours the female-coded (communal / target) version.

## Ranking accuracy (test)

| Scorer | nDCG@10 | MRR | P@5 | P@10 | pairs with entities |
|---|---|---|---|---|---|
| ex_noun_chunk | 0.477 [0.452, 0.502] | 0.742 [0.699, 0.786] | 0.483 [0.448, 0.516] | 0.371 [0.347, 0.396] | 1.000 [1.000, 1.000] |
| ex_esco | 0.378 [0.345, 0.410] | 0.570 [0.519, 0.617] | 0.382 [0.345, 0.421] | 0.310 [0.282, 0.339] | 0.695 [0.684, 0.704] |
| ex_jobbert_ft | 0.324 [0.299, 0.350] | 0.609 [0.558, 0.660] | 0.328 [0.295, 0.361] | 0.245 [0.223, 0.269] | 0.373 [0.364, 0.382] |
| ex_union | 0.441 [0.412, 0.471] | 0.662 [0.617, 0.710] | 0.436 [0.398, 0.474] | 0.356 [0.328, 0.383] | 0.765 [0.755, 0.772] |

## Counterfactual |gap| (normalised, changed bios)

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| ex_noun_chunk | 0.163 [0.153, 0.171] | 0.031 [0.029, 0.033] | 0.032 [0.030, 0.034] | 0.029 [0.028, 0.031] | 0.139 [0.094, 0.191] | 0.051 [0.044, 0.058] | 0.164 [0.155, 0.172] |
| ex_esco | 0.000 [0.000, 0.000] | 0.007 [0.005, 0.010] | 0.002 [0.001, 0.003] | 0.002 [0.001, 0.003] | 0.000 [0.000, 0.000] | 0.563 [0.498, 0.635] | 0.002 [0.001, 0.002] |
| ex_jobbert_ft | 0.161 [0.155, 0.167] | 0.069 [0.061, 0.077] | 0.108 [0.097, 0.119] | 0.102 [0.092, 0.113] | 0.000 [0.000, 0.001] | 0.159 [0.124, 0.197] | 0.170 [0.164, 0.176] |
| ex_union | 0.070 [0.067, 0.073] | 0.040 [0.035, 0.046] | 0.052 [0.045, 0.058] | 0.052 [0.044, 0.060] | 0.000 [0.000, 0.001] | 0.450 [0.397, 0.503] | 0.075 [0.072, 0.078] |

## Signed gap (normalised, changed bios; + favours female/communal/target)

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| ex_noun_chunk | 0.153 [0.144, 0.162] | -0.002 [-0.004, 0.000] | -0.002 [-0.004, 0.000] | -0.005 [-0.007, -0.003] | -0.123 [-0.179, -0.073] | 0.027 [0.018, 0.035] | 0.152 [0.143, 0.161] |
| ex_esco | 0.000 [-0.000, 0.000] | 0.006 [0.004, 0.009] | 0.001 [0.000, 0.002] | -0.002 [-0.003, -0.001] | 0.000 [0.000, 0.000] | -0.559 [-0.632, -0.494] | 0.001 [0.001, 0.002] |
| ex_jobbert_ft | -0.118 [-0.124, -0.112] | -0.021 [-0.028, -0.013] | -0.026 [-0.037, -0.015] | -0.036 [-0.046, -0.026] | -0.000 [-0.001, 0.000] | -0.022 [-0.062, 0.016] | -0.120 [-0.126, -0.114] |
| ex_union | -0.043 [-0.047, -0.040] | -0.009 [-0.014, -0.003] | -0.016 [-0.023, -0.009] | -0.019 [-0.026, -0.012] | -0.000 [-0.001, 0.000] | -0.422 [-0.479, -0.368] | -0.044 [-0.047, -0.040] |

## Mean |rank shift| in the pool (changed bios)

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| ex_noun_chunk | 4.351 [4.091, 4.601] | 0.835 [0.775, 0.895] | 0.857 [0.799, 0.916] | 0.795 [0.741, 0.853] | 4.503 [2.692, 6.719] | 1.315 [1.092, 1.602] | 4.377 [4.121, 4.628] |
| ex_esco | 0.006 [0.002, 0.012] | 0.156 [0.104, 0.213] | 0.048 [0.025, 0.075] | 0.048 [0.025, 0.075] | 0.000 [0.000, 0.000] | 18.050 [16.282, 20.136] | 0.039 [0.027, 0.052] |
| ex_jobbert_ft | 3.753 [3.601, 3.907] | 1.575 [1.364, 1.803] | 2.546 [2.274, 2.829] | 2.388 [2.140, 2.667] | 0.000 [0.000, 0.000] | 3.745 [2.807, 4.673] | 3.969 [3.809, 4.129] |
| ex_union | 2.259 [2.163, 2.368] | 1.200 [1.059, 1.363] | 1.516 [1.331, 1.707] | 1.566 [1.367, 1.785] | 0.000 [0.000, 0.000] | 13.739 [12.302, 15.117] | 2.417 [2.316, 2.523] |

## Entity scorers: |gap| restricted to pairs where both sides have entities

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| ex_esco | 0.000 [0.000, 0.000] | 0.002 [0.001, 0.002] | 0.001 [0.001, 0.002] | 0.001 [0.001, 0.002] | 0.000 [0.000, 0.000] | 0.286 [0.249, 0.325] | 0.000 [0.000, 0.001] |
| ex_jobbert_ft | 0.161 [0.154, 0.167] | 0.073 [0.064, 0.082] | 0.092 [0.082, 0.102] | 0.084 [0.075, 0.094] | 0.001 [0.000, 0.002] | 0.118 [0.088, 0.151] | 0.173 [0.166, 0.179] |
| ex_union | 0.059 [0.057, 0.062] | 0.028 [0.025, 0.032] | 0.037 [0.033, 0.041] | 0.034 [0.030, 0.038] | 0.000 [0.000, 0.001] | 0.268 [0.235, 0.303] | 0.063 [0.061, 0.066] |

## TPR gender gap (threshold chosen on dev; TPR_F - TPR_M over JD occupations)

| Scorer | threshold (z) | mean gap | RMS gap |
|---|---|---|---|
| ex_noun_chunk | 1.32 | 0.042 [0.007, 0.078] | 0.101 (no CI: bootstrap invalid for RMS here) |
| ex_esco | 1.02 | -0.005 [-0.044, 0.032] | 0.073 (no CI: bootstrap invalid for RMS here) |
| ex_jobbert_ft | 1.47 | -0.012 [-0.049, 0.024] | 0.068 (no CI: bootstrap invalid for RMS here) |
| ex_union | 1.16 | -0.009 [-0.044, 0.027] | 0.089 (no CI: bootstrap invalid for RMS here) |

## Top-10 exposure (female share - 0.5; pools are 50/50)

| Scorer | top-10 share | discounted exposure |
|---|---|---|
| ex_noun_chunk | 0.071 [0.054, 0.088] | 0.082 [0.064, 0.100] |
| ex_esco | -0.010 [-0.028, 0.008] | -0.006 [-0.027, 0.014] |
| ex_jobbert_ft | -0.017 [-0.034, 0.002] | -0.016 [-0.035, 0.006] |
| ex_union | 0.007 [-0.010, 0.026] | 0.014 [-0.006, 0.034] |

## Paired permutation tests: ex_union vs baselines (10000 sign flips, Holm within each row family)

| condition | metric | baseline | mean diff (ours - baseline) | p | p (Holm) | pools |
|---|---|---|---|---|---|---|
| original | ndcg@10 | ex_esco | 0.0628 | 0.0001 | 0.0003 | 234 |
| original | ndcg@10 | ex_jobbert_ft | 0.1170 | 0.0001 | 0.0003 | 234 |
| original | ndcg@10 | ex_noun_chunk | -0.0364 | 0.0181 | 0.0181 | 234 |
| pronoun_swap | abs_gap_norm_changed | ex_esco | 0.0696 | 0.0001 | 0.0003 | 232 |
| pronoun_swap | abs_gap_norm_changed | ex_jobbert_ft | -0.0908 | 0.0001 | 0.0003 | 227 |
| pronoun_swap | abs_gap_norm_changed | ex_noun_chunk | -0.0920 | 0.0001 | 0.0003 | 233 |
| name_swap_us | abs_gap_norm_changed | ex_esco | 0.0332 | 0.0001 | 0.0003 | 232 |
| name_swap_us | abs_gap_norm_changed | ex_jobbert_ft | -0.0280 | 0.0001 | 0.0003 | 227 |
| name_swap_us | abs_gap_norm_changed | ex_noun_chunk | 0.0095 | 0.0020 | 0.0020 | 233 |
| name_swap_in | abs_gap_norm_changed | ex_esco | 0.0501 | 0.0001 | 0.0003 | 232 |
| name_swap_in | abs_gap_norm_changed | ex_jobbert_ft | -0.0551 | 0.0001 | 0.0003 | 227 |
| name_swap_in | abs_gap_norm_changed | ex_noun_chunk | 0.0199 | 0.0001 | 0.0003 | 233 |
| name_in_same_gender | abs_gap_norm_changed | ex_esco | 0.0505 | 0.0001 | 0.0003 | 232 |
| name_in_same_gender | abs_gap_norm_changed | ex_jobbert_ft | -0.0495 | 0.0001 | 0.0003 | 227 |
| name_in_same_gender | abs_gap_norm_changed | ex_noun_chunk | 0.0227 | 0.0001 | 0.0003 | 233 |
| affiliation_swap | abs_gap_norm_changed | ex_esco | 0.0003 | 1.0000 | 1.0000 | 51 |
| affiliation_swap | abs_gap_norm_changed | ex_jobbert_ft | -0.0001 | 1.0000 | 1.0000 | 51 |
| affiliation_swap | abs_gap_norm_changed | ex_noun_chunk | -0.1386 | 0.0001 | 0.0003 | 51 |
| agentic_communal | abs_gap_norm_changed | ex_esco | -0.1126 | 0.0001 | 0.0003 | 222 |
| agentic_communal | abs_gap_norm_changed | ex_jobbert_ft | 0.2945 | 0.0001 | 0.0003 | 217 |
| agentic_communal | abs_gap_norm_changed | ex_noun_chunk | 0.3989 | 0.0001 | 0.0003 | 223 |
| gender_full | abs_gap_norm_changed | ex_esco | 0.0734 | 0.0001 | 0.0003 | 232 |
| gender_full | abs_gap_norm_changed | ex_jobbert_ft | -0.0948 | 0.0001 | 0.0003 | 227 |
| gender_full | abs_gap_norm_changed | ex_noun_chunk | -0.0877 | 0.0001 | 0.0003 | 233 |

Scoring wall-clock (s): ex_noun_chunk 67, ex_esco 76, ex_jobbert_ft 69, ex_union 67
