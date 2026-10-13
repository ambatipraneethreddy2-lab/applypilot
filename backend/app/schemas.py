"""Pydantic models: the shape of data going in and out of the API,
and the strict shape we force the LLM's JSON answers into."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

Status = Literal["saved", "applied", "interview", "offer", "rejected"]


# ---------- Auth ----------
class SignupIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(default="", max_length=120)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    name: str


# ---------- LLM output contracts ----------
def _clean_list(values: list[str]) -> list[str]:
    """Trim, drop empties and de-duplicate (case-insensitive), keeping order."""
    seen, out = set(), []
    for v in values or []:
        v = str(v).strip()
        if v and v.lower() not in seen:
            seen.add(v.lower())
            out.append(v)
    return out


class JobExtraction(BaseModel):
    company: str = ""
    title: str = ""
    location: str = ""
    salary: str = ""
    deadline: str = ""
    required_skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)

    @field_validator("required_skills", "nice_to_have_skills")
    @classmethod
    def clean_skills(cls, v: list[str]) -> list[str]:
        return _clean_list(v)

    @field_validator("company", "title", "location", "salary", "deadline", mode="before")
    @classmethod
    def none_to_empty(cls, v):
        return "" if v is None else str(v).strip()


class ResumeExtraction(BaseModel):
    skills: list[str] = Field(default_factory=list)

    @field_validator("skills")
    @classmethod
    def clean_skills(cls, v: list[str]) -> list[str]:
        return _clean_list(v)


class MatchExplanation(BaseModel):
    summary: str = ""


class TailoredContent(BaseModel):
    bullets: list[str] = Field(default_factory=list, max_length=8)
    cover_letter: str = ""


# ---------- Resumes ----------
class ResumeOut(BaseModel):
    id: int
    filename: str
    skills: list[str]
    text_preview: str
    created_at: datetime


# ---------- Jobs ----------
class JobCreate(BaseModel):
    raw_text: str = Field(min_length=50, max_length=30000)
    url: str = Field(default="", max_length=1000)


class JobUpdate(BaseModel):
    status: Status | None = None
    notes: str | None = Field(default=None, max_length=5000)
    company: str | None = Field(default=None, max_length=255)
    title: str | None = Field(default=None, max_length=255)


class JobOut(BaseModel):
    id: int
    url: str
    company: str
    title: str
    location: str
    salary: str
    deadline: str
    required_skills: list[str]
    nice_to_have_skills: list[str]
    match_score: float | None
    matched_skills: list[str]
    missing_skills: list[str]
    match_summary: str
    tailored_bullets: list[str]
    cover_letter: str
    status: Status
    notes: str
    applied_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------- Dashboard ----------
class DashboardOut(BaseModel):
    total: int
    by_status: dict[str, int]
    applied_this_week: int
    response_rate: float          # % of applied jobs that reached interview/offer/rejected
    interview_rate: float         # % of applied jobs that reached interview/offer
    average_match_score: float | None
    top_missing_skills: list[dict]  # [{"skill": "Docker", "count": 7}, ...]
