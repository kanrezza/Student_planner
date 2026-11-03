"""Tóm tắt hằng ngày và mức "Quan trọng" qua API (FR-065 đến FR-070, task T150)."""

from datetime import datetime

import pytest

from app.lib import timeutil
from app.lib.timeutil import TZ
from app.services.revision import current_revision
from tests.integration.helpers import create_semester, create_subject, create_task, sessions_of

NOW = datetime(2026, 11, 9, 4, 0, tzinfo=TZ)  # Thứ Hai, trước giờ tổng hợp 05:00


@pytest.fixture(autouse=True)
def fixed_now(monkeypatch):
    monkeypatch.setattr(timeutil, "now", lambda: NOW)


def feed(client):
    return client.get("/api/sync/feed").get_json()


def by_key(items):
    return {i["sync_key"]: i for i in items}


def bumps(db_session, action):
    before = current_revision(db_session)
    action()
    return current_revision(db_session) > before


def monday_subject(client):
    # Thứ Hai 06:45–09:25: các buổi 02, 09, 16, 23/11.
    return create_subject(client, create_semester(client, "2026-11-02", "2026-11-29", "HK"))


def test_important_flags_change_feed(client, db_session):
    subject = monday_subject(client)
    sessions = sessions_of(client, subject["id"])
    task = create_task(client, db_session, "Nộp báo cáo", due_date="2026-11-12", due_time="17:00")

    assert bumps(
        db_session,
        lambda: client.patch(f"/api/tasks/{task['id']}", json={"is_important": True}),
    )
    reminder = by_key(feed(client)["reminders"])[f"task:{task['id']}"]
    assert reminder["important"] is True
    assert reminder["alarms_at"] == [
        "2026-11-11T17:00:00+07:00",
        "2026-11-12T14:00:00+07:00",
        "2026-11-12T16:00:00+07:00",
        "2026-11-12T16:45:00+07:00",
    ]

    assert bumps(
        db_session,
        lambda: client.patch(f"/api/subjects/{subject['id']}", json={"is_important": True}),
    )
    events = by_key(feed(client)["events"])
    key_16 = f"session:{sessions[2]['id']}"
    assert events[key_16]["title"] == "★ Giải tích 1"
    assert events[key_16]["important"] is True
    assert events[key_16]["alarms_minutes_before"] == [1440, 180, 60, 15]

    # Đặt riêng buổi 16/11 là không quan trọng.
    assert bumps(
        db_session,
        lambda: client.patch(
            f"/api/sessions/{sessions[2]['id']}", json={"important_override": False}
        ),
    )
    events = by_key(feed(client)["events"])
    assert events[key_16]["title"] == "Giải tích 1"
    assert events[key_16]["alarms_minutes_before"] == [15]
    assert events[f"session:{sessions[3]['id']}"]["important"] is True
    detail = client.get(f"/api/sessions/{sessions[2]['id']}").get_json()
    assert detail["is_important"] is False and detail["important_override"] is False
    assert detail["subject_is_important"] is True

    # null = quay về theo môn.
    client.patch(f"/api/sessions/{sessions[2]['id']}", json={"important_override": None})
    assert by_key(feed(client)["events"])[key_16]["important"] is True


def test_important_shown_on_today_and_calendar(client, db_session):
    subject = monday_subject(client)
    client.patch(f"/api/subjects/{subject['id']}", json={"is_important": True})
    create_task(client, db_session, "Gấp", due_date="2026-11-09", is_important=True)
    today = client.get("/api/today").get_json()
    assert today["sessions"][0]["is_important"] is True
    assert today["tasks_due_today"][0]["is_important"] is True
    cal = client.get("/api/calendar?from=2026-11-09&to=2026-11-15").get_json()
    assert cal["sessions"][0]["is_important"] is True


