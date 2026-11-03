from datetime import time
from types import SimpleNamespace

from app.services.shifts import match_shift_range, resolve_range, shift_label

CA = [
    SimpleNamespace(id=1, name="Ca 1", position=1, start_time=time(6, 45), end_time=time(9, 25)),
    SimpleNamespace(id=2, name="Ca 2", position=2, start_time=time(9, 35), end_time=time(12, 10)),
    SimpleNamespace(id=3, name="Ca 3", position=3, start_time=time(13, 0), end_time=time(15, 40)),
    SimpleNamespace(id=4, name="Ca 4", position=4, start_time=time(15, 45), end_time=time(18, 25)),
]


def test_resolve_range():
    assert resolve_range(CA[0], CA[1]) == (time(6, 45), time(12, 10))
    assert resolve_range(CA[2], CA[2]) == (time(13, 0), time(15, 40))


def test_match_single_shift_with_tolerance():
    assert match_shift_range(time(9, 35), time(12, 10), CA) == (2, 2)
    assert match_shift_range(time(9, 31), time(12, 14), CA) == (2, 2)  # lệch 4 phút
    assert match_shift_range(time(9, 29), time(12, 10), CA) is None  # lệch 6 phút


def test_match_consecutive_range_and_none():
    assert match_shift_range(time(6, 45), time(12, 10), CA) == (1, 2)
    assert match_shift_range(time(13, 0), time(18, 25), CA) == (3, 4)
    assert match_shift_range(time(20, 0), time(21, 30), CA) is None


def test_shift_label():
    assert shift_label(CA[0], CA[0]) == "Ca 1"
    assert shift_label(CA[0], CA[1]) == "Ca 1–2"
    assert shift_label(None, None) is None
