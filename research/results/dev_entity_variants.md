# Scorer smoke test (DEV pools, PRELIMINARY sanity check, not a result)

30 dev pools x 100 bios = 3000 pairs; seed 13. Times include first-time extraction/embedding (later runs hit the caches). AUC = P(relevant bio outscores irrelevant bio) within a pool, averaged over pools.

| scorer | fit_s | score_s | pairs_per_s | n_nan | n_empty | mean_pool_auc | score_mean_rel | score_mean_irrel |
|---|---|---|---|---|---|---|---|---|
| ent_jobbert | 0.0 | 25.7 | 116.9 | 0 | 1872.0 | 0.606 | 0.121 | 0.0701 |
| ent_esco | 0.0 | 52.8 | 56.8 | 0 | 881.0 | 0.604 | 0.2298 | 0.1808 |
| ent_union | 0.0 | 1.1 | 2771.0 | 0 | 698.0 | 0.681 | 0.2318 | 0.1673 |
| ent_esco_nc | 0.0 | 74.0 | 40.5 | 0 | 0.0 | 0.767 | 0.3478 | 0.2998 |
| ent_nounchunk_all | 0.0 | 60.5 | 49.6 | 0 | 0.0 | 0.77 | 0.3499 | 0.3114 |
| sbert_minilm | 0.0 | 8.9 | 337.9 | 0 | nan | 0.809 | 0.254 | 0.1162 |
