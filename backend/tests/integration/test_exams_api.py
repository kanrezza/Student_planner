from datetime import datetime

import pytest

from app.lib import timeutil
from app.lib.timeutil import TZ
from app.services.revision import current_revision
from tests.integration.helpers import create_semester, create_subject, sessions_of

NOW = datetime(2026, 11, 9, 5, 0, tzinfo=TZ)


@pytest.fixture(autouse=True)
def fixed_now(monkeypatch):
    monkeypatch.setattr(timeutil, "now", lambda: NOW)


def make_exam(client, **fields):
    body = {
        "course_name": "Cơ sở dữ liệu",
        "date": "2026-11-20",
        "start_time": "07:30",
        "end_time": "08:30",
        **fields,
    }
    resp = client.post("/api/exams", json=body)
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()


def exam_tag_id(client):
    return next(t["id"] for t in client.get("/api/tags").get_json() if t["system_key"] == "exam")


def test_create_update_delete_bump_revision(client, db_session):
    r0 = current_revision(db_session)
    exam = make_exam(client, room="A5-310", course_code="CSE2301")["exam"]
    assert current_revision(db_session) == r0 + 1
    assert exam["is_important"] is True and exam["attempt"] == 1
    assert exam["start_at"] == "2026-11-20T07:30:00+07:00"

    resp = client.patch(f"/api/exams/{exam['id']}", json={"room": "B2-101", "end_time": "09:00"})
    assert resp.status_code == 200
    assert resp.get_json()["exam"]["room"] == "B2-101"
    assert current_revision(db_session) == r0 + 2

    assert client.delete(f"/api/exams/{exam['id']}").status_code == 204
    assert current_revision(db_session) == r0 + 3
    assert client.get("/api/exams").get_json()["exams"] == []


def test_validation_errors(client):
    def post(**fields):
        body = {
            "course_name": "X",
            "date": "2026-11-20",
            "start_time": "07:30",
            "end_time": "08:30",
            **fields,
        }
        return client.post("/api/exams", json=body)

    assert post(course_name="").get_json()["error"]["fields"]["course_name"]
    assert post(end_time="07:30").get_json()["error"]["fields"]["end_time"]
    assert post(attempt=0).status_code == 400
    assert post(room="").status_code == 201  # phòng trống được chấp nhận


def test_exam_tag_always_first(client):
    thi = exam_tag_id(client)
    other = client.post("/api/tags", json={"name": "Quan trọng nhất"}).get_json()["id"]
    exam = make_exam(client, tag_ids=[other])["exam"]
    assert [t["id"] for t in exam["tags"]] == [thi, other]
    resp = client.put(f"/api/exams/{exam['id']}/tags", json={"tag_ids": []})
    assert [t["id"] for t in resp.get_json()["tags"]] == [thi]
    assert client.delete(f"/api/tags/{thi}").status_code == 400


def test_time_conflict_with_session_and_exam(client):
    semester = create_semester(client, "2026-11-02", "2026-11-29", "HK")
    subject = create_subject(client, semester, weekdays=[5], start_time="07:00", end_time="09:00")
    friday = next(s for s in sessions_of(client, subject["id"]) if s["date"] == "2026-11-20")

    body = make_exam(client)  # 07:30–08:30 trùng buổi học 07:00–09:00
    assert body["warnings"][0]["code"] == "time_conflict"
    assert body["conflicts"][0]["kind"] == "session"

    # buổi học đã huỷ thì không còn cảnh báo
    client.post(f"/api/sessions/{friday['id']}/cancel")
    assert (
        make_exam(client, course_name="Đại số", start_time="12:00", end_time="13:00")["warnings"]
        == []
    )
    second = make_exam(client, course_name="Vật lý", start_time="12:30", end_time="13:30")
    assert second["conflicts"][0]["kind"] == "exam"


def test_today_and_calendar_include_exams(client):
    make_exam(client, date="2026-11-09", start_time="10:00", end_time="11:00", course_name="Sớm")
    make_exam(client, date="2026-11-09", start_time="08:00", end_time="09:00", course_name="Trước")
    make_exam(client, date="2026-11-12")
    today = client.get("/api/today").get_json()["exams"]
    assert [e["course_name"] for e in today] == ["Trước", "Sớm"]

    cal = client.get("/api/calendar?from=2026-11-09&to=2026-11-15").get_json()["exams"]
    assert len(cal) == 3
    thi = exam_tag_id(client)
    filtered = client.get(f"/api/calendar?from=2026-11-09&to=2026-11-15&tags={thi}").get_json()
    assert len(filtered["exams"]) == 3
    other = client.post("/api/tags", json={"name": "Khác"}).get_json()["id"]
    empty = client.get(f"/api/calendar?from=2026-11-09&to=2026-11-15&tags={other}").get_json()
    assert empty["exams"] == []


def test_list_hides_past_by_default(client):
    make_exam(client, date="2026-11-01", course_name="Đã qua")
    make_exam(client, date="2026-11-20", course_name="Sắp tới")
    names = [e["course_name"] for e in client.get("/api/exams").get_json()["exams"]]
    assert names == ["Sắp tới"]
    everything = client.get("/api/exams?include_past=true").get_json()["exams"]
    assert [e["course_name"] for e in everything] == ["Đã qua", "Sắp tới"]
    assert everything[0]["is_past"] is True


def test_reminders_feed_and_digest(client):
    exam = make_exam(client, date="2026-11-20", course_name="Giải tích", room="A1-101")["exam"]
    feed = client.get("/api/sync/feed").get_json()
    event = next(e for e in feed["events"] if e["sync_key"] == f"exam:{exam['id']}")
    assert event["title"] == "★ Thi: Giải tích"
    assert event["alarms_minutes_before"] == [10080, 1440, 180, 60, 15]
    assert set(event) == {
        "sync_key",
        "title",
        "location",
        "start_at",
        "end_at",
        "important",
        "alarms_minutes_before",
        "fingerprint",
    }  # không có số báo danh, hình thức thi (FR-064)

    # Đổi sang không quan trọng → một mốc; tắt nhắc → không mốc; revision tăng
    r0 = current_revision(client.application.extensions["sqlalchemy"].session)
    client.patch(f"/api/exams/{exam['id']}", json={"is_important": False})
    event = next(
        e
        for e in client.get("/api/sync/feed").get_json()["events"]
        if e["sync_key"].startswith("exam:")
    )
    assert event["alarms_minutes_before"] == [60] and not event["title"].startswith("★")
    client.patch(f"/api/exams/{exam['id']}", json={"reminder_offsets": []})
    event = next(
        e
        for e in client.get("/api/sync/feed").get_json()["events"]
        if e["sync_key"].startswith("exam:")
    )
    assert event["alarms_minutes_before"] == []
    assert current_revision(client.application.extensions["sqlalchemy"].session) > r0

    digest = next(
        d for d in client.get("/api/sync/feed").get_json()["digests"] if d["date"] == "2026-11-20"
    )
    assert digest["title"].startswith("★ Hôm nay: Thi Giải tích 07:30 A1-101")


def test_upcoming_reminders_for_exam(client):
    make_exam(client, date="2026-11-09", start_time="06:30", end_time="07:30", course_name="Sáng")
    keys = {r["sync_key"] for r in client.get("/api/reminders/upcoming?hours=3").get_json()}
    assert any(k.startswith("exam:") for k in keys)
