"""Sao lưu tự động: backup_config, backup_status, backup_jobs (feature 003 US1, data-model §1).

Idempotent (bỏ qua bảng đã có): khi khôi phục một bản sao lưu cũ hơn, ba bảng này không bị đụng tới
(research R8/R9) nên migration có thể chạy lại trên database đã có sẵn chúng.

Revision ID: 0006_backup
Revises: 0005_exams
Create Date: 2026-11-05
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0006_backup"
down_revision = "0005_exams"
branch_labels = None
depends_on = None


def _missing(name: str) -> bool:
    return not sa.inspect(op.get_bind()).has_table(name)


def upgrade():
    if _missing("backup_config"):
        op.create_table(
            "backup_config",
            sa.Column("id", sa.SmallInteger(), primary_key=True, server_default=sa.text("1")),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column(
                "schedule_time", sa.Time(), nullable=False, server_default=sa.text("'21:00'")
            ),
            sa.Column("destination_path", sa.Text()),
            sa.Column("retention_count", sa.SmallInteger(), nullable=False, server_default="14"),
            sa.Column(
                "enabled_since",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.CheckConstraint("id = 1", name="ck_backup_config_single_row"),
            sa.CheckConstraint(
                "retention_count BETWEEN 1 AND 365", name="ck_backup_config_retention"
            ),
            sa.CheckConstraint(
                "destination_path IS NULL OR destination_path LIKE '/%'",
                name="ck_backup_config_destination_absolute",
            ),
        )
    op.execute("INSERT INTO backup_config (id) VALUES (1) ON CONFLICT (id) DO NOTHING")

    if _missing("backup_status"):
        op.create_table(
            "backup_status",
            sa.Column("id", sa.SmallInteger(), primary_key=True, server_default=sa.text("1")),
            sa.Column("destination_resolved", sa.Text()),
            sa.Column("destination_state", sa.Text(), nullable=False, server_default="ok"),
            sa.Column("destination_message", sa.Text()),
            sa.Column("last_attempt_at", sa.DateTime(timezone=True)),
            sa.Column("last_attempt_ok", sa.Boolean()),
            sa.Column("last_attempt_error", sa.Text()),
            sa.Column("last_attempt_size", sa.BigInteger()),
            sa.Column("last_success_at", sa.DateTime(timezone=True)),
            sa.Column("last_success_size", sa.BigInteger()),
            sa.Column(
                "files",
                postgresql.JSONB(),
                nullable=False,
                server_default=sa.text("'[]'::jsonb"),
            ),
            sa.Column("reported_at", sa.DateTime(timezone=True)),
            sa.CheckConstraint("id = 1", name="ck_backup_status_single_row"),
            sa.CheckConstraint(
                "destination_state IN ('ok','missing','no_permission','icloud_off','not_writable')",
                name="ck_backup_status_destination_state",
            ),
        )
    op.execute("INSERT INTO backup_status (id) VALUES (1) ON CONFLICT (id) DO NOTHING")

    if _missing("backup_jobs"):
        op.create_table(
            "backup_jobs",
            sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column("kind", sa.Text(), nullable=False),
            sa.Column("source_path", sa.Text()),
            sa.Column("state", sa.Text(), nullable=False, server_default="pending"),
            sa.Column("step", sa.Text()),
            sa.Column("message", sa.Text()),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column("started_at", sa.DateTime(timezone=True)),
            sa.Column("finished_at", sa.DateTime(timezone=True)),
            sa.CheckConstraint("kind IN ('backup_now','restore')", name="ck_backup_jobs_kind"),
            sa.CheckConstraint(
                "state IN ('pending','running','done','failed')", name="ck_backup_jobs_state"
            ),
            sa.CheckConstraint(
                "kind <> 'restore' OR source_path IS NOT NULL",
                name="ck_backup_jobs_restore_source",
            ),
        )
        op.execute(
            "CREATE UNIQUE INDEX uq_backup_jobs_one_active ON backup_jobs ((true)) "
            "WHERE state IN ('pending','running')"
        )


def downgrade():
    op.drop_table("backup_jobs")
    op.drop_table("backup_status")
    op.drop_table("backup_config")
