from datetime import datetime

import pytest

from app.lib import timeutil
from app.lib.timeutil import TZ
from app.services.revision import current_revision
from tests.factories import study_list


@pytest.fixture
def list_id(db_session):
    return study_list(db_session).id


def create(client, **fields):
    return client.post("/api/tasks", json=fields)


def test_create_task_with_all_fields(client, db_session, list_id):
    before = current_revision(db_session)
    resp = create(
        client,
        title="  Nộp bài tập Toán  ",
        notes="Chương 3, bài 1–5",
        due_date="2026-11-10",
        due_time="17:00",
        priority=1,
        list_id=list_id,
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["title"] == "Nộp bài tập Toán"
    assert data["notes"] == "Chương 3, bài 1–5"
    assert data["due_date"] == "2026-11-10"
    assert data["due_time"] == "17:00"
    assert data["due_at"] == "2026-11-10T17:00:00+07:00"
    assert data["priority"] == 1
    assert data["list_id"] == list_id
    assert data["list_name"] == "Học tập"
    assert data["completed"] is False
    assert data["is_auto"] is False
    assert data["display_color"] == "c01"  # màu danh sách Học tập
    assert current_revision(db_session) == before + 1
    assert client.get(f"/api/tasks/{data['id']}").get_json()["title"] == "Nộp bài tập Toán"


def test_defaults_priority_medium(client, list_id):
    data = create(client, title="Đọc sách", list_id=list_id).get_json()
    assert data["priority"] == 2
    assert data["due_at"] is None


@pytest.mark.parametrize("title", ["", "   "])
def test_blank_title_rejected(client, list_id, title):
    resp = create(client, title=title, list_id=list_id)
    assert resp.status_code == 400
    assert resp.get_json()["error"]["fields"]["title"] == "Trường này không được để trống"


def test_too_long_title_rejected(client, list_id):
    resp = create(client, title="x" * 301, list_id=list_id)
    assert resp.status_code == 400
    assert "300" in resp.get_json()["error"]["fields"]["title"]


def test_due_time_without_date_rejected(client, list_id):
    resp = create(client, title="A", list_id=list_id, due_time="17:00")
    assert resp.status_code == 400
    assert "ngày hạn chót" in resp.get_json()["error"]["fields"]["due_time"]


def test_invalid_priority_and_unknown_list_rejected(client, list_id):
    resp = create(client, title="A", list_id=list_id, priority=4)
    assert resp.status_code == 400
    assert "priority" in resp.get_json()["error"]["fields"]
    resp = create(client, title="A", list_id=999999)
    assert resp.status_code == 400
    assert resp.get_json()["error"]["fields"]["list_id"] == "Danh sách không tồn tại"


def test_patch_complete_uncomplete_delete(client, list_id):
    task_id = create(client, title="A", list_id=list_id, due_date="2026-11-10").get_json()["id"]

    resp = client.patch(f"/api/tasks/{task_id}", json={"title": "B", "due_time": "08:30"})
    assert resp.status_code == 200
    assert resp.get_json()["title"] == "B"
    assert resp.get_json()["due_time"] == "08:30"

    # Bỏ ngày hạn chót trong khi vẫn còn giờ → lỗi
    resp = client.patch(f"/api/tasks/{task_id}", json={"due_date": None})
    assert resp.status_code == 400
    # Bỏ cả ngày và giờ → được
    resp = client.patch(f"/api/tasks/{task_id}", json={"due_date": None, "due_time": None})
    assert resp.get_json()["due_at"] is None

    assert client.patch(f"/api/tasks/{task_id}", json={"title": None}).status_code == 400

    done = client.post(f"/api/tasks/{task_id}/complete").get_json()
    assert done["completed"] is True and done["completed_at"] is not None
    undone = client.post(f"/api/tasks/{task_id}/uncomplete").get_json()
    assert undone["completed"] is False and undone["completed_at"] is None

    # Feature 002 FR-030: xoá = chuyển vào Thùng rác, trả task để Hoàn tác.
    resp = client.delete(f"/api/tasks/{task_id}")
    assert resp.status_code == 200 and resp.get_json()["deleted_at"] is not None
    assert client.get(f"/api/tasks/{task_id}").status_code == 404


def test_list_hides_completed_by_default_and_sorts(client, list_id):
    ids = {}
    for title, due, prio in [
        ("không hạn", None, 1),
        ("hạn 12 thấp", "2026-11-12", 3),
        ("hạn 10", "2026-11-10", 2),
        ("hạn 12 cao", "2026-11-12", 1),
    ]:
        ids[title] = create(
            client, title=title, due_date=due, priority=prio, list_id=list_id
        ).get_json()["id"]
    client.post(f"/api/tasks/{ids['hạn 10']}/complete")

    titles = [t["title"] for t in client.get(f"/api/tasks?list_id={list_id}").get_json()]
    assert titles == ["hạn 12 cao", "hạn 12 thấp", "không hạn"]

    titles = [
        t["title"]
        for t in client.get(f"/api/tasks?list_id={list_id}&include_completed=true").get_json()
    ]
    assert titles == ["hạn 10", "hạn 12 cao", "hạn 12 thấp", "không hạn"]


def test_overdue_flag(client, list_id, monkeypatch):
    monkeypatch.setattr(timeutil, "now", lambda: datetime(2026, 11, 11, 9, 0, tzinfo=TZ))
    data = create(client, title="Trễ", list_id=list_id, due_date="2026-11-10").get_json()
    assert data["is_overdue"] is True


def test_vietnamese_title_round_trip(client, list_id):
    title = "Ôn tập “Triết học Mác - Lênin”: chương 3 — phép biện chứng"
    task_id = create(client, title=title, list_id=list_id).get_json()["id"]
    assert client.get(f"/api/tasks/{task_id}").get_json()["title"] == title


# ---- Feature 003: tag_names (nhãn từ ô thêm nhanh, research R14) --------------------------------


def _tags(client) -> list[dict]:
    return client.get("/api/tags").get_json()


def test_tag_names_gan_nhan_co_san_khong_phan_biet_dau(client):
    gap = client.post("/api/tags", json={"name": "Gấp"}).get_json()
    before = len(_tags(client))
    resp = client.post(
        "/api/tasks",
        json={"title": "Việc", "list_id": _list_id(client), "tag_names": ["gap", "GẤP"]},
    )
    assert resp.status_code == 201, resp.get_json()
    assert [t["id"] for t in resp.get_json()["tags"]] == [gap["id"]]
    assert len(_tags(client)) == before  # không tạo nhãn mới


def test_tag_names_tao_nhan_moi_cung_giao_dich(client):
    resp = client.post(
        "/api/tasks",
        json={"title": "Đọc sách", "list_id": _list_id(client), "tag_names": ["ThóiQuenMới"]},
    )
    assert resp.status_code == 201
    tags = resp.get_json()["tags"]
    assert [t["name"] for t in tags] == ["ThóiQuenMới"]
    assert tags[0]["color"]  # màu mặc định kế tiếp
    assert "ThóiQuenMới" in [t["name"] for t in _tags(client)]


def test_tag_names_ket_hop_tag_ids_giu_thu_tu_va_bo_trung(client):
    a = client.post("/api/tags", json={"name": "A"}).get_json()
    resp = client.post(
        "/api/tasks",
        json={
            "title": "Việc",
            "list_id": _list_id(client),
            "tag_ids": [a["id"]],
            "tag_names": ["a", "B", "b"],
        },
    )
    assert [t["name"] for t in resp.get_json()["tags"]] == ["A", "B"]


def test_tag_names_loi_validate_khong_de_lai_nhan_thua(client):
    before = len(_tags(client))
    resp = client.post(
        "/api/tasks",
        json={"title": "Việc", "list_id": 999999, "tag_names": ["NhanThua"]},
    )
    assert resp.status_code == 400
    assert len(_tags(client)) == before


def test_tag_names_ten_rong_hoac_qua_dai_bi_tu_choi(client):
    for name in ["", "x" * 51]:
        resp = client.post(
            "/api/tasks", json={"title": "Việc", "list_id": _list_id(client), "tag_names": [name]}
        )
        assert resp.status_code == 400


def _list_id(client) -> int:
    return next(
        item["id"] for item in client.get("/api/lists").get_json() if item["is_default_study"]
    )
