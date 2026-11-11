"""Dữ liệu vào của API bảng Kanban (feature 005, contracts/rest-api.md)."""

from typing import Literal

from app.schemas.common import ApiModel


class BoardMoveIn(ApiModel):
    status: Literal["todo", "doing", "done"]
    before_id: int | None = None  # thẻ ngay trên vị trí thả
    after_id: int | None = None  # thẻ ngay dưới vị trí thả
