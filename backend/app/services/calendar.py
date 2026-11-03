"""Dữ liệu cho lịch ngày/tuần/tháng (FR-016, FR-017) và lọc theo nhãn (FR-045)."""

from datetime import date

from sqlalchemy import or_, select

from app.extensions import db
from app.models import ClassSession, SessionTag, SubjectTag, Task, TaskTag

MAX_RANGE_DAYS = 62  # đủ cho chế độ xem tháng (tối đa 6 tuần) kèm phần đệm


def sessions_in_range(start: date, end: date, tag_ids: list[int]) -> list[ClassSession]:
    """Buổi học trong [start, end], kể cả buổi đã huỷ (hiển thị khác biệt ở giao diện)."""
    query = select(ClassSession).where(ClassSession.date.between(start, end))
    if tag_ids:
        query = query.where(
            or_(
                ClassSession.subject_id.in_(
                    select(SubjectTag.subject_id).where(SubjectTag.tag_id.in_(tag_ids))
                ),
                ClassSession.id.in_(
                    select(SessionTag.session_id).where(SessionTag.tag_id.in_(tag_ids))
                ),
            )
        )
    return list(db.session.scalars(query.order_by(ClassSession.start_at)))


def tasks_in_range(start: date, end: date, tag_ids: list[int]) -> list[Task]:
    """Task có hạn chót trong [start, end]; task không có hạn chót không hiện trên lịch."""
    query = select(Task).where(Task.due_date.between(start, end))
    if tag_ids:
        query = query.where(Task.id.in_(select(TaskTag.task_id).where(TaskTag.tag_id.in_(tag_ids))))
    return list(db.session.scalars(query.order_by(Task.due_date, Task.due_time)))
