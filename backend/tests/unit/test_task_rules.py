from datetime import date, datetime, time
from types import SimpleNamespace

from app.lib.timeutil import TZ, combine
from app.services.tasks import due_at, is_overdue, sort_key


def task(due_date=None, due_time=None, priority=2, completed_at=None, id=1):
    return SimpleNamespace(
        id=id, due_date=due_date, due_time=due_time, priority=priority, completed_at=completed_at
    )


def test_due_at_uses_time_or_end_of_day():
    assert due_at(task(date(2026, 11, 10), time(17, 0))) == combine(date(2026, 11, 10), time(17, 0))
    assert due_at(task(date(2026, 11, 10))) == combine(date(2026, 11, 10), time(23, 59))
    assert due_at(task()) is None


def test_is_overdue_only_when_not_completed_and_past():
    now = datetime(2026, 11, 10, 18, 0, tzinfo=TZ)
    assert is_overdue(task(date(2026, 11, 10), time(17, 0)), now)
    assert not is_overdue(task(date(2026, 11, 10)), now)  # hạn 23:59 chưa tới
    assert not is_overdue(task(date(2026, 11, 9), completed_at=now), now)
    assert not is_overdue(task(), now)


def test_sort_by_due_then_priority_with_no_due_last():
    items = [
        task(None, priority=1, id=1),
        task(date(2026, 11, 12), priority=3, id=2),
        task(date(2026, 11, 10), time(9, 0), priority=3, id=3),
        task(date(2026, 11, 12), priority=1, id=4),
        task(date(2026, 11, 10), time(9, 0), priority=1, id=5),
    ]
    assert [t.id for t in sorted(items, key=sort_key)] == [5, 3, 4, 2, 1]
