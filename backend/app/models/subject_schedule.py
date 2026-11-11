from datetime import date, time

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    ForeignKey,
    SmallInteger,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import IdMixin, TimestampMixin


class SubjectSchedule(IdMixin, TimestampMixin, db.Model):
    """Một quy tắc lặp hằng tuần của môn: thứ, khoảng ngày, giờ (hoặc ca) và phòng (feature 004,
    FR-020).

    Một môn có ≥ 1 quy tắc (kiểm tra ở service). `weekdays`: 1 = Thứ Hai … 7 = Chủ Nhật, không trùng
    phần tử (kiểm tra ở schema pydantic). `period_from`/`period_to`: khoảng tiết gốc từ PDF, chỉ để
    hiển thị "Tiết 1–2"; giờ thật luôn nằm ở `start_time`/`end_time`.
    """

    __tablename__ = "subject_schedules"
    __table_args__ = (
        UniqueConstraint("subject_id", "position", name="uq_subject_schedules_position"),
        CheckConstraint("position >= 0", name="ck_subject_schedules_position"),
        CheckConstraint(
            "cardinality(weekdays) >= 1 AND weekdays <@ ARRAY[1,2,3,4,5,6,7]::smallint[]",
            name="ck_subject_schedules_weekdays",
        ),
        CheckConstraint("end_date >= start_date", name="ck_subject_schedules_dates"),
        CheckConstraint("end_time > start_time", name="ck_subject_schedules_times"),
        CheckConstraint(
            "(start_shift_id IS NULL) = (end_shift_id IS NULL)",
            name="ck_subject_schedules_shift_pair",
        ),
        CheckConstraint(
            "(period_from IS NULL) = (period_to IS NULL) AND "
            "(period_from IS NULL OR (period_from >= 1 AND period_from <= period_to "
            "AND period_to <= 30))",
            name="ck_subject_schedules_periods",
        ),
    )

    subject_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    weekdays: Mapped[list[int]] = mapped_column(ARRAY(SmallInteger), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_shift_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("shifts.id", ondelete="SET NULL")
    )
    end_shift_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("shifts.id", ondelete="SET NULL")
    )
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    period_from: Mapped[int | None] = mapped_column(SmallInteger)
    period_to: Mapped[int | None] = mapped_column(SmallInteger)
    room: Mapped[str | None] = mapped_column(Text)

    subject = relationship("Subject", back_populates="schedules")
    start_shift = relationship("Shift", foreign_keys=[start_shift_id])
    end_shift = relationship("Shift", foreign_keys=[end_shift_id])
