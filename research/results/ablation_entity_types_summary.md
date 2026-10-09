# Main results

Test pools unless noted. Values: mean over JD pools [95% cluster-bootstrap CI over pools, 1000 resamples]. Gaps: |score change| / SD of the pool's original scores, over CHANGED bios. Signed gaps: + = favours the female-coded (communal / target) version.

## Ranking accuracy (test)

| Scorer | nDCG@10 | MRR | P@5 | P@10 | pairs with entities |
|---|---|---|---|---|---|
| ent_skills_only | 0.441 [0.412, 0.471] | 0.662 [0.617, 0.710] | 0.436 [0.398, 0.474] | 0.356 [0.328, 0.383] | 0.765 [0.755, 0.772] |
| ent_plus_noun_chunks | 0.546 [0.520, 0.570] | 0.790 [0.749, 0.832] | 0.560 [0.523, 0.596] | 0.445 [0.421, 0.468] | 1.000 [1.000, 1.000] |
| ent_plus_noun_chunks_verbs | 0.524 [0.497, 0.549] | 0.778 [0.735, 0.818] | 0.527 [0.490, 0.563] | 0.424 [0.399, 0.447] | 1.000 [1.000, 1.000] |

## Counterfactual |gap| (normalised, changed bios)

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| ent_skills_only | 0.070 [0.067, 0.073] | 0.040 [0.035, 0.046] | 0.052 [0.045, 0.058] | 0.052 [0.044, 0.060] | 0.000 [0.000, 0.001] | 0.450 [0.397, 0.503] | 0.075 [0.072, 0.078] |
| ent_plus_noun_chunks | 0.026 [0.025, 0.028] | 0.036 [0.034, 0.039] | 0.040 [0.038, 0.043] | 0.039 [0.036, 0.041] | 0.185 [0.127, 0.251] | 0.151 [0.136, 0.166] | 0.033 [0.031, 0.034] |
| ent_plus_noun_chunks_verbs | 0.026 [0.025, 0.027] | 0.034 [0.032, 0.037] | 0.036 [0.034, 0.039] | 0.034 [0.032, 0.036] | 0.163 [0.110, 0.225] | 0.122 [0.110, 0.136] | 0.032 [0.030, 0.033] |

## Signed gap (normalised, changed bios; + favours female/communal/target)

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| ent_skills_only | -0.043 [-0.047, -0.040] | -0.009 [-0.014, -0.003] | -0.016 [-0.023, -0.009] | -0.019 [-0.026, -0.012] | -0.000 [-0.001, 0.000] | -0.422 [-0.479, -0.368] | -0.044 [-0.047, -0.040] |
| ent_plus_noun_chunks | -0.007 [-0.008, -0.005] | -0.002 [-0.005, 0.000] | 0.000 [-0.002, 0.003] | -0.005 [-0.008, -0.002] | -0.167 [-0.235, -0.101] | -0.128 [-0.147, -0.112] | -0.007 [-0.009, -0.006] |
| ent_plus_noun_chunks_verbs | -0.006 [-0.007, -0.005] | -0.002 [-0.004, 0.001] | 0.001 [-0.001, 0.004] | -0.005 [-0.007, -0.002] | -0.136 [-0.207, -0.080] | -0.072 [-0.089, -0.057] | -0.006 [-0.007, -0.005] |

## Mean |rank shift| in the pool (changed bios)

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| ent_skills_only | 2.259 [2.163, 2.368] | 1.200 [1.059, 1.363] | 1.516 [1.331, 1.707] | 1.566 [1.367, 1.785] | 0.000 [0.000, 0.000] | 13.739 [12.302, 15.117] | 2.417 [2.316, 2.523] |
| ent_plus_noun_chunks | 0.751 [0.713, 0.793] | 1.078 [0.996, 1.164] | 1.122 [1.038, 1.202] | 1.097 [1.013, 1.181] | 6.065 [3.705, 8.792] | 4.369 [3.846, 4.880] | 0.937 [0.898, 0.985] |
| ent_plus_noun_chunks_verbs | 0.745 [0.711, 0.784] | 0.977 [0.901, 1.054] | 1.017 [0.949, 1.090] | 0.953 [0.874, 1.029] | 5.781 [3.431, 8.485] | 3.509 [3.093, 3.944] | 0.910 [0.871, 0.951] |

## Entity scorers: |gap| restricted to pairs where both sides have entities

