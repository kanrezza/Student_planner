"""Sao lưu gồm cả file đính kèm (.lhbackup format 2) và khôi phục (feature 005, US6, SC-007)."""

import hashlib
import io
import json
import os
import time
import zipfile

import pytest
import sqlalchemy as sa

from app.extensions import db
from app.services import attachments_store as store
from tests.ocr_helpers import load_attachment


@pytest.fixture
def client(isolated_app):
    return isolated_app.test_client()


@pytest.fixture
def kho(isolated_app):
    """Gốc kho file đính kèm của app cô lập (cần app context để đọc cấu hình)."""
    with isolated_app.app_context():
        return store.root()


@pytest.fixture(autouse=True)
def clean_state(isolated_app):
    with isolated_app.app_context():
        db.session.execute(sa.text("DELETE FROM attachments"))
        db.session.execute(sa.text("DELETE FROM attachment_blobs"))
        db.session.execute(sa.text("DELETE FROM tasks"))
        db.session.execute(sa.text("DELETE FROM backup_jobs"))
        db.session.commit()
        db.session.remove()
        root = store.root()
        for child in list(root.iterdir()):
            if child.is_dir():
                import shutil

                shutil.rmtree(child)
    yield


def add_task(client, title="Việc có file") -> int:
    lists = client.get("/api/lists").get_json()
    resp = client.post("/api/tasks", json={"title": title, "list_id": lists[0]["id"]})
    assert resp.status_code == 201
    return resp.get_json()["id"]


