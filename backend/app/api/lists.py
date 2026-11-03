"""/api/lists (contracts/rest-api.md — Task và danh sách)."""

from flask import Blueprint, request

from app.api.params import bool_arg, int_arg
from app.schemas.tasks import ListIn, ListPatch, serialize_list
from app.services import task_lists as service

bp = Blueprint("lists", __name__)


@bp.get("/lists")
def list_lists():
    return [serialize_list(tl, count) for tl, count in service.lists_with_open_counts()]


@bp.post("/lists")
def create_list():
    data = ListIn.model_validate(request.get_json(silent=True) or {})
    task_list = service.create_list(data.name, data.color)
    return serialize_list(task_list, 0), 201


@bp.patch("/lists/<int:list_id>")
def update_list(list_id: int):
    patch = ListPatch.model_validate(request.get_json(silent=True) or {})
    task_list = service.update_list(list_id, patch.model_dump(exclude_unset=True))
    return serialize_list(task_list, service.open_count(list_id))


@bp.delete("/lists/<int:list_id>")
def delete_list(list_id: int):
    service.delete_list(
        list_id, move_to=int_arg("move_to"), delete_tasks=bool_arg("delete_tasks", False)
    )
    return "", 204
