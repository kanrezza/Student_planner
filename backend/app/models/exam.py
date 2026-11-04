from datetime import date, datetime
from datetime import date as calendar_date  # cột `date` bên dưới che tên kiểu `date`

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Index,
    SmallInteger,
    Text,
    true,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import IdMixin, TimestampMixin


class Exam(IdMixin, TimestampMixin, db.Model):
    """Buổi thi: sự kiện một lần, độc lập với học kỳ và môn học (FR-055).

    Không có cột nào cho họ tên hay mã số sinh viên (FR-061).
    """

    __tablename__ = "exams"
    __table_args__ = (
        CheckConstraint("end_at > start_at", name="ck_exams_times"),
        CheckConstraint("attempt >= 1", name="ck_exams_attempt"),
        CheckConstraint("char_length(btrim(course_name)) BETWEEN 1 AND 200", name="ck_exams_name"),
        CheckConstraint(
            "reminder_offsets IS NULL OR 0 <= ALL(reminder_offsets)", name="ck_exams_reminders"
        ),
        Index("ix_exams_start_at", "start_at"),
    )

    course_code: Mapped[str | None] = mapped_column(Text)
    course_name: Mapped[str] = mapped_column(Text, nullable=False)
    attempt: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="1")
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    exam_format: Mapped[str | None] = mapped_column(Text)
    room: Mapped[str | None] = mapped_column(Text)
    candidate_number: Mapped[str | None] = mapped_column(Text)
    # NULL = theo mặc định; [] = tắt nhắc; mỗi phần tử là số phút báo trước.
    reminder_offsets: Mapped[list[int] | None] = mapped_column(ARRAY(SmallInteger))
    is_important: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())

    tag_links = relationship(
        "ExamTag",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ExamTag.position",
    )

    @property
    def tags(self):
        return [link.tag for link in self.tag_links]

    @property
    def local_date(self) -> calendar_date:
        return self.date
