"""POST /api/backup/restore: khôi phục trọn vẹn, từ chối bản hỏng / quá mới (feature 003, T039)."""

import io
import json
import time
import zipfile

import pytest
import sqlalchemy as sa

from app.extensions import db
from app.services import backup


@pytest.fixture
def client(isolated_app):
    return isolated_app.test_client()


@pytest.fixture(autouse=True)
def clean_database(isolated_app):
    """Mỗi test bắt đầu từ dữ liệu trống (xoá task, đặt lại cấu hình sao lưu mặc định)."""
    with isolated_app.app_context():
        db.session.execute(sa.text("DELETE FROM tasks"))
        db.session.execute(sa.text("DELETE FROM backup_jobs"))
        db.session.execute(
            sa.text("UPDATE backup_config SET retention_count = 14, schedule_time = '21:00'")
        )
        db.session.commit()
        db.session.remove()
    yield


def study_list_id(client) -> int:
    return client.get("/api/lists").get_json()[0]["id"]


def add_task(client, title: str) -> int:
    resp = client.post("/api/tasks", json={"title": title, "list_id": study_list_id(client)})
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["id"]


def task_titles(client) -> list[str]:
    return sorted(t["title"] for t in client.get("/api/tasks?view=all").get_json())


def make_dump(client, kind="thu-cong") -> bytes:
    resp = client.get(f"/api/backup/dump?kind={kind}")
    assert resp.status_code == 200
    return resp.data


def restore(client, data: bytes):
    return client.post("/api/backup/restore", data=data, content_type="application/zip")


def rebuild_zip(data: bytes, manifest_changes: dict) -> bytes:
    """Ghi lại file .lhbackup với manifest đã sửa (giữ nguyên dump)."""
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        manifest = {**json.loads(zf.read("manifest.json")), **manifest_changes}
        dump = zf.read("data.dump")
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.writestr("data.dump", dump)
    return out.getvalue()


def test_khoi_phuc_tra_lai_du_lieu_va_giu_cau_hinh_sao_luu(client, isolated_app):
    add_task(client, "Kiểm tra khôi phục")
    add_task(client, "Việc thứ hai")
    dump = make_dump(client)

    # Sau khi sao lưu: xoá hẳn một việc, thêm một việc mới, đổi cấu hình sao lưu.
    first = next(
        t["id"]
        for t in client.get("/api/tasks?view=all").get_json()
        if t["title"] == "Kiểm tra khôi phục"
    )
    assert client.delete(f"/api/tasks/{first}").status_code == 200  # vào Thùng rác
    assert client.delete("/api/trash").get_json()["deleted"] == 1  # rồi xoá hẳn
    add_task(client, "Việc tạo sau khi sao lưu")
    client.patch("/api/backup/config", json={"retention_count": 5, "schedule_time": "22:15"})
    job = client.post("/api/backup/jobs", json={"kind": "backup_now"}).get_json()
    revision_before = client.get("/api/sync/changes?after=0&wait=0").get_json()["revision"]

    resp = restore(client, dump)
    assert resp.status_code == 200, resp.get_json()
    assert resp.get_json()["schema_upgraded"] is False

    assert task_titles(client) == ["Kiểm tra khôi phục", "Việc thứ hai"]
    config = client.get("/api/backup/config").get_json()
    assert config["retention_count"] == 5 and config["schedule_time"] == "22:15"  # R9
    status = client.get("/api/backup/status").get_json()
    assert status["job"]["id"] == job["id"] and status["job"]["state"] == "pending"  # việc còn đó
    revision_after = client.get("/api/sync/changes?after=0&wait=0").get_json()["revision"]
    assert revision_after > revision_before


def test_khoi_phuc_xong_cho_phep_tao_viec_moi_va_cac_api_hoat_dong(client, isolated_app):
    add_task(client, "A")
    dump = make_dump(client)
    assert restore(client, dump).status_code == 200
    assert client.get("/api/health").status_code == 200
    assert add_task(client, "B")
    assert client.post("/api/backup/jobs", json={"kind": "backup_now"}).status_code == 201
    with isolated_app.app_context():
        assert not backup.is_restoring()


