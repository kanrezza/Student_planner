from datetime import datetime, time

from sqlalchemy import Boolean, CheckConstraint, DateTime, SmallInteger, Time, false, func
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class Period(db.Model):
    """Một tiết học: số tiết, giờ bắt đầu, giờ kết thúc (feature 004, FR-011).

    Tiết 1–12 suy từ 4 ca (ca k = tiết 3k−2…3k), tiết 16–18 mặc định 21:05–22:00. `is_manual = true`
    khi người dùng sửa tay: đổi giờ ca không ghi đè tiết này.
    """

    __tablename__ = "periods"
    __table_args__ = (
        CheckConstraint("number BETWEEN 1 AND 30", name="ck_periods_number"),
        CheckConstraint("end_time > start_time", name="ck_periods_times"),
    )

    number: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_manual: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
