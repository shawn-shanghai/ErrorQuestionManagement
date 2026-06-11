from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, text

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import Answer, Question, QuestionStatus, QuestionTag, StudyEvent, User

router = APIRouter()

W1 = 0.4  # time decay weight
W2 = 0.6  # error rate weight


# ---------------------------------------------------------------------------
# Next recommended card
# ---------------------------------------------------------------------------
@router.get("/next")
async def next_card(
    subject_id: Optional[str] = Query(None),
    tag_ids: list[str] = Query(default=[]),
    exclude_ids: list[str] = Query(default=[]),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Build base query for active questions in scope
    q = select(Question).where(
        Question.user_id == current_user.id,
        Question.status == QuestionStatus.active,
    )
    if subject_id:
        q = q.where(Question.subject_id == subject_id)
    if tag_ids:
        subq = (
            select(QuestionTag.question_id)
            .where(QuestionTag.tag_id.in_(tag_ids))
            .group_by(QuestionTag.question_id)
            .having(func.count(QuestionTag.tag_id.distinct()) == len(tag_ids))
            .scalar_subquery()
        )
        q = q.where(Question.id.in_(subq))
    if exclude_ids:
        q = q.where(Question.id.notin_(exclude_ids))

    result = await db.execute(q)
    questions = result.scalars().all()
    if not questions:
        return None

    # Compute priority score for each question
    now = datetime.now(timezone.utc)
    scored = []
    for question in questions:
        # Last review + accuracy
        events_result = await db.execute(
            select(StudyEvent).where(
                StudyEvent.user_id == current_user.id,
                StudyEvent.question_id == question.id,
            )
        )
        events = events_result.scalars().all()
        if events:
            total = len(events)
            correct = sum(1 for e in events if e.is_correct)
            accuracy = correct / total
            last_reviewed = max(e.reviewed_at for e in events)
            last_reviewed = last_reviewed.replace(tzinfo=timezone.utc) if last_reviewed.tzinfo is None else last_reviewed
            days = (now - last_reviewed).total_seconds() / 86400
            time_decay = min(days / 30, 1.0)
        else:
            accuracy = 0.0
            time_decay = 1.0

        score = W1 * time_decay + W2 * (1 - accuracy)
        scored.append((score, question))

    scored.sort(key=lambda x: x[0], reverse=True)
    best = scored[0][1]

    # Load answer
    ans_result = await db.execute(select(Answer).where(Answer.question_id == best.id))
    answer = ans_result.scalar_one_or_none()

    return {
        "id": best.id,
        "image_url": f"/uploads/{best.image_path}",
        "ocr_verified_text": best.ocr_verified_text,
        "answer_text": answer.answer_text if answer else None,
        "subject_id": best.subject_id,
    }


# ---------------------------------------------------------------------------
# Submit review result
# ---------------------------------------------------------------------------
class SubmitReviewRequest(BaseModel):
    question_id: str
    is_correct: bool
    duration_seconds: Optional[int] = None


@router.post("/submit")
async def submit_review(
    body: SubmitReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify question belongs to user
    result = await db.execute(
        select(Question).where(Question.id == body.question_id, Question.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="题目不存在")

    event = StudyEvent(
        user_id=current_user.id,
        question_id=body.question_id,
        is_correct=body.is_correct,
        duration_seconds=body.duration_seconds,
    )
    db.add(event)
    await db.commit()
    return {"ok": True}
