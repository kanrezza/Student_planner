"""Thời gian theo múi giờ Việt Nam (research R10)."""

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from app.config import TIMEZONE

TZ = ZoneInfo(TIMEZONE)


def now() -> datetime:
    return datetime.now(TZ)


def today() -> date:
    return now().date()


def combine(d: date, t: time) -> datetime:
    """Ghép ngày + giờ thành thời điểm có múi giờ Asia/Ho_Chi_Minh."""
    return datetime.combine(d, t, tzinfo=TZ)


def iso(dt: datetime) -> str:
    """Chuỗi ISO 8601 có offset, quy về giờ Việt Nam: 2026-11-16T07:30:00+07:00."""
    return dt.astimezone(TZ).isoformat(timespec="seconds")


def weekday_vn(d: date) -> int:
    """1 = Thứ Hai … 7 = Chủ Nhật."""
    return d.isoweekday()
