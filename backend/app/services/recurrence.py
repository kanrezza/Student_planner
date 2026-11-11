"""Sinh buổi học lặp hàng tuần và kế hoạch sinh lại khi môn học đổi (research R8). Chỉ hàm thuần.

Môn có thể có nhiều quy tắc lặp (feature 004): `desired_sessions` gộp các quy tắc thành ánh xạ
ngày → buổi mong muốn, `plan_sessions` so sánh với buổi hiện có.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Protocol

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
    # Ngày gốc khi buổi đã được dời sang ngày khác (feature 002 FR-028); None = chưa dời.
    original_date: date | None = None
    schedule_id: int | None = None  # quy tắc đã sinh ra buổi (feature 004)

    @property
    def lock_date(self) -> date:
        """Ngày khoá để khớp với ngày sinh từ quy tắc lặp: ngày gốc nếu đã dời."""
        return self.original_date or self.date

    @property
    def has_exception(self) -> bool:
        return (
            self.is_cancelled
            or self.time_overridden
            or self.room_overridden
            or self.original_date is not None
        )


@dataclass(frozen=True)
class SessionUpdate:
    """Trường None = giữ nguyên."""

    id: int
    start_at: datetime | None = None
    end_at: datetime | None = None
    room: str | None = None
    clear_room: bool = False  # đặt phòng về rỗng (môn bỏ phòng học)
    set_schedule: bool = False  # đổi quy tắc sinh buổi (kể cả về None)
    schedule_id: int | None = None


@dataclass
class Plan:
    to_create: list[date] = field(default_factory=list)
    to_update: list[SessionUpdate] = field(default_factory=list)
    to_delete: list[int] = field(default_factory=list)
    exception_conflicts: list[int] = field(default_factory=list)


class ScheduleLike(Protocol):
    """Quy tắc lặp (SubjectSchedule hoặc bản dựng tay trong test)."""

    id: int | None
    weekdays: list[int]
    start_date: date
    end_date: date
    start_time: time
    end_time: time
    room: str | None


@dataclass(frozen=True)
class DesiredSession:
    """Buổi mong muốn ở một ngày: giờ, phòng và quy tắc sinh ra nó."""

    schedule_id: int | None
    start_time: time
    end_time: time
    room: str | None


def desired_sessions(
    schedules: Sequence[ScheduleLike],
) -> tuple[dict[date, DesiredSession], list[date]]:
    """Gộp các quy tắc thành {ngày: buổi mong muốn}.

    Hai quy tắc rơi vào cùng một ngày: quy tắc đứng trước (thứ tự trong `schedules`) thắng, ngày đó
    được ghi vào danh sách trùng để cảnh báo (FR-023).
    """
    desired: dict[date, DesiredSession] = {}
    overlaps: list[date] = []
    for rule in schedules:
        for day in generate_dates(rule.weekdays, rule.start_date, rule.end_date):
            if day in desired:
                overlaps.append(day)
                continue
            desired[day] = DesiredSession(rule.id, rule.start_time, rule.end_time, rule.room)
    return desired, sorted(set(overlaps))


def plan_regeneration(
    existing: list[ExistingSession],
    desired_dates: list[date],
    start_time: time,
    end_time: time,
    room: str | None,
) -> Plan:
    """Như `plan_sessions` cho một quy tắc duy nhất (cùng giờ và phòng cho mọi ngày)."""
    same = DesiredSession(None, start_time, end_time, room)
    return plan_sessions(existing, {d: same for d in desired_dates}, keep_before=None)


def plan_sessions(
    existing: list[ExistingSession],
    desired: dict[date, DesiredSession],
    keep_before: date | None = None,
) -> Plan:
    """So sánh buổi hiện có với các ngày mong muốn.

    - Ngày mới → tạo.
    - Buổi không có ngoại lệ → cập nhật giờ, phòng và quy tắc theo buổi mong muốn; nằm ngoài lịch →
    xoá.
    - Buổi đã huỷ → giữ nguyên hoàn toàn. Buổi đã sửa giờ → giữ giờ; đã sửa phòng → giữ phòng.
    - Buổi có ngoại lệ nằm ngoài lịch mới → báo trong `exception_conflicts` (FR-013).
    - Buổi đã dời khớp theo ngày gốc (`lock_date`), nên không sinh buổi mới ở ngày gốc; giờ/phòng
      mới của quy tắc áp lên ngày đã dời.
    - `keep_before` (nhập PDF, FR-022): buổi có ngày trước mốc này không bị tạo, sửa hay xoá.
    """

    def frozen(day: date) -> bool:
        return keep_before is not None and day < keep_before

    plan = Plan()
    by_date = {s.lock_date: s for s in existing}

    for d in sorted(desired):
        want = desired[d]
        current = by_date.get(d)
        if current is None:
            if not frozen(d):
                plan.to_create.append(d)
            continue
        if current.is_cancelled or frozen(current.date):
            continue
        start_at = combine(current.date, want.start_time)
        end_at = combine(current.date, want.end_time)
        new_times = not current.time_overridden and (
            current.start_at != start_at or current.end_at != end_at
        )
        new_room = not current.room_overridden and current.room != want.room
        new_schedule = current.schedule_id != want.schedule_id
        if new_times or new_room or new_schedule:
            plan.to_update.append(
                SessionUpdate(
                    id=current.id,
                    start_at=start_at if new_times else None,
                    end_at=end_at if new_times else None,
                    room=want.room if new_room else None,
                    clear_room=new_room and want.room is None,
                    set_schedule=new_schedule,
                    schedule_id=want.schedule_id,
                )
            )

    for s in existing:
        if s.lock_date in desired or frozen(s.date):
            continue
        (plan.exception_conflicts if s.has_exception else plan.to_delete).append(s.id)
    return plan
