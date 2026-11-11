"""Trạng thái và thứ tự thẻ trên bảng Kanban — hàm thuần (feature 005, research R2)."""

from datetime import date, datetime, timedelta

from app.lib.timeutil import TZ

DONE_WINDOW_DAYS = 7
REBALANCE_GAP = 1e-6


def task_status(completed_at: datetime | None, in_progress: bool) -> str:
    """ "done" khi đã hoàn thành; ngược lại "doing" nếu đang làm; còn lại "todo"."""
    if completed_at is not None:
        return "done"
    return "doing" if in_progress else "todo"


def rank_between(before: float | None, after: float | None) -> float:
    """Thứ tự cho thẻ thả giữa `before` (thẻ ngay trên) và `after` (thẻ ngay dưới)."""
    if before is None and after is None:
        return 0.0
    if before is None:
        return after - 1
    if after is None:
        return before + 1
    return (before + after) / 2


def needs_rebalance(ranks: list[float]) -> bool:
    """Hai thẻ kề nhau quá sát (hoặc trùng) thì cần đánh số lại cả cột."""
    ordered = sorted(ranks)
    return any(b - a < REBALANCE_GAP for a, b in zip(ordered, ordered[1:], strict=False))


def rebalance(ranks_in_order: list[float]) -> list[float]:
    """1, 2, 3… theo đúng thứ tự đã cho."""
    return [float(i) for i in range(1, len(ranks_in_order) + 1)]


def done_window_start(now: datetime) -> datetime:
    """00:00 (giờ Việt Nam) của ngày hôm nay trừ 6 ngày: cột Xong chỉ hiện từ mốc này (FR-010)."""
    today: date = now.astimezone(TZ).date()
    first_day = today - timedelta(days=DONE_WINDOW_DAYS - 1)
    return datetime(first_day.year, first_day.month, first_day.day, tzinfo=TZ)
