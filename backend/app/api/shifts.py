"""/api/shifts — bảng ca học (FR-038 đến FR-040)."""

from flask import Blueprint, request
from pydantic import Field

from app.api.params import bool_arg
from app.schemas.common import HHMM, ApiModel, VietnameseText
from app.services import shifts as service

bp = Blueprint("shifts", __name__)


class ShiftIn(ApiModel):
    name: VietnameseText = Field(min_length=1, max_length=50)
    start_time: HHMM
    end_time: HHMM


class ShiftPatch(ApiModel):
    name: VietnameseText | None = Field(default=None, min_length=1, max_length=50)
    start_time: HHMM | None = None
    end_time: HHMM | None = None


def serialize_shift(shift) -> dict:
    return {
        "id": shift.id,
        "name": shift.name,
        "start_time": shift.start_time.strftime("%H:%M"),
        "end_time": shift.end_time.strftime("%H:%M"),
        "position": shift.position,
    }


@bp.get("/shifts")
def list_shifts():
    return [serialize_shift(s) for s in service.list_shifts()]


@bp.post("/shifts")
def create_shift():
    data = ShiftIn.model_validate(request.get_json(silent=True) or {})
    return serialize_shift(service.create_shift(data.name, data.start_time, data.end_time)), 201


@bp.patch("/shifts/<int:shift_id>")
def update_shift(shift_id: int):
    patch = ShiftPatch.model_validate(request.get_json(silent=True) or {})
    shift = service.update_shift(
        shift_id, patch.model_dump(exclude_unset=True), bool_arg("confirm", False)
    )
    return serialize_shift(shift)


@bp.delete("/shifts/<int:shift_id>")
def delete_shift(shift_id: int):
    service.delete_shift(shift_id, bool_arg("confirm", False))
    return "", 204
