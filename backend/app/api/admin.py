from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.database import get_db
from app.core.deps import require_admin
from app.models.models import Answer, Question, QuestionStatus, QuestionTag, User

router = APIRouter()


# ---------------------------------------------------------------------------
# Pending OCR list
# ---------------------------------------------------------------------------
@router.get("/questions/pending")
async def pending_questions(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    result = await db.execute(
        select(Question).where(Question.ocr_status == "done", Question.ocr_verified == False)
        .order_by(Question.created_at)
        .limit(50)
    )
    questions = result.scalars().all()
    return [
        {
            "id": q.id,
            "image_url": f"/uploads/{q.image_path}",
            "ocr_raw_text": q.ocr_raw_text,
            "ocr_verified_text": q.ocr_verified_text,
            "subject_id": q.subject_id,
            "status": q.status.value,
            "created_at": str(q.created_at),
        }
        for q in questions
    ]


# ---------------------------------------------------------------------------
# Edit single question
# ---------------------------------------------------------------------------
class QuestionEditRequest(BaseModel):
    subject_id: Optional[str] = None
    ocr_verified_text: Optional[str] = None
    answer_text: Optional[str] = None
    tag_ids: Optional[List[str]] = None
    status: Optional[str] = None


@router.put("/questions/{question_id}")
async def edit_question(
    question_id: str,
    body: QuestionEditRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    result = await db.execute(select(Question).where(Question.id == question_id))
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="题目不存在")

    if body.subject_id is not None:
        q.subject_id = body.subject_id
    if body.ocr_verified_text is not None:
        q.ocr_verified_text = body.ocr_verified_text
        q.ocr_verified = True
    if body.status is not None:
        q.status = QuestionStatus(body.status)

    # Update answer
    if body.answer_text is not None:
        ans_result = await db.execute(select(Answer).where(Answer.question_id == q.id))
        answer = ans_result.scalar_one_or_none()
        if answer:
            answer.answer_text = body.answer_text
            answer.updated_by = admin.id
        else:
            db.add(Answer(question_id=q.id, answer_text=body.answer_text, updated_by=admin.id))

    # Update tags
    if body.tag_ids is not None:
        await db.execute(
            QuestionTag.__table__.delete().where(QuestionTag.question_id == q.id)
        )
        for tag_id in body.tag_ids:
            db.add(QuestionTag(question_id=q.id, tag_id=tag_id))

    await db.commit()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Batch edit
# ---------------------------------------------------------------------------
class BatchEditRequest(BaseModel):
    question_ids: List[str]
    subject_id: Optional[str] = None
    add_tag_ids: Optional[List[str]] = None
    status: Optional[str] = None


@router.post("/questions/batch")
async def batch_edit(
    body: BatchEditRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    if not body.question_ids:
        raise HTTPException(status_code=400, detail="未选择题目")

    if body.subject_id is not None:
        await db.execute(
            update(Question)
            .where(Question.id.in_(body.question_ids))
            .values(subject_id=body.subject_id)
        )

    if body.status is not None:
        await db.execute(
            update(Question)
            .where(Question.id.in_(body.question_ids))
            .values(status=QuestionStatus(body.status))
        )

    if body.add_tag_ids:
        for qid in body.question_ids:
            for tag_id in body.add_tag_ids:
                # Only insert if not already associated
                exists = await db.execute(
                    select(QuestionTag).where(
                        QuestionTag.question_id == qid,
                        QuestionTag.tag_id == tag_id,
                    )
                )
                if not exists.scalar_one_or_none():
                    db.add(QuestionTag(question_id=qid, tag_id=tag_id))

    await db.commit()
    return {"ok": True, "affected": len(body.question_ids)}
