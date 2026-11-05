"""Schema API sao lưu (feature 003, contracts/rest-api.md)."""

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator

from app.schemas.common import HHMM, ApiModel

Kind = Literal["tu-dong", "thu-cong", "truoc-khoi-phuc"]
DestinationState = Literal["ok", "missing", "no_permission", "icloud_off", "not_writable"]


class BackupConfigPatch(ApiModel):
    """Chỉ cập nhật trường được gửi; `destination_path: null` = quay về thư mục mặc định."""

    enabled: bool | None = None
    schedule_time: HHMM | None = None
    destination_path: str | None = None
    retention_count: int | None = Field(default=None, ge=1, le=365)

    @field_validator("destination_path")
    @classmethod
    def _absolute(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None
        if not value.startswith("/"):
            raise ValueError("Đường dẫn thư mục phải là đường dẫn đầy đủ")
        return value


class JobCreate(ApiModel):
    kind: Literal["backup_now", "restore"]
    source_path: str | None = None

    @field_validator("source_path")
    @classmethod
    def _absolute(cls, value: str | None) -> str | None:
        if value is not None and not value.startswith("/"):
            raise ValueError("Đường dẫn file phải là đường dẫn đầy đủ")
        return value


class JobUpdate(ApiModel):
    state: Literal["running", "done", "failed"]
    step: str | None = None
    message: str | None = None


class BackupFileIn(ApiModel):
    name: str
    path: str
    kind: Kind
    created_at: datetime
    size: int = Field(ge=0)
    location: Literal["local", "icloud"]


class AgentReportIn(ApiModel):
    destination_resolved: str | None = None
    destination_state: DestinationState
    destination_message: str | None = None
    last_attempt_at: datetime | None = None
    last_attempt_ok: bool | None = None
    last_attempt_error: str | None = None
    last_attempt_size: int | None = Field(default=None, ge=0)
    last_success_at: datetime | None = None
    last_success_size: int | None = Field(default=None, ge=0)
    files: list[BackupFileIn] = []
