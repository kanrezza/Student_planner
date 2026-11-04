import datetime as dt

from pydantic import Field, field_validator

from app.lib.timeutil import iso
from app.schemas.common import HHMM, ApiModel, OptionalText, VietnameseText
from app.services.colors import display_color
from app.services.tag_links import serialize_tags

EXAM_COLOR_FALLBACK = "c07"


def _check_offsets(value: list[int] | None) -> list[int] | None:
    if value is not None and any(v < 0 for v in value):
        raise ValueError("Số phút báo trước phải từ 0 trở lên")
    return value


class ExamFields(ApiModel):
    course_name: VietnameseText = Field(min_length=1, max_length=200)
    course_code: OptionalText = None
    attempt: int = Field(default=1, ge=1, le=99)
    date: dt.date
    start_time: HHMM
    end_time: HHMM
    exam_format: OptionalText = None
    room: OptionalText = None
    candidate_number: OptionalText = None
    tag_ids: list[int] = []
    reminder_offsets: list[int] | None = None
    is_important: bool = True

    _offsets = field_validator("reminder_offsets")(_check_offsets)

    @field_validator("end_time")
    @classmethod
    def _after_start(cls, value, info):
        start = info.data.get("start_time")
        if start is not None and value <= start:
            raise ValueError("Giờ kết thúc phải sau giờ bắt đầu")
        return value


class ExamPatch(ApiModel):
    course_name: VietnameseText | None = Field(default=None, min_length=1, max_length=200)
    course_code: OptionalText = None
    attempt: int | None = Field(default=None, ge=1, le=99)
    date: dt.date | None = None
    start_time: HHMM | None = None
    end_time: HHMM | None = None
    exam_format: OptionalText = None
    room: OptionalText = None
    candidate_number: OptionalText = None
    reminder_offsets: list[int] | None = None
    is_important: bool | None = None

    _offsets = field_validator("reminder_offsets")(_check_offsets)


def serialize_exam(exam, now, conflicts: list[dict] | None = None) -> dict:
    tags = exam.tags
    return {
        "id": exam.id,
        "course_code": exam.course_code,
        "course_name": exam.course_name,
        "attempt": exam.attempt,
        "date": exam.date.isoformat(),
        "start_at": iso(exam.start_at),
        "end_at": iso(exam.end_at),
        "exam_format": exam.exam_format,
        "room": exam.room,
        "candidate_number": exam.candidate_number,
        "is_past": exam.end_at < now,
        "is_important": exam.is_important,
        "reminder_offsets": exam.reminder_offsets,
        "tags": serialize_tags(tags),
        "display_color": display_color([t.color for t in tags], EXAM_COLOR_FALLBACK),
        "conflicts": conflicts or [],
    }
