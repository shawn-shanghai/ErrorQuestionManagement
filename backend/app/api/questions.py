import asyncio
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from PIL import Image
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import Answer, Question, QuestionStatus, QuestionTag, Tag, User
from app.services.ocr import extract_text

router = APIRouter()


# ---------------------------------------------------------------------------
# Background OCR task
# ---------------------------------------------------------------------------
def _run_ocr_sync(question_id: str, image_path: str, db_url: str):
    """Run OCR synchronously in a thread pool, update DB directly."""
    import psycopg2, os
    text = ""
    try:
        text = extract_text(image_path)
        status_val = "done"
    except Exception:
        status_val = "failed"

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute(
        "UPDATE questions SET ocr_raw_text=%s, ocr_verified_text=%s, ocr_status=%s, updated_at=now() WHERE id=%s",
        (text, text, status_val, question_id),
    )
    conn.commit()
    cur.close()
    conn.close()


async def _ocr_background(question_id: str, image_path: str):
    loop = asyncio.get_event_loop()
    db_url = settings.DATABASE_URL
    await loop.run_in_executor(None, _run_ocr_sync, question_id, image_path, db_url)


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------
class UploadResponse(BaseModel):
    question_id: str
    ocr_status: str


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_question(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    subject_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Validate file type
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=400, detail="仅支持 JPG/PNG/WebP 图片")

    # Build upload path
    from datetime import datetime
    month_dir = datetime.now().strftime("%Y%m")
    dest_dir = Path(settings.UPLOAD_PATH) / current_user.id / month_dir
    dest_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4()}.jpg"
    dest_path = dest_dir / filename

    # Save & convert to JPEG
    contents = await file.read()
    from io import BytesIO
    img = Image.open(BytesIO(contents)).convert("RGB")
    img.save(str(dest_path), "JPEG", quality=85)

    relative_path = f"{current_user.id}/{month_dir}/{filename}"

    question = Question(
        user_id=current_user.id,
        subject_id=subject_id,
        image_path=relative_path,
        ocr_status="pending",
    )
    db.add(question)
    await db.commit()
    await db.refresh(question)

    background_tasks.add_task(_ocr_background, question.id, str(dest_path))

    return UploadResponse(question_id=question.id, ocr_status="pending")


# ---------------------------------------------------------------------------
# OCR status polling
# ---------------------------------------------------------------------------
class OcrStatusResponse(BaseModel):
    ocr_status: str
    ocr_verified_text: Optional[str]


@router.get("/{question_id}/ocr-status", response_model=OcrStatusResponse)
async def get_ocr_status(
    question_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Question).where(Question.id == question_id, Question.user_id == current_user.id)
    )
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    return OcrStatusResponse(ocr_status=question.ocr_status, ocr_verified_text=question.ocr_verified_text)


# ---------------------------------------------------------------------------
# Update OCR verified text
# ---------------------------------------------------------------------------
class OcrUpdateRequest(BaseModel):
    ocr_verified_text: str


@router.put("/{question_id}/ocr")
async def update_ocr_text(
    question_id: str,
    body: OcrUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Question).where(Question.id == question_id, Question.user_id == current_user.id)
    )
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    question.ocr_verified_text = body.ocr_verified_text
    question.ocr_verified = True
    await db.commit()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Filtered question list (subject + multi-tag AND)
# ---------------------------------------------------------------------------
class QuestionListItem(BaseModel):
    id: str
    subject_id: Optional[str]
    ocr_verified_text: Optional[str]
    image_path: str
    status: str
    has_answer: bool
    created_at: str


@router.get("", response_model=list[QuestionListItem])
async def list_questions(
    subject_id: Optional[str] = Query(None),
    tag_ids: List[str] = Query(default=[]),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Question).where(
        Question.user_id == current_user.id,
        Question.status == QuestionStatus.active,
    )
    if subject_id:
        query = query.where(Question.subject_id == subject_id)

    # Multi-tag AND: keep only questions having ALL selected tags
    if tag_ids:
        subq = (
            select(QuestionTag.question_id)
            .where(QuestionTag.tag_id.in_(tag_ids))
            .group_by(QuestionTag.question_id)
            .having(func.count(QuestionTag.tag_id.distinct()) == len(tag_ids))
            .scalar_subquery()
        )
        query = query.where(Question.id.in_(subq))

    query = query.order_by(Question.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    questions = result.scalars().all()

    # Load answers in one query
    q_ids = [q.id for q in questions]
    answers_result = await db.execute(select(Answer).where(Answer.question_id.in_(q_ids)))
    answered = {a.question_id for a in answers_result.scalars()}

    return [
        QuestionListItem(
            id=q.id,
            subject_id=q.subject_id,
            ocr_verified_text=q.ocr_verified_text,
            image_path=q.image_path,
            status=q.status.value,
            has_answer=q.id in answered,
            created_at=str(q.created_at),
        )
        for q in questions
    ]


# ---------------------------------------------------------------------------
# Question detail
# ---------------------------------------------------------------------------
class QuestionDetail(BaseModel):
    id: str
    subject_id: Optional[str]
    image_path: str
    image_url: str
    ocr_raw_text: Optional[str]
    ocr_verified_text: Optional[str]
    ocr_verified: bool
    ocr_status: str
    status: str
    answer_text: Optional[str]
    tags: list[dict]
    created_at: str


@router.get("/{question_id}", response_model=QuestionDetail)
async def get_question(
    question_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Question).where(Question.id == question_id, Question.user_id == current_user.id)
    )
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="题目不存在")

    # Load tags
    tag_result = await db.execute(
        select(Tag).join(QuestionTag, Tag.id == QuestionTag.tag_id).where(QuestionTag.question_id == q.id)
    )
    tags = [{"id": t.id, "name": t.name} for t in tag_result.scalars()]

    # Load answer
    ans_result = await db.execute(select(Answer).where(Answer.question_id == q.id))
    answer = ans_result.scalar_one_or_none()

    return QuestionDetail(
        id=q.id,
        subject_id=q.subject_id,
        image_path=q.image_path,
        image_url=f"/uploads/{q.image_path}",
        ocr_raw_text=q.ocr_raw_text,
        ocr_verified_text=q.ocr_verified_text,
        ocr_verified=q.ocr_verified,
        ocr_status=q.ocr_status,
        status=q.status.value,
        answer_text=answer.answer_text if answer else None,
        tags=tags,
        created_at=str(q.created_at),
    )
