from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import llm, services
from ..auth import get_current_user
from ..database import get_db
from ..models import Job, User
from ..schemas import JobCreate, JobOut, JobUpdate

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def get_own_job(db: Session, user: User, job_id: int) -> Job:
    """Fetch a job and make sure it belongs to the caller.
    Returning 404 (not 403) avoids leaking that the id exists."""
    job = db.get(Job, job_id)
    if not job or job.user_id != user.id:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job


@router.post("", response_model=JobOut, status_code=201)
def create_job(body: JobCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    services.check_rate_limit(db, user, "extract_job")
    try:
        data = services.extract_job(body.raw_text)
    except llm.LLMError as e:
        raise HTTPException(status_code=502, detail=str(e))

    vectors = llm.embed([body.raw_text])
    job = Job(user_id=user.id, raw_text=body.raw_text, url=body.url.strip(),
              embedding=vectors[0] if vectors else None, **data.model_dump())
    db.add(job)
    db.flush()

    resume = services.latest_resume(db, user)
    if resume:
        try:
            services.score_job(db, job, resume)
        except llm.LLMError:
            pass  # job is still saved; score can be retried with /rematch
    db.commit()
    return job


@router.get("", response_model=list[JobOut])
def list_jobs(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(select(Job).where(Job.user_id == user.id).order_by(Job.updated_at.desc())).all()


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_own_job(db, user, job_id)


@router.patch("/{job_id}", response_model=JobOut)
def update_job(job_id: int, body: JobUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    job = get_own_job(db, user, job_id)
    changes = body.model_dump(exclude_unset=True)
    if changes.get("status") == "applied" and job.applied_at is None:
        job.applied_at = datetime.now(timezone.utc)
    for key, value in changes.items():
        if value is not None:
            setattr(job, key, value)
    db.commit()
    return job


@router.delete("/{job_id}", status_code=204)
def delete_job(job_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.delete(get_own_job(db, user, job_id))
    db.commit()
    return Response(status_code=204)


@router.post("/{job_id}/rematch", response_model=JobOut)
def rematch(job_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    job = get_own_job(db, user, job_id)
    resume = services.latest_resume(db, user)
    if not resume:
        raise HTTPException(status_code=400, detail="Upload a resume first.")
    services.check_rate_limit(db, user, "explain_match")
    try:
        services.score_job(db, job, resume)
    except llm.LLMError as e:
        raise HTTPException(status_code=502, detail=str(e))
    db.commit()
    return job


@router.post("/{job_id}/tailor", response_model=JobOut)
def tailor(job_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    job = get_own_job(db, user, job_id)
    resume = services.latest_resume(db, user)
    if not resume:
        raise HTTPException(status_code=400, detail="Upload a resume first.")
    services.check_rate_limit(db, user, "tailor")
    try:
        content = services.tailor_for_job(job, resume)
    except llm.LLMError as e:
        raise HTTPException(status_code=502, detail=str(e))
    job.tailored_bullets = content.bullets
    job.cover_letter = content.cover_letter
    db.commit()
    return job
