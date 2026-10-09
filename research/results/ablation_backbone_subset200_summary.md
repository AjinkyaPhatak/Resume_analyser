# PRELIMINARY SMOKE TEST (--subset 200 pools per split)

Test pools unless noted. Values: mean over JD pools [95% cluster-bootstrap CI over pools, 1000 resamples]. Gaps: |score change| / SD of the pool's original scores, over CHANGED bios. Signed gaps: + = favours the female-coded (communal / target) version.

## Ranking accuracy (test)

| Scorer | nDCG@10 | MRR | P@5 | P@10 | pairs with entities |
|---|---|---|---|---|---|
| bb_minilm | 0.443 [0.411, 0.474] | 0.662 [0.612, 0.714] | 0.438 [0.395, 0.479] | 0.357 [0.328, 0.387] | 0.764 [0.753, 0.772] |
| bb_mpnet | 0.436 [0.405, 0.468] | 0.661 [0.610, 0.716] | 0.450 [0.407, 0.492] | 0.347 [0.317, 0.376] | 0.764 [0.753, 0.772] |
| bb_jobbert_v2 | 0.486 [0.454, 0.517] | 0.690 [0.643, 0.736] | 0.501 [0.457, 0.544] | 0.394 [0.365, 0.424] | 0.764 [0.753, 0.772] |

## Counterfactual |gap| (normalised, changed bios)

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| bb_minilm | 0.069 [0.066, 0.073] | 0.041 [0.035, 0.046] | 0.054 [0.047, 0.061] | 0.052 [0.044, 0.060] | 0.000 [0.000, 0.001] | 0.447 [0.387, 0.503] | 0.074 [0.071, 0.078] |
| bb_mpnet | 0.067 [0.064, 0.071] | 0.041 [0.035, 0.047] | 0.054 [0.046, 0.061] | 0.050 [0.042, 0.059] | 0.000 [0.000, 0.000] | 0.371 [0.318, 0.421] | 0.073 [0.069, 0.076] |
| bb_jobbert_v2 | 0.061 [0.058, 0.065] | 0.041 [0.035, 0.049] | 0.051 [0.043, 0.059] | 0.048 [0.039, 0.056] | 0.000 [0.000, 0.000] | 0.275 [0.226, 0.321] | 0.067 [0.063, 0.070] |

## Signed gap (normalised, changed bios; + favours female/communal/target)

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| bb_minilm | -0.043 [-0.046, -0.040] | -0.009 [-0.015, -0.003] | -0.016 [-0.024, -0.009] | -0.018 [-0.024, -0.011] | -0.000 [-0.001, 0.000] | -0.418 [-0.475, -0.358] | -0.043 [-0.047, -0.040] |
| bb_mpnet | -0.045 [-0.048, -0.041] | -0.009 [-0.015, -0.003] | -0.017 [-0.025, -0.010] | -0.019 [-0.026, -0.012] | -0.000 [-0.000, 0.000] | -0.347 [-0.399, -0.294] | -0.045 [-0.048, -0.041] |
| bb_jobbert_v2 | -0.046 [-0.049, -0.042] | -0.009 [-0.015, -0.002] | -0.018 [-0.026, -0.010] | -0.021 [-0.028, -0.014] | 0.000 [0.000, 0.000] | -0.244 [-0.294, -0.195] | -0.045 [-0.049, -0.042] |

## Mean |rank shift| in the pool (changed bios)

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| bb_minilm | 2.229 [2.122, 2.342] | 1.209 [1.036, 1.373] | 1.571 [1.356, 1.780] | 1.561 [1.339, 1.803] | 0.000 [0.000, 0.000] | 13.799 [12.270, 15.397] | 2.388 [2.274, 2.500] |
| bb_mpnet | 2.105 [2.004, 2.212] | 1.229 [1.041, 1.416] | 1.574 [1.339, 1.793] | 1.484 [1.251, 1.719] | 0.011 [0.000, 0.033] | 10.930 [9.590, 12.483] | 2.266 [2.160, 2.378] |
| bb_jobbert_v2 | 2.258 [2.151, 2.366] | 1.354 [1.162, 1.546] | 1.709 [1.481, 1.935] | 1.594 [1.373, 1.839] | 0.000 [0.000, 0.000] | 6.958 [6.069, 7.990] | 2.438 [2.328, 2.552] |

