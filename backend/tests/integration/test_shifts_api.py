from tests.integration.helpers import create_semester, create_subject, sessions_of


def shifts(client):
    return client.get("/api/shifts").get_json()


def test_default_shifts(client):
    assert [(s["name"], s["start_time"], s["end_time"]) for s in shifts(client)] == [
        ("Ca 1", "06:45", "09:25"),
        ("Ca 2", "09:35", "12:10"),
        ("Ca 3", "13:00", "15:40"),
        ("Ca 4", "15:45", "18:25"),
    ]


def test_create_validates_times_and_name(client):
    resp = client.post(
        "/api/shifts", json={"name": "Ca 5", "start_time": "18:35", "end_time": "18:35"}
    )
    assert resp.status_code == 400 and "end_time" in resp.get_json()["error"]["fields"]
    resp = client.post(
        "/api/shifts", json={"name": "ca 1", "start_time": "18:35", "end_time": "21:15"}
    )
    assert resp.status_code == 400 and "name" in resp.get_json()["error"]["fields"]
    resp = client.post(
        "/api/shifts", json={"name": "Ca 5", "start_time": "18:35", "end_time": "21:15"}
    )
    assert resp.status_code == 201 and resp.get_json()["position"] == 5


def test_subject_by_shift_range(client):
    subject = create_subject(
        client, create_semester(client), shift={"start_shift_id": 1, "end_shift_id": 2}
    )
    assert (subject["start_time"], subject["end_time"], subject["shift_label"]) == (
        "06:45",
        "12:10",
        "Ca 1–2",
    )


def test_changing_used_shift_needs_confirm_and_propagates(client):
    ca2 = shifts(client)[1]
    subject = create_subject(
        client,
        create_semester(client),
        shift={"start_shift_id": ca2["id"], "end_shift_id": ca2["id"]},
    )
    sessions = sessions_of(client, subject["id"])
    client.patch(
        f"/api/sessions/{sessions[3]['id']}", json={"start_time": "10:00", "end_time": "11:00"}
    )

    resp = client.patch(
        f"/api/shifts/{ca2['id']}", json={"start_time": "09:30", "end_time": "12:05"}
    )
    assert resp.status_code == 409
    assert resp.get_json()["error"]["details"] == {"subject_count": 1}

    resp = client.patch(
        f"/api/shifts/{ca2['id']}?confirm=true", json={"start_time": "09:30", "end_time": "12:05"}
    )
    assert resp.status_code == 200
    detail = client.get(f"/api/subjects/{subject['id']}").get_json()
    assert (detail["start_time"], detail["end_time"]) == ("09:30", "12:05")
    after = detail["sessions"]
    assert after[0]["start_at"].endswith("09:30:00+07:00")
    assert after[3]["start_at"].endswith("10:00:00+07:00")  # buổi đã sửa giờ riêng giữ nguyên

    # Đổi tên không cần xác nhận
    assert client.patch(f"/api/shifts/{ca2['id']}", json={"name": "Ca sáng 2"}).status_code == 200


def test_deleting_used_shift_switches_subject_to_custom_time(client):
    ca3 = shifts(client)[2]
    subject = create_subject(
        client,
        create_semester(client),
        shift={"start_shift_id": ca3["id"], "end_shift_id": ca3["id"]},
    )

    resp = client.delete(f"/api/shifts/{ca3['id']}")
    assert resp.status_code == 409 and resp.get_json()["error"]["details"] == {"subject_count": 1}
    assert client.delete(f"/api/shifts/{ca3['id']}?confirm=true").status_code == 204

    detail = client.get(f"/api/subjects/{subject['id']}").get_json()
    assert detail["shift"] is None and detail["shift_label"] is None
    assert (detail["start_time"], detail["end_time"]) == ("13:00", "15:40")
    assert [s["name"] for s in shifts(client)] == ["Ca 1", "Ca 2", "Ca 4"]