def attach(client, task_id, name, content) -> dict:
    resp = client.post(
        "/api/attachments",
        data={"owner_type": "task", "owner_id": str(task_id), "file": (io.BytesIO(content), name)},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["attachments"][0]


def make_dump(client) -> bytes:
    resp = client.get("/api/backup/dump?kind=thu-cong")
    assert resp.status_code == 200
    return resp.data


def restore(client, data):
    return client.post("/api/backup/restore", data=data, content_type="application/zip")


def wipe(isolated_app):
    """Mô phỏng máy mới: không còn dữ liệu và không còn file."""
    import shutil

    with isolated_app.app_context():
        db.session.execute(sa.text("DELETE FROM attachments"))
        db.session.execute(sa.text("DELETE FROM attachment_blobs"))
        db.session.execute(sa.text("DELETE FROM tasks"))
        db.session.commit()
        db.session.remove()
        for child in store.root().iterdir():
            shutil.rmtree(child) if child.is_dir() else child.unlink()


def rewrite(data: bytes, change) -> bytes:
    out = io.BytesIO()
    with (
        zipfile.ZipFile(io.BytesIO(data)) as src,
        zipfile.ZipFile(out, "w", zipfile.ZIP_STORED) as dst,
    ):
        for item in src.infolist():
            payload = change(item.filename, src.read(item.filename))
            if payload is not None:
                dst.writestr(item.filename, payload)
    return out.getvalue()


def test_file_zip_co_blob_va_manifest_format_2(client):
    task = add_task(client)
    pdf, png = load_attachment("de-cuong.pdf"), load_attachment("anh-nho.png")
    attach(client, task, "a.pdf", pdf)
    attach(client, task, "b.pdf", pdf)  # trùng nội dung: một mục trong zip
    attach(client, task, "c.png", png)
    client.delete(f"/api/tasks/{task}")  # task trong Thùng rác vẫn nằm trong bản sao lưu
    with zipfile.ZipFile(io.BytesIO(make_dump(client))) as zf:
        names = sorted(zf.namelist())
        manifest = json.loads(zf.read("manifest.json"))
        assert all(i.compress_type == zipfile.ZIP_STORED for i in zf.infolist())
        sha_pdf = hashlib.sha256(pdf).hexdigest()
        assert f"attachments/{sha_pdf}" in names and zf.read(f"attachments/{sha_pdf}") == pdf
    assert names[:2] == [
        f"attachments/{n}" for n in sorted([sha_pdf, hashlib.sha256(png).hexdigest()])
    ]
    assert manifest["format"] == 2
    assert manifest["attachments"] == {"count": 2, "bytes": len(pdf) + len(png)}


def test_khoi_phuc_vao_may_trong_mo_duoc_file_khop_noi_dung(client, isolated_app, kho):
    task = add_task(client)
    pdf = load_attachment("de-cuong.pdf")
    first = attach(client, task, "Đề cương.pdf", pdf)
    dump = make_dump(client)
    wipe(isolated_app)
    assert client.get("/api/attachments/stats").get_json()["blob_count"] == 0
    response = restore(client, dump)
    assert response.status_code == 200, response.get_json()
    stats = client.get("/api/attachments/stats").get_json()
    assert stats["blob_count"] == 1 and stats["total_bytes"] == len(pdf)
    restored = client.get(f"/api/attachments/{first['id']}")
    assert restored.status_code == 200
    assert client.get(first["content_url"]).data == pdf
    assert not (kho / ".restore").exists() or not list((kho / ".restore").iterdir())


def test_khoi_phuc_ban_format_1_chay_duoc_va_don_blob_khong_con_tham_chieu(
    client, isolated_app, kho
):
    task = add_task(client, "Cũ")
    dump = make_dump(client)  # chưa có file
    old = rewrite(
        dump,
        lambda name, data: (
            json.dumps({**json.loads(data), "format": 1, "attachments": None}).encode()
            if name == "manifest.json"
            else data
        ),
    )
    # Sau khi sao lưu mới gắn file: bản format 1 không có nó.
    stray = attach(client, task, "moi.pdf", load_attachment("de-cuong.pdf"))
    sha = hashlib.sha256(load_attachment("de-cuong.pdf")).hexdigest()
    blob = kho / sha[:2] / sha
    assert blob.exists() and stray["id"]
    assert restore(client, old).status_code == 200
    assert client.get("/api/attachments/stats").get_json()["blob_count"] == 0
    past = time.time() - 7200
    os.utime(blob, (past, past))
    from app.services import attachments

    with isolated_app.app_context():
        attachments.sweep_orphans()
    assert not blob.exists()


def test_blob_bi_sua_thi_tu_choi_va_giu_nguyen_du_lieu_hien_tai(client, kho):
    task = add_task(client)
    attach(client, task, "a.pdf", load_attachment("de-cuong.pdf"))
    dump = make_dump(client)
    current = add_task(client, "Việc hiện tại")
    bad = rewrite(dump, lambda name, data: b"hong" if name.startswith("attachments/") else data)
    response = restore(client, bad)
    assert response.status_code == 400 and response.get_json()["error"]["code"] == "backup_corrupt"
    titles = [t["title"] for t in client.get("/api/tasks?view=all").get_json()]
    assert "Việc hiện tại" in titles and current
    assert client.get("/api/attachments/stats").get_json()["blob_count"] == 1
    restore_dir = kho / ".restore"
    assert not restore_dir.exists() or not any(restore_dir.iterdir())


def test_thieu_file_trong_zip_thi_tu_choi(client):
    task = add_task(client)
    attach(client, task, "a.pdf", load_attachment("de-cuong.pdf"))
    dump = make_dump(client)
    missing = rewrite(dump, lambda name, data: None if name.startswith("attachments/") else data)
    assert restore(client, missing).get_json()["error"]["code"] == "backup_corrupt"


def test_loi_sau_khi_nap_dump_hoan_tac_va_file_cu_con(client, isolated_app, monkeypatch, kho):
    task = add_task(client)
    pdf = load_attachment("de-cuong.pdf")
    attach(client, task, "a.pdf", pdf)
    dump = make_dump(client)

    def boom(*_args, **_kwargs):
        raise OSError("hết chỗ khi chuyển file")

    monkeypatch.setattr(store, "ensure_blob_from", boom)
    wipe(isolated_app)
    response = restore(client, dump)
    assert response.status_code == 500
    assert client.get("/api/attachments/stats").get_json()["blob_count"] == 0  # dữ liệu như trước
    monkeypatch.undo()
    assert not (kho / ".restore").exists() or not any((kho / ".restore").iterdir())


def test_status_co_so_lieu_file_va_canh_bao_vuot_nguong(client):
    task = add_task(client)
    status = client.get("/api/backup/status").get_json()
    assert status["attachments_bytes"] == 0 and status["attachments_warning"] is False
    attach(client, task, "lon.bin", b"x" * (2 * 1024 * 1024))
    assert client.get("/api/backup/status").get_json()["attachments_warning"] is False
    client.patch("/api/settings", json={"backup_attachments_warn_mb": 100})
    # Ngưỡng tối thiểu 100 MB: dùng bản ghi tổng lớn bằng cách đặt ngưỡng thấp trực tiếp.
    with client.application.app_context():
        db.session.execute(sa.text("UPDATE settings SET backup_attachments_warn_mb = 100"))
        db.session.execute(sa.text("UPDATE attachment_blobs SET size = 200 * 1024 * 1024"))
        db.session.commit()
    status = client.get("/api/backup/status").get_json()
    assert status["attachments_warning"] is True
    assert status["estimated_backup_bytes"] >= status["attachments_bytes"] == 200 * 1024 * 1024
