"""Thời điểm nhắc (FR-021 đến FR-023) và danh sách nhắc cho trình duyệt (dự phòng khi chưa đồng bộ).

Quy tắc `reminder_minutes` (môn học, task): NULL = theo cài đặt mặc định; -1 = tắt nhắc (mọi task,
kể cả task chỉ có ngày); số ≥ 0 = số phút báo trước (chỉ có tác dụng với buổi học và task có giờ).
"""

from datetime import datetime, timedelta

from sqlalchemy import select

from app.extensions import db
from app.lib.timeutil import TZ, combine
from app.models import ClassSession, Settings, Task
from app.services.tasks import due_at

OFF = -1
CATCH_UP = timedelta(minutes=1)  # nhắc đã qua quá 1 phút thì bỏ, không hiện dồn


def get_settings() -> Settings:
    return db.session.get(Settings, 1)


def session_alarm_minutes(session, settings) -> list[int]:
    """Danh sách số phút báo trước của một buổi học (rỗng = không nhắc)."""
    if session.is_cancelled:
        return []
    minutes = session.subject.reminder_minutes
    if minutes == OFF:
        return []
    return [settings.session_reminder_minutes if minutes is None else minutes]


def task_alarm_at(task, settings) -> datetime | None:
    if task.completed_at is not None or task.due_date is None or task.reminder_minutes == OFF:
        return None
    if task.due_time is None:
        return combine(task.due_date, settings.date_only_task_reminder_time)
    minutes = (
        settings.task_reminder_minutes if task.reminder_minutes is None else task.reminder_minutes
    )
    return due_at(task) - timedelta(minutes=minutes)


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
        for minutes in session_alarm_minutes(s, settings):
            fire = s.start_at - timedelta(minutes=minutes)
            if now - CATCH_UP <= fire <= window_end:
                room = f" · Phòng {s.room}" if s.room else ""
                items.append(
                    {
                        "sync_key": f"session:{s.id}",
                        "kind": "session",
                        "title": s.subject.name,
                        "body": f"{_fmt_time(s.start_at)} – {_fmt_time(s.end_at)}{room}",
                        "fire_at": fire.astimezone(TZ).isoformat(timespec="seconds"),
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
        fire = task_alarm_at(task, settings)
        if fire is not None and now - CATCH_UP <= fire <= window_end:
            when = due_at(task).astimezone(TZ)
            items.append(
                {
                    "sync_key": f"task:{task.id}",
                    "kind": "task",
                    "title": task.title,
                    "body": f"Hạn {when:%d/%m}" + (f" lúc {when:%H:%M}" if task.due_time else ""),
                    "fire_at": fire.astimezone(TZ).isoformat(timespec="seconds"),
                }
            )
    return sorted(items, key=lambda i: i["fire_at"])
