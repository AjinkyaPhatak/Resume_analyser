# Near-miss suggestion band sweep

**PRELIMINARY: --subset 200 pools per split.**

Suggestion = a JD skill whose best resume match has cosine similarity in [lo, hi) (ESCO EntityRuler entities, minilm embeddings, relevant bio-JD pairs). Precision proxy from the ESCO hierarchy: *strict* = same concept or direct parent/child; *lenient* = strict or siblings. The band is chosen on DEV (max lenient precision with >= 100 dev suggestions) and evaluated on TEST. 95% CIs: cluster bootstrap over JD pools.

| Band | split | suggestions | per pair | strict precision | lenient precision |
|---|---|---|---|---|---|
| backend 0.35-0.55 | dev | 1275 | 1.73 | 0.013 [0.006, 0.021] | 0.080 [0.051, 0.113] |
| backend 0.35-0.55 | test | 2631 | 1.75 | 0.017 [0.011, 0.024] | 0.118 [0.086, 0.156] |
| chosen 0.65-0.90 | dev | 151 | 0.20 | 0.364 [0.262, 0.489] | 0.510 [0.366, 0.691] |
| chosen 0.65-0.90 | test | 309 | 0.21 | 0.482 [0.392, 0.588] | 0.702 [0.616, 0.789] |

Base rates (dev): share of ALL best matches that are correct -- strict 0.043, lenient 0.080 (n = 7509).

Base rates (test): share of ALL best matches that are correct -- strict 0.054, lenient 0.096 (n = 13727).

Figures: `research/results/summaries/figures/nearmiss_curves_subset200.(pdf|png)`, `nearmiss_heatmap_dev_subset200.(pdf|png)`.
