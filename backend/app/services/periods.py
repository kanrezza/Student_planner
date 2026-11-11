"""Bảng tiết: giờ từng tiết suy từ ca, đổi khoảng tiết sang giờ/ca (feature 004, R8, FR-011 đến
FR-015).

Hàm thuần: `default_period_times`, `default_periods`, `periods_to_time`. Phần dùng CSDL ở cuối file.
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy import select

from app.api.errors import ApiError, not_found
from app.extensions import db
from app.models import Period, Shift

PERIODS_PER_SHIFT = 3
BREAK_MINUTES = 5
MIN_PERIOD_MINUTES = 10  # ca quá ngắn để chia thành 3 tiết thì không có tiết mặc định
MAX_SHIFTS_WITH_PERIODS = 4  # ca thứ k chỉ ứng với tiết 3k−2…3k khi k ≤ 4
MIN_PERIOD, MAX_PERIOD = 1, 30
EVENING_PERIODS = {
    16: (time(21, 5), time(21, 20)),
    17: (time(21, 20), time(21, 40)),
    18: (time(21, 40), time(22, 0)),
}

TimeRange = tuple[time, time]


# ---- Hàm thuần ---------------------------------------------------------------------------------


def _minutes_between(start: time, end: time) -> int:
    return (datetime.combine(date.min, end) - datetime.combine(date.min, start)) // timedelta(
        minutes=1
    )


def default_period_times(start: time, end: time) -> list[TimeRange]:
    """3 tiết của một ca: mỗi tiết như nhau, nghỉ 5 phút giữa các tiết; tiết cuối kết thúc đúng giờ
    ca.

    Ca 160 phút (mặc định) → tiết 50 phút. Ca quá ngắn (không đủ chia) → danh sách rỗng.
    """
    total = _minutes_between(start, end)
    each = (total - (PERIODS_PER_SHIFT - 1) * BREAK_MINUTES) // PERIODS_PER_SHIFT
    if each < MIN_PERIOD_MINUTES:
        return []
    result: list[TimeRange] = []
    cursor = datetime.combine(date.min, start)
    for index in range(PERIODS_PER_SHIFT):
        last = index == PERIODS_PER_SHIFT - 1
        finish = datetime.combine(date.min, end) if last else cursor + timedelta(minutes=each)
        result.append((cursor.time(), finish.time()))
        cursor = finish + timedelta(minutes=BREAK_MINUTES)
    return result


def shift_period_numbers(shift_index: int) -> range:
    """Số tiết của ca thứ `shift_index` (đếm từ 1): ca 1 → tiết 1–3, ca 2 → tiết 4–6…"""
    first = (shift_index - 1) * PERIODS_PER_SHIFT + 1
    return range(first, first + PERIODS_PER_SHIFT)


def default_periods(shifts: list[Shift]) -> dict[int, TimeRange]:
    """Bảng tiết mặc định từ các ca (theo `position`) cộng tiết 16–18."""
    periods: dict[int, TimeRange] = {}
    ordered = sorted(shifts, key=lambda s: s.position)[:MAX_SHIFTS_WITH_PERIODS]
    for index, shift in enumerate(ordered, start=1):
        for number, times in zip(
            shift_period_numbers(index),
            default_period_times(shift.start_time, shift.end_time),
            strict=False,
        ):
            periods[number] = times
    periods.update(EVENING_PERIODS)
    return periods


@dataclass(frozen=True)
class PeriodResolution:
    """Kết quả đổi khoảng tiết sang giờ.

    `shift` = (id ca đầu, id ca cuối) khi khoảng tiết trùng đúng một ca hoặc dãy ca liền nhau;
    ngược lại giờ tuỳ chỉnh. `error` có khi thiếu giờ của tiết nào đó.
    """

    start_time: time | None = None
    end_time: time | None = None
    shift: tuple[int, int] | None = None
    error: str | None = None


def describe_periods(first: int, last: int) -> str:
    return f"tiết {first}" if first == last else f"tiết {first}–{last}"


def periods_to_time(
    first: int, last: int, periods: dict[int, TimeRange], shifts: list[Shift]
) -> PeriodResolution:
    """Đổi khoảng tiết [first, last] sang giờ (FR-014).

    - Trùng đúng một ca hoặc dãy ca liền nhau (tiết 3i−2 … 3j của ca i…j) → gắn ca, giờ lấy theo ca.
    - Còn lại → giờ bắt đầu của tiết đầu tới giờ kết thúc của tiết cuối.
    - Tiết nào trong khoảng chưa có giờ → lỗi "Chưa có giờ cho tiết a–b" (FR-015).
    """
    ordered = sorted(shifts, key=lambda s: s.position)[:MAX_SHIFTS_WITH_PERIODS]
    if (first - 1) % PERIODS_PER_SHIFT == 0 and last % PERIODS_PER_SHIFT == 0:
        i, j = (first - 1) // PERIODS_PER_SHIFT, last // PERIODS_PER_SHIFT - 1
        if 0 <= i <= j < len(ordered):
            return PeriodResolution(
                ordered[i].start_time, ordered[j].end_time, (ordered[i].id, ordered[j].id)
            )
    missing = [n for n in range(first, last + 1) if n not in periods]
    if missing:
        return PeriodResolution(error=f"Chưa có giờ cho {describe_periods(first, last)}")
    start, end = periods[first][0], periods[last][1]
    if end <= start:
        return PeriodResolution(error=f"Giờ của {describe_periods(first, last)} không hợp lệ")
    return PeriodResolution(start, end)


# ---- Đọc/ghi bảng tiết -------------------------------------------------------------------------


def load_periods() -> dict[int, TimeRange]:
    return {
        p.number: (p.start_time, p.end_time)
        for p in db.session.scalars(select(Period).order_by(Period.number))
    }


def list_periods() -> list[Period]:
    return list(db.session.scalars(select(Period).order_by(Period.number)))


def recompute_for_shift(shift: Shift, shifts: list[Shift]) -> None:
    """Tính lại các tiết của ca (chưa sửa tay) sau khi đổi giờ ca; giữ tiết `is_manual`."""
    ordered = sorted(shifts, key=lambda s: s.position)[:MAX_SHIFTS_WITH_PERIODS]
    if shift not in ordered:
        return
    index = ordered.index(shift) + 1
    existing = {p.number: p for p in list_periods()}
    for number, (start, end) in zip(
        shift_period_numbers(index),
        default_period_times(shift.start_time, shift.end_time),
        strict=False,
    ):
        period = existing.get(number)
        if period is None:
            db.session.add(Period(number=number, start_time=start, end_time=end))
        elif not period.is_manual:
            period.start_time, period.end_time = start, end


def _invalid(field: str, message: str) -> ApiError:
    return ApiError(400, "validation_error", "Dữ liệu chưa hợp lệ", {field: message})


def _check_number(number: int) -> None:
    if not MIN_PERIOD <= number <= MAX_PERIOD:
        raise not_found(f"Tiết phải từ {MIN_PERIOD} đến {MAX_PERIOD}")


def put_period(number: int, start: time, end: time) -> tuple[Period, list[dict]]:
    """Tạo hoặc sửa một tiết (đặt `is_manual`); trả kèm cảnh báo khi chồng giờ tiết kề."""
    _check_number(number)
    if end <= start:
        raise _invalid("end_time", "Giờ kết thúc phải sau giờ bắt đầu")
    period = db.session.get(Period, number)
    if period is None:
        period = Period(number=number, start_time=start, end_time=end, is_manual=True)
        db.session.add(period)
    else:
        period.start_time, period.end_time, period.is_manual = start, end, True
    db.session.flush()
    warnings = _overlap_warnings(number)
    db.session.commit()
    return period, warnings


def _overlap_warnings(number: int) -> list[dict]:
    me = db.session.get(Period, number)
    warnings = []
    for neighbour_number in (number - 1, number + 1):
        other = db.session.get(Period, neighbour_number)
        if other is None:
            continue
        first, second = (other, me) if neighbour_number < number else (me, other)
        if first.end_time > second.start_time:
            warnings.append(
                {
                    "code": "period_overlap",
                    "message": f"Tiết {first.number} kết thúc sau khi tiết {second.number} bắt đầu",
                }
            )
    return warnings


def reset_period(number: int) -> Period | None:
    """Về giờ suy từ ca; tiết không thuộc ca nào và không có mặc định thì bị xoá (trả None)."""
    _check_number(number)
    shifts = list(db.session.scalars(select(Shift).order_by(Shift.position)))
    default = default_periods(shifts).get(number)
    period = db.session.get(Period, number)
    if default is None:
        if period is not None:
            db.session.delete(period)
        db.session.commit()
        return None
    if period is None:
        period = Period(number=number, start_time=default[0], end_time=default[1])
        db.session.add(period)
    else:
        period.start_time, period.end_time, period.is_manual = default[0], default[1], False
    db.session.commit()
    return period


def delete_period(number: int) -> None:
    """Xoá tiết không thuộc ca nào (tiết thuộc ca chỉ "về mặc định" được)."""
    _check_number(number)
    shifts = list(db.session.scalars(select(Shift).order_by(Shift.position)))
    if number in {n for n in default_periods(shifts) if n <= 12}:
        raise _invalid("number", "Tiết này thuộc một ca; hãy dùng “Về mặc định”")
    period = db.session.get(Period, number)
    if period is None:
        raise not_found("Không tìm thấy tiết")
    db.session.delete(period)
    db.session.commit()
