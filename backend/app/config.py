"""App settings, read from environment variables (or a .env file).

Keeping every secret and environment-specific value here means the same code
runs on your laptop, in tests and in production; only the env vars change.
"""
import os
from pathlib import Path


def _load_dotenv() -> None:
    """Tiny .env loader so we don't need an extra dependency."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()


class Settings:
    # Database: SQLite locally, Postgres in production
    # (e.g. postgresql+psycopg://user:pass@host:5432/applypilot)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./applypilot.db")

    # Auth
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

    # LLM: "openai", "anthropic" or "mock" (mock = offline, no API key needed)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock").lower()
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_EMBED_MODEL: str = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5")

    # Abuse protection: max AI calls per user per hour
    AI_CALLS_PER_HOUR: int = int(os.getenv("AI_CALLS_PER_HOUR", "30"))

    # CORS: which frontend origins may call the API
    CORS_ORIGINS: list[str] = [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if o.strip()
    ]


settings = Settings()
