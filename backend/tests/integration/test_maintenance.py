"""Chế độ bảo trì khi đang khôi phục (feature 003, T041)."""

from pathlib import Path

import pytest


@pytest.fixture
def flag(isolated_app):
    path = Path(isolated_app.config["RESTORE_FLAG_PATH"])
    path.write_text("test")
    yield path
    path.unlink(missing_ok=True)


@pytest.fixture
def client(isolated_app):
    return isolated_app.test_client()


def test_dang_khoi_phuc_cac_api_khac_tra_503(client, flag):
    resp = client.get("/api/tasks?view=all")
    assert resp.status_code == 503
    error = resp.get_json()["error"]
    assert error["code"] == "restoring"
    assert error["message"] == "Đang khôi phục dữ liệu…"
    assert client.post("/api/tasks", json={"title": "x", "list_id": 1}).status_code == 503
    assert client.get("/api/sync/changes?after=0&wait=0").status_code == 503
    assert client.get("/api/backup/dump").status_code == 503
    assert client.post("/api/backup/jobs", json={"kind": "backup_now"}).status_code == 503


def test_cac_api_van_phuc_vu_khi_dang_khoi_phuc(client, flag):
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/backup/status").status_code == 200
    assert client.put("/api/backup/jobs/1", json={"state": "running"}).status_code != 503
    assert (
        client.put("/api/backup/agent-report", json={"destination_state": "ok"}).status_code == 204
    )


def test_het_bao_tri_thi_binh_thuong(client, flag):
    flag.unlink()
    assert client.get("/api/tasks?view=all").status_code == 200
