"""Trạng thái "Đang làm", thứ tự mặc định và môn gắn tay của task (feature 005, nền tảng)."""

from tests.factories import make_semester, make_subject


def create(client, title="Việc", **extra):
    lists = client.get("/api/lists").get_json()
    body = {"title": title, "list_id": lists[0]["id"], **extra}
    response = client.post("/api/tasks", json=body)
    assert response.status_code == 201, response.get_json()
    return response.get_json()


def test_task_moi_o_cot_chua_lam_dau_cot(client):
    a, b, c = create(client, "A"), create(client, "B"), create(client, "C")
    assert [a["status"], b["status"], c["status"]] == ["todo"] * 3
    assert c["board_rank"] < b["board_rank"] < a["board_rank"]
    assert a["subject_id"] is None and a["effective_subject_id"] is None
    assert a["attachment_count"] == 0


def test_tao_voi_trang_thai_dang_lam(client):
    task = create(client, status="doing")
    assert task["status"] == "doing" and not task["completed"]


def test_doi_trang_thai_qua_patch(client):
    task = create(client)
    other = create(client, "Khác")
    doing = client.patch(f"/api/tasks/{task['id']}", json={"status": "doing"}).get_json()
    assert doing["status"] == "doing"
    back = client.patch(f"/api/tasks/{task['id']}", json={"status": "todo"}).get_json()
    assert back["status"] == "todo" and back["board_rank"] < other["board_rank"]  # lên đầu cột
    assert client.patch(f"/api/tasks/{task['id']}", json={"status": "done"}).status_code == 400


def test_hoan_thanh_dat_lai_dang_lam_va_bo_tick_ve_chua_lam(client):
    task = create(client, status="doing")
    done = client.post(f"/api/tasks/{task['id']}/complete").get_json()
    assert done["status"] == "done"
    undone = client.post(f"/api/tasks/{task['id']}/uncomplete").get_json()
    assert undone["status"] == "todo"
    doing = client.patch(f"/api/tasks/{task['id']}", json={"status": "doing"}).get_json()
    client.post(f"/api/tasks/{task['id']}/complete")
    again = client.patch(f"/api/tasks/{task['id']}", json={"status": "doing"}).get_json()
    assert doing["status"] == "doing" and again["status"] == "doing" and not again["completed"]


def test_gan_mon_hoc(client, db_session):
    subject = make_subject(db_session, make_semester(db_session))
    task = create(client, subject_id=subject.id)
    assert task["subject_id"] == subject.id and task["effective_subject_id"] == subject.id
    cleared = client.patch(f"/api/tasks/{task['id']}", json={"subject_id": None}).get_json()
    assert cleared["subject_id"] is None
    bad = client.patch(f"/api/tasks/{task['id']}", json={"subject_id": 999999})
    assert bad.status_code == 400 and "subject_id" in bad.get_json()["error"]["fields"]
