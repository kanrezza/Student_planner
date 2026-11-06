"""run_backup: ghi file an toàn, kiểm tra SHA-256, dọn bản cũ (contracts/agent-backup.md, R4)."""

import hashlib
import os
import time
from datetime import datetime
from datetime import time as dtime
from pathlib import Path

import requests

from lichhoc_agent.backup import BackupConfig, build_report, run_backup
from lichhoc_agent.state import State

NOW = datetime(2026, 11, 5, 21, 0, 12)
PAYLOAD = b"PK-du-lieu-sao-luu" * 100


class FakeBackend:
    def __init__(self, payload=PAYLOAD, sha=None, error=None):
        self.payload = payload
        self.sha = sha or hashlib.sha256(payload).hexdigest()
        self.error = error
        self.calls = 0

    def download_backup(self, kind, dest: Path):
        self.calls += 1
        if self.error:
            dest.write_bytes("dở dang".encode())  # đã ghi một phần rồi mới lỗi
            raise self.error
        dest.write_bytes(self.payload)
        return "ten-do-backend-dat.lhbackup", self.sha


def make_config(folder: Path, keep=14) -> BackupConfig:
    return BackupConfig(
        enabled=True,
        schedule_time=dtime(21, 0),
        destination_path=str(folder),
        retention_count=keep,
        enabled_since=datetime(2026, 11, 1),
    )


def make_state(tmp_path: Path) -> State:
    return State(path=tmp_path / "state.json")


def old_backup(folder: Path, day: int) -> Path:
    path = folder / f"LichHoc-2026-11-{day:02d}-2100-tu-dong.lhbackup"
    path.write_bytes(b"cu")
    return path


def test_thanh_cong_ghi_file_ten_that_va_khong_con_partial(tmp_path):
    folder = tmp_path / "Sao lưu"
    folder.mkdir()
    state = make_state(tmp_path)
    result = run_backup("tu-dong", FakeBackend(), state, make_config(folder), NOW)
    assert result.ok and result.error is None
    target = folder / "LichHoc-2026-11-05-2100-tu-dong.lhbackup"
    assert target.read_bytes() == PAYLOAD
    assert result.size == len(PAYLOAD)
    assert [p.name for p in folder.iterdir()] == [target.name]  # không còn .partial
    assert state.backup_last_success_at == NOW.isoformat()
    assert state.backup_last_attempt_ok is True
    assert state.backup_last_success_size == len(PAYLOAD)


def test_sau_khi_thanh_cong_moi_don_ban_cu(tmp_path):
    folder = tmp_path / "Sao lưu"
    folder.mkdir()
    for day in (1, 2, 3):
        old_backup(folder, day)
    (folder / "ghi-chu.txt").write_text("của người dùng")
    run_backup("tu-dong", FakeBackend(), make_state(tmp_path), make_config(folder, keep=3), NOW)
    names = sorted(p.name for p in folder.iterdir())
    assert "LichHoc-2026-11-01-2100-tu-dong.lhbackup" not in names  # cũ nhất bị xoá
    assert "LichHoc-2026-11-02-2100-tu-dong.lhbackup" in names
    assert "LichHoc-2026-11-05-2100-tu-dong.lhbackup" in names
    assert "ghi-chu.txt" in names  # file lạ không bao giờ bị đụng
    assert len(names) == 4  # 3 bản + ghi-chu.txt


def test_ban_duoc_bao_ve_khong_bi_don(tmp_path):
    folder = tmp_path / "Sao lưu"
    folder.mkdir()
    oldest = old_backup(folder, 1)
    old_backup(folder, 2)
    run_backup(
        "truoc-khoi-phuc",
        FakeBackend(),
        make_state(tmp_path),
        make_config(folder, keep=2),
        NOW,
        protect=str(oldest),
    )
    assert oldest.exists()


def test_sha256_sai_khong_co_file_ten_that_va_ban_cu_con(tmp_path):
    folder = tmp_path / "Sao lưu"
    folder.mkdir()
    keep = old_backup(folder, 4)
    state = make_state(tmp_path)
    result = run_backup("tu-dong", FakeBackend(sha="0" * 64), state, make_config(folder), NOW)
    assert not result.ok
    assert [p.name for p in folder.iterdir()] == [keep.name]  # không .partial, bản cũ còn
    assert state.backup_last_attempt_ok is False
    assert "kiểm tra" in state.backup_last_attempt_error
    assert state.backup_last_success_at is None


def test_thu_muc_khong_co_khong_goi_backend_va_khong_nem_loi(tmp_path):
    backend = FakeBackend()
    state = make_state(tmp_path)
    result = run_backup("tu-dong", backend, state, make_config(tmp_path / "SSD-da-thao"), NOW)
    assert not result.ok
    assert backend.calls == 0
    assert result.destination.state == "missing"
    assert state.backup_last_attempt_at == NOW.isoformat()
    assert "Không tìm thấy thư mục sao lưu" in state.backup_last_attempt_error


def test_backend_loi_giua_chung_xoa_partial_va_giu_ban_cu(tmp_path):
    folder = tmp_path / "Sao lưu"
    folder.mkdir()
    keep = old_backup(folder, 4)
    state = make_state(tmp_path)
    backend = FakeBackend(error=requests.ConnectionError("db chưa chạy"))
    result = run_backup("tu-dong", backend, state, make_config(folder), NOW)
    assert not result.ok
    assert [p.name for p in folder.iterdir()] == [keep.name]
    assert state.backup_last_attempt_ok is False


def test_don_partial_cu_hon_1_ngay_giu_partial_moi(tmp_path):
    folder = tmp_path / "Sao lưu"
    folder.mkdir()
    stale = folder / ".LichHoc-2026-11-01-2100-tu-dong.lhbackup.partial"
    fresh = folder / ".LichHoc-2026-11-05-2059-tu-dong.lhbackup.partial"
    stale.write_bytes(b"x")
    fresh.write_bytes(b"x")
    two_days_ago = time.time() - 2 * 86400
    os.utime(stale, (two_days_ago, two_days_ago))
    run_backup("tu-dong", FakeBackend(), make_state(tmp_path), make_config(folder), datetime.now())
    assert not stale.exists()
    assert fresh.exists()


def test_trung_phut_them_hau_to(tmp_path):
    folder = tmp_path / "Sao lưu"
    folder.mkdir()
    run_backup("tu-dong", FakeBackend(), make_state(tmp_path), make_config(folder), NOW)
    run_backup("tu-dong", FakeBackend(), make_state(tmp_path), make_config(folder), NOW)
    assert sorted(p.name for p in folder.iterdir()) == [
        "LichHoc-2026-11-05-2100-tu-dong-2.lhbackup",
        "LichHoc-2026-11-05-2100-tu-dong.lhbackup",
    ]


def test_build_report_co_du_truong(tmp_path):
    folder = tmp_path / "Sao lưu"
    folder.mkdir()
    state = make_state(tmp_path)
    result = run_backup("tu-dong", FakeBackend(), state, make_config(folder), NOW)
    report = build_report(state, result.destination)
    assert report["destination_state"] == "ok"
    assert report["destination_resolved"] == str(folder)
    assert report["last_attempt_ok"] is True
    assert report["last_success_size"] == len(PAYLOAD)
    assert report["last_attempt_at"].startswith("2026-11-05T21:00:12")
    assert report["files"][0]["kind"] == "tu-dong"
    assert report["files"][0]["location"] == "local"
