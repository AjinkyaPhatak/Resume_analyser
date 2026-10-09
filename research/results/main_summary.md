# Main results

Test pools unless noted. Values: mean over JD pools [95% cluster-bootstrap CI over pools, 1000 resamples]. Gaps: |score change| / SD of the pool's original scores, over CHANGED bios. Signed gaps: + = favours the female-coded (communal / target) version.

## Ranking accuracy (test)

| Scorer | nDCG@10 | MRR | P@5 | P@10 | pairs with entities |
|---|---|---|---|---|---|
| bm25 | 0.541 [0.514, 0.570] | 0.799 [0.759, 0.838] | 0.582 [0.546, 0.621] | 0.441 [0.417, 0.469] | 1.000 [1.000, 1.000] |
| tfidf | 0.518 [0.494, 0.543] | 0.791 [0.753, 0.830] | 0.555 [0.518, 0.589] | 0.421 [0.398, 0.445] | 1.000 [1.000, 1.000] |
| sbert_minilm | 0.602 [0.574, 0.631] | 0.836 [0.799, 0.874] | 0.635 [0.598, 0.674] | 0.498 [0.471, 0.526] | 1.000 [1.000, 1.000] |
| sbert_mpnet | 0.633 [0.606, 0.661] | 0.859 [0.822, 0.893] | 0.650 [0.615, 0.686] | 0.535 [0.509, 0.560] | 1.000 [1.000, 1.000] |
| jobbert_v2 | 0.716 [0.692, 0.739] | 0.907 [0.877, 0.933] | 0.743 [0.711, 0.774] | 0.613 [0.589, 0.637] | 1.000 [1.000, 1.000] |
| cross_encoder | 0.401 [0.375, 0.427] | 0.657 [0.609, 0.701] | 0.407 [0.372, 0.441] | 0.322 [0.299, 0.345] | 1.000 [1.000, 1.000] |
| backend_match | 0.535 [0.508, 0.563] | 0.793 [0.751, 0.833] | 0.552 [0.519, 0.588] | 0.438 [0.414, 0.463] | 1.000 [1.000, 1.000] |
| entity_li | 0.619 [0.592, 0.644] | 0.843 [0.805, 0.879] | 0.641 [0.608, 0.676] | 0.518 [0.493, 0.545] | 1.000 [1.000, 1.000] |

## Counterfactual |gap| (normalised, changed bios)

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| bm25 | 0.000 [0.000, 0.001] | 0.002 [0.001, 0.003] | 0.001 [0.000, 0.002] | 0.001 [0.000, 0.002] | 0.047 [0.011, 0.098] | 0.056 [0.042, 0.072] | 0.001 [0.000, 0.001] |
| tfidf | 0.001 [0.000, 0.001] | 0.019 [0.017, 0.021] | 0.032 [0.030, 0.034] | 0.032 [0.029, 0.034] | 0.062 [0.022, 0.115] | 0.071 [0.055, 0.090] | 0.005 [0.004, 0.005] |
| sbert_minilm | 0.135 [0.125, 0.146] | 0.280 [0.270, 0.290] | 0.294 [0.283, 0.305] | 0.284 [0.274, 0.294] | 0.068 [0.052, 0.085] | 0.045 [0.039, 0.051] | 0.181 [0.169, 0.192] |
| sbert_mpnet | 0.117 [0.109, 0.126] | 0.216 [0.207, 0.224] | 0.233 [0.224, 0.242] | 0.227 [0.218, 0.235] | 0.076 [0.055, 0.101] | 0.046 [0.042, 0.052] | 0.149 [0.141, 0.159] |
| jobbert_v2 | 0.107 [0.100, 0.114] | 0.135 [0.129, 0.141] | 0.189 [0.182, 0.196] | 0.188 [0.180, 0.195] | 0.057 [0.035, 0.088] | 0.058 [0.052, 0.065] | 0.126 [0.118, 0.132] |
| cross_encoder | 0.103 [0.096, 0.111] | 0.156 [0.149, 0.163] | 0.212 [0.204, 0.221] | 0.203 [0.195, 0.211] | 0.108 [0.083, 0.138] | 0.058 [0.051, 0.067] | 0.121 [0.114, 0.129] |
| backend_match | 0.272 [0.239, 0.301] | 0.008 [0.006, 0.010] | 0.010 [0.008, 0.013] | 0.007 [0.006, 0.009] | 0.069 [0.035, 0.106] | 0.051 [0.037, 0.067] | 0.272 [0.239, 0.301] |
| entity_li | 0.022 [0.021, 0.023] | 0.058 [0.054, 0.062] | 0.064 [0.061, 0.067] | 0.058 [0.055, 0.062] | 0.046 [0.030, 0.065] | 0.066 [0.056, 0.076] | 0.033 [0.031, 0.035] |

