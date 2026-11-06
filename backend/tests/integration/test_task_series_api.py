"""Task lặp lại qua API: tạo, hoàn thành, phạm vi sửa/xoá, Thùng rác (feature 003 T080)."""

from datetime import timedelta

import pytest

from app.lib import timeutil
from tests.factories import study_list
from tests.integration.helpers import create_task


@pytest.fixture
def today():
    return timeutil.today()


def make(client, db_session, rule, **fields):
    return create_task(client, db_session, "Nộp báo cáo tuần", recurrence=rule, **fields)


def weekly(*days, **end):
    return {"freq": "weekly", "weekdays": list(days), "end": end or {"kind": "never"}}


def get(client, task_id):
    return client.get(f"/api/tasks/{task_id}").get_json()


def open_tasks(client):
    return client.get("/api/tasks?view=all").get_json()


def test_tao_task_lap_sinh_chuoi_va_lan_dau(client, db_session, today):
    task = make(client, db_session, {"freq": "daily"}, due_date=today.isoformat())
    assert task["series_id"] and task["occurrence_no"] == 1
    assert task["recurrence"] == {"freq": "daily", "end": {"kind": "never"}}
    assert task["series_finished"] is False


def test_khong_co_han_thi_han_la_ngay_khop_gan_nhat(client, db_session, today):
    task = make(client, db_session, weekly(1, 4))
    due = timeutil.today() + timedelta(days=0)
    assert task["due_date"] is not None
    from datetime import date

    d = date.fromisoformat(task["due_date"])
    assert d >= due and d.isoweekday() in (1, 4)
    assert all(
        d - timedelta(days=k) < due or (d - timedelta(days=k)).isoweekday() not in (1, 4)
        for k in range(1, (d - due).days + 1)
    )


def test_hoan_thanh_sinh_lan_ke_tiep_giu_cac_truong(client, db_session, today):
    tag = client.post("/api/tags", json={"name": "Gấp"}).get_json()
    due = (today + timedelta(days=1)).isoformat()
    task = make(
        client,
        db_session,
        {"freq": "daily"},
        due_date=due,
        due_time="17:00",
        notes="Ghi chú",
        priority=1,
        is_important=True,
        reminder_minutes=30,
        tag_ids=[tag["id"]],
        work_date=due,
        work_start="09:00",
        work_end="10:00",
    )
    resp = client.post(f"/api/tasks/{task['id']}/complete")
    body = resp.get_json()
    assert body["completed"] is True
    nxt = body["next_task"]
    assert nxt["id"] != task["id"] and nxt["series_id"] == task["series_id"]
    assert nxt["occurrence_no"] == 2
    assert nxt["due_date"] == (today + timedelta(days=2)).isoformat()
    assert nxt["due_time"] == "17:00" and nxt["title"] == "Nộp báo cáo tuần"
    assert nxt["notes"] == "Ghi chú" and nxt["priority"] == 1 and nxt["is_important"]
    assert nxt["reminder_minutes"] == 30 and [t["id"] for t in nxt["tags"]] == [tag["id"]]
    assert nxt["work_date"] == nxt["due_date"] and nxt["work_start"] == "09:00"
    assert [t["id"] for t in open_tasks(client)] == [nxt["id"]]


def test_hoan_thanh_hai_lan_lien_tiep_khong_trung(client, db_session, today):
    task = make(client, db_session, {"freq": "daily"}, due_date=today.isoformat())
    first = client.post(f"/api/tasks/{task['id']}/complete").get_json()
    second = client.post(f"/api/tasks/{task['id']}/complete").get_json()
    assert first["next_task"] is not None and second["next_task"] is None
    assert len(open_tasks(client)) == 1


def test_qua_han_khong_sinh_cac_lan_da_lo(client, db_session, today):
    old = (today - timedelta(days=3)).isoformat()
    task = make(client, db_session, {"freq": "daily"}, due_date=old, due_time="23:59")
    nxt = client.post(f"/api/tasks/{task['id']}/complete").get_json()["next_task"]
    assert nxt["due_date"] >= today.isoformat()


