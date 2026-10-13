"""LLM layer: one small interface, three providers.

    complete_json(task, system, user, schema) -> validated Pydantic object
    embed(texts) -> list of vectors, or None if the provider has no embeddings

Why this design (good interview talking point):
- The rest of the app never talks to OpenAI/Anthropic directly, so swapping
  providers is a config change (LLM_PROVIDER=openai|anthropic|mock).
- Every answer is forced into a Pydantic schema. If the model returns broken
  or wrong-shaped JSON we retry ONCE, telling it exactly what was wrong; if it
  still fails we raise LLMError and the API returns a clean 502 instead of
  crashing or saving garbage.
- The "mock" provider is deterministic and offline, so tests and demos run
  with no API key and no cost.
"""
from __future__ import annotations

import json
import logging
import re
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from .config import settings
from .skills_vocab import find_known_skills

log = logging.getLogger("applypilot.llm")
T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """Raised when the model can't produce a valid answer."""


def _extract_json(text: str) -> dict:
    """Models sometimes wrap JSON in ```json fences or add a sentence; pull out the object."""
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    else:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            text = text[start : end + 1]
    return json.loads(text)


# ---------------------------------------------------------------- providers
class OpenAIProvider:
    def __init__(self) -> None:
        if not settings.OPENAI_API_KEY:
            raise LLMError("OPENAI_API_KEY is not set")
        self.client = httpx.Client(
            base_url="https://api.openai.com/v1",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            timeout=60,
        )

    def chat(self, system: str, user: str) -> str:
        r = self.client.post(
            "/chat/completions",
            json={
                "model": settings.OPENAI_MODEL,
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            },
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    def embed(self, texts: list[str]) -> list[list[float]] | None:
        r = self.client.post(
            "/embeddings",
            json={"model": settings.OPENAI_EMBED_MODEL, "input": [t[:8000] for t in texts]},
        )
        r.raise_for_status()
        return [d["embedding"] for d in r.json()["data"]]


class AnthropicProvider:
    def __init__(self) -> None:
        if not settings.ANTHROPIC_API_KEY:
            raise LLMError("ANTHROPIC_API_KEY is not set")
        self.client = httpx.Client(
            base_url="https://api.anthropic.com/v1",
            headers={"x-api-key": settings.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01"},
            timeout=60,
        )

    def chat(self, system: str, user: str) -> str:
        r = self.client.post(
            "/messages",
            json={
                "model": settings.ANTHROPIC_MODEL,
                "max_tokens": 2000,
                "temperature": 0.2,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
        )
        r.raise_for_status()
        return "".join(b.get("text", "") for b in r.json()["content"])

    def embed(self, texts: list[str]) -> list[list[float]] | None:
        return None  # no embeddings endpoint -> matching falls back to local TF-IDF


class MockProvider:
    """Offline, deterministic stand-in. Uses keyword rules instead of a model."""

    current_task: str = ""

    def chat(self, system: str, user: str) -> str:
        data = _between(user, "<job_posting>", "</job_posting>") or _between(user, "<resume>", "</resume>") or user
        if self.current_task == "extract_job":
            return json.dumps(_mock_extract_job(data))
        if self.current_task == "extract_resume":
            return json.dumps({"skills": find_known_skills(data)})
        if self.current_task == "explain_match":
            info = json.loads(_between(user, "<match_data>", "</match_data>") or "{}")
            matched, missing = info.get("matched", []), info.get("missing", [])
            summary = (
                f"You match {len(matched)} of {len(matched) + len(missing)} listed skills"
                + (f", including {', '.join(matched[:3])}." if matched else ".")
                + (f" Biggest gaps: {', '.join(missing[:3])}." if missing else " No major gaps.")
            )
            return json.dumps({"summary": summary})
        if self.current_task == "tailor":
            info = json.loads(_between(user, "<match_data>", "</match_data>") or "{}")
            matched = info.get("matched", []) or ["software engineering"]
            role, company = info.get("title") or "this role", info.get("company") or "your team"
            bullets = [
                f"Built and shipped features using {s}, focusing on reliability and clean, testable code."
                for s in matched[:4]
            ]
            letter = (
                f"Dear Hiring Team,\n\nI'm excited to apply for {role} at {company}. "
                f"My experience with {', '.join(matched[:3])} maps directly to what you're looking for, "
                "and I enjoy turning ambiguous problems into working products.\n\n"
                "I'd welcome the chance to talk about how I can contribute.\n\nBest regards"
            )
            return json.dumps({"bullets": bullets, "cover_letter": letter})
        return "{}"

    def embed(self, texts: list[str]) -> list[list[float]] | None:
        return None


def _between(text: str, start: str, end: str) -> str:
    i, j = text.find(start), text.find(end)
    return text[i + len(start) : j].strip() if i != -1 and j > i else ""


def _mock_extract_job(text: str) -> dict:
    def field(*labels: str) -> str:
        for label in labels:
            m = re.search(rf"^\s*{label}\s*[:\-]\s*(.+)$", text, re.IGNORECASE | re.MULTILINE)
            if m:
                return m.group(1).strip()
        return ""

    first_line = next((l.strip() for l in text.splitlines() if l.strip()), "")
    nice_section = re.split(r"nice to have|preferred|bonus", text, flags=re.IGNORECASE)
    required_text = nice_section[0]
    nice_text = " ".join(nice_section[1:]) if len(nice_section) > 1 else ""
    required = find_known_skills(required_text)
    nice = [s for s in find_known_skills(nice_text) if s not in required]
    return {
        "company": field("company", "employer", "organization"),
        "title": field("title", "job title", "role", "position") or first_line[:120],
        "location": field("location"),
        "salary": field("salary", "compensation", "pay"),
        "deadline": field("deadline", "apply by"),
        "required_skills": required,
        "nice_to_have_skills": nice,
    }


# ---------------------------------------------------------------- public API
_provider = None


def get_provider():
    global _provider
    if _provider is None:
        name = settings.LLM_PROVIDER
        _provider = {"openai": OpenAIProvider, "anthropic": AnthropicProvider}.get(name, MockProvider)()
        log.info("LLM provider: %s", type(_provider).__name__)
    return _provider


def complete_json(task: str, system: str, user: str, schema: type[T]) -> T:
    provider = get_provider()
    if isinstance(provider, MockProvider):
        provider.current_task = task

    system = (
        system
        + "\n\nRespond with ONLY a JSON object matching this JSON schema, no prose:\n"
        + json.dumps(schema.model_json_schema())
    )
    last_error = ""
    for attempt in range(2):  # first try + one repair try
        prompt = user if attempt == 0 else (
            f"{user}\n\nYour previous answer was invalid: {last_error}\nReturn corrected JSON only."
        )
        try:
            raw = provider.chat(system, prompt)
            return schema.model_validate(_extract_json(raw))
        except (json.JSONDecodeError, ValidationError) as e:
            last_error = str(e)[:500]
            log.warning("LLM %s returned invalid JSON (attempt %d): %s", task, attempt + 1, last_error)
        except httpx.HTTPError as e:
            log.error("LLM %s HTTP error: %s", task, e)
            raise LLMError("The AI service is unavailable right now. Please try again.") from e
    raise LLMError("The AI returned an invalid response. Please try again.")


def embed(texts: list[str]) -> list[list[float]] | None:
    try:
        return get_provider().embed(texts)
    except httpx.HTTPError as e:
        log.warning("Embedding failed, falling back to local similarity: %s", e)
        return None