## Signed gap (normalised, changed bios; + favours female/communal/target)

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| bm25 | 0.000 [0.000, 0.001] | -0.001 [-0.002, 0.001] | -0.001 [-0.002, 0.000] | -0.001 [-0.002, -0.000] | -0.030 [-0.085, 0.010] | 0.018 [0.004, 0.035] | 0.000 [-0.000, 0.001] |
| tfidf | 0.001 [0.000, 0.001] | -0.007 [-0.009, -0.005] | -0.001 [-0.004, 0.001] | -0.022 [-0.024, -0.019] | -0.039 [-0.094, 0.005] | 0.021 [0.003, 0.040] | -0.001 [-0.001, -0.000] |
| sbert_minilm | 0.094 [0.078, 0.110] | 0.028 [0.012, 0.043] | 0.051 [0.038, 0.065] | 0.009 [-0.007, 0.025] | -0.045 [-0.065, -0.025] | 0.021 [0.015, 0.028] | 0.099 [0.081, 0.118] |
| sbert_mpnet | 0.087 [0.075, 0.098] | 0.051 [0.040, 0.063] | 0.015 [0.004, 0.026] | -0.075 [-0.089, -0.062] | -0.047 [-0.074, -0.020] | 0.004 [-0.003, 0.010] | 0.097 [0.084, 0.109] |
| jobbert_v2 | 0.045 [0.033, 0.057] | 0.026 [0.019, 0.033] | 0.021 [0.013, 0.028] | -0.007 [-0.018, 0.002] | 0.014 [-0.014, 0.049] | 0.036 [0.028, 0.044] | 0.049 [0.036, 0.062] |
| cross_encoder | -0.040 [-0.053, -0.027] | 0.024 [0.017, 0.033] | 0.032 [0.024, 0.041] | 0.093 [0.086, 0.103] | -0.075 [-0.111, -0.042] | -0.016 [-0.026, -0.005] | -0.037 [-0.050, -0.023] |
| backend_match | 0.259 [0.225, 0.290] | -0.000 [-0.002, 0.002] | -0.001 [-0.003, 0.002] | -0.002 [-0.004, -0.000] | -0.047 [-0.087, -0.009] | 0.026 [0.011, 0.042] | 0.258 [0.224, 0.289] |
| entity_li | -0.007 [-0.008, -0.006] | 0.008 [0.004, 0.012] | 0.008 [0.005, 0.012] | 0.004 [-0.000, 0.008] | -0.016 [-0.037, 0.004] | -0.046 [-0.057, -0.036] | -0.005 [-0.006, -0.004] |

