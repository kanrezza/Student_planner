from pydantic import Field, field_validator

from app.lib.text import nfc
from app.schemas.common import HHMM, ApiModel


class SettingsOut(ApiModel):
    session_reminder_minutes: int
    task_reminder_minutes: int
    date_only_task_reminder_time: HHMM
    calendar_sync_enabled: bool
    calendar_sync_prompted: bool
    auto_deadline_evening_from: HHMM
    auto_deadline_due_time: HHMM
    auto_deadline_excluded_keywords: list[str]
    important_reminder_offsets: list[int]
    exam_extra_reminder_offsets: list[int]
    exam_reminder_minutes: int
    daily_digest_enabled: bool
    daily_digest_time: HHMM
    daily_digest_overdue_only: bool


def _offsets(value: list[int] | None, low: int, high: int, label: str) -> list[int] | None:
    if value is None:
        return None
    if any(v < 0 for v in value):
        raise ValueError("Mốc nhắc phải là số phút ≥ 0")
    cleaned = sorted(set(value), reverse=True)
    if not low <= len(cleaned) <= high:
        raise ValueError(f"{label} cần từ {low} đến {high} mốc")
    return cleaned


class SettingsPatch(ApiModel):
    """Mọi trường tuỳ chọn; chỉ cập nhật trường được gửi."""

    session_reminder_minutes: int | None = Field(default=None, ge=0)
    task_reminder_minutes: int | None = Field(default=None, ge=0)
    date_only_task_reminder_time: HHMM | None = None
    calendar_sync_enabled: bool | None = None
    calendar_sync_prompted: bool | None = None
    auto_deadline_evening_from: HHMM | None = None
    auto_deadline_due_time: HHMM | None = None
    auto_deadline_excluded_keywords: list[str] | None = None
    important_reminder_offsets: list[int] | None = None
    exam_extra_reminder_offsets: list[int] | None = None
    exam_reminder_minutes: int | None = Field(default=None, ge=0)
    daily_digest_enabled: bool | None = None
    daily_digest_time: HHMM | None = None
    daily_digest_overdue_only: bool | None = None

    @field_validator("important_reminder_offsets")
    @classmethod
    def _important(cls, value):
        return _offsets(value, 1, 6, "Mục quan trọng")

    @field_validator("exam_extra_reminder_offsets")
    @classmethod
    def _exam_extra(cls, value):
        return _offsets(value, 0, 3, "Buổi thi quan trọng")

    @field_validator("auto_deadline_excluded_keywords")
    @classmethod
    def _keywords(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        cleaned = [nfc(k) for k in value]
        if any(not k for k in cleaned):
            raise ValueError("Từ khoá môn ngoại lệ không được để trống")
        return list(dict.fromkeys(cleaned))  # bỏ trùng, giữ thứ tự
