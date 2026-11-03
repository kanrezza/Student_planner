import time as clock
from datetime import datetime, timedelta

import pytest

from app.lib import timeutil
from app.lib.timeutil import TZ
from app.models import AgentStatus
from app.services.revision import current_revision
from tests.integration.helpers import create_semester, create_subject, create_task, sessions_of

NOW = datetime(2026, 11, 9, 7, 0, tzinfo=TZ)  # Thứ Hai 09/11/2026 07:00

EVENT_KEYS = {
    "sync_key",
    "fingerprint",
    "title",
    "location",
    "start_at",
    "end_at",
    "alarms_minutes_before",
}
REMINDER_KEYS = {"sync_key", "fingerprint", "title", "due_at", "due_has_time", "alarm_at"}


@pytest.fixture(autouse=True)
def fixed_now(monkeypatch):
    monkeypatch.setattr(timeutil, "now", lambda: NOW)


def feed(client):
    return client.get("/api/sync/feed").get_json()


def test_revision_bumps_on_every_kind_of_change(client, db_session):
    def bumped(action):
        before = current_revision(db_session)
        action()
        return current_revision(db_session) > before

    semester_id = None

    def make_semester():
        nonlocal semester_id
        semester_id = create_semester(client, "2026-11-02", "2026-12-20", "HK")

    assert bumped(make_semester)
    subject = {}
    assert bumped(lambda: subject.update(create_subject(client, semester_id)))
    session_id = sessions_of(client, subject["id"])[2]["id"]
    assert bumped(lambda: client.post(f"/api/sessions/{session_id}/cancel"))
    task = {}
    assert bumped(lambda: task.update(create_task(client, db_session, due_date="2026-11-10")))
    assert bumped(lambda: client.post(f"/api/tasks/{task['id']}/complete"))
    assert bumped(lambda: client.patch("/api/shifts/1?confirm=true", json={"start_time": "06:40"}))
    assert bumped(lambda: client.patch("/api/settings", json={"calendar_sync_enabled": True}))


def test_long_poll(client, db_session):
    rev = current_revision(db_session)
    started = clock.monotonic()
    data = client.get(f"/api/sync/changes?after={rev - 1}&wait=5").get_json()
    assert data["revision"] == rev and clock.monotonic() - started < 1  # trả ngay
    started = clock.monotonic()
    data = client.get(f"/api/sync/changes?after={rev}&wait=1").get_json()
    assert data["revision"] == rev and clock.monotonic() - started >= 0.9  # chờ rồi trả
    assert data["sync_enabled"] is False


def test_feed_content_is_minimal_and_filtered(client, db_session):
    semester_id = create_semester(client, "2026-11-02", "2026-11-29", "HK")
    subject = create_subject(
        client, semester_id, lecturer="ThS. Nguyễn Văn An", class_code="MAT1101(N01)"
    )
    sessions = sessions_of(client, subject["id"])  # 02, 09, 16, 23/11
    client.post(f"/api/sessions/{sessions[2]['id']}/cancel")
    create_task(
        client,
        db_session,
        "Có giờ",
        due_date="2026-11-10",
        due_time="17:00",
        notes="ghi chú riêng tư",
    )
    create_task(client, db_session, "Chỉ ngày", due_date="2026-11-11")
    done = create_task(client, db_session, "Đã xong", due_date="2026-11-12")
    client.post(f"/api/tasks/{done['id']}/complete")
    create_task(client, db_session, "Không hạn")

    data = feed(client)
    assert data["calendar_name"] == data["reminder_list_name"] == "Lịch Học Cá Nhân"
    events = data["events"]
    assert [e["start_at"][:10] for e in events] == [
        "2026-11-09",
        "2026-11-23",
    ]  # bỏ 02/11, buổi huỷ
    assert all(set(e) == EVENT_KEYS for e in events)
    assert events[0] == {
        **events[0],
        "sync_key": f"session:{sessions[1]['id']}",
        "title": "Giải tích 1",
        "location": "A2-301",
        "alarms_minutes_before": [15],
    }
    reminders = {r["title"]: r for r in data["reminders"]}
    assert set(reminders) == {"Có giờ", "Chỉ ngày"}
    assert all(set(r) == REMINDER_KEYS for r in reminders.values())
    assert reminders["Có giờ"]["alarm_at"] == "2026-11-10T16:00:00+07:00"
    assert reminders["Chỉ ngày"] == {
        **reminders["Chỉ ngày"],
        "due_has_time": False,
        "alarm_at": "2026-11-11T08:00:00+07:00",
    }
    assert "ghi chú" not in str(data) and "Nguyễn Văn An" not in str(data)


def test_fingerprint_stable_and_changes_with_room(client):
    semester_id = create_semester(client, "2026-11-02", "2026-11-29", "HK")
    subject = create_subject(client, semester_id)
    first = feed(client)["events"][0]
    assert feed(client)["events"][0]["fingerprint"] == first["fingerprint"]
    session_id = int(first["sync_key"].split(":")[1])
    client.patch(f"/api/sessions/{session_id}", json={"room": "C1-204"})
    assert feed(client)["events"][0]["fingerprint"] != first["fingerprint"]
    assert subject["id"]


def test_agent_status_and_today_notices(client, db_session):
    client.patch("/api/settings", json={"calendar_sync_enabled": True})
    notices = client.get("/api/today").get_json()["notices"]
    assert [n["code"] for n in notices] == ["agent_offline"]

    resp = client.put(
        "/api/sync/agent-status",
        json={
            "permission": "denied",
            "icloud_source": "unknown",
            "last_synced_revision": 0,
            "last_error": None,
            "agent_version": "0.1.0",
        },
    )
    assert resp.status_code == 204
    status = db_session.get(AgentStatus, 1)
    db_session.refresh(status)
    assert status.last_seen_at is not None and status.permission == "denied"
    notices = client.get("/api/today").get_json()["notices"]
    assert [n["code"] for n in notices] == ["permission_denied"]

    client.put(
        "/api/sync/agent-status",
        json={"permission": "granted", "icloud_source": "icloud", "last_synced_revision": 5},
    )
    assert client.get("/api/today").get_json()["notices"] == []
    status = client.get("/api/sync/status").get_json()
    assert status["agent_online"] is True and status["sync_enabled"] is True

    status_row = db_session.get(AgentStatus, 1)
    status_row.last_seen_at = NOW - timedelta(minutes=5)
    db_session.commit()
    assert client.get("/api/sync/status").get_json()["agent_online"] is False


def test_browser_reminders_only_when_sync_off(client, db_session):
    create_task(client, db_session, "Sắp tới", due_date="2026-11-09", due_time="09:00")
    upcoming = client.get("/api/reminders/upcoming?hours=24").get_json()
    assert [(r["kind"], r["title"], r["fire_at"]) for r in upcoming] == [
        ("task", "Sắp tới", "2026-11-09T08:00:00+07:00")
    ]
    client.patch("/api/settings", json={"calendar_sync_enabled": True})
    assert client.get("/api/reminders/upcoming?hours=24").get_json() == []
