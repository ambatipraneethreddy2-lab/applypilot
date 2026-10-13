"""Database tables.

users ──< resumes
  │
  └────< jobs ──< ai_usage (rate limiting log lives per user)

A job row is both "the posting" and "my application to it" (status column),
which keeps the MVP simple: one card on the board = one row.
"""
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

STATUSES = ["saved", "applied", "interview", "offer", "rejected"]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    resumes: Mapped[list["Resume"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    jobs: Mapped[list["Job"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    text: Mapped[str] = mapped_column(Text)
    skills: Mapped[list] = mapped_column(JSON, default=list)        # extracted by the LLM
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)  # vector (pgvector in prod)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[User] = relationship(back_populates="resumes")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    # Raw input + structured fields the LLM extracted from it
    raw_text: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(1000), default="")
    company: Mapped[str] = mapped_column(String(255), default="")
    title: Mapped[str] = mapped_column(String(255), default="")
    location: Mapped[str] = mapped_column(String(255), default="")
    salary: Mapped[str] = mapped_column(String(255), default="")
    deadline: Mapped[str] = mapped_column(String(50), default="")
    required_skills: Mapped[list] = mapped_column(JSON, default=list)
    nice_to_have_skills: Mapped[list] = mapped_column(JSON, default=list)
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Match results against the user's latest resume
    match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    matched_skills: Mapped[list] = mapped_column(JSON, default=list)
    missing_skills: Mapped[list] = mapped_column(JSON, default=list)
    match_summary: Mapped[str] = mapped_column(Text, default="")

    # Generated content
    tailored_bullets: Mapped[list] = mapped_column(JSON, default=list)
    cover_letter: Mapped[str] = mapped_column(Text, default="")

    # Tracker
    status: Mapped[str] = mapped_column(String(20), default="saved", index=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user: Mapped[User] = relationship(back_populates="jobs")


class AIUsage(Base):
    """One row per AI call, used to rate-limit each user (protects your API bill)."""
    __tablename__ = "ai_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    action: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
