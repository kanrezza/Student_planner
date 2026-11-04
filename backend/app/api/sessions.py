"""/api/sessions — sửa, huỷ, khôi phục, gắn nhãn một buổi học (FR-011, FR-012, FR-043)."""

import datetime as dt

from flask import Blueprint, request

from app.schemas.common import HHMM, ApiModel, OptionalText
from app.schemas.subjects import serialize_session
from app.schemas.tags import TagIdsIn
from app.services import sessions as service

bp = Blueprint("sessions", __name__)


class SessionPatch(ApiModel):
    date: dt.date | None = None  # dời sang ngày khác (feature 002 FR-028)
    start_time: HHMM | None = None
    end_time: HHMM | None = None
    room: OptionalText = None
    important_override: bool | None = None  # null = theo môn (FR-067)


@bp.get("/sessions/<int:session_id>")
def get_session(session_id: int):
    return serialize_session(service.get_session(session_id))


@bp.patch("/sessions/<int:session_id>")
def update_session(session_id: int):
    patch = SessionPatch.model_validate(request.get_json(silent=True) or {})
    changes = patch.model_dump(exclude_unset=True)
    if changes.get("date") is None:
        changes.pop("date", None)
    session, warnings = service.update_session(session_id, changes)
    return {"session": serialize_session(session), "warnings": warnings}


@bp.post("/sessions/<int:session_id>/cancel")
def cancel(session_id: int):
    return serialize_session(service.set_cancelled(session_id, True))


@bp.post("/sessions/<int:session_id>/restore")
def restore(session_id: int):
    return serialize_session(service.set_cancelled(session_id, False))


@bp.put("/sessions/<int:session_id>/tags")
def set_tags(session_id: int):
    data = TagIdsIn.model_validate(request.get_json(silent=True) or {})
    return serialize_session(service.set_session_tags(session_id, data.tag_ids))
