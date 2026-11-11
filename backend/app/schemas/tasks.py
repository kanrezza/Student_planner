"""Schema request/response cho task và danh sách (contracts/rest-api.md, data-model.md)."""

import datetime as _dt
import math
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, Field, ValidationInfo, field_validator
from sqlalchemy import exists, select

from app.extensions import db
from app.lib.timeutil import iso
from app.models import Task
from app.schemas.common import HHMM, ApiModel, OptionalText, VietnameseText
from app.services import tasks as task_rules
from app.services.board_rank import task_status
from app.services.colors import display_color
from app.services.tag_links import serialize_tags
from app.services.task_series import rule_dict

Priority = Literal[1, 2, 3]  # 1 = Cao, 2 = Trung bình, 3 = Thấp


class RecurrenceEnd(ApiModel):
    kind: Literal["never", "on_date", "after_count"] = "never"
    date: _dt.date | None = None
    count: int | None = None


class RecurrenceIn(ApiModel):
    """Quy tắc lặp (data-model §4). Kiểm tra ràng buộc theo kiểu ở `task_recurrence.validate`."""

    freq: Literal["daily", "every_n_days", "weekly", "monthly"]
    interval_days: int | None = None
    weekdays: list[int] | None = None
    month_day: int | None = None
    end: RecurrenceEnd = RecurrenceEnd()


Scope = Literal["this", "following"]


class TaskIn(ApiModel):
    title: VietnameseText = Field(min_length=1, max_length=300)
    notes: OptionalText = None
    due_date: date | None = None
    due_time: HHMM | None = None
    priority: Priority = 2
    list_id: int
    tag_ids: list[int] = []
    # Tên nhãn từ ô thêm nhanh: gắn nhãn có sẵn (so khớp không dấu) hoặc tạo nhãn mới (feature 003).
    tag_names: list[Annotated[VietnameseText, Field(min_length=1, max_length=50)]] = []
    # None = theo mặc định; -1 = tắt nhắc; ≥ 0 = số phút trước hạn (chỉ với task có giờ).
    reminder_minutes: int | None = Field(default=None, ge=-1)
    is_important: bool = False
    # Bảng Kanban (feature 005): môn gắn tay; trạng thái ban đầu "todo" hoặc "doing".
    subject_id: int | None = None
    status: Literal["todo", "doing"] = "todo"
    # Khung giờ làm (feature 002 FR-018): kiểm tra "đủ ba trường" và "kết thúc sau bắt đầu" ở
    # service, sau khi gộp với giá trị đang có (PATCH chỉ gửi một phần).
    work_date: date | None = None
    work_start: HHMM | None = None
    work_end: HHMM | None = None
    recurrence: RecurrenceIn | None = None

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
    is_important: bool | None = None
    subject_id: int | None = None
    # Chuyển sang "done" qua /complete hoặc /board; ở đây chỉ nhận todo/doing.
    status: Literal["todo", "doing"] | None = None
    work_date: date | None = None
    work_start: HHMM | None = None
    work_end: HHMM | None = None
    # Task lặp (feature 003 US3): `recurrence` = null bỏ lặp; `scope` bắt buộc khi sửa lần hiện tại.
    recurrence: RecurrenceIn | None = None
    scope: Scope | None = None


# ---- Emoji của danh sách (feature 002 FR-015) ------------------------------------------------
# Không dùng thư viện: kiểm tra theo dải mã emoji, ZWJ, VS16, modifier màu da và cờ (data-model).

EMOJI_ERROR = "Chỉ chọn một emoji"
EMOJI_MAX_BYTES = 64
_VS16, _ZWJ = 0xFE0F, 0x200D
_SKIN_TONES = range(0x1F3FB, 0x1F400)
_REGIONAL = range(0x1F1E6, 0x1F200)
_EMOJI_RANGES = (
    range(0x1F000, 0x1FB00),
    range(0x2600, 0x27C0),
    range(0x2B00, 0x2C00),
    range(0x2300, 0x2400),
    range(0x2194, 0x21AB),
)
_EMOJI_SINGLES = {0x3030, 0x303D, 0x3297, 0x3299, 0xA9, 0xAE, 0x203C, 0x2049, 0x2122, 0x2139}


def _is_emoji_char(code: int) -> bool:
    return code in _EMOJI_SINGLES or any(code in r for r in _EMOJI_RANGES)


def _is_flag(codes: list[int]) -> bool:
    return len(codes) == 2 and all(c in _REGIONAL for c in codes)


