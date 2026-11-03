"""Sinh buổi học lặp hàng tuần và kế hoạch sinh lại khi môn học đổi (research R8). Chỉ hàm thuần."""

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

from app.lib.timeutil import combine


def generate_dates(weekdays: list[int], start: date, end: date) -> list[date]:
    """Mọi ngày trong [start, end] (tính cả hai đầu) rơi vào các thứ đã chọn (1 = Thứ Hai)."""
    wanted = set(weekdays)
    days = (end - start).days + 1
    return [
        start + timedelta(n)
        for n in range(max(days, 0))
        if (start + timedelta(n)).isoweekday() in wanted
    ]


@dataclass(frozen=True)
class ExistingSession:
    id: int
    date: date
    start_at: datetime
    end_at: datetime
    room: str | None
    is_cancelled: bool
    time_overridden: bool
    room_overridden: bool

    @property
    def has_exception(self) -> bool:
        return self.is_cancelled or self.time_overridden or self.room_overridden


@dataclass(frozen=True)
class SessionUpdate:
    """Trường None = giữ nguyên."""

    id: int
    start_at: datetime | None = None
    end_at: datetime | None = None
    room: str | None = None
    clear_room: bool = False  # đặt phòng về rỗng (môn bỏ phòng học)


@dataclass
class Plan:
    to_create: list[date] = field(default_factory=list)
    to_update: list[SessionUpdate] = field(default_factory=list)
    to_delete: list[int] = field(default_factory=list)
    exception_conflicts: list[int] = field(default_factory=list)


def plan_regeneration(
    existing: list[ExistingSession],
    desired_dates: list[date],
    start_time: time,
    end_time: time,
    room: str | None,
) -> Plan:
    """So sánh buổi hiện có với tập ngày mong muốn.

    - Ngày mới → tạo.
    - Buổi không có ngoại lệ → cập nhật giờ và phòng theo môn; nằm ngoài khoảng → xoá.
    - Buổi đã huỷ → giữ nguyên hoàn toàn. Buổi đã sửa giờ → giữ giờ; đã sửa phòng → giữ phòng.
    - Buổi có ngoại lệ nằm ngoài khoảng mới → báo trong `exception_conflicts` (FR-013).
    """
    plan = Plan()
    by_date = {s.date: s for s in existing}
    desired = set(desired_dates)

    for d in sorted(desired):
        current = by_date.get(d)
        if current is None:
            plan.to_create.append(d)
            continue
        if current.is_cancelled:
            continue
        start_at, end_at = combine(d, start_time), combine(d, end_time)
        new_times = not current.time_overridden and (
            current.start_at != start_at or current.end_at != end_at
        )
        new_room = not current.room_overridden and current.room != room
        if new_times or new_room:
            plan.to_update.append(
                SessionUpdate(
                    id=current.id,
                    start_at=start_at if new_times else None,
                    end_at=end_at if new_times else None,
                    room=room if new_room else None,
                    clear_room=new_room and room is None,
                )
            )

    for s in existing:
        if s.date not in desired:
            (plan.exception_conflicts if s.has_exception else plan.to_delete).append(s.id)
    return plan
