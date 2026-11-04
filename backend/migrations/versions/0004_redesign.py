"""Feature 002: khung giờ làm, Thùng rác, emoji danh sách, dời buổi học (data-model 002).

Revision ID: 0004_redesign
Revises: 0003_auto_deadline_reminder
Create Date: 2026-11-04
"""

import sqlalchemy as sa
from alembic import op

revision = "0004_redesign"
down_revision = "0003_auto_deadline_reminder"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("tasks", sa.Column("work_date", sa.Date(), nullable=True))
    op.add_column("tasks", sa.Column("work_start", sa.Time(), nullable=True))
    op.add_column("tasks", sa.Column("work_end", sa.Time(), nullable=True))
    op.add_column("tasks", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tasks", sa.Column("trashed_from_list_name", sa.Text(), nullable=True))
    op.create_check_constraint(
        "ck_tasks_work_window_complete",
        "tasks",
        "(work_date IS NULL) = (work_start IS NULL) AND (work_date IS NULL) = (work_end IS NULL)",
    )
    op.create_check_constraint(
        "ck_tasks_work_window_order", "tasks", "work_end IS NULL OR work_end > work_start"
    )
    op.create_index(
        "ix_tasks_deleted_at",
        "tasks",
        ["deleted_at"],
        postgresql_where=sa.text("deleted_at IS NOT NULL"),
    )
    op.create_index("ix_tasks_work_date", "tasks", ["work_date"])

    op.add_column("task_lists", sa.Column("emoji", sa.Text(), nullable=True))
    op.create_check_constraint(
        "ck_task_lists_emoji", "task_lists", "emoji IS NULL OR octet_length(emoji) <= 64"
    )

    op.add_column("class_sessions", sa.Column("original_date", sa.Date(), nullable=True))


def downgrade():
    op.drop_column("class_sessions", "original_date")
    op.drop_constraint("ck_task_lists_emoji", "task_lists", type_="check")
    op.drop_column("task_lists", "emoji")
    op.drop_index("ix_tasks_work_date", table_name="tasks")
    op.drop_index("ix_tasks_deleted_at", table_name="tasks")
    op.drop_constraint("ck_tasks_work_window_order", "tasks", type_="check")
    op.drop_constraint("ck_tasks_work_window_complete", "tasks", type_="check")
    for column in ("trashed_from_list_name", "deleted_at", "work_end", "work_start", "work_date"):
        op.drop_column("tasks", column)
