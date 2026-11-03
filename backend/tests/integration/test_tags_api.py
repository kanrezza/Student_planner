from tests.integration.helpers import create_semester, create_subject, create_task, sessions_of


def tags(client):
    return {t["name"]: t for t in client.get("/api/tags").get_json()}


def new_tag(client, name, color="c07"):
    resp = client.post("/api/tags", json={"name": name, "color": color})
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()


def test_create_and_duplicate(client):
    assert "E-Learning" in tags(client)
    new_tag(client, "Gấp")
    resp = client.post("/api/tags", json={"name": "gấp"})
    assert resp.status_code == 400
    assert resp.get_json()["error"]["fields"]["name"] == "Đã có nhãn tên này"


def test_system_tag_only_color_changes(client):
    e_learning = tags(client)["E-Learning"]
    assert client.patch(f"/api/tags/{e_learning['id']}", json={"name": "Online"}).status_code == 400
    assert client.delete(f"/api/tags/{e_learning['id']}").status_code == 400
    resp = client.patch(f"/api/tags/{e_learning['id']}", json={"color": "c09"})
    assert resp.status_code == 200 and resp.get_json()["color"] == "c09"


def test_task_tags_order_and_display_color(client, db_session):
    gap, hop = new_tag(client, "Gấp", "c07"), new_tag(client, "Họp", "c04")
    task = create_task(client, db_session)
    resp = client.put(f"/api/tasks/{task['id']}/tags", json={"tag_ids": [hop["id"], gap["id"]]})
    assert resp.status_code == 200
    data = client.get(f"/api/tasks/{task['id']}").get_json()
    assert [t["name"] for t in data["tags"]] == ["Họp", "Gấp"]
    assert data["display_color"] == "c04"


def test_session_effective_tags_and_delete(client, db_session):
    gap, hop = new_tag(client, "Gấp", "c07"), new_tag(client, "Họp", "c04")
    subject = create_subject(client, create_semester(client))
    sessions = sessions_of(client, subject["id"])
    client.put(f"/api/subjects/{subject['id']}/tags", json={"tag_ids": [gap["id"]]})
    resp = client.put(f"/api/sessions/{sessions[0]['id']}/tags", json={"tag_ids": [hop["id"]]})
    assert resp.status_code == 200

    first, second = sessions_of(client, subject["id"])[:2]
    assert [t["name"] for t in first["tags"]] == ["Gấp", "Họp"]  # nhãn môn trước, rồi nhãn riêng
    assert first["own_tag_ids"] == [hop["id"]]
    assert first["display_color"] == "c07"
    assert [t["name"] for t in second["tags"]] == ["Gấp"]

    assert client.delete(f"/api/tags/{gap['id']}").status_code == 204
    first, second = sessions_of(client, subject["id"])[:2]
    assert [t["name"] for t in first["tags"]] == ["Họp"]
    assert second["tags"] == [] and second["display_color"] == subject["color"]


def test_filter_calendar_and_tasks_by_tags(client, db_session):
    gap, hop = new_tag(client, "Gấp"), new_tag(client, "Họp")
    t1 = create_task(client, db_session, "A", due_date="2026-09-08", tag_ids=[gap["id"]])
    t2 = create_task(client, db_session, "B", due_date="2026-09-09", tag_ids=[hop["id"]])
    create_task(client, db_session, "C", due_date="2026-09-09")
    subject = create_subject(client, create_semester(client))
    session_id = sessions_of(client, subject["id"])[0]["id"]
    client.put(f"/api/sessions/{session_id}/tags", json={"tag_ids": [gap["id"]]})

    data = client.get(f"/api/calendar?from=2026-09-07&to=2026-09-13&tags={gap['id']}").get_json()
    assert [t["id"] for t in data["tasks"]] == [t1["id"]]
    assert [s["id"] for s in data["sessions"]] == [session_id]

    both = client.get(f"/api/tasks?tags={gap['id']},{hop['id']}").get_json()
    assert sorted(t["id"] for t in both) == sorted([t1["id"], t2["id"]])
