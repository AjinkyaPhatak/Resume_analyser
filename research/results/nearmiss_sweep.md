# Near-miss suggestion band sweep

Suggestion = a JD skill whose best resume match has cosine similarity in [lo, hi) (ESCO EntityRuler entities, minilm embeddings, relevant bio-JD pairs). Precision proxy from the ESCO hierarchy: *strict* = same concept or direct parent/child; *lenient* = strict or siblings. The band is chosen on DEV (max lenient precision with >= 100 dev suggestions) and evaluated on TEST. 95% CIs: cluster bootstrap over JD pools.

| Band | split | suggestions | per pair | strict precision | lenient precision |
|---|---|---|---|---|---|
| backend 0.35-0.55 | dev | 1275 | 1.73 | 0.013 [0.006, 0.021] | 0.080 [0.051, 0.113] |
| backend 0.35-0.55 | test | 3100 | 1.76 | 0.015 [0.010, 0.021] | 0.125 [0.094, 0.160] |
| chosen 0.65-0.90 | dev | 151 | 0.20 | 0.364 [0.262, 0.489] | 0.510 [0.366, 0.691] |
| chosen 0.65-0.90 | test | 362 | 0.21 | 0.483 [0.400, 0.569] | 0.707 [0.627, 0.793] |

Base rates (dev): share of ALL best matches that are correct -- strict 0.043, lenient 0.080 (n = 7509).

Base rates (test): share of ALL best matches that are correct -- strict 0.053, lenient 0.098 (n = 16489).

Figures: `research/results/summaries/figures/nearmiss_curves.(pdf|png)`, `nearmiss_heatmap_dev.(pdf|png)`.
