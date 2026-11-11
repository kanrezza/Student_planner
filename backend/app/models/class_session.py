from datetime import date, datetime
from datetime import date as calendar_date  # cột `date` bên dưới che tên kiểu `date`

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint,
    false,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import IdMixin, TimestampMixin


class ClassSession(IdMixin, TimestampMixin, db.Model):
    """Một buổi học cụ thể, được sinh sẵn từ môn học (research R8).

    Buổi có `is_cancelled`, `time_overridden`, `room_overridden` hoặc `original_date` (đã dời) là
    buổi có ngoại lệ và được giữ nguyên khi môn học thay đổi (FR-013, feature 002 FR-028).
    """

    __tablename__ = "class_sessions"
    __table_args__ = (
        CheckConstraint("end_at > start_at", name="ck_class_sessions_times"),
        UniqueConstraint("subject_id", "date", "start_at", name="uq_class_sessions_slot"),
    )

    subject_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    room: Mapped[str | None] = mapped_column(Text)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())
    time_overridden: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())
    room_overridden: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())
    auto_task_suppressed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=false()
    )
    # NULL = theo môn; True/False = đặt riêng buổi này (FR-067).
    important_override: Mapped[bool | None] = mapped_column(Boolean)
    # Ngày gốc khi buổi được dời sang ngày khác (feature 002 FR-028); NULL = chưa dời.
    original_date: Mapped[calendar_date | None] = mapped_column(Date)

    schedule_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("subject_schedules.id", ondelete="SET NULL"), index=True
    )

    subject = relationship("Subject", back_populates="sessions")
    schedule = relationship("SubjectSchedule", foreign_keys=[schedule_id])
    tag_links = relationship(
        "SessionTag",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SessionTag.position",
    )
    auto_task = relationship("Task", back_populates="source_session", uselist=False)

    @property
    def has_exception(self) -> bool:
        return (
            self.is_cancelled
            or self.time_overridden
            or self.room_overridden
            or self.original_date is not None
        )

    @property
    def is_moved(self) -> bool:
        return self.original_date is not None

    @property
    def is_important(self) -> bool:
        if self.important_override is not None:
            return self.important_override
        return self.subject.is_important

    @property
    def effective_tags(self):
        """Nhãn của môn trước, rồi nhãn riêng của buổi (data-model.md)."""
        seen, result = set(), []
        for tag in [*self.subject.tags, *(link.tag for link in self.tag_links)]:
            if tag.id not in seen:
                seen.add(tag.id)
                result.append(tag)
        return result
