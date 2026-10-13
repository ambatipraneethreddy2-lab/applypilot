from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import llm, services
from ..auth import get_current_user
from ..database import get_db
from ..models import Job, Resume, User
from ..resume_parser import ResumeParseError, extract_text
from ..schemas import ResumeOut

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


def to_out(r: Resume) -> ResumeOut:
    return ResumeOut(id=r.id, filename=r.filename, skills=r.skills,
                     text_preview=r.text[:600], created_at=r.created_at)


@router.post("", response_model=ResumeOut, status_code=201)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data = await file.read()
    try:
        text = extract_text(file.filename or "resume", data)
    except ResumeParseError as e:
        raise HTTPException(status_code=400, detail=str(e))

    services.check_rate_limit(db, user, "extract_resume")
    try:
        skills = services.extract_resume_skills(text)
    except llm.LLMError as e:
        raise HTTPException(status_code=502, detail=str(e))
    vectors = llm.embed([text])

    resume = Resume(user_id=user.id, filename=file.filename or "resume", text=text,
                    skills=skills, embedding=vectors[0] if vectors else None)
    db.add(resume)
    db.flush()

    # New resume -> re-score existing jobs (cheap: score is computed locally,
    # only the short explanation calls the LLM). Capped to keep uploads fast.
    jobs = db.scalars(select(Job).where(Job.user_id == user.id).order_by(Job.id.desc()).limit(20)).all()
    for job in jobs:
        try:
            services.score_job(db, job, resume)
        except llm.LLMError:
            pass  # keep the old score; the user can re-run matching from the job page
    db.commit()
    return to_out(resume)


@router.get("/latest", response_model=ResumeOut | None)
def get_latest(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    r = services.latest_resume(db, user)
    return to_out(r) if r else None