def test_ket_thuc_sau_n_lan(client, db_session, today):
    rule = {"freq": "daily", "end": {"kind": "after_count", "count": 2}}
    task = make(client, db_session, rule, due_date=today.isoformat())
    second = client.post(f"/api/tasks/{task['id']}/complete").get_json()["next_task"]
    assert second is not None
    last = client.post(f"/api/tasks/{second['id']}/complete").get_json()
    assert last["next_task"] is None and last["series_finished"] is True
    assert open_tasks(client) == []


def test_bo_hoan_thanh_go_lan_ke_tiep_chua_sua(client, db_session, today):
    task = make(client, db_session, {"freq": "daily"}, due_date=today.isoformat())
    nxt = client.post(f"/api/tasks/{task['id']}/complete").get_json()["next_task"]
    back = client.post(f"/api/tasks/{task['id']}/uncomplete").get_json()
    assert back["removed_next_task_id"] == nxt["id"] and back["completed"] is False
    assert [t["id"] for t in open_tasks(client)] == [task["id"]]
    assert client.get(f"/api/tasks/{nxt['id']}").status_code == 404
    # Hoàn thành lại vẫn sinh đúng một lần kế tiếp, số lần không lệch.
    again = client.post(f"/api/tasks/{task['id']}/complete").get_json()["next_task"]
    assert again["occurrence_no"] == 2


def test_bo_hoan_thanh_giu_ca_hai_neu_lan_ke_tiep_da_sua(client, db_session, today):
    task = make(client, db_session, {"freq": "daily"}, due_date=today.isoformat())
    nxt = client.post(f"/api/tasks/{task['id']}/complete").get_json()["next_task"]
    assert (
        client.patch(
            f"/api/tasks/{nxt['id']}", json={"title": "Đã sửa", "scope": "this"}
        ).status_code
        == 200
    )
    back = client.post(f"/api/tasks/{task['id']}/uncomplete").get_json()
    assert back["removed_next_task_id"] is None
    titles = sorted(t["title"] for t in open_tasks(client))
    assert titles == ["Nộp báo cáo tuần", "Đã sửa"]
    assert back["series_id"] is None  # tách khỏi chuỗi: mỗi chuỗi chỉ một lần hiện tại


def test_sua_thieu_scope_la_409(client, db_session, today):
    task = make(client, db_session, {"freq": "daily"}, due_date=today.isoformat())
    resp = client.patch(f"/api/tasks/{task['id']}", json={"title": "Mới"})
    assert resp.status_code == 409 and resp.get_json()["error"]["code"] == "scope_required"
    assert get(client, task["id"])["title"] == "Nộp báo cáo tuần"


def test_scope_this_chi_doi_lan_nay(client, db_session, today):
    task = make(client, db_session, {"freq": "daily"}, due_date=today.isoformat())
    client.patch(f"/api/tasks/{task['id']}", json={"title": "Chỉ lần này", "scope": "this"})
    nxt = client.post(f"/api/tasks/{task['id']}/complete").get_json()["next_task"]
    assert nxt["title"] == "Nộp báo cáo tuần"


def test_scope_following_doi_mau(client, db_session, today):
    task = make(client, db_session, {"freq": "daily"}, due_date=today.isoformat())
    client.patch(
        f"/api/tasks/{task['id']}",
        json={"title": "Từ nay", "due_time": "08:00", "scope": "following"},
    )
    nxt = client.post(f"/api/tasks/{task['id']}/complete").get_json()["next_task"]
    assert nxt["title"] == "Từ nay" and nxt["due_time"] == "08:00"


def test_doi_ngay_following_dich_quy_tac(client, db_session):
    # Thứ Hai 09/11/2026 → Thứ Ba 10/11/2026: T2+T5 thành T3+T5.
    task = make(client, db_session, weekly(1, 4), due_date="2026-11-09")
    resp = client.patch(
        f"/api/tasks/{task['id']}", json={"due_date": "2026-11-10", "scope": "following"}
    )
    assert resp.get_json()["recurrence"]["weekdays"] == [2, 4]


def test_chi_sua_recurrence_khong_can_scope_va_giu_han(client, db_session, today):
    task = make(client, db_session, {"freq": "daily"}, due_date=today.isoformat())
    resp = client.patch(
        f"/api/tasks/{task['id']}",
        json={"recurrence": {"freq": "every_n_days", "interval_days": 3}},
    )
    body = resp.get_json()
    assert resp.status_code == 200 and body["due_date"] == today.isoformat()
    assert body["recurrence"]["interval_days"] == 3
    nxt = client.post(f"/api/tasks/{task['id']}/complete").get_json()["next_task"]
    assert nxt["due_date"] == (today + timedelta(days=3)).isoformat()


