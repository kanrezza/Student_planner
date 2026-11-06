"""Sao lưu tự động (feature 003, data-model §1).

Ba bảng này KHÔNG đi theo bản sao lưu (research R9): khôi phục bản cũ không được đổi thư mục
đích / giờ sao lưu hay xoá việc đang chạy.
"""

from datetime import datetime, time

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    SmallInteger,
    Text,
    Time,
    func,
    text,
    true,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.models.base import IdMixin
from app.models.settings import _SingleRow

DESTINATION_STATES = ("ok", "missing", "no_permission", "icloud_off", "not_writable")
JOB_KINDS = ("backup_now", "restore")
JOB_STATES = ("pending", "running", "done", "failed")
ACTIVE_JOB_STATES = ("pending", "running")


class BackupConfig(_SingleRow, db.Model):
    """Cấu hình sao lưu (FR-001, FR-004, FR-006, FR-009)."""

    __tablename__ = "backup_config"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_backup_config_single_row"),
        CheckConstraint("retention_count BETWEEN 1 AND 365", name="ck_backup_config_retention"),
        CheckConstraint(
            "destination_path IS NULL OR destination_path LIKE '/%'",
            name="ck_backup_config_destination_absolute",
        ),
    )

    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())
    schedule_time: Mapped[time] = mapped_column(
        Time, nullable=False, server_default=text("'21:00'")
    )
    # NULL = thư mục mặc định trong iCloud Drive (agent tự suy ra đường dẫn).
    destination_path: Mapped[str | None] = mapped_column(Text)
    retention_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="14")
    enabled_since: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class BackupStatus(_SingleRow, db.Model):
    """Trạng thái do agent báo về qua PUT /backup/agent-report."""

    __tablename__ = "backup_status"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_backup_status_single_row"),
        CheckConstraint(
            "destination_state IN ('ok','missing','no_permission','icloud_off','not_writable')",
            name="ck_backup_status_destination_state",
        ),
    )

    destination_resolved: Mapped[str | None] = mapped_column(Text)
    destination_state: Mapped[str] = mapped_column(Text, nullable=False, server_default="ok")
    destination_message: Mapped[str | None] = mapped_column(Text)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_attempt_ok: Mapped[bool | None] = mapped_column(Boolean)
    last_attempt_error: Mapped[str | None] = mapped_column(Text)
    last_attempt_size: Mapped[int | None] = mapped_column(BigInteger)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_success_size: Mapped[int | None] = mapped_column(BigInteger)
    files: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    reported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class BackupJob(IdMixin, db.Model):
    """Việc giao cho agent (Sao lưu ngay / Khôi phục)."""

    __tablename__ = "backup_jobs"
    __table_args__ = (
        CheckConstraint("kind IN ('backup_now','restore')", name="ck_backup_jobs_kind"),
        CheckConstraint(
            "state IN ('pending','running','done','failed')", name="ck_backup_jobs_state"
        ),
        CheckConstraint(
            "kind <> 'restore' OR source_path IS NOT NULL", name="ck_backup_jobs_restore_source"
        ),
        # Tối đa một việc đang chờ/đang chạy: không chạy hai lần sao lưu chồng nhau (FR-010).
        Index(
            "uq_backup_jobs_one_active",
            text("(true)"),
            unique=True,
            postgresql_where=text("state IN ('pending','running')"),
        ),
    )

    kind: Mapped[str] = mapped_column(Text, nullable=False)
    source_path: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str] = mapped_column(Text, nullable=False, server_default="pending")
    step: Mapped[str | None] = mapped_column(Text)
    message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