| Scorer | pronoun_swap | name_swap_us | name_swap_in | name_in_same_gender | affiliation_swap | agentic_communal | gender_full |
|---|---|---|---|---|---|---|---|
| ent_skills_only | 0.059 [0.057, 0.062] | 0.028 [0.025, 0.032] | 0.037 [0.033, 0.041] | 0.034 [0.030, 0.038] | 0.000 [0.000, 0.001] | 0.268 [0.235, 0.303] | 0.063 [0.061, 0.066] |

## TPR gender gap (threshold chosen on dev; TPR_F - TPR_M over JD occupations)

| Scorer | threshold (z) | mean gap | RMS gap |
|---|---|---|---|
| ent_skills_only | 1.16 | -0.009 [-0.044, 0.027] | 0.089 (no CI: bootstrap invalid for RMS here) |
| ent_plus_noun_chunks | 1.34 | -0.010 [-0.049, 0.027] | 0.084 (no CI: bootstrap invalid for RMS here) |
| ent_plus_noun_chunks_verbs | 1.44 | -0.008 [-0.044, 0.025] | 0.082 (no CI: bootstrap invalid for RMS here) |

## Top-10 exposure (female share - 0.5; pools are 50/50)

| Scorer | top-10 share | discounted exposure |
|---|---|---|
| ent_skills_only | 0.007 [-0.010, 0.026] | 0.014 [-0.006, 0.034] |
| ent_plus_noun_chunks | 0.015 [-0.003, 0.029] | 0.013 [-0.007, 0.028] |
| ent_plus_noun_chunks_verbs | 0.019 [0.003, 0.034] | 0.025 [0.007, 0.042] |

## Paired permutation tests: ent_skills_only vs baselines (10000 sign flips, Holm within each row family)

| condition | metric | baseline | mean diff (ours - baseline) | p | p (Holm) | pools |
|---|---|---|---|---|---|---|
| original | ndcg@10 | ent_plus_noun_chunks | -0.1047 | 0.0001 | 0.0002 | 234 |
| original | ndcg@10 | ent_plus_noun_chunks_verbs | -0.0826 | 0.0001 | 0.0002 | 234 |
| pronoun_swap | abs_gap_norm_changed | ent_plus_noun_chunks | 0.0434 | 0.0001 | 0.0002 | 233 |
| pronoun_swap | abs_gap_norm_changed | ent_plus_noun_chunks_verbs | 0.0436 | 0.0001 | 0.0002 | 233 |
| name_swap_us | abs_gap_norm_changed | ent_plus_noun_chunks | 0.0039 | 0.1729 | 0.1729 | 233 |
| name_swap_us | abs_gap_norm_changed | ent_plus_noun_chunks_verbs | 0.0065 | 0.0236 | 0.0472 | 233 |
| name_swap_in | abs_gap_norm_changed | ent_plus_noun_chunks | 0.0115 | 0.0014 | 0.0014 | 233 |
| name_swap_in | abs_gap_norm_changed | ent_plus_noun_chunks_verbs | 0.0154 | 0.0001 | 0.0002 | 233 |
| name_in_same_gender | abs_gap_norm_changed | ent_plus_noun_chunks | 0.0132 | 0.0012 | 0.0012 | 233 |
| name_in_same_gender | abs_gap_norm_changed | ent_plus_noun_chunks_verbs | 0.0180 | 0.0001 | 0.0002 | 233 |
| affiliation_swap | abs_gap_norm_changed | ent_plus_noun_chunks | -0.1850 | 0.0001 | 0.0002 | 51 |
| affiliation_swap | abs_gap_norm_changed | ent_plus_noun_chunks_verbs | -0.1627 | 0.0001 | 0.0002 | 51 |
| agentic_communal | abs_gap_norm_changed | ent_plus_noun_chunks | 0.2986 | 0.0001 | 0.0002 | 223 |
| agentic_communal | abs_gap_norm_changed | ent_plus_noun_chunks_verbs | 0.3269 | 0.0001 | 0.0002 | 223 |
| gender_full | abs_gap_norm_changed | ent_plus_noun_chunks | 0.0424 | 0.0001 | 0.0002 | 233 |
| gender_full | abs_gap_norm_changed | ent_plus_noun_chunks_verbs | 0.0432 | 0.0001 | 0.0002 | 233 |

Scoring wall-clock (s): ent_skills_only 68, ent_plus_noun_chunks 64, ent_plus_noun_chunks_verbs 61
