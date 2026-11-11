"""API bảng Kanban: GET /tasks/board và PATCH /tasks/{id}/board (feature 005, US1)."""

from datetime import datetime, timedelta

import pytest

from app.lib import timeutil
from app.lib.timeutil import TZ
from app.models import Task
from tests.integration.test_task_status_api import create

NOW = datetime(2026, 11, 11, 10, 0, tzinfo=TZ)


@pytest.fixture(autouse=True)
def fixed_now(monkeypatch):
    monkeypatch.setattr(timeutil, "now", lambda: NOW)


def board(client, query=""):
    response = client.get(f"/api/tasks/board{query}")
    assert response.status_code == 200, response.get_json()
    return response.get_json()


def ids(column):
    return [t["id"] for t in column]


def move(client, task_id, status, before_id=None, after_id=None):
    body = {"status": status, "before_id": before_id, "after_id": after_id}
    return client.patch(f"/api/tasks/{task_id}/board", json=body)


def test_ba_cot_theo_thu_tu(client):
    a, b, c = create(client, "A"), create(client, "B"), create(client, "C", status="doing")
    done = create(client, "D")
    client.post(f"/api/tasks/{done['id']}/complete")
    data = board(client)
    assert ids(data["columns"]["todo"]) == [b["id"], a["id"]]  # mới tạo nằm đầu cột
    assert ids(data["columns"]["doing"]) == [c["id"]]
    assert ids(data["columns"]["done"]) == [done["id"]]
    assert data["done_hidden_count"] == 0


def test_cot_xong_7_ngay(client, db_session):
    recent, old = create(client, "Mới"), create(client, "Cũ")
    for task, days in ((recent, 1), (old, 10)):
        client.post(f"/api/tasks/{task['id']}/complete")
        db_session.get(Task, task["id"]).completed_at = NOW - timedelta(days=days)
    db_session.flush()
    seven = board(client)
    assert ids(seven["columns"]["done"]) == [recent["id"]] and seven["done_hidden_count"] == 1
    everything = board(client, "?done_window=all")
    assert set(ids(everything["columns"]["done"])) == {recent["id"], old["id"]}
    assert everything["done_hidden_count"] == 0
    assert client.get("/api/tasks/board?done_window=1y").status_code == 400


def test_khong_co_task_thung_rac(client):
    task = create(client, "Bỏ")
    client.delete(f"/api/tasks/{task['id']}")
    assert board(client)["columns"]["todo"] == []


def test_todo_sang_doing_va_xong_giong_tick(client):
    task = create(client)
    doing = move(client, task["id"], "doing").get_json()
    assert doing["task"]["status"] == "doing"
    done = move(client, task["id"], "done").get_json()["task"]
    assert done["status"] == "done" and done["completed_at"] and done["completed"]
    reference = create(client, "Đối chiếu")
    ticked = client.post(f"/api/tasks/{reference['id']}/complete").get_json()
    assert set(done) == set(ticked) - {"next_task"}
    assert ticked["status"] == "done"


def test_chuyen_xong_dong_bo_feed_nhu_tick(client):
    a, b = create(client, "A"), create(client, "B")
    before = client.get("/api/sync/changes?after=0").get_json()
    client.post(f"/api/tasks/{a['id']}/complete")
    move(client, b["id"], "done")
    after = client.get("/api/sync/changes?after=0").get_json()
    assert after["revision"] - before["revision"] >= 2  # cả hai lần đều tăng revision


def test_xong_ve_chua_lam_va_dang_lam(client):
    task = create(client)
    move(client, task["id"], "done")
    todo = move(client, task["id"], "todo").get_json()["task"]
    assert todo["status"] == "todo" and not todo["completed"]
    move(client, task["id"], "done")
    doing = move(client, task["id"], "doing").get_json()["task"]
    assert doing["status"] == "doing" and not doing["completed"]


