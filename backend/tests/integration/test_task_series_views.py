"""Hiển thị task lặp: danh sách, lịch, bản tóm tắt, feed Lời nhắc (feature 003 T081)."""

from datetime import timedelta

import pytest

from app.lib import timeutil
from tests.integration.helpers import create_task


@pytest.fixture
def today():
    return timeutil.today()


def series(client, db_session, today, rule=None, **fields):
    return create_task(
        client,
        db_session,
        "Uống thuốc",
        due_date=today.isoformat(),
        due_time="20:00",
        recurrence=rule or {"freq": "daily"},
        **fields,
    )


def calendar(client, start, end):
    return client.get(f"/api/calendar?from={start}&to={end}").get_json()


def test_chi_lan_hien_tai_nam_trong_danh_sach_va_so_dem(client, db_session, today):
    series(client, db_session, today)
    assert len(client.get("/api/tasks?view=all").get_json()) == 1
    assert client.get("/api/task-counts").get_json()["all"] == 1
    assert client.get("/api/search?q=thuoc").get_json()["groups"]["tasks"]["total"] == 1


def test_lich_co_lan_du_kien_khong_trung_lan_hien_tai(client, db_session, today):
    task = series(client, db_session, today)
    end = today + timedelta(days=5)
    data = calendar(client, today, end)
    assert [t["id"] for t in data["tasks"]] == [task["id"]]
    days = [p["date"] for p in data["projected_tasks"]]
    assert days == [(today + timedelta(days=k)).isoformat() for k in range(1, 6)]
    first = data["projected_tasks"][0]
    assert first["kind"] == "projected_task" and first["current_task_id"] == task["id"]
    assert first["time"] == "20:00" and first["title"] == "Uống thuốc"


def test_lich_dung_khi_chuoi_het_so_lan(client, db_session, today):
    series(client, db_session, today, {"freq": "daily", "end": {"kind": "after_count", "count": 3}})
    data = calendar(client, today, today + timedelta(days=20))
    assert len(data["projected_tasks"]) == 2


def test_lich_chuoi_ket_thuc_theo_ngay(client, db_session, today):
    end = today + timedelta(days=2)
    series(
        client,
        db_session,
        today,
        {"freq": "daily", "end": {"kind": "on_date", "date": end.isoformat()}},
    )
    data = calendar(client, today, today + timedelta(days=10))
    assert [p["date"] for p in data["projected_tasks"]][-1] == end.isoformat()


def test_chuoi_da_dung_khong_con_du_kien(client, db_session, today):
    task = series(client, db_session, today)
    client.delete(f"/api/tasks/{task['id']}?scope=following")
    assert calendar(client, today, today + timedelta(days=5))["projected_tasks"] == []


def test_ban_tom_tat_cac_ngay_toi_co_lan_du_kien(client, db_session, today):
    from app.extensions import db
    from app.services.digest import digests_for_range
    from app.services.reminders import get_settings

    series(client, db_session, today)
    settings = get_settings()
    settings.daily_digest_enabled = True
    db.session.flush()
    digests = digests_for_range(today, 4, settings)
    assert [d.date for d in digests] == [today + timedelta(days=k) for k in range(4)]
    assert all("Uống thuốc" in d.title for d in digests)


def test_feed_loi_nhac_chi_co_lan_hien_tai_va_doi_sang_lan_ke_tiep(client, db_session, today):
    task = series(client, db_session, today)
    feed = client.get("/api/sync/feed").get_json()
    keys = [r["sync_key"] for r in feed["reminders"]]
    assert keys == [f"task:{task['id']}"]
    nxt = client.post(f"/api/tasks/{task['id']}/complete").get_json()["next_task"]
    feed2 = client.get("/api/sync/feed").get_json()
    assert [r["sync_key"] for r in feed2["reminders"]] == [f"task:{nxt['id']}"]
    assert feed2["revision"] > feed["revision"]
