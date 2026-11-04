"""Danh sách thông minh và số đếm (feature 002 FR-008, FR-009; task T019)."""

from datetime import datetime

import pytest

from app.lib import timeutil
from app.lib.timeutil import TZ
from app.models import Task
from tests.integration.helpers import create_task

NOW = datetime(2026, 11, 9, 9, 0, tzinfo=TZ)  # Thứ Hai 09/11/2026 09:00


@pytest.fixture(autouse=True)
def fixed_now(monkeypatch):
    monkeypatch.setattr(timeutil, "now", lambda: NOW)


@pytest.fixture
def tasks(client, db_session):
    tag = client.post("/api/tags", json={"name": "Gấp"}).get_json()
    personal = client.post("/api/lists", json={"name": "Việc riêng"}).get_json()

    def make(title, **fields):
        return create_task(client, db_session, title, **fields)["id"]

    made = {
        "today": make("Hạn hôm nay", due_date="2026-11-09"),
        "today_past_time": make("Hạn 08:00 hôm nay", due_date="2026-11-09", due_time="08:00"),
        "overdue": make("Quá hạn", due_date="2026-11-08"),
        "tomorrow": make("Ngày mai", due_date="2026-11-10", tag_ids=[tag["id"]]),
        "d5": make("5 ngày nữa", due_date="2026-11-14"),
        "d10": make("10 ngày nữa", due_date="2026-11-19"),
        "no_due": make("Không hạn"),
        "work_tomorrow": make(
            "Làm ngày mai, hạn xa",
            due_date="2026-11-19",
            work_date="2026-11-10",
            work_start="19:00",
            work_end="21:00",
        ),
        "personal": make("Việc nhà", list_id=personal["id"]),
        "done": make("Đã xong", due_date="2026-11-09"),
        "trashed": make("Trong Thùng rác", due_date="2026-11-09", tag_ids=[tag["id"]]),
    }
    client.post(f"/api/tasks/{made['done']}/complete")
    db_session.get(Task, made["trashed"]).deleted_at = NOW
    db_session.flush()
    return made, tag["id"], personal["id"]


def view_ids(client, query: str) -> set[int]:
    resp = client.get(f"/api/tasks?{query}")
    assert resp.status_code == 200, resp.get_json()
    return {t["id"] for t in resp.get_json()}


def pick(made, *names) -> set[int]:
    return {made[n] for n in names}


def test_smart_views(client, tasks):
    made, tag_id, personal_id = tasks
    assert view_ids(client, "view=today") == pick(made, "today", "today_past_time", "overdue")
    assert view_ids(client, "view=tomorrow") == pick(made, "tomorrow", "work_tomorrow")
    assert view_ids(client, "view=next7") == pick(
        made, "today", "today_past_time", "overdue", "tomorrow", "d5", "work_tomorrow"
    )
    all_open = pick(
        made,
        "today",
        "today_past_time",
        "overdue",
        "tomorrow",
        "d5",
        "d10",
        "no_due",
        "work_tomorrow",
        "personal",
    )
    assert view_ids(client, "view=all") == all_open
    assert view_ids(client, "view=completed") == pick(made, "done")
    assert view_ids(client, f"list_id={personal_id}") == pick(made, "personal")
    assert view_ids(client, f"tag_id={tag_id}") == pick(made, "tomorrow")


def test_unknown_view_is_rejected(client):
    resp = client.get("/api/tasks?view=yesterday")
    assert resp.status_code == 400
    assert "view" in resp.get_json()["error"]["fields"]


def test_task_counts(client, tasks):
    made, _, personal_id = tasks
    counts = client.get("/api/task-counts").get_json()
    assert {k: counts[k] for k in ("today", "tomorrow", "next7", "all")} == {
        "today": 3,
        "tomorrow": 2,
        "next7": 6,
        "all": 9,
    }
    # Học tập có 8 task chưa xong, đang dùng; Việc riêng có 1 (task trong Thùng rác không được đếm).
    assert counts["lists"][str(personal_id)] == 1
    assert sum(counts["lists"].values()) == 9


def test_task_fields_include_work_window_and_trash(client, tasks):
    made, _, _ = tasks
    task = client.get(f"/api/tasks/{made['work_tomorrow']}").get_json()
    assert (task["work_date"], task["work_start"], task["work_end"]) == (
        "2026-11-10",
        "19:00",
        "21:00",
    )
    assert task["deleted_at"] is None and task["days_left_in_trash"] is None
    assert task["trashed_from_list_name"] is None
