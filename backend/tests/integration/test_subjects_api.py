import pytest
from sqlalchemy import func, select

from app.models import ClassSession, Subject


@pytest.fixture
def semester_id(client):
    resp = client.post(
        "/api/semesters",
        json={"name": "HK1 2026–2027", "start_date": "2026-09-07", "end_date": "2026-12-20"},
    )
    return resp.get_json()["id"]


def subject_body(semester_id, **fields):
    return {
        "name": "Giải tích 1",
        "semester_id": semester_id,
        "class_code": "MAT1101-1-1-26(N01)",
        "lecturer": "ThS. Nguyễn Văn An",
        "room": "A2-301",
        "weekdays": [1],
        "start_time": "06:45",
        "end_time": "09:25",
        **fields,
    }


def test_create_generates_weekly_sessions(client, semester_id):
    resp = client.post("/api/subjects", json=subject_body(semester_id, weekdays=[1, 4]))
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["session_count"] == 30  # 15 Thứ Hai + 15 Thứ Năm
    assert data["warnings"] == []
    subject = data["subject"]
    assert subject["start_date"] == "2026-09-07" and subject["end_date"] == "2026-12-20"
    assert subject["color"] == "c01"

    detail = client.get(f"/api/subjects/{subject['id']}").get_json()
    first = detail["sessions"][0]
    assert first["date"] == "2026-09-07"
    assert first["start_at"] == "2026-09-07T06:45:00+07:00"
    assert first["end_at"] == "2026-09-07T09:25:00+07:00"
    assert first["room"] == "A2-301"
    assert first["subject_name"] == "Giải tích 1"


def test_defaults_to_current_semester(client, semester_id):
    body = subject_body(semester_id)
    del body["semester_id"]
    resp = client.post("/api/subjects", json=body)
    assert resp.status_code == 201
    assert resp.get_json()["subject"]["semester_id"] == semester_id


def test_no_semester_yet(client):
    resp = client.post("/api/subjects", json=subject_body(None))
    assert resp.status_code == 400
    assert "Chưa có học kỳ" in resp.get_json()["error"]["fields"]["semester_id"]


@pytest.mark.parametrize(
    "fields, bad_field",
    [
        ({"end_time": "06:45"}, "end_time"),
        ({"weekdays": []}, "weekdays"),
        ({"weekdays": [1, 1]}, "weekdays"),
        ({"weekdays": [8]}, "weekdays"),
        ({"start_date": "2026-09-01"}, "start_date"),
        ({"end_date": "2027-01-10"}, "end_date"),
        ({"shift": {"start_shift_id": 1, "end_shift_id": 1}}, "start_time"),
        ({"start_time": None, "end_time": None}, "start_time"),
        ({"name": "  "}, "name"),
    ],
)
def test_validation_errors(client, semester_id, fields, bad_field):
    resp = client.post("/api/subjects", json=subject_body(semester_id, **fields))
    assert resp.status_code == 400
    assert bad_field in resp.get_json()["error"]["fields"]


def test_shift_resolves_times(client, semester_id):
    body = subject_body(semester_id, shift={"start_shift_id": 1, "end_shift_id": 2})
    del body["start_time"], body["end_time"]
    subject = client.post("/api/subjects", json=body).get_json()["subject"]
    assert (subject["start_time"], subject["end_time"]) == ("06:45", "12:10")
    assert subject["shift_label"] == "Ca 1–2"


