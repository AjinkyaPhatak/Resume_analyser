# Held-out check: test pools never used before the final run

34 fresh test pools (of 234); the other 200 were used by the subset-200 smoke test and the Phase 6 ablations that motivated the final method's candidate family. Mean over pools [95% cluster-bootstrap CI].

| scorer | ndcg@10 (fresh) | gender_full |gap| (fresh) | ndcg@10 (all test) |
|---|---|---|---|
| bm25 | 0.465 [0.400, 0.527] | 0.001 [0.000, 0.001] | 0.541 |
| tfidf | 0.458 [0.398, 0.517] | 0.005 [0.004, 0.006] | 0.518 |
| sbert_minilm | 0.548 [0.478, 0.611] | 0.198 [0.170, 0.229] | 0.602 |
| sbert_mpnet | 0.571 [0.509, 0.634] | 0.159 [0.141, 0.178] | 0.633 |
| jobbert_v2 | 0.652 [0.585, 0.710] | 0.132 [0.115, 0.153] | 0.716 |
| cross_encoder | 0.325 [0.263, 0.391] | 0.112 [0.095, 0.133] | 0.401 |
| backend_match | 0.446 [0.376, 0.517] | 0.258 [0.186, 0.345] | 0.535 |
| entity_li | 0.544 [0.473, 0.611] | 0.035 [0.031, 0.040] | 0.619 |
