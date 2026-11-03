"""/api/tags và gắn nhãn cho môn học, task (FR-042, FR-043)."""

from flask import Blueprint, request

from app.lib import timeutil
from app.schemas.subjects import serialize_subject
from app.schemas.tags import TagIdsIn, TagIn, TagPatch, serialize_tag
from app.schemas.tasks import serialize_task
from app.services import tags as service
from app.services import tasks as task_service

bp = Blueprint("tags", __name__)


@bp.get("/tags")
def list_tags():
    return [serialize_tag(t) for t in service.list_tags()]


@bp.post("/tags")
def create_tag():
    data = TagIn.model_validate(request.get_json(silent=True) or {})
    return serialize_tag(service.create_tag(data.name, data.color)), 201


@bp.patch("/tags/<int:tag_id>")
def update_tag(tag_id: int):
    patch = TagPatch.model_validate(request.get_json(silent=True) or {})
    return serialize_tag(service.update_tag(tag_id, patch.model_dump(exclude_unset=True)))


@bp.delete("/tags/<int:tag_id>")
def delete_tag(tag_id: int):
    service.delete_tag(tag_id)
    return "", 204


@bp.put("/subjects/<int:subject_id>/tags")
def set_subject_tags(subject_id: int):
    data = TagIdsIn.model_validate(request.get_json(silent=True) or {})
    return serialize_subject(service.set_subject_tags(subject_id, data.tag_ids))


@bp.put("/tasks/<int:task_id>/tags")
def set_task_tags(task_id: int):
    """Đi qua `update_task` để task tự tạo được đánh dấu "đã bị người dùng sửa"."""
    data = TagIdsIn.model_validate(request.get_json(silent=True) or {})
    task = task_service.update_task(task_id, {"tag_ids": data.tag_ids})
    return serialize_task(task, timeutil.now())
