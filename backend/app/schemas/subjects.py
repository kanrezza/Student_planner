"""Schema học kỳ, môn học, buổi học (contracts/rest-api.md, data-model.md)."""

from datetime import date

from pydantic import Field, ValidationInfo, field_validator, model_validator

from app.lib.timeutil import iso
from app.schemas.common import HHMM, ApiModel, OptionalText, VietnameseText
from app.services.colors import display_color
from app.services.shifts import shift_label
from app.services.tag_links import serialize_tags

# ---- Học kỳ ---------------------------------------------------------------------------------


class SemesterIn(ApiModel):
    name: VietnameseText = Field(min_length=1, max_length=100)
    start_date: date
    end_date: date

    @field_validator("end_date")
    @classmethod
    def _end_after_start(cls, value: date, info: ValidationInfo):
        start = info.data.get("start_date")
        if start and value < start:
            raise ValueError("Ngày kết thúc phải sau hoặc bằng ngày bắt đầu")
        return value


class SemesterPatch(ApiModel):
    name: VietnameseText | None = Field(default=None, min_length=1, max_length=100)
    start_date: date | None = None
    end_date: date | None = None


def serialize_semester(semester, is_current: bool) -> dict:
    return {
        "id": semester.id,
        "name": semester.name,
        "start_date": semester.start_date.isoformat(),
        "end_date": semester.end_date.isoformat(),
        "is_current": is_current,
    }


# ---- Môn học --------------------------------------------------------------------------------


def _check_weekdays(value: list[int] | None) -> list[int] | None:
    if value is None:
        return None
    if any(d < 1 or d > 7 for d in value):
        raise ValueError("Thứ phải từ 1 (Thứ Hai) đến 7 (Chủ Nhật)")
    if len(set(value)) != len(value):
        raise ValueError("Các thứ không được trùng nhau")
    return sorted(value)


class ShiftRef(ApiModel):
    start_shift_id: int
    end_shift_id: int


class ScheduleIn(ApiModel):
    """Một quy tắc lặp hằng tuần của môn (feature 004, FR-020).

    Đúng một trong hai: `shift` (ca/dãy ca) hoặc cặp `start_time`/`end_time` (giờ tuỳ chỉnh); ràng
    buộc này kiểm tra ở service để báo lỗi đúng tên trường. `id` có mặt khi sửa quy tắc đã lưu.
    """

    id: int | None = None
    weekdays: list[int] = Field(min_length=1)
    start_date: date | None = None  # None = theo học kỳ
    end_date: date | None = None
    shift: ShiftRef | None = None
    start_time: HHMM | None = None
    end_time: HHMM | None = None
    period_from: int | None = Field(default=None, ge=1, le=30)
    period_to: int | None = Field(default=None, ge=1, le=30)
    room: OptionalText = None

    @field_validator("weekdays")
    @classmethod
    def _weekdays(cls, value):
        return _check_weekdays(value)


class SubjectFields(ApiModel):
    """Trường chung của một môn (dùng cho thêm một môn và cho từng dòng khi nhập nhiều môn).

    Lịch học: `schedules` (≥ 1 quy tắc), hoặc dạng rút gọn cho một quy tắc duy nhất bằng các trường
    phẳng `weekdays`, `shift` / `start_time` + `end_time`, `room` (tương thích với bản trước
    feature 004).
    """

    name: VietnameseText = Field(min_length=1, max_length=200)
    class_code: OptionalText = None
    course_code: OptionalText = None
    credits: int | None = Field(default=None, ge=0, le=30)
    lecturer: OptionalText = None
    schedules: list[ScheduleIn] | None = Field(default=None, min_length=1)
    room: OptionalText = None
    weekdays: list[int] | None = Field(default=None, min_length=1)
    shift: ShiftRef | None = None
    start_time: HHMM | None = None
    end_time: HHMM | None = None
    color: str | None = None
    tag_ids: list[int] = []
    reminder_minutes: int | None = Field(default=None, ge=-1)
    is_important: bool = False

    @field_validator("weekdays")
    @classmethod
    def _weekdays(cls, value):
        return _check_weekdays(value)

    @model_validator(mode="after")
    def _has_schedule(self):
        if self.schedules is None and self.weekdays is None:
            raise ValueError(
                "Cần ít nhất một lịch học (schedules) hoặc các thứ trong tuần (weekdays)"
            )
        return self


class SubjectIn(SubjectFields):
    semester_id: int | None = None  # None = học kỳ hiện tại
    start_date: date | None = None  # None = ngày bắt đầu học kỳ (dạng rút gọn)
    end_date: date | None = None  # None = ngày kết thúc học kỳ (dạng rút gọn)


