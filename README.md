# Resume Analyser

Matches a resume to a job description by **skills**, and lets you check that the score doesn't
depend on who wrote the resume. The matcher is the method from the accompanying paper,
*Do Entity-Level Resume Matchers Leak Less Demographic Signal? A Counterfactual Fairness Audit
of Semantic Resume–Job Matching*. The paper's code, data pipeline and results live in
[`research/`](research/README.md), and the website's **Research** page presents them.

- `backend/`: FastAPI. `/analysis/match` runs the paper's entity-level matcher (skill entities
  from a fine-tuned JobBERT tagger + ESCO + filtered noun chunks, JobBERT-v2 embeddings,
  IDF-weighted MaxSim). `/analysis/counterfactual` runs the paper's perturbations on the
  submitted resume. `/analysis/bias` flags gender-coded wording. `/resume/parse` reads a PDF
  without storing it.
- `frontend/`: Next.js App Router, TypeScript, Tailwind. Pages: analyse, results (with the
  fairness check), research.
- `research/`: the paper's codebase (see `CLAUDE.md` and `research/README.md`).

## Setup

The backend imports the research package, so install both sets of requirements into one
virtual environment at the repo root:

```bash
python -m venv venv
venv/Scripts/python.exe -m pip install -r backend/requirements.txt -r research/requirements.txt
```

The matcher needs files that are too large for git (all regenerable, see `research/README.md`):

| Needed | Where | How |
|---|---|---|
| Fine-tuned skill tagger | `research/models/jobbert_skillspan/seed13/` | `python -m research.experiments.train_extractor --set seed=13` |
| ESCO v1.2.1 skills | `research/data/raw/esco/` | manual download, see `research/data/README.md` |
| Name lists (for name-swap checks; optional) | `research/data/raw/names/` | see `research/data/README.md` |
| JobBERT-v2, MiniLM, spaCy `en_core_web_sm` | Hugging Face / pip cache | downloaded on first use |

`backend/artifacts/entity_li.json` (IDF table, dev calibration, suggestion band) is committed.
It's regenerated from the final runs with `python -m research.analysis.export_app`. The
research page's data (`frontend/public/research/`) is regenerated with
`python -m research.analysis.export_web`.

## Run

```bash
venv/Scripts/python.exe -m uvicorn main:app --app-dir backend --port 8000
```

```bash
npm --prefix frontend run dev
```

The API loads its models in the background at startup (about a minute; `GET /analysis/status`).
The frontend is at `http://localhost:3000`. Auth and `/resume/upload` still need MongoDB
(`backend/.env.example`). Analysis doesn't.

## Tests

```bash
cd backend && ../venv/Scripts/python.exe -m pytest
```

```bash
venv/Scripts/python.exe -m pytest research
```

Add `-m slow` to either to run the tests that load real models. The backend's slow tests check
that the app's score equals the research scorer's.
