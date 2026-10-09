# Phase 0 audit of the backend matcher and bias services

> **Status (2026-10-10):** this audit describes the app as it was at `60bfe79`. The app now runs
> the paper's entity-level method (`backend/app/services/engine.py`), the bias-service bugs in
> section 3 are fixed (the word lists are still unverified), and the audited matcher is kept
> verbatim in `research/legacy/backend_matcher_60bfe79.py`.

Audited at commit `60bfe79`. Files: `backend/app/services/matcher.py`,
`backend/app/services/bias.py`, `backend/app/routers/analysis.py`,
`backend/app/schemas/analysis.py`. Behaviour marked **(verified)** was reproduced by
running the code, not only read.

## 1. How the match score is computed

`semantic_match(resume_text, jd_text)`:

1. **Entity extraction** (`extract_entities`, spaCy `en_core_web_sm`), run separately on
   each document. The result is the *set union* of three sources:
   - NER spans labelled `ORG`, `PRODUCT`, `GPE`, `WORK_OF_ART`;
   - every noun chunk whose stripped text is 3–59 characters long;
   - "verb phrases": for each `VERB` token whose dependency is `ROOT`, `conj` or
     `advcl`, the verb's text joined with the head-word text of its `dobj` / `attr` /
     `prep` children (only the child token, not its subtree), kept if longer than 3
     characters. Example **(verified)**: "She led a team" gives `led team`.
   Deduplication is exact-string and case-sensitive ("AWS" and "aws" are separate).
2. **Encoding**: all resume entities and all JD entities go through `all-MiniLM-L6-v2`
   in one `model.encode` call. Each entity is embedded **in isolation**, with no
   sentence context.
3. **Similarity matrix**: `cos_sim(JD entities, resume entities)`, shape |JD| × |R|.
4. **Aggregation**: for each JD entity take the max similarity over resume entities
   (a MaxSim / BERTScore-recall step). Then **threshold** it:
   - max ≥ 0.55: *matched* (paired with the argmax resume entity);
   - otherwise a *gap*; and if max ≥ 0.35 it is also a *near-miss suggestion*.
5. **Score** = `matched / |JD entities| × 100`, rounded to 1 decimal place.
   So the score is the *fraction of JD entities whose best match clears 0.55*, not the
   mean of the max similarities. Every JD entity has equal weight (no IDF), one resume
   entity can satisfy any number of JD entities (many-to-one), and resume entities with
   no JD counterpart do not affect the score (recall-only).
6. If either side yields no entities, the endpoint returns HTTP 400.

## 2. Hardcoded magic numbers and choices

| Location | Value | Role |
|---|---|---|
| matcher.py:5 | `"en_core_web_sm"` | spaCy pipeline (small model; noisy parser/NER) |
| matcher.py:6 | `"all-MiniLM-L6-v2"` | embedding backbone |
| matcher.py:16 | `ORG, PRODUCT, GPE, WORK_OF_ART` | NER labels kept as "skills" |
| matcher.py:22 | `2 < len < 60` | noun-chunk length filter, in characters |
| matcher.py:27 | `ROOT, conj, advcl` | verb dependency labels kept |
| matcher.py:29 | `dobj, attr, prep` | child dependencies appended to verbs |
| matcher.py:31 | `len(phrase) > 3` | verb-phrase length filter |
| matcher.py:57 | `MATCH_THRESHOLD = 0.55` | match cut-off |
| matcher.py:58 | `NEAR_MISS_THRESHOLD = 0.35` | near-miss lower bound (band 0.35–0.55) |
| matcher.py:73,84 | `round(…, 2)` | reported similarity precision |
| matcher.py:87 | `× 100`, `round(…, 1)` | percent scaling |
| bias.py:4–22 | two word lists (37 + 35 entries) | gender-coded lexicon |
| bias.py:33,40 | `startswith` | prefix matching for **every** entry |
| bias.py:53 | `/ len(words) × 100`, `round(…, 2)` | per-100-words normalisation |
| bias.py:57–61 | `±1` | verdict cut-offs |

None of these are configurable. Phase 3 moves the matcher's values into YAML, and
Phase 6 sweeps the 0.35/0.55 band.

## 3. Problems found

### Breaks the running app
- **`POST /analysis/match` returns HTTP 500 at HEAD (verified).** Commit `60bfe79`
  changed the service's return keys to `matched` / `gaps` / `suggestions` /
  `total_jd_requirements` (with `jd_requirement` inside each match), but
  `MatchResponse` and `frontend/lib/types.ts` still expect `matched_skills` /
  `missing_skills` / `total_jd_skills` (with `jd_skill`). FastAPI's response
  validation fails. `/analysis/bias` works. There are **no backend tests**, so nothing
  caught this.

### Directly relevant to the fairness claim
- **Gendered tokens become "skills" (verified).** Pronoun noun chunks pass the length
  filter: "She" is extracted from "She is a nurse…". "Women" (from "Women in Tech"),
  hospital names (`ORG`) and cities (`GPE`) are also extracted. These get embedded and
  can match JD entities, so the current extractor *does* give a path for demographic
  signal to enter the score. That's the motivation for Phase 1, and it's also a
  finding worth reporting in the paper as "the naive entity matcher".
- Entities are embedded without context, so "led team" and "supported team" depend
  entirely on the backbone's prior for those strings. That's exactly what the
  agentic/communal perturbation probes.

### Reproducibility
- `extract_entities` returns `list(set(...))`. Python randomises string hashing per
  process, so **entity order changes between runs (verified)**. The score itself
  doesn't depend on order, but argmax ties and output order do. Research code sorts.
- Models load at import time as module globals; device and batch size aren't set.

### Bias service bugs
- **A masculine score of exactly `1.0` gets the verdict "Feminine-coded" (verified):**
  the `abs < 1` / `> 1` / `else` chain sends `== 1` to the feminine branch.
- `self-reliant` and `self-sufficient` can **never match (verified)**, because
  `\b\w+\b` splits on the hyphen.
- Prefix matching applies to every entry, giving false positives **(verified)**:
  `commit` → "committee", `kind` → "kindergarten". Others likely: `trust` → "trustee",
  `warm` → "warmup". Meanwhile full-word entries miss the stems Gaucher et al. intended
  (e.g. `analytical` doesn't match "analysis", and `competitive` doesn't match
  "competition").
- **Provenance of the lists needs checking.** Gaucher et al. (2011) publish stem lists
  (e.g. `analy*`, `compet*`, `lead*`). To my knowledge, some entries here (`ninja`,
  `rockstar`, `warrior`, `fighter`, `battle`, `champion`, `fearless`, `driven`, `family`,
  `flexible`, `enthusiastic`) come from later practitioner lists rather than the paper,
  but I haven't checked this against the paper's appendix. The comment also cites
  Bolukbasi et al. (2016), which is about debiasing embeddings, not a word list.
  **Phase 4 depends on these lists, so they should be transcribed verbatim from the
  paper before then.**
- The score divides by total words, so long texts shrink toward 0.
