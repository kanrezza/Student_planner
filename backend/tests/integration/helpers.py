"""Hàm tạo dữ liệu qua API dùng chung cho các test tích hợp."""

from tests.factories import study_list


def create_semester(client, start="2026-09-07", end="2026-12-20", name="HK1 2026–2027") -> int:
    resp = client.post("/api/semesters", json={"name": name, "start_date": start, "end_date": end})
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["id"]


def create_subject(client, semester_id, **fields) -> dict:
    body = {
        "name": "Giải tích 1",
        "semester_id": semester_id,
        "weekdays": [1],
        "start_time": "06:45",
        "end_time": "09:25",
        "room": "A2-301",
        **fields,
    }
    if "shift" in fields:
        body.pop("start_time", None)
        body.pop("end_time", None)
    resp = client.post("/api/subjects", json=body)
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["subject"]


def sessions_of(client, subject_id) -> list[dict]:
    return client.get(f"/api/subjects/{subject_id}").get_json()["sessions"]


def create_task(client, db_session, title="Bài tập", **fields) -> dict:
    body = {"title": title, "list_id": study_list(db_session).id, **fields}
    resp = client.post("/api/tasks", json=body)
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()
