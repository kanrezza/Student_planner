from datetime import datetime, timedelta

from lichhoc_agent.calendar_store import all_day_range, event_range


def test_all_day_end_is_after_start():
    for raw in ("2026-11-05", "2026-11-05T00:00:00+07:00", "2026-11-05T13:30:00+07:00"):
        start, end = all_day_range(raw)
        s, e = datetime.fromisoformat(start), datetime.fromisoformat(end)
        assert e > s
        assert (s.hour, s.minute, s.second) == (0, 0, 0)
        assert e - s == timedelta(days=1, seconds=-1)


def test_event_range_keeps_valid_end():
    start, end = "2026-11-16T06:45:00+07:00", "2026-11-16T09:25:00+07:00"
    assert event_range(start, end) == (start, end)


def test_event_range_fixes_missing_or_equal_or_reversed_end():
    start = "2026-11-16T06:45:00+07:00"
    expected = "2026-11-16T07:45:00+07:00"
    assert event_range(start, None) == (start, expected)
    assert event_range(start, start) == (start, expected)
    assert event_range(start, "2026-11-16T06:00:00+07:00") == (start, expected)
