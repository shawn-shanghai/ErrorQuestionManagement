from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import Subject, Question, User

router = APIRouter()


class SubjectIn(BaseModel):
    name: str
    description: str | None = None


class SubjectOut(BaseModel):
    id: str
    name: str
    description: str | None
    created_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=list[SubjectOut])
async def list_subjects(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Subject).where(Subject.user_id == current_user.id).order_by(Subject.created_at)
    )
    return [SubjectOut(id=s.id, name=s.name, description=s.description, created_at=str(s.created_at)) for s in result.scalars()]


@router.post("", response_model=SubjectOut, status_code=status.HTTP_201_CREATED)
async def create_subject(body: SubjectIn, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    subject = Subject(name=body.name, description=body.description, user_id=current_user.id)
    db.add(subject)
    try:
        await db.commit()
        await db.refresh(subject)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="科目名称已存在")
    return SubjectOut(id=subject.id, name=subject.name, description=subject.description, created_at=str(subject.created_at))


@router.put("/{subject_id}", response_model=SubjectOut)
async def update_subject(subject_id: str, body: SubjectIn, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subject).where(Subject.id == subject_id, Subject.user_id == current_user.id))
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="科目不存在")
    subject.name = body.name
    subject.description = body.description
    try:
        await db.commit()
        await db.refresh(subject)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="科目名称已存在")
    return SubjectOut(id=subject.id, name=subject.name, description=subject.description, created_at=str(subject.created_at))


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subject(subject_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subject).where(Subject.id == subject_id, Subject.user_id == current_user.id))
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="科目不存在")
    # Null out questions' subject_id (handled by DB ON DELETE SET NULL)
    await db.delete(subject)
    await db.commit()
