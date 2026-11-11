from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class CanonicalSubjectName(db.Model):
    """Tên môn chuẩn lấy từ PDF thời khoá biểu, dùng để sửa tên khi nhập từ ảnh (feature 004,
    FR-028).

    Không có khoá ngoại tới `subjects`: tên vẫn còn khi môn bị xoá, cho đến khi người dùng xoá danh
    sách. Duy nhất theo `lower(name)` (khớp `ci_key`).
    """

    __tablename__ = "canonical_subject_names"
    __table_args__ = (
        CheckConstraint("char_length(name) BETWEEN 1 AND 200", name="ck_canonical_names_length"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    course_code: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


Index("uq_canonical_names_lower", func.lower(CanonicalSubjectName.name), unique=True)
