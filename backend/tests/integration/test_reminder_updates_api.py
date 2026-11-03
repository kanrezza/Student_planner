"""Nhắc cập nhật ngay khi dữ liệu đổi (FR-023): kiểm tra ngay sau request ghi, không chờ.
Phần buổi thi được kiểm tra cùng US11."""

from datetime import datetime

import pytest

from app.lib import timeutil
from app.lib.timeutil import TZ
from app.services.revision import current_revision
from tests.integration.helpers import create_semester, create_subject, create_task, sessions_of

NOW = datetime(2026, 11, 9, 5, 0, tzinfo=TZ)


@pytest.fixture(autouse=True)
def fixed_now(monkeypatch):
    monkeypatch.setattr(timeutil, "now", lambda: NOW)


def keys_upcoming(client):
    return {r["sync_key"]: r["fire_at"] for r in client.get("/api/reminders/upcoming").get_json()}


def feed_keys(client):
    data = client.get("/api/sync/feed").get_json()
    return {i["sync_key"]: i for i in data["events"] + data["reminders"]}


def test_changes_reflect_immediately(client, db_session):
    subject = create_subject(client, create_semester(client, "2026-11-02", "2026-11-29", "HK"))
    today_session = sessions_of(client, subject["id"])[1]  # 09/11
    key = f"session:{today_session['id']}"
    task = create_task(client, db_session, due_date="2026-11-09", due_time="20:00")
    task_key = f"task:{task['id']}"
    assert key in keys_upcoming(client) and task_key in keys_upcoming(client)

    def step(action):
        before = current_revision(db_session)
        action()
        assert current_revision(db_session) > before

    step(lambda: client.post(f"/api/sessions/{today_session['id']}/cancel"))
    assert key not in keys_upcoming(client) and key not in feed_keys(client)
    step(lambda: client.post(f"/api/sessions/{today_session['id']}/restore"))
    assert key in keys_upcoming(client)

    step(
        lambda: client.patch(
            f"/api/sessions/{today_session['id']}",
            json={"start_time": "08:00", "end_time": "09:30"},
        )
    )
    assert keys_upcoming(client)[key] == "2026-11-09T07:45:00+07:00"
    assert feed_keys(client)[key]["start_at"] == "2026-11-09T08:00:00+07:00"

    step(lambda: client.patch(f"/api/tasks/{task['id']}", json={"due_time": "21:00"}))
    assert feed_keys(client)[task_key]["alarms_at"] == ["2026-11-09T20:00:00+07:00"]

    step(lambda: client.post(f"/api/tasks/{task['id']}/complete"))
    assert task_key not in keys_upcoming(client) and task_key not in feed_keys(client)
    step(lambda: client.post(f"/api/tasks/{task['id']}/uncomplete"))
    assert task_key in feed_keys(client)
    step(lambda: client.delete(f"/api/tasks/{task['id']}"))
    assert task_key not in feed_keys(client)

    step(lambda: client.delete(f"/api/subjects/{subject['id']}"))
    assert not any(k.startswith("session:") for k in feed_keys(client))
