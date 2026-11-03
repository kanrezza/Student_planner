"""GET /api/today (FR-019, FR-020)."""

from flask import Blueprint

from app.schemas.subjects import serialize_session
from app.schemas.tasks import serialize_task
from app.services.today import today_view

bp = Blueprint("today", __name__)


@bp.get("/today")
def today():
    now, day, sessions, due_today, overdue = today_view()
    return {
        "date": day.isoformat(),
        "sessions": [serialize_session(s) for s in sessions],
        "tasks_due_today": [serialize_task(t, now) for t in due_today],
        "overdue_tasks": [serialize_task(t, now) for t in overdue],
        "notices": [],  # cảnh báo quyền thông báo / trạng thái đồng bộ: User Story 7
    }
