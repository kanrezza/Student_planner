"""GET /api/backup/dump: định dạng .lhbackup (feature 003, research R3/R4, T013)."""

import hashlib
import io
import json
import re
import subprocess
import zipfile

import pytest

from app.services import backup

NAME_PATTERN = re.compile(
    r"^LichHoc-\d{4}-\d{2}-\d{2}-\d{4}-(tu-dong|thu-cong|truoc-khoi-phuc)\.lhbackup$"
)


@pytest.fixture
def dump_response(client):
    resp = client.get("/api/backup/dump?kind=tu-dong")
    assert resp.status_code == 200, resp.get_data(as_text=True)
    return resp


def test_dump_la_zip_co_manifest_va_data_dump(dump_response):
    assert dump_response.mimetype == "application/zip"
    with zipfile.ZipFile(io.BytesIO(dump_response.data)) as zf:
        assert sorted(zf.namelist()) == ["data.dump", "manifest.json"]
        assert all(i.compress_type == zipfile.ZIP_STORED for i in zf.infolist())
        manifest = json.loads(zf.read("manifest.json"))
        dump = zf.read("data.dump")
    assert manifest["format"] == 1
    assert manifest["kind"] == "tu-dong"
    assert manifest["schema_revision"] == backup._head_revision()
    assert manifest["app_version"]
    assert manifest["created_at"].endswith("+07:00")
    assert manifest["dump_size"] == len(dump)
    assert manifest["dump_sha256"] == hashlib.sha256(dump).hexdigest()
    assert set(manifest["counts"]) == {
        "tasks",
        "task_lists",
        "tags",
        "semesters",
        "subjects",
        "class_sessions",
        "exams",
        "shifts",
    }


def test_header_ten_va_sha256(dump_response):
    name = dump_response.headers["X-Backup-Name"]
    assert NAME_PATTERN.match(name), name
    assert (
        dump_response.headers["X-Backup-Sha256"] == hashlib.sha256(dump_response.data).hexdigest()
    )
    assert name in dump_response.headers["Content-Disposition"]


def test_dump_doc_lai_duoc_bang_pg_restore_va_khong_chua_du_lieu_bang_cau_hinh(dump_response):
    with zipfile.ZipFile(io.BytesIO(dump_response.data)) as zf:
        dump = zf.read("data.dump")
    listing = subprocess.run(
        ["pg_restore", "--list"], input=dump, capture_output=True, check=True
    ).stdout.decode()
    assert "TABLE DATA public tasks" in listing
    for table in ("backup_config", "backup_status", "backup_jobs", "agent_status"):
        assert f"TABLE public {table}" in listing  # cấu trúc bảng vẫn có
        assert f"TABLE DATA public {table}" not in listing  # nhưng không có dữ liệu (R9)


@pytest.mark.parametrize("kind", ["thu-cong", "truoc-khoi-phuc"])
def test_cac_loai_ban_hop_le(client, kind):
    resp = client.get(f"/api/backup/dump?kind={kind}")
    assert resp.status_code == 200
    assert f"-{kind}.lhbackup" in resp.headers["X-Backup-Name"]


def test_loai_la_bi_tu_choi(client):
    resp = client.get("/api/backup/dump?kind=khac")
    assert resp.status_code == 400
    assert resp.get_json()["error"]["code"] == "invalid_kind"
