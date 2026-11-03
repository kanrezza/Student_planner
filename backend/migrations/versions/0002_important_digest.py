"""Mức "Quan trọng" và thông báo tổng hợp hằng ngày (FR-065 đến FR-070, task T147).

Revision ID: 0002_important_digest
Revises: 0001_initial
Create Date: 2026-11-04
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_important_digest"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

_FALSE = sa.false()
_TRUE = sa.true()


def upgrade():
    op.add_column(
        "subjects", sa.Column("is_important", sa.Boolean(), nullable=False, server_default=_FALSE)
    )
    op.add_column(
        "tasks", sa.Column("is_important", sa.Boolean(), nullable=False, server_default=_FALSE)
    )
    op.add_column("class_sessions", sa.Column("important_override", sa.Boolean(), nullable=True))

    op.add_column(
        "settings",
        sa.Column(
            "important_reminder_offsets",
            postgresql.ARRAY(sa.Integer()),
            nullable=False,
            server_default=sa.text("'{1440,180,60,15}'::integer[]"),
        ),
    )
    op.add_column(
        "settings",
        sa.Column(
            "exam_extra_reminder_offsets",
            postgresql.ARRAY(sa.Integer()),
            nullable=False,
            server_default=sa.text("'{10080}'::integer[]"),
        ),
    )
    op.add_column(
        "settings",
        sa.Column(
            "exam_reminder_minutes", sa.Integer(), nullable=False, server_default=sa.text("60")
        ),
    )
    op.add_column(
        "settings",
        sa.Column("daily_digest_enabled", sa.Boolean(), nullable=False, server_default=_TRUE),
    )
    op.add_column(
        "settings",
        sa.Column(
            "daily_digest_time", sa.Time(), nullable=False, server_default=sa.text("'05:00'")
        ),
    )
    op.add_column(
        "settings",
        sa.Column("daily_digest_overdue_only", sa.Boolean(), nullable=False, server_default=_TRUE),
    )
    op.create_check_constraint(
        "ck_settings_important_offsets",
        "settings",
        "cardinality(important_reminder_offsets) BETWEEN 1 AND 6 "
        "AND 0 <= ALL(important_reminder_offsets)",
    )
    op.create_check_constraint(
        "ck_settings_exam_extra_offsets",
        "settings",
        "cardinality(exam_extra_reminder_offsets) <= 3 AND 0 <= ALL(exam_extra_reminder_offsets)",
    )
    op.create_check_constraint(
        "ck_settings_exam_reminder_minutes", "settings", "exam_reminder_minutes >= 0"
    )


def downgrade():
    for name in (
        "ck_settings_exam_reminder_minutes",
        "ck_settings_exam_extra_offsets",
        "ck_settings_important_offsets",
    ):
        op.drop_constraint(name, "settings", type_="check")
    for column in (
        "daily_digest_overdue_only",
        "daily_digest_time",
        "daily_digest_enabled",
        "exam_reminder_minutes",
        "exam_extra_reminder_offsets",
        "important_reminder_offsets",
    ):
        op.drop_column("settings", column)
    op.drop_column("class_sessions", "important_override")
    op.drop_column("tasks", "is_important")
    op.drop_column("subjects", "is_important")
