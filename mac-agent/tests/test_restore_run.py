"""run_restore: sao lưu dữ liệu hiện tại → kiểm tra file → gửi cho backend → đồng bộ lại (T042)."""

import hashlib
import io
import json
import zipfile
from datetime import datetime
from datetime import time as dtime
from pathlib import Path

import requests

from lichhoc_agent.backup import BackupConfig, run_restore
from lichhoc_agent.state import State

NOW = datetime(2026, 11, 6, 9, 0, 0)
DUMP = b"PGDMP-gia-lap" * 50


def make_lhbackup(path: Path, corrupt=False) -> Path:
    manifest = {
        "format": 1,
        "dump_sha256": hashlib.sha256(DUMP).hexdigest(),
        "dump_size": len(DUMP),
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.writestr("data.dump", DUMP[:-1] + b"X" if corrupt else DUMP)
    path.write_bytes(buf.getvalue())
    return path


class FakeBackend:
    def __init__(self, tmp_path, restore_error=None):
        self.tmp_path = tmp_path
        self.restore_error = restore_error
        self.steps = []
        self.uploaded = []

    def download_backup(self, kind, dest):
        dest.write_bytes(DUMP)
        return "x", hashlib.sha256(DUMP).hexdigest()

    def update_job(self, job_id, **fields):
        if "step" in fields:
            self.steps.append(fields["step"])

    def upload_restore(self, path):
        self.uploaded.append(path)
        if self.restore_error:
            raise self.restore_error
        return {"restored": True}


def setup(tmp_path, keep=14):
    folder = tmp_path / "Sao lưu"
    folder.mkdir()
    config = BackupConfig(True, dtime(21, 0), str(folder), keep, datetime(2026, 11, 1))
    return folder, config, State(path=tmp_path / "state.json")


def run(tmp_path, source, backend, config, state, **kw):
    resynced = []
    ok, message = run_restore(
        {"id": 1, "source_path": str(source)},
        backend,
        state,
        config,
        NOW,
        resync=lambda: resynced.append(1),
        **kw,
    )
    return ok, message, resynced


def test_thanh_cong_dung_thu_tu_buoc(tmp_path):
    folder, config, state = setup(tmp_path)
    source = make_lhbackup(folder / "LichHoc-2026-11-04-2100-tu-dong.lhbackup")
    backend = FakeBackend(tmp_path)
    ok, message, resynced = run(tmp_path, source, backend, config, state)
    assert ok
    assert message == "Đã khôi phục dữ liệu về 21:00 04/11/2026"
    assert backend.steps == ["pre_backup", "restoring", "resync"]
    assert backend.uploaded == [source]
    assert resynced == [1]
    assert any("truoc-khoi-phuc" in p.name for p in folder.iterdir())  # có bản an toàn


def test_khong_tao_duoc_ban_truoc_khoi_phuc_thi_dung(tmp_path):
    _, config, state = setup(tmp_path)
    config.destination_path = str(tmp_path / "o-da-thao")
    source = make_lhbackup(tmp_path / "LichHoc-2026-11-04-2100-tu-dong.lhbackup")
    backend = FakeBackend(tmp_path)
    ok, message, resynced = run(tmp_path, source, backend, config, state)
    assert not ok
    assert message == "Không tạo được bản sao lưu dữ liệu hiện tại nên chưa khôi phục."
    assert backend.uploaded == [] and resynced == []


def test_file_hong_khong_gui_len_backend(tmp_path):
    folder, config, state = setup(tmp_path)
    source = make_lhbackup(folder / "LichHoc-2026-11-04-2100-tu-dong.lhbackup", corrupt=True)
    backend = FakeBackend(tmp_path)
    ok, message, _ = run(tmp_path, source, backend, config, state)
    assert not ok and message == "Bản sao lưu bị hỏng, không thể khôi phục"
    assert backend.uploaded == []


def test_file_chi_tren_icloud_tai_truoc(tmp_path):
    folder, config, state = setup(tmp_path)
    source = folder / "LichHoc-2026-11-04-2100-tu-dong.lhbackup"
    (folder / ".LichHoc-2026-11-04-2100-tu-dong.lhbackup.icloud").write_bytes(b"")
    backend = FakeBackend(tmp_path)

    def fake_download(path):
        make_lhbackup(path)

    ok, _, _ = run(tmp_path, source, backend, config, state, ensure_downloaded=fake_download)
    assert ok
    assert backend.steps[:2] == ["pre_backup", "downloading"]


def test_tai_icloud_qua_han(tmp_path):
    folder, config, state = setup(tmp_path)
    source = folder / "LichHoc-2026-11-04-2100-tu-dong.lhbackup"
    (folder / ".LichHoc-2026-11-04-2100-tu-dong.lhbackup.icloud").write_bytes(b"")

    def too_slow(_path):
        raise TimeoutError("quá hạn")

    ok, message, _ = run(
        tmp_path, source, FakeBackend(tmp_path), config, state, ensure_downloaded=too_slow
    )
    assert not ok and "iCloud" in message


def test_backend_tu_choi_hien_loi_cua_backend(tmp_path):
    folder, config, state = setup(tmp_path)
    source = make_lhbackup(folder / "LichHoc-2026-11-04-2100-tu-dong.lhbackup")
    response = requests.Response()
    response.status_code = 500
    response._content = json.dumps(
        {"error": {"code": "upgrade_failed", "message": "Không nâng cấp được dữ liệu."}}
    ).encode()
    error = requests.HTTPError(response=response)
    ok, message, resynced = run(tmp_path, source, FakeBackend(tmp_path, error), config, state)
    assert not ok and message == "Không nâng cấp được dữ liệu."
    assert resynced == []


def test_ban_cu_nhat_khong_bi_don_khi_khoi_phuc(tmp_path):
    folder, config, state = setup(tmp_path, keep=2)
    oldest = make_lhbackup(folder / "LichHoc-2026-11-01-2100-tu-dong.lhbackup")
    make_lhbackup(folder / "LichHoc-2026-11-02-2100-tu-dong.lhbackup")
    backend = FakeBackend(tmp_path)

    seen = {}
    original_upload = backend.upload_restore

    def spy(path):
        seen["exists_at_upload"] = path.exists()
        return original_upload(path)

    backend.upload_restore = spy
    ok, _, _ = run(tmp_path, oldest, backend, config, state)
    assert ok and seen["exists_at_upload"]
    # Sau khi khôi phục xong mới dọn: bản thừa (cũ nhất) giờ mới được xoá.
    assert not oldest.exists()