def test_digests_in_feed_follow_data_and_settings(client, db_session):
    subject = monday_subject(client)
    sessions = sessions_of(client, subject["id"])
    digests = by_key(feed(client)["digests"])
    assert set(digests) == {"digest:2026-11-09", "digest:2026-11-16"}  # 23/11 ngoài 14 ngày
    first = digests["digest:2026-11-09"]
    assert first["title"] == "Hôm nay: 06:45 Giải tích 1 A2-301"
    assert first["notes"] == "06:45: Giải tích 1 – A2-301"
    assert first["alarm_at"] == "2026-11-09T05:00:00+07:00"

    client.post(f"/api/sessions/{sessions[2]['id']}/cancel")
    assert set(by_key(feed(client)["digests"])) == {"digest:2026-11-09"}

    assert bumps(
        db_session, lambda: client.patch("/api/settings", json={"daily_digest_time": "06:30"})
    )
    assert feed(client)["digests"][0]["alarm_at"] == "2026-11-09T06:30:00+07:00"

    client.patch("/api/settings", json={"daily_digest_enabled": False})
    assert feed(client)["digests"] == []


def test_task_titles_and_overdue_only_option(client, db_session):
    monday_subject(client)
    old = create_task(client, db_session, "Bài cũ", due_date="2026-11-05")
    digests = by_key(feed(client)["digests"])
    # Từ 09/11 mọi ngày đều có việc quá hạn.
    assert len(digests) == 14
    assert digests["digest:2026-11-10"]["notes"] == "Bài cũ – quá hạn từ 05/11"
    before = digests["digest:2026-11-09"]["fingerprint"]

    client.patch(f"/api/tasks/{old['id']}", json={"title": "Bài cũ (sửa)"})
    digests = by_key(feed(client)["digests"])
    assert digests["digest:2026-11-09"]["fingerprint"] != before
    assert "Bài cũ (sửa) (quá hạn)" in digests["digest:2026-11-09"]["title"]

    client.patch("/api/settings", json={"daily_digest_overdue_only": False})
    assert set(by_key(feed(client)["digests"])) == {"digest:2026-11-09", "digest:2026-11-16"}

    client.post(f"/api/tasks/{old['id']}/complete")
    client.patch("/api/settings", json={"daily_digest_overdue_only": True})
    assert set(by_key(feed(client)["digests"])) == {"digest:2026-11-09", "digest:2026-11-16"}


def test_digest_preview_endpoint(client):
    monday_subject(client)
    data = client.get("/api/digest?date=2026-11-09").get_json()
    assert data["empty"] is False
    assert data["lines"] == ["06:45: Giải tích 1 – A2-301"]
    assert data["fire_at"] == "2026-11-09T05:00:00+07:00"
    assert client.get("/api/digest?date=2026-11-10").get_json() == {
        "date": "2026-11-10",
        "empty": True,
    }
    assert client.get("/api/digest").get_json()["date"] == "2026-11-09"
    assert client.get("/api/digest?date=abc").status_code == 400
    # Xem trước vẫn chạy khi đang tắt thông báo tổng hợp.
    client.patch("/api/settings", json={"daily_digest_enabled": False})
    assert client.get("/api/digest?date=2026-11-09").get_json()["empty"] is False


def test_upcoming_has_digest_and_each_important_alarm(client, db_session):
    monday_subject(client)
    task = create_task(
        client, db_session, "Gấp", due_date="2026-11-09", due_time="20:00", is_important=True
    )
    upcoming = client.get("/api/reminders/upcoming?hours=24").get_json()
    keys = {i["sync_key"]: i for i in upcoming}
    assert keys["digest:2026-11-09"]["fire_at"] == "2026-11-09T05:00:00+07:00"
    assert keys["digest:2026-11-09"]["kind"] == "digest"
    assert {k for k in keys if k.startswith(f"task:{task['id']}:")} == {
        f"task:{task['id']}:180",
        f"task:{task['id']}:60",
        f"task:{task['id']}:15",
    }  # mốc 1 ngày trước đã qua
    assert keys[f"task:{task['id']}:60"]["important"] is True


def test_settings_validation_and_revision(client, db_session):
    assert bumps(
        db_session,
        lambda: client.patch("/api/settings", json={"important_reminder_offsets": [30, 120, 30]}),
    )
    assert client.get("/api/settings").get_json()["important_reminder_offsets"] == [120, 30]
    assert client.patch("/api/settings", json={"important_reminder_offsets": []}).status_code == 400
    too_many = [1, 2, 3, 4, 5, 6, 7]
    resp = client.patch("/api/settings", json={"important_reminder_offsets": too_many})
    assert resp.status_code == 400
    resp = client.patch("/api/settings", json={"important_reminder_offsets": [-5]})
    assert resp.status_code == 400
