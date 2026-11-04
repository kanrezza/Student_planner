from datetime import date, time
from types import SimpleNamespace

from app.lib.timeutil import combine
from app.services.exams import (
    Interval,
    duplicate_key,
    duration_from_format,
    find_conflicts,
    is_duplicate,
    is_past,
    resolve_offsets,
)

SETTINGS = SimpleNamespace(
    important_reminder_offsets=[1440, 180, 60, 15],
    exam_extra_reminder_offsets=[10080],
    exam_reminder_minutes=60,
)
DAY = date(2026, 11, 20)


def at(hh, mm):
    return combine(DAY, time(hh, mm))


def test_duration_from_format():
    assert duration_from_format("Trắc nghiệm trên máy 60p") == 60
    assert duration_from_format("Tự luận 90 phút") == 90
    assert duration_from_format("Bài tập lớn") is None
    assert duration_from_format(None) is None
    assert duration_from_format("") is None


def test_resolve_offsets_defaults():
    assert resolve_offsets(None, True, SETTINGS) == [10080, 1440, 180, 60, 15]
    assert resolve_offsets(None, False, SETTINGS) == [60]


def test_resolve_offsets_custom_and_off():
    assert resolve_offsets([], True, SETTINGS) == []
    assert resolve_offsets([120], True, SETTINGS) == [120]
    assert resolve_offsets([15, 120, 120], False, SETTINGS) == [120, 15]


def test_find_conflicts_overlap_and_touching():
    session = Interval("session", 1, "Giải tích", at(7, 0), at(9, 25))
    exam = Interval("exam", 2, "Đại số", at(8, 0), at(9, 0))
    assert find_conflicts(at(8, 30), at(9, 30), [session, exam]) == [session, exam]
    # chạm mép: kết thúc 09:25, bắt đầu 09:25 → không trùng
    assert find_conflicts(at(9, 25), at(10, 25), [session]) == []
    assert find_conflicts(at(5, 0), at(7, 0), [session]) == []


def test_is_past_uses_end_time():
    assert is_past(at(9, 0), at(9, 1))
    assert not is_past(at(9, 0), at(9, 0))
    assert not is_past(at(9, 0), at(8, 0))


def test_duplicate_same_code_day_start_attempt():
    a = duplicate_key("CSE703057", "Tối ưu hóa", DAY, time(18, 30), 1)
    b = duplicate_key("cse703057", "Toi uu hoa (tên khác)", DAY, time(18, 30), 1)
    assert is_duplicate(a, b)  # cả hai có mã → so theo mã


def test_different_attempt_is_not_duplicate():
    a = duplicate_key("CSE703057", "Tối ưu hóa", DAY, time(18, 30), 1)
    b = duplicate_key("CSE703057", "Tối ưu hóa", DAY, time(18, 30), 2)
    assert not is_duplicate(a, b)


def test_without_code_compare_by_name_ci_nfc():
    import unicodedata

    nfd = unicodedata.normalize("NFD", "Tối ưu hóa")
    a = duplicate_key(None, "TỐI ƯU HÓA", DAY, time(18, 30))
    b = duplicate_key("CSE703057", nfd, DAY, time(18, 30))  # một bên thiếu mã → so theo tên
    assert is_duplicate(a, b)
    assert not is_duplicate(a, duplicate_key(None, "Tối ưu hóa", DAY, time(19, 0)))
