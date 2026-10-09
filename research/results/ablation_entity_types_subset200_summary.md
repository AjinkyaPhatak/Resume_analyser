# PRELIMINARY SMOKE TEST (--subset 200 pools per split)

Test pools unless noted. Values: mean over JD pools [95% cluster-bootstrap CI over pools, 1000 resamples]. Gaps: |score change| / SD of the pool's original scores, over CHANGED bios. Signed gaps: + = favours the female-coded (communal / target) version.

## Ranking accuracy (test)

| Scorer | nDCG@10 | MRR | P@5 | P@10 | pairs with entities |
|---|---|---|---|---|---|
| ent_skills_only | 0.443 [0.411, 0.474] | 0.662 [0.612, 0.714] | 0.438 [0.395, 0.479] | 0.357 [0.328, 0.387] | 0.764 [0.753, 0.772] |
| ent_plus_noun_chunks | 0.559 [0.531, 0.585] | 0.800 [0.756, 0.839] | 0.572 [0.529, 0.612] | 0.455 [0.429, 0.482] | 1.000 [1.000, 1.000] |
| ent_plus_noun_chunks_verbs | 0.536 [0.507, 0.565] | 0.787 [0.740, 0.829] | 0.543 [0.502, 0.588] | 0.432 [0.405, 0.460] | 1.000 [1.000, 1.000] |

## Counterfactual |gap| (normalised, changed bios)

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| ent_skills_only | 0.069 [0.066, 0.073] | 0.041 [0.035, 0.046] | 0.054 [0.047, 0.061] | 0.052 [0.044, 0.060] | 0.000 [0.000, 0.001] | 0.447 [0.387, 0.503] | 0.074 [0.071, 0.078] |
| ent_plus_noun_chunks | 0.026 [0.024, 0.027] | 0.037 [0.034, 0.039] | 0.041 [0.038, 0.044] | 0.039 [0.036, 0.042] | 0.191 [0.131, 0.260] | 0.153 [0.136, 0.171] | 0.032 [0.031, 0.034] |
| ent_plus_noun_chunks_verbs | 0.026 [0.024, 0.027] | 0.034 [0.031, 0.037] | 0.037 [0.034, 0.039] | 0.034 [0.032, 0.036] | 0.171 [0.113, 0.236] | 0.124 [0.110, 0.138] | 0.031 [0.030, 0.033] |

## Signed gap (normalised, changed bios; + favours female/communal/target)

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| ent_skills_only | -0.043 [-0.046, -0.040] | -0.009 [-0.015, -0.003] | -0.016 [-0.024, -0.009] | -0.018 [-0.024, -0.011] | -0.000 [-0.001, 0.000] | -0.418 [-0.475, -0.358] | -0.043 [-0.047, -0.040] |
| ent_plus_noun_chunks | -0.007 [-0.008, -0.006] | -0.003 [-0.006, -0.001] | 0.001 [-0.002, 0.004] | -0.006 [-0.009, -0.003] | -0.172 [-0.249, -0.107] | -0.130 [-0.151, -0.109] | -0.007 [-0.009, -0.006] |
| ent_plus_noun_chunks_verbs | -0.006 [-0.007, -0.005] | -0.002 [-0.005, 0.000] | 0.001 [-0.001, 0.004] | -0.005 [-0.008, -0.003] | -0.141 [-0.215, -0.081] | -0.074 [-0.093, -0.054] | -0.006 [-0.008, -0.005] |

## Mean |rank shift| in the pool (changed bios)

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| ent_skills_only | 2.229 [2.122, 2.342] | 1.209 [1.036, 1.373] | 1.571 [1.356, 1.780] | 1.561 [1.339, 1.803] | 0.000 [0.000, 0.000] | 13.799 [12.270, 15.397] | 2.388 [2.274, 2.500] |
| ent_plus_noun_chunks | 0.741 [0.698, 0.786] | 1.074 [0.979, 1.169] | 1.136 [1.040, 1.224] | 1.101 [1.013, 1.185] | 6.385 [3.885, 9.325] | 4.445 [3.869, 5.073] | 0.928 [0.879, 0.977] |
| ent_plus_noun_chunks_verbs | 0.738 [0.699, 0.778] | 0.983 [0.896, 1.070] | 1.033 [0.954, 1.114] | 0.967 [0.884, 1.046] | 6.152 [3.618, 9.138] | 3.523 [3.059, 3.993] | 0.903 [0.861, 0.949] |

