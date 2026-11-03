"""Nền tảng cho schema request/response (pydantic) và thông điệp lỗi tiếng Việt."""

import re
from datetime import time
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, PlainSerializer

from app.lib.text import nfc

_HHMM_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


class ApiModel(BaseModel):
    """Bỏ khoảng trắng hai đầu chuỗi; không chấp nhận trường lạ."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


def _parse_hhmm(value: Any) -> time:
    if isinstance(value, time):
        return value
    if isinstance(value, str) and (m := _HHMM_RE.match(value.strip())):
        return time(int(m.group(1)), int(m.group(2)))
    raise ValueError("Giờ phải có dạng HH:MM (ví dụ 07:30)")


HHMM = Annotated[
    time,
    BeforeValidator(_parse_hhmm),
    PlainSerializer(lambda t: t.strftime("%H:%M"), return_type=str),
]

VietnameseText = Annotated[str, BeforeValidator(lambda v: nfc(v) if isinstance(v, str) else v)]


def _field_path(loc: tuple) -> str:
    """('rows', 2, 'end_time') → 'rows[2].end_time'."""
    path = ""
    for part in loc:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            path += f".{part}" if path else str(part)
    return path or "_"


def _message(err: dict) -> str:
    kind, ctx = err["type"], err.get("ctx") or {}
    if kind == "missing":
        return "Trường này là bắt buộc"
    if kind in ("string_too_short", "string_too_long"):
        lo, hi = ctx.get("min_length"), ctx.get("max_length")
        if lo is not None and hi is not None:
            return f"Phải dài từ {lo} đến {hi} ký tự"
        if kind == "string_too_long":
            return f"Không được dài quá {hi} ký tự"
        if lo == 1:
            return "Trường này không được để trống"
        return f"Phải dài ít nhất {lo} ký tự"
    if kind in ("too_short", "too_long"):
        return "Số phần tử không hợp lệ"
    if kind == "greater_than_equal":
        return f"Phải lớn hơn hoặc bằng {ctx.get('ge')}"
    if kind == "less_than_equal":
        return f"Phải nhỏ hơn hoặc bằng {ctx.get('le')}"
    if kind in ("int_parsing", "int_type", "int_from_float"):
        return "Phải là số nguyên"
    if kind in ("bool_parsing", "bool_type"):
        return "Phải là đúng/sai"
    if kind in ("date_parsing", "date_from_datetime_parsing", "date_type"):
        return "Ngày phải có dạng YYYY-MM-DD"
    if kind in ("list_type", "string_type"):
        return "Kiểu dữ liệu không hợp lệ"
    if kind == "extra_forbidden":
        return "Trường không được hỗ trợ"
    if kind == "value_error":
        return str(ctx.get("error") or err.get("msg", "")).removeprefix("Value error, ")
    return "Giá trị không hợp lệ"


def vi_error_messages(errors: list[dict]) -> dict[str, str]:
    """Chuyển danh sách lỗi pydantic thành {đường dẫn trường: câu tiếng Việt} (giữ lỗi đầu tiên)."""
    fields: dict[str, str] = {}
    for err in errors:
        fields.setdefault(_field_path(tuple(err["loc"])), _message(err))
    return fields
