from datetime import datetime

import pytest
from sqlalchemy import select

from app.lib import timeutil
from app.lib.timeutil import TZ
from app.models import Tag, Task
from app.services.revision import current_revision
from tests.integration.helpers import create_semester, create_subject, sessions_of

NOW = datetime(2026, 11, 2, 9, 0, tzinfo=TZ)  # Thứ Hai 02/11/2026


@pytest.fixture(autouse=True)
def fixed_now(monkeypatch):
    monkeypatch.setattr(timeutil, "now", lambda: NOW)


@pytest.fixture
def e_learning(db_session):
    return db_session.scalars(select(Tag).where(Tag.system_key == "e_learning")).one().id


def auto_tasks(db_session):
    """Task tự tạo đang dùng (task trong Thùng rác không tính, feature 002)."""
    db_session.expire_all()
    return db_session.scalars(
        select(Task).where(Task.is_auto, Task.deleted_at.is_(None)).order_by(Task.due_date)
    ).all()


def setup(client, e_learning, **fields):
    semester_id = create_semester(client, "2026-11-02", "2026-11-29", "HK test")
    body = {"name": "Triết học", "weekdays": [2], "tag_ids": [e_learning], **fields}
    return create_subject(client, semester_id, **body)


def test_e_learning_subject_creates_weekly_deadlines(client, db_session, e_learning):
    setup(client, e_learning)  # Thứ Ba 03, 10, 17, 24/11
    tasks = auto_tasks(db_session)
    assert [(t.title, str(t.due_date), str(t.due_time)) for t in tasks] == [
        ("Bài tập Triết học – buổi 03/11", "2026-11-08", "08:00:00"),
        ("Bài tập Triết học – buổi 10/11", "2026-11-15", "08:00:00"),
        ("Bài tập Triết học – buổi 17/11", "2026-11-22", "08:00:00"),
        ("Bài tập Triết học – buổi 24/11", "2026-11-29", "08:00:00"),
    ]
    assert all(t.priority == 2 and t.list.is_default_study for t in tasks)
    data = client.get(f"/api/tasks/{tasks[0].id}").get_json()
    assert data["is_auto"] is True and data["source_session_id"] is not None


def test_cancel_restore_and_manual_delete(client, db_session, e_learning):
    subject = setup(client, e_learning)
    first, second = sessions_of(client, subject["id"])[:2]

    client.post(f"/api/sessions/{first['id']}/cancel")
    assert len(auto_tasks(db_session)) == 3
    client.post(f"/api/sessions/{first['id']}/restore")
    assert len(auto_tasks(db_session)) == 4

    task_id = next(t.id for t in auto_tasks(db_session) if t.source_session_id == second["id"])
    assert client.delete(f"/api/tasks/{task_id}").status_code == 200  # vào Thùng rác (002 FR-030)
    client.patch(f"/api/sessions/{second['id']}", json={"room": "B1"})  # kích hoạt reconcile
    assert len(auto_tasks(db_session)) == 3  # không tạo lại


def test_user_edit_protects_task_and_unedited_follows_changes(client, db_session, e_learning):
    subject = setup(client, e_learning)
    s1, s2 = sessions_of(client, subject["id"])[:2]
    edited = next(t for t in auto_tasks(db_session) if t.source_session_id == s1["id"])
    client.patch(f"/api/tasks/{edited.id}", json={"title": "Bài thu hoạch chương 1"})

    # Đổi giờ hai lần: task chưa sửa vẫn do quy tắc quản lý, task đã sửa giữ nguyên.
    for start, end in [("19:00", "20:00"), ("20:30", "21:30")]:
        client.patch(f"/api/sessions/{s1['id']}", json={"start_time": start, "end_time": end})
        client.patch(f"/api/sessions/{s2['id']}", json={"start_time": start, "end_time": end})
    tasks = {t.source_session_id: t for t in auto_tasks(db_session)}
    assert tasks[s1["id"]].title == "Bài thu hoạch chương 1"
    assert tasks[s1["id"]].user_modified is True
    assert tasks[s2["id"]].user_modified is False
    assert tasks[s2["id"]].title == "Bài tập Triết học – buổi 10/11"


