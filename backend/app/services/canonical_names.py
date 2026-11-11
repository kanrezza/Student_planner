"""Tên môn chuẩn lấy từ PDF thời khoá biểu, dùng sửa tên khi nhập từ ảnh (feature 004, FR-028)."""

from sqlalchemy import delete, func, select

from app.extensions import db
from app.lib.text import ci_key
from app.models import CanonicalSubjectName


def list_names() -> list[CanonicalSubjectName]:
    return list(
        db.session.scalars(select(CanonicalSubjectName).order_by(CanonicalSubjectName.created_at))
    )


def names() -> list[str]:
    return [n.name for n in list_names()]


def record(entries: list[tuple[str, str | None]]) -> None:
    """Ghi các (tên, mã HP) chưa có (duy nhất theo `lower(name)`); không commit."""
    seen = {ci_key(n) for n in names()}
    for name, course_code in entries:
        key = ci_key(name)
        if not key or key in seen or len(name) > 200:
            continue
        seen.add(key)
        db.session.add(CanonicalSubjectName(name=name, course_code=course_code))
    db.session.flush()


def clear() -> int:
    count = db.session.scalar(select(func.count()).select_from(CanonicalSubjectName)) or 0
    db.session.execute(delete(CanonicalSubjectName))
    db.session.commit()
    return count
