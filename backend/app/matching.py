"""Resume <-> job matching.

Score (0-100) = 70% skill coverage + 30% semantic similarity.

- Skill coverage is deterministic and explainable: "you have 6 of 8 required
  skills". Nice-to-have skills count half as much as required ones.
- Semantic similarity catches overall fit that exact skill names miss
  (e.g. a resume about "building chatbots" vs a job about "conversational AI").
  It uses real embeddings when the provider offers them, otherwise a local
  bag-of-words cosine similarity, so the feature never breaks.

The LLM does NOT invent the number. We compute it in code and only ask the
LLM to explain it in plain English. That keeps scores consistent between runs.
"""
import math
import re
from collections import Counter

from .skills_vocab import normalize_skill

STOPWORDS = set(
    """a an the and or but if of to in on for with at by from as is are was were be been being this that these
    those it its we you your our they their will would can could should may might must have has had do does did
    not no yes than then so such into about over under across per via etc using use used work working experience
    years year team role job ability strong skills skill including include responsibilities requirements""".split()
)


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _tokens(text: str) -> Counter:
    words = re.findall(r"[a-z][a-z0-9+#.\-]{1,}", text.lower())
    return Counter(w.strip(".-") for w in words if w not in STOPWORDS)


def text_similarity(a: str, b: str) -> float:
    """Bag-of-words cosine similarity (fallback when there are no embeddings)."""
    ta, tb = _tokens(a), _tokens(b)
    common = set(ta) & set(tb)
    dot = sum(ta[w] * tb[w] for w in common)
    na = math.sqrt(sum(v * v for v in ta.values()))
    nb = math.sqrt(sum(v * v for v in tb.values()))
    return dot / (na * nb) if na and nb else 0.0


def compare_skills(resume_skills: list[str], resume_text: str, job_skills: list[str]) -> tuple[list[str], list[str]]:
    """Split job skills into (matched, missing). A skill counts as matched if it's in
    the extracted resume skills OR literally mentioned in the resume text."""
    have = {normalize_skill(s) for s in resume_skills}
    text = " " + resume_text.lower() + " "
    matched, missing = [], []
    for skill in job_skills:
        norm = normalize_skill(skill)
        in_text = re.search(r"(?<![\w])" + re.escape(norm) + r"(?![\w+#])", text) is not None
        (matched if norm in have or in_text else missing).append(skill)
    return matched, missing


def compute_match(
    resume_skills: list[str],
    resume_text: str,
    required: list[str],
    nice_to_have: list[str],
    resume_embedding: list[float] | None,
    job_embedding: list[float] | None,
    job_text: str,
) -> dict:
    req_matched, req_missing = compare_skills(resume_skills, resume_text, required)
    nice_matched, nice_missing = compare_skills(resume_skills, resume_text, nice_to_have)

    # weighted coverage: required = 1 point each, nice-to-have = 0.5
    total_weight = len(required) + 0.5 * len(nice_to_have)
    got_weight = len(req_matched) + 0.5 * len(nice_matched)
    coverage = got_weight / total_weight if total_weight else None

    if resume_embedding and job_embedding:
        semantic = cosine(resume_embedding, job_embedding)
        # embedding cosines for related texts usually sit in ~0.2-0.8; stretch to 0-1
        semantic = min(1.0, max(0.0, (semantic - 0.2) / 0.6))
    else:
        semantic = min(1.0, text_similarity(resume_text, job_text) / 0.35)  # word overlap rarely exceeds ~0.35

    score = semantic if coverage is None else 0.7 * coverage + 0.3 * semantic
    return {
        "score": round(score * 100, 1),
        "matched": req_matched + nice_matched,
        "missing": req_missing + nice_missing,
        "required_missing": req_missing,
        "coverage": coverage,
        "semantic": semantic,
    }