def test_settings_change_reconciles_future(client, db_session, e_learning):
    setup(client, e_learning)
    client.patch("/api/settings", json={"auto_deadline_due_time": "22:00"})
    assert {str(t.due_time) for t in auto_tasks(db_session)} == {"22:00:00"}


def test_evening_rule_and_removing_tag(client, db_session, e_learning):
    semester_id = create_semester(client, "2026-11-02", "2026-11-29", "HK test")
    evening = create_subject(
        client,
        semester_id,
        name="Lập trình web",
        weekdays=[3],
        start_time="20:00",
        end_time="21:30",
    )
    assert len(auto_tasks(db_session)) == 4
    client.patch("/api/settings", json={"auto_deadline_evening_from": "20:30"})
    assert len(auto_tasks(db_session)) == 0
    online = create_subject(
        client, semester_id, name="Triết học", weekdays=[2], tag_ids=[e_learning]
    )
    assert len(auto_tasks(db_session)) == 4
    client.put(f"/api/subjects/{online['id']}/tags", json={"tag_ids": []})
    assert len(auto_tasks(db_session)) == 0
    assert evening["id"]


def test_physical_education_excluded(client, db_session, e_learning):
    semester_id = create_semester(client, "2026-11-02", "2026-11-29", "HK test")
    create_subject(
        client,
        semester_id,
        name="Giáo dục thể chất 2",
        weekdays=[3],
        start_time="20:30",
        end_time="22:00",
        tag_ids=[e_learning],
    )
    assert auto_tasks(db_session) == []


def test_deleting_subject_removes_unedited_auto_tasks(client, db_session, e_learning):
    subject = setup(client, e_learning)
    first = auto_tasks(db_session)[0]
    client.post(f"/api/tasks/{first.id}/complete")
    client.delete(f"/api/subjects/{subject['id']}")
    remaining = auto_tasks(db_session)
    assert [t.id for t in remaining] == [first.id]  # task đã hoàn thành được giữ lại


def test_full_semester_count(client, db_session, e_learning):
    semester_id = create_semester(client, "2026-11-02", "2027-02-14", "HK 15 tuần")
    create_subject(client, semester_id, name="Triết học", weekdays=[2], tag_ids=[e_learning])
    create_subject(client, semester_id, name="Giải tích", weekdays=[1])  # không thoả điều kiện
    assert len(auto_tasks(db_session)) == 15  # SC-015


def test_auto_tasks_follow_subject_importance(client, db_session, e_learning):
    subject = setup(client, e_learning)
    tasks = auto_tasks(db_session)
    edited = tasks[-1]
    client.patch(f"/api/tasks/{edited.id}", json={"title": "Bài cuối (đã sửa)"})

    client.patch(f"/api/subjects/{subject['id']}", json={"is_important": True})
    tasks = auto_tasks(db_session)
    assert [t.is_important for t in tasks] == [True, True, True, False]
    reminder = next(
        r
        for r in client.get("/api/sync/feed").get_json()["reminders"]
        if r["sync_key"] == f"task:{tasks[1].id}"
    )
    assert reminder["important"] is True
    assert len(reminder["alarms_at"]) == 5  # tối hôm trước + 4 mốc quan trọng

    client.patch(f"/api/subjects/{subject['id']}", json={"is_important": False})
    assert [t.is_important for t in auto_tasks(db_session)] == [False] * 4


def test_eve_reminder_setting(client, db_session, e_learning):
    setup(client, e_learning)
    key = f"task:{auto_tasks(db_session)[1].id}"  # hạn 08:00 CN 15/11

    def alarms():
        feed = client.get("/api/sync/feed").get_json()
        return next(r for r in feed["reminders"] if r["sync_key"] == key)["alarms_at"]

    assert alarms() == ["2026-11-14T20:00:00+07:00", "2026-11-15T07:00:00+07:00"]
    before = current_revision(db_session)
    resp = client.patch("/api/settings", json={"auto_deadline_eve_reminder_time": "21:30"})
    assert resp.get_json()["auto_deadline_eve_reminder_time"] == "21:30"
    assert current_revision(db_session) > before
    assert alarms()[0] == "2026-11-14T21:30:00+07:00"
    resp = client.patch("/api/settings", json={"auto_deadline_eve_reminder_time": None})
    assert resp.get_json()["auto_deadline_eve_reminder_time"] is None
    assert alarms() == ["2026-11-15T07:00:00+07:00"]
