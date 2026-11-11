"""Tạo và khôi phục bản sao lưu toàn bộ dữ liệu bằng pg_dump / pg_restore (feature 003).

Định dạng `.lhbackup` (research R3): file ZIP không nén gồm `manifest.json`, `data.dump`
(`pg_dump -Fc`) và, từ format 2 (feature 005), `attachments/<sha256>` cho mỗi file đính kèm.
Khôi phục (research R8) chạy ở chế độ bảo trì, `pg_restore --single-transaction`
nên hoặc thành công hoàn toàn hoặc dữ liệu hiện tại giữ nguyên; nâng cấp schema của bản cũ lỗi thì
tự đưa dữ liệu về lúc trước khi khôi phục. Chỉ chạm vào localhost (constitution IV).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import subprocess
import tempfile
import uuid
import zipfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import sqlalchemy as sa
from alembic.script import ScriptDirectory
from flask import current_app
from flask_migrate import upgrade as upgrade_database

from app.api.errors import ApiError
from app.config import APP_VERSION
from app.extensions import db
from app.lib import timeutil
from app.services import attachments_store

log = logging.getLogger(__name__)

KINDS = ("tu-dong", "thu-cong", "truoc-khoi-phuc")
MANIFEST_FORMAT = 2  # 2: thêm attachments/<sha256> (feature 005); vẫn đọc được format 1
SUPPORTED_FORMATS = (1, 2)
MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"
DEFAULT_FLAG_PATH = "/tmp/lichhoc-restoring"  # noqa: S108 — cờ nội bộ trong container

# Khôi phục bản cũ không được đổi cấu hình/trạng thái sao lưu hay xoá việc đang chạy (research R9).
PRESERVED_TABLES = ("backup_config", "backup_status", "backup_jobs", "agent_status")
COUNTED_TABLES = (
    "tasks",
    "task_lists",
    "tags",
    "semesters",
    "subjects",
    "class_sessions",
    "exams",
    "shifts",
)


class BackupError(ApiError):
    """Lỗi sao lưu/khôi phục; được trả nguyên cho giao diện theo định dạng lỗi chung của API."""


@dataclass
class BuiltBackup:
    path: Path
    name: str
    sha256: str
    size: int
    workdir: Path

    def cleanup(self) -> None:
        shutil.rmtree(self.workdir, ignore_errors=True)


# ---- Chế độ bảo trì -------------------------------------------------------------------------


def _flag_path() -> Path:
    return Path(current_app.config.get("RESTORE_FLAG_PATH", DEFAULT_FLAG_PATH))


def is_restoring() -> bool:
    return _flag_path().exists()


@contextmanager
def maintenance_mode():
    flag = _flag_path()
    flag.write_text(str(os.getpid()))
    try:
        yield
    finally:
        flag.unlink(missing_ok=True)


def clear_stale_maintenance_flag() -> None:
    """Backend vừa khởi động thì không thể đang khôi phục: gỡ cờ còn sót sau sự cố."""
    _flag_path().unlink(missing_ok=True)


# ---- pg_dump / pg_restore -------------------------------------------------------------------


def _connection_args() -> tuple[list[str], dict[str, str]]:
    url = db.engine.url
    args = [
        "-h",
        url.host or "localhost",
        "-p",
        str(url.port or 5432),
        "-U",
        url.username or "lichhoc",
        "-d",
        url.database or "lichhoc",
    ]
    return args, {**os.environ, "PGPASSWORD": url.password or ""}


def _run(command: list[str], env: dict[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, env=env, capture_output=True, text=True, check=False)


def _dump_to(path: Path) -> None:
    args, env = _connection_args()
    exclude = [f"--exclude-table-data={table}" for table in PRESERVED_TABLES]
    result = _run(["pg_dump", "-Fc", "--no-owner", *exclude, *args, "-f", str(path)], env)
    if result.returncode != 0:
        log.error("pg_dump lỗi: %s", result.stderr.strip())
        raise BackupError(
            500, "dump_failed", "Không tạo được bản sao lưu. Hãy thử lại sau ít phút."
        )
    check = _run(["pg_restore", "--list", str(path)], env)
    if check.returncode != 0:
        log.error("pg_restore --list lỗi: %s", check.stderr.strip())
        raise BackupError(500, "dump_failed", "Bản sao lưu vừa tạo không đọc lại được.")


def _data_tables() -> list[str]:
    """Mọi bảng dữ liệu hiện có, trừ `PRESERVED_TABLES` (dữ liệu của chúng đã đọc vào bộ nhớ)."""
    db.session.remove()
    with db.engine.connect() as conn:
        names = conn.scalars(sa.text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
        return [name for name in names.all() if name not in PRESERVED_TABLES]


def _restore_dump(path: Path) -> None:
    """Nạp một dump, thay thế toàn bộ bảng dữ liệu, trong MỘT giao dịch: lỗi thì dữ liệu cũ còn
    nguyên.

    `pg_restore --clean` chỉ xoá được đúng các bảng/ràng buộc mà dump biết. Bản sao lưu cũ không
    biết bảng của migration mới hơn (vd. `subject_schedules` trỏ khoá ngoại vào `subjects`) và
    schema hiện có có thể khác schema trong dump, nên xoá từng phần sẽ lỗi "cannot drop … because
    other objects depend on it". Vì vậy ghép `DROP TABLE … CASCADE` cho mọi bảng dữ liệu vào đầu
    đúng kịch bản SQL mà `pg_restore` xuất ra, rồi chạy tất cả bằng `psql --single-transaction`.
    """
    args, env = _connection_args()
    script = _run(["pg_restore", "--clean", "--if-exists", "--no-owner", "-f", "-", str(path)], env)
    if script.returncode != 0:
        log.error("pg_restore lỗi: %s", script.stderr.strip())
        raise BackupError(
            500, "restore_failed", "Không khôi phục được dữ liệu. Dữ liệu hiện tại giữ nguyên."
        )
    drops = "".join(f'DROP TABLE IF EXISTS "{name}" CASCADE;\n' for name in _data_tables())
    result = subprocess.run(
        ["psql", *args, "--single-transaction", "--quiet", "-v", "ON_ERROR_STOP=1"],
        input=drops + script.stdout,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        log.error("nạp dữ liệu lỗi: %s", result.stderr.strip())
        raise BackupError(
            500, "restore_failed", "Không khôi phục được dữ liệu. Dữ liệu hiện tại giữ nguyên."
        )


# ---- Tạo bản sao lưu ------------------------------------------------------------------------


def backup_name(created_at: datetime, kind: str) -> str:
    return f"LichHoc-{created_at:%Y-%m-%d-%H%M}-{kind}.lhbackup"


def _schema_revision() -> str:
    return db.session.scalar(sa.text("SELECT version_num FROM alembic_version"))


def _counts() -> dict[str, int]:
    return {
        table: db.session.scalar(sa.text(f"SELECT count(*) FROM {table}"))  # noqa: S608
        for table in COUNTED_TABLES
    }


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _attachment_blobs() -> list[tuple[str, int]]:
    """Mọi nội dung file đính kèm đang có (kể cả của task trong Thùng rác) kèm dung lượng."""
    if db.session.scalar(sa.text("SELECT to_regclass('public.attachment_blobs')")) is None:
        return []  # database ở revision cũ (trước migration 0012) chưa có bảng này
    rows = db.session.execute(sa.text("SELECT sha256, size FROM attachment_blobs ORDER BY sha256"))
    present = []
    for sha, size in rows:
        if attachments_store.blob_path(sha).is_file():
            present.append((sha, size))
        else:
            log.warning("File đính kèm %s thiếu trong kho, bỏ qua khi sao lưu", sha[:8])
    return present


def build_backup(kind: str, now: datetime | None = None) -> BuiltBackup:
    if kind not in KINDS:
        raise BackupError(400, "invalid_kind", "Loại bản sao lưu không hợp lệ")
    now = now or timeutil.now()
    workdir = Path(tempfile.mkdtemp(prefix="lichhoc-backup-"))
    try:
        dump_path = workdir / "data.dump"
        _dump_to(dump_path)
        manifest = {
            "format": MANIFEST_FORMAT,
            "created_at": timeutil.iso(now),
            "kind": kind,
            "schema_revision": _schema_revision(),
            "app_version": APP_VERSION,
            "dump_sha256": _file_sha256(dump_path),
            "dump_size": dump_path.stat().st_size,
            "counts": _counts(),
        }
        name = backup_name(now, kind)
        archive = workdir / name
        blobs = _attachment_blobs()
        manifest["attachments"] = {"count": len(blobs), "bytes": sum(size for _, size in blobs)}
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_STORED) as zf:
            zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
            zf.write(dump_path, "data.dump")
            for sha, _size in blobs:
                zf.write(attachments_store.blob_path(sha), f"attachments/{sha}")
        dump_path.unlink()
        return BuiltBackup(archive, name, _file_sha256(archive), archive.stat().st_size, workdir)
    except Exception:
        shutil.rmtree(workdir, ignore_errors=True)
        raise


# ---- Khôi phục ------------------------------------------------------------------------------

_CORRUPT = BackupError(400, "backup_corrupt", "Bản sao lưu bị hỏng, không thể khôi phục")


def _open_backup(archive: Path, workdir: Path) -> tuple[dict, Path]:
    """Kiểm tra file `.lhbackup`, giải nén dump ra `workdir`; trả (manifest, đường dẫn dump).

    File đính kèm (format 2) được kiểm tra và giải nén riêng bởi `_stage_attachments`.
    """
    try:
        with zipfile.ZipFile(archive) as zf:
            manifest = json.loads(zf.read("manifest.json"))
            dump_path = workdir / "restore.dump"
            with zf.open("data.dump") as src, dump_path.open("wb") as dst:
                shutil.copyfileobj(src, dst, 1 << 20)
    except (zipfile.BadZipFile, KeyError, ValueError, OSError) as error:
        log.warning("Bản sao lưu không đọc được: %s", error)
        raise _CORRUPT from error
    if (
        not isinstance(manifest, dict)
        or manifest.get("format") not in SUPPORTED_FORMATS
        or manifest.get("dump_sha256") != _file_sha256(dump_path)
        or manifest.get("dump_size") != dump_path.stat().st_size
    ):
        raise _CORRUPT
    _, env = _connection_args()
    if _run(["pg_restore", "--list", str(dump_path)], env).returncode != 0:
        raise _CORRUPT
    return manifest, dump_path


def _stage_attachments(archive: Path, manifest: dict, staging: Path) -> dict[str, Path]:
    """Giải nén `attachments/<sha256>` vào `staging` (cùng ổ đĩa với kho để đổi tên nhanh) và kiểm
    tra SHA-256 từng file trước khi đụng tới dữ liệu hiện tại. Bản format 1 không có file."""
    expected = manifest.get("attachments") or {"count": 0, "bytes": 0}
    staged: dict[str, Path] = {}
    try:
        with zipfile.ZipFile(archive) as zf:
            names = [n for n in zf.namelist() if n.startswith("attachments/")]
            for name in names:
                sha = name.removeprefix("attachments/")
                if not attachments_store.SHA_RE.match(sha):
                    raise _CORRUPT
                target = staging / sha
                digest = hashlib.sha256()
                with zf.open(name) as src, target.open("wb") as dst:
                    for block in iter(lambda: src.read(1 << 20), b""):
                        digest.update(block)
                        dst.write(block)
                if digest.hexdigest() != sha:
                    raise _CORRUPT
                staged[sha] = target
    except (zipfile.BadZipFile, OSError) as error:
        log.warning("File đính kèm trong bản sao lưu không đọc được: %s", error)
        raise _CORRUPT from error
    total = sum(path.stat().st_size for path in staged.values())
    if expected.get("count") != len(staged) or expected.get("bytes") != total:
        raise _CORRUPT
    return staged


def _known_revision(revision: str) -> bool:
    try:
        return ScriptDirectory(str(MIGRATIONS_DIR)).get_revision(revision) is not None
    except Exception:  # noqa: BLE001 — alembic ném nhiều loại lỗi cho revision lạ
        return False


def _head_revision() -> str:
    return ScriptDirectory(str(MIGRATIONS_DIR)).get_current_head()


def _upgrade_database() -> None:
    upgrade_database(directory=str(MIGRATIONS_DIR))


def _table(name: str) -> sa.Table:
    return sa.Table(name, sa.MetaData(), autoload_with=db.engine)


def _read_preserved() -> dict[str, list[dict]]:
    return {
        name: [dict(row) for row in db.session.execute(sa.select(_table(name))).mappings()]
        for name in PRESERVED_TABLES
    }


def _write_preserved(preserved: dict[str, list[dict]], previous_revision: int) -> None:
    with db.engine.begin() as conn:
        for name, rows in preserved.items():
            table = _table(name)
            conn.execute(sa.delete(table))
            if rows:
                conn.execute(sa.insert(table), rows)
        conn.execute(
            sa.text(
                "SELECT setval(pg_get_serial_sequence('backup_jobs', 'id'), "
                "GREATEST((SELECT COALESCE(MAX(id), 0) FROM backup_jobs), 1))"
            )
        )
        restored = conn.scalar(sa.text("SELECT revision FROM sync_state WHERE id = 1"))
        conn.execute(
            sa.text("UPDATE sync_state SET revision = :revision WHERE id = 1"),
            {"revision": max(previous_revision, restored or 0) + 1},
        )


def _sync_revision() -> int:
    return db.session.scalar(sa.text("SELECT revision FROM sync_state WHERE id = 1")) or 0


def restore_backup(archive: Path) -> dict:
    """Khôi phục từ file `.lhbackup` đã nằm trên đĩa của container (research R8)."""
    workdir = Path(tempfile.mkdtemp(prefix="lichhoc-restore-"))
    staging = attachments_store.root() / attachments_store.RESTORE / uuid.uuid4().hex
    try:
        manifest, dump_path = _open_backup(archive, workdir)
        staging.mkdir(parents=True)
        staged = _stage_attachments(archive, manifest, staging)
        revision = manifest.get("schema_revision")
        if not isinstance(revision, str) or not _known_revision(revision):
            raise BackupError(
                409,
                "backup_too_new",
                "Bản sao lưu được tạo bởi phiên bản app mới hơn. Hãy cập nhật app rồi thử lại.",
            )
        with maintenance_mode():
            return _restore_in_maintenance(workdir, dump_path, revision, staged)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
        shutil.rmtree(staging, ignore_errors=True)


def _restore_in_maintenance(
    workdir: Path, dump_path: Path, revision: str, staged: dict[str, Path]
) -> dict:
    safety = workdir / "safety.dump"
    _dump_to(safety)  # lưới an toàn nội bộ, ngoài bản "Trước khi khôi phục" của agent
    preserved = _read_preserved()
    previous_revision = _sync_revision()
    db.session.remove()
    db.engine.dispose()

    _restore_dump(dump_path)  # lỗi → giao dịch bị huỷ, dữ liệu cũ còn nguyên
    try:
        upgraded = revision != _head_revision()
        if upgraded:
            _upgrade_database()
        _write_preserved(preserved, previous_revision)
        for (
            sha,
            path,
        ) in staged.items():  # chuyển file vào kho; blob cũ chưa bị xoá nên lỗi vẫn an toàn
            attachments_store.ensure_blob_from(path, sha)
    except Exception as error:  # noqa: BLE001 — mọi lỗi sau khi đã thay dữ liệu đều phải hoàn tác
        log.exception("Khôi phục lỗi sau khi nạp dữ liệu, đang đưa về như cũ")
        db.session.remove()
        db.engine.dispose()
        try:
            _restore_dump(safety)
            _write_preserved(preserved, previous_revision)
        except Exception as rollback_error:  # noqa: BLE001
            log.exception("Không hoàn tác được")
            raise BackupError(
                500,
                "restore_failed",
                'Khôi phục gặp lỗi nặng. Hãy khôi phục bằng bản "Trước khi khôi phục" mới nhất.',
            ) from rollback_error
        raise BackupError(
            500,
            "upgrade_failed",
            "Không nâng cấp được dữ liệu của bản sao lưu cũ; "
            "dữ liệu đã được đưa về như trước khi khôi phục.",
        ) from error
    log.info("Đã khôi phục dữ liệu (nâng cấp schema: %s)", upgraded)
    return {"schema_upgraded": upgraded, "restored_schema_revision": revision}
