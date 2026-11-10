"""Task lặp lại: bảng task_series và các cột series của tasks (feature 003 US3, data-model §4).

Revision ID: 0008_recurring_tasks
Revises: 0007_search
Create Date: 2026-11-06
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0008_recurring_tasks"
down_revision = "0007_search"
branch_labels = None
depends_on = None


def upgrade():
    # Khôi phục bản sao lưu cũ hơn để lại bảng task_series của dữ liệu mới (bản cũ không biết bảng
    # này); chuỗi cũ không còn task nào trỏ tới nên bỏ đi rồi tạo lại.
    op.execute("DROP TABLE IF EXISTS task_series CASCADE")
    op.create_table(
        "task_series",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("freq", sa.Text(), nullable=False),
        sa.Column("interval_days", sa.SmallInteger()),
        sa.Column("weekdays", postgresql.ARRAY(sa.SmallInteger())),
        sa.Column("month_day", sa.SmallInteger()),
        sa.Column("anchor_date", sa.Date(), nullable=False),
        sa.Column("end_kind", sa.Text(), nullable=False, server_default="never"),
        sa.Column("end_date", sa.Date()),
        sa.Column("end_count", sa.SmallInteger()),
        sa.Column("occurrences_created", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("template", postgresql.JSONB(), nullable=False),
        sa.Column("stopped_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "freq IN ('daily', 'every_n_days', 'weekly', 'monthly')", name="ck_task_series_freq"
        ),
        sa.CheckConstraint(
            "freq <> 'every_n_days' OR interval_days BETWEEN 2 AND 365",
            name="ck_task_series_interval",
        ),
        sa.CheckConstraint(
            "freq <> 'weekly' OR (weekdays IS NOT NULL AND cardinality(weekdays) >= 1 "
            "AND weekdays <@ ARRAY[1,2,3,4,5,6,7]::smallint[])",
            name="ck_task_series_weekdays",
        ),
        sa.CheckConstraint(
            "freq <> 'monthly' OR month_day BETWEEN 1 AND 31", name="ck_task_series_month_day"
        ),
        sa.CheckConstraint(
            "end_kind IN ('never', 'on_date', 'after_count')", name="ck_task_series_end_kind"
        ),
        sa.CheckConstraint(
            "end_kind <> 'on_date' OR end_date IS NOT NULL", name="ck_task_series_end_date"
        ),
        sa.CheckConstraint(
            "end_kind <> 'after_count' OR end_count BETWEEN 1 AND 999",
            name="ck_task_series_end_count",
        ),
    )
    op.add_column(
        "tasks",
        sa.Column(
            "series_id",
            sa.BigInteger(),
            sa.ForeignKey("task_series.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column("tasks", sa.Column("occurrence_no", sa.SmallInteger(), nullable=True))
    # Không có FK tự tham chiếu (xem models/task.py): tránh làm hỏng pg_restore --clean của bản cũ.
    op.add_column("tasks", sa.Column("spawned_from_task_id", sa.BigInteger(), nullable=True))
    op.add_column("tasks", sa.Column("trash_scope", sa.Text(), nullable=True))
    op.create_index("ix_tasks_series_id", "tasks", ["series_id"])
    op.create_index(
        "uq_tasks_series_current",
        "tasks",
        ["series_id"],
        unique=True,
        postgresql_where=sa.text(
            "series_id IS NOT NULL AND completed_at IS NULL AND deleted_at IS NULL"
        ),
    )
    op.create_check_constraint(
        "ck_tasks_series_not_auto", "tasks", "series_id IS NULL OR is_auto = false"
    )
    op.create_check_constraint(
        "ck_tasks_trash_scope",
        "tasks",
        "trash_scope IS NULL OR trash_scope IN ('this', 'following')",
    )


def downgrade():
    op.drop_constraint("ck_tasks_trash_scope", "tasks")
    op.drop_constraint("ck_tasks_series_not_auto", "tasks")
    op.drop_index("uq_tasks_series_current", "tasks")
    op.drop_index("ix_tasks_series_id", "tasks")
    op.drop_column("tasks", "trash_scope")
    op.drop_column("tasks", "spawned_from_task_id")
    op.drop_column("tasks", "occurrence_no")
    op.drop_column("tasks", "series_id")
    op.drop_table("task_series")
