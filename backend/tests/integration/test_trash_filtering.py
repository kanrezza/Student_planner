"""Task trong Thùng rác bị loại khỏi mọi chỗ đọc task (feature 002 FR-030, task T007)."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from app.lib import timeutil
from app.lib.timeutil import TZ
from app.models import Tag, Task
from tests.integration.helpers import create_semester, create_subject, create_task

NOW = datetime(2026, 11, 9, 4, 0, tzinfo=TZ)  # Thứ Hai 09/11/2026, trước giờ tổng hợp 05:00


@pytest.fixture(autouse=True)
def fixed_now(monkeypatch):
    monkeypatch.setattr(timeutil, "now", lambda: NOW)


def trash_directly(db_session, task_id: int) -> None:
    task = db_session.get(Task, task_id)
    task.deleted_at = NOW - timedelta(hours=1)
    db_session.flush()


def ids(items) -> set[int]:
    return {item["id"] for item in items}


def test_trashed_task_is_hidden_everywhere(client, db_session):
    tag = client.post("/api/tags", json={"name": "Gấp"}).get_json()
    # Đồng bộ Lịch tắt để /reminders/upcoming (nhắc dự phòng của trình duyệt) có trả task.
    client.patch("/api/settings", json={"daily_digest_enabled": True})
    kept = create_task(client, db_session, "Còn dùng", due_date="2026-11-09", due_time="10:00")
    gone = create_task(
        client,
        db_session,
        "Đã xoá",
        due_date="2026-11-09",
        due_time="10:00",
        tag_ids=[tag["id"]],
        reminder_minutes=30,
    )
    study_list_id = gone["list_id"]
    count_before = next(
        item["open_task_count"]
        for item in client.get("/api/lists").get_json()
        if item["id"] == study_list_id
    )
    trash_directly(db_session, gone["id"])

    assert ids(client.get("/api/tasks").get_json()) == {kept["id"]}
    assert ids(client.get(f"/api/tasks?tags={tag['id']}").get_json()) == set()
    assert client.get(f"/api/tasks/{gone['id']}").status_code == 404

    today = client.get("/api/today").get_json()
    assert gone["id"] not in ids(today["tasks_due_today"])

    calendar = client.get("/api/calendar?from=2026-11-09&to=2026-11-15").get_json()
    assert ids(calendar["tasks"]) == {kept["id"]}

    feed_keys = {r["sync_key"] for r in client.get("/api/sync/feed").get_json()["reminders"]}
    assert feed_keys == {f"task:{kept['id']}"}

    digest = client.get("/api/digest?date=2026-11-09").get_json()
    assert "Đã xoá" not in " ".join(digest["lines"])
    assert "Còn dùng" in " ".join(digest["lines"])

    upcoming = client.get("/api/reminders/upcoming?hours=24").get_json()
    assert not any(item["sync_key"].startswith(f"task:{gone['id']}") for item in upcoming)
    assert any(item["sync_key"].startswith(f"task:{kept['id']}") for item in upcoming)

    count_after = next(
        item["open_task_count"]
        for item in client.get("/api/lists").get_json()
        if item["id"] == study_list_id
    )
    assert count_after == count_before - 1


def test_trashed_auto_task_is_not_updated_or_recreated(client, db_session):
    e_learning = db_session.scalars(select(Tag).where(Tag.system_key == "e_learning")).one().id
    semester_id = create_semester(client, "2026-11-02", "2026-11-29", "HK test")
    subject = create_subject(
        client, semester_id, name="Triết học", weekdays=[2], tag_ids=[e_learning]
    )
    auto = db_session.scalars(
        select(Task).where(Task.is_auto).order_by(Task.due_date.desc())
    ).first()
    session_id, old_title, old_due = auto.source_session_id, auto.title, auto.due_date
    auto.deleted_at = NOW
    auto.source_session.auto_task_suppressed = True  # như khi người dùng xoá
    db_session.flush()

    # Đổi giờ học → reconcile chạy lại cho mọi buổi của môn.
    resp = client.patch(
        f"/api/subjects/{subject['id']}", json={"start_time": "13:00", "end_time": "15:40"}
    )
    assert resp.status_code == 200, resp.get_json()

    db_session.expire_all()
    trashed = db_session.get(Task, auto.id)
    assert (trashed.title, trashed.due_date, trashed.deleted_at) == (old_title, old_due, NOW)
    linked = db_session.scalars(
        select(Task).where(Task.source_session_id == session_id, Task.deleted_at.is_(None))
    ).all()
    assert linked == []
