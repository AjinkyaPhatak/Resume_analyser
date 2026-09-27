import spacy
from sentence_transformers import SentenceTransformer, util
import re

nlp = spacy.load("en_core_web_sm")
model = SentenceTransformer("all-MiniLM-L6-v2")

# --- Entity Extraction ---

def extract_entities(text: str) -> list[str]:
    doc = nlp(text)
    entities = set()

    # named entities — ORG, PRODUCT, GPE often catch tech/tools
    for ent in doc.ents:
        if ent.label_ in ("ORG", "PRODUCT", "GPE", "WORK_OF_ART"):
            entities.add(ent.text.strip())

    # noun chunks — catches "machine learning", "REST APIs", "data pipelines"
    for chunk in doc.noun_chunks:
        chunk_text = chunk.text.strip()
        if 2 < len(chunk_text) < 60:
            entities.add(chunk_text)

    # verb phrases — catches "built", "designed", "led", "deployed"
    for token in doc:
        if token.pos_ == "VERB" and token.dep_ in ("ROOT", "conj", "advcl"):
            phrase = " ".join(
                [token.text] + [c.text for c in token.children if c.dep_ in ("dobj", "attr", "prep")]
            )
            if len(phrase) > 3:
                entities.add(phrase.strip())

    return list(entities)


# --- Single BERT Pass ---

def semantic_match(resume_text: str, jd_text: str) -> dict:
    # Step 1 — entity extraction via spaCy (no BERT yet)
    resume_entities = extract_entities(resume_text)
    jd_entities = extract_entities(jd_text)

    if not resume_entities or not jd_entities:
        return {"error": "Could not extract meaningful entities from input"}

    # Step 2 — single BERT pass, encode everything together for efficiency
    all_texts = resume_entities + jd_entities
    all_embeddings = model.encode(all_texts, convert_to_tensor=True)

    resume_embeddings = all_embeddings[:len(resume_entities)]
    jd_embeddings = all_embeddings[len(resume_entities):]

    # Step 3 — build one similarity matrix, derive everything from it
    similarity_matrix = util.cos_sim(jd_embeddings, resume_embeddings)

    MATCH_THRESHOLD = 0.55
    NEAR_MISS_THRESHOLD = 0.35

    matched = []
    gaps = []
    suggestions = []

    for i, jd_entity in enumerate(jd_entities):
        scores = similarity_matrix[i]
        best_score = float(scores.max())
        best_match_idx = int(scores.argmax())

        if best_score >= MATCH_THRESHOLD:
            matched.append({
                "jd_requirement": jd_entity,
                "resume_match": resume_entities[best_match_idx],
                "score": round(best_score, 2)
            })
        else:
            gaps.append(jd_entity)

            # near miss — resume has something related but not well framed
            if best_score >= NEAR_MISS_THRESHOLD:
                suggestions.append({
                    "gap": jd_entity,
                    "closest_resume_phrase": resume_entities[best_match_idx],
                    "suggestion": f"Consider reframing '{resume_entities[best_match_idx]}' to more explicitly highlight '{jd_entity}'",
                    "similarity": round(best_score, 2)
                })

    match_percent = round(len(matched) / len(jd_entities) * 100, 1)

    return {
        "match_percent": match_percent,
        "matched": matched,
        "gaps": gaps,
        "suggestions": suggestions,
        "total_jd_requirements": len(jd_entities),
        "total_matched": len(matched)
    }