## Mean |rank shift| in the pool (changed bios)

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| bm25 | 0.016 [0.005, 0.032] | 0.056 [0.021, 0.098] | 0.031 [0.003, 0.067] | 0.031 [0.003, 0.067] | 1.549 [0.216, 3.295] | 1.659 [1.222, 2.194] | 0.026 [0.014, 0.042] |
| tfidf | 0.027 [0.014, 0.045] | 0.424 [0.373, 0.481] | 0.733 [0.673, 0.792] | 0.706 [0.653, 0.764] | 1.771 [0.425, 3.549] | 2.105 [1.558, 2.702] | 0.113 [0.097, 0.134] |
| sbert_minilm | 3.890 [3.589, 4.213] | 8.086 [7.766, 8.434] | 8.534 [8.204, 8.860] | 8.192 [7.871, 8.484] | 2.095 [1.353, 3.036] | 1.223 [1.034, 1.423] | 5.196 [4.866, 5.526] |
| sbert_mpnet | 3.456 [3.226, 3.713] | 6.402 [6.145, 6.670] | 6.871 [6.566, 7.142] | 6.773 [6.493, 7.045] | 2.131 [1.264, 3.154] | 1.245 [1.074, 1.422] | 4.424 [4.181, 4.708] |
| jobbert_v2 | 3.457 [3.224, 3.659] | 4.304 [4.124, 4.491] | 6.033 [5.784, 6.277] | 6.013 [5.768, 6.275] | 1.474 [0.922, 2.085] | 1.742 [1.516, 1.992] | 4.054 [3.817, 4.265] |
| cross_encoder | 3.195 [2.965, 3.447] | 4.450 [4.239, 4.670] | 6.240 [5.978, 6.528] | 5.917 [5.656, 6.182] | 2.480 [1.578, 3.539] | 1.665 [1.483, 1.864] | 3.681 [3.460, 3.932] |
| backend_match | 10.119 [9.051, 11.127] | 0.226 [0.164, 0.288] | 0.275 [0.212, 0.338] | 0.207 [0.154, 0.266] | 1.967 [0.894, 3.319] | 1.345 [0.988, 1.753] | 10.101 [9.046, 11.103] |
| entity_li | 0.650 [0.615, 0.687] | 1.774 [1.643, 1.920] | 1.906 [1.792, 2.020] | 1.697 [1.591, 1.802] | 1.500 [0.899, 2.236] | 1.973 [1.668, 2.262] | 0.979 [0.931, 1.031] |

## TPR gender gap (threshold chosen on dev; TPR_F - TPR_M over JD occupations)

| Scorer | threshold (z) | mean gap | RMS gap |
|---|---|---|---|
| bm25 | 1.48 | 0.009 [-0.032, 0.046] | 0.131 (no CI: bootstrap invalid for RMS here) |
| tfidf | 1.27 | 0.031 [-0.009, 0.070] | 0.123 (no CI: bootstrap invalid for RMS here) |
| sbert_minilm | 1.44 | 0.063 [0.026, 0.102] | 0.136 (no CI: bootstrap invalid for RMS here) |
| sbert_mpnet | 1.32 | 0.057 [0.017, 0.101] | 0.134 (no CI: bootstrap invalid for RMS here) |
| jobbert_v2 | 1.42 | 0.018 [-0.021, 0.055] | 0.134 (no CI: bootstrap invalid for RMS here) |
| cross_encoder | 1.24 | 0.013 [-0.022, 0.049] | 0.068 (no CI: bootstrap invalid for RMS here) |
| backend_match | 1.39 | 0.052 [0.017, 0.090] | 0.120 (no CI: bootstrap invalid for RMS here) |
| entity_li | 1.36 | 0.009 [-0.030, 0.049] | 0.083 (no CI: bootstrap invalid for RMS here) |

## Top-10 exposure (female share - 0.5; pools are 50/50)

| Scorer | top-10 share | discounted exposure |
|---|---|---|
| bm25 | 0.019 [-0.000, 0.037] | 0.018 [-0.002, 0.036] |
| tfidf | 0.020 [-0.001, 0.038] | 0.026 [0.005, 0.046] |
| sbert_minilm | 0.063 [0.045, 0.081] | 0.067 [0.046, 0.087] |
| sbert_mpnet | 0.059 [0.042, 0.076] | 0.071 [0.053, 0.089] |
| jobbert_v2 | 0.014 [-0.003, 0.030] | 0.019 [-0.000, 0.038] |
| cross_encoder | -0.002 [-0.023, 0.017] | 0.000 [-0.021, 0.020] |
| backend_match | 0.082 [0.063, 0.101] | 0.091 [0.071, 0.112] |
| entity_li | 0.010 [-0.005, 0.026] | 0.013 [-0.004, 0.031] |