## Entity scorers: |gap| restricted to pairs where both sides have entities

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| ent_skills_only | 0.058 [0.056, 0.061] | 0.028 [0.024, 0.032] | 0.037 [0.033, 0.042] | 0.034 [0.030, 0.039] | 0.000 [0.000, 0.001] | 0.262 [0.227, 0.300] | 0.062 [0.060, 0.065] |

## TPR gender gap (threshold chosen on dev; test; TPR_F - TPR_M over JD occupations)

| Scorer | threshold (z) | mean gap | RMS gap |
|---|---|---|---|
| ent_skills_only | 1.16 | -0.002 [-0.043, 0.037] | 0.088 [0.083, 0.163] |
| ent_plus_noun_chunks | 1.34 | -0.008 [-0.055, 0.038] | 0.096 [0.096, 0.186] |
| ent_plus_noun_chunks_verbs | 1.44 | -0.004 [-0.043, 0.036] | 0.095 [0.096, 0.164] |

## Top-10 exposure (female share - 0.5; pools are 50/50)

| Scorer | top-10 share | discounted exposure |
|---|---|---|
| ent_skills_only | 0.015 [-0.005, 0.034] | 0.019 [-0.002, 0.041] |
| ent_plus_noun_chunks | 0.015 [-0.003, 0.034] | 0.014 [-0.007, 0.035] |
| ent_plus_noun_chunks_verbs | 0.021 [0.004, 0.038] | 0.028 [0.009, 0.047] |

## Paired permutation tests: ent_skills_only vs baselines (10000 sign flips, Holm within each row family)

| condition | metric | baseline | mean diff (ours - baseline) | p | p (Holm) | pools |
|---|---|---|---|---|---|---|
| original | ndcg@10 | ent_plus_noun_chunks | -0.1160 | 0.0001 | 0.0002 | 200 |
| original | ndcg@10 | ent_plus_noun_chunks_verbs | -0.0930 | 0.0001 | 0.0002 | 200 |
| pronoun_swap | abs_gap_norm_changed | ent_plus_noun_chunks | 0.0433 | 0.0001 | 0.0002 | 199 |
| pronoun_swap | abs_gap_norm_changed | ent_plus_noun_chunks_verbs | 0.0435 | 0.0001 | 0.0002 | 199 |
| name_swap_us | abs_gap_norm_changed | ent_plus_noun_chunks | 0.0042 | 0.1835 | 0.1835 | 199 |
| name_swap_us | abs_gap_norm_changed | ent_plus_noun_chunks_verbs | 0.0070 | 0.0258 | 0.0516 | 199 |
| name_swap_in | abs_gap_norm_changed | ent_plus_noun_chunks | 0.0131 | 0.0013 | 0.0013 | 199 |
| name_swap_in | abs_gap_norm_changed | ent_plus_noun_chunks_verbs | 0.0174 | 0.0001 | 0.0002 | 199 |
| name_in_same_gender | abs_gap_norm_changed | ent_plus_noun_chunks | 0.0126 | 0.0021 | 0.0021 | 199 |
| name_in_same_gender | abs_gap_norm_changed | ent_plus_noun_chunks_verbs | 0.0177 | 0.0001 | 0.0002 | 199 |
| affiliation_swap | abs_gap_norm_changed | ent_plus_noun_chunks | -0.1906 | 0.0001 | 0.0002 | 45 |
| affiliation_swap | abs_gap_norm_changed | ent_plus_noun_chunks_verbs | -0.1705 | 0.0001 | 0.0002 | 45 |
| agentic_communal | abs_gap_norm_changed | ent_plus_noun_chunks | 0.2931 | 0.0001 | 0.0002 | 189 |
| agentic_communal | abs_gap_norm_changed | ent_plus_noun_chunks_verbs | 0.3218 | 0.0001 | 0.0002 | 189 |
| gender_full | abs_gap_norm_changed | ent_plus_noun_chunks | 0.0421 | 0.0001 | 0.0002 | 199 |
| gender_full | abs_gap_norm_changed | ent_plus_noun_chunks_verbs | 0.0430 | 0.0001 | 0.0002 | 199 |

Scoring wall-clock (s): ent_skills_only 110, ent_plus_noun_chunks 1143, ent_plus_noun_chunks_verbs 1722
