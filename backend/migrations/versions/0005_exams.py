"""Lịch thi: bảng exams, exam_tags và nhãn hệ thống "Thi" (feature 001 US11, data-model "exams").

Revision ID: 0005_exams
Revises: 0004_redesign
Create Date: 2026-11-05
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0005_exams"
down_revision = "0004_redesign"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "exams",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("course_code", sa.Text()),
        sa.Column("course_name", sa.Text(), nullable=False),
        sa.Column("attempt", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("exam_format", sa.Text()),
        sa.Column("room", sa.Text()),
        sa.Column("candidate_number", sa.Text()),
        sa.Column("reminder_offsets", postgresql.ARRAY(sa.SmallInteger())),
        sa.Column("is_important", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("end_at > start_at", name="ck_exams_times"),
        sa.CheckConstraint("attempt >= 1", name="ck_exams_attempt"),
        sa.CheckConstraint(
            "char_length(btrim(course_name)) BETWEEN 1 AND 200", name="ck_exams_name"
        ),
        sa.CheckConstraint(
            "reminder_offsets IS NULL OR 0 <= ALL(reminder_offsets)", name="ck_exams_reminders"
        ),
    )
    op.create_index("ix_exams_date", "exams", ["date"])
    op.create_index("ix_exams_start_at", "exams", ["start_at"])

    op.create_table(
        "exam_tags",
        sa.Column(
            "exam_id",
            sa.BigInteger(),
            sa.ForeignKey("exams.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "tag_id",
            sa.BigInteger(),
            sa.ForeignKey("tags.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("position", sa.SmallInteger(), nullable=False),
    )

    # Nhãn "Thi" người dùng đã tự tạo được nhận làm nhãn hệ thống (tên nhãn là duy nhất).
    op.execute(
        "UPDATE tags SET system_key = 'exam' WHERE lower(name) = 'thi' AND system_key IS NULL"
    )
    op.execute(
        """
        INSERT INTO tags (name, color, system_key)
        SELECT 'Thi', 'c07', 'exam'
        WHERE NOT EXISTS (SELECT 1 FROM tags WHERE system_key = 'exam')
        """
    )


def downgrade():
    op.execute("DELETE FROM tags WHERE system_key = 'exam'")
    op.drop_table("exam_tags")
    op.drop_index("ix_exams_start_at", table_name="exams")
    op.drop_index("ix_exams_date", table_name="exams")
    op.drop_table("exams")
