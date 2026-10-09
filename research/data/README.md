# Data

Raw data lives in `research/data/raw/` (gitignored). Never commit it.

## SkillSpan (automatic)

```
venv/Scripts/python.exe -m research.data.download skillspan
```
Downloads `jjzha/skillspan` pinned at revision `33062e6` (see `configs/data.yaml`) into
`raw/skillspan/` and writes `MANIFEST.json` with SHA-256 hashes of each file.
License: CC-BY-4.0. The public release has only the STAR ("house") and StackOverflow
("tech") sources: 4800 / 3174 / 3569 train/dev/test sentences.

## ESCO skills taxonomy (manual: the portal emails a download link)

1. Go to <https://esco.ec.europa.eu/en/use-esco/download>.
2. Select:
   - **Version**: the latest ESCO version offered (write down the exact number, e.g. `v1.2.x`);
   - **Content**: *Classification*;
   - **Language**: *English (en)*;
   - **File type**: *CSV*.
3. Enter your email address and submit. ESCO emails you a link to a zip file.
4. Unzip it and copy **`skills_en.csv`** to `research/data/raw/esco/skills_en.csv`. Only
   this file is needed for Phase 1. Keep the rest of the zip, since the occupation files
   may be useful in Phase 2.
5. Put the version number in `configs/data.yaml` under `datasets.esco.version`.

The loader expects the columns `preferredLabel`, `altLabels` (newline-separated) and,
if present, `skillType`, `conceptUri` and `status`. It fails with a clear error if the
file is missing or has different columns. Every run logs the SHA-256 of the CSV in
`run_meta.json`.

## BiasBios (automatic)

```
venv/Scripts/python.exe -m research.data.download biasbios
```
Downloads `LabHC/bias_in_bios` (De-Arteaga et al., 2019; Ravfogel et al., 2020 version;
MIT) pinned at revision `052f01d` into `raw/biasbios/`, plus `MANIFEST.json` hashes.

## Job postings (manual: needs a Kaggle login)

Dataset: **LinkedIn Job Postings (2023–2024)** by arshkon, CC BY-SA 4.0,
<https://www.kaggle.com/datasets/arshkon/linkedin-job-postings>.

1. Sign in to Kaggle, open the link above and click **Download**. You get a zip of about
   0.5 GB; the exact size depends on the dataset version.
2. Unzip it and copy **`postings.csv`** to `research/data/raw/jobs/postings.csv`.
   The other files (companies/, jobs/, mappings/) aren't needed.
3. Note the dataset version shown on the Kaggle page; it's logged with every run.

Then run `python -m research.experiments.prepare_data` and review
`research/data/occupation_map.csv` (instructions at the top of
`research/data/occupation_map.py`).

Why not a Hugging Face mirror? The HF copies of this data are re-uploads with
licences added by the uploader. The other HF job datasets checked on 2026-10-09 were
IT-only (Djinni), LLM-summarised (NextGig), or had no licence, so they were rejected.

## Relevance labels and candidate pools (Phase 2 design)

- **Mapping JDs to occupations**: by job title, using the regexes in `configs/occupations.yaml`
  (include / weak / flag / exclude, plus `title_exclude_all`). Architect postings also have
  to mention building-architecture terms in the description, because most LinkedIn
  "architect" titles are IT roles. The review file is `data/occupation_map.csv`: fill
  `reviewed_occupation` with one of the 28 occupations or `none`. Rows marked
  `review_priority = high` can add JDs to occupations that are short of them.
- **Binary relevance**: a bio is relevant (1) to a JD of its own occupation, otherwise 0.
- **Graded relevance**: 2 = same occupation, 1 = same SOC 2018 major group (codes in
  `configs/occupations.yaml`, verified against O*NET-SOC 2019), 0 = otherwise. Examples of
  grade-1 pairs: attorney/paralegal (23), physician/nurse/dentist/surgeon/dietitian/
  chiropractor (29), teacher/professor (25), personal trainer/yoga teacher (39), and the
  arts/media occupations (27). This grouping is coarse; `relevance.soc_level: minor`
  gives a finer one.
- **Pools**: each JD gets 100 candidate bios: 10 of its occupation (5 F, 5 M) and 90 from
  other occupations (45 F, 45 M), with the other occupation drawn uniformly per slot.
  JDs are split 30/70 into dev pools (for choosing thresholds) and test pools. Dev pools
  draw bios from the BiasBios dev split, test pools from the test split.
