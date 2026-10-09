# Skill extraction on SkillSpan

SkillSpan `jjzha/skillspan` @ `33062e6`; sentences evaluated: dev=3174, test=3569. Gold = union of skill and knowledge layers unless stated. Micro-averaged.
Exact = identical token boundaries. Partial = overlap of at least 1 token, with P and R counted separately (lenient; see research/metrics/span_metrics.py).

## All spans (skill ∪ knowledge)

| Extractor | Split | Exact P | Exact R | Exact F1 | Partial P | Partial R | Partial F1 | #pred | #gold |
|---|---|---|---|---|---|---|---|---|---|
| noun_chunk | dev | 0.039 | 0.233 | **0.067** | 0.222 | 0.918 | **0.357** | 12885 | 2163 |
| noun_chunk | test | 0.042 | 0.256 | **0.073** | 0.200 | 0.919 | **0.328** | 13652 | 2265 |
| esco | dev | 0.209 | 0.115 | **0.148** | 0.485 | 0.258 | **0.337** | 1188 | 2163 |
| esco | test | 0.231 | 0.131 | **0.167** | 0.465 | 0.256 | **0.330** | 1287 | 2265 |
| esco+nc | dev | 0.075 | 0.258 | **0.117** | 0.280 | 0.791 | **0.413** | 7392 | 2163 |
| esco+nc | test | 0.082 | 0.289 | **0.128** | 0.255 | 0.781 | **0.385** | 7947 | 2265 |
| filtered_nc | dev | 0.060 | 0.194 | **0.091** | 0.266 | 0.807 | **0.400** | 7011 | 2163 |
| filtered_nc | test | 0.064 | 0.213 | **0.099** | 0.243 | 0.809 | **0.374** | 7534 | 2265 |
| jobbert_ft_s13 | dev | 0.557 | 0.659 | **0.604** | 0.821 | 0.894 | **0.856** | 2562 | 2163 |
| jobbert_ft_s13 | test | 0.575 | 0.661 | **0.615** | 0.833 | 0.909 | **0.869** | 2606 | 2265 |
| jobbert_ft_s14 | dev | 0.566 | 0.636 | **0.599** | 0.845 | 0.883 | **0.864** | 2431 | 2163 |
| jobbert_ft_s14 | test | 0.571 | 0.634 | **0.601** | 0.848 | 0.898 | **0.872** | 2512 | 2265 |
| jobbert_ft_s15 | dev | 0.585 | 0.645 | **0.613** | 0.850 | 0.866 | **0.858** | 2386 | 2163 |
| jobbert_ft_s15 | test | 0.587 | 0.651 | **0.617** | 0.850 | 0.892 | **0.871** | 2511 | 2265 |

## Mean ± SD over training seeds (all spans, F1)

| Extractor | Seeds | Split | Exact F1 | Partial F1 |
|---|---|---|---|---|
| jobbert_ft | 3 | dev | 0.605 ± 0.007 | 0.859 ± 0.004 |
| jobbert_ft | 3 | test | 0.611 ± 0.009 | 0.871 ± 0.002 |

## Per gold layer (F1)

Predicted `skill`/`verb_phrase` spans are scored against the skill layer, and `knowledge` spans against the knowledge layer.

| Extractor | Split | Skill exact | Skill partial | Knowledge exact | Knowledge partial |
|---|---|---|---|---|---|
| noun_chunk | dev | 0.048 | 0.286 | 0.057 | 0.145 |
| noun_chunk | test | 0.058 | 0.241 | 0.057 | 0.145 |
| esco | dev | 0.025 | 0.148 | 0.216 | 0.327 |
| esco | test | 0.038 | 0.153 | 0.236 | 0.325 |
| esco+nc | dev | 0.025 | 0.148 | 0.107 | 0.192 |
| esco+nc | test | 0.038 | 0.153 | 0.112 | 0.189 |
| filtered_nc | dev | 0.000 | 0.000 | 0.081 | 0.180 |
| filtered_nc | test | 0.000 | 0.000 | 0.082 | 0.182 |
| jobbert_ft_s13 | dev | 0.536 | 0.801 | 0.629 | 0.797 |
| jobbert_ft_s13 | test | 0.512 | 0.804 | 0.666 | 0.824 |
| jobbert_ft_s14 | dev | 0.516 | 0.803 | 0.638 | 0.819 |
| jobbert_ft_s14 | test | 0.483 | 0.798 | 0.672 | 0.837 |
| jobbert_ft_s15 | dev | 0.552 | 0.805 | 0.631 | 0.803 |
| jobbert_ft_s15 | test | 0.524 | 0.802 | 0.663 | 0.833 |

## By source (all spans, F1 exact / partial)

| Extractor | Split | house | tech |
|---|---|---|---|
| noun_chunk | dev | 0.053 / 0.336 | 0.079 / 0.375 |
| noun_chunk | test | 0.067 / 0.329 | 0.079 / 0.327 |
| esco | dev | 0.093 / 0.321 | 0.184 / 0.348 |
| esco | test | 0.117 / 0.297 | 0.210 / 0.359 |
| esco+nc | dev | 0.092 / 0.403 | 0.136 / 0.422 |
| esco+nc | test | 0.110 / 0.387 | 0.145 / 0.383 |
| filtered_nc | dev | 0.084 / 0.387 | 0.097 / 0.410 |
| filtered_nc | test | 0.097 / 0.374 | 0.100 / 0.373 |
| jobbert_ft_s13 | dev | 0.552 / 0.837 | 0.635 / 0.867 |
| jobbert_ft_s13 | test | 0.573 / 0.860 | 0.650 / 0.878 |
| jobbert_ft_s14 | dev | 0.562 / 0.856 | 0.621 / 0.869 |
| jobbert_ft_s14 | test | 0.545 / 0.863 | 0.648 / 0.880 |
| jobbert_ft_s15 | dev | 0.577 / 0.846 | 0.636 / 0.865 |
| jobbert_ft_s15 | test | 0.582 / 0.862 | 0.646 / 0.877 |

Wall-clock seconds (build / extract all splits): noun_chunk: 3.7 / 30.5; esco: 112.4 / 63.4; esco+nc: 117.1 / 63.9; filtered_nc: 0.9 / 24.5; jobbert_ft_s13: 19.9 / 14.0; jobbert_ft_s14: 4.7 / 14.0; jobbert_ft_s15: 4.5 / 13.9
