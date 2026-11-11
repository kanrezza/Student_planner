"""Bảng Kanban: trạng thái, thứ tự và lọc thẻ (feature 005, research R2, R13).

"Xong" vẫn là `completed_at`; chuyển sang/rời Xong luôn đi qua `tasks.complete_task` /
`tasks.uncomplete_task` để có đúng hệ quả của tick (nhắc, đồng bộ, task lặp).
"""

from sqlalchemy import func, select

from app.extensions import db
from app.models import Task
from app.services.revision import bump_revision

STATUSES = ("todo", "doing", "done")


def _column_filter(status: str):
    base = [Task.deleted_at.is_(None)]
    if status == "done":
        return [*base, Task.completed_at.is_not(None)]
    return [*base, Task.completed_at.is_(None), Task.in_progress.is_(status == "doing")]


def top_rank(status: str, exclude_id: int | None = None) -> float:
    """Thứ tự để đặt một thẻ lên đầu cột `status`."""
    query = select(func.min(Task.board_rank)).where(*_column_filter(status))
    if exclude_id is not None:
        query = query.where(Task.id != exclude_id)
    lowest = db.session.scalar(query)
    return (lowest if lowest is not None else 1.0) - 1


def set_status(task_id: int, status: str) -> Task:
    """Đổi trạng thái (không chỉ vị trí), thẻ lên đầu cột đích. Xong = tick; rời Xong = bỏ tick."""
    from app.services import tasks as task_service  # tránh vòng phụ thuộc

    task = task_service.get_task(task_id)
    if status == "done":
        task, _ = task_service.complete_task(task_id)
        return task
    if task.completed_at is not None:
        task, _ = task_service.uncomplete_task(task_id)
    task.in_progress = status == "doing"
    task.board_rank = top_rank(status, exclude_id=task.id)
    bump_revision(db.session)
    db.session.commit()
    return task
