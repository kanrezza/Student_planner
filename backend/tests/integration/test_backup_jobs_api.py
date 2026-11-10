"""Việc 'Sao lưu ngay' / 'Khôi phục' giao cho agent (feature 003, T015)."""

from datetime import timedelta

from app.lib import timeutil
from app.models import BackupJob


def create(client, **body):
    return client.post("/api/backup/jobs", json={"kind": "backup_now", **body})


def test_tao_viec_va_changes_bao_co_viec(client):
    assert create(client).status_code == 201
    changes = client.get("/api/sync/changes?after=0&wait=0").get_json()
    assert changes["backup_jobs_pending"] == 1


def test_khong_tao_hai_viec_chong_nhau(client):
    assert create(client).status_code == 201
    resp = create(client)
    assert resp.status_code == 409
    assert resp.get_json()["error"]["code"] == "job_running"
    client.post("/api/backup/jobs/claim")  # chuyển sang running vẫn là việc đang hoạt động
    assert create(client).status_code == 409


def test_claim_chuyen_running_goi_lai_204(client):
    job_id = create(client).get_json()["id"]
    claimed = client.post("/api/backup/jobs/claim")
    assert claimed.status_code == 200
    assert claimed.get_json()["id"] == job_id and claimed.get_json()["state"] == "running"
    assert client.post("/api/backup/jobs/claim").status_code == 204


def test_cap_nhat_viec_done_va_failed(client):
    job_id = create(client).get_json()["id"]
    client.post("/api/backup/jobs/claim")
    resp = client.put(f"/api/backup/jobs/{job_id}", json={"state": "running", "step": "restoring"})
    assert resp.get_json()["step"] == "restoring"
    done = client.put(f"/api/backup/jobs/{job_id}", json={"state": "done", "message": "Xong"})
    assert done.get_json()["state"] == "done" and done.get_json()["finished_at"]
    assert client.put(f"/api/backup/jobs/{job_id}", json={"state": "failed"}).status_code == 409
    assert create(client).status_code == 201  # việc cũ đã xong → tạo được việc mới

    second = client.get("/api/backup/status").get_json()["job"]
    assert second["state"] == "pending"


def test_viec_khoi_phuc_can_duong_dan_tuyet_doi(client):
    assert client.post("/api/backup/jobs", json={"kind": "restore"}).status_code == 400
    bad = client.post(
        "/api/backup/jobs", json={"kind": "restore", "source_path": "ban-sao.lhbackup"}
    )
    assert bad.status_code == 400
    ok = client.post(
        "/api/backup/jobs", json={"kind": "restore", "source_path": "/sao-luu/a.lhbackup"}
    )
    assert ok.status_code == 201 and ok.get_json()["source_path"] == "/sao-luu/a.lhbackup"


def test_viec_treo_qua_30_phut_bi_danh_failed(client, db_session):
    job_id = create(client).get_json()["id"]
    client.post("/api/backup/jobs/claim")
    job = db_session.get(BackupJob, job_id)
    job.created_at = timeutil.now() - timedelta(minutes=45)
    job.started_at = timeutil.now() - timedelta(minutes=40)
    db_session.commit()
    status = client.get("/api/backup/status").get_json()
    assert status["job"]["state"] == "failed"
    assert status["job"]["message"] == "Trình sao lưu không phản hồi"
    assert create(client).status_code == 201


def test_viec_khong_ton_tai(client):
    assert client.put("/api/backup/jobs/99999", json={"state": "done"}).status_code == 404
