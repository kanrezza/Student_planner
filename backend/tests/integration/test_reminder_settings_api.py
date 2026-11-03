"""Nhắc theo từng mục (FR-022). Phần buổi thi (reminder_offsets) được kiểm tra cùng US11."""

from datetime import datetime

import pytest

from app.lib import timeutil
from app.lib.timeutil import TZ
from app.services.revision import current_revision
from tests.integration.helpers import create_semester, create_subject, create_task

NOW = datetime(2026, 11, 9, 5, 0, tzinfo=TZ)  # Thứ Hai 05:00, trước buổi 06:45


@pytest.fixture(autouse=True)
def fixed_now(monkeypatch):
    monkeypatch.setattr(timeutil, "now", lambda: NOW)


def first_event(client):
    return client.get("/api/sync/feed").get_json()["events"][0]


def upcoming(client):
    return client.get("/api/reminders/upcoming?hours=24").get_json()


def test_subject_reminder_override_and_off(client):
    subject = create_subject(client, create_semester(client, "2026-11-02", "2026-11-29", "HK"))
    assert first_event(client)["alarms_minutes_before"] == [15]
    assert upcoming(client)[0]["fire_at"] == "2026-11-09T06:30:00+07:00"

    client.patch(f"/api/subjects/{subject['id']}", json={"reminder_minutes": 30})
    assert first_event(client)["alarms_minutes_before"] == [30]
    assert upcoming(client)[0]["fire_at"] == "2026-11-09T06:15:00+07:00"

    client.patch(f"/api/subjects/{subject['id']}", json={"reminder_minutes": -1})
    assert first_event(client)["alarms_minutes_before"] == []
    assert upcoming(client) == []


def test_task_reminder_override(client, db_session):
    timed = create_task(
        client, db_session, "Có giờ", due_date="2026-11-09", due_time="17:00", reminder_minutes=10
    )
    assert timed["reminder_at"] == "2026-11-09T16:50:00+07:00"
    date_only = create_task(
        client, db_session, "Chỉ ngày", due_date="2026-11-10", reminder_minutes=-1
    )
    assert date_only["reminder_at"] is None
    reminders = {r["title"]: r for r in client.get("/api/sync/feed").get_json()["reminders"]}
    assert reminders["Có giờ"]["alarm_at"] == "2026-11-09T16:50:00+07:00"
    assert reminders["Chỉ ngày"]["alarm_at"] is None


def test_default_session_minutes_change(client, db_session):
    create_subject(client, create_semester(client, "2026-11-02", "2026-11-29", "HK"))
    before = current_revision(db_session)
    client.patch("/api/settings", json={"session_reminder_minutes": 5})
    assert current_revision(db_session) == before + 1
    assert first_event(client)["alarms_minutes_before"] == [5]
