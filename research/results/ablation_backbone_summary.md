# Main results

Test pools unless noted. Values: mean over JD pools [95% cluster-bootstrap CI over pools, 1000 resamples]. Gaps: |score change| / SD of the pool's original scores, over CHANGED bios. Signed gaps: + = favours the female-coded (communal / target) version.

## Ranking accuracy (test)

| Scorer | nDCG@10 | MRR | P@5 | P@10 | pairs with entities |
|---|---|---|---|---|---|
| bb_minilm | 0.441 [0.412, 0.471] | 0.662 [0.617, 0.710] | 0.436 [0.398, 0.474] | 0.356 [0.328, 0.383] | 0.765 [0.755, 0.772] |
| bb_mpnet | 0.433 [0.403, 0.463] | 0.657 [0.610, 0.705] | 0.445 [0.407, 0.484] | 0.345 [0.317, 0.374] | 0.765 [0.755, 0.772] |
| bb_jobbert_v2 | 0.486 [0.455, 0.517] | 0.690 [0.647, 0.733] | 0.502 [0.461, 0.540] | 0.395 [0.364, 0.423] | 0.765 [0.755, 0.772] |

## Counterfactual |gap| (normalised, changed bios)

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| bb_minilm | 0.070 [0.067, 0.073] | 0.040 [0.035, 0.046] | 0.052 [0.045, 0.058] | 0.052 [0.044, 0.060] | 0.000 [0.000, 0.001] | 0.450 [0.397, 0.503] | 0.075 [0.072, 0.078] |
| bb_mpnet | 0.067 [0.064, 0.070] | 0.040 [0.035, 0.046] | 0.052 [0.045, 0.059] | 0.051 [0.043, 0.059] | 0.000 [0.000, 0.000] | 0.373 [0.322, 0.421] | 0.073 [0.070, 0.076] |
| bb_jobbert_v2 | 0.061 [0.058, 0.064] | 0.041 [0.034, 0.047] | 0.048 [0.042, 0.055] | 0.049 [0.041, 0.056] | 0.000 [0.000, 0.000] | 0.281 [0.235, 0.325] | 0.067 [0.064, 0.070] |

## Signed gap (normalised, changed bios; + favours female/communal/target)

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| bb_minilm | -0.043 [-0.047, -0.040] | -0.009 [-0.014, -0.003] | -0.016 [-0.023, -0.009] | -0.019 [-0.026, -0.012] | -0.000 [-0.001, 0.000] | -0.422 [-0.479, -0.368] | -0.044 [-0.047, -0.040] |
| bb_mpnet | -0.045 [-0.048, -0.042] | -0.010 [-0.015, -0.004] | -0.017 [-0.024, -0.010] | -0.020 [-0.027, -0.013] | -0.000 [-0.000, 0.000] | -0.350 [-0.400, -0.300] | -0.045 [-0.048, -0.042] |
| bb_jobbert_v2 | -0.046 [-0.049, -0.043] | -0.009 [-0.014, -0.002] | -0.017 [-0.024, -0.010] | -0.023 [-0.030, -0.016] | 0.000 [0.000, 0.000] | -0.250 [-0.297, -0.203] | -0.046 [-0.049, -0.042] |

## Mean |rank shift| in the pool (changed bios)

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| bb_minilm | 2.259 [2.163, 2.368] | 1.200 [1.059, 1.363] | 1.516 [1.331, 1.707] | 1.566 [1.367, 1.785] | 0.000 [0.000, 0.000] | 13.739 [12.302, 15.117] | 2.417 [2.316, 2.523] |
| bb_mpnet | 2.101 [2.007, 2.204] | 1.215 [1.065, 1.389] | 1.521 [1.339, 1.728] | 1.490 [1.289, 1.717] | 0.010 [0.000, 0.029] | 10.974 [9.713, 12.164] | 2.264 [2.166, 2.370] |
| bb_jobbert_v2 | 2.256 [2.162, 2.356] | 1.345 [1.173, 1.538] | 1.657 [1.470, 1.867] | 1.626 [1.421, 1.846] | 0.000 [0.000, 0.000] | 7.058 [6.178, 7.880] | 2.443 [2.346, 2.549] |

