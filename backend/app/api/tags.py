from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import Tag, User

router = APIRouter()


class TagIn(BaseModel):
    name: str


class TagOut(BaseModel):
    id: str
    name: str
    created_at: str


@router.get("", response_model=list[TagOut])
async def list_tags(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Tag).where(Tag.user_id == current_user.id).order_by(Tag.created_at)
    )
    return [TagOut(id=t.id, name=t.name, created_at=str(t.created_at)) for t in result.scalars()]


@router.post("", response_model=TagOut, status_code=status.HTTP_201_CREATED)
async def create_tag(body: TagIn, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    tag = Tag(name=body.name, user_id=current_user.id)
    db.add(tag)
    try:
        await db.commit()
        await db.refresh(tag)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="标签名称已存在")
    return TagOut(id=tag.id, name=tag.name, created_at=str(tag.created_at))


@router.put("/{tag_id}", response_model=TagOut)
async def update_tag(tag_id: str, body: TagIn, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tag).where(Tag.id == tag_id, Tag.user_id == current_user.id))
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    tag.name = body.name
    try:
        await db.commit()
        await db.refresh(tag)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="标签名称已存在")
    return TagOut(id=tag.id, name=tag.name, created_at=str(tag.created_at))


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(tag_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tag).where(Tag.id == tag_id, Tag.user_id == current_user.id))
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    await db.delete(tag)
    await db.commit()
