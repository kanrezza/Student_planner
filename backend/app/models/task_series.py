from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, SmallInteger, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.models.base import IdMixin, TimestampMixin


class TaskSeries(IdMixin, TimestampMixin, db.Model):
    """Chuỗi task lặp: quy tắc + mẫu để sinh lần kế tiếp (feature 003 data-model §4)."""

    __tablename__ = "task_series"
    __table_args__ = (
        CheckConstraint(
            "freq IN ('daily', 'every_n_days', 'weekly', 'monthly')", name="ck_task_series_freq"
        ),
        CheckConstraint(
            "freq <> 'every_n_days' OR interval_days BETWEEN 2 AND 365",
            name="ck_task_series_interval",
        ),
        CheckConstraint(
            "freq <> 'weekly' OR (weekdays IS NOT NULL AND cardinality(weekdays) >= 1 "
            "AND weekdays <@ ARRAY[1,2,3,4,5,6,7]::smallint[])",
            name="ck_task_series_weekdays",
        ),
        CheckConstraint(
            "freq <> 'monthly' OR month_day BETWEEN 1 AND 31", name="ck_task_series_month_day"
        ),
        CheckConstraint(
            "end_kind IN ('never', 'on_date', 'after_count')", name="ck_task_series_end_kind"
        ),
        CheckConstraint(
            "end_kind <> 'on_date' OR end_date IS NOT NULL", name="ck_task_series_end_date"
        ),
        CheckConstraint(
            "end_kind <> 'after_count' OR end_count BETWEEN 1 AND 999",
            name="ck_task_series_end_count",
        ),
    )

    freq: Mapped[str] = mapped_column(Text, nullable=False)
    interval_days: Mapped[int | None] = mapped_column(SmallInteger)
    weekdays: Mapped[list[int] | None] = mapped_column(ARRAY(SmallInteger))
    month_day: Mapped[int | None] = mapped_column(SmallInteger)
    anchor_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_kind: Mapped[str] = mapped_column(Text, nullable=False, server_default="never")
    end_date: Mapped[date | None] = mapped_column(Date)
    end_count: Mapped[int | None] = mapped_column(SmallInteger)
    occurrences_created: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default="1"
    )
    template: Mapped[dict] = mapped_column(JSONB, nullable=False)
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
