# Annotation guidelines: resume–job fit (0–3)

You will see **250 pairs**. Each pair is a **job description** (a real LinkedIn posting)
and a **candidate bio** (a real short professional biography from the BiasBios dataset).
For each pair, rate **how well the candidate fits the job**.

Plan for about **1–1.5 minutes per pair** (4–6 hours in total; split it over several sittings).
The app saves every rating immediately, so you can stop and continue at any time.

## What you're judging

Rate **professional fit only**: occupation, field, skills, qualifications, experience.
Ask yourself: *"Would a reasonable recruiter put this person on a shortlist for this job,
based only on this bio?"*

## The scale

| Rating | Label | Use it when |
|---|---|---|
| **3** | Strong fit | The bio shows the **same occupation** as the job, and the job's core requirements (key skills, credentials or experience) are evident or very likely. |
| **2** | Partial fit | **Same or closely related occupation**, but notable gaps: a different specialty or level, or key requirements are missing or unclear. A plausible candidate a recruiter might still consider. |
| **1** | Weak fit | A **different occupation** with a related field or some transferable skills. Unlikely to be shortlisted. |
| **0** | No fit | **Unrelated** occupation or field; nothing in the bio speaks to the job. |

### Illustrative examples (written for these guidelines; not from the dataset)

- Job: *Registered Nurse, ICU*. Bio: "She has worked in critical care for eight years and is
  certified in advanced cardiac life support." → **3** (same occupation, core requirement evident).
- Job: *Registered Nurse, ICU*. Bio: "He is a nurse educator who teaches pharmacology at a
  community college." → **2** (same occupation, but not clinical ICU work).
- Job: *Paralegal*. Bio: "She is a litigation attorney focusing on employment disputes." → **1**
  (related legal field, different occupation and level).
- Job: *Software Engineer*. Bio: "He is a wedding photographer based in Austin." → **0**.

## Rules

1. **Ignore personal characteristics.** Names, pronouns, gender, age, nationality, ethnicity,
   religion, family status and photos (there are none) must not affect your rating. Two bios
   that differ only in a name or pronoun should get the same rating.
2. **Don't reward writing style.** A short, plain bio of the right occupation beats a polished
   bio of the wrong one.
3. **The bio's first sentence was removed** by the dataset creators (it usually stated the job
   title). Infer the occupation from what's left. If you genuinely can't tell, rate on the
   evidence available and write "unclear occupation" in the comment.
4. **Job descriptions are long.** Skim for the role, the main duties and the hard requirements
   (licences, degrees, years of experience). Ignore company boilerplate, benefits and EEO text.
5. **Seniority mismatch** (e.g. a senior surgeon for a resident post, or a student for a senior
   role) lowers the rating by about one step; it doesn't make it 0.
6. **Don't look anything up** (no web searches for the people or companies). Use only the text.
7. **When torn between two ratings, pick one and say so in the comment** ("2 or 3"). Don't leave
   pairs unrated.
8. **Work independently.** Don't discuss specific pairs with other annotators until everyone has
   finished, except during calibration (below).

## Calibration (do this first)

Before rating independently, all annotators rate the **same first 10 pairs** they see. Then
compare and discuss disagreements against these guidelines, without changing anyone's
saved ratings. You can re-rate those 10 later through "Revisit a rated pair"; the latest
rating counts. Then everyone continues alone.

## Using the app

```
streamlit run research/annotation/app.py
```
1. Type your name in the sidebar (always the same spelling: it names your ratings file).
2. Read the job description (left) and the bio (right), choose 0–3, optionally comment, then
   **Save and continue**.
3. The sidebar shows progress. "Revisit a rated pair" lets you change an earlier rating.
4. Your ratings are in `research/annotation/labels/<your-name>.csv`. Send that file when you're done.

## Data and licences

Job descriptions: LinkedIn Job Postings (2023–2024), Kaggle dataset by arshkon, CC BY-SA 4.0.
Bios: Bias in Bios (De-Arteaga et al., 2019), MIT licence. Don't share the texts outside the project.
