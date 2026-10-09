# PRELIMINARY SMOKE TEST (--subset 200 pools per split)

Test pools unless noted. Values: mean over JD pools [95% cluster-bootstrap CI over pools, 1000 resamples]. Gaps: |score change| / SD of the pool's original scores, over CHANGED bios. Signed gaps: + = favours the female-coded (communal / target) version.

## Ranking accuracy (test)

| Scorer | nDCG@10 | MRR | P@5 | P@10 | pairs with entities |
|---|---|---|---|---|---|
| bm25 | 0.553 [0.524, 0.584] | 0.814 [0.769, 0.857] | 0.590 [0.550, 0.633] | 0.453 [0.425, 0.481] | 1.000 [1.000, 1.000] |
| tfidf | 0.528 [0.501, 0.558] | 0.800 [0.759, 0.843] | 0.565 [0.527, 0.605] | 0.429 [0.405, 0.455] | 1.000 [1.000, 1.000] |
| sbert_minilm | 0.612 [0.580, 0.641] | 0.836 [0.793, 0.874] | 0.647 [0.608, 0.685] | 0.507 [0.478, 0.536] | 1.000 [1.000, 1.000] |
| sbert_mpnet | 0.644 [0.613, 0.672] | 0.858 [0.818, 0.895] | 0.661 [0.622, 0.700] | 0.545 [0.516, 0.572] | 1.000 [1.000, 1.000] |
| jobbert_v2 | 0.727 [0.702, 0.751] | 0.911 [0.879, 0.939] | 0.754 [0.719, 0.786] | 0.622 [0.595, 0.648] | 1.000 [1.000, 1.000] |
| cross_encoder | 0.414 [0.385, 0.444] | 0.668 [0.619, 0.719] | 0.422 [0.384, 0.461] | 0.333 [0.307, 0.360] | 1.000 [1.000, 1.000] |
| backend_match | 0.550 [0.521, 0.580] | 0.808 [0.768, 0.848] | 0.569 [0.531, 0.611] | 0.449 [0.423, 0.477] | 1.000 [1.000, 1.000] |
| entity_li | 0.443 [0.411, 0.474] | 0.662 [0.612, 0.714] | 0.438 [0.395, 0.479] | 0.357 [0.328, 0.387] | 0.764 [0.753, 0.772] |

## Counterfactual |gap| (normalised, changed bios)

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| bm25 | 0.000 [0.000, 0.001] | 0.002 [0.001, 0.003] | 0.001 [0.000, 0.003] | 0.001 [0.000, 0.003] | 0.053 [0.013, 0.108] | 0.053 [0.037, 0.070] | 0.001 [0.000, 0.001] |
| tfidf | 0.001 [0.000, 0.001] | 0.019 [0.017, 0.022] | 0.032 [0.030, 0.035] | 0.032 [0.029, 0.035] | 0.069 [0.023, 0.129] | 0.065 [0.048, 0.081] | 0.005 [0.004, 0.005] |
| sbert_minilm | 0.132 [0.121, 0.145] | 0.280 [0.270, 0.291] | 0.292 [0.282, 0.302] | 0.283 [0.273, 0.293] | 0.067 [0.051, 0.083] | 0.043 [0.038, 0.049] | 0.178 [0.166, 0.191] |
| sbert_mpnet | 0.115 [0.107, 0.124] | 0.216 [0.207, 0.224] | 0.233 [0.224, 0.242] | 0.225 [0.216, 0.235] | 0.080 [0.057, 0.103] | 0.047 [0.041, 0.054] | 0.147 [0.138, 0.158] |
| jobbert_v2 | 0.106 [0.098, 0.113] | 0.135 [0.129, 0.141] | 0.189 [0.180, 0.196] | 0.188 [0.181, 0.196] | 0.061 [0.035, 0.099] | 0.060 [0.054, 0.066] | 0.124 [0.117, 0.132] |
| cross_encoder | 0.104 [0.096, 0.113] | 0.156 [0.149, 0.164] | 0.213 [0.204, 0.222] | 0.204 [0.196, 0.213] | 0.113 [0.084, 0.149] | 0.058 [0.050, 0.067] | 0.122 [0.114, 0.131] |
| backend_match | 0.274 [0.240, 0.311] | 0.009 [0.006, 0.011] | 0.011 [0.008, 0.013] | 0.007 [0.005, 0.009] | 0.079 [0.042, 0.124] | 0.055 [0.038, 0.071] | 0.274 [0.239, 0.310] |
| entity_li | 0.069 [0.066, 0.073] | 0.041 [0.035, 0.046] | 0.054 [0.047, 0.061] | 0.052 [0.044, 0.060] | 0.000 [0.000, 0.001] | 0.447 [0.387, 0.503] | 0.074 [0.071, 0.078] |

