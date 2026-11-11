"""Bảng Kanban: trạng thái, thứ tự và lọc thẻ (feature 005, research R2, R13).

"Xong" vẫn là `completed_at`; chuyển sang/rời Xong luôn đi qua `tasks.complete_task` /
`tasks.uncomplete_task` để có đúng hệ quả của tick (nhắc, đồng bộ, task lặp).
"""

from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import func, select

from app.api.errors import ApiError
from app.extensions import db
from app.models import ClassSession, Task
from app.services import tasks as task_service
from app.services.board_rank import (
    done_window_start,
    needs_rebalance,
    rank_between,
    rebalance,
    task_status,
)
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


# ---- Đọc bảng -----------------------------------------------------------------------------------


@dataclass
class BoardFilters:
    list_ids: list[int] = field(default_factory=list)
    tag_ids: list[int] = field(default_factory=list)
    subject_ids: list[int] = field(default_factory=list)


def _filtered(filters: BoardFilters):
    """Task đang dùng (không ở Thùng rác) khớp bộ lọc; các loại lọc kết hợp bằng "và" (FR-011)."""
    query = (
        select(Task)
        .outerjoin(ClassSession, Task.source_session_id == ClassSession.id)
        .where(Task.deleted_at.is_(None))
    )
    if filters.list_ids:
        query = query.where(Task.list_id.in_(filters.list_ids))
    if filters.tag_ids:
        query = query.where(task_service._has_any_tag(filters.tag_ids))
    if filters.subject_ids:
        effective = func.coalesce(Task.subject_id, ClassSession.subject_id)
        query = query.where(effective.in_(filters.subject_ids))
    return query


def board(filters: BoardFilters, done_window: str, now: datetime) -> dict:
    """Ba cột đã sắp theo `board_rank`; cột Xong mặc định chỉ từ 7 ngày gần nhất (FR-010)."""
    columns: dict[str, list[Task]] = {"todo": [], "doing": [], "done": []}
    hidden = 0
    since = done_window_start(now) if done_window == "7d" else None
    for task in db.session.scalars(_filtered(filters)):
        status = task_status(task.completed_at, task.in_progress)
        if status == "done" and since is not None and task.completed_at < since:
            hidden += 1
            continue
        columns[status].append(task)
    for tasks in columns.values():
        tasks.sort(key=lambda t: (t.board_rank, t.id))
    return {"columns": columns, "done_hidden_count": hidden}


# ---- Chuyển thẻ ---------------------------------------------------------------------------------


def _fail(field_name: str, message: str) -> ApiError:
    return ApiError(400, "validation_error", "Dữ liệu chưa hợp lệ", {field_name: message})


def _column_tasks(status: str, exclude_id: int) -> list[Task]:
    tasks = db.session.scalars(
        select(Task).where(*_column_filter(status), Task.id != exclude_id)
    ).all()
    return sorted(tasks, key=lambda t: (t.board_rank, t.id))


def _neighbour(task_id: int | None, status: str, task: Task, name: str) -> Task | None:
    if task_id is None:
        return None
    if task_id == task.id:
        raise _fail(name, "Thẻ kề không được là chính thẻ đang chuyển")
    other = db.session.get(Task, task_id)
    if (
        other is None
        or other.deleted_at is not None
        or task_status(other.completed_at, other.in_progress) != status
    ):
        raise _fail(name, "Thẻ kề không nằm trong cột đích")
    return other


def _neighbours_of(task: Task, status: str) -> tuple[int | None, int | None]:
    """Thẻ ngay trên và ngay dưới `task` trong cột `status` (để hoàn tác)."""
    column = sorted(
        db.session.scalars(select(Task).where(*_column_filter(status))).all(),
        key=lambda t: (t.board_rank, t.id),
    )
    index = next((i for i, t in enumerate(column) if t.id == task.id), None)
    if index is None:
        return None, None
    above = column[index - 1].id if index > 0 else None
    below = column[index + 1].id if index + 1 < len(column) else None
    return above, below


def move(task_id: int, status: str, before_id: int | None, after_id: int | None) -> dict:
    """Chuyển thẻ sang cột `status`, chèn giữa `before_id` (ngay trên) và `after_id` (ngay dưới).

    Sang Xong = `complete_task`, rời Xong = `uncomplete_task` (cùng hệ quả với tick). Trả
    `{task, next_task, undo}`; `undo` đủ để chuyển ngược lại đúng cột và vị trí cũ.
    """
    if status not in STATUSES:
        raise _fail("status", "Trạng thái không hợp lệ")
    task = task_service.get_task(task_id)
    before_card = _neighbour(before_id, status, task, "before_id")
    after_card = _neighbour(after_id, status, task, "after_id")
    old_status = task_status(task.completed_at, task.in_progress)
    above, below = _neighbours_of(task, old_status)
    undo = {"status": old_status, "before_id": above, "after_id": below}

    next_task = None
    if status == "done" and old_status != "done":
        task, next_task = task_service.complete_task(task_id)
    elif status != "done" and old_status == "done":
        task, _ = task_service.uncomplete_task(task_id)
    task.in_progress = status == "doing"
    _place(task, status, before_card, after_card)
    bump_revision(db.session)
    db.session.commit()
    return {"task": task, "next_task": next_task, "undo": undo}


def _place(task: Task, status: str, before_card: Task | None, after_card: Task | None) -> None:
    others = _column_tasks(status, task.id)
    if before_card is None and after_card is None:
        index = 0
    elif before_card is not None:
        index = next(i for i, t in enumerate(others) if t.id == before_card.id) + 1
    else:
        index = next(i for i, t in enumerate(others) if t.id == after_card.id)
    above = others[index - 1].board_rank if index > 0 else None
    below = others[index].board_rank if index < len(others) else None
    task.board_rank = rank_between(above, below)
    ranks = [t.board_rank for t in others[:index]] + [task.board_rank]
    ranks += [t.board_rank for t in others[index:]]
    if needs_rebalance(ranks):
        ordered = [*others[:index], task, *others[index:]]
        for card, rank in zip(ordered, rebalance(ranks), strict=True):
            card.board_rank = rank
