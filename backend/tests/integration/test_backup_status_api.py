"""Cấu hình, trạng thái và báo cáo của agent (feature 003, T014)."""

from datetime import timedelta

from app.extensions import db
from app.lib import timeutil
from app.models import BackupConfig, BackupStatus
from app.services import sync_feed


def report(**overrides) -> dict:
    now = timeutil.now()
    body = {
        "destination_resolved": "/Users/x/Library/Mobile Documents/com~apple~CloudDocs/Lịch Học Cá Nhân/Sao lưu",
        "destination_state": "ok",
        "destination_message": None,
        "last_attempt_at": timeutil.iso(now),
        "last_attempt_ok": True,
        "last_attempt_error": None,
        "last_attempt_size": 2516582,
        "last_success_at": timeutil.iso(now),
        "last_success_size": 2516582,
        "files": [
            {
                "name": "LichHoc-2026-11-05-2100-tu-dong.lhbackup",
                "path": "/sao-luu/LichHoc-2026-11-05-2100-tu-dong.lhbackup",
                "kind": "tu-dong",
                "created_at": "2026-11-05T21:00:00+07:00",
                "size": 2516582,
                "location": "local",
            }
        ],
    }
    return {**body, **overrides}


def test_mac_dinh(client):
    body = client.get("/api/backup/status").get_json()
    assert body["config"] == {
        "enabled": True,
        "schedule_time": "21:00",
        "destination_path": None,
        "destination_display": "iCloud Drive › Lịch Học Cá Nhân › Sao lưu",
        "retention_count": 14,
        "enabled_since": body["config"]["enabled_since"],
    }
    assert body["agent_online"] is False
    assert body["last_success"] is None
    assert body["files"] == []
    assert body["job"] is None
    assert body["stale"] is False  # vừa bật, chưa quá 3 ngày


def test_patch_cau_hinh(client):
    resp = client.patch(
        "/api/backup/config",
        json={
            "schedule_time": "22:30",
            "retention_count": 7,
            "destination_path": "/Volumes/SSD/Sao lưu",
        },
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["schedule_time"] == "22:30"
    assert body["retention_count"] == 7
    assert body["destination_display"] == "SSD › Sao lưu"
    # null = quay về thư mục mặc định
    again = client.patch("/api/backup/config", json={"destination_path": None}).get_json()
    assert again["destination_path"] is None
    assert again["retention_count"] == 7


def test_patch_gia_tri_khong_hop_le(client):
    for body, field in [
        ({"retention_count": 0}, "retention_count"),
        ({"retention_count": 366}, "retention_count"),
        ({"schedule_time": "25:00"}, "schedule_time"),
        ({"destination_path": "Sao lưu"}, "destination_path"),
    ]:
        resp = client.patch("/api/backup/config", json=body)
        assert resp.status_code == 400, body
        assert field in resp.get_json()["error"]["fields"]
    resp = client.patch("/api/backup/config", json={"destination_path": "Sao lưu"})
    assert resp.get_json()["error"]["fields"]["destination_path"] == (
        "Đường dẫn thư mục phải là đường dẫn đầy đủ"
    )


def test_patch_tang_revision_dong_bo(client):
    before = sync_feed.current_revision()
    client.patch("/api/backup/config", json={"retention_count": 10})
    assert sync_feed.current_revision() == before + 1


def test_changes_co_revision_cau_hinh_va_so_viec(client):
    first = client.get("/api/sync/changes?after=999999&wait=0").get_json()
    assert first["backup_jobs_pending"] == 0
    client.patch("/api/backup/config", json={"retention_count": 9})
    second = client.get("/api/sync/changes?after=999999&wait=0").get_json()
    assert second["backup_config_revision"] > first["backup_config_revision"]


def test_agent_report_cap_nhat_trang_thai_va_danh_sach(client):
    assert client.put("/api/backup/agent-report", json=report()).status_code == 204
    body = client.get("/api/backup/status").get_json()
    assert body["agent_online"] is True
    assert body["destination"]["state"] == "ok"
    assert body["last_attempt"]["ok"] is True and body["last_attempt"]["size"] == 2516582
    assert body["last_success"]["size"] == 2516582
    assert body["files"][0]["name"].endswith("tu-dong.lhbackup")
    assert body["files"][0]["created_at"] == "2026-11-05T21:00:00+07:00"


def test_agent_report_that_bai_van_giu_lan_thanh_cong(client):
    client.put("/api/backup/agent-report", json=report())
    client.put(
        "/api/backup/agent-report",
        json=report(
            last_attempt_ok=False,
            last_attempt_error="Ổ đầy",
            destination_state="missing",
            destination_message="Không tìm thấy thư mục sao lưu",
        ),
    )
    body = client.get("/api/backup/status").get_json()
    assert body["last_attempt"]["ok"] is False
    assert body["last_attempt"]["error"] == "Ổ đầy"
    assert body["destination"]["state"] == "missing"
    assert body["last_success"] is not None  # lần thành công gần nhất vẫn hiện riêng


def test_agent_report_sai_dinh_dang(client):
    assert (
        client.put("/api/backup/agent-report", json=report(destination_state="la")).status_code
        == 400
    )
    assert (
        client.put("/api/backup/agent-report", json=report(files=[{"name": "x"}])).status_code
        == 400
    )


def test_agent_offline_khi_qua_2_phut(client, db_session):
    client.put("/api/backup/agent-report", json=report())
    status = db_session.get(BackupStatus, 1)
    status.reported_at = timeutil.now() - timedelta(minutes=3)
    db_session.commit()
    assert client.get("/api/backup/status").get_json()["agent_online"] is False


def test_stale_khi_qua_3_ngay_khong_co_ban_thanh_cong(client, db_session):
    config = db_session.get(BackupConfig, 1)
    config.enabled_since = timeutil.now() - timedelta(days=4)
    db_session.commit()
    assert client.get("/api/backup/status").get_json()["stale"] is True
    status = db_session.get(BackupStatus, 1)
    status.last_success_at = timeutil.now() - timedelta(days=1)
    db_session.commit()
    assert client.get("/api/backup/status").get_json()["stale"] is False
    status.last_success_at = timeutil.now() - timedelta(days=3, hours=1)
    db_session.commit()
    assert client.get("/api/backup/status").get_json()["stale"] is True
    config.enabled = False
    db_session.commit()
    assert client.get("/api/backup/status").get_json()["stale"] is False


def test_bat_lai_dat_lai_moc_enabled_since(client, db_session):
    config = db_session.get(BackupConfig, 1)
    config.enabled_since = timeutil.now() - timedelta(days=10)
    config.enabled = False
    db_session.commit()
    client.patch("/api/backup/config", json={"enabled": True})
    db.session.refresh(config)
    assert timeutil.now() - config.enabled_since < timedelta(minutes=1)