def is_single_emoji(text: str) -> bool:
    """Đúng một emoji: ký tự emoji, theo sau chỉ có VS16, màu da, hoặc ZWJ + emoji; hoặc một cờ."""
    if not text or len(text.encode()) > EMOJI_MAX_BYTES:
        return False
    codes = [ord(ch) for ch in text]
    if codes[0] in _REGIONAL:
        return _is_flag(codes)
    if not _is_emoji_char(codes[0]) or codes[0] in _SKIN_TONES:
        return False
    i = 1
    while i < len(codes):
        code = codes[i]
        if code == _VS16 or code in _SKIN_TONES:
            i += 1
        elif code == _ZWJ and i + 1 < len(codes) and _is_emoji_char(codes[i + 1]):
            i += 2
        else:
            return False
    return True


def _check_emoji(value: str | None) -> str | None:
    if value is not None and not is_single_emoji(value):
        raise ValueError(EMOJI_ERROR)
    return value


Emoji = Annotated[str | None, AfterValidator(_check_emoji)]


class ListIn(ApiModel):
    name: VietnameseText = Field(min_length=1, max_length=100)
    color: str | None = None
    emoji: Emoji = None


class ListPatch(ApiModel):
    name: VietnameseText | None = Field(default=None, min_length=1, max_length=100)
    color: str | None = None
    emoji: Emoji = None


def _reminder_times(task) -> list[str]:
    from app.services.reminders import get_settings, task_alarm_times  # tránh import vòng

    return [iso(t) for t in task_alarm_times(task, get_settings())]


def _reminder_fields(task) -> dict:
    times = _reminder_times(task)
    # `reminder_at` = mốc sớm nhất (giữ tương thích), `reminder_times` = mọi mốc (FR-068).
    return {"reminder_at": times[0] if times else None, "reminder_times": times}


TRASH_DAYS = 30


def days_left_in_trash(deleted_at: datetime | None, now: datetime) -> int | None:
    """Còn N ngày = 30 − số ngày đã qua (làm tròn lên, tối thiểu 0); None nếu không ở Thùng rác."""
    if deleted_at is None:
        return None
    elapsed_days = (now - deleted_at).total_seconds() / 86400
    return max(0, math.ceil(TRASH_DAYS - elapsed_days))


def _hhmm(value) -> str | None:
    return value.strftime("%H:%M") if value else None


def _series_fields(task) -> dict:
    series = task.series if task.series_id is not None else None
    if series is None:
        return {
            "series_id": None,
            "recurrence": None,
            "occurrence_no": None,
            "series_finished": False,
        }
    finished = (
        task.completed_at is not None
        and series.stopped_at is None
        and not db.session.scalar(
            select(
                exists().where(
                    Task.series_id == series.id,
                    Task.deleted_at.is_(None),
                    Task.completed_at.is_(None),
                )
            )
        )
    )
    return {
        "series_id": series.id,
        "recurrence": rule_dict(series),
        "occurrence_no": task.occurrence_no,
        "series_finished": finished,
    }


def effective_subject_id(task) -> int | None:
    """Môn gắn tay, hoặc môn của buổi học nguồn (deadline tự tạo) — dùng để lọc bảng."""
    if task.subject_id is not None:
        return task.subject_id
    return task.source_session.subject_id if task.source_session is not None else None


def attachment_count(task) -> int:
    return task.attachment_total


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
        "is_important": task.is_important,
        "status": task_status(task.completed_at, task.in_progress),
        "board_rank": task.board_rank,
        "subject_id": task.subject_id,
        "effective_subject_id": effective_subject_id(task),
        "attachment_count": attachment_count(task),
        "work_date": task.work_date.isoformat() if task.work_date else None,
        "work_start": _hhmm(task.work_start),
        "work_end": _hhmm(task.work_end),
        "deleted_at": iso(task.deleted_at) if task.deleted_at else None,
        "days_left_in_trash": days_left_in_trash(task.deleted_at, now),
        "trashed_from_list_name": task.trashed_from_list_name,
        **_series_fields(task),
        **_reminder_fields(task),
    }


def serialize_list(task_list, open_task_count: int) -> dict:
    return {
        "id": task_list.id,
        "name": task_list.name,
        "color": task_list.color,
        "is_default_study": task_list.is_default_study,
        "emoji": task_list.emoji,
        "open_task_count": open_task_count,
    }
