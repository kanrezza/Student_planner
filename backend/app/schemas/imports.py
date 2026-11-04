"""Dữ liệu gửi lên `POST /api/imports/commit` (contracts/rest-api.md "Nhập ảnh")."""

import datetime as dt
from typing import Any, Literal

from pydantic import ConfigDict, Field

from app.schemas.common import ApiModel


class FieldIn(ApiModel):
    """Một trường của dòng xem trước sau khi người dùng chỉnh: `certain` là cờ "đã chắc chắn"."""

    value: Any = None
    certain: bool = True
    reason: str | None = None


class RepeatIn(ApiModel):
    mode: Literal["once", "weekly"] = "once"
    until: dt.date | None = None


class ShiftIn(ApiModel):
    start_shift_id: int
    end_shift_id: int


class ImportRowIn(ApiModel):
    # Giao diện gửi lại nguyên dòng xem trước (kèm các trường chỉ để hiển thị): bỏ qua trường thừa.
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    fields: dict[str, FieldIn]
    shift: ShiftIn | None = None
    semester_id: int | None = None
    repeat: RepeatIn = RepeatIn()
    merge_group: str | None = None
    merge_accepted: bool = False
    tag_ids: list[int] = []
    selected: bool = True


class ExamRowIn(ApiModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    fields: dict[str, FieldIn]
    tag_ids: list[int] = []
    selected: bool = True


class CommitIn(ApiModel):
    kind: Literal["week_schedule", "exam_table"]
    rows: list[ImportRowIn] = Field(default_factory=list)
    exam_rows: list[ExamRowIn] = Field(default_factory=list)
