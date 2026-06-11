from datetime import timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import Question, QuestionTag, StudyEvent, User

router = APIRouter()


# ---------------------------------------------------------------------------
# Stats per tag
# ---------------------------------------------------------------------------
@router.get("/stats")
async def study_stats(
    tag_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(StudyEvent).where(StudyEvent.user_id == current_user.id)

    if tag_id:
        # Only events for questions that have this tag
        subq = (
            select(QuestionTag.question_id)
            .where(QuestionTag.tag_id == tag_id)
            .scalar_subquery()
        )
        q = q.where(StudyEvent.question_id.in_(subq))

    result = await db.execute(q)
    events = result.scalars().all()

    if not events:
        return {
            "total_reviews": 0,
            "correct_reviews": 0,
            "accuracy_rate": None,
            "last_reviewed_at": None,
        }

    total = len(events)
    correct = sum(1 for e in events if e.is_correct)
    last = max(e.reviewed_at for e in events)

    return {
        "total_reviews": total,
        "correct_reviews": correct,
        "accuracy_rate": round(correct / total, 3),
        "last_reviewed_at": str(last),
    }


# ---------------------------------------------------------------------------
# History list
# ---------------------------------------------------------------------------
@router.get("/history")
async def study_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(StudyEvent, Question)
        .join(Question, StudyEvent.question_id == Question.id)
        .where(StudyEvent.user_id == current_user.id)
        .order_by(StudyEvent.reviewed_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(q)
    rows = result.all()

    return [
        {
            "event_id": event.id,
            "question_id": question.id,
            "image_url": f"/uploads/{question.image_path}",
            "ocr_verified_text": question.ocr_verified_text,
            "is_correct": event.is_correct,
            "duration_seconds": event.duration_seconds,
            "reviewed_at": str(event.reviewed_at),
        }
        for event, question in rows
    ]
