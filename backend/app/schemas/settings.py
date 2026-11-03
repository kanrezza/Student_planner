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

    @field_validator("auto_deadline_excluded_keywords")
    @classmethod
    def _keywords(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        cleaned = [nfc(k) for k in value]
        if any(not k for k in cleaned):
            raise ValueError("Từ khoá môn ngoại lệ không được để trống")
        return list(dict.fromkeys(cleaned))  # bỏ trùng, giữ thứ tự
