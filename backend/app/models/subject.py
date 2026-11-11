from datetime import date

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    SmallInteger,
    Text,
    false,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import IdMixin, TimestampMixin


class Subject(IdMixin, TimestampMixin, db.Model):
    """Môn học (lớp học phần) trong một học kỳ (FR-007 đến FR-015, FR-039; feature 004).

    Lịch học nằm ở các quy tắc lặp `schedules` (≥ 1), mỗi quy tắc có thứ, khoảng ngày, giờ/ca và
    phòng.
    `reminder_minutes`: NULL = theo mặc định; -1 = tắt nhắc; ≥ 0 = số phút báo trước.
    """

    __tablename__ = "subjects"
    __table_args__ = (
        CheckConstraint("char_length(name) BETWEEN 1 AND 200", name="ck_subjects_name_length"),
        CheckConstraint(
            "reminder_minutes IS NULL OR reminder_minutes >= -1", name="ck_subjects_reminder"
        ),
        CheckConstraint("credits IS NULL OR credits BETWEEN 0 AND 30", name="ck_subjects_credits"),
    )

    semester_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("semesters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    class_code: Mapped[str | None] = mapped_column(Text)
    course_code: Mapped[str | None] = mapped_column(Text)
    credits: Mapped[int | None] = mapped_column(SmallInteger)
    lecturer: Mapped[str | None] = mapped_column(Text)
    color: Mapped[str] = mapped_column(Text, nullable=False)
    reminder_minutes: Mapped[int | None] = mapped_column(Integer)
    is_important: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())

    semester = relationship("Semester", back_populates="subjects")
    schedules = relationship(
        "SubjectSchedule",
        back_populates="subject",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SubjectSchedule.position",
    )
    sessions = relationship(
        "ClassSession",
        back_populates="subject",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ClassSession.start_at",
    )
    tag_links = relationship(
        "SubjectTag",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SubjectTag.position",
    )

    @property
    def tags(self):
        return [link.tag for link in self.tag_links]

    @property
    def date_span(self) -> tuple[date, date] | None:
        """Ngày sớm nhất và muộn nhất của các quy tắc; None khi chưa có quy tắc."""
        if not self.schedules:
            return None
        return (
            min(rule.start_date for rule in self.schedules),
            max(rule.end_date for rule in self.schedules),
        )