## Signed gap (normalised, changed bios; + favours female/communal/target)

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| bm25 | 0.000 [0.000, 0.001] | -0.001 [-0.002, 0.000] | -0.001 [-0.002, 0.000] | -0.001 [-0.003, -0.000] | -0.034 [-0.091, 0.010] | 0.016 [-0.000, 0.032] | 0.000 [-0.000, 0.001] |
| tfidf | 0.001 [0.000, 0.001] | -0.007 [-0.010, -0.005] | -0.001 [-0.004, 0.001] | -0.022 [-0.024, -0.019] | -0.045 [-0.106, 0.005] | 0.016 [-0.001, 0.032] | -0.001 [-0.001, -0.000] |
| sbert_minilm | 0.089 [0.073, 0.107] | 0.025 [0.010, 0.041] | 0.048 [0.034, 0.063] | 0.008 [-0.008, 0.025] | -0.042 [-0.063, -0.020] | 0.018 [0.011, 0.026] | 0.094 [0.076, 0.115] |
| sbert_mpnet | 0.085 [0.074, 0.097] | 0.055 [0.043, 0.069] | 0.016 [0.004, 0.027] | -0.077 [-0.091, -0.062] | -0.047 [-0.078, -0.018] | 0.004 [-0.003, 0.011] | 0.096 [0.083, 0.110] |
| jobbert_v2 | 0.042 [0.027, 0.056] | 0.026 [0.018, 0.035] | 0.019 [0.010, 0.028] | -0.004 [-0.015, 0.007] | 0.016 [-0.014, 0.056] | 0.037 [0.029, 0.045] | 0.046 [0.030, 0.061] |
| cross_encoder | -0.038 [-0.052, -0.025] | 0.024 [0.016, 0.034] | 0.034 [0.026, 0.043] | 0.090 [0.081, 0.100] | -0.078 [-0.118, -0.040] | -0.013 [-0.024, -0.002] | -0.035 [-0.049, -0.021] |
| backend_match | 0.261 [0.226, 0.299] | -0.000 [-0.003, 0.002] | -0.000 [-0.003, 0.002] | -0.002 [-0.003, 0.000] | -0.053 [-0.099, -0.012] | 0.027 [0.009, 0.044] | 0.260 [0.225, 0.298] |
| entity_li | -0.043 [-0.046, -0.040] | -0.009 [-0.015, -0.003] | -0.016 [-0.024, -0.009] | -0.018 [-0.024, -0.011] | -0.000 [-0.001, 0.000] | -0.418 [-0.475, -0.358] | -0.043 [-0.047, -0.040] |

