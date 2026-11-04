import pytest
from sqlalchemy import select

from app.models import TaskList


def lists(client):
    return {item["name"]: item for item in client.get("/api/lists").get_json()}


def test_default_lists(client):
    data = lists(client)
    assert list(data) == ["Học tập", "Cá nhân", "Công việc"]
    assert data["Học tập"]["is_default_study"] is True
    assert data["Cá nhân"]["open_task_count"] == 0


def test_create_rename_recolor(client):
    resp = client.post("/api/lists", json={"name": "Câu lạc bộ"})
    assert resp.status_code == 201
    created = resp.get_json()
    assert created["color"] == "c04"  # màu chưa dùng tiếp theo
    resp = client.patch(f"/api/lists/{created['id']}", json={"name": "CLB Tin học", "color": "c09"})
    assert resp.get_json()["name"] == "CLB Tin học"
    assert resp.get_json()["color"] == "c09"
    assert client.patch(f"/api/lists/{created['id']}", json={"color": "red"}).status_code == 400


def test_duplicate_name_case_insensitive_rejected(client):
    resp = client.post("/api/lists", json={"name": "HỌC TẬP"})
    assert resp.status_code == 400
    assert resp.get_json()["error"]["fields"]["name"] == "Đã có danh sách tên này"


def test_delete_list_with_tasks_requires_choice(client):
    personal = lists(client)["Cá nhân"]["id"]
    work = lists(client)["Công việc"]["id"]
    task_id = client.post("/api/tasks", json={"title": "Mua sách", "list_id": personal}).get_json()[
        "id"
    ]

    resp = client.delete(f"/api/lists/{personal}")
    assert resp.status_code == 409
    assert resp.get_json()["error"]["details"] == {"task_count": 1}

    assert client.delete(f"/api/lists/{personal}?move_to={work}").status_code == 204
    assert client.get(f"/api/tasks/{task_id}").get_json()["list_id"] == work
    assert "Cá nhân" not in lists(client)


def test_delete_list_and_its_tasks(client):
    work = lists(client)["Công việc"]["id"]
    task_id = client.post("/api/tasks", json={"title": "Báo cáo", "list_id": work}).get_json()["id"]
    assert client.delete(f"/api/lists/{work}?delete_tasks=true").status_code == 204
    assert client.get(f"/api/tasks/{task_id}").status_code == 404
    # Feature 002 FR-030: task vào Thùng rác chứ không bị xoá hẳn.
    trash = client.get("/api/tasks?view=trash").get_json()
    assert [t["id"] for t in trash] == [task_id]


def test_default_study_list_needs_replacement(client, db_session):
    study = lists(client)["Học tập"]["id"]
    personal = lists(client)["Cá nhân"]["id"]

    resp = client.delete(f"/api/lists/{study}")
    assert resp.status_code == 400
    assert resp.get_json()["error"]["code"] == "default_list_requires_replacement"

    assert client.delete(f"/api/lists/{study}?move_to={personal}").status_code == 204
    new_default = db_session.scalars(select(TaskList).where(TaskList.is_default_study)).one()
    assert new_default.id == personal


# ---- Emoji của danh sách (feature 002 FR-015, task T020) -------------------------------------


@pytest.mark.parametrize("emoji", ["🏠", "❤️", "👍🏽", "👨‍👩‍👧", "🇻🇳"])
def test_list_emoji_valid(client, emoji):
    resp = client.post("/api/lists", json={"name": "Nhà", "emoji": emoji})
    assert resp.status_code == 201, resp.get_json()
    assert resp.get_json()["emoji"] == emoji
    assert lists(client)["Nhà"]["emoji"] == emoji


@pytest.mark.parametrize("emoji", ["ab", "a", "🏠🏠", "🏠a", "🏠 a", "1️⃣", ""])
def test_list_emoji_invalid(client, emoji):
    resp = client.post("/api/lists", json={"name": "Nhà", "emoji": emoji})
    assert resp.status_code == 400
    assert resp.get_json()["error"]["fields"] == {"emoji": "Chỉ chọn một emoji"}


def test_list_emoji_patch_and_remove(client):
    personal = lists(client)["Cá nhân"]
    assert personal["emoji"] is None
    resp = client.patch(f"/api/lists/{personal['id']}", json={"emoji": "🏠"})
    assert resp.status_code == 200 and resp.get_json()["emoji"] == "🏠"
    assert client.patch(f"/api/lists/{personal['id']}", json={"emoji": "🏠🏠"}).status_code == 400
    resp = client.patch(f"/api/lists/{personal['id']}", json={"emoji": None})
    assert resp.get_json()["emoji"] is None
    # Đổi tên không làm mất emoji.
    client.patch(f"/api/lists/{personal['id']}", json={"emoji": "📚"})
    resp = client.patch(f"/api/lists/{personal['id']}", json={"name": "Riêng tư"})
    assert resp.get_json()["emoji"] == "📚"
