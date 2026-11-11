"""Sinh buổi từ nhiều quy tắc lặp của một môn (feature 004, FR-020, FR-022, FR-023)."""

from dataclasses import dataclass
from datetime import date, time

from app.lib.timeutil import combine
from app.services.recurrence import (
    DesiredSession,
    ExistingSession,
    desired_sessions,
    plan_sessions,
)

MON, TUE, FRI = 1, 2, 5


@dataclass
class Rule:
    id: int
    weekdays: list[int]
    start_date: date
    end_date: date
    start_time: time = time(9, 30)
    end_time: time = time(12, 10)
    room: str | None = "A101"


def existing(
    id, d, rule_id=1, room="A101", *, cancelled=False, time_overridden=False, room_overridden=False
):
    return ExistingSession(
        id=id,
        date=d,
        start_at=combine(d, time(9, 30)),
        end_at=combine(d, time(12, 10)),
        room=room,
        is_cancelled=cancelled,
        time_overridden=time_overridden,
        room_overridden=room_overridden,
        schedule_id=rule_id,
    )


def test_holiday_gap_between_two_rules_has_no_sessions():
    rules = [
        Rule(1, [MON], date(2026, 11, 30), date(2027, 1, 24)),
        Rule(2, [MON], date(2027, 2, 15), date(2027, 2, 28)),
    ]
    desired, overlaps = desired_sessions(rules)
    assert overlaps == []
    assert date(2027, 1, 25) not in desired and date(2027, 2, 8) not in desired
    assert min(desired) == date(2026, 11, 30) and max(desired) == date(2027, 2, 22)
    assert desired[date(2027, 2, 15)].schedule_id == 2
    assert len([d for d in desired if d < date(2027, 1, 25)]) == 8  # các thứ Hai 30/11 … 18/01


def test_rule_rooms_follow_their_own_rule():
    rules = [
        Rule(1, [MON], date(2026, 11, 30), date(2026, 12, 6), room="A6-501"),
        Rule(2, [MON], date(2026, 12, 7), date(2026, 12, 13), room="A6-203"),
    ]
    desired, _ = desired_sessions(rules)
    assert desired[date(2026, 11, 30)].room == "A6-501"
    assert desired[date(2026, 12, 7)].room == "A6-203"


def test_two_weekdays_in_one_rule():
    rule = Rule(1, [TUE, FRI], date(2026, 12, 21), date(2026, 12, 27))
    desired, _ = desired_sessions([rule])
    assert sorted(desired) == [date(2026, 12, 22), date(2026, 12, 25)]


def test_overlapping_rules_earlier_one_wins_and_overlap_is_reported():
    first = Rule(1, [MON], date(2026, 12, 7), date(2026, 12, 14), room="X")
    second = Rule(2, [MON], date(2026, 12, 14), date(2026, 12, 21), room="Y")
    desired, overlaps = desired_sessions([first, second])
    assert overlaps == [date(2026, 12, 14)]
    assert desired[date(2026, 12, 14)].schedule_id == 1 and desired[date(2026, 12, 14)].room == "X"
    assert desired[date(2026, 12, 21)].schedule_id == 2


def desired_for(days, rule_id=1, room="A101", start=time(9, 30), end=time(12, 10)):
    return {d: DesiredSession(rule_id, start, end, room) for d in days}


def test_exceptions_are_kept_like_before():
    d1, d2, d3, d4 = date(2026, 12, 7), date(2026, 12, 14), date(2026, 12, 21), date(2026, 12, 28)
    current = [
        existing(1, d1),
        existing(2, d2, cancelled=True),
        existing(3, d3, time_overridden=True),
        existing(4, d4, room="B2", room_overridden=True),
    ]
    plan = plan_sessions(current, desired_for([d1, d2, d3, d4], room="C3"))
    updates = {u.id: u for u in plan.to_update}
    # #1 và #3 đổi phòng (giờ riêng của #3 được giữ); #4 giữ phòng riêng, giờ vẫn khớp nên không đổi gì
    assert set(updates) == {1, 3}
    assert updates[1].room == "C3" and updates[3].room == "C3"
    assert updates[3].start_at is None
    assert plan.to_delete == [] and plan.exception_conflicts == []


def test_session_moves_to_new_rule_without_other_changes():
    d = date(2026, 12, 7)
    plan = plan_sessions([existing(1, d, rule_id=1)], desired_for([d], rule_id=2))
    (update,) = plan.to_update
    assert update.set_schedule and update.schedule_id == 2
    assert update.start_at is None and update.room is None


def test_removed_rule_deletes_plain_sessions_and_flags_exceptions():
    d1, d2 = date(2026, 12, 7), date(2026, 12, 14)
    current = [existing(1, d1), existing(2, d2, cancelled=True)]
    plan = plan_sessions(current, {})
    assert plan.to_delete == [1] and plan.exception_conflicts == [2]


def test_keep_before_freezes_past_sessions():
    past, today, future = date(2026, 11, 30), date(2026, 12, 7), date(2026, 12, 14)
    current = [existing(1, past), existing(2, future)]
    # lịch mới đổi phòng và bỏ ngày `past`; mốc = hôm nay (07/12)
    desired = desired_for([today, future], room="NEW")
    plan = plan_sessions(current, desired, keep_before=today)
    assert plan.to_delete == [] and plan.exception_conflicts == []  # buổi quá khứ không xoá
    assert [u.id for u in plan.to_update] == [2]
    assert plan.to_create == [today]


def test_keep_before_does_not_create_or_update_past_days():
    past, today = date(2026, 12, 1), date(2026, 12, 7)
    plan = plan_sessions(
        [existing(1, past, room="OLD")], desired_for([past, today], room="NEW"), keep_before=today
    )
    assert plan.to_create == [today]
    assert plan.to_update == []


def test_exception_outside_new_schedule_before_cutoff_is_not_a_conflict():
    past = date(2026, 12, 1)
    plan = plan_sessions(
        [existing(1, past, cancelled=True)], desired_for([date(2026, 12, 8)]), date(2026, 12, 7)
    )
    assert plan.exception_conflicts == []
