"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-11
"""
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("username", sa.String(50), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("student", "admin", name="userrole"), nullable=False, server_default="student"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "subjects",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("user_id", UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "name", name="uq_subject_user_name"),
    )

    op.create_table(
        "questions",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subject_id", UUID(as_uuid=False), sa.ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True),
        sa.Column("image_path", sa.String(500), nullable=False),
        sa.Column("ocr_raw_text", sa.Text, nullable=True),
        sa.Column("ocr_verified_text", sa.Text, nullable=True),
        sa.Column("ocr_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("ocr_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("status", sa.Enum("pending", "active", "archived", name="questionstatus"), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_questions_user_id", "questions", ["user_id"])
    op.create_index("ix_questions_subject_id", "questions", ["subject_id"])

    op.create_table(
        "answers",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("question_id", UUID(as_uuid=False), sa.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("answer_text", sa.Text, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_by", UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )

    op.create_table(
        "tags",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("user_id", UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "name", name="uq_tag_user_name"),
    )

    op.create_table(
        "question_tags",
        sa.Column("question_id", UUID(as_uuid=False), sa.ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", UUID(as_uuid=False), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_index("ix_question_tags_tag_question", "question_tags", ["tag_id", "question_id"])

    op.create_table(
        "study_events",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", UUID(as_uuid=False), sa.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_correct", sa.Boolean, nullable=False),
        sa.Column("duration_seconds", sa.Integer, nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_study_events_user_id", "study_events", ["user_id"])
    op.create_index("ix_study_events_question_id", "study_events", ["question_id"])


def downgrade() -> None:
    op.drop_table("study_events")
    op.drop_table("question_tags")
    op.drop_table("tags")
    op.drop_table("answers")
    op.drop_table("questions")
    op.drop_table("subjects")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS questionstatus")