## Paired permutation tests: entity_li vs baselines (10000 sign flips, Holm within each row family)

| condition | metric | baseline | mean diff (ours - baseline) | p | p (Holm) | pools |
|---|---|---|---|---|---|---|
| original | ndcg@10 | backend_match | 0.0835 | 0.0001 | 0.0007 | 234 |
| original | ndcg@10 | bm25 | 0.0780 | 0.0001 | 0.0007 | 234 |
| original | ndcg@10 | cross_encoder | 0.2177 | 0.0001 | 0.0007 | 234 |
| original | ndcg@10 | jobbert_v2 | -0.0979 | 0.0001 | 0.0007 | 234 |
| original | ndcg@10 | sbert_minilm | 0.0161 | 0.1928 | 0.3856 | 234 |
| original | ndcg@10 | sbert_mpnet | -0.0148 | 0.2636 | 0.3856 | 234 |
| original | ndcg@10 | tfidf | 0.1009 | 0.0001 | 0.0007 | 234 |
| pronoun_swap | abs_gap_norm_changed | backend_match | -0.2497 | 0.0001 | 0.0007 | 234 |
| pronoun_swap | abs_gap_norm_changed | bm25 | 0.0219 | 0.0001 | 0.0007 | 234 |
| pronoun_swap | abs_gap_norm_changed | cross_encoder | -0.0811 | 0.0001 | 0.0007 | 234 |
| pronoun_swap | abs_gap_norm_changed | jobbert_v2 | -0.0848 | 0.0001 | 0.0007 | 234 |
| pronoun_swap | abs_gap_norm_changed | sbert_minilm | -0.1132 | 0.0001 | 0.0007 | 234 |
| pronoun_swap | abs_gap_norm_changed | sbert_mpnet | -0.0950 | 0.0001 | 0.0007 | 234 |
| pronoun_swap | abs_gap_norm_changed | tfidf | 0.0214 | 0.0001 | 0.0007 | 234 |
| name_swap_us | abs_gap_norm_changed | backend_match | 0.0495 | 0.0001 | 0.0007 | 234 |
| name_swap_us | abs_gap_norm_changed | bm25 | 0.0559 | 0.0001 | 0.0007 | 234 |
| name_swap_us | abs_gap_norm_changed | cross_encoder | -0.0979 | 0.0001 | 0.0007 | 234 |
| name_swap_us | abs_gap_norm_changed | jobbert_v2 | -0.0771 | 0.0001 | 0.0007 | 234 |
| name_swap_us | abs_gap_norm_changed | sbert_minilm | -0.2225 | 0.0001 | 0.0007 | 234 |
| name_swap_us | abs_gap_norm_changed | sbert_mpnet | -0.1580 | 0.0001 | 0.0007 | 234 |
| name_swap_us | abs_gap_norm_changed | tfidf | 0.0385 | 0.0001 | 0.0007 | 234 |
| name_swap_in | abs_gap_norm_changed | backend_match | 0.0535 | 0.0001 | 0.0007 | 234 |
| name_swap_in | abs_gap_norm_changed | bm25 | 0.0627 | 0.0001 | 0.0007 | 234 |
| name_swap_in | abs_gap_norm_changed | cross_encoder | -0.1481 | 0.0001 | 0.0007 | 234 |
| name_swap_in | abs_gap_norm_changed | jobbert_v2 | -0.1255 | 0.0001 | 0.0007 | 234 |
| name_swap_in | abs_gap_norm_changed | sbert_minilm | -0.2302 | 0.0001 | 0.0007 | 234 |
| name_swap_in | abs_gap_norm_changed | sbert_mpnet | -0.1695 | 0.0001 | 0.0007 | 234 |
| name_swap_in | abs_gap_norm_changed | tfidf | 0.0317 | 0.0001 | 0.0007 | 234 |
| name_in_same_gender | abs_gap_norm_changed | backend_match | 0.0511 | 0.0001 | 0.0007 | 234 |
| name_in_same_gender | abs_gap_norm_changed | bm25 | 0.0574 | 0.0001 | 0.0007 | 234 |
| name_in_same_gender | abs_gap_norm_changed | cross_encoder | -0.1446 | 0.0001 | 0.0007 | 234 |
| name_in_same_gender | abs_gap_norm_changed | jobbert_v2 | -0.1295 | 0.0001 | 0.0007 | 234 |
| name_in_same_gender | abs_gap_norm_changed | sbert_minilm | -0.2259 | 0.0001 | 0.0007 | 234 |
| name_in_same_gender | abs_gap_norm_changed | sbert_mpnet | -0.1687 | 0.0001 | 0.0007 | 234 |
| name_in_same_gender | abs_gap_norm_changed | tfidf | 0.0268 | 0.0001 | 0.0007 | 234 |
| affiliation_swap | abs_gap_norm_changed | backend_match | -0.0237 | 0.1973 | 0.7891 | 51 |
| affiliation_swap | abs_gap_norm_changed | bm25 | -0.0015 | 0.9544 | 1.0000 | 51 |
| affiliation_swap | abs_gap_norm_changed | cross_encoder | -0.0628 | 0.0008 | 0.0056 | 51 |
| affiliation_swap | abs_gap_norm_changed | jobbert_v2 | -0.0114 | 0.5846 | 1.0000 | 51 |
| affiliation_swap | abs_gap_norm_changed | sbert_minilm | -0.0221 | 0.0917 | 0.4585 | 51 |
| affiliation_swap | abs_gap_norm_changed | sbert_mpnet | -0.0305 | 0.0464 | 0.2784 | 51 |
| affiliation_swap | abs_gap_norm_changed | tfidf | -0.0161 | 0.5080 | 1.0000 | 51 |
| agentic_communal | abs_gap_norm_changed | backend_match | 0.0151 | 0.0706 | 0.3530 | 224 |
| agentic_communal | abs_gap_norm_changed | bm25 | 0.0109 | 0.1581 | 0.6307 | 224 |
| agentic_communal | abs_gap_norm_changed | cross_encoder | 0.0081 | 0.2094 | 0.6307 | 224 |
| agentic_communal | abs_gap_norm_changed | jobbert_v2 | 0.0082 | 0.1577 | 0.6307 | 224 |
| agentic_communal | abs_gap_norm_changed | sbert_minilm | 0.0215 | 0.0001 | 0.0007 | 224 |
| agentic_communal | abs_gap_norm_changed | sbert_mpnet | 0.0200 | 0.0003 | 0.0018 | 224 |
| agentic_communal | abs_gap_norm_changed | tfidf | -0.0042 | 0.6250 | 0.6307 | 224 |
| gender_full | abs_gap_norm_changed | backend_match | -0.2387 | 0.0001 | 0.0007 | 234 |
| gender_full | abs_gap_norm_changed | bm25 | 0.0322 | 0.0001 | 0.0007 | 234 |
| gender_full | abs_gap_norm_changed | cross_encoder | -0.0880 | 0.0001 | 0.0007 | 234 |
| gender_full | abs_gap_norm_changed | jobbert_v2 | -0.0926 | 0.0001 | 0.0007 | 234 |
| gender_full | abs_gap_norm_changed | sbert_minilm | -0.1477 | 0.0001 | 0.0007 | 234 |
| gender_full | abs_gap_norm_changed | sbert_mpnet | -0.1163 | 0.0001 | 0.0007 | 234 |
| gender_full | abs_gap_norm_changed | tfidf | 0.0281 | 0.0001 | 0.0007 | 234 |

Scoring wall-clock (s): bm25 61, tfidf 59, sbert_minilm 60, sbert_mpnet 60, jobbert_v2 67, cross_encoder 68, backend_match 64, entity_li 69
