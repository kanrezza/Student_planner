"""Danh sách task (FR-004): tạo, đổi tên/màu, xoá có chuyển hoặc xoá task (data-model.md)."""

from sqlalchemy import func, select

from app.api.errors import ApiError, not_found
from app.extensions import db
from app.lib.text import ci_key
from app.models import Task, TaskList
from app.services.colors import is_palette_color, next_color
from app.services.revision import bump_revision
from app.services.tasks import delete_task_rows


def _invalid(field: str, message: str) -> ApiError:
    return ApiError(400, "validation_error", "Dữ liệu chưa hợp lệ", {field: message})


def get_list(list_id: int) -> TaskList:
    task_list = db.session.get(TaskList, list_id)
    if task_list is None:
        raise not_found("Không tìm thấy danh sách")
    return task_list


def lists_with_open_counts() -> list[tuple[TaskList, int]]:
    counts = dict(
        db.session.execute(
            select(Task.list_id, func.count())
            .where(Task.completed_at.is_(None))
            .group_by(Task.list_id)
        ).all()
    )
    lists = db.session.scalars(select(TaskList).order_by(TaskList.id)).all()
    return [(tl, counts.get(tl.id, 0)) for tl in lists]


def open_count(list_id: int) -> int:
    return db.session.scalar(
        select(func.count()).where(Task.list_id == list_id, Task.completed_at.is_(None))
    )


def _check_name(name: str, exclude_id: int | None = None) -> None:
    for other in db.session.scalars(select(TaskList)):
        if other.id != exclude_id and ci_key(other.name) == ci_key(name):
            raise _invalid("name", "Đã có danh sách tên này")


def _check_color(color: str) -> None:
    if not is_palette_color(color):
        raise _invalid("color", "Màu không hợp lệ")


def create_list(name: str, color: str | None) -> TaskList:
    _check_name(name)
    if color is None:
        color = next_color(list(db.session.scalars(select(TaskList.color))))
    _check_color(color)
    task_list = TaskList(name=name, color=color)
    db.session.add(task_list)
    db.session.commit()
    return task_list


def update_list(list_id: int, changes: dict) -> TaskList:
    task_list = get_list(list_id)
    if changes.get("name") is not None:
        _check_name(changes["name"], exclude_id=list_id)
        task_list.name = changes["name"]
    if changes.get("color") is not None:
        _check_color(changes["color"])
        task_list.color = changes["color"]
    db.session.commit()
    return task_list


def delete_list(list_id: int, move_to: int | None, delete_tasks: bool) -> None:
    task_list = get_list(list_id)
    target = None
    if move_to is not None:
        if move_to == list_id:
            raise _invalid("move_to", "Hãy chọn một danh sách khác")
        target = get_list(move_to)

    # "Học tập" là nơi chứa task tự tạo: phải có danh sách thay thế (data-model.md).
    if task_list.is_default_study and target is None:
        raise ApiError(
            400,
            "default_list_requires_replacement",
            "Cần chọn danh sách thay thế cho “Học tập” (nơi chứa task tự tạo)",
        )

    tasks = list(db.session.scalars(select(Task).where(Task.list_id == list_id)))
    if tasks and target is None and not delete_tasks:
        raise ApiError(
            409,
            "conflict",
            "Danh sách còn công việc: hãy chuyển sang danh sách khác hoặc xoá luôn",
            details={"task_count": len(tasks)},
        )

    for task in tasks:
        if target is not None:
            task.list_id = target.id
        else:
            delete_task_rows(task)
    if task_list.is_default_study:
        task_list.is_default_study = False
        db.session.flush()  # tránh vi phạm "đúng một danh sách mặc định" khi chuyển cờ
        target.is_default_study = True
    db.session.flush()
    db.session.delete(task_list)
    bump_revision(db.session)
    db.session.commit()
