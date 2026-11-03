"""/api/sync/* cho mac-agent (contracts/calendar-sync.md) và /api/reminders/upcoming (FR-021)."""

from datetime import date, timedelta

from flask import Blueprint, request
from pydantic import Field

from app.api.errors import ApiError
from app.api.params import int_arg
from app.extensions import db
from app.lib import timeutil
from app.lib.timeutil import iso
from app.models import AgentStatus
from app.schemas.common import ApiModel
from app.services import digest, reminders, sync_feed

bp = Blueprint("sync", __name__)

AGENT_OFFLINE_AFTER = timedelta(minutes=2)


class AgentStatusIn(ApiModel):
    permission: str = Field(pattern="^(unknown|granted|denied)$")
    icloud_source: str = Field(default="unknown", pattern="^(icloud|local_only|unknown)$")
    last_synced_revision: int = 0
    last_error: str | None = None
    agent_version: str | None = None


def agent_online(status: AgentStatus) -> bool:
    return status.last_seen_at is not None and (
        timeutil.now() - status.last_seen_at <= AGENT_OFFLINE_AFTER
    )


@bp.get("/sync/changes")
def changes():
    after = int_arg("after") or 0
    wait = int_arg("wait") or 0
    revision = sync_feed.wait_for_change(after, wait)
    return {"revision": revision, "sync_enabled": reminders.get_settings().calendar_sync_enabled}


@bp.get("/sync/feed")
def feed():
    return sync_feed.build_feed(timeutil.now())


@bp.put("/sync/agent-status")
def put_agent_status():
    data = AgentStatusIn.model_validate(request.get_json(silent=True) or {})
    status = db.session.get(AgentStatus, 1)
    status.permission = data.permission
    status.icloud_source = data.icloud_source
    status.last_synced_revision = data.last_synced_revision
    status.last_error = data.last_error
    status.last_seen_at = timeutil.now()
    db.session.commit()
    return "", 204


@bp.get("/sync/status")
def sync_status():
    status = db.session.get(AgentStatus, 1)
    return {
        "sync_enabled": reminders.get_settings().calendar_sync_enabled,
        "revision": sync_feed.current_revision(),
        "agent_online": agent_online(status),
        "last_seen_at": iso(status.last_seen_at) if status.last_seen_at else None,
        "permission": status.permission,
        "icloud_source": status.icloud_source,
        "last_synced_revision": status.last_synced_revision,
        "last_error": status.last_error,
    }


@bp.get("/digest")
def digest_preview():
    """Xem trước bản tóm tắt của một ngày (mặc định hôm nay), FR-065."""
    raw = request.args.get("date")
    try:
        day = date.fromisoformat(raw) if raw else timeutil.today()
    except ValueError:
        raise ApiError(
            400, "validation_error", "Dữ liệu chưa hợp lệ", {"date": "Ngày không hợp lệ"}
        ) from None
    # Xem trước luôn tính nội dung, kể cả khi đang tắt thông báo tổng hợp.
    settings = reminders.get_settings()
    found = digest.digest_for_day(day, _EnabledView(settings))
    if found is None:
        return {"date": day.isoformat(), "empty": True}
    return {
        "date": day.isoformat(),
        "empty": False,
        "fire_at": iso(found.fire_at),
        "title": found.title,
        "lines": found.lines,
        "is_important": found.is_important,
    }


class _EnabledView:
    """Bọc cài đặt, coi như thông báo tổng hợp đang bật (chỉ dùng cho xem trước)."""

    def __init__(self, settings):
        self._settings = settings

    daily_digest_enabled = True

    def __getattr__(self, name):
        return getattr(self._settings, name)


@bp.get("/reminders/upcoming")
def upcoming():
    hours = min(max(int_arg("hours") or 24, 1), 72)
    return reminders.upcoming(timeutil.now(), hours)


def sync_notices() -> list[dict]:
    """Cảnh báo trên trang Hôm nay khi đồng bộ đang bật nhưng agent có vấn đề."""
    if not reminders.get_settings().calendar_sync_enabled:
        return []
    status = db.session.get(AgentStatus, 1)
    if status.permission == "denied":
        return [
            {
                "code": "permission_denied",
                "message": "Trình đồng bộ bị từ chối quyền truy cập Lịch/Lời nhắc. Mở Cài đặt hệ "
                "thống → Quyền riêng tư & Bảo mật → Lịch và Lời nhắc, bật cho LichHocAgent.",
            }
        ]
    if not agent_online(status):
        return [
            {
                "code": "agent_offline",
                "message": "Chưa kết nối được trình đồng bộ Lịch trên Mac. Hãy cài hoặc mở lại "
                "LichHocAgent (xem Cài đặt → Nhắc lịch).",
            }
        ]
    if status.icloud_source == "local_only":
        return [
            {
                "code": "no_icloud",
                "message": "Lịch đang lưu trên máy, chưa có iCloud: iPhone sẽ không nhận được "
                "nhắc. Hãy bật iCloud cho Lịch và Lời nhắc.",
            }
        ]
    return []
