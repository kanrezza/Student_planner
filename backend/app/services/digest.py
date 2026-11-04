"""Bản tóm tắt hằng ngày (FR-065, FR-066; data-model "Bản tóm tắt hằng ngày", research R15).

`build_digest` là hàm thuần: nhận dữ liệu đã lọc của một ngày, trả `Digest` hoặc `None` (không gửi).
`digests_for_range` truy vấn database một lần cho cả khoảng ngày.
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy import select

from app.extensions import db
from app.lib.timeutil import TZ, combine
from app.models import ClassSession, Exam, Task
from app.services.shifts import shift_label
from app.services.tasks import active_tasks, due_at

MAX_TASKS_SHOWN = 3
DAYS_AHEAD = 14  # hôm nay + 13 ngày (research R15)
NO_ROOM = "chưa có phòng"


@dataclass(frozen=True)
class DigestSession:
    start_at: datetime
    label: str | None  # "Ca 1" nếu buổi theo ca, None nếu giờ tuỳ chỉnh
    name: str
    room: str | None
    is_important: bool = False


@dataclass(frozen=True)
class DigestExam:
    start_at: datetime
    name: str
    room: str | None
    is_important: bool = True


@dataclass(frozen=True)
class DigestTask:
    title: str
    due_at: datetime
    has_time: bool
    is_important: bool = False


@dataclass(frozen=True)
class Digest:
    date: date
    fire_at: datetime
    title: str
    lines: list[str]
    is_important: bool


def _hhmm(dt: datetime) -> str:
    return dt.astimezone(TZ).strftime("%H:%M")


def _with_room(text: str, room: str | None) -> str:
    return f"{text} {room}" if room else text


def classify_tasks(day: date, tasks) -> tuple[list[DigestTask], list[DigestTask]]:
    """Chia task chưa xong thành (đến hạn trong `day`, quá hạn trước `day`)."""
    start = combine(day, time.min)
    due_today, overdue = [], []
    for task in tasks:
        if task.completed_at is not None or task.due_date is None:
            continue
        item = DigestTask(task.title, due_at(task), task.due_time is not None, task.is_important)
        if task.due_date == day:
            due_today.append(item)
        elif item.due_at < start:
            overdue.append(item)
    return due_today, overdue


def build_digest(
    day: date,
    exams: list[DigestExam],
    sessions: list[DigestSession],
    due_today: list[DigestTask],
    overdue: list[DigestTask],
    settings,
) -> Digest | None:
    if not settings.daily_digest_enabled:
        return None
    if not (exams or sessions or due_today or overdue):
        return None
    if not (exams or sessions or due_today) and not settings.daily_digest_overdue_only:
        return None

    exams = sorted(exams, key=lambda e: e.start_at)
    sessions = sorted(sessions, key=lambda s: s.start_at)
    today_sorted = sorted(due_today, key=lambda t: (not t.has_time, t.due_at))
    overdue_sorted = sorted(overdue, key=lambda t: t.due_at)
    picked = [(t, False) for t in today_sorted] + [(t, True) for t in overdue_sorted]
    shown, remaining = picked[:MAX_TASKS_SHOWN], len(picked) - MAX_TASKS_SHOWN

    lines: list[str] = []
    parts: list[str] = []
    for e in exams:
        lines.append(f"Thi {_hhmm(e.start_at)}: {e.name} – {e.room or NO_ROOM}")
        parts.append(_with_room(f"Thi {e.name} {_hhmm(e.start_at)}", e.room))
    for s in sessions:
        when = f"{s.label} ({_hhmm(s.start_at)})" if s.label else _hhmm(s.start_at)
        lines.append(f"{when}: {s.name} – {s.room or NO_ROOM}")
        parts.append(_with_room(f"{s.label or _hhmm(s.start_at)} {s.name}", s.room))
    titles = []
    for task, is_overdue in shown:
        if is_overdue:
            lines.append(f"{task.title} – quá hạn từ {task.due_at.astimezone(TZ):%d/%m}")
            titles.append(f"{task.title} (quá hạn)")
        else:
            when = f"hạn {_hhmm(task.due_at)}" if task.has_time else "cả ngày"
            lines.append(f"{task.title} – {when}")
            titles.append(task.title)
    more = f"+{remaining} việc khác" if remaining > 0 else ""
    if more:
        lines.append(more)
    if titles:
        parts.append("Việc: " + ", ".join(titles) + (f" {more}" if more else ""))

    important = bool(exams) or any(s.is_important for s in sessions)
    important = important or any(t.is_important for t in [*due_today, *overdue])
    title = ("★ " if important else "") + "Hôm nay: " + " · ".join(parts)
    return Digest(
        date=day,
        fire_at=combine(day, settings.daily_digest_time),
        title=title,
        lines=lines,
        is_important=important,
    )


def _session_info(s: ClassSession) -> DigestSession:
    subject = s.subject
    label = None if s.time_overridden else shift_label(subject.start_shift, subject.end_shift)
    return DigestSession(s.start_at, label, subject.name, s.room, s.is_important)


def digests_for_range(start: date, days: int, settings) -> list[Digest]:
    """Bản tóm tắt không trống của `days` ngày từ `start`; buổi thi đứng đầu (FR-065)."""
    if not settings.daily_digest_enabled:
        return []
    end = start + timedelta(days=days - 1)
    sessions_by_day: dict[date, list[DigestSession]] = {}
    for s in db.session.scalars(
        select(ClassSession).where(
            ClassSession.is_cancelled.is_(False),
            ClassSession.date >= start,
            ClassSession.date <= end,
        )
    ):
        sessions_by_day.setdefault(s.date, []).append(_session_info(s))
    exams_by_day: dict[date, list[DigestExam]] = {}
    for e in db.session.scalars(select(Exam).where(Exam.date >= start, Exam.date <= end)):
        exams_by_day.setdefault(e.date, []).append(
            DigestExam(e.start_at, e.course_name, e.room, e.is_important)
        )
    tasks = list(
        db.session.scalars(
            active_tasks().where(
                Task.completed_at.is_(None), Task.due_date.is_not(None), Task.due_date <= end
            )
        )
    )
    result = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        due_today, overdue = classify_tasks(day, tasks)
        digest = build_digest(
            day,
            exams_by_day.get(day, []),
            sessions_by_day.get(day, []),
            due_today,
            overdue,
            settings,
        )
        if digest is not None:
            result.append(digest)
    return result


def digest_for_day(day: date, settings) -> Digest | None:
    found = digests_for_range(day, 1, settings)
    return found[0] if found else None
