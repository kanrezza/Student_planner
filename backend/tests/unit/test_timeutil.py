from datetime import date, time, timedelta

from app.lib.timeutil import TZ, combine, iso, now, weekday_vn


def test_combine_is_vietnam_time():
    dt = combine(date(2026, 11, 16), time(7, 30))
    assert dt.tzinfo == TZ
    assert dt.utcoffset() == timedelta(hours=7)


def test_iso_has_plus_seven_offset():
    assert iso(combine(date(2026, 11, 16), time(7, 30))) == "2026-11-16T07:30:00+07:00"


def test_iso_converts_other_timezones_to_vietnam():
    from datetime import UTC, datetime

    assert iso(datetime(2026, 11, 16, 0, 30, tzinfo=UTC)) == "2026-11-16T07:30:00+07:00"


def test_weekday_vn_monday_is_1_sunday_is_7():
    assert weekday_vn(date(2026, 11, 16)) == 1  # Thứ Hai
    assert weekday_vn(date(2026, 11, 22)) == 7  # Chủ Nhật


def test_now_is_timezone_aware():
    assert now().utcoffset() == timedelta(hours=7)
