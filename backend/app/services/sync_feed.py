"""Dữ liệu cho mac-agent (contracts/calendar-sync.md, research R5).

Trạng thái mong muốn (feed) và long-poll chờ thay đổi.

Chỉ gồm các trường tối thiểu cho lời nhắc (FR-052, constitution IV): tiêu đề, phòng, thời gian,
báo trước, mức quan trọng và bản tóm tắt hằng ngày. Không có ghi chú, giảng viên, mã lớp, nhãn.
"""

import hashlib
import json
import time as clock
from datetime import datetime, timedelta

from sqlalchemy import select

from app.extensions import db
from app.lib.timeutil import TZ, combine, iso
from app.models import ClassSession, Exam, SyncState, Task
from app.services.digest import DAYS_AHEAD, digests_for_range
from app.services.reminders import (
    exam_alarm_offsets,
    get_settings,
    session_alarm_minutes,
    task_alarm_times,
)
from app.services.tasks import active_tasks, due_at

CONTAINER_NAME = "Lịch Học Cá Nhân"
OVERDUE_DAYS_KEPT = 7
STAR = "★ "
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
                "title": _star(s.subject.name, s.is_important),
                "location": s.room,
                "start_at": iso(s.start_at),
                "end_at": iso(s.end_at),
                "important": s.is_important,
                "alarms_minutes_before": session_alarm_minutes(s, settings),
            }
        )
        for s in sessions
    ]
    # Buổi thi: không có số báo danh, hình thức thi, mã học phần (FR-064, constitution IV).
    exams = db.session.scalars(
        select(Exam).where(Exam.start_at >= start_of_today).order_by(Exam.start_at)
    )
    events += [
        _with_fingerprint(
            {
                "sync_key": f"exam:{e.id}",
                "title": _star(f"Thi: {e.course_name}", e.is_important),
                "location": e.room,
                "start_at": iso(e.start_at),
                "end_at": iso(e.end_at),
                "important": e.is_important,
                "alarms_minutes_before": exam_alarm_offsets(e, settings),
            }
        )
        for e in exams
    ]
    tasks = db.session.scalars(
        active_tasks()
        .where(
            Task.completed_at.is_(None),
            Task.due_date.is_not(None),
            Task.due_date >= start_of_today.date() - timedelta(days=OVERDUE_DAYS_KEPT),
        )
        .order_by(Task.due_date, Task.due_time)
    )
    reminders = []
    for task in tasks:
        reminders.append(
            _with_fingerprint(
                {
                    "sync_key": f"task:{task.id}",
                    "title": task.title,
                    "due_at": iso(due_at(task)),
                    "due_has_time": task.due_time is not None,
                    "important": task.is_important,
                    # Mốc nhắc đã qua không còn tác dụng; gửi sang Lời nhắc chỉ khiến nó hiện giờ
                    # lúc đồng bộ thay vì giờ nhắc đã đặt (ví dụ task chỉ có ngày tạo sau 08:00).
                    "alarms_at": [iso(t) for t in task_alarm_times(task, settings) if t >= now],
                }
            )
        )
    digests = [
        _with_fingerprint(
            {
                "sync_key": f"digest:{d.date.isoformat()}",
                "date": d.date.isoformat(),
                "title": d.title,
                "notes": "\n".join(d.lines),
                "alarm_at": iso(d.fire_at),
            }
        )
        for d in digests_for_range(start_of_today.date(), DAYS_AHEAD, settings)
    ]
    return {
        "revision": current_revision(),
        "sync_enabled": settings.calendar_sync_enabled,
        "calendar_name": CONTAINER_NAME,
        "reminder_list_name": CONTAINER_NAME,
        "events": events,
        "reminders": reminders,
        "digests": digests,
    }


def _star(title: str, important: bool) -> str:
    return STAR + title if important else title


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
