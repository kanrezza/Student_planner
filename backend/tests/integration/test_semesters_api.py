from datetime import date, datetime

from app.lib import timeutil
from app.lib.timeutil import TZ


def create(client, name="HK1 2026–2027", start="2026-09-07", end="2026-12-20"):
    return client.post("/api/semesters", json={"name": name, "start_date": start, "end_date": end})


def add_subject(client, semester_id, **fields):
    body = {
        "name": "Giải tích 1",
        "semester_id": semester_id,
        "weekdays": [1],
        "start_time": "06:45",
        "end_time": "09:25",
        **fields,
    }
    return client.post("/api/subjects", json=body)


def test_create_and_overlap(client):
    resp = create(client)
    assert resp.status_code == 201
    assert resp.get_json()["name"] == "HK1 2026–2027"

    resp = create(client, "HK2", "2026-12-20", "2027-05-01")
    assert resp.status_code == 400
    assert "HK1 2026–2027" in resp.get_json()["error"]["fields"]["start_date"]

    resp = create(client, "Sai", "2027-05-01", "2027-01-01")
    assert resp.status_code == 400
    assert "end_date" in resp.get_json()["error"]["fields"]


def test_is_current(client, monkeypatch):
    create(client, "HK1", "2026-09-07", "2026-12-20")
    create(client, "HK2", "2027-01-11", "2027-05-30")

    monkeypatch.setattr(timeutil, "now", lambda: datetime(2026, 11, 4, 9, 0, tzinfo=TZ))
    current = [s["name"] for s in client.get("/api/semesters").get_json() if s["is_current"]]
    assert current == ["HK1"]

    # Đang nghỉ giữa hai học kỳ → học kỳ sắp tới gần nhất
    monkeypatch.setattr(timeutil, "now", lambda: datetime(2026, 12, 28, 9, 0, tzinfo=TZ))
    current = [s["name"] for s in client.get("/api/semesters").get_json() if s["is_current"]]
    assert current == ["HK2"]


def test_shrinking_semester_requires_clamp(client):
    semester_id = create(client).get_json()["id"]
    subject_id = add_subject(client, semester_id).get_json()["subject"]["id"]

    resp = client.patch(f"/api/semesters/{semester_id}", json={"end_date": "2026-11-30"})
    assert resp.status_code == 409
    affected = resp.get_json()["error"]["details"]["subjects"]
    assert [s["id"] for s in affected] == [subject_id]

    resp = client.patch(
        f"/api/semesters/{semester_id}?clamp_subjects=true", json={"end_date": "2026-11-30"}
    )
    assert resp.status_code == 200
    subject = client.get(f"/api/subjects/{subject_id}").get_json()
    assert subject["end_date"] == "2026-11-30"
    assert subject["sessions"][-1]["date"] == "2026-11-30"  # Thứ Hai cuối cùng còn lại
    assert len(subject["sessions"]) == 13


def test_delete_requires_confirm_and_cascades(client):
    semester_id = create(client).get_json()["id"]
    subject_id = add_subject(client, semester_id).get_json()["subject"]["id"]

    resp = client.delete(f"/api/semesters/{semester_id}")
    assert resp.status_code == 409
    assert resp.get_json()["error"]["details"] == {"subject_count": 1}

    assert client.delete(f"/api/semesters/{semester_id}?confirm=true").status_code == 204
    assert client.get(f"/api/subjects/{subject_id}").status_code == 404


def test_semester_dates_round_trip(client):
    data = create(client).get_json()
    assert (data["start_date"], data["end_date"]) == ("2026-09-07", "2026-12-20")
    assert date.fromisoformat(data["start_date"]).isoweekday() == 1
