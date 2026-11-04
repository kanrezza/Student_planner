"""Thời điểm nhắc (FR-021 đến FR-023) và danh sách nhắc cho trình duyệt (dự phòng khi chưa đồng bộ).

Quy tắc `reminder_minutes` (môn học, task): NULL = theo cài đặt mặc định; -1 = tắt nhắc (mọi task,
kể cả task chỉ có ngày); số ≥ 0 = số phút báo trước (chỉ có tác dụng với buổi học và task có giờ).
"""

from datetime import datetime, timedelta

from sqlalchemy import select

from app.extensions import db
from app.lib.timeutil import TZ, combine
from app.models import ClassSession, Settings, Task
from app.services.digest import digests_for_range
from app.services.tasks import due_at

OFF = -1
CATCH_UP = timedelta(minutes=1)  # nhắc đã qua quá 1 phút thì bỏ, không hiện dồn


def get_settings() -> Settings:
    return db.session.get(Settings, 1)


def alarm_offsets(
    item_minutes: int | None, is_important: bool, default: int, settings
) -> list[int]:
    """Phút báo trước theo data-model "Quy tắc mốc nhắc" (FR-022, FR-068); giảm dần, không trùng.

    `item_minutes`: mốc riêng của mục (None = mặc định, -1 = tắt mọi mốc).
    """
    if item_minutes == OFF:
        return []
    if not is_important:
        return [default if item_minutes is None else item_minutes]
    offsets = set(settings.important_reminder_offsets)
    if item_minutes is not None:
        offsets.add(item_minutes)
    return sorted(offsets, reverse=True)


def session_alarm_minutes(session, settings) -> list[int]:
    """Danh sách số phút báo trước của một buổi học (rỗng = không nhắc)."""
    if session.is_cancelled:
        return []
    return alarm_offsets(
        session.subject.reminder_minutes,
        session.is_important,
        settings.session_reminder_minutes,
        settings,
    )


def task_alarm_times(task, settings) -> list[datetime]:
    """Các thời điểm nhắc của task, tăng dần (rỗng = không nhắc)."""
    if task.completed_at is not None or task.due_date is None or task.reminder_minutes == OFF:
        return []
    if task.due_time is None:
        # Task chỉ có ngày: nhắc lúc giờ cố định; mục quan trọng thêm các ngày ứng với mốc ≥ 1 ngày.
        morning = combine(task.due_date, settings.date_only_task_reminder_time)
        days = {0}
        if task.is_important:
            days |= {m // 1440 for m in settings.important_reminder_offsets if m >= 1440}
        return _with_eve(task, settings, {morning - timedelta(days=d) for d in days})
    offsets = alarm_offsets(
        task.reminder_minutes, task.is_important, settings.task_reminder_minutes, settings
    )
    deadline = due_at(task)
    return _with_eve(task, settings, {deadline - timedelta(minutes=m) for m in offsets})


def _with_eve(task, settings, times: set[datetime]) -> list[datetime]:
    """Task tự tạo: thêm mốc tối hôm trước ngày hạn (FR-071); thời điểm trùng chỉ một lần."""
    eve = settings.auto_deadline_eve_reminder_time
    if task.is_auto and eve is not None:
        times.add(combine(task.due_date - timedelta(days=1), eve))
    return sorted(times)


def _key(kind: str, item_id: int, minutes: int, count: int) -> str:
    """`session:12`, hoặc `session:12:1440` khi mục có nhiều mốc (contracts/rest-api.md)."""
    return f"{kind}:{item_id}:{minutes}" if count > 1 else f"{kind}:{item_id}"


def _fmt_time(dt: datetime) -> str:
    return dt.astimezone(TZ).strftime("%H:%M")


def upcoming(now: datetime, hours: int) -> list[dict]:
    """Nhắc trong `hours` giờ tới, dùng cho thông báo trình duyệt. Rỗng khi đồng bộ đang bật."""
    settings = get_settings()
    if settings.calendar_sync_enabled:
        return []
    window_end = now + timedelta(hours=hours)
    items: list[dict] = []

    sessions = db.session.scalars(
        select(ClassSession).where(
            ClassSession.is_cancelled.is_(False),
            ClassSession.start_at >= now - CATCH_UP,
            ClassSession.start_at <= window_end + timedelta(days=1),
        )
    )
    for s in sessions:
        offsets = session_alarm_minutes(s, settings)
        for minutes in offsets:
            fire = s.start_at - timedelta(minutes=minutes)
            if now - CATCH_UP <= fire <= window_end:
                room = f" · Phòng {s.room}" if s.room else ""
                items.append(
                    {
                        "sync_key": _key("session", s.id, minutes, len(offsets)),
                        "kind": "session",
                        "title": s.subject.name,
                        "body": f"{_fmt_time(s.start_at)} – {_fmt_time(s.end_at)}{room}",
                        "fire_at": fire.astimezone(TZ).isoformat(timespec="seconds"),
                        "important": s.is_important,
                    }
                )

    tasks = db.session.scalars(
        select(Task).where(
            Task.completed_at.is_(None),
            Task.due_date.is_not(None),
            Task.due_date <= window_end.date() + timedelta(days=1),
            Task.due_date >= (now - timedelta(days=1)).date(),
        )
    )
    for task in tasks:
        times = task_alarm_times(task, settings)
        when = due_at(task).astimezone(TZ) if times else None
        for fire in times:
            if not (now - CATCH_UP <= fire <= window_end):
                continue
            minutes = int((due_at(task) - fire).total_seconds() // 60)
            items.append(
                {
                    "sync_key": _key("task", task.id, minutes, len(times)),
                    "kind": "task",
                    "title": task.title,
                    "body": f"Hạn {when:%d/%m}" + (f" lúc {when:%H:%M}" if task.due_time else ""),
                    "fire_at": fire.astimezone(TZ).isoformat(timespec="seconds"),
                    "important": task.is_important,
                }
            )

    # Bản tóm tắt hằng ngày (FR-065) của các ngày trong cửa sổ.
    first_day = (now - CATCH_UP).astimezone(TZ).date()
    days = (window_end.astimezone(TZ).date() - first_day).days + 1
    for digest in digests_for_range(first_day, days, settings):
        if now - CATCH_UP <= digest.fire_at <= window_end:
            items.append(
                {
                    "sync_key": f"digest:{digest.date.isoformat()}",
                    "kind": "digest",
                    "title": digest.title,
                    "body": "\n".join(digest.lines),
                    "fire_at": digest.fire_at.astimezone(TZ).isoformat(timespec="seconds"),
                    "important": digest.is_important,
                }
            )
    return sorted(items, key=lambda i: i["fire_at"])
