"""/api/exams — buổi thi (FR-055 đến FR-058, FR-063)."""

from flask import Blueprint, request

from app.api.params import bool_arg, date_arg
from app.lib import timeutil
from app.schemas.exams import ExamFields, ExamPatch, serialize_exam
from app.schemas.tags import TagIdsIn
from app.services import exams as service

bp = Blueprint("exams", __name__)


def _one(exam, conflicts=None) -> dict:
    return serialize_exam(exam, timeutil.now(), conflicts)


@bp.get("/exams")
def list_exams():
    now = timeutil.now()
    items = service.list_exams(
        date_arg("from"), date_arg("to"), bool_arg("include_past", False), now
    )
    conflicts = service.conflicts_for(items)
    return {"exams": [serialize_exam(e, now, conflicts[e.id]) for e in items]}


@bp.post("/exams")
def create_exam():
    data = ExamFields.model_validate(request.get_json(silent=True) or {}).model_dump()
    exam, conflicts, warnings = service.create_exam(data)
    return {"exam": _one(exam, conflicts), "conflicts": conflicts, "warnings": warnings}, 201


@bp.patch("/exams/<int:exam_id>")
def update_exam(exam_id: int):
    patch = ExamPatch.model_validate(request.get_json(silent=True) or {})
    exam, conflicts, warnings = service.update_exam(exam_id, patch.model_dump(exclude_unset=True))
    return {"exam": _one(exam, conflicts), "conflicts": conflicts, "warnings": warnings}


@bp.delete("/exams/<int:exam_id>")
def delete_exam(exam_id: int):
    service.delete_exam(exam_id, bool_arg("confirm", False))
    return "", 204


@bp.put("/exams/<int:exam_id>/tags")
def set_tags(exam_id: int):
    data = TagIdsIn.model_validate(request.get_json(silent=True) or {})
    exam = service.set_exam_tags(exam_id, data.tag_ids)
    return _one(exam, service.conflicts_for([exam])[exam.id])
