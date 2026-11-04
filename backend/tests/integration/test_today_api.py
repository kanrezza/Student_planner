from datetime import datetime

import pytest
from sqlalchemy import select

from app.lib import timeutil
from app.lib.timeutil import TZ
from app.models import ClassSession
from tests.factories import study_list

NOW = datetime(2026, 11, 10, 10, 0, tzinfo=TZ)  # Thứ Ba 10/11/2026, 10:00


@pytest.fixture(autouse=True)
def fixed_now(monkeypatch):
    monkeypatch.setattr(timeutil, "now", lambda: NOW)


@pytest.fixture
def semester_id(client):
    resp = client.post(
        "/api/semesters",
        json={"name": "HK1", "start_date": "2026-09-07", "end_date": "2026-12-20"},
    )
    return resp.get_json()["id"]


def add_subject(client, semester_id, name, weekdays, start, end, room="A101"):
    body = {
        "name": name,
        "semester_id": semester_id,
        "weekdays": weekdays,
        "start_time": start,
        "end_time": end,
        "room": room,
    }
    return client.post("/api/subjects", json=body).get_json()["subject"]["id"]


def test_today_lists_sessions_tasks_and_overdue(client, db_session, semester_id):
    list_id = study_list(db_session).id
    # Thứ Ba: hai môn, tạo theo thứ tự ngược để kiểm tra sắp xếp theo giờ
    add_subject(client, semester_id, "Chiều", [2], "13:00", "15:40", room="B2")
    morning = add_subject(client, semester_id, "Sáng", [2], "06:45", "09:25")
    add_subject(client, semester_id, "Thứ Tư", [3], "06:45", "09:25")  # không phải hôm nay

    # Huỷ buổi sáng hôm nay
    session = db_session.scalars(
        select(ClassSession).where(
            ClassSession.subject_id == morning, ClassSession.date == NOW.date()
        )
    ).one()
    session.is_cancelled = True
    db_session.commit()

    def task(title, **fields):
        return client.post(
            "/api/tasks", json={"title": title, "list_id": list_id, **fields}
        ).get_json()["id"]

    task("Hôm nay có giờ", due_date="2026-11-10", due_time="17:00")
    task("Hôm nay đã qua giờ", due_date="2026-11-10", due_time="08:00")
    task("Hôm nay chỉ ngày", due_date="2026-11-10")
    done_today = task("Hôm nay đã xong", due_date="2026-11-10")
    client.post(f"/api/tasks/{done_today}/complete")
    task("Hôm qua chưa xong", due_date="2026-11-09")
    done_late = task("Hôm qua đã xong", due_date="2026-11-09")
    client.post(f"/api/tasks/{done_late}/complete")
    task("Ngày mai", due_date="2026-11-11")
    task("Không hạn")

    data = client.get("/api/today").get_json()
    assert data["date"] == "2026-11-10"
    assert [(s["subject_name"], s["is_cancelled"]) for s in data["sessions"]] == [
        ("Sáng", True),
        ("Chiều", False),
    ]
    assert data["sessions"][1]["room"] == "B2"
    assert data["sessions"][1]["start_at"] == "2026-11-10T13:00:00+07:00"

    today_titles = [t["title"] for t in data["tasks_due_today"]]
    assert today_titles == [
        "Hôm nay đã qua giờ",
        "Hôm nay có giờ",
        "Hôm nay chỉ ngày",
        "Hôm nay đã xong",
    ]
    assert data["tasks_due_today"][0]["is_overdue"] is True
    assert [t["title"] for t in data["overdue_tasks"]] == ["Hôm qua chưa xong"]
    assert data["notices"] == []


def test_empty_day(client):
    data = client.get("/api/today").get_json()
    assert data == {
        "date": "2026-11-10",
        "exams": [],
        "sessions": [],
        "tasks_due_today": [],
        "overdue_tasks": [],
        "notices": [],
    }
