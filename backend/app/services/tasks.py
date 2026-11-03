"""Nghiệp vụ task (FR-001 đến FR-006). Hàm thuần ở đầu file; hàm ghi dữ liệu gọi `bump_revision`."""

from datetime import date, datetime, time

from sqlalchemy import select

from app.api.errors import ApiError, not_found
from app.extensions import db
from app.lib import timeutil
from app.lib.timeutil import combine
from app.models import ClassSession, Task, TaskList, TaskTag
from app.services.revision import bump_revision
from app.services.tag_links import replace_tag_links

END_OF_DAY = time(23, 59)
DUE_TIME_NEEDS_DATE = "Cần chọn ngày hạn chót trước khi đặt giờ"
REQUIRED = "Trường này là bắt buộc"


# ---- Hàm thuần ------------------------------------------------------------------------------


def due_at(task) -> datetime | None:
    """Hạn chót = ngày + giờ; task chỉ có ngày thì hạn là 23:59 ngày đó."""
    if task.due_date is None:
        return None
    return combine(task.due_date, task.due_time or END_OF_DAY)


def is_overdue(task, now: datetime) -> bool:
    deadline = due_at(task)
    return task.completed_at is None and deadline is not None and deadline < now


_FAR_FUTURE = combine(date(9999, 12, 31), END_OF_DAY)


def sort_key(task) -> tuple:
    """Theo hạn chót (task không hạn ở cuối), rồi mức ưu tiên Cao → Thấp (FR-005)."""
    deadline = due_at(task)
    return (deadline is None, deadline or _FAR_FUTURE, task.priority, task.id)


# ---- Truy vấn ---------------------------------------------------------------------------------


def get_task(task_id: int) -> Task:
    task = db.session.get(Task, task_id)
    if task is None:
        raise not_found("Không tìm thấy công việc")
    return task


def list_tasks(
    list_id: int | None = None, include_completed: bool = False, tag_ids: list[int] | None = None
) -> list[Task]:
    query = select(Task)
    if list_id is not None:
        query = query.where(Task.list_id == list_id)
    if not include_completed:
        query = query.where(Task.completed_at.is_(None))
    if tag_ids:
        query = query.where(Task.id.in_(select(TaskTag.task_id).where(TaskTag.tag_id.in_(tag_ids))))
    return sorted(db.session.scalars(query), key=sort_key)


# ---- Ghi dữ liệu ------------------------------------------------------------------------------


def _check_list(list_id: int) -> None:
    if db.session.get(TaskList, list_id) is None:
        raise ApiError(
            400, "validation_error", "Dữ liệu chưa hợp lệ", {"list_id": "Danh sách không tồn tại"}
        )


def create_task(data: dict) -> Task:
    tag_ids = data.pop("tag_ids", [])
    _check_list(data["list_id"])
    task = Task(**data)
    db.session.add(task)
    db.session.flush()
    replace_tag_links(TaskTag, "task_id", task.id, tag_ids)
    bump_revision(db.session)
    db.session.commit()
    return task


def update_task(task_id: int, changes: dict) -> Task:
    """`changes` chỉ chứa trường được gửi; giá trị None nghĩa là xoá (với trường cho phép)."""
    task = get_task(task_id)
    for field in ("title", "priority", "list_id"):
        if field in changes and changes[field] is None:
            raise ApiError(400, "validation_error", "Dữ liệu chưa hợp lệ", {field: REQUIRED})
    if "list_id" in changes:
        _check_list(changes["list_id"])

    tag_ids = changes.pop("tag_ids", None)
    for field, value in changes.items():
        setattr(task, field, value)
    if task.due_time is not None and task.due_date is None:
        raise ApiError(
            400, "validation_error", "Dữ liệu chưa hợp lệ", {"due_time": DUE_TIME_NEEDS_DATE}
        )
    if tag_ids is not None:
        replace_tag_links(TaskTag, "task_id", task.id, tag_ids)
        db.session.expire(task, ["tag_links"])
    if task.is_auto and (changes or tag_ids is not None):
        task.user_modified = True  # task tự tạo đã bị người dùng sửa → không tự cập nhật nữa
    bump_revision(db.session)
    db.session.commit()
    return task


def set_completed(task_id: int, completed: bool) -> Task:
    task = get_task(task_id)
    task.completed_at = timeutil.now() if completed else None
    bump_revision(db.session)
    db.session.commit()
    return task


def delete_task_rows(task: Task) -> None:
    """Xoá một task; task tự tạo thì đánh dấu buổi học để không tạo lại (FR-049)."""
    if task.is_auto and task.source_session_id is not None:
        session = db.session.get(ClassSession, task.source_session_id)
        if session is not None:
            session.auto_task_suppressed = True
    db.session.delete(task)


def delete_task(task_id: int) -> None:
    delete_task_rows(get_task(task_id))
    bump_revision(db.session)
    db.session.commit()