## Mean |rank shift| in the pool (changed bios)

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| bm25 | 0.018 [0.005, 0.035] | 0.059 [0.021, 0.111] | 0.035 [0.003, 0.084] | 0.035 [0.003, 0.084] | 1.756 [0.244, 3.712] | 1.475 [1.031, 1.932] | 0.029 [0.014, 0.047] |
| tfidf | 0.029 [0.013, 0.049] | 0.425 [0.367, 0.493] | 0.723 [0.660, 0.799] | 0.704 [0.650, 0.774] | 2.007 [0.467, 3.904] | 1.798 [1.279, 2.309] | 0.115 [0.095, 0.138] |
| sbert_minilm | 3.800 [3.470, 4.159] | 8.109 [7.774, 8.486] | 8.519 [8.220, 8.835] | 8.181 [7.887, 8.501] | 2.307 [1.430, 3.333] | 1.174 [0.970, 1.391] | 5.124 [4.786, 5.501] |
| sbert_mpnet | 3.402 [3.146, 3.677] | 6.375 [6.096, 6.677] | 6.805 [6.498, 7.091] | 6.686 [6.398, 7.007] | 2.370 [1.363, 3.515] | 1.242 [1.060, 1.439] | 4.381 [4.115, 4.682] |
| jobbert_v2 | 3.455 [3.208, 3.705] | 4.355 [4.167, 4.546] | 6.015 [5.724, 6.276] | 6.035 [5.757, 6.309] | 1.581 [0.981, 2.259] | 1.849 [1.625, 2.098] | 4.074 [3.823, 4.327] |
| cross_encoder | 3.244 [2.991, 3.516] | 4.469 [4.252, 4.692] | 6.257 [5.949, 6.559] | 5.957 [5.702, 6.232] | 2.744 [1.722, 4.001] | 1.669 [1.449, 1.894] | 3.738 [3.486, 4.005] |
| backend_match | 10.252 [9.120, 11.440] | 0.223 [0.160, 0.298] | 0.277 [0.214, 0.347] | 0.210 [0.148, 0.276] | 2.230 [0.941, 3.803] | 1.416 [0.994, 1.838] | 10.231 [9.114, 11.420] |
| entity_li | 2.229 [2.122, 2.342] | 1.209 [1.036, 1.373] | 1.571 [1.356, 1.780] | 1.561 [1.339, 1.803] | 0.000 [0.000, 0.000] | 13.799 [12.270, 15.397] | 2.388 [2.274, 2.500] |

## Entity scorers: |gap| restricted to pairs where both sides have entities

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| entity_li | 0.058 [0.056, 0.061] | 0.028 [0.024, 0.032] | 0.037 [0.033, 0.042] | 0.034 [0.030, 0.039] | 0.000 [0.000, 0.001] | 0.262 [0.227, 0.300] | 0.062 [0.060, 0.065] |

## TPR gender gap (threshold chosen on dev; test; TPR_F - TPR_M over JD occupations)

| Scorer | threshold (z) | mean gap | RMS gap |
|---|---|---|---|
| bm25 | 1.48 | 0.008 [-0.034, 0.048] | 0.141 [0.130, 0.205] |
| tfidf | 1.27 | 0.025 [-0.022, 0.071] | 0.123 [0.118, 0.201] |
| sbert_minilm | 1.44 | 0.068 [0.029, 0.107] | 0.142 [0.130, 0.205] |
| sbert_mpnet | 1.32 | 0.056 [0.014, 0.099] | 0.127 [0.119, 0.201] |
| jobbert_v2 | 1.42 | 0.017 [-0.029, 0.058] | 0.157 [0.140, 0.230] |
| cross_encoder | 1.24 | 0.007 [-0.034, 0.046] | 0.085 [0.084, 0.156] |
| backend_match | 1.39 | 0.052 [0.010, 0.094] | 0.122 [0.109, 0.198] |
| entity_li | 1.16 | -0.002 [-0.043, 0.037] | 0.088 [0.083, 0.163] |

## Top-10 exposure (female share - 0.5; pools are 50/50)

| Scorer | top-10 share | discounted exposure |
|---|---|---|
| bm25 | 0.018 [-0.001, 0.039] | 0.020 [-0.000, 0.041] |
| tfidf | 0.017 [-0.005, 0.038] | 0.024 [0.001, 0.046] |
| sbert_minilm | 0.061 [0.044, 0.079] | 0.065 [0.045, 0.085] |
| sbert_mpnet | 0.056 [0.038, 0.073] | 0.067 [0.047, 0.086] |
| jobbert_v2 | 0.012 [-0.007, 0.029] | 0.018 [-0.002, 0.039] |
| cross_encoder | -0.008 [-0.029, 0.014] | -0.006 [-0.028, 0.016] |
| backend_match | 0.084 [0.064, 0.103] | 0.098 [0.076, 0.119] |
| entity_li | 0.015 [-0.005, 0.034] | 0.019 [-0.002, 0.041] |