class SubjectPatch(ApiModel):
    name: VietnameseText | None = Field(default=None, min_length=1, max_length=200)
    class_code: OptionalText = None
    course_code: OptionalText = None
    credits: int | None = Field(default=None, ge=0, le=30)
    lecturer: OptionalText = None
    schedules: list[ScheduleIn] | None = Field(default=None, min_length=1)
    room: OptionalText = None
    weekdays: list[int] | None = Field(default=None, min_length=1)
    shift: ShiftRef | None = None
    start_time: HHMM | None = None
    end_time: HHMM | None = None
    color: str | None = None
    tag_ids: list[int] | None = None
    reminder_minutes: int | None = Field(default=None, ge=-1)
    is_important: bool | None = None
    start_date: date | None = None
    end_date: date | None = None

    @field_validator("weekdays")
    @classmethod
    def _weekdays(cls, value):
        return _check_weekdays(value)


class BulkSubjectsIn(ApiModel):
    semester_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    rows: list[SubjectFields] = Field(min_length=1)


def serialize_schedule(rule) -> dict:
    """Quy tắc lặp (đọc) — contracts/rest-api.md (feature 004)."""
    return {
        "id": rule.id,
        "position": rule.position,
        "weekdays": list(rule.weekdays),
        "start_date": rule.start_date.isoformat(),
        "end_date": rule.end_date.isoformat(),
        "shift": (
            {"start_shift_id": rule.start_shift_id, "end_shift_id": rule.end_shift_id}
            if rule.start_shift_id
            else None
        ),
        "shift_label": shift_label(rule.start_shift, rule.end_shift),
        "start_time": rule.start_time.strftime("%H:%M"),
        "end_time": rule.end_time.strftime("%H:%M"),
        "period_from": rule.period_from,
        "period_to": rule.period_to,
        "room": rule.room,
    }


def serialize_subject(subject, session_count: int | None = None) -> dict:
    tags = subject.tags
    first = subject.schedules[0]
    span_start, span_end = subject.date_span
    data = {
        "id": subject.id,
        "semester_id": subject.semester_id,
        "name": subject.name,
        "class_code": subject.class_code,
        "course_code": subject.course_code,
        "credits": subject.credits,
        "lecturer": subject.lecturer,
        "color": subject.color,
        "schedules": [serialize_schedule(rule) for rule in subject.schedules],
        # Tóm tắt tương thích ngược: thứ, ca, giờ, phòng của lịch đầu tiên; khoảng ngày là phạm vi
        # từ ngày sớm nhất tới muộn nhất của mọi lịch. Giao diện mới dùng `schedules`.
        "room": first.room,
        "weekdays": list(first.weekdays),
        "shift": (
            {"start_shift_id": first.start_shift_id, "end_shift_id": first.end_shift_id}
            if first.start_shift_id
            else None
        ),
        "shift_label": shift_label(first.start_shift, first.end_shift),
        "start_time": first.start_time.strftime("%H:%M"),
        "end_time": first.end_time.strftime("%H:%M"),
        "start_date": span_start.isoformat(),
        "end_date": span_end.isoformat(),
        "reminder_minutes": subject.reminder_minutes,
        "is_important": subject.is_important,
        "tags": serialize_tags(tags),
    }
    if session_count is not None:
        data["session_count"] = session_count
    return data


def _active_auto_task_id(session) -> int | None:
    """Task tự tạo đã ở Thùng rác coi như không có (feature 002 FR-031)."""
    task = session.auto_task
    return task.id if task is not None and task.deleted_at is None else None


def session_shift_label(session) -> str | None:
    """Nhãn ca của buổi: lấy từ quy tắc đã sinh buổi, không có khi buổi đã sửa giờ riêng."""
    rule = session.schedule
    if session.time_overridden or rule is None:
        return None
    return shift_label(rule.start_shift, rule.end_shift)


def serialize_session(session) -> dict:
    """Buổi học (đọc) — contracts/rest-api.md "Session (đọc)"."""
    subject = session.subject
    tags = session.effective_tags
    return {
        "id": session.id,
        "subject_id": subject.id,
        "subject_name": subject.name,
        "date": session.date.isoformat(),
        "original_date": session.original_date.isoformat() if session.original_date else None,
        "is_moved": session.is_moved,
        "start_at": iso(session.start_at),
        "end_at": iso(session.end_at),
        "room": session.room,
        "lecturer": subject.lecturer,
        "class_code": subject.class_code,
        "is_cancelled": session.is_cancelled,
        "time_overridden": session.time_overridden,
        "room_overridden": session.room_overridden,
        "color": subject.color,
        "tags": serialize_tags(tags),
        "own_tag_ids": [link.tag_id for link in session.tag_links],  # nhãn riêng (không gồm môn)
        "display_color": display_color([t.color for t in tags], subject.color),
        "shift_label": session_shift_label(session),
        "auto_task_id": _active_auto_task_id(session),
        "is_important": session.is_important,
        "important_override": session.important_override,
        "subject_is_important": subject.is_important,
    }
