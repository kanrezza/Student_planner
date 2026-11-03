from datetime import date, time

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    SmallInteger,
    Text,
    Time,
    false,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import IdMixin, TimestampMixin


class Subject(IdMixin, TimestampMixin, db.Model):
    """Môn học: quy tắc lặp hàng tuần trong một học kỳ (FR-007 đến FR-015, FR-039).

    `weekdays`: 1 = Thứ Hai … 7 = Chủ Nhật; ≥ 1 phần tử. Việc không trùng phần tử được kiểm tra ở
    schema (pydantic) vì CHECK của PostgreSQL không diễn đạt gọn được.
    `reminder_minutes`: NULL = theo mặc định; -1 = tắt nhắc; ≥ 0 = số phút báo trước.
    """

    __tablename__ = "subjects"
    __table_args__ = (
        CheckConstraint("char_length(name) BETWEEN 1 AND 200", name="ck_subjects_name_length"),
        CheckConstraint(
            "cardinality(weekdays) >= 1 AND weekdays <@ ARRAY[1,2,3,4,5,6,7]::smallint[]",
            name="ck_subjects_weekdays",
        ),
        CheckConstraint(
            "(start_shift_id IS NULL) = (end_shift_id IS NULL)", name="ck_subjects_shift_pair"
        ),
        CheckConstraint("end_time > start_time", name="ck_subjects_times"),
        CheckConstraint("end_date >= start_date", name="ck_subjects_dates"),
        CheckConstraint(
            "reminder_minutes IS NULL OR reminder_minutes >= -1", name="ck_subjects_reminder"
        ),
    )

    semester_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("semesters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    class_code: Mapped[str | None] = mapped_column(Text)
    lecturer: Mapped[str | None] = mapped_column(Text)
    room: Mapped[str | None] = mapped_column(Text)
    color: Mapped[str] = mapped_column(Text, nullable=False)
    weekdays: Mapped[list[int]] = mapped_column(ARRAY(SmallInteger), nullable=False)
    start_shift_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("shifts.id", ondelete="SET NULL")
    )
    end_shift_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("shifts.id", ondelete="SET NULL")
    )
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    reminder_minutes: Mapped[int | None] = mapped_column(Integer)
    is_important: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())

    semester = relationship("Semester", back_populates="subjects")
    sessions = relationship(
        "ClassSession",
        back_populates="subject",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ClassSession.start_at",
    )
    start_shift = relationship("Shift", foreign_keys=[start_shift_id])
    end_shift = relationship("Shift", foreign_keys=[end_shift_id])
    tag_links = relationship(
        "SubjectTag",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SubjectTag.position",
    )

    @property
    def tags(self):
        return [link.tag for link in self.tag_links]
