"""API môn học nhiều quy tắc lặp (feature 004, FR-020, FR-020a)."""

from tests.integration.helpers import create_semester, create_subject, sessions_of


def body(**overrides):
    base = {
        "name": "Xử lý ngôn ngữ tự nhiên",
        "class_code": "2-2-26(N01)",
        "course_code": "CSE703065",
        "credits": 3,
        "schedules": [
            {
                "weekdays": [5],
                "start_date": "2026-11-30",
                "end_date": "2026-12-20",
                "start_time": "09:30",
                "end_time": "12:10",
                "room": "A6-501 (PC)",
            },
            {
                "weekdays": [2],
                "start_date": "2026-12-21",
                "end_date": "2027-01-24",
                "start_time": "09:30",
                "end_time": "12:10",
                "room": "A6-203 (PC)",
            },
        ],
    }
    base.update(overrides)
    return base


def semester(client):
    return create_semester(client, "2026-11-30", "2027-02-28", "HK2")


def post(client, semester_id, **overrides):
    return client.post("/api/subjects", json={"semester_id": semester_id, **body(**overrides)})


def test_two_schedules_generate_sessions_with_their_own_rooms(client):
    sem = semester(client)
    resp = post(client, sem)
    assert resp.status_code == 201, resp.get_json()
    subject = resp.get_json()["subject"]
    assert subject["course_code"] == "CSE703065" and subject["credits"] == 3
    assert [r["weekdays"] for r in subject["schedules"]] == [[5], [2]]
    sessions = sessions_of(client, subject["id"])
    by_date = {s["date"]: s["room"] for s in sessions}
    assert by_date["2026-12-04"] == "A6-501 (PC)"  # thứ Sáu đầu tiên
    assert by_date["2026-12-22"] == "A6-203 (PC)"  # thứ Ba đầu tiên của lịch thứ hai
    assert len(sessions) == 3 + 5  # 04, 11, 18/12 và 22, 29/12, 05, 12, 19/01


def test_summary_fields_still_describe_the_first_schedule(client):
    subject = post(client, semester(client)).get_json()["subject"]
    assert subject["weekdays"] == [5] and subject["room"] == "A6-501 (PC)"
    assert (subject["start_date"], subject["end_date"]) == ("2026-11-30", "2027-01-24")


def test_patch_replaces_schedule_list_by_id(client):
    sem = semester(client)
    subject = post(client, sem).get_json()["subject"]
    first, second = subject["schedules"]
    patch = {
        "schedules": [
            {
                **{k: second[k] for k in ("id", "weekdays", "start_date", "end_date", "room")},
                "start_time": "09:30",
                "end_time": "12:10",
                "room": "A6-999",
            },
            {
                "weekdays": [1],
                "start_date": "2027-02-01",
                "end_date": "2027-02-28",
                "start_time": "07:00",
                "end_time": "09:00",
            },
        ]
    }
    resp = client.patch(f"/api/subjects/{subject['id']}", json=patch)
    assert resp.status_code == 200, resp.get_json()
    updated = resp.get_json()["subject"]["schedules"]
    assert [r["id"] for r in updated][0] == second["id"]  # giữ id → cập nhật
    assert first["id"] not in [r["id"] for r in updated]  # vắng mặt → xoá
    assert updated[0]["room"] == "A6-999" and updated[1]["weekdays"] == [1]  # mới → tạo
    dates = [s["date"] for s in sessions_of(client, subject["id"])]
    assert "2026-12-04" not in dates  # lịch thứ Sáu đã bị xoá nên buổi đó cũng mất
    assert "2027-02-01" in dates


def test_cannot_have_zero_schedules(client):
    sem = semester(client)
    resp = post(client, sem, schedules=[])
    assert resp.status_code == 400
    assert "schedules" in resp.get_json()["error"]["fields"]
    subject = post(client, sem).get_json()["subject"]
    resp = client.patch(f"/api/subjects/{subject['id']}", json={"schedules": []})
    assert resp.status_code == 400


def test_errors_name_the_schedule_that_is_wrong(client):
    sem = semester(client)
    bad = body()
    bad["schedules"][1]["end_time"] = "08:00"  # trước giờ bắt đầu
    bad["schedules"][0]["end_date"] = "2027-03-31"  # ngoài học kỳ
    fields = post(client, sem, schedules=bad["schedules"]).get_json()["error"]["fields"]
    assert "schedules[1].end_time" in fields
    assert "schedules[0].end_date" in fields


def test_bulk_rows_report_nested_schedule_errors(client):
    sem = semester(client)
    row = body()
    row["schedules"][0]["start_time"] = None
    row["schedules"][0]["end_time"] = None
    resp = client.post(
        "/api/subjects/bulk", json={"semester_id": sem, "rows": [body(name="OK"), row]}
    )
    assert resp.status_code == 400
    assert "rows[1].schedules[0].start_time" in resp.get_json()["error"]["fields"]


def test_overlapping_schedules_warn_and_keep_the_first(client):
    sem = semester(client)
    rules = body()["schedules"]
    rules[1] = {**rules[0], "start_date": "2026-12-11", "end_date": "2026-12-18", "room": "KHÁC"}
    resp = post(client, sem, schedules=rules)
    assert resp.status_code == 201
    assert any(w["code"] == "schedule_overlap" for w in resp.get_json()["warnings"])
    rooms = {s["date"]: s["room"] for s in sessions_of(client, resp.get_json()["subject"]["id"])}
    assert rooms["2026-12-11"] == "A6-501 (PC)"


def test_legacy_flat_fields_still_make_one_schedule(client):
    sem = semester(client)
    subject = create_subject(client, sem, weekdays=[1], start_time="07:00", end_time="09:00")
    assert len(subject["schedules"]) == 1 and subject["schedules"][0]["weekdays"] == [1]
    patched = client.patch(f"/api/subjects/{subject['id']}", json={"room": "Z1"}).get_json()
    assert patched["subject"]["schedules"][0]["room"] == "Z1"


def test_flat_patch_on_multi_schedule_subject_is_rejected(client):
    subject = post(client, semester(client)).get_json()["subject"]
    resp = client.patch(f"/api/subjects/{subject['id']}", json={"room": "Z1"})
    assert resp.status_code == 400 and "schedules" in resp.get_json()["error"]["fields"]


def test_session_shift_label_follows_the_session_schedule(client):
    sem = semester(client)
    ca = {s["name"]: s["id"] for s in client.get("/api/shifts").get_json()}
    rules = body()["schedules"]
    rules[0] = {**rules[0], "shift": {"start_shift_id": ca["Ca 2"], "end_shift_id": ca["Ca 2"]}}
    rules[0].pop("start_time")
    rules[0].pop("end_time")
    subject = post(client, sem, schedules=rules).get_json()["subject"]
    labels = {s["date"]: s["shift_label"] for s in sessions_of(client, subject["id"])}
    assert labels["2026-12-04"] == "Ca 2"  # buổi của lịch gắn ca
    assert labels["2026-12-22"] is None  # buổi của lịch giờ tuỳ chỉnh
