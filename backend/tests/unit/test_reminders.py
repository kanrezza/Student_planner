from datetime import date, datetime, time, timedelta
from types import SimpleNamespace

from app.lib.timeutil import TZ, combine
from app.services.reminders import alarm_offsets, session_alarm_minutes, task_alarm_times

SETTINGS = SimpleNamespace(
    session_reminder_minutes=15,
    task_reminder_minutes=60,
    date_only_task_reminder_time=time(8, 0),
    important_reminder_offsets=[1440, 180, 60, 15],
    auto_deadline_eve_reminder_time=time(20, 0),
)


def session(reminder_minutes=None, cancelled=False, important=False, override=None):
    subject = SimpleNamespace(reminder_minutes=reminder_minutes, is_important=important)
    effective = important if override is None else override
    return SimpleNamespace(is_cancelled=cancelled, subject=subject, is_important=effective)


def task(
    due_date=date(2026, 11, 10),
    due_time=time(17, 0),
    reminder_minutes=None,
    done=False,
    important=False,
    auto=False,
):
    return SimpleNamespace(
        is_auto=auto,
        due_date=due_date,
        due_time=due_time,
        reminder_minutes=reminder_minutes,
        is_important=important,
        completed_at=datetime(2026, 11, 9, tzinfo=TZ) if done else None,
    )


def test_session_alarm_minutes():
    assert session_alarm_minutes(session(), SETTINGS) == [15]
    assert session_alarm_minutes(session(30), SETTINGS) == [30]
    assert session_alarm_minutes(session(0), SETTINGS) == [0]
    assert session_alarm_minutes(session(-1), SETTINGS) == []
    assert session_alarm_minutes(session(cancelled=True), SETTINGS) == []


def test_important_session_gets_all_offsets():
    assert session_alarm_minutes(session(important=True), SETTINGS) == [1440, 180, 60, 15]
    # Mốc riêng của môn được cộng thêm; mốc trùng chỉ một lần.
    assert session_alarm_minutes(session(30, important=True), SETTINGS) == [1440, 180, 60, 30, 15]
    assert session_alarm_minutes(session(15, important=True), SETTINGS) == [1440, 180, 60, 15]
    # "Không nhắc" thắng cả mục quan trọng.
    assert session_alarm_minutes(session(-1, important=True), SETTINGS) == []


def test_session_override_beats_subject():
    assert session_alarm_minutes(session(important=True, override=False), SETTINGS) == [15]
    assert session_alarm_minutes(session(important=False, override=True), SETTINGS) == [
        1440,
        180,
        60,
        15,
    ]


def test_alarm_offsets_sorted_descending_and_deduplicated():
    s = SimpleNamespace(important_reminder_offsets=[15, 60, 60])
    assert alarm_offsets(None, True, 10, s) == [60, 15]
    assert alarm_offsets(None, False, 10, s) == [10]


def test_task_with_time():
    due = combine(date(2026, 11, 10), time(17, 0))
    assert task_alarm_times(task(), SETTINGS) == [due - timedelta(minutes=60)]
    assert task_alarm_times(task(reminder_minutes=10), SETTINGS) == [due - timedelta(minutes=10)]
    assert task_alarm_times(task(reminder_minutes=-1), SETTINGS) == []


def test_important_task_with_time_has_four_alarms_ascending():
    due = combine(date(2026, 11, 10), time(17, 0))
    assert task_alarm_times(task(important=True), SETTINGS) == [
        due - timedelta(minutes=m) for m in (1440, 180, 60, 15)
    ]
    assert task_alarm_times(task(important=True, reminder_minutes=-1), SETTINGS) == []


def test_task_date_only_uses_morning_time():
    morning = combine(date(2026, 11, 10), time(8, 0))
    assert task_alarm_times(task(due_time=None), SETTINGS) == [morning]
    assert task_alarm_times(task(due_time=None, reminder_minutes=30), SETTINGS) == [morning]
    assert task_alarm_times(task(due_time=None, reminder_minutes=-1), SETTINGS) == []


def test_important_date_only_task_uses_whole_days():
    morning = combine(date(2026, 11, 10), time(8, 0))
    assert task_alarm_times(task(due_time=None, important=True), SETTINGS) == [
        morning - timedelta(days=1),
        morning,
    ]
    two_days = SimpleNamespace(**{**vars(SETTINGS), "important_reminder_offsets": [2880, 60]})
    assert task_alarm_times(task(due_time=None, important=True), two_days) == [
        morning - timedelta(days=2),
        morning,
    ]


def test_no_reminder_for_completed_or_undated_tasks():
    assert task_alarm_times(task(done=True), SETTINGS) == []
    assert task_alarm_times(task(due_date=None, due_time=None), SETTINGS) == []


def test_auto_deadline_gets_eve_reminder():
    due = combine(date(2026, 11, 15), time(8, 0))  # Chủ Nhật
    eve = combine(date(2026, 11, 14), time(20, 0))
    auto = task(due_date=date(2026, 11, 15), due_time=time(8, 0), auto=True)
    assert task_alarm_times(auto, SETTINGS) == [eve, due - timedelta(minutes=60)]
    later = SimpleNamespace(**{**vars(SETTINGS), "auto_deadline_eve_reminder_time": time(21, 30)})
    assert task_alarm_times(auto, later)[0] == combine(date(2026, 11, 14), time(21, 30))
    off = SimpleNamespace(**{**vars(SETTINGS), "auto_deadline_eve_reminder_time": None})
    assert task_alarm_times(auto, off) == [due - timedelta(minutes=60)]
    # Tắt nhắc của task thắng mốc tối hôm trước; task thường không có mốc này.
    muted = task(due_date=date(2026, 11, 15), due_time=time(8, 0), auto=True, reminder_minutes=-1)
    assert task_alarm_times(muted, SETTINGS) == []
    plain = task(due_date=date(2026, 11, 15), due_time=time(8, 0))
    assert task_alarm_times(plain, SETTINGS) == [due - timedelta(minutes=60)]


def test_eve_reminder_not_duplicated():
    # Mốc 12 giờ trước 08:00 CN trùng đúng 20:00 Thứ Bảy → chỉ một lần.
    auto = task(due_date=date(2026, 11, 15), due_time=time(8, 0), auto=True, reminder_minutes=720)
    assert task_alarm_times(auto, SETTINGS) == [combine(date(2026, 11, 14), time(20, 0))]