def test_bulk_is_all_or_nothing(client, db_session, semester_id):
    rows = [
        {"name": "Giải tích 1", "weekdays": [1], "start_time": "06:45", "end_time": "09:25"},
        {"name": "Triết học", "weekdays": [2], "start_time": "09:35", "end_time": "12:10"},
        {"name": "Cơ sở dữ liệu", "weekdays": [3], "start_time": "13:00", "end_time": "12:00"},
    ]
    resp = client.post("/api/subjects/bulk", json={"semester_id": semester_id, "rows": rows})
    assert resp.status_code == 400
    assert "rows[2].end_time" in resp.get_json()["error"]["fields"]
    assert db_session.scalar(select(func.count()).select_from(Subject)) == 0

    rows[2]["end_time"] = "15:40"
    resp = client.post(
        "/api/subjects/bulk",
        json={
            "semester_id": semester_id,
            "start_date": "2026-11-01",
            "end_date": "2026-11-30",
            "rows": rows,
        },
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert [s["name"] for s in data["subjects"]] == ["Giải tích 1", "Triết học", "Cơ sở dữ liệu"]
    # Tháng 11/2026: 5 Thứ Hai (2, 9, 16, 23, 30), 4 Thứ Ba, 4 Thứ Tư.
    assert data["session_count"] == 5 + 4 + 4


def test_time_conflict_warning_and_no_sessions_warning(client, semester_id):
    client.post("/api/subjects", json=subject_body(semester_id))
    resp = client.post(
        "/api/subjects",
        json=subject_body(semester_id, name="Vật lý", start_time="08:00", end_time="10:00"),
    )
    assert resp.status_code == 201
    warnings = resp.get_json()["warnings"]
    assert warnings[0]["code"] == "time_conflict"
    assert "Giải tích 1" in warnings[0]["message"]

    resp = client.post(
        "/api/subjects",
        json=subject_body(
            semester_id, name="Ngắn", weekdays=[1], start_date="2026-09-08", end_date="2026-09-10"
        ),
    )
    assert resp.get_json()["warnings"][0]["code"] == "no_sessions"


def test_patch_keeps_exceptions(client, db_session, semester_id):
    subject_id = client.post("/api/subjects", json=subject_body(semester_id)).get_json()["subject"][
        "id"
    ]
    sessions = db_session.scalars(
        select(ClassSession)
        .where(ClassSession.subject_id == subject_id)
        .order_by(ClassSession.date)
    ).all()
    sessions[1].is_cancelled = True
    sessions[2].room = "Phòng riêng"
    sessions[2].room_overridden = True
    db_session.commit()

    resp = client.patch(
        f"/api/subjects/{subject_id}", json={"room": "C1-204", "start_time": "07:00"}
    )
    assert resp.status_code == 200
    detail = client.get(f"/api/subjects/{subject_id}").get_json()["sessions"]
    assert detail[0]["room"] == "C1-204" and detail[0]["start_at"].endswith("07:00:00+07:00")
    assert detail[1]["is_cancelled"] is True
    assert detail[2]["room"] == "Phòng riêng" and detail[2]["start_at"].endswith("07:00:00+07:00")


def test_patch_out_of_range_exception_needs_confirm(client, db_session, semester_id):
    subject_id = client.post("/api/subjects", json=subject_body(semester_id)).get_json()["subject"][
        "id"
    ]
    last = db_session.scalars(
        select(ClassSession)
        .where(ClassSession.subject_id == subject_id)
        .order_by(ClassSession.date.desc())
    ).first()
    last.is_cancelled = True
    db_session.commit()

    resp = client.patch(f"/api/subjects/{subject_id}", json={"end_date": "2026-11-30"})
    assert resp.status_code == 409
    assert resp.get_json()["error"]["details"]["sessions"][0]["date"] == "2026-12-14"
    resp = client.patch(f"/api/subjects/{subject_id}?confirm=true", json={"end_date": "2026-11-30"})
    assert resp.status_code == 200
    assert resp.get_json()["session_count"] == 13


def test_delete_cascades_sessions(client, db_session, semester_id):
    subject_id = client.post("/api/subjects", json=subject_body(semester_id)).get_json()["subject"][
        "id"
    ]
    assert client.delete(f"/api/subjects/{subject_id}").status_code == 204
    count = db_session.scalar(
        select(func.count()).select_from(ClassSession).where(ClassSession.subject_id == subject_id)
    )
    assert count == 0
