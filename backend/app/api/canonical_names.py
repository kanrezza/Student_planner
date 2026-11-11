"""/api/canonical-names — danh sách tên môn chuẩn từ PDF (feature 004, FR-028, FR-029)."""

from flask import Blueprint

from app.services import canonical_names as service

bp = Blueprint("canonical_names", __name__)


@bp.get("/canonical-names")
def list_names():
    return [
        {
            "id": n.id,
            "name": n.name,
            "course_code": n.course_code,
            "created_at": n.created_at.isoformat(),
        }
        for n in service.list_names()
    ]


@bp.delete("/canonical-names")
def clear_names():
    service.clear()
    return "", 204
