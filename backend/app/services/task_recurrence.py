"""Quy tắc lặp của task (feature 003 US3, research R16). Chỉ hàm thuần, không đụng database.

Bốn kiểu: hằng ngày, mỗi N ngày, hằng tuần (nhiều thứ), hằng tháng (ngày D; tháng thiếu ngày
thì lấy cuối tháng).
"""

import calendar
from dataclasses import dataclass, replace
from datetime import date, datetime, time, timedelta

from app.lib.timeutil import combine

FREQS = ("daily", "every_n_days", "weekly", "monthly")
END_KINDS = ("never", "on_date", "after_count")
MAX_SEARCH_DAYS = 800  # đủ cho "mỗi 365 ngày" cộng thêm một chu kỳ


@dataclass(frozen=True)
class Rule:
    freq: str
    anchor_date: date
    interval_days: int | None = None
    weekdays: tuple[int, ...] = ()  # 1 = Thứ Hai … 7 = Chủ Nhật
    month_day: int | None = None
    end_kind: str = "never"
    end_date: date | None = None
    end_count: int | None = None


def clamp_month_day(year: int, month: int, day: int) -> int:
    """Ngày D trong tháng; tháng không có ngày D thì lấy ngày cuối tháng (FR-018)."""
    return min(day, calendar.monthrange(year, month)[1])


def matches(rule: Rule, day: date) -> bool:
    """`day` có khớp mẫu lặp không (chưa xét điều kiện kết thúc)."""
    if rule.freq == "daily":
        return True
    if rule.freq == "every_n_days":
        delta = (day - rule.anchor_date).days
        return delta >= 0 and delta % (rule.interval_days or 1) == 0
    if rule.freq == "weekly":
        return day.isoweekday() in rule.weekdays
    if rule.freq == "monthly":
        return day.day == clamp_month_day(day.year, day.month, rule.month_day or 1)
    raise ValueError(rule.freq)


def _within_end_date(rule: Rule, day: date) -> bool:
    return rule.end_kind != "on_date" or rule.end_date is None or day <= rule.end_date


def first_due_on_or_after(rule: Rule, start: date) -> date | None:
    """Ngày khớp quy tắc đầu tiên từ `start` (tính cả `start`), None nếu quá ngày kết thúc."""
    for offset in range(MAX_SEARCH_DAYS):
        day = start + timedelta(days=offset)
        if matches(rule, day):
            return day if _within_end_date(rule, day) else None
    return None


def occurrences(rule: Rule, start: date, end: date, limit: int | None = None) -> list[date]:
    """Mọi ngày khớp quy tắc trong [start, end], dừng ở ngày kết thúc và tối đa `limit` ngày."""
    result: list[date] = []
    day = start
    while day <= end and (limit is None or len(result) < limit):
        if not _within_end_date(rule, day):
            break
        if matches(rule, day):
            result.append(day)
        day += timedelta(days=1)
    return result


def is_finished(rule: Rule, occurrences_created: int) -> bool:
    """Đã đủ N lần (kiểu `after_count`)."""
    return rule.end_kind == "after_count" and occurrences_created >= (rule.end_count or 0)


def not_before_date(now: datetime, due_time: time | None) -> date:
    """Ngày sớm nhất được phép cho lần mới: hôm nay nếu giờ hạn chưa qua, không thì ngày mai."""
    today = now.date()
    if due_time is not None and combine(today, due_time) <= now:
        return today + timedelta(days=1)
    return today


def next_due(
    rule: Rule,
    after: date,
    now: datetime,
    due_time: time | None,
    occurrences_created: int,
) -> date | None:
    """Hạn của lần kế tiếp: ngày khớp đầu tiên sau `after` và không sớm hơn hôm nay (FR-017).

    None khi chuỗi đã kết thúc (đủ N lần hoặc quá ngày kết thúc). Không sinh các lần đã lỡ.
    """
    if is_finished(rule, occurrences_created):
        return None
    start = max(after + timedelta(days=1), not_before_date(now, due_time))
    return first_due_on_or_after(rule, start)


def shift_rule(rule: Rule, old_date: date, new_date: date) -> Rule:
    """Dời quy tắc khi đổi ngày hạn với "Lần này và các lần sau" (FR-020a)."""
    if rule.freq in ("daily", "every_n_days"):
        return replace(rule, anchor_date=new_date)
    if rule.freq == "weekly":
        days = {d for d in rule.weekdays if d != old_date.isoweekday()}
        days.add(new_date.isoweekday())
        return replace(rule, weekdays=tuple(sorted(days)), anchor_date=new_date)
    return replace(rule, month_day=new_date.day, anchor_date=new_date)


def validate(rule: Rule) -> dict[str, str]:
    """Lỗi theo trường (tiếng Việt), rỗng nếu hợp lệ."""
    errors: dict[str, str] = {}
    if rule.freq not in FREQS:
        errors["freq"] = "Kiểu lặp không hợp lệ"
    if rule.freq == "every_n_days" and not (
        rule.interval_days is not None and 2 <= rule.interval_days <= 365
    ):
        errors["interval_days"] = "Số ngày phải từ 2 đến 365"
    if rule.freq == "weekly":
        if not rule.weekdays:
            errors["weekdays"] = "Chọn ít nhất một thứ"
        elif any(d < 1 or d > 7 for d in rule.weekdays):
            errors["weekdays"] = "Thứ phải từ 1 (Thứ Hai) đến 7 (Chủ Nhật)"
    if rule.freq == "monthly" and not (rule.month_day is not None and 1 <= rule.month_day <= 31):
        errors["month_day"] = "Ngày trong tháng phải từ 1 đến 31"
    if rule.end_kind not in END_KINDS:
        errors["end"] = "Kiểu kết thúc không hợp lệ"
    if rule.end_kind == "on_date" and rule.end_date is None:
        errors["end"] = "Chọn ngày kết thúc"
    if rule.end_kind == "after_count" and not (
        rule.end_count is not None and 1 <= rule.end_count <= 999
    ):
        errors["end"] = "Số lần phải từ 1 đến 999"
    return errors
