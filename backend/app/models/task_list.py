from sqlalchemy import Boolean, CheckConstraint, Index, Text, false, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import IdMixin, TimestampMixin


class TaskList(IdMixin, TimestampMixin, db.Model):
    """Danh sách task (FR-004). Đúng một danh sách là "Học tập" (`is_default_study`)."""

    __tablename__ = "task_lists"
    __table_args__ = (
        CheckConstraint("emoji IS NULL OR octet_length(emoji) <= 64", name="ck_task_lists_emoji"),
    )

    name: Mapped[str] = mapped_column(Text, nullable=False)
    color: Mapped[str] = mapped_column(Text, nullable=False)
    is_default_study: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())
    emoji: Mapped[str | None] = mapped_column(Text)  # đúng một emoji (feature 002 FR-015)

    tasks = relationship("Task", back_populates="list", passive_deletes=True)


Index("uq_task_lists_name_ci", func.lower(TaskList.name), unique=True)
Index(
    "uq_task_lists_default_study",
    TaskList.is_default_study,
    unique=True,
    postgresql_where=text("is_default_study"),
)
