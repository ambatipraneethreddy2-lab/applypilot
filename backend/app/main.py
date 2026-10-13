"""ApplyPilot API entry point.

Run locally:  uvicorn app.main:app --reload
Docs:         http://localhost:8000/docs  (auto-generated Swagger UI)
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine
from .routers import auth, dashboard, jobs, resumes

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

# For an MVP we create tables on startup. In a bigger project you'd use
# Alembic migrations instead (mention this in interviews!).
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ApplyPilot API", version="1.0.0",
              description="AI job application tracker: extract, match, tailor, track.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(resumes.router)
app.include_router(jobs.router)
app.include_router(dashboard.router)


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok", "llm_provider": settings.LLM_PROVIDER}
