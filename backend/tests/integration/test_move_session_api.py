"""Dời buổi học sang ngày khác (feature 002 FR-028, research R8)."""

from app.services.revision import current_revision
from tests.integration.helpers import create_semester, create_subject, sessions_of


def setup_subject(client, **fields):
    semester_id = create_semester(client)
    subject = create_subject(client, semester_id, **fields)
    return subject["id"], sessions_of(client, subject["id"])


def patch(client, session_id, body):
    return client.patch(f"/api/sessions/{session_id}", json=body)


def test_move_to_another_day_sets_original_date_and_bumps_revision(client, db_session):
    subject_id, sessions = setup_subject(client)
    target = sessions[10]  # Thứ Hai 16/11/2026
    assert target["date"] == "2026-11-16" and target["original_date"] is None
    before = current_revision(db_session)

    resp = patch(
        client, target["id"], {"date": "2026-11-21", "start_time": "08:00", "end_time": "10:40"}
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["warnings"] == []
    moved = body["session"]
    assert moved["date"] == "2026-11-21"
    assert moved["start_at"] == "2026-11-21T08:00:00+07:00"
    assert moved["end_at"] == "2026-11-21T10:40:00+07:00"
    assert moved["original_date"] == "2026-11-16" and moved["is_moved"] is True
    assert moved["time_overridden"] is True
    assert current_revision(db_session) == before + 1

    # Các buổi khác không đổi; sync feed có sự kiện ở ngày mới.
    others = [s for s in sessions_of(client, subject_id) if s["id"] != target["id"]]
    assert all(not s["is_moved"] for s in others)
    feed = client.get("/api/sync/feed").get_json()
    starts = [e["start_at"] for e in feed["events"] if e["sync_key"] == f"session:{target['id']}"]
    assert starts == ["2026-11-21T08:00:00+07:00"]


def test_move_date_only_keeps_time_of_day(client):
    _, sessions = setup_subject(client)
    moved = patch(client, sessions[3]["id"], {"date": "2026-10-03"}).get_json()["session"]
    assert moved["start_at"] == "2026-10-03T06:45:00+07:00"
    assert moved["time_overridden"] is False and moved["is_moved"] is True


def test_move_back_to_original_date_clears_original_date(client):
    _, sessions = setup_subject(client)
    target = sessions[10]
    patch(client, target["id"], {"date": "2026-11-21"})
    back = patch(client, target["id"], {"date": "2026-11-16"}).get_json()["session"]
    assert back["date"] == "2026-11-16"
    assert back["original_date"] is None and back["is_moved"] is False


def test_move_twice_keeps_the_first_original_date(client):
    _, sessions = setup_subject(client)
    target = sessions[10]
    patch(client, target["id"], {"date": "2026-11-21"})
    second = patch(client, target["id"], {"date": "2026-11-25"}).get_json()["session"]
    assert second["original_date"] == "2026-11-16" and second["date"] == "2026-11-25"


def test_duplicate_slot_is_rejected(client):
    _, sessions = setup_subject(client)
    # Dời buổi 16/11 sang 23/11 06:45 — trùng buổi 23/11 của cùng môn.
    resp = patch(client, sessions[10]["id"], {"date": sessions[11]["date"]})
    assert resp.status_code == 400
    assert resp.get_json()["error"]["fields"]["date"] == "Môn này đã có buổi học vào ngày và giờ đó"
    assert sessions_of(client, sessions[10]["subject_id"])[10]["date"] == "2026-11-16"


def test_outside_semester_succeeds_with_warning(client):
    _, sessions = setup_subject(client)
    resp = patch(client, sessions[0]["id"], {"date": "2027-01-09"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert [w["code"] for w in body["warnings"]] == ["outside_semester"]
    assert body["session"]["date"] == "2027-01-09"


def test_moved_session_survives_subject_schedule_change(client):
    subject_id, sessions = setup_subject(client)
    target = sessions[10]
    patch(client, target["id"], {"date": "2026-11-21"})

    resp = client.patch(f"/api/subjects/{subject_id}", json={"room": "B9-101"})
    assert resp.status_code == 200
    after = sessions_of(client, subject_id)
    assert len(after) == len(sessions)  # không sinh buổi mới ở ngày gốc 16/11
    assert all(s["date"] != "2026-11-16" for s in after)
    moved = next(s for s in after if s["id"] == target["id"])
    assert moved["date"] == "2026-11-21" and moved["is_moved"] is True and moved["room"] == "B9-101"


def test_response_is_session_and_warnings_for_every_patch(client):
    _, sessions = setup_subject(client)
    body = patch(client, sessions[0]["id"], {"room": "Z1"}).get_json()
    assert set(body) == {"session", "warnings"} and body["session"]["room"] == "Z1"
