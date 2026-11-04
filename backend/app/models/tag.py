from sqlalchemy import BigInteger, ForeignKey, Index, SmallInteger, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import IdMixin, TimestampMixin


class Tag(IdMixin, TimestampMixin, db.Model):
    """Nhãn có màu (FR-042). Nhãn có `system_key` (ví dụ 'e_learning') không xoá/đổi tên được."""

    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(Text, nullable=False)
    color: Mapped[str] = mapped_column(Text, nullable=False)
    system_key: Mapped[str | None] = mapped_column(Text, unique=True)


Index("uq_tags_name_ci", func.lower(Tag.name), unique=True)


class _TagLinkMixin:
    """`position` giữ thứ tự gắn: nhãn gắn đầu tiên quyết định màu hiển thị (FR-044)."""

    tag_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )
    position: Mapped[int] = mapped_column(SmallInteger, nullable=False)


class SubjectTag(_TagLinkMixin, db.Model):
    __tablename__ = "subject_tags"

    subject_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("subjects.id", ondelete="CASCADE"), primary_key=True
    )
    tag = relationship("Tag", lazy="joined")


class SessionTag(_TagLinkMixin, db.Model):
    __tablename__ = "session_tags"

    session_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("class_sessions.id", ondelete="CASCADE"), primary_key=True
    )
    tag = relationship("Tag", lazy="joined")


class TaskTag(_TagLinkMixin, db.Model):
    __tablename__ = "task_tags"

    task_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True
    )
    tag = relationship("Tag", lazy="joined")


class ExamTag(_TagLinkMixin, db.Model):
    __tablename__ = "exam_tags"

    exam_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("exams.id", ondelete="CASCADE"), primary_key=True
    )
    tag = relationship("Tag", lazy="joined")
