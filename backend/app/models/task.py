from datetime import date, datetime, time

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
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

    list = relationship("TaskList", back_populates="tasks")
    source_session = relationship("ClassSession", back_populates="auto_task")
    tag_links = relationship(
        "TaskTag",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="TaskTag.position",
    )

    @property
    def tags(self):
        return [link.tag for link in self.tag_links]
