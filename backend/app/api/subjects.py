"""/api/subjects (FR-007 đến FR-015)."""

from flask import Blueprint, request

from app.api.params import bool_arg, int_arg
from app.schemas.subjects import (
    BulkSubjectsIn,
    SubjectIn,
    SubjectPatch,
    serialize_session,
    serialize_subject,
)
from app.services import subjects as service

bp = Blueprint("subjects", __name__)


def _count(subject) -> int:
    return len(subject.sessions)


@bp.get("/subjects")
def list_subjects():
    return [serialize_subject(s, _count(s)) for s in service.list_subjects(int_arg("semester_id"))]


@bp.get("/subjects/<int:subject_id>")
def get_subject(subject_id: int):
    subject = service.get_subject(subject_id)
    data = serialize_subject(subject, _count(subject))
    data["sessions"] = [serialize_session(s) for s in subject.sessions]
    return data


@bp.post("/subjects")
def create_subject():
    data = SubjectIn.model_validate(request.get_json(silent=True) or {})
    subject, warnings = service.create_subject(data.model_dump())
    return {
        "subject": serialize_subject(subject),
        "session_count": _count(subject),
        "warnings": warnings,
    }, 201


@bp.post("/subjects/bulk")
def create_bulk():
    data = BulkSubjectsIn.model_validate(request.get_json(silent=True) or {})
    subjects, warnings = service.create_bulk(data.model_dump())
    return {
        "subjects": [serialize_subject(s, _count(s)) for s in subjects],
        "session_count": sum(_count(s) for s in subjects),
        "warnings": warnings,
    }, 201


@bp.patch("/subjects/<int:subject_id>")
def update_subject(subject_id: int):
    patch = SubjectPatch.model_validate(request.get_json(silent=True) or {})
    subject, warnings = service.update_subject(
        subject_id, patch.model_dump(exclude_unset=True), bool_arg("confirm", False)
    )
    return {
        "subject": serialize_subject(subject),
        "session_count": _count(subject),
        "warnings": warnings,
    }


@bp.delete("/subjects/<int:subject_id>")
def delete_subject(subject_id: int):
    service.delete_subject(subject_id, bool_arg("confirm", False))
    return "", 204