## Entity scorers: |gap| restricted to pairs where both sides have entities

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| bb_minilm | 0.059 [0.057, 0.062] | 0.028 [0.025, 0.032] | 0.037 [0.033, 0.041] | 0.034 [0.030, 0.038] | 0.000 [0.000, 0.001] | 0.268 [0.235, 0.303] | 0.063 [0.061, 0.066] |
| bb_mpnet | 0.057 [0.055, 0.059] | 0.027 [0.023, 0.030] | 0.036 [0.032, 0.041] | 0.033 [0.029, 0.037] | 0.000 [0.000, 0.000] | 0.210 [0.184, 0.237] | 0.061 [0.059, 0.063] |
| bb_jobbert_v2 | 0.043 [0.041, 0.045] | 0.022 [0.019, 0.025] | 0.028 [0.025, 0.031] | 0.025 [0.022, 0.028] | 0.000 [0.000, 0.000] | 0.104 [0.087, 0.119] | 0.046 [0.045, 0.048] |

## TPR gender gap (threshold chosen on dev; TPR_F - TPR_M over JD occupations)

| Scorer | threshold (z) | mean gap | RMS gap |
|---|---|---|---|
| bb_minilm | 1.16 | -0.009 [-0.044, 0.027] | 0.089 (no CI: bootstrap invalid for RMS here) |
| bb_mpnet | 1.22 | -0.011 [-0.047, 0.025] | 0.098 (no CI: bootstrap invalid for RMS here) |
| bb_jobbert_v2 | 0.98 | -0.003 [-0.038, 0.034] | 0.095 (no CI: bootstrap invalid for RMS here) |

## Top-10 exposure (female share - 0.5; pools are 50/50)

| Scorer | top-10 share | discounted exposure |
|---|---|---|
| bb_minilm | 0.007 [-0.010, 0.026] | 0.014 [-0.006, 0.034] |
| bb_mpnet | 0.010 [-0.009, 0.031] | 0.018 [-0.004, 0.039] |
| bb_jobbert_v2 | 0.017 [-0.001, 0.034] | 0.021 [0.000, 0.039] |

## Paired permutation tests: bb_minilm vs baselines (10000 sign flips, Holm within each row family)

| condition | metric | baseline | mean diff (ours - baseline) | p | p (Holm) | pools |
|---|---|---|---|---|---|---|
| original | ndcg@10 | bb_jobbert_v2 | -0.0451 | 0.0001 | 0.0002 | 234 |
| original | ndcg@10 | bb_mpnet | 0.0078 | 0.0989 | 0.0989 | 234 |
| pronoun_swap | abs_gap_norm_changed | bb_jobbert_v2 | 0.0085 | 0.0001 | 0.0002 | 233 |
| pronoun_swap | abs_gap_norm_changed | bb_mpnet | 0.0024 | 0.0001 | 0.0002 | 233 |
| name_swap_us | abs_gap_norm_changed | bb_jobbert_v2 | -0.0003 | 0.8095 | 1.0000 | 233 |
| name_swap_us | abs_gap_norm_changed | bb_mpnet | 0.0000 | 0.9908 | 1.0000 | 233 |
| name_swap_in | abs_gap_norm_changed | bb_jobbert_v2 | 0.0031 | 0.0209 | 0.0418 | 233 |
| name_swap_in | abs_gap_norm_changed | bb_mpnet | -0.0003 | 0.7790 | 0.7790 | 233 |
| name_in_same_gender | abs_gap_norm_changed | bb_jobbert_v2 | 0.0032 | 0.0066 | 0.0132 | 233 |
| name_in_same_gender | abs_gap_norm_changed | bb_mpnet | 0.0012 | 0.2026 | 0.2026 | 233 |
| affiliation_swap | abs_gap_norm_changed | bb_jobbert_v2 | 0.0003 | 1.0000 | 1.0000 | 51 |
| affiliation_swap | abs_gap_norm_changed | bb_mpnet | 0.0002 | 1.0000 | 1.0000 | 51 |
| agentic_communal | abs_gap_norm_changed | bb_jobbert_v2 | 0.1688 | 0.0001 | 0.0002 | 223 |
| agentic_communal | abs_gap_norm_changed | bb_mpnet | 0.0765 | 0.0001 | 0.0002 | 223 |
| gender_full | abs_gap_norm_changed | bb_jobbert_v2 | 0.0083 | 0.0001 | 0.0002 | 233 |
| gender_full | abs_gap_norm_changed | bb_mpnet | 0.0024 | 0.0001 | 0.0002 | 233 |

Scoring wall-clock (s): bb_minilm 65, bb_mpnet 66, bb_jobbert_v2 62