def test_bo_lap_thanh_task_thuong(client, db_session, today):
    task = make(client, db_session, {"freq": "daily"}, due_date=today.isoformat())
    resp = client.patch(f"/api/tasks/{task['id']}", json={"recurrence": None})
    body = resp.get_json()
    assert body["series_id"] is None and body["recurrence"] is None
    assert client.post(f"/api/tasks/{task['id']}/complete").get_json()["next_task"] is None


def test_dat_lap_cho_task_co_san(client, db_session, today):
    task = create_task(client, db_session, "Việc thường", due_date=today.isoformat())
    resp = client.patch(f"/api/tasks/{task['id']}", json={"recurrence": {"freq": "daily"}})
    assert resp.get_json()["series_id"] is not None


def test_xoa_thieu_scope_la_409(client, db_session, today):
    task = make(client, db_session, {"freq": "daily"}, due_date=today.isoformat())
    resp = client.delete(f"/api/tasks/{task['id']}")
    assert resp.status_code == 409 and resp.get_json()["error"]["code"] == "scope_required"


def test_xoa_chi_lan_nay_lan_ke_tiep_xuat_hien(client, db_session, today):
    task = make(client, db_session, {"freq": "daily"}, due_date=today.isoformat())
    body = client.delete(f"/api/tasks/{task['id']}?scope=this").get_json()
    assert body["deleted_at"] and body["next_task"] is not None
    assert [t["id"] for t in open_tasks(client)] == [body["next_task"]["id"]]


def test_xoa_cac_lan_sau_dung_chuoi(client, db_session, today):
    task = make(client, db_session, {"freq": "daily"}, due_date=today.isoformat())
    body = client.delete(f"/api/tasks/{task['id']}?scope=following").get_json()
    assert body["next_task"] is None and open_tasks(client) == []


def test_khoi_phuc_this_thanh_task_thuong(client, db_session, today):
    task = make(client, db_session, {"freq": "daily"}, due_date=today.isoformat())
    client.delete(f"/api/tasks/{task['id']}?scope=this")
    restored = client.post(f"/api/tasks/{task['id']}/restore").get_json()["task"]
    assert restored["series_id"] is None and restored["recurrence"] is None


def test_khoi_phuc_following_chuoi_tiep_tuc(client, db_session, today):
    task = make(client, db_session, {"freq": "daily"}, due_date=today.isoformat())
    client.delete(f"/api/tasks/{task['id']}?scope=following")
    restored = client.post(f"/api/tasks/{task['id']}/restore").get_json()["task"]
    assert restored["series_id"] == task["series_id"] and restored["recurrence"]
    nxt = client.post(f"/api/tasks/{task['id']}/complete").get_json()["next_task"]
    assert nxt is not None


def test_task_tu_tao_khong_dat_lap_duoc(client, db_session, today):
    from app.models import Task

    task = Task(title="Tự tạo", list_id=study_list(db_session).id, due_date=today, is_auto=True)
    db_session.add(task)
    db_session.commit()
    resp = client.patch(f"/api/tasks/{task.id}", json={"recurrence": {"freq": "daily"}})
    assert resp.status_code == 400


def test_hang_tuan_khong_chon_thu_la_400(client, db_session):
    body = {"title": "x", "list_id": study_list(db_session).id, "recurrence": weekly()}
    resp = client.post("/api/tasks", json=body)
    assert resp.status_code == 400
    assert "Chọn ít nhất một thứ" in str(resp.get_json()["error"]["fields"])


def test_xoa_ca_danh_sach_dung_chuoi(client, db_session, today):
    lst = client.post("/api/lists", json={"name": "Tạm"}).get_json()
    task = create_task(
        client,
        db_session,
        "Lặp",
        list_id=lst["id"],
        due_date=today.isoformat(),
        recurrence={"freq": "daily"},
    )
    assert client.delete(f"/api/lists/{lst['id']}?delete_tasks=true").status_code == 204
    assert task["id"] not in [t["id"] for t in open_tasks(client)]
