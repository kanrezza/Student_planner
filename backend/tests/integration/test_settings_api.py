import unicodedata

from app.services.revision import current_revision


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_get_settings_defaults(client):
    data = client.get("/api/settings").get_json()
    assert data == {
        "session_reminder_minutes": 15,
        "task_reminder_minutes": 60,
        "date_only_task_reminder_time": "08:00",
        "calendar_sync_enabled": False,
        "calendar_sync_prompted": False,
        "auto_deadline_evening_from": "20:00",
        "auto_deadline_due_time": "08:00",
        "auto_deadline_excluded_keywords": ["Giáo dục thể chất"],
        "important_reminder_offsets": [1440, 180, 60, 15],
        "exam_extra_reminder_offsets": [10080],
        "exam_reminder_minutes": 60,
        "daily_digest_enabled": True,
        "daily_digest_time": "05:00",
        "daily_digest_overdue_only": True,
    }


def test_patch_settings_updates_only_sent_fields_and_bumps_revision(client, db_session):
    before = current_revision(db_session)
    resp = client.patch(
        "/api/settings",
        json={"session_reminder_minutes": 30, "auto_deadline_evening_from": "19:30"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["session_reminder_minutes"] == 30
    assert data["auto_deadline_evening_from"] == "19:30"
    assert data["task_reminder_minutes"] == 60
    assert current_revision(db_session) == before + 1
    assert client.get("/api/settings").get_json()["session_reminder_minutes"] == 30


def test_patch_settings_normalizes_keywords_to_nfc_and_dedupes(client):
    nfd = unicodedata.normalize("NFD", "Giáo dục thể chất")
    resp = client.patch(
        "/api/settings", json={"auto_deadline_excluded_keywords": [nfd, "GDTC", "GDTC"]}
    )
    assert resp.status_code == 200
    assert resp.get_json()["auto_deadline_excluded_keywords"] == ["Giáo dục thể chất", "GDTC"]


def test_patch_settings_rejects_invalid_values_in_vietnamese(client):
    resp = client.patch(
        "/api/settings",
        json={
            "session_reminder_minutes": -1,
            "date_only_task_reminder_time": "25:00",
            "auto_deadline_excluded_keywords": ["  "],
        },
    )
    assert resp.status_code == 400
    error = resp.get_json()["error"]
    assert error["code"] == "validation_error"
    assert error["fields"]["session_reminder_minutes"] == "Phải lớn hơn hoặc bằng 0"
    assert error["fields"]["date_only_task_reminder_time"].startswith("Giờ phải có dạng HH:MM")
    assert "không được để trống" in error["fields"]["auto_deadline_excluded_keywords"]


def test_patch_settings_rejects_unknown_field(client):
    resp = client.patch("/api/settings", json={"theme": "dark"})
    assert resp.status_code == 400
    assert resp.get_json()["error"]["fields"]["theme"] == "Trường không được hỗ trợ"
