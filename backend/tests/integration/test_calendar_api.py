from tests.integration.helpers import create_semester, create_subject, create_task, sessions_of


def test_calendar_range_sessions_and_tasks(client, db_session):
    semester_id = create_semester(client)
    subject = create_subject(client, semester_id, weekdays=[1, 4])
    sessions = sessions_of(client, subject["id"])
    client.post(f"/api/sessions/{sessions[0]['id']}/cancel")  # 07/09 bị huỷ vẫn hiện

    create_task(client, db_session, "Trong khoảng", due_date="2026-09-10", due_time="17:00")
    create_task(client, db_session, "Biên cuối", due_date="2026-09-13")
    create_task(client, db_session, "Ngoài khoảng", due_date="2026-09-14")
    create_task(client, db_session, "Không hạn")

    data = client.get("/api/calendar?from=2026-09-07&to=2026-09-13").get_json()
    assert [s["date"] for s in data["sessions"]] == ["2026-09-07", "2026-09-10"]
    assert data["sessions"][0]["is_cancelled"] is True
    assert data["sessions"][0]["display_color"] == subject["color"]
    assert sorted(t["title"] for t in data["tasks"]) == ["Biên cuối", "Trong khoảng"]
    assert all(t["display_color"] == "c01" for t in data["tasks"])  # màu danh sách Học tập


def test_calendar_requires_valid_range(client):
    assert client.get("/api/calendar?from=2026-09-07").status_code == 400
    assert client.get("/api/calendar?from=2026-09-10&to=2026-09-01").status_code == 400
    assert client.get("/api/calendar?from=2026-01-01&to=2026-12-31").status_code == 400  # quá dài
