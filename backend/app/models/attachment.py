from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Text,
    false,
    func,
    select,
    text,
)
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from app.extensions import db


class AttachmentBlob(db.Model):
    """Nội dung một file (một bản duy nhất cho mỗi nội dung), nhận biết theo SHA-256 (feature 005).

    File thật nằm trong volume `lichhoc_attachments` tại `<sha[0:2]>/<sha>`. Dòng này chỉ được tạo
    sau khi file đã ghi xuống đĩa (research R4); bị xoá cùng file khi không còn mục đính kèm nào.
    """

    __tablename__ = "attachment_blobs"
    __table_args__ = (
        CheckConstraint("sha256 ~ '^[0-9a-f]{64}$'", name="ck_attachment_blobs_sha"),
        CheckConstraint("size >= 0", name="ck_attachment_blobs_size"),
    )

    sha256: Mapped[str] = mapped_column(Text, primary_key=True)
    size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'application/octet-stream'")
    )
    is_executable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Attachment(db.Model):
    """Một lần gắn file vào đúng một nơi: task, môn học, buổi học hoặc buổi thi."""

    __tablename__ = "attachments"
    __table_args__ = (
        CheckConstraint(
            "num_nonnulls(task_id, subject_id, session_id, exam_id) = 1",
            name="ck_attachments_one_owner",
        ),
        CheckConstraint(
            "char_length(display_name) BETWEEN 1 AND 255", name="ck_attachments_name_length"
        ),
        Index("ix_attachments_vn_fold_name", text("vn_fold(display_name)")),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    blob_sha256: Mapped[str] = mapped_column(
        Text, ForeignKey("attachment_blobs.sha256", ondelete="RESTRICT"), nullable=False, index=True
    )
    task_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("tasks.id", ondelete="CASCADE"), index=True
    )
    subject_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("subjects.id", ondelete="CASCADE"), index=True
    )
    session_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("class_sessions.id", ondelete="CASCADE"), index=True
    )
    exam_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("exams.id", ondelete="CASCADE"), index=True
    )
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    blob = relationship("AttachmentBlob")


def _count_for(owner_column, owner_id_column):
    return (
        select(func.count(Attachment.id))
        .where(owner_column == owner_id_column)
        .correlate_except(Attachment)
        .scalar_subquery()
    )


def register_attachment_counts() -> None:
    """Số mục đính kèm của task/môn/buổi học/buổi thi, nạp cùng truy vấn chính (không N+1).

    Gọi sau khi mọi model đã định nghĩa (cuối `app/models/__init__.py`).
    """
    from app.models.class_session import ClassSession
    from app.models.exam import Exam
    from app.models.subject import Subject
    from app.models.task import Task

    for model, column in (
        (Task, Attachment.task_id),
        (Subject, Attachment.subject_id),
        (ClassSession, Attachment.session_id),
        (Exam, Attachment.exam_id),
    ):
        model.attachment_total = column_property(_count_for(column, model.id), deferred=False)
