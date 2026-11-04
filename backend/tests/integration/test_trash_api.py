"""Thùng rác: xoá, khôi phục, xoá hẳn, dọn sạch, tự xoá sau 30 ngày (feature 002 US7; task T046)."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from app.lib import timeutil
from app.lib.timeutil import TZ
from app.models import ClassSession, Tag, Task
from app.services import tasks as task_service
from app.services.revision import current_revision
from tests.integration.helpers import create_semester, create_subject, create_task

NOW = datetime(2026, 11, 9, 9, 0, tzinfo=TZ)
clock = {"now": NOW}


@pytest.fixture(autouse=True)
def fixed_now(monkeypatch):
    clock["now"] = NOW
    monkeypatch.setattr(timeutil, "now", lambda: clock["now"])
    task_service.reset_purge_throttle()


def feed_keys(client) -> set[str]:
    return {r["sync_key"] for r in client.get("/api/sync/feed").get_json()["reminders"]}


def full_task(client, db_session) -> dict:
    tag = client.post("/api/tags", json={"name": "Gấp"}).get_json()
    return create_task(
        client,
        db_session,
        "Nộp tiểu luận",
        notes="Bản in 2 mặt",
        due_date="2026-11-12",
        due_time="17:00",
        work_date="2026-11-11",
        work_start="19:00",
        work_end="21:00",
        priority=1,
        tag_ids=[tag["id"]],
        is_important=True,
        reminder_minutes=60,
    )


KEPT_FIELDS = (
    "title",
    "notes",
    "due_date",
    "due_time",
    "work_date",
    "work_start",
    "work_end",
    "priority",
    "list_id",
    "tags",
    "is_important",
    "reminder_minutes",
    "reminder_times",
)


def test_trash_and_restore_keep_every_field(client, db_session):
    task = full_task(client, db_session)
    assert f"task:{task['id']}" in feed_keys(client)

    revision = current_revision(db_session)
    resp = client.delete(f"/api/tasks/{task['id']}")
    assert resp.status_code == 200
    trashed = resp.get_json()
    assert trashed["deleted_at"] == "2026-11-09T09:00:00+07:00"
    assert trashed["days_left_in_trash"] == 30
    assert current_revision(db_session) > revision
    assert f"task:{task['id']}" not in feed_keys(client)
    assert client.delete(f"/api/tasks/{task['id']}").status_code == 404

    revision = current_revision(db_session)
    resp = client.post(f"/api/tasks/{task['id']}/restore")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["warnings"] == []
    assert {k: body["task"][k] for k in KEPT_FIELDS} == {k: task[k] for k in KEPT_FIELDS}
    assert body["task"]["deleted_at"] is None
    assert current_revision(db_session) > revision
    assert f"task:{task['id']}" in feed_keys(client)
    # Khôi phục task không ở Thùng rác → 404.
    assert client.post(f"/api/tasks/{task['id']}/restore").status_code == 404


def test_trash_view_order_and_days_left(client, db_session):
    older = create_task(client, db_session, "Cũ")
    newer = create_task(client, db_session, "Mới")
    clock["now"] = NOW - timedelta(days=10, hours=1)
    client.delete(f"/api/tasks/{older['id']}")
    clock["now"] = NOW
    client.delete(f"/api/tasks/{newer['id']}")

    items = client.get("/api/tasks?view=trash").get_json()
    assert [(t["id"], t["days_left_in_trash"]) for t in items] == [
        (newer["id"], 30),
        (older["id"], 20),  # 10 ngày 1 giờ đã qua → còn 19,96 ngày → làm tròn lên 20
    ]
    assert all(t["id"] not in {older["id"], newer["id"]} for t in client.get("/api/tasks").json)


def test_trashed_task_cannot_be_edited(client, db_session):
    task = create_task(client, db_session, "Xoá rồi")
    client.delete(f"/api/tasks/{task['id']}")
    assert client.patch(f"/api/tasks/{task['id']}", json={"title": "Sửa"}).status_code == 404
    assert client.post(f"/api/tasks/{task['id']}/complete").status_code == 404


@pytest.mark.parametrize("endpoint", ["/api/tasks?view=trash", "/api/task-counts", "/api/today"])
def test_purge_after_30_days(client, db_session, endpoint):
    old = create_task(client, db_session, "Quá 30 ngày")
    recent = create_task(client, db_session, "29 ngày")
    db_session.get(Task, old["id"]).deleted_at = NOW - timedelta(days=31)
    db_session.get(Task, recent["id"]).deleted_at = NOW - timedelta(days=29)
    db_session.flush()

    assert client.get(endpoint).status_code == 200
    db_session.expire_all()
    assert db_session.get(Task, old["id"]) is None
    assert db_session.get(Task, recent["id"]) is not None


def test_sync_feed_purges_at_most_once_per_hour(client, db_session):
    first = create_task(client, db_session, "Hết hạn trước")
    second = create_task(client, db_session, "Hết hạn sau")
    db_session.get(Task, first["id"]).deleted_at = NOW - timedelta(days=31)
    db_session.get(Task, second["id"]).deleted_at = NOW - timedelta(days=29, hours=23, minutes=30)
    db_session.flush()

    feed = client.get("/api/sync/feed").get_json()
    assert {"events", "reminders"} <= set(feed)
    db_session.expire_all()
    assert db_session.get(Task, first["id"]) is None
    assert db_session.get(Task, second["id"]) is not None

    clock["now"] = NOW + timedelta(minutes=40)  # `second` đã quá 30 ngày nhưng chưa tới 1 giờ
    client.get("/api/sync/feed")
    db_session.expire_all()
    assert db_session.get(Task, second["id"]) is not None

    clock["now"] = NOW + timedelta(minutes=61)
    client.get("/api/sync/feed")
    db_session.expire_all()
    assert db_session.get(Task, second["id"]) is None


def test_delete_permanently_and_empty_trash(client, db_session):
    active = create_task(client, db_session, "Đang dùng")
    a = create_task(client, db_session, "A")
    b = create_task(client, db_session, "B")
    c = create_task(client, db_session, "C")

    resp = client.delete(f"/api/tasks/{active['id']}?permanent=true")
    assert resp.status_code == 409

    for task in (a, b, c):
        client.delete(f"/api/tasks/{task['id']}")
    assert client.delete(f"/api/tasks/{a['id']}?permanent=true").status_code == 204
    assert db_session.get(Task, a["id"]) is None

    resp = client.delete("/api/trash")
    assert resp.status_code == 200 and resp.get_json() == {"deleted": 2}
    assert client.get("/api/tasks?view=trash").get_json() == []
    assert client.get(f"/api/tasks/{active['id']}").status_code == 200


def test_auto_task_trash_and_restore(client, db_session):
    e_learning = db_session.scalars(select(Tag).where(Tag.system_key == "e_learning")).one().id
    semester_id = create_semester(client, "2026-11-02", "2026-11-29", "HK test")
    create_subject(client, semester_id, name="Triết học", weekdays=[2], tag_ids=[e_learning])

    def autos():
        db_session.expire_all()
        return db_session.scalars(
            select(Task).where(Task.is_auto, Task.deleted_at.is_(None)).order_by(Task.due_date)
        ).all()

    target = autos()[-1]
    task_id, session_id = target.id, target.source_session_id
    count = len(autos())

    client.delete(f"/api/tasks/{task_id}")
    assert db_session.get(ClassSession, session_id).auto_task_suppressed is True
    client.patch(f"/api/sessions/{session_id}", json={"room": "B1"})  # kích hoạt reconcile
    assert len(autos()) == count - 1  # không tạo lại

    resp = client.post(f"/api/tasks/{task_id}/restore")
    assert resp.status_code == 200
    assert db_session.get(ClassSession, session_id).auto_task_suppressed is False
    assert len(autos()) == count  # quay lại, không sinh task trùng
    assert resp.get_json()["task"]["source_session_id"] == session_id


def test_delete_list_moves_tasks_to_trash(client, db_session):
    work = client.post("/api/lists", json={"name": "Dự án"}).get_json()
    open_task = create_task(client, db_session, "Báo cáo", list_id=work["id"])
    done_task = create_task(client, db_session, "Đã xong", list_id=work["id"])
    client.post(f"/api/tasks/{done_task['id']}/complete")
    already = create_task(client, db_session, "Đã xoá trước", list_id=work["id"])
    client.delete(f"/api/tasks/{already['id']}")

    assert client.delete(f"/api/lists/{work['id']}?delete_tasks=true").status_code == 204
    trash = {t["id"]: t for t in client.get("/api/tasks?view=trash").get_json()}
    assert set(trash) == {open_task["id"], done_task["id"], already["id"]}
    study_id = create_task(client, db_session, "x")["list_id"]
    for item in trash.values():
        assert item["list_id"] == study_id
        assert item["trashed_from_list_name"] == "Dự án"

    resp = client.post(f"/api/tasks/{open_task['id']}/restore")
    body = resp.get_json()
    assert body["task"]["list_id"] == study_id
    assert body["task"]["trashed_from_list_name"] is None
    assert body["warnings"] == [
        {
            "code": "list_replaced",
            "message": "Danh sách cũ “Dự án” đã bị xoá, công việc được đưa về Học tập",
        }
    ]


def test_list_with_only_trashed_tasks_can_be_deleted(client, db_session):
    work = client.post("/api/lists", json={"name": "Tạm"}).get_json()
    task = create_task(client, db_session, "Rác", list_id=work["id"])
    client.delete(f"/api/tasks/{task['id']}")
    assert client.delete(f"/api/lists/{work['id']}").status_code == 204
    trashed = client.get("/api/tasks?view=trash").get_json()
    assert trashed[0]["trashed_from_list_name"] == "Tạm"
