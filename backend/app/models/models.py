import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey,
    Index, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    student = "student"
    admin = "admin"


class QuestionStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    archived = "archived"


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.student)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    subjects = relationship("Subject", back_populates="user", cascade="all, delete-orphan")
    tags = relationship("Tag", back_populates="user", cascade="all, delete-orphan")
    questions = relationship("Question", back_populates="user", cascade="all, delete-orphan")
    study_events = relationship("StudyEvent", back_populates="user", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Subject
# ---------------------------------------------------------------------------
class Subject(Base):
    __tablename__ = "subjects"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_subject_user_name"),)

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="subjects")
    questions = relationship("Question", back_populates="subject")


# ---------------------------------------------------------------------------
# Question
# ---------------------------------------------------------------------------
class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(UUID(as_uuid=False), ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True, index=True)
    image_path = Column(String(500), nullable=False)
    ocr_raw_text = Column(Text, nullable=True)
    ocr_verified_text = Column(Text, nullable=True)
    ocr_verified = Column(Boolean, default=False, nullable=False)
    ocr_status = Column(String(20), default="pending", nullable=False)  # pending|done|failed
    status = Column(Enum(QuestionStatus), nullable=False, default=QuestionStatus.pending)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="questions")
    subject = relationship("Subject", back_populates="questions")
    answer = relationship("Answer", back_populates="question", uselist=False, cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="question_tags", back_populates="questions")
    study_events = relationship("StudyEvent", back_populates="question", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Answer
# ---------------------------------------------------------------------------
class Answer(Base):
    __tablename__ = "answers"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    question_id = Column(UUID(as_uuid=False), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, unique=True)
    answer_text = Column(Text, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    question = relationship("Question", back_populates="answer")


# ---------------------------------------------------------------------------
# Tag
# ---------------------------------------------------------------------------
class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_tag_user_name"),)

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String(100), nullable=False)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="tags")
    questions = relationship("Question", secondary="question_tags", back_populates="tags")


# ---------------------------------------------------------------------------
# QuestionTag  (association table)
# ---------------------------------------------------------------------------
class QuestionTag(Base):
    __tablename__ = "question_tags"
    __table_args__ = (
        Index("ix_question_tags_tag_question", "tag_id", "question_id"),
    )

    question_id = Column(
        UUID(as_uuid=False), ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id = Column(
        UUID(as_uuid=False), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )


# ---------------------------------------------------------------------------
# StudyEvent
# ---------------------------------------------------------------------------
class StudyEvent(Base):
    __tablename__ = "study_events"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(UUID(as_uuid=False), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    is_correct = Column(Boolean, nullable=False)
    duration_seconds = Column(Integer, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="study_events")
    question = relationship("Question", back_populates="study_events")
