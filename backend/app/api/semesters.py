"""/api/semesters (FR-036, FR-037)."""

from flask import Blueprint, request

from app.api.params import bool_arg
from app.schemas.subjects import SemesterIn, SemesterPatch, serialize_semester
from app.services import semesters as service

bp = Blueprint("semesters", __name__)


def _out(semester):
    current = service.current_semester()
    return serialize_semester(semester, current is not None and current.id == semester.id)


@bp.get("/semesters")
def list_semesters():
    return [_out(s) for s in service.all_semesters()]


@bp.post("/semesters")
def create_semester():
    data = SemesterIn.model_validate(request.get_json(silent=True) or {})
    return _out(service.create_semester(data.name, data.start_date, data.end_date)), 201


@bp.patch("/semesters/<int:semester_id>")
def update_semester(semester_id: int):
    patch = SemesterPatch.model_validate(request.get_json(silent=True) or {})
    semester = service.update_semester(
        semester_id, patch.model_dump(exclude_unset=True), bool_arg("clamp_subjects", False)
    )
    return _out(semester)


@bp.delete("/semesters/<int:semester_id>")
def delete_semester(semester_id: int):
    service.delete_semester(semester_id, bool_arg("confirm", False))
    return "", 204