## Paired permutation tests: entity_li vs baselines (10000 sign flips, Holm within each row family)

| condition | metric | baseline | mean diff (ours - baseline) | p | p (Holm) | pools |
|---|---|---|---|---|---|---|
| original | ndcg@10 | backend_match | -0.1071 | 0.0001 | 0.0007 | 200 |
| original | ndcg@10 | bm25 | -0.1102 | 0.0001 | 0.0007 | 200 |
| original | ndcg@10 | cross_encoder | 0.0293 | 0.1554 | 0.1554 | 200 |
| original | ndcg@10 | jobbert_v2 | -0.2842 | 0.0001 | 0.0007 | 200 |
| original | ndcg@10 | sbert_minilm | -0.1686 | 0.0001 | 0.0007 | 200 |
| original | ndcg@10 | sbert_mpnet | -0.2009 | 0.0001 | 0.0007 | 200 |
| original | ndcg@10 | tfidf | -0.0848 | 0.0001 | 0.0007 | 200 |
| pronoun_swap | abs_gap_norm_changed | backend_match | -0.2005 | 0.0001 | 0.0007 | 199 |
| pronoun_swap | abs_gap_norm_changed | bm25 | 0.0687 | 0.0001 | 0.0007 | 199 |
| pronoun_swap | abs_gap_norm_changed | cross_encoder | -0.0354 | 0.0001 | 0.0007 | 199 |
| pronoun_swap | abs_gap_norm_changed | jobbert_v2 | -0.0366 | 0.0001 | 0.0007 | 199 |
| pronoun_swap | abs_gap_norm_changed | sbert_minilm | -0.0627 | 0.0001 | 0.0007 | 199 |
| pronoun_swap | abs_gap_norm_changed | sbert_mpnet | -0.0461 | 0.0001 | 0.0007 | 199 |
| pronoun_swap | abs_gap_norm_changed | tfidf | 0.0683 | 0.0001 | 0.0007 | 199 |
| name_swap_us | abs_gap_norm_changed | backend_match | 0.0321 | 0.0001 | 0.0007 | 199 |
| name_swap_us | abs_gap_norm_changed | bm25 | 0.0390 | 0.0001 | 0.0007 | 199 |
| name_swap_us | abs_gap_norm_changed | cross_encoder | -0.1159 | 0.0001 | 0.0007 | 199 |
| name_swap_us | abs_gap_norm_changed | jobbert_v2 | -0.0946 | 0.0001 | 0.0007 | 199 |
| name_swap_us | abs_gap_norm_changed | sbert_minilm | -0.2393 | 0.0001 | 0.0007 | 199 |
| name_swap_us | abs_gap_norm_changed | sbert_mpnet | -0.1752 | 0.0001 | 0.0007 | 199 |
| name_swap_us | abs_gap_norm_changed | tfidf | 0.0216 | 0.0001 | 0.0007 | 199 |
| name_swap_in | abs_gap_norm_changed | backend_match | 0.0439 | 0.0001 | 0.0007 | 199 |
| name_swap_in | abs_gap_norm_changed | bm25 | 0.0528 | 0.0001 | 0.0007 | 199 |
| name_swap_in | abs_gap_norm_changed | cross_encoder | -0.1590 | 0.0001 | 0.0007 | 199 |
| name_swap_in | abs_gap_norm_changed | jobbert_v2 | -0.1347 | 0.0001 | 0.0007 | 199 |
| name_swap_in | abs_gap_norm_changed | sbert_minilm | -0.2378 | 0.0001 | 0.0007 | 199 |
| name_swap_in | abs_gap_norm_changed | sbert_mpnet | -0.1794 | 0.0001 | 0.0007 | 199 |
| name_swap_in | abs_gap_norm_changed | tfidf | 0.0219 | 0.0001 | 0.0007 | 199 |
| name_in_same_gender | abs_gap_norm_changed | backend_match | 0.0442 | 0.0001 | 0.0007 | 199 |
| name_in_same_gender | abs_gap_norm_changed | bm25 | 0.0503 | 0.0001 | 0.0007 | 199 |
| name_in_same_gender | abs_gap_norm_changed | cross_encoder | -0.1527 | 0.0001 | 0.0007 | 199 |
| name_in_same_gender | abs_gap_norm_changed | jobbert_v2 | -0.1368 | 0.0001 | 0.0007 | 199 |
| name_in_same_gender | abs_gap_norm_changed | sbert_minilm | -0.2317 | 0.0001 | 0.0007 | 199 |
| name_in_same_gender | abs_gap_norm_changed | sbert_mpnet | -0.1742 | 0.0001 | 0.0007 | 199 |
| name_in_same_gender | abs_gap_norm_changed | tfidf | 0.0199 | 0.0001 | 0.0007 | 199 |
| affiliation_swap | abs_gap_norm_changed | backend_match | -0.0783 | 0.0003 | 0.0007 | 45 |
| affiliation_swap | abs_gap_norm_changed | bm25 | -0.0530 | 0.0162 | 0.0162 | 45 |
| affiliation_swap | abs_gap_norm_changed | cross_encoder | -0.1129 | 0.0001 | 0.0007 | 45 |
| affiliation_swap | abs_gap_norm_changed | jobbert_v2 | -0.0607 | 0.0001 | 0.0007 | 45 |
| affiliation_swap | abs_gap_norm_changed | sbert_minilm | -0.0664 | 0.0001 | 0.0007 | 45 |
| affiliation_swap | abs_gap_norm_changed | sbert_mpnet | -0.0793 | 0.0001 | 0.0007 | 45 |
| affiliation_swap | abs_gap_norm_changed | tfidf | -0.0691 | 0.0001 | 0.0007 | 45 |
| agentic_communal | abs_gap_norm_changed | backend_match | 0.3917 | 0.0001 | 0.0007 | 189 |
| agentic_communal | abs_gap_norm_changed | bm25 | 0.3930 | 0.0001 | 0.0007 | 189 |
| agentic_communal | abs_gap_norm_changed | cross_encoder | 0.3885 | 0.0001 | 0.0007 | 189 |
| agentic_communal | abs_gap_norm_changed | jobbert_v2 | 0.3876 | 0.0001 | 0.0007 | 189 |
| agentic_communal | abs_gap_norm_changed | sbert_minilm | 0.4037 | 0.0001 | 0.0007 | 189 |
| agentic_communal | abs_gap_norm_changed | sbert_mpnet | 0.3994 | 0.0001 | 0.0007 | 189 |
| agentic_communal | abs_gap_norm_changed | tfidf | 0.3817 | 0.0001 | 0.0007 | 189 |
| gender_full | abs_gap_norm_changed | backend_match | -0.1949 | 0.0001 | 0.0007 | 199 |
| gender_full | abs_gap_norm_changed | bm25 | 0.0736 | 0.0001 | 0.0007 | 199 |
| gender_full | abs_gap_norm_changed | cross_encoder | -0.0483 | 0.0001 | 0.0007 | 199 |
| gender_full | abs_gap_norm_changed | jobbert_v2 | -0.0503 | 0.0001 | 0.0007 | 199 |
| gender_full | abs_gap_norm_changed | sbert_minilm | -0.1031 | 0.0001 | 0.0007 | 199 |
| gender_full | abs_gap_norm_changed | sbert_mpnet | -0.0732 | 0.0001 | 0.0007 | 199 |
| gender_full | abs_gap_norm_changed | tfidf | 0.0696 | 0.0001 | 0.0007 | 199 |

Scoring wall-clock (s): bm25 160, tfidf 90, sbert_minilm 198, sbert_mpnet 470, jobbert_v2 427, cross_encoder 429, backend_match 1564, entity_li 1705
