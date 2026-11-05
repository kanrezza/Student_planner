"""Khôi phục bản sao lưu từ phiên bản schema cũ hơn (feature 003, T040)."""

import pytest
import sqlalchemy as sa
from flask_migrate import downgrade, upgrade

from app.extensions import db
from app.services import backup


@pytest.fixture
def client(isolated_app):
    return isolated_app.test_client()


@pytest.fixture(autouse=True)
def clean_database(isolated_app):
    with isolated_app.app_context():
        db.session.execute(sa.text("DELETE FROM tasks"))
        db.session.execute(sa.text("DELETE FROM backup_jobs"))
        db.session.execute(sa.text("UPDATE backup_config SET retention_count = 14"))
        db.session.commit()
        db.session.remove()
    yield


def add_task(client, title):
    list_id = client.get("/api/lists").get_json()[0]["id"]
    resp = client.post("/api/tasks", json={"title": title, "list_id": list_id})
    assert resp.status_code == 201, resp.get_json()


def titles(client):
    return sorted(t["title"] for t in client.get("/api/tasks?view=all").get_json())


def revision(isolated_app):
    with isolated_app.app_context():
        value = db.session.scalar(sa.text("SELECT version_num FROM alembic_version"))
        db.session.remove()
        return value


@pytest.fixture
def old_dump(isolated_app, client):
    """Bản sao lưu tạo khi schema còn ở 0005 (chưa có bảng sao lưu); xong trả schema về mới nhất."""
    add_task(client, "Việc của bản cũ")
    with isolated_app.app_context():
        db.session.remove()
        db.engine.dispose()
        downgrade(revision="0005_exams")
        data = isolated_app.test_client().get("/api/backup/dump?kind=thu-cong").data
        db.session.remove()
        db.engine.dispose()
        upgrade()
    client.patch("/api/backup/config", json={"retention_count": 9})
    return data


def test_ban_cu_duoc_nang_cap_va_cau_hinh_sao_luu_con_nguyen(client, isolated_app, old_dump):
    add_task(client, "Việc tạo sau")
    resp = client.post("/api/backup/restore", data=old_dump, content_type="application/zip")
    assert resp.status_code == 200, resp.get_json()
    assert resp.get_json()["schema_upgraded"] is True
    assert revision(isolated_app) == "0006_backup"
    assert titles(client) == ["Việc của bản cũ"]
    assert client.get("/api/backup/config").get_json()["retention_count"] == 9
    assert client.get("/api/backup/status").status_code == 200  # các bảng sao lưu dùng được


def test_nang_cap_loi_tu_dua_du_lieu_ve_nhu_cu(client, isolated_app, old_dump, monkeypatch):
    add_task(client, "Việc tạo sau")

    def boom():
        raise RuntimeError("giả lập migration lỗi")

    monkeypatch.setattr(backup, "_upgrade_database", boom)
    resp = client.post("/api/backup/restore", data=old_dump, content_type="application/zip")
    assert resp.status_code == 500
    error = resp.get_json()["error"]
    assert error["code"] == "upgrade_failed"
    assert "đã được đưa về như trước khi khôi phục" in error["message"]
    monkeypatch.undo()

    assert revision(isolated_app) == "0006_backup"
    assert titles(client) == ["Việc của bản cũ", "Việc tạo sau"]  # nguyên như trước khi khôi phục
    assert client.get("/api/backup/config").get_json()["retention_count"] == 9
    with isolated_app.app_context():
        assert not backup.is_restoring()
