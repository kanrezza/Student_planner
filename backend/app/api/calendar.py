"""GET /api/calendar?from=&to=&tags= (FR-016, FR-017, FR-045)."""

from flask import Blueprint

from app.api.errors import ApiError
from app.api.params import date_arg, int_list_arg
from app.lib import timeutil
from app.schemas.subjects import serialize_session
from app.schemas.tasks import serialize_task
from app.services import calendar as service

bp = Blueprint("calendar", __name__)


@bp.get("/calendar")
def calendar():
    start, end = date_arg("from", required=True), date_arg("to", required=True)
    if end < start:
        raise ApiError(400, "validation_error", "Tham số không hợp lệ", {"to": "Phải sau `from`"})
    if (end - start).days > service.MAX_RANGE_DAYS:
        raise ApiError(
            400,
            "validation_error",
            "Tham số không hợp lệ",
            {"to": f"Khoảng ngày tối đa {service.MAX_RANGE_DAYS} ngày"},
        )
    tag_ids = int_list_arg("tags")
    now = timeutil.now()
    return {
        "sessions": [serialize_session(s) for s in service.sessions_in_range(start, end, tag_ids)],
        "tasks": [serialize_task(t, now) for t in service.tasks_in_range(start, end, tag_ids)],
    }
