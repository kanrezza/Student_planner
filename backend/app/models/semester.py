from datetime import date

from sqlalchemy import CheckConstraint, Date, Text, literal_column
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import IdMixin, TimestampMixin


class Semester(IdMixin, TimestampMixin, db.Model):
    """Học kỳ (FR-036, FR-037). Các học kỳ không được chồng lấn ngày."""

    __tablename__ = "semesters"
    __table_args__ = (
        CheckConstraint("char_length(name) BETWEEN 1 AND 100", name="ck_semesters_name_length"),
        CheckConstraint("end_date >= start_date", name="ck_semesters_dates"),
        ExcludeConstraint(
            (literal_column("daterange(start_date, end_date, '[]')"), "&&"),
            name="ex_semesters_no_overlap",
            using="gist",
        ),
    )

    name: Mapped[str] = mapped_column(Text, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    subjects = relationship(
        "Subject", back_populates="semester", cascade="all, delete-orphan", passive_deletes=True
    )
