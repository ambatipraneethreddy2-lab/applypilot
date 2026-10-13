"""Unit tests for the pieces that don't need HTTP."""
import pytest

from app import llm
from app.matching import compare_skills, compute_match, text_similarity
from app.schemas import JobExtraction
from app.skills_vocab import find_known_skills, normalize_skill


def test_normalize_aliases():
    assert normalize_skill("JS") == "javascript"
    assert normalize_skill(" Postgres ") == "postgresql"
    assert normalize_skill("K8s") == "kubernetes"


def test_find_known_skills_handles_symbols_and_false_positives():
    found = find_known_skills("Experience with C++, Node.js and GitHub Actions. Ready to go!")
    assert "c++" in found and "node.js" in found and "github actions" in found
    assert "go" not in found          # plain English "go" is not Golang
    assert "git" not in found         # "GitHub" should not count as "git"


def test_compare_skills_uses_aliases_and_text():
    matched, missing = compare_skills(["JavaScript"], "I deploy with Docker", ["JS", "Docker", "Kubernetes"])
    assert matched == ["JS", "Docker"]
    assert missing == ["Kubernetes"]


def test_score_bounds_and_ordering():
    strong = compute_match(["python", "docker"], "python docker fastapi", ["python", "docker"], [], None, None,
                           "python docker fastapi")
    weak = compute_match(["java"], "java spring", ["python", "docker"], [], None, None, "python docker fastapi")
    assert 0 <= weak["score"] < strong["score"] <= 100


def test_uses_embeddings_when_available():
    m = compute_match([], "x", [], [], [1.0, 0.0], [1.0, 0.0], "y")
    assert m["score"] == 100.0  # identical vectors, no skills -> pure semantic score


def test_text_similarity():
    assert text_similarity("python fastapi docker", "python fastapi docker") == pytest.approx(1.0)
    assert text_similarity("python", "cooking") == 0.0


class FlakyProvider:
    """Returns broken JSON first, valid JSON second: proves the repair retry works."""

    def __init__(self, answers):
        self.answers, self.calls = list(answers), 0

    def chat(self, system, user):
        self.calls += 1
        return self.answers.pop(0)


def test_llm_retries_once_then_succeeds(monkeypatch):
    p = FlakyProvider(['not json at all', '```json\n{"company": "Acme", "required_skills": ["Python", "python"]}\n```'])
    monkeypatch.setattr(llm, "_provider", p)
    out = llm.complete_json("extract_job", "sys", "user", JobExtraction)
    assert out.company == "Acme"
    assert out.required_skills == ["Python"]  # de-duplicated by the schema validator
    assert p.calls == 2


def test_llm_gives_up_after_two_bad_answers(monkeypatch):
    monkeypatch.setattr(llm, "_provider", FlakyProvider(["nope", '{"required_skills": "not a list"}']))
    with pytest.raises(llm.LLMError):
        llm.complete_json("extract_job", "sys", "user", JobExtraction)
