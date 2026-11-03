from datetime import date, time

from app.lib.timeutil import combine
from app.services.recurrence import ExistingSession, generate_dates, plan_regeneration

MON, THU = 1, 4


def test_semester_mondays():
    dates = generate_dates([MON], date(2026, 9, 7), date(2026, 12, 20))
    assert len(dates) == 15
    assert dates[0] == date(2026, 9, 7)
    assert dates[-1] == date(2026, 12, 14)
    assert all(d.isoweekday() == MON for d in dates)


def test_multiple_weekdays_and_start_not_on_weekday():
    dates = generate_dates([MON, THU], date(2026, 9, 8), date(2026, 9, 21))  # bắt đầu Thứ Ba
    assert dates == [date(2026, 9, 10), date(2026, 9, 14), date(2026, 9, 17), date(2026, 9, 21)]


def test_range_without_selected_weekday_is_empty():
    assert generate_dates([MON], date(2026, 9, 8), date(2026, 9, 10)) == []


def test_single_day_range():
    assert generate_dates([MON], date(2026, 9, 7), date(2026, 9, 7)) == [date(2026, 9, 7)]


def existing(
    id,
    d,
    start=time(6, 45),
    end=time(9, 25),
    room="A101",
    *,
    cancelled=False,
    time_overridden=False,
    room_overridden=False,
):
    return ExistingSession(
        id=id,
        date=d,
        start_at=combine(d, start),
        end_at=combine(d, end),
        room=room,
        is_cancelled=cancelled,
        time_overridden=time_overridden,
        room_overridden=room_overridden,
    )


def test_plan_regeneration_keeps_exceptions_and_updates_others():
    d1, d2, d3, d4 = date(2026, 9, 7), date(2026, 9, 14), date(2026, 9, 21), date(2026, 9, 28)
    new_day = date(2026, 10, 5)
    current = [
        existing(1, d1),  # buổi thường → cập nhật giờ và phòng
        existing(2, d2, cancelled=True),  # đã huỷ → giữ nguyên
        existing(3, d3, time(7, 0), time(9, 0), time_overridden=True),  # giữ giờ, đổi phòng
        existing(4, d4, room="B2", room_overridden=True),  # giữ phòng, đổi giờ
    ]
    plan = plan_regeneration(current, [d1, d2, d3, d4, new_day], time(9, 35), time(12, 10), "C3")

    assert plan.to_create == [new_day]
    updates = {u.id: u for u in plan.to_update}
    assert updates[1].start_at == combine(d1, time(9, 35))
    assert updates[1].end_at == combine(d1, time(12, 10))
    assert updates[1].room == "C3"
    assert 2 not in updates
    assert updates[3].start_at is None and updates[3].room == "C3"
    assert updates[4].room is None and updates[4].start_at == combine(d4, time(9, 35))
    assert plan.to_delete == [] and plan.exception_conflicts == []


def test_plan_regeneration_out_of_range():
    d1, d2 = date(2026, 9, 7), date(2026, 9, 14)
    current = [existing(1, d1), existing(2, d2, cancelled=True)]
    plan = plan_regeneration(current, [], time(6, 45), time(9, 25), "A101")
    assert plan.to_delete == [1]  # buổi thường ngoài khoảng → xoá
    assert plan.exception_conflicts == [2]  # buổi có ngoại lệ ngoài khoảng → báo người dùng


def test_plan_regeneration_noop_when_unchanged():
    d1 = date(2026, 9, 7)
    plan = plan_regeneration([existing(1, d1)], [d1], time(6, 45), time(9, 25), "A101")
    assert plan.to_create == plan.to_update == plan.to_delete == plan.exception_conflicts == []
