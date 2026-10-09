# CLAUDE.md

This repo has two parts:
- `backend/` (FastAPI) + `frontend/` (Next.js): the working resume analyser app.
  **Never modify `frontend/`.** Backend changes must keep endpoints working.
- `research/`: the research codebase for a paper (below). All research code lives here.

## Research claim

> Entity-level resume–JD matching (extract skills first, then do late-interaction
> matching over entity embeddings) leaks less demographic signal into match scores than
> full-text embedding matchers, at competitive ranking accuracy.

Working title: *Do Entity-Level Resume Matchers Leak Less Demographic Signal? A
Counterfactual Fairness Audit of Semantic Resume–Job Matching.*

Test: a **counterfactual fairness audit**. Perturb each resume (name swap, pronoun swap,
affiliation swap, agentic/communal rewrite) and measure how much each scorer's output
shifts, alongside ranking accuracy (nDCG@10 etc.) on BiasBios bios vs job descriptions.

**Novelty framing:** our method is late interaction (cf. ColBERT, Khattab & Zaharia
2020; BERTScore, Zhang et al. 2020) applied to *extracted skill entities*. We cite
those papers and do **not** claim the MaxSim/late-interaction mechanism is new. The
contribution is the fairness audit and the entity-restriction hypothesis.

## Ground rules
1. Research code goes in `research/` only. Don't break the backend.
2. **Never fabricate data, results or numbers.** If a dataset can't be downloaded, stop
   and tell the user exactly what to download manually and where to put it
   (`research/data/raw/`). No synthetic stand-ins presented as real.
3. Seeds everywhere; every hyperparameter in YAML under `research/configs/`; deps pinned
   in `research/requirements.txt`; every run logs config + git hash (`run_meta.json`).
4. Pytest for every non-trivial component, on tiny fixtures. Tests must not need full
   datasets; anything needing a model download is marked `@pytest.mark.slow`.
5. Embeddings are cached on disk (`research/common/embedding_cache.py`), keyed by model
   namespace + sha256(text).
6. CPU by default, GPU if available (`device: auto`). Every experiment takes `--subset N`.
7. Work proceeds in phases; **stop and report at the end of each phase** and wait for
   "continue".
8. Verify every HuggingFace model/dataset ID exists before using it.
9. Don't rely on set/dict iteration order of strings (hash randomisation); sort.

## Layout
```
research/
  common/          config (YAML + base: inheritance + --set overrides), seeding/device,
                   provenance (git hash, env), embedding cache, shared CLI
  configs/         YAML experiment configs (base.yaml = shared defaults)
  data/            loaders + download scripts (data/raw, data/processed gitignored)
  extraction/      skill extractors (Extractor interface)
  scorers/         all matching methods behind the Scorer protocol (scorers/base.py)
  perturbations/   counterfactual generators
  metrics/         ranking + fairness metrics, significance tests
  experiments/     runnable scripts: python -m research.experiments.<name>
  annotation/      human labelling tool
  analysis/        figures + LaTeX tables
  results/         outputs (gitignored except *.md and results/summaries/)
  tests/
  BACKEND_AUDIT.md Phase 0 audit of the backend matcher/bias services
```
Config paths are relative to the repo root. Configs inherit via a top-level `base:` key.

## Environment
- Python 3.14 venv at `venv/` (shared with the backend). Use `venv/Scripts/python.exe`.
- torch 2.13.0+cu126 (CUDA) on an RTX 2060 6 GB (installed 2026-10-09). `device: auto` uses it.
  fp16 autocast is used for training/inference where configured.

