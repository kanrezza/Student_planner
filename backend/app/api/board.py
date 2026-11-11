"""/api/tasks/board — bảng Kanban (feature 005)."""

from flask import Blueprint, request

from app.api.errors import ApiError
from app.api.params import int_list_arg
from app.lib import timeutil
from app.schemas.board import BoardMoveIn
from app.schemas.tasks import serialize_task
from app.services import board as service

bp = Blueprint("board", __name__)


@bp.get("/tasks/board")
def get_board():
    done_window = request.args.get("done_window", "7d")
    if done_window not in ("7d", "all"):
        raise ApiError(
            400, "validation_error", "Tham số không hợp lệ", {"done_window": "Phải là 7d hoặc all"}
        )
    filters = service.BoardFilters(
        list_ids=int_list_arg("list_ids"),
        tag_ids=int_list_arg("tag_ids"),
        subject_ids=int_list_arg("subject_ids"),
    )
    now = timeutil.now()
    result = service.board(filters, done_window, now)
    return {
        "columns": {
            status: [serialize_task(task, now) for task in tasks]
            for status, tasks in result["columns"].items()
        },
        "done_hidden_count": result["done_hidden_count"],
    }


@bp.patch("/tasks/<int:task_id>/board")
def move_card(task_id: int):
    data = BoardMoveIn.model_validate(request.get_json(silent=True) or {})
    result = service.move(task_id, data.status, data.before_id, data.after_id)
    now = timeutil.now()
    return {
        "task": serialize_task(result["task"], now),
        "next_task": serialize_task(result["next_task"], now) if result["next_task"] else None,
        "undo": result["undo"],
    }
