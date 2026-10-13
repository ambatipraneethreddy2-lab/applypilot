from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import STATUSES, Job, User
from ..schemas import DashboardOut
from ..skills_vocab import normalize_skill

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    jobs = db.scalars(select(Job).where(Job.user_id == user.id)).all()
    by_status = {s: 0 for s in STATUSES}
    for j in jobs:
        by_status[j.status] = by_status.get(j.status, 0) + 1

    # "Applied" = anything that left the Saved column
    applied = len(jobs) - by_status["saved"]
    responded = by_status["interview"] + by_status["offer"] + by_status["rejected"]
    interviews = by_status["interview"] + by_status["offer"]

    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    applied_this_week = db.scalar(
        select(func.count()).select_from(Job).where(Job.user_id == user.id, Job.applied_at >= week_ago)
    )

    scores = [j.match_score for j in jobs if j.match_score is not None]

    # The most useful insight: which skills keep showing up as gaps?
    # Display the most common original spelling for each normalized skill.
    counts: Counter = Counter()
    spelling: dict[str, Counter] = {}
    for j in jobs:
        for s in {normalize_skill(x): x for x in j.missing_skills}.items():
            counts[s[0]] += 1
            spelling.setdefault(s[0], Counter())[s[1]] += 1
    top_missing = [{"skill": spelling[k].most_common(1)[0][0], "count": c} for k, c in counts.most_common(8)]

    return DashboardOut(
        total=len(jobs),
        by_status=by_status,
        applied_this_week=applied_this_week or 0,
        response_rate=round(100 * responded / applied, 1) if applied else 0.0,
        interview_rate=round(100 * interviews / applied, 1) if applied else 0.0,
        average_match_score=round(sum(scores) / len(scores), 1) if scores else None,
        top_missing_skills=top_missing,
    )