## Commands (run from repo root)
| Phase | Command | Status |
|---|---|---|
| 0 | `venv/Scripts/python.exe -m pytest research` (fast; add `-m slow` for model-loading tests) | done |
| 0 | `cd backend && ../venv/Scripts/python.exe -m pytest` (endpoint tests) | done |
| 0 | `venv/Scripts/python.exe -m research.experiments.check_env [--subset N] [--set k=v]` | done |
| 1 | `venv/Scripts/python.exe -m research.data.download skillspan` | done |
| 1 | `venv/Scripts/python.exe -m research.experiments.eval_extraction [--subset N]` -> results/extraction.md | done: a, b, c + diagnostic scored (ESCO v1.2.1 in research/data/raw/esco). All < 0.4 F1 |
| 1 | `venv/Scripts/python.exe -m research.experiments.train_extractor [--subset N] [--set seed=K]` (GPU needed in practice) | done: 3 seeds trained on GPU |
| 1 | `venv/Scripts/python.exe -m research.experiments.extraction_errors --set analyse=<name>` (dev only) | done |
| 2 | `venv/Scripts/python.exe -m research.data.download biasbios` | done |
| 2 | `venv/Scripts/python.exe -m research.experiments.prepare_data [--subset N]` -> data/processed/, data/occupation_map.csv, results/data_stats.md | done: 18/28 occupations have pools (100 dev / 234 test); 1114 ambiguous titles unreviewed |
| 3 | `venv/Scripts/python.exe -m pytest research -m slow` (real-model scorer tests incl. backend parity) | done |
| 3 | `venv/Scripts/python.exe -m research.experiments.scorer_smoke [--config ...] [--subset N]` (DEV pools only) | done |
| 4 | `venv/Scripts/python.exe -m research.experiments.make_perturbations [--subset N]` -> data/processed/perturbations_*.parquet, results/perturbation_samples.md, results/perturbation_stats.md | done |
| 5 | `venv/Scripts/python.exe -m research.experiments.run --config configs/main.yaml [--subset N]` -> results/main[_subsetN]/ + results/main[_subsetN]_summary.md | harness done; smoke test --subset 200 |
| 6 | `venv/Scripts/python.exe -m research.experiments.run --config configs/ablations/{entity_types,aggregation,backbone,extractor}.yaml [--subset N]` | done (subset 200) |
| 6 | `venv/Scripts/python.exe -m research.experiments.nearmiss_sweep --config configs/ablations/nearmiss.yaml [--subset N]` -> results/nearmiss_sweep*.md, results/summaries/figures/ | done (subset 200) |
| 7 | `venv/Scripts/python.exe -m research.annotation.sample` (250 pairs) / `streamlit run research/annotation/app.py` / `venv/Scripts/python.exe -m research.annotation.agreement` | tool done; awaiting human ratings |
| 8 | `venv/Scripts/python.exe -m research.experiments.run --config configs/selection.yaml` (dev-only selection) | done |
| 8 | `venv/Scripts/python.exe -m research.analysis.make_all [--set analysis.main_dir=...]` -> results/summaries/{figures,tables}, see research/README.md | done |

Update this table as each phase lands.

## Phase 8 notes + FINAL RESULTS (full run, 234 test pools; results/main_summary.md)
- nDCG@10: jobbert_v2 0.716 > sbert_mpnet 0.633 > entity_li (final) 0.619 ~ sbert_minilm 0.602 >
  bm25 0.541 ~ backend 0.535 > tfidf 0.518 > cross_encoder 0.401.
- Full gender flip |gap| (norm.): bm25 0.001, tfidf 0.005, entity_li 0.033, cross 0.121, jobbert 0.126,
  mpnet 0.149, minilm 0.181, backend 0.272. entity_li beats every neural full-text scorer on every
  gender condition (Holm p<0.001) but is above lexical scorers; agentic/communal ~ all scorers (0.05-0.07).
- Held-out check on the 34 test pools never used before the final run: same pattern
  (research.analysis.fresh_pools -> results/fresh_pools_check.md).
- RMS TPR gap reported without CI (bootstrap invalid for that statistic here); mean TPR gap has CIs.
- run.py `experiment.reuse_scores: true` recomputes all metrics from a run's scores.parquet.

## Phase 7 notes (annotation)
- research/annotation/: sample.py (strata = consensus-score bin x JD occupation x bio gender;
  EQUAL budget per score bin cut at the 50%/90% consensus quantiles, because proportional
  sampling gave 78% obvious non-matches), storage.py (append-only CSV per annotator, latest
  rating wins), app.py (Streamlit; shows only texts, per-annotator seeded order),
  agreement.py (Cohen's kappa incl. quadratic, ordinal Krippendorff alpha, Spearman of each
  scorer and of the graded BiasBios label vs mean human rating, bootstrap CIs), GUIDELINES.md.
- sample_250.csv (texts shown) / sample_250_meta.csv (hidden strata, labels). Sample drawn from
  results/main_subset200 scores: 165 / 35 / 50 pairs with graded label 0 / 1 / 2.
- labels/<annotator>.csv are research data: commit them.

## Phase 6 notes (ablations)
- Ablation configs in configs/ablations/ reuse run.py; each lists the main variant as `our_method`
  (reference for paired tests). entity_types: skills-only / +filtered noun chunks / +verb phrases.
