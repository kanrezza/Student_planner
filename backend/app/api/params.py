"""Đọc tham số query string, báo lỗi tiếng Việt khi sai kiểu."""

from datetime import date

from flask import request

from app.api.errors import ApiError


def _invalid(name: str, message: str) -> ApiError:
    return ApiError(400, "validation_error", "Tham số không hợp lệ", {name: message})


def int_arg(name: str) -> int | None:
    value = request.args.get(name)
    if value in (None, ""):
        return None
    try:
        return int(value)
    except ValueError:
        raise _invalid(name, "Phải là số nguyên") from None


def int_list_arg(name: str) -> list[int]:
    """`?tags=1,2,3` → [1, 2, 3]."""
    value = request.args.get(name, "")
    try:
        return [int(part) for part in value.split(",") if part.strip()]
    except ValueError:
        raise _invalid(name, "Phải là danh sách số, cách nhau bởi dấu phẩy") from None


def bool_arg(name: str, default: bool) -> bool:
    value = request.args.get(name)
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes")


def date_arg(name: str, required: bool = False) -> date | None:
    value = request.args.get(name)
    if not value:
        if required:
            raise _invalid(name, "Trường này là bắt buộc")
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise _invalid(name, "Ngày phải có dạng YYYY-MM-DD") from None
