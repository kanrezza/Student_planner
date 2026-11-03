"""Schema request/response cho task và danh sách (contracts/rest-api.md, data-model.md)."""

from datetime import date
from typing import Literal

from pydantic import Field, ValidationInfo, field_validator

from app.lib.timeutil import iso
from app.schemas.common import HHMM, ApiModel, OptionalText, VietnameseText
from app.services import tasks as task_rules
from app.services.colors import display_color
from app.services.tag_links import serialize_tags

Priority = Literal[1, 2, 3]  # 1 = Cao, 2 = Trung bình, 3 = Thấp


class TaskIn(ApiModel):
    title: VietnameseText = Field(min_length=1, max_length=300)
    notes: OptionalText = None
    due_date: date | None = None
    due_time: HHMM | None = None
    priority: Priority = 2
    list_id: int
    tag_ids: list[int] = []
    # None = theo mặc định; -1 = tắt nhắc; ≥ 0 = số phút trước hạn (chỉ với task có giờ).
    reminder_minutes: int | None = Field(default=None, ge=-1)

    @field_validator("due_time")
    @classmethod
    def _time_needs_date(cls, value, info: ValidationInfo):
        if value is not None and info.data.get("due_date") is None:
            raise ValueError(task_rules.DUE_TIME_NEEDS_DATE)
        return value


class TaskPatch(ApiModel):
    """Sửa một phần. Gửi `null` để xoá giá trị (ví dụ bỏ hạn chót)."""

    title: VietnameseText | None = Field(default=None, min_length=1, max_length=300)
    notes: OptionalText = None
    due_date: date | None = None
    due_time: HHMM | None = None
    priority: Priority | None = None
    list_id: int | None = None
    tag_ids: list[int] | None = None
    reminder_minutes: int | None = Field(default=None, ge=-1)


class ListIn(ApiModel):
    name: VietnameseText = Field(min_length=1, max_length=100)
    color: str | None = None


class ListPatch(ApiModel):
    name: VietnameseText | None = Field(default=None, min_length=1, max_length=100)
    color: str | None = None


def serialize_task(task, now) -> dict:
    due = task_rules.due_at(task)
    tags = task.tags
    return {
        "id": task.id,
        "title": task.title,
        "notes": task.notes,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "due_time": task.due_time.strftime("%H:%M") if task.due_time else None,
        "due_at": iso(due) if due else None,
        "priority": task.priority,
        "list_id": task.list_id,
        "list_name": task.list.name,
        "completed": task.completed_at is not None,
        "completed_at": iso(task.completed_at) if task.completed_at else None,
        "is_overdue": task_rules.is_overdue(task, now),
        "is_auto": task.is_auto,
        "source_session_id": task.source_session_id,
        "user_modified": task.user_modified,
        "tags": serialize_tags(tags),
        "display_color": display_color([t.color for t in tags], task.list.color),
        "reminder_minutes": task.reminder_minutes,
        "reminder_at": None,  # được tính ở User Story 7 (nhắc lịch)
    }


def serialize_list(task_list, open_task_count: int) -> dict:
    return {
        "id": task_list.id,
        "name": task_list.name,
        "color": task_list.color,
        "is_default_study": task_list.is_default_study,
        "open_task_count": open_task_count,
    }