- Near-miss sweep: suggestion correctness proxy = ESCO hierarchy (strict: same concept or direct
  parent/child; lenient: + siblings). Band chosen on DEV, reported on TEST. Backend band 0.35-0.55 is at
  the base rate (noise); best dev band 0.65-0.90 (above the backend's 0.55 match threshold).
- Figures go to results/summaries/figures/ (tracked). Colours: validated dataviz palette
  (categorical #2a78d6/#eb6834, blue sequential ramp); render and eyeball every figure.

## Phase 5 notes (metrics + harness)
- metrics/ranking.py: TIE-AWARE expected nDCG@10 (graded, gain 2^g-1), MRR, P@k (McSherry & Najork 2008),
  because entity scorers give many exact ties (0.0).
- metrics/fairness.py: per-pool counterfactual gap (raw and NORMALISED by the pool's SD of original
  scores -- scorer scales differ), signed gap oriented + = favours female/communal/target version,
  rank shift, TPR gap (threshold = best F1 on DEV per-pool z-scores, applied to test), top-10 exposure.
- metrics/stats.py: cluster bootstrap over JD pools (1000, seeded); paired sign-flip permutation tests
  over pools (ours vs each baseline), Holm-corrected per metric family.
- Unchanged counterfactuals copy the original score (gap 0); headline gaps use CHANGED bios only;
  entity scorers also report gaps restricted to pairs with entities on both sides (`*_nonempty`).
- --subset N = N seeded pools per split.

## Phase 4 notes (perturbations)
- `research/perturbations/`: each bio parsed once (en_core_web_sm); parts propose token-range
  replacements, conditions merge parts (`registry.py`). Every substitution is logged (`Change`).
- Conditions (configs/perturbations.yaml): pronoun_swap (bidirectional CDA; her/his heuristics in
  pronouns.py), name_swap_us / name_swap_in (opposite gender), name_in_same_gender (ethnicity cue
  only), affiliation_swap (configs/affiliations.yaml), agentic_communal (configs/agentic_communal.yaml,
  POS/dep/passive/idiom guards), gender_full (pronoun + US name).
- Name sources: SSA national counts (HF mirror nkrishnaswami/us-ssa-baby-names-national @ b10af86,
  spot-checked vs official files; ssa.gov blocks scripts) and Wikidata given names of Indian citizens
  (query research/data/wikidata_india_names.rq, CSV snapshot in data/raw/names/). Rejected: HF
  "indian names" sets without gender/provenance, and MeghanaKap/indian_names (customer PII).
- Name swap only touches strongly gendered (>=95%) first names of the bio's SUBJECT (single-word
  mention or clause subject), never after titles or surnames.
- Coverage is uneven by design: pronoun ~99% of bios, names ~30%, agentic ~6%, affiliation <1%.
  Unchanged bios have zero gap by construction -> report gaps on changed bios as well.

## Phase 3 notes (scorers)
- All scorers implement `scorers/base.py::Scorer`; built from `configs/scorers.yaml` via
  `scorers/registry.py` (`build_scorers`, `fit_scorer`). Types: bm25, tfidf, sbert, cross_encoder,
  llm_judge (off by default; Qwen2.5-1.5B-Instruct), entity.
- **Our method** = `scorers/entity.py::EntityLateInteractionScorer`: late interaction
  (ColBERT / BERTScore-style MaxSim) over *extracted skill entities*. We cite ColBERT and
  BERTScore and do NOT claim the mechanism is new. Aggregations in `scorers/aggregation.py`.
- `backend_match` = the deployed app's matcher reproduced exactly (slow parity test).
- BM25 re-implements rank_bm25's BM25Okapi formula (test checks equality) so perturbed,
  unseen resumes can be scored with fixed IDF. Lexical IDF fitted on 50k TRAIN bios + pool JDs.
  Default stop-word list removes he/she/his/her -> lexical scorers are blind to pronoun swaps.
- Dense full-text scorers chunk long texts into token windows and mean-pool (`long_text: chunk_mean`);
  `truncate` available. JobBERT-v2 = title-trained (64-token) encoder, anchor head, used on
  documents via 64-token windows -- a stated limitation.
- Caches: embeddings (`.cache/embeddings`), pair scores (`.cache/pair_scores`), extracted spans
  (`.cache/extraction`, keyed by extractor spec fingerprint).
- FINAL MAIN METHOD (user chose "option 1" after Phase 7; selected by the pre-declared dev-only
  rule in configs/selection.yaml, highest dev nDCG@10 = 0.606): `entity_li` = union(JobBERT ft seed13,
  ESCO, filtered noun chunks), skill+knowledge labels, JobBERT-v2 entity embeddings, idf_weighted.
- EARLIER MAIN METHOD (Phases 3-6; still the reference of the Phase 6 ablations): union(fine-tuned JobBERT seed13,
  ESCO) extractor, skill+knowledge labels only, MiniLM, maxsim_mean. Dev (30 pools): 23% pairs
  empty, AUC 0.68 vs full-text MiniLM 0.81; esco+nc / noun-chunk variants 0.77 (Phase 6 ablation).
- KEY RISK found on dev: fine-tuned extractor finds 0 skill entities in ~51% of BiasBios bios
  (bios list credentials, not skills) -> score 0 before and after perturbation -> trivial
  'fairness'. Must report coverage and condition fairness analyses on non-empty entities.

## Phase 2 notes (data)
- BiasBios: LabHC/bias_in_bios @ 052f01d (MIT), `hard_text` = bio minus first sentence.
  Official splits kept by default (`biasbios.split_strategy: official`; `stratified` re-split
  available). Cleaning removes in-split duplicates and dev/test texts seen in earlier splits.
  Gender is binary in the source (M/F). Bios avg ~61 words.
- JDs: Kaggle arshkon LinkedIn postings (CC BY-SA 4.0), in data/raw/jobs/ (sha256 in configs/data.yaml).
  106,326 postings after cleaning (16k duplicate descriptions dropped).
- Occupations WITHOUT pools (too few postings): comedian, composer, dj, filmmaker, model,
  painter, pastor, poet, rapper, yoga_teacher. Their bios still appear as irrelevant
  candidates. chiropractor (7), surgeon (13) and photographer (14) have fewer than 20 JDs.
- Mapping revisions made after inspecting titles (data cleaning, before any scorer) are
  listed at the top of configs/occupations.yaml. Pattern keys: include / weak / flag /
  exclude / require_description, plus global title_exclude_all.
- Title -> occupation patterns + SOC 2018 codes in configs/occupations.yaml (written before
  seeing JD data). Review file data/occupation_map.csv: fill `reviewed_occupation`
  (occupation or `none`); reviews survive regeneration; unreviewed ambiguous titles excluded.
- Relevance: binary (same occupation); graded 2/1/0 with 1 = same SOC major group.
- Pools: per JD 100 bios, 10 relevant, gender-balanced (relevant 5F/5M, irrelevant 45F/45M),
  irrelevant occupation drawn uniformly. JDs split 30/70 into dev/test pools (dev for thresholds).

## Known backend state (see research/BACKEND_AUDIT.md)
- `POST /analysis/match` 500 (commit 60bfe79) fixed in Phase 1: the router maps the
  service output onto `MatchResponse`; `suggestions` was added as an optional field.
  Endpoint tests are in `backend/tests/`.

## Phase 1 notes (extraction)
- Extractors in `research/extraction/`: `noun_chunk` (faithful port of backend
  `extract_entities`; parity test is marked slow), `esco` (EntityRuler, lemma + lower),
  `esco+nc` (ESCO + filtered noun chunks), `filtered_nc` (diagnostic). Build via
  `extraction.registry.build_extractor`.
- Phase 1 result (test exact / partial F1): noun_chunk 0.073/0.328, esco 0.167/0.330,
  esco+nc 0.128/0.385, filtered_nc 0.099/0.374. No tuning has been done on these yet.
  Fine-tuned JobBERT (d), 3 seeds (13/14/15), best epoch by dev exact F1:
  test exact 0.611 +- 0.009, partial 0.871 +- 0.002 (dev 0.605 / 0.859). Only (d) clears 0.4.
  Models: research/models/jobbert_skillspan/seed{13,14,15} (~1.5 min/epoch on the RTX 2060).
  Dev error analysis: 44% of ESCO preds are in unannotated sentences (titles/tag lines);
  ESCO lacks modern tools (aws, docker, react, kubernetes); ESCO matches agentic words
  ("lead", "leading") -- relevant to the agentic/communal perturbation in Phase 4.
- Typed spans: label in {skill, knowledge, verb_phrase}; source in {esco, noun_chunk, ner, verb, model}.
- Tune noun-chunk filter / ESCO options on SkillSpan **dev only**; report test.
- spaCy en_core_web_sm runs ~1.3k words/s on this machine (slow); cache extraction outputs
  before running it over BiasBios.
- Fine-tuned extractor (d): `extraction/token_classifier.py` (shared encoder, one O/B/I head
  per SkillSpan layer, first-sub-token labels) + `extraction/train_tagger.py` (select on dev
  exact F1). Base `jjzha/jobbert-base-cased` @ eee1c8d. Weights go to `research/models/`
  (gitignored). Registry type `token_classifier`.
- Machine note (2026-10-08): CPU torch ~11 GFLOP/s under heavy background load -> JobBERT
  fine-tuning ~2 h/epoch on CPU. Needs CUDA torch (RTX 2060) to be practical.
- transformers 5.x gotcha: `BertTokenizerFast(vocab_file=...)` silently ignores the file;
  pass `vocab={token: id}`.