## Entity scorers: |gap| restricted to pairs where both sides have entities

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| bb_minilm | 0.058 [0.056, 0.061] | 0.028 [0.024, 0.032] | 0.037 [0.033, 0.042] | 0.034 [0.030, 0.039] | 0.000 [0.000, 0.001] | 0.262 [0.227, 0.300] | 0.062 [0.060, 0.065] |
| bb_mpnet | 0.057 [0.054, 0.059] | 0.026 [0.023, 0.030] | 0.036 [0.032, 0.041] | 0.033 [0.029, 0.038] | 0.000 [0.000, 0.000] | 0.206 [0.178, 0.235] | 0.061 [0.058, 0.063] |
| bb_jobbert_v2 | 0.042 [0.041, 0.044] | 0.022 [0.019, 0.025] | 0.028 [0.024, 0.031] | 0.025 [0.022, 0.028] | 0.000 [0.000, 0.000] | 0.097 [0.081, 0.114] | 0.046 [0.044, 0.048] |

## TPR gender gap (threshold chosen on dev; test; TPR_F - TPR_M over JD occupations)

| Scorer | threshold (z) | mean gap | RMS gap |
|---|---|---|---|
| bb_minilm | 1.16 | -0.002 [-0.043, 0.037] | 0.088 [0.083, 0.163] |
| bb_mpnet | 1.22 | -0.009 [-0.048, 0.033] | 0.093 [0.088, 0.168] |
| bb_jobbert_v2 | 0.98 | -0.001 [-0.042, 0.037] | 0.092 [0.089, 0.168] |

## Top-10 exposure (female share - 0.5; pools are 50/50)

| Scorer | top-10 share | discounted exposure |
|---|---|---|
| bb_minilm | 0.015 [-0.005, 0.034] | 0.019 [-0.002, 0.041] |
| bb_mpnet | 0.015 [-0.005, 0.036] | 0.023 [0.003, 0.045] |
| bb_jobbert_v2 | 0.021 [0.003, 0.038] | 0.024 [0.002, 0.043] |

## Paired permutation tests: bb_minilm vs baselines (10000 sign flips, Holm within each row family)

| condition | metric | baseline | mean diff (ours - baseline) | p | p (Holm) | pools |
|---|---|---|---|---|---|---|
| original | ndcg@10 | bb_jobbert_v2 | -0.0428 | 0.0001 | 0.0002 | 200 |
| original | ndcg@10 | bb_mpnet | 0.0067 | 0.1676 | 0.1676 | 200 |
| pronoun_swap | abs_gap_norm_changed | bb_jobbert_v2 | 0.0079 | 0.0001 | 0.0002 | 199 |
| pronoun_swap | abs_gap_norm_changed | bb_mpnet | 0.0018 | 0.0046 | 0.0046 | 199 |
| name_swap_us | abs_gap_norm_changed | bb_jobbert_v2 | -0.0006 | 0.6595 | 1.0000 | 199 |
| name_swap_us | abs_gap_norm_changed | bb_mpnet | -0.0002 | 0.8207 | 1.0000 | 199 |
| name_swap_in | abs_gap_norm_changed | bb_jobbert_v2 | 0.0031 | 0.0272 | 0.0544 | 199 |
| name_swap_in | abs_gap_norm_changed | bb_mpnet | -0.0000 | 0.9936 | 0.9936 | 199 |
| name_in_same_gender | abs_gap_norm_changed | bb_jobbert_v2 | 0.0040 | 0.0012 | 0.0024 | 199 |
| name_in_same_gender | abs_gap_norm_changed | bb_mpnet | 0.0015 | 0.1458 | 0.1458 | 199 |
| affiliation_swap | abs_gap_norm_changed | bb_jobbert_v2 | 0.0003 | 1.0000 | 1.0000 | 45 |
| affiliation_swap | abs_gap_norm_changed | bb_mpnet | 0.0002 | 1.0000 | 1.0000 | 45 |
| agentic_communal | abs_gap_norm_changed | bb_jobbert_v2 | 0.1712 | 0.0001 | 0.0002 | 189 |
| agentic_communal | abs_gap_norm_changed | bb_mpnet | 0.0760 | 0.0001 | 0.0002 | 189 |
| gender_full | abs_gap_norm_changed | bb_jobbert_v2 | 0.0078 | 0.0001 | 0.0002 | 199 |
| gender_full | abs_gap_norm_changed | bb_mpnet | 0.0017 | 0.0066 | 0.0066 | 199 |

Scoring wall-clock (s): bb_minilm 136, bb_mpnet 198, bb_jobbert_v2 180
