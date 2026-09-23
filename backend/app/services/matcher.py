from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("all-MiniLM-L6-v2")

def extract_skills(text: str) -> list[str]:
    # split by common delimiters and clean up
    import re
    lines = re.split(r'[,\n•·\-|/]', text)
    skills = [line.strip() for line in lines if 2 < len(line.strip()) < 60]
    return skills

def semantic_match(resume_text: str, jd_text: str) -> dict:
    resume_skills = extract_skills(resume_text)
    jd_skills = extract_skills(jd_text)

    if not resume_skills or not jd_skills:
        return {"error": "Could not extract skills from input"}

    resume_embeddings = model.encode(resume_skills, convert_to_tensor=True)
    jd_embeddings = model.encode(jd_skills, convert_to_tensor=True)

    matched = []
    unmatched = []
    THRESHOLD = 0.75

    for i, jd_skill in enumerate(jd_skills):
        scores = util.cos_sim(jd_embeddings[i], resume_embeddings)[0]
        best_score = float(scores.max())
        best_match_idx = int(scores.argmax())

        if best_score >= THRESHOLD:
            matched.append({
                "jd_skill": jd_skill,
                "resume_match": resume_skills[best_match_idx],
                "score": round(best_score, 2)
            })
        else:
            unmatched.append(jd_skill)

    match_percent = round(len(matched) / len(jd_skills) * 100, 1)

    return {
        "match_percent": match_percent,
        "matched_skills": matched,
        "missing_skills": unmatched,
        "total_jd_skills": len(jd_skills),
        "total_matched": len(matched)
    }