"""Bảng tiết: giờ mặc định từ ca và đổi khoảng tiết sang giờ/ca (feature 004, FR-011 đến FR-015)."""

from datetime import time
from types import SimpleNamespace

import pytest

from app.services.periods import (
    EVENING_PERIODS,
    default_period_times,
    default_periods,
    periods_to_time,
)
from tests.ocr_helpers import shifts as make_shifts


def shifts():
    """Ca 1 06:45–09:25, Ca 2 09:30–12:10, Ca 3 13:00–15:40, Ca 4 15:45–18:25."""
    return make_shifts()


def test_default_period_times_for_a_160_minute_shift():
    assert default_period_times(time(6, 45), time(9, 25)) == [
        (time(6, 45), time(7, 35)),
        (time(7, 40), time(8, 30)),
        (time(8, 35), time(9, 25)),
    ]


def test_default_periods_match_the_documented_table():
    periods = default_periods(shifts())
    assert periods[1] == (time(6, 45), time(7, 35))
    assert periods[3] == (time(8, 35), time(9, 25))
    assert periods[4] == (time(9, 30), time(10, 20))
    assert periods[6] == (time(11, 20), time(12, 10))
    assert periods[7] == (time(13, 0), time(13, 50))
    assert periods[12] == (time(17, 35), time(18, 25))
    assert {n: periods[n] for n in (16, 17, 18)} == EVENING_PERIODS
    assert periods[16] == (time(21, 5), time(21, 20))
    assert periods[18] == (time(21, 40), time(22, 0))
    assert not {13, 14, 15} & periods.keys()


def test_shift_of_other_length_ends_exactly_at_shift_end():
    # 100 phút → (100 − 10) / 3 = 30 phút mỗi tiết, tiết cuối kéo dài tới đúng giờ kết thúc
    result = default_period_times(time(8, 0), time(9, 40))
    assert result[0] == (time(8, 0), time(8, 30))
    assert result[1] == (time(8, 35), time(9, 5))
    assert result[2] == (time(9, 10), time(9, 40))


def test_too_short_shift_has_no_periods():
    assert default_period_times(time(8, 0), time(8, 20)) == []


def test_only_first_four_shifts_get_periods():
    extra = SimpleNamespace(id=9, position=5, start_time=time(19, 0), end_time=time(21, 40))
    periods = default_periods([*shifts(), extra])
    assert 13 not in periods and 15 not in periods


@pytest.mark.parametrize(
    ("first", "last", "shift_ids", "start", "end"),
    [
        (1, 3, (1, 1), time(6, 45), time(9, 25)),  # đúng Ca 1
        (4, 6, (2, 2), time(9, 30), time(12, 10)),  # đúng Ca 2
        (1, 6, (1, 2), time(6, 45), time(12, 10)),  # dãy Ca 1–2
        (10, 12, (4, 4), time(15, 45), time(18, 25)),
        (1, 2, None, time(6, 45), time(8, 30)),  # tiết lẻ → giờ tuỳ chỉnh
        (2, 4, None, time(7, 40), time(10, 20)),
        (16, 18, None, time(21, 5), time(22, 0)),  # ngoài 4 ca
    ],
)
def test_periods_to_time(first, last, shift_ids, start, end):
    result = periods_to_time(first, last, default_periods(shifts()), shifts())
    assert result.error is None
    assert (result.start_time, result.end_time) == (start, end)
    assert result.shift == shift_ids


def test_period_without_time_is_an_error_with_its_range():
    result = periods_to_time(13, 15, default_periods(shifts()), shifts())
    assert result.error == "Chưa có giờ cho tiết 13–15"
    assert result.start_time is None and result.shift is None
    assert periods_to_time(13, 13, default_periods(shifts()), shifts()).error == (
        "Chưa có giờ cho tiết 13"
    )


def test_manual_period_times_are_used_for_custom_ranges():
    periods = default_periods(shifts())
    periods[2] = (time(7, 40), time(8, 25))  # người dùng sửa tiết 2
    result = periods_to_time(1, 2, periods, shifts())
    assert (result.start_time, result.end_time) == (time(6, 45), time(8, 25))
