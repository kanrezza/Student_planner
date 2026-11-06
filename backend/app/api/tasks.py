"""/api/tasks, /api/task-counts, /api/trash (contracts/rest-api.md của feature 001 và 002)."""

from flask import Blueprint, request

from app.api.errors import ApiError
from app.api.params import bool_arg, int_arg, int_list_arg
from app.lib import timeutil
from app.schemas.tasks import TaskIn, TaskPatch, serialize_task
from app.services import tasks as service

bp = Blueprint("tasks", __name__)


def _out(task, status: int = 200):
    return serialize_task(task, timeutil.now()), status


def _out_with_warnings(task, status: int = 200):
    """Có cảnh báo → `{task, warnings}`; không có → chỉ task (giữ dạng trả của feature 001)."""
    warnings = service.task_warnings(task)
    if not warnings:
        return _out(task, status)
    return {"task": serialize_task(task, timeutil.now()), "warnings": warnings}, status


@bp.get("/tasks")
def list_tasks():
    now = timeutil.now()
    view, list_id, tag_id = request.args.get("view"), int_arg("list_id"), int_arg("tag_id")
    if view is not None and view not in service.SMART_VIEWS:
        raise ApiError(
            400,
            "validation_error",
            "Tham số không hợp lệ",
            {"view": "Giá trị phải là một trong: " + ", ".join(service.SMART_VIEWS)},
        )
    if view is not None or tag_id is not None:
        tasks = service.smart_view(view, now, list_id=list_id, tag_id=tag_id)
    else:  # tham số của feature 001
        tasks = service.list_tasks(
            list_id=list_id,
            include_completed=bool_arg("include_completed", False),
            tag_ids=int_list_arg("tags"),
        )
    return [serialize_task(t, now) for t in tasks]


@bp.get("/task-counts")
def task_counts():
    return service.counts(timeutil.now())


@bp.get("/tasks/<int:task_id>")
def get_task(task_id: int):
    return _out(service.get_task(task_id))


@bp.post("/tasks")
def create_task():
    data = TaskIn.model_validate(request.get_json(silent=True) or {})
    return _out_with_warnings(service.create_task(data.model_dump()), 201)


@bp.patch("/tasks/<int:task_id>")
def update_task(task_id: int):
    patch = TaskPatch.model_validate(request.get_json(silent=True) or {})
    changes = patch.model_dump(exclude_unset=True)
    scope = changes.pop("scope", None)
    return _out_with_warnings(service.update_task(task_id, changes, scope))


@bp.post("/tasks/<int:task_id>/complete")
def complete(task_id: int):
    """Task lặp: trả thêm `next_task` (lần kế tiếp, hoặc null khi chuỗi kết thúc)."""
    task, next_task = service.complete_task(task_id)
    now = timeutil.now()
    return {
        **serialize_task(task, now),
        "next_task": serialize_task(next_task, now) if next_task else None,
    }


@bp.post("/tasks/<int:task_id>/uncomplete")
def uncomplete(task_id: int):
    """Task lặp: trả thêm `removed_next_task_id` (lần kế tiếp đã gỡ, hoặc null)."""
    task, removed = service.uncomplete_task(task_id)
    return {**serialize_task(task, timeutil.now()), "removed_next_task_id": removed}


@bp.delete("/tasks/<int:task_id>")
def delete_task(task_id: int):
    """Mặc định chuyển vào Thùng rác (trả task để Hoàn tác); `?permanent=true` xoá hẳn."""
    if bool_arg("permanent", False):
        service.delete_permanently(task_id)
        return "", 204
    scope = request.args.get("scope")
    if scope is not None and scope not in ("this", "following"):
        raise ApiError(
            400,
            "validation_error",
            "Tham số không hợp lệ",
            {"scope": "Giá trị phải là this hoặc following"},
        )
    task, next_task = service.trash_task(task_id, scope)
    now = timeutil.now()
    return {
        **serialize_task(task, now),
        "next_task": serialize_task(next_task, now) if next_task else None,
    }


@bp.post("/tasks/<int:task_id>/restore")
def restore(task_id: int):
    task, warnings = service.restore_task(task_id)
    return {"task": serialize_task(task, timeutil.now()), "warnings": warnings}


@bp.delete("/trash")
def empty_trash():
    return {"deleted": service.empty_trash()}
