"""/api/tasks (contracts/rest-api.md — Task và danh sách)."""

from flask import Blueprint, request

from app.api.params import bool_arg, int_arg, int_list_arg
from app.lib import timeutil
from app.schemas.tasks import TaskIn, TaskPatch, serialize_task
from app.services import tasks as service

bp = Blueprint("tasks", __name__)


def _out(task, status: int = 200):
    return serialize_task(task, timeutil.now()), status


@bp.get("/tasks")
def list_tasks():
    tasks = service.list_tasks(
        list_id=int_arg("list_id"),
        include_completed=bool_arg("include_completed", False),
        tag_ids=int_list_arg("tags"),
    )
    now = timeutil.now()
    return [serialize_task(t, now) for t in tasks]


@bp.get("/tasks/<int:task_id>")
def get_task(task_id: int):
    return _out(service.get_task(task_id))


@bp.post("/tasks")
def create_task():
    data = TaskIn.model_validate(request.get_json(silent=True) or {})
    return _out(service.create_task(data.model_dump()), 201)


@bp.patch("/tasks/<int:task_id>")
def update_task(task_id: int):
    patch = TaskPatch.model_validate(request.get_json(silent=True) or {})
    return _out(service.update_task(task_id, patch.model_dump(exclude_unset=True)))


@bp.post("/tasks/<int:task_id>/complete")
def complete(task_id: int):
    return _out(service.set_completed(task_id, True))


@bp.post("/tasks/<int:task_id>/uncomplete")
def uncomplete(task_id: int):
    return _out(service.set_completed(task_id, False))


@bp.delete("/tasks/<int:task_id>")
def delete_task(task_id: int):
    service.delete_task(task_id)
    return "", 204
