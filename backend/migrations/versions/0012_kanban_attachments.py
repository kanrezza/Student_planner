"""Bảng Kanban và file đính kèm (feature 005, data-model "Migration 0012").

Revision ID: 0012_kanban_attachments
Revises: 0011_periods_canonical_names
Create Date: 2026-11-11

- `tasks`: `in_progress`, `board_rank` (đánh số 1, 2, 3… theo thứ tự hiện có trong từng nhóm chưa
  xong / đã xong), `subject_id`.
- `settings`: giới hạn mỗi file (50 MB) và ngưỡng cảnh báo sao lưu (1024 MB).
- Bảng `attachment_blobs` và `attachments`.
"""

import sqlalchemy as sa
from alembic import op

revision = "0012_kanban_attachments"
down_revision = "0011_periods_canonical_names"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column("in_progress", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column(
        "tasks", sa.Column("board_rank", sa.Float(), server_default=sa.text("0"), nullable=False)
    )
    op.add_column(
        "tasks",
        sa.Column("subject_id", sa.BigInteger(), sa.ForeignKey("subjects.id", ondelete="SET NULL")),
    )
    op.create_index("ix_tasks_subject_id", "tasks", ["subject_id"])
    # Thứ tự ban đầu: theo hạn chót (task không hạn ở cuối), ưu tiên Cao → Thấp, id; task đã xong
    # theo thời điểm hoàn thành mới nhất trước.
    op.execute(
        """
        UPDATE tasks SET board_rank = ranked.rn FROM (
            SELECT id, row_number() OVER (
                PARTITION BY (completed_at IS NULL)
                ORDER BY
                    CASE WHEN completed_at IS NULL THEN 0 ELSE 1 END,
                    CASE WHEN completed_at IS NULL THEN (due_date IS NULL) END,
                    CASE WHEN completed_at IS NULL THEN due_date END,
                    CASE WHEN completed_at IS NULL THEN due_time END,
                    CASE WHEN completed_at IS NULL THEN priority END,
                    completed_at DESC NULLS LAST,
                    id
            ) AS rn FROM tasks
        ) AS ranked WHERE tasks.id = ranked.id
        """
    )
    op.create_index(
        "ix_tasks_board", "tasks", [sa.text("(completed_at IS NULL)"), "in_progress", "board_rank"]
    )

    op.add_column(
        "settings",
        sa.Column("attachment_max_mb", sa.SmallInteger(), server_default="50", nullable=False),
    )
    op.add_column(
        "settings",
        sa.Column(
            "backup_attachments_warn_mb", sa.Integer(), server_default="1024", nullable=False
        ),
    )
    op.create_check_constraint(
        "ck_settings_attachment_max", "settings", "attachment_max_mb BETWEEN 1 AND 500"
    )
    op.create_check_constraint(
        "ck_settings_attachment_warn",
        "settings",
        "backup_attachments_warn_mb BETWEEN 100 AND 1000000",
    )

    op.create_table(
        "attachment_blobs",
        sa.Column("sha256", sa.Text(), primary_key=True),
        sa.Column("size", sa.BigInteger(), nullable=False),
        sa.Column(
            "mime_type",
            sa.Text(),
            server_default=sa.text("'application/octet-stream'"),
            nullable=False,
        ),
        sa.Column("is_executable", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("sha256 ~ '^[0-9a-f]{64}$'", name="ck_attachment_blobs_sha"),
        sa.CheckConstraint("size >= 0", name="ck_attachment_blobs_size"),
    )
    op.create_table(
        "attachments",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "blob_sha256",
            sa.Text(),
            sa.ForeignKey("attachment_blobs.sha256", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("task_id", sa.BigInteger(), sa.ForeignKey("tasks.id", ondelete="CASCADE")),
        sa.Column("subject_id", sa.BigInteger(), sa.ForeignKey("subjects.id", ondelete="CASCADE")),
        sa.Column(
            "session_id", sa.BigInteger(), sa.ForeignKey("class_sessions.id", ondelete="CASCADE")
        ),
        sa.Column("exam_id", sa.BigInteger(), sa.ForeignKey("exams.id", ondelete="CASCADE")),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "num_nonnulls(task_id, subject_id, session_id, exam_id) = 1",
            name="ck_attachments_one_owner",
        ),
        sa.CheckConstraint(
            "char_length(display_name) BETWEEN 1 AND 255", name="ck_attachments_name_length"
        ),
    )
    for column in ("blob_sha256", "task_id", "subject_id", "session_id", "exam_id"):
        op.create_index(f"ix_attachments_{column}", "attachments", [column])
    op.execute("CREATE INDEX ix_attachments_vn_fold_name ON attachments (vn_fold(display_name))")


def downgrade() -> None:
    op.drop_table("attachments")
    op.drop_table("attachment_blobs")
    op.drop_constraint("ck_settings_attachment_warn", "settings", type_="check")
    op.drop_constraint("ck_settings_attachment_max", "settings", type_="check")
    op.drop_column("settings", "backup_attachments_warn_mb")
    op.drop_column("settings", "attachment_max_mb")
    op.drop_index("ix_tasks_board", table_name="tasks")
    op.drop_index("ix_tasks_subject_id", table_name="tasks")
    op.drop_column("tasks", "subject_id")
    op.drop_column("tasks", "board_rank")
    op.drop_column("tasks", "in_progress")