def test_dat_vi_tri_giua_hai_the(client):
    a, b, c = create(client, "A"), create(client, "B"), create(client, "C")
    # Cột todo hiện [C, B, A]. Kéo A lên đầu rồi giữa.
    move(client, a["id"], "todo", before_id=None, after_id=c["id"])
    assert ids(board(client)["columns"]["todo"]) == [a["id"], c["id"], b["id"]]
    move(client, a["id"], "todo", before_id=c["id"], after_id=b["id"])
    assert ids(board(client)["columns"]["todo"]) == [c["id"], a["id"], b["id"]]
    move(client, a["id"], "todo", before_id=b["id"], after_id=None)
    assert ids(board(client)["columns"]["todo"]) == [c["id"], b["id"], a["id"]]


def test_chuyen_cot_chen_vao_giua(client):
    x, y = create(client, "X", status="doing"), create(client, "Y", status="doing")
    task = create(client, "T")
    result = move(client, task["id"], "doing", before_id=y["id"], after_id=x["id"])
    assert result.status_code == 200
    assert ids(board(client)["columns"]["doing"]) == [y["id"], task["id"], x["id"]]


def test_the_ke_khong_thuoc_cot_dich_la_loi(client):
    a, b = create(client, "A"), create(client, "B", status="doing")
    response = move(client, a["id"], "todo", after_id=b["id"])
    assert response.status_code == 400
    assert "after_id" in response.get_json()["error"]["fields"]
    assert move(client, a["id"], "doing", before_id=a["id"]).status_code == 400
    assert move(client, 999999, "doing").status_code == 404


def test_task_thung_rac_khong_chuyen_duoc(client):
    task = create(client)
    client.delete(f"/api/tasks/{task['id']}")
    assert move(client, task["id"], "doing").status_code == 404


def test_task_lap_keo_sang_xong_sinh_lan_ke_tiep_va_hoan_tac(client):
    task = create(client, "Lặp", due_date="2026-11-12", recurrence={"freq": "daily"})
    result = move(client, task["id"], "done").get_json()
    nxt = result["next_task"]
    assert nxt and nxt["status"] == "todo" and nxt["id"] != task["id"]
    assert result["undo"]["status"] == "todo"
    assert nxt["id"] in ids(board(client)["columns"]["todo"])
    undone = move(client, task["id"], **{"status": result["undo"]["status"]}).get_json()
    assert undone["task"]["status"] == "todo"
    assert nxt["id"] not in ids(board(client)["columns"]["todo"])  # lần kế tiếp chưa sửa bị gỡ


def test_hoan_tac_ve_dung_cot_va_vi_tri(client):
    a, b, c = (
        create(client, "A", status="doing"),
        create(client, "B", status="doing"),
        create(client, "C", status="doing"),
    )
    # doing: [C, B, A]; kéo B sang done rồi hoàn tác về giữa C và A.
    result = move(client, b["id"], "done").get_json()
    undo = result["undo"]
    assert undo == {"status": "doing", "before_id": c["id"], "after_id": a["id"]}
    move(client, b["id"], undo["status"], undo["before_id"], undo["after_id"])
    assert ids(board(client)["columns"]["doing"]) == [c["id"], b["id"], a["id"]]


def test_doi_cho_nhieu_lan_van_dung_thu_tu(client):
    a, b, c = create(client, "A"), create(client, "B"), create(client, "C")
    # todo: [C, B, A]. Chèn liên tiếp giữa hai thẻ để buộc phải sắp lại cột.
    anchor_top, anchor_bottom = c["id"], b["id"]
    inserted = []
    for _ in range(45):
        moved = create(client, "m")
        move(client, moved["id"], "todo", before_id=anchor_top, after_id=anchor_bottom)
        inserted.append(moved["id"])
        anchor_bottom = moved["id"]
    order = ids(board(client)["columns"]["todo"])
    assert order == [c["id"], *reversed(inserted), b["id"], a["id"]]
