"""Sao lưu tự động: lịch, ghi file an toàn, dọn bản cũ, báo cáo cho backend (feature 003, US1).

Quyết định "khi nào sao lưu", "tên file", "dọn bản nào" là các hàm thuần có test
(contracts/agent-backup.md). Phần ghi file chỉ chạm vào thư mục sao lưu và chỉ file khớp mẫu tên của
app (constitution IV, ngoại lệ 2).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time as clock_time
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from pathlib import Path

import requests

from lichhoc_agent import icloud, notify
from lichhoc_agent.state import State

log = logging.getLogger("lichhoc_agent")

KINDS = ("tu-dong", "thu-cong", "truoc-khoi-phuc")
RETRY_AFTER = timedelta(minutes=4)  # thử lại sau thất bại; cộng chu kỳ lặp ≤ 25 s vẫn < 5 phút
PARTIAL_MAX_AGE = timedelta(days=1)
REPORT_EVERY_SECONDS = 60
ICLOUD_DRIVE_PARTS = ("Library", "Mobile Documents", "com~apple~CloudDocs")
DEFAULT_FOLDER_PARTS = ("Lịch Học Cá Nhân", "Sao lưu")

MSG_MISSING = (
    "Không tìm thấy thư mục sao lưu (ổ đĩa có thể đã được tháo). Sẽ thử lại khi ổ được cắm lại."
)
MSG_ICLOUD_OFF = "iCloud Drive chưa bật. Bật iCloud Drive hoặc chọn thư mục khác."
MSG_NO_PERMISSION = (
    "Chưa được cấp quyền ghi vào thư mục sao lưu. Mở Cài đặt hệ thống → Quyền riêng tư & Bảo mật "
    "→ Tệp và thư mục (hoặc Truy cập toàn bộ ổ đĩa), bật cho LichHocAgent."
)
MSG_NOT_WRITABLE = (
    "Không ghi được vào thư mục sao lưu (ổ đĩa đầy hoặc chỉ cho đọc). "
    "Giải phóng dung lượng hoặc chọn thư mục khác."
)
MSG_BAD_CHECKSUM = (
    "Không kiểm tra lại được bản sao lưu vừa ghi (mã kiểm tra không khớp), bản này đã bị bỏ. "
    "Bản sao lưu cũ vẫn còn nguyên."
)

_NAME_PATTERN = re.compile(
    r"^(?P<dot>\.)?LichHoc-(?P<y>\d{4})-(?P<mo>\d{2})-(?P<d>\d{2})-(?P<h>\d{2})(?P<mi>\d{2})"
    r"-(?P<kind>tu-dong|thu-cong|truoc-khoi-phuc)(?:-(?P<seq>\d+))?\.lhbackup(?P<cloud>\.icloud)?$"
)
_PARTIAL_PATTERN = re.compile(r"^\.LichHoc-.*\.lhbackup\.partial$")


# ---- Kiểu dữ liệu ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ParsedName:
    name: str  # tên thật, không có dấu chấm đầu / đuôi .icloud
    kind: str
    created_at: datetime
    seq: int
    cloud_only: bool


@dataclass(frozen=True)
class BackupFile:
    name: str
    path: str
    kind: str
    created_at: datetime
    size: int
    location: str  # "local" | "icloud"
    seq: int = 1


@dataclass(frozen=True)
class Destination:
    path: Path | None
    state: str  # ok | missing | no_permission | icloud_off | not_writable
    message: str | None
    requested: str | None = None  # đường dẫn người dùng chọn (None = mặc định)


@dataclass
class BackupConfig:
    enabled: bool
    schedule_time: time
    destination_path: str | None
    retention_count: int
    enabled_since: datetime  # giờ địa phương, không múi giờ

    @classmethod
    def from_api(cls, data: dict) -> BackupConfig:
        hour, minute = (int(part) for part in data["schedule_time"].split(":")[:2])
        since = datetime.fromisoformat(data["enabled_since"])
        if since.tzinfo is not None:
            since = since.astimezone().replace(tzinfo=None)
        return cls(
            enabled=bool(data["enabled"]),
            schedule_time=time(hour, minute),
            destination_path=data.get("destination_path"),
            retention_count=int(data["retention_count"]),
            enabled_since=since,
        )


@dataclass
class BackupResult:
    ok: bool
    destination: Destination
    error: str | None = None
    size: int | None = None
    file: Path | None = None


# ---- Hàm thuần ------------------------------------------------------------------------------


def backup_due(
    now: datetime,
    schedule_time: time,
    enabled: bool,
    last_success_at: datetime | None,
    last_attempt_at: datetime | None,
) -> bool:
    """Đã đến lúc sao lưu tự động chưa? Lỡ nhiều ngày vẫn chỉ một bản bù (FR-003)."""
    if not enabled:
        return False
    slot = datetime.combine(now.date(), schedule_time)
    if slot > now:
        slot -= timedelta(days=1)  # mốc gần nhất đã qua
    if last_success_at is not None and last_success_at >= slot:
        return False
    if last_attempt_at is not None and timedelta(0) <= now - last_attempt_at < RETRY_AFTER:
        return False
    return True


def parse_backup_name(file_name: str) -> ParsedName | None:
    """Nhận tên file do app tạo (kể cả dạng chỗ giữ chỗ `.Tên.lhbackup.icloud`); file lạ → None."""
    match = _NAME_PATTERN.match(file_name)
    if match is None or bool(match["dot"]) != bool(match["cloud"]):
        return None
    try:
        created_at = datetime(
            int(match["y"]), int(match["mo"]), int(match["d"]), int(match["h"]), int(match["mi"])
        )
    except ValueError:
        return None
    seq = int(match["seq"]) if match["seq"] else 1
    return ParsedName(
        name=_build_name(created_at, match["kind"], seq),
        kind=match["kind"],
        created_at=created_at,
        seq=seq,
        cloud_only=bool(match["cloud"]),
    )


def _build_name(created_at: datetime, kind: str, seq: int = 1) -> str:
    suffix = f"-{seq}" if seq > 1 else ""
    return f"LichHoc-{created_at:%Y-%m-%d-%H%M}-{kind}{suffix}.lhbackup"


def unique_name(existing: set[str], created_at: datetime, kind: str) -> str:
    """Tên chưa dùng: trùng phút thì thêm -2, -3… — không bao giờ ghi đè bản cũ."""
    seq = 1
    while True:
        name = _build_name(created_at, kind, seq)
        if name not in existing and f".{name}.icloud" not in existing:
            return name
        seq += 1


def prune(files: list[BackupFile], keep: int, protect: str | None = None) -> list[BackupFile]:
    """Các bản cần xoá để còn `keep` bản mới nhất; bản `protect` (đang khôi phục) không bị xoá."""
    newest_first = sorted(files, key=lambda f: (f.created_at, f.seq), reverse=True)
    return [f for f in newest_first[keep:] if f.path != protect][::-1]


def to_aware(moment: datetime) -> datetime:
    return moment if moment.tzinfo else moment.astimezone()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


# ---- Thư mục đích và danh sách bản ------------------------------------------------------------


def resolve_destination(
    destination_path: str | None, home: Path | None = None, probe: bool = True
) -> Destination:
    """Thư mục sao lưu dùng được không? Không tự tạo thư mục người dùng chọn (ổ có thể đã tháo)."""
    home = home or Path.home()
    try:
        if destination_path is None:
            icloud_root = home.joinpath(*ICLOUD_DRIVE_PARTS)
            if not icloud_root.is_dir():
                return Destination(None, "icloud_off", MSG_ICLOUD_OFF)
            folder = icloud_root.joinpath(*DEFAULT_FOLDER_PARTS)
            folder.mkdir(parents=True, exist_ok=True)
        else:
            folder = Path(destination_path)
            if not folder.is_dir():
                return Destination(None, "missing", MSG_MISSING, destination_path)
        if probe:
            test_file = folder / f".lichhoc-ghi-thu-{os.getpid()}"
            test_file.write_bytes(b"")
            test_file.unlink()
        return Destination(folder, "ok", None, destination_path)
    except PermissionError:
        return Destination(None, "no_permission", MSG_NO_PERMISSION, destination_path)
    except OSError:
        return Destination(None, "not_writable", MSG_NOT_WRITABLE, destination_path)


def list_backups(folder: Path) -> list[BackupFile]:
    """Các bản sao lưu của app trong thư mục (mới nhất trước); file lạ bị bỏ qua."""
    try:
        entries = list(os.scandir(folder))
    except OSError:
        return []
    files = []
    for entry in entries:
        parsed = parse_backup_name(entry.name)
        if parsed is None:
            continue
        try:
            size = 0 if parsed.cloud_only else entry.stat().st_size
        except OSError:
            continue
        files.append(
            BackupFile(
                name=parsed.name,
                path=str(Path(folder) / parsed.name),
                kind=parsed.kind,
                created_at=parsed.created_at,
                size=size,
                location="icloud" if parsed.cloud_only else "local",
                seq=parsed.seq,
            )
        )
    return sorted(files, key=lambda f: (f.created_at, f.seq), reverse=True)


# ---- Sao lưu --------------------------------------------------------------------------------


def _remove_stale_partials(folder: Path, now: datetime) -> None:
    for entry in os.scandir(folder):
        if not _PARTIAL_PATTERN.match(entry.name):
            continue
        try:
            age = now.timestamp() - entry.stat().st_mtime
            if age > PARTIAL_MAX_AGE.total_seconds():
                os.unlink(entry.path)
                log.info("Đã dọn file sao lưu dở dang cũ: %s", entry.name)
        except OSError:
            pass


def _fsync(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _describe_error(error: Exception) -> str:
    if isinstance(error, requests.RequestException):
        return f"Không lấy được dữ liệu từ ứng dụng ({error}). Hãy kiểm tra OrbStack đang chạy."
    if isinstance(error, PermissionError):
        return MSG_NO_PERMISSION
    if isinstance(error, OSError):
        return MSG_NOT_WRITABLE
    return str(error)


def _record_failure(state: State, now: datetime, destination: Destination, message: str):
    state.backup_last_attempt_at = now.isoformat()
    state.backup_last_attempt_ok = False
    state.backup_last_attempt_error = message
    state.backup_last_attempt_size = None
    log.error("Sao lưu thất bại: %s", message)
    return BackupResult(ok=False, destination=destination, error=message)


def _prune_folder(folder: Path, keep: int, protect: str | None) -> None:
    try:
        for old in prune(list_backups(folder), keep, protect):
            Path(old.path).unlink(missing_ok=True)
            log.info("Đã xoá bản sao lưu cũ: %s", old.name)
    except OSError as e:
        log.warning("Không dọn được bản sao lưu cũ: %s", e)  # không làm hỏng bản vừa tạo


def run_backup(
    kind: str,
    backend,
    state: State,
    config: BackupConfig,
    now: datetime,
    protect: str | None = None,
    home: Path | None = None,
) -> BackupResult:
    """Tạo một bản sao lưu: `.partial` → fsync → đọc lại SHA-256 → đổi tên → dọn bản cũ (R4)."""
    destination = resolve_destination(config.destination_path, home=home)
    if destination.path is None:
        return _record_failure(state, now, destination, destination.message or MSG_MISSING)

    folder = destination.path
    partial = None
    try:
        _remove_stale_partials(folder, now)
        name = unique_name({entry.name for entry in os.scandir(folder)}, now, kind)
        partial = folder / f".{name}.partial"
        _, expected_sha = backend.download_backup(kind, partial)
        _fsync(partial)
        if sha256_file(partial) != expected_sha:
            raise ValueError(MSG_BAD_CHECKSUM)
        size = partial.stat().st_size
        os.replace(partial, folder / name)
    except (requests.RequestException, OSError, ValueError) as error:
        if partial is not None:
            partial.unlink(missing_ok=True)
        return _record_failure(state, now, destination, _describe_error(error))

    state.backup_last_attempt_at = state.backup_last_success_at = now.isoformat()
    state.backup_last_attempt_ok = True
    state.backup_last_attempt_error = None
    state.backup_last_attempt_size = state.backup_last_success_size = size
    log.info("Sao lưu xong: %s (%d byte)", name, size)
    _prune_folder(folder, config.retention_count, protect)
    return BackupResult(ok=True, destination=destination, size=size, file=folder / name)


def build_report(state: State, destination: Destination) -> dict:
    """Nội dung PUT /backup/agent-report (contracts/rest-api.md)."""

    def aware(value: str | None) -> str | None:
        return to_aware(datetime.fromisoformat(value)).isoformat() if value else None

    files = list_backups(destination.path) if destination.path else []
    return {
        "destination_resolved": (
            str(destination.path) if destination.path else destination.requested
        ),
        "destination_state": destination.state,
        "destination_message": destination.message,
        "last_attempt_at": aware(state.backup_last_attempt_at),
        "last_attempt_ok": state.backup_last_attempt_ok,
        "last_attempt_error": state.backup_last_attempt_error,
        "last_attempt_size": state.backup_last_attempt_size,
        "last_success_at": aware(state.backup_last_success_at),
        "last_success_size": state.backup_last_success_size,
        "files": [
            {
                "name": f.name,
                "path": f.path,
                "kind": f.kind,
                "created_at": to_aware(f.created_at).isoformat(),
                "size": f.size,
                "location": f.location,
            }
            for f in files
        ],
    }


# ---- Khôi phục -------------------------------------------------------------------------------

MSG_PRE_BACKUP_FAILED = "Không tạo được bản sao lưu dữ liệu hiện tại nên chưa khôi phục."
MSG_CORRUPT = "Bản sao lưu bị hỏng, không thể khôi phục"
MSG_ICLOUD_DOWNLOAD = "Không tải được bản sao lưu từ iCloud. Hãy kiểm tra mạng rồi thử lại."
MSG_FILE_MISSING = "Không tìm thấy file sao lưu."


def verify_lhbackup(path: Path) -> bool:
    """File `.lhbackup` đọc được và dump khớp SHA-256 trong manifest (không giải nén ra đĩa)."""
    try:
        with zipfile.ZipFile(path) as zf:
            manifest = json.loads(zf.read("manifest.json"))
            digest = hashlib.sha256()
            with zf.open("data.dump") as handle:
                for block in iter(lambda: handle.read(1 << 20), b""):
                    digest.update(block)
        return manifest.get("dump_sha256") == digest.hexdigest()
    except (zipfile.BadZipFile, KeyError, ValueError, OSError):
        return False


def _backend_message(error: requests.RequestException) -> str:
    try:
        return error.response.json()["error"]["message"]
    except (AttributeError, KeyError, ValueError, TypeError):
        return _describe_error(error)


def run_restore(
    job: dict,
    backend,
    state: State,
    config: BackupConfig,
    now: datetime,
    resync: Callable[[], None] = lambda: None,
    ensure_downloaded: Callable[[Path], None] = icloud.ensure_downloaded,
    home: Path | None = None,
) -> tuple[bool, str]:
    """Khôi phục (spec FR-012): sao lưu dữ liệu hiện tại → tải từ iCloud nếu cần → kiểm tra file →
    gửi cho backend → đồng bộ lại Lịch/Lời nhắc. Trả (thành công, thông báo tiếng Việt)."""
    source = Path(job["source_path"])

    def step(name: str) -> None:
        backend.update_job(job["id"], state="running", step=name)
        log.info("Khôi phục: %s", name)

    step("pre_backup")
    safety = run_backup(
        "truoc-khoi-phuc", backend, state, config, now, protect=str(source), home=home
    )
    if not safety.ok:
        return False, MSG_PRE_BACKUP_FAILED
    if icloud.is_cloud_only(source):
        step("downloading")
        try:
            ensure_downloaded(source)
        except (TimeoutError, OSError) as error:
            log.error("Không tải được %s từ iCloud: %s", source.name, error)
            return False, MSG_ICLOUD_DOWNLOAD
    if not source.is_file():
        return False, MSG_FILE_MISSING
    if not verify_lhbackup(source):
        return False, MSG_CORRUPT

    step("restoring")
    try:
        backend.upload_restore(source)
    except requests.HTTPError as error:
        return False, _backend_message(error)
    except requests.RequestException as error:
        return False, _describe_error(error)

    step("resync")
    try:
        resync()
    except Exception:  # noqa: BLE001 — khôi phục đã xong; đồng bộ lại sẽ tự thử ở vòng sau
        log.exception("Khôi phục xong nhưng chưa cập nhật được Lịch/Lời nhắc")
    if safety.destination.path is not None:
        _prune_folder(safety.destination.path, config.retention_count, None)
    parsed = parse_backup_name(source.name)
    if parsed is None:
        return True, "Đã khôi phục dữ liệu"
    return True, f"Đã khôi phục dữ liệu về {parsed.created_at:%H:%M %d/%m/%Y}"


# ---- Điều phối trong vòng lặp của agent ---------------------------------------------------------


def _parse_moment(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


class BackupService:
    """Mỗi vòng lặp gọi `tick`: nhận việc từ giao diện, sao lưu đúng lịch, báo cáo, thông báo."""

    def __init__(
        self,
        backend,
        state: State,
        clock: Callable[[], datetime] = datetime.now,
        send_notice: Callable[[], bool] = notify.send_stale_notice,
        resync: Callable[[], None] = lambda: None,
        send_text: Callable[[str], bool] = notify.send_notice,
    ):
        self.backend = backend
        self.state = state
        self.clock = clock
        self.send_notice = send_notice
        self.send_text = send_text
        self.resync = resync
        self.config: BackupConfig | None = None
        self._config_revision: int | None = None
        self._last_report = 0.0
        self._dirty = True

    def tick(self, changes: dict | None = None) -> None:
        now = self.clock()
        revision = (changes or {}).get("backup_config_revision")
        if self.config is None or revision != self._config_revision:
            self.config = BackupConfig.from_api(self.backend.backup_config())
            self._config_revision = revision
            self._dirty = True
        pending = changes is None or (changes.get("backup_jobs_pending") or 0) > 0
        job = self.backend.claim_job() if pending else None
        if job is not None:
            self._run_job(job, now)
        elif backup_due(
            now,
            self.config.schedule_time,
            self.config.enabled,
            _parse_moment(self.state.backup_last_success_at),
            _parse_moment(self.state.backup_last_attempt_at),
        ):
            result = run_backup("tu-dong", self.backend, self.state, self.config, now)
            self._finish(result)
            if result.ok:
                self._maybe_notify_attachments(now)
        self._maybe_notify(now)
        self._maybe_report()

    def _run_job(self, job: dict, now: datetime) -> None:
        if job["kind"] == "backup_now":
            self.backend.update_job(job["id"], state="running", step="backup")
            result = run_backup("thu-cong", self.backend, self.state, self.config, now)
            self._finish(result)
            if result.ok:
                self.backend.update_job(job["id"], state="done", message="Đã sao lưu xong")
            else:
                self.backend.update_job(job["id"], state="failed", message=result.error)
        else:
            ok, message = run_restore(
                job, self.backend, self.state, self.config, now, resync=self.resync
            )
            self._finish(None)
            self.backend.update_job(job["id"], state="done" if ok else "failed", message=message)

    def _finish(self, result: BackupResult | None) -> None:
        self.state.save()
        self._dirty = True

    def _maybe_notify(self, now: datetime) -> None:
        config = self.config
        last_success = _parse_moment(self.state.backup_last_success_at)
        if notify.stale_notice_due(
            now, last_success, config.enabled_since, self.state.stale_notified_for, config.enabled
        ):
            anchor = notify.stale_anchor(last_success, config.enabled_since)
            if self.send_notice():
                self.state.stale_notified_for = anchor.isoformat()
                self.state.save()

    def _maybe_notify_attachments(self, now: datetime) -> None:
        """Sau sao lưu tự động: file đính kèm vượt ngưỡng thì báo nhẹ, tối đa một lần mỗi ngày."""
        try:
            status = self.backend.backup_status()
        except requests.RequestException:
            return
        today = now.date().isoformat()
        if not notify.attachments_notice_due(
            status.get("attachments_warning", False), self.state.attachments_notified_on, today
        ):
            return
        body = notify.attachments_notice_body(
            status.get("attachments_bytes", 0), status.get("estimated_backup_bytes", 0)
        )
        if self.send_text(body):
            self.state.attachments_notified_on = today
            self.state.save()

    def _maybe_report(self) -> None:
        if not self._dirty and clock_time.monotonic() - self._last_report < REPORT_EVERY_SECONDS:
            return
        destination = resolve_destination(self.config.destination_path, probe=False)
        self.backend.put_backup_report(build_report(self.state, destination))
        self._last_report = clock_time.monotonic()
        self._dirty = False