def test_ban_hong_bi_tu_choi_va_du_lieu_giu_nguyen(client):
    add_task(client, "Còn nguyên")
    dump = bytearray(make_dump(client))
    offset = dump.find(b"PGDMP") + 40
    dump[offset] ^= 0xFF  # sửa vài byte trong phần dump
    resp = restore(client, bytes(dump))
    assert resp.status_code == 400
    assert resp.get_json()["error"]["code"] == "backup_corrupt"
    assert resp.get_json()["error"]["message"] == "Bản sao lưu bị hỏng, không thể khôi phục"
    assert task_titles(client) == ["Còn nguyên"]


def test_file_khong_phai_zip_va_file_rong_la_ban_hong(client):
    assert restore(client, b"khong phai zip").get_json()["error"]["code"] == "backup_corrupt"
    assert restore(client, b"").status_code == 400


def test_ban_moi_hon_app_bi_tu_choi(client):
    add_task(client, "Còn nguyên")
    dump = rebuild_zip(make_dump(client), {"schema_revision": "9999_tuong_lai"})
    resp = restore(client, dump)
    assert resp.status_code == 409
    assert resp.get_json()["error"]["code"] == "backup_too_new"
    assert task_titles(client) == ["Còn nguyên"]


def test_loi_khi_nap_du_lieu_giu_nguyen_du_lieu_cu(client, isolated_app, monkeypatch):
    add_task(client, "Còn nguyên")
    dump = make_dump(client)
    add_task(client, "Việc thêm sau")

    def fail(_path):
        raise backup.BackupError(500, "restore_failed", "giả lập")

    monkeypatch.setattr(backup, "_restore_dump", fail)
    resp = restore(client, dump)
    assert resp.status_code == 500 and resp.get_json()["error"]["code"] == "restore_failed"
    monkeypatch.undo()
    assert task_titles(client) == ["Còn nguyên", "Việc thêm sau"]
    with isolated_app.app_context():
        assert not backup.is_restoring()  # cờ bảo trì luôn được gỡ


def test_khoi_phuc_that_su_o_che_do_bao_tri(client, isolated_app, monkeypatch):
    add_task(client, "A")
    dump = make_dump(client)
    seen = {}
    real = backup._restore_dump

    def spy(path):
        seen["restoring"] = backup.is_restoring()
        seen["tasks_status"] = client.get("/api/tasks?view=all").status_code
        real(path)

    monkeypatch.setattr(backup, "_restore_dump", spy)
    assert restore(client, dump).status_code == 200
    assert seen == {"restoring": True, "tasks_status": 503}


def test_hai_lan_khoi_phuc_lien_tiep_deu_thanh_cong(client):
    add_task(client, "A")
    dump = make_dump(client)
    start = time.monotonic()
    assert restore(client, dump).status_code == 200
    assert restore(client, dump).status_code == 200
    assert time.monotonic() - start < 60  # SC-002: một học kỳ khôi phục dưới 1 phút


def test_khoi_phuc_giu_du_chuoi_task_lap_va_quy_tac(client):
    """quickstart R7: sao lưu → xoá chuỗi → khôi phục còn đủ chuỗi và quy tắc."""
    rule = {"freq": "weekly", "weekdays": [1, 4], "end": {"kind": "after_count", "count": 5}}
    resp = client.post(
        "/api/tasks",
        json={
            "title": "Nộp báo cáo tuần",
            "list_id": study_list_id(client),
            "due_date": "2026-11-09",
            "recurrence": rule,
        },
    )
    assert resp.status_code == 201, resp.get_json()
    original = resp.get_json()
    dump = make_dump(client)

    assert client.delete(f"/api/tasks/{original['id']}?scope=following").status_code == 200
    assert client.delete("/api/trash").get_json()["deleted"] == 1
    assert task_titles(client) == []

    assert restore(client, dump).status_code == 200
    tasks = client.get("/api/tasks?view=all").get_json()
    assert [t["title"] for t in tasks] == ["Nộp báo cáo tuần"]
    assert tasks[0]["series_id"] == original["series_id"]
    assert tasks[0]["recurrence"] == original["recurrence"] == {**rule, "weekdays": [1, 4]}
    nxt = client.post(f"/api/tasks/{tasks[0]['id']}/complete").get_json()["next_task"]
    assert nxt["due_date"] == "2026-11-12"  # chuỗi vẫn sinh được lần kế tiếp sau khi khôi phục
