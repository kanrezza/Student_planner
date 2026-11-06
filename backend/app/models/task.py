from datetime import date, datetime, time

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    Text,
    Time,
    false,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import IdMixin, TimestampMixin


class Task(IdMixin, TimestampMixin, db.Model):
    """Công việc (FR-001 đến FR-006); task tự tạo có `is_auto` và `source_session_id` (FR-047)."""

    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            "char_length(btrim(title)) BETWEEN 1 AND 300", name="ck_tasks_title_length"
        ),
        CheckConstraint("due_time IS NULL OR due_date IS NOT NULL", name="ck_tasks_due_time"),
        CheckConstraint("priority IN (1, 2, 3)", name="ck_tasks_priority"),
        CheckConstraint(
            "reminder_minutes IS NULL OR reminder_minutes >= -1", name="ck_tasks_reminder"
        ),
        CheckConstraint(
            "(work_date IS NULL) = (work_start IS NULL) "
            "AND (work_date IS NULL) = (work_end IS NULL)",
            name="ck_tasks_work_window_complete",
        ),
        CheckConstraint(
            "work_end IS NULL OR work_end > work_start", name="ck_tasks_work_window_order"
        ),
        Index("ix_tasks_deleted_at", "deleted_at", postgresql_where=text("deleted_at IS NOT NULL")),
        # Task lặp (feature 003): CHECK khớp migration 0008.
        CheckConstraint("series_id IS NULL OR is_auto = false", name="ck_tasks_series_not_auto"),
        CheckConstraint(
            "trash_scope IS NULL OR trash_scope IN ('this', 'following')",
            name="ck_tasks_trash_scope",
        ),
        # Đúng một lần hiện tại mỗi chuỗi.
        Index(
            "uq_tasks_series_current",
            "series_id",
            unique=True,
            postgresql_where=text(
                "series_id IS NOT NULL AND completed_at IS NULL AND deleted_at IS NULL"
            ),
        ),
    )

    list_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("task_lists.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    due_date: Mapped[date | None] = mapped_column(Date, index=True)
    due_time: Mapped[time | None] = mapped_column(Time)
    priority: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("2"))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reminder_minutes: Mapped[int | None] = mapped_column(Integer)
    source_session_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("class_sessions.id", ondelete="SET NULL"), unique=True
    )
    is_auto: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())
    user_modified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())
    is_important: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())
    # Khung giờ làm (feature 002 FR-018): cả ba cùng có hoặc cùng trống, trong một ngày.
    work_date: Mapped[date | None] = mapped_column(Date, index=True)
    work_start: Mapped[time | None] = mapped_column(Time)
    work_end: Mapped[time | None] = mapped_column(Time)
    # Thùng rác (feature 002 FR-030): NULL = đang dùng.
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    trashed_from_list_name: Mapped[str | None] = mapped_column(Text)
    # Task lặp (feature 003 US3, data-model §4).
    series_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("task_series.id", ondelete="SET NULL"), index=True
    )
    occurrence_no: Mapped[int | None] = mapped_column(SmallInteger)
    # Không có FK tự tham chiếu: nó chặn `pg_restore --clean` khi khôi phục bản sao lưu cũ hơn
    # (constraint phụ thuộc tasks_pkey mà bản cũ không biết). id không bao giờ được dùng lại.
    spawned_from_task_id: Mapped[int | None] = mapped_column(BigInteger)
    trash_scope: Mapped[str | None] = mapped_column(Text)

    list = relationship("TaskList", back_populates="tasks")
    source_session = relationship("ClassSession", back_populates="auto_task")
    series = relationship("TaskSeries", foreign_keys=[series_id])
    tag_links = relationship(
        "TaskTag",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="TaskTag.position",
    )

    @property
    def tags(self):
        return [link.tag for link in self.tag_links]
