import unicodedata
from datetime import date, datetime, time

from app.lib.timeutil import TZ, combine
from app.services.auto_deadlines import (
    AutoTaskInfo,
    Create,
    Delete,
    Rules,
    SessionInfo,
    Update,
    due_at,
    eligible,
    plan,
    title_for,
)

RULES = Rules(evening_from=time(20, 0), due_time=time(8, 0), excluded=["Giáo dục thể chất"])
NOW = datetime(2026, 11, 9, 12, 0, tzinfo=TZ)  # Thứ Hai


def session(
    id=1,
    d=date(2026, 11, 10),
    start=time(6, 45),
    end=time(9, 25),
    name="Triết học",
    tags=frozenset({"e_learning"}),
    cancelled=False,
    suppressed=False,
):
    return SessionInfo(
        id=id,
        date=d,
        start_local=start,
        end_at=combine(d, end),
        is_cancelled=cancelled,
        subject_name=name,
        tag_keys=tags,
        suppressed=suppressed,
    )


def test_eligible_rules():
    assert eligible(session(), RULES)  # môn có nhãn E-Learning
    assert eligible(session(tags=frozenset(), start=time(20, 0), end=time(21, 30)), RULES)
    assert not eligible(session(tags=frozenset(), start=time(19, 59), end=time(21, 0)), RULES)
    assert not eligible(session(cancelled=True), RULES)
    nfd_name = unicodedata.normalize("NFD", "giáo dục thể chất 2")
    assert not eligible(session(name=nfd_name, start=time(20, 30), end=time(22, 0)), RULES)


def test_due_at_next_sunday_after_end():
    tue = combine(date(2026, 11, 10), time(9, 25))
    assert due_at(tue, time(8, 0)) == combine(date(2026, 11, 15), time(8, 0))
    sunday_evening = combine(date(2026, 11, 15), time(21, 30))
    assert due_at(sunday_evening, time(8, 0)) == combine(date(2026, 11, 22), time(8, 0))
    sunday_early = combine(date(2026, 11, 15), time(7, 30))
    assert due_at(sunday_early, time(8, 0)) == combine(date(2026, 11, 15), time(8, 0))
    assert due_at(tue, time(22, 0)) == combine(date(2026, 11, 15), time(22, 0))


def test_title():
    assert title_for("Triết học", date(2026, 11, 10)) == "Bài tập Triết học – buổi 10/11"


def auto_task(
    id=50,
    session_id=1,
    title="Bài tập Triết học – buổi 10/11",
    due=(15, 8),
    completed=False,
    modified=False,
):
    return AutoTaskInfo(
        id=id,
        session_id=session_id,
        title=title,
        due=combine(date(2026, 11, due[0]), time(due[1], 0)),
        completed=completed,
        user_modified=modified,
    )


def test_plan_create_update_delete():
    actions = plan([session()], [], RULES, NOW)
    assert actions == [
        Create(
            session_id=1,
            title="Bài tập Triết học – buổi 10/11",
            due=combine(date(2026, 11, 15), time(8, 0)),
        )
    ]
    # Đã có task đúng → không làm gì
    assert plan([session()], [auto_task()], RULES, NOW) == []
    # Hạn lệch (đổi giờ deadline) → cập nhật
    assert plan([session()], [auto_task(due=(15, 7))], RULES, NOW) == [
        Update(
            task_id=50,
            title="Bài tập Triết học – buổi 10/11",
            due=combine(date(2026, 11, 15), time(8, 0)),
        )
    ]
    # Không còn thoả điều kiện → xoá
    assert plan([session(cancelled=True)], [auto_task()], RULES, NOW) == [Delete(task_id=50)]


def test_plan_leaves_user_owned_tasks_alone():
    assert plan([session(cancelled=True)], [auto_task(modified=True)], RULES, NOW) == []
    assert plan([session(cancelled=True)], [auto_task(completed=True)], RULES, NOW) == []
    assert plan([session(suppressed=True)], [], RULES, NOW) == []


def test_plan_skips_past_deadlines():
    old = session(d=date(2026, 11, 3))  # hạn 08/11 đã qua so với NOW (09/11)
    assert plan([old], [], RULES, NOW) == []
    # Task cũ đã qua hạn thì không bị sửa dù quy tắc đổi
    assert plan([old], [auto_task(due=(8, 7))], RULES, NOW) == []
