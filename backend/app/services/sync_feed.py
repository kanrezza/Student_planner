"""Dữ liệu cho mac-agent (contracts/calendar-sync.md, research R5).

Trạng thái mong muốn (feed) và long-poll chờ thay đổi.

Chỉ gồm các trường tối thiểu cho lời nhắc (FR-052, constitution IV): tiêu đề, phòng, thời gian,
báo trước. Không có ghi chú, giảng viên, mã lớp, nhãn.
"""

import hashlib
import json
import time as clock
from datetime import datetime, timedelta

from sqlalchemy import select

from app.extensions import db
from app.lib.timeutil import TZ, combine, iso
from app.models import ClassSession, SyncState, Task
from app.services.reminders import get_settings, session_alarm_minutes, task_alarm_at
from app.services.tasks import due_at

CONTAINER_NAME = "Lịch Học Cá Nhân"
OVERDUE_DAYS_KEPT = 7
MAX_WAIT_SECONDS = 25


def fingerprint(item: dict) -> str:
    content = {k: v for k, v in item.items() if k != "fingerprint"}
    raw = json.dumps(content, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def _with_fingerprint(item: dict) -> dict:
    return {**item, "fingerprint": fingerprint(item)}


def build_feed(now: datetime) -> dict:
    settings = get_settings()
    start_of_today = combine(now.astimezone(TZ).date(), datetime.min.time())
    sessions = db.session.scalars(
        select(ClassSession)
        .where(ClassSession.is_cancelled.is_(False), ClassSession.start_at >= start_of_today)
        .order_by(ClassSession.start_at)
    )
    events = [
        _with_fingerprint(
            {
                "sync_key": f"session:{s.id}",
                "title": s.subject.name,
                "location": s.room,
                "start_at": iso(s.start_at),
                "end_at": iso(s.end_at),
                "alarms_minutes_before": session_alarm_minutes(s, settings),
            }
        )
        for s in sessions
    ]
    tasks = db.session.scalars(
        select(Task)
        .where(
            Task.completed_at.is_(None),
            Task.due_date.is_not(None),
            Task.due_date >= start_of_today.date() - timedelta(days=OVERDUE_DAYS_KEPT),
        )
        .order_by(Task.due_date, Task.due_time)
    )
    reminders = []
    for task in tasks:
        alarm = task_alarm_at(task, settings)
        reminders.append(
            _with_fingerprint(
                {
                    "sync_key": f"task:{task.id}",
                    "title": task.title,
                    "due_at": iso(due_at(task)),
                    "due_has_time": task.due_time is not None,
                    "alarm_at": iso(alarm) if alarm else None,
                }
            )
        )
    return {
        "revision": current_revision(),
        "sync_enabled": settings.calendar_sync_enabled,
        "calendar_name": CONTAINER_NAME,
        "reminder_list_name": CONTAINER_NAME,
        "events": events,
        "reminders": reminders,
    }


def current_revision() -> int:
    return db.session.scalar(select(SyncState.revision).where(SyncState.id == 1))


def wait_for_change(after: int, wait: int) -> int:
    """Chờ tối đa `wait` giây cho tới khi revision > `after`.

    Ở mức READ COMMITTED, mỗi câu lệnh thấy dữ liệu mới nhất đã commit.
    """
    deadline = clock.monotonic() + min(max(wait, 0), MAX_WAIT_SECONDS)
    while True:
        revision = current_revision()
        if revision > after or clock.monotonic() >= deadline:
            return revision
        db.session.rollback()  # kết thúc transaction đọc để không giữ khoá/snapshot
        clock.sleep(1)
