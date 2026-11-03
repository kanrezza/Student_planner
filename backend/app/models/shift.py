from datetime import time

from sqlalchemy import CheckConstraint, SmallInteger, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.models.base import IdMixin, TimestampMixin


class Shift(IdMixin, TimestampMixin, db.Model):
    """Ca học cố định của trường (FR-038 đến FR-040)."""

    __tablename__ = "shifts"
    __table_args__ = (CheckConstraint("end_time > start_time", name="ck_shifts_times"),)

    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    position: Mapped[int] = mapped_column(SmallInteger, nullable=False, unique=True)
