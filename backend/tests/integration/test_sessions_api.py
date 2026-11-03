from app.services.revision import current_revision
from tests.integration.helpers import create_semester, create_subject, sessions_of


def setup_subject(client):
    semester_id = create_semester(client)
    subject = create_subject(client, semester_id)
    return subject["id"], sessions_of(client, subject["id"])


def test_cancel_and_restore_only_affect_one_session(client, db_session):
    subject_id, sessions = setup_subject(client)
    target = sessions[10]  # 16/11/2026
    assert target["date"] == "2026-11-16"
    before = current_revision(db_session)

    resp = client.post(f"/api/sessions/{target['id']}/cancel")
    assert resp.status_code == 200
    assert resp.get_json()["is_cancelled"] is True
    assert current_revision(db_session) == before + 1
    after = sessions_of(client, subject_id)
    assert [s["is_cancelled"] for s in after].count(True) == 1

    resp = client.post(f"/api/sessions/{target['id']}/restore")
    assert resp.get_json()["is_cancelled"] is False


def test_patch_time_and_room_sets_overrides(client):
    subject_id, sessions = setup_subject(client)
    target = sessions[11]  # 23/11/2026

    resp = client.patch(
        f"/api/sessions/{target['id']}", json={"start_time": "07:00", "end_time": "09:00"}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["start_at"] == "2026-11-23T07:00:00+07:00"
    assert data["end_at"] == "2026-11-23T09:00:00+07:00"
    assert data["time_overridden"] is True and data["room_overridden"] is False
    assert data["shift_label"] is None

    data = client.patch(f"/api/sessions/{target['id']}", json={"room": "C1-204"}).get_json()
    assert data["room"] == "C1-204" and data["room_overridden"] is True

    others = [s for s in sessions_of(client, subject_id) if s["id"] != target["id"]]
    assert all(s["room"] == "A2-301" and not s["time_overridden"] for s in others)


def test_only_one_time_field_keeps_the_other(client):
    _, sessions = setup_subject(client)
    data = client.patch(f"/api/sessions/{sessions[0]['id']}", json={"end_time": "10:00"}).get_json()
    assert data["start_at"].endswith("06:45:00+07:00")
    assert data["end_at"].endswith("10:00:00+07:00")


def test_get_single_session(client):
    _, sessions = setup_subject(client)
    data = client.get(f"/api/sessions/{sessions[2]['id']}").get_json()
    assert data["date"] == sessions[2]["date"] and data["subject_name"] == "Giải tích 1"
    assert client.get("/api/sessions/999999").status_code == 404


def test_invalid_times_rejected(client):
    _, sessions = setup_subject(client)
    resp = client.patch(
        f"/api/sessions/{sessions[0]['id']}", json={"start_time": "09:00", "end_time": "08:00"}
    )
    assert resp.status_code == 400
    assert "end_time" in resp.get_json()["error"]["fields"]
    assert client.patch("/api/sessions/999999", json={"room": "X"}).status_code == 404


def test_restore_keeps_overrides_and_subject_edit_keeps_exceptions(client):
    subject_id, sessions = setup_subject(client)
    cancelled, moved = sessions[10], sessions[11]
    client.patch(f"/api/sessions/{cancelled['id']}", json={"room": "Phòng riêng"})
    client.post(f"/api/sessions/{cancelled['id']}/cancel")
    client.patch(f"/api/sessions/{moved['id']}", json={"room": "C1-204"})

    client.patch(f"/api/subjects/{subject_id}", json={"room": "B5-101"})
    after = {s["id"]: s for s in sessions_of(client, subject_id)}
    assert after[cancelled["id"]]["is_cancelled"] is True
    assert after[moved["id"]]["room"] == "C1-204"
    assert after[sessions[0]["id"]]["room"] == "B5-101"

    restored = client.post(f"/api/sessions/{cancelled['id']}/restore").get_json()
    assert restored["is_cancelled"] is False and restored["room"] == "Phòng riêng"
