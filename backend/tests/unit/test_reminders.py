from datetime import date, datetime, time, timedelta
from types import SimpleNamespace

from app.lib.timeutil import TZ, combine
from app.services.reminders import session_alarm_minutes, task_alarm_at

SETTINGS = SimpleNamespace(
    session_reminder_minutes=15,
    task_reminder_minutes=60,
    date_only_task_reminder_time=time(8, 0),
)


def session(reminder_minutes=None, cancelled=False):
    return SimpleNamespace(
        is_cancelled=cancelled, subject=SimpleNamespace(reminder_minutes=reminder_minutes)
    )


def task(due_date=date(2026, 11, 10), due_time=time(17, 0), reminder_minutes=None, done=False):
    return SimpleNamespace(
        due_date=due_date,
        due_time=due_time,
        reminder_minutes=reminder_minutes,
        completed_at=datetime(2026, 11, 9, tzinfo=TZ) if done else None,
    )


def test_session_alarm_minutes():
    assert session_alarm_minutes(session(), SETTINGS) == [15]
    assert session_alarm_minutes(session(30), SETTINGS) == [30]
    assert session_alarm_minutes(session(0), SETTINGS) == [0]
    assert session_alarm_minutes(session(-1), SETTINGS) == []
    assert session_alarm_minutes(session(cancelled=True), SETTINGS) == []


def test_task_with_time():
    due = combine(date(2026, 11, 10), time(17, 0))
    assert task_alarm_at(task(), SETTINGS) == due - timedelta(minutes=60)
    assert task_alarm_at(task(reminder_minutes=10), SETTINGS) == due - timedelta(minutes=10)
    assert task_alarm_at(task(reminder_minutes=-1), SETTINGS) is None


def test_task_date_only_uses_morning_time():
    morning = combine(date(2026, 11, 10), time(8, 0))
    assert task_alarm_at(task(due_time=None), SETTINGS) == morning
    assert task_alarm_at(task(due_time=None, reminder_minutes=30), SETTINGS) == morning
    assert task_alarm_at(task(due_time=None, reminder_minutes=-1), SETTINGS) is None


def test_no_reminder_for_completed_or_undated_tasks():
    assert task_alarm_at(task(done=True), SETTINGS) is None
    assert task_alarm_at(task(due_date=None, due_time=None), SETTINGS) is None
