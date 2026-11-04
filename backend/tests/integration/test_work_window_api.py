"""Khung giờ làm của task (feature 002 FR-018, FR-019; task T043)."""

from datetime import datetime

import pytest
from sqlalchemy import select

from app.lib import timeutil
from app.lib.timeutil import TZ
from app.models import Tag, Task
from tests.integration.helpers import create_semester, create_subject, create_task

NOW = datetime(2026, 11, 9, 4, 0, tzinfo=TZ)  # Thứ Hai 09/11/2026 04:00
WINDOW = {"work_date": "2026-11-12", "work_start": "19:00", "work_end": "21:00"}
NO_WINDOW = {"work_date": None, "work_start": None, "work_end": None}


@pytest.fixture(autouse=True)
def fixed_now(monkeypatch):
    monkeypatch.setattr(timeutil, "now", lambda: NOW)


def task_of(resp) -> dict:
    """POST/PATCH trả task, hoặc `{task, warnings}` khi có cảnh báo."""
    body = resp.get_json()
    return body["task"] if "warnings" in body else body


def test_create_and_patch_work_window(client, db_session):
    task = create_task(client, db_session, "Ôn thi", due_date="2026-11-15", **WINDOW)
    assert (task["work_date"], task["work_start"], task["work_end"]) == (
        "2026-11-12",
        "19:00",
        "21:00",
    )
    resp = client.patch(f"/api/tasks/{task['id']}", json={"work_end": "22:30"})
    assert resp.status_code == 200 and task_of(resp)["work_end"] == "22:30"

    resp = client.patch(f"/api/tasks/{task['id']}", json=NO_WINDOW)
    assert resp.status_code == 200
    assert task_of(resp)["work_date"] is None and task_of(resp)["work_start"] is None


@pytest.mark.parametrize(
    "fields",
    [
        {"work_date": "2026-11-12"},
        {"work_date": "2026-11-12", "work_start": "19:00"},
        {"work_start": "19:00", "work_end": "21:00"},
    ],
)
def test_incomplete_work_window_rejected(client, db_session, fields):
    resp = client.post(
        "/api/tasks", json={"title": "Ôn thi", "list_id": _study(db_session), **fields}
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"]["fields"] == {
        "work_date": "Cần chọn đủ ngày, giờ bắt đầu và giờ kết thúc"
    }


@pytest.mark.parametrize("end", ["19:00", "18:00"])
def test_work_end_must_follow_start(client, db_session, end):
    task = create_task(client, db_session, "Ôn thi", **WINDOW)
    resp = client.patch(f"/api/tasks/{task['id']}", json={"work_end": end})
    assert resp.status_code == 400
    assert resp.get_json()["error"]["fields"] == {"work_end": "Giờ kết thúc phải sau giờ bắt đầu"}
    # Bỏ một trường khi các trường khác vẫn còn cũng bị từ chối.
    resp = client.patch(f"/api/tasks/{task['id']}", json={"work_start": None})
    assert resp.status_code == 400


def test_work_after_due_is_a_warning(client, db_session):
    resp = client.post(
        "/api/tasks",
        json={
            "title": "Làm muộn",
            "list_id": _study(db_session),
            "due_date": "2026-11-11",
            **WINDOW,
        },
    )
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["warnings"] == [{"code": "work_after_due", "message": "Khung giờ làm sau hạn chót"}]
    assert body["task"]["work_date"] == "2026-11-12"
    # Không có cảnh báo → giữ dạng trả cũ (chỉ task).
    resp = client.patch(f"/api/tasks/{body['task']['id']}", json={"due_date": "2026-11-13"})
    assert "warnings" not in resp.get_json() and resp.get_json()["due_date"] == "2026-11-13"


def test_work_window_does_not_change_reminders_or_sync(client, db_session):
    client.patch(
        "/api/settings", json={"calendar_sync_enabled": True, "daily_digest_enabled": True}
    )
    task = create_task(client, db_session, "Nộp báo cáo", due_date="2026-11-09", due_time="17:00")
    feed_before = client.get("/api/sync/feed").get_json()["reminders"]
    digest_before = client.get("/api/digest?date=2026-11-09").get_json()

    resp = client.patch(
        f"/api/tasks/{task['id']}",
        json={"work_date": "2026-11-09", "work_start": "13:00", "work_end": "15:00"},
    )
    after = task_of(resp)
    assert after["reminder_times"] == task["reminder_times"]
    assert after["is_overdue"] == task["is_overdue"] and after["due_at"] == task["due_at"]
    assert client.get("/api/sync/feed").get_json()["reminders"] == feed_before
    assert client.get("/api/digest?date=2026-11-09").get_json() == digest_before


def test_editing_work_window_marks_auto_task_modified(client, db_session):
    e_learning = db_session.scalars(select(Tag).where(Tag.system_key == "e_learning")).one().id
    semester_id = create_semester(client, "2026-11-02", "2026-11-29", "HK test")
    create_subject(client, semester_id, name="Triết học", weekdays=[2], tag_ids=[e_learning])
    auto = db_session.scalars(select(Task).where(Task.is_auto).order_by(Task.due_date)).first()
    assert auto.user_modified is False
    resp = client.patch(f"/api/tasks/{auto.id}", json=WINDOW)
    assert resp.status_code == 200
    assert task_of(resp)["user_modified"] is True


def test_today_and_calendar_include_work_window(client, db_session):
    worked_today = create_task(
        client,
        db_session,
        "Làm hôm nay, hạn tuần sau",
        due_date="2026-11-16",
        work_date="2026-11-09",
        work_start="19:00",
        work_end="21:00",
    )
    both_in_range = create_task(
        client,
        db_session,
        "Làm và hạn cùng tuần",
        due_date="2026-11-13",
        work_date="2026-11-10",
        work_start="08:00",
        work_end="09:00",
    )
    no_due = create_task(
        client,
        db_session,
        "Chỉ có khung giờ làm",
        work_date="2026-11-11",
        work_start="08:00",
        work_end="09:00",
    )
    today = client.get("/api/today").get_json()
    assert worked_today["id"] in {t["id"] for t in today["tasks_due_today"]}

    calendar = client.get("/api/calendar?from=2026-11-09&to=2026-11-15").get_json()
    calendar_ids = [t["id"] for t in calendar["tasks"]]
    assert sorted(calendar_ids) == sorted([worked_today["id"], both_in_range["id"], no_due["id"]])


def _study(db_session) -> int:
    from tests.factories import study_list

    return study_list(db_session).id
