"""/api/periods — bảng tiết: giờ từng tiết, suy từ ca, sửa tay được (feature 004, FR-011…015)."""

from flask import Blueprint, request
from sqlalchemy import select

from app.extensions import db
from app.models import Shift
from app.schemas.common import HHMM, ApiModel
from app.services import periods as service

bp = Blueprint("periods", __name__)


class PeriodIn(ApiModel):
    start_time: HHMM
    end_time: HHMM


def _shift_ids() -> list[int]:
    shifts = db.session.scalars(select(Shift).order_by(Shift.position))
    return [s.id for s in shifts][: service.MAX_SHIFTS_WITH_PERIODS]


def serialize_period(period, shift_ids: list[int]) -> dict:
    index = (period.number - 1) // service.PERIODS_PER_SHIFT
    in_shift = period.number <= service.PERIODS_PER_SHIFT * len(shift_ids)
    return {
        "number": period.number,
        "start_time": period.start_time.strftime("%H:%M"),
        "end_time": period.end_time.strftime("%H:%M"),
        "is_manual": period.is_manual,
        "shift_id": shift_ids[index] if in_shift else None,
    }


@bp.get("/periods")
def list_periods():
    shift_ids = _shift_ids()
    return [serialize_period(p, shift_ids) for p in service.list_periods()]


@bp.put("/periods/<int:number>")
def put_period(number: int):
    data = PeriodIn.model_validate(request.get_json(silent=True) or {})
    period, warnings = service.put_period(number, data.start_time, data.end_time)
    body = serialize_period(period, _shift_ids())
    return {**body, "warnings": warnings} if warnings else body


@bp.post("/periods/<int:number>/reset")
def reset_period(number: int):
    period = service.reset_period(number)
    return serialize_period(period, _shift_ids()) if period is not None else ("", 204)


@bp.delete("/periods/<int:number>")
def delete_period(number: int):
    service.delete_period(number)
    return "", 204
