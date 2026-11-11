"""Kho nội dung file đính kèm trên đĩa (feature 005, research R4, R8, R9).

Nội dung nằm trong Docker named volume `lichhoc_attachments`, tên file là SHA-256 của nội dung:
`<ATTACHMENTS_DIR>/<2 ký tự đầu>/<sha256>`. Ghi an toàn: luồng upload → file tạm trong `.incoming/`
(vừa ghi vừa băm) → `fsync` → đổi tên vào chỗ → `fsync` thư mục. Module này không đụng CSDL và không
ghi log nội dung file.
"""

from __future__ import annotations

import contextlib
import errno
import hashlib
import os
import re
import time
import unicodedata
import uuid
from collections.abc import Iterable
from pathlib import Path
from typing import BinaryIO

from flask import current_app

CHUNK = 1 << 20
INCOMING = ".incoming"
RESTORE = ".restore"
STALE_SECONDS = 3600  # file tạm/mồ côi chỉ bị dọn khi cũ hơn 1 giờ
SHA_RE = re.compile(r"^[0-9a-f]{64}$")

SAFE_PREVIEW_MIME = {
    "image/png": "image",
    "image/jpeg": "image",
    "image/gif": "image",
    "image/webp": "image",
    "image/heic": "image",
    "image/heif": "image",
    "application/pdf": "pdf",
}
EXECUTABLE_EXTENSIONS = {
    ".app", ".command", ".sh", ".tool", ".exe", ".msi", ".pkg", ".dmg", ".scpt", ".jar", ".bat",
    ".ps1", ".js", ".vbs", ".workflow",
}  # fmt: skip
EXTENSION_MIME = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
    ".webp": "image/webp", ".heic": "image/heic", ".heif": "image/heif", ".pdf": "application/pdf",
    ".svg": "image/svg+xml", ".txt": "text/plain", ".csv": "text/csv", ".json": "application/json",
    ".html": "text/html", ".htm": "text/html", ".zip": "application/zip",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".doc": "application/msword", ".xls": "application/vnd.ms-excel",
    ".ppt": "application/vnd.ms-powerpoint",
}  # fmt: skip
MAGIC = (  # (chữ ký đầu file, MIME)
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
    (b"%PDF-", "application/pdf"),
)
EXECUTABLE_MAGIC = (
    b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf",
    b"\xca\xfe\xba\xbe", b"\x7fELF", b"MZ",
)  # fmt: skip


class FileTooLarge(Exception):
    pass


class DiskFull(Exception):
    pass


def root() -> Path:
    path = Path(current_app.config["ATTACHMENTS_DIR"])
    path.mkdir(parents=True, exist_ok=True)
    return path


def blob_path(sha256: str) -> Path:
    if not SHA_RE.match(sha256):
        raise ValueError("SHA-256 không hợp lệ")
    return root() / sha256[:2] / sha256


def _fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def store_stream(stream: BinaryIO, max_bytes: int) -> tuple[str, int, bytes]:
    """Ghi luồng vào kho; trả (sha256, số byte, 4 KB đầu để nhận dạng loại file).

    Vượt `max_bytes` → `FileTooLarge`; hết chỗ → `DiskFull`; mọi lỗi đều không để lại file tạm.
    """
    incoming = root() / INCOMING
    incoming.mkdir(exist_ok=True)
    temp = incoming / uuid.uuid4().hex
    digest, size, head = hashlib.sha256(), 0, b""
    try:
        with temp.open("wb") as out:
            while chunk := stream.read(CHUNK):
                size += len(chunk)
                if size > max_bytes:
                    raise FileTooLarge
                if len(head) < 4096:
                    head += chunk[: 4096 - len(head)]
                digest.update(chunk)
                out.write(chunk)
            out.flush()
            os.fsync(out.fileno())
        sha = digest.hexdigest()
        target = blob_path(sha)
        if target.exists():
            temp.unlink()  # nội dung trùng: giữ một bản (FR-020)
        else:
            target.parent.mkdir(exist_ok=True)
            os.replace(temp, target)
            _fsync_dir(target.parent)
        return sha, size, head
    except OSError as error:
        temp.unlink(missing_ok=True)
        if error.errno == errno.ENOSPC:
            raise DiskFull from error
        raise
    except BaseException:
        temp.unlink(missing_ok=True)
        raise


def ensure_blob_from(path: Path, sha256: str) -> None:
    """Đặt file nội dung ở `path` vào chỗ chính nếu đang thiếu (khôi phục, chạy chồng)."""
    target = blob_path(sha256)
    if target.exists():
        return
    target.parent.mkdir(exist_ok=True)
    os.replace(path, target)
    _fsync_dir(target.parent)


def open_blob(sha256: str) -> Path:
    path = blob_path(sha256)
    if not path.is_file():
        raise FileNotFoundError(sha256)
    return path


def delete_blob(sha256: str) -> None:
    with contextlib.suppress(FileNotFoundError):
        blob_path(sha256).unlink()


def stored_shas() -> set[str]:
    return {
        f.name
        for d in root().iterdir()
        if d.is_dir() and not d.name.startswith(".")
        for f in d.iterdir()
        if SHA_RE.match(f.name)
    }


def sweep(known_shas: Iterable[str], now: float | None = None) -> int:
    """Dọn file lạ: `.incoming`/`.restore` cũ hơn 1 giờ và file không có dòng CSDL (cũ hơn 1 giờ).

    File vừa đổi tên vào chỗ nhưng dòng CSDL chưa commit có thời gian sửa mới nên không bị xoá.
    """
    now = time.time() if now is None else now
    known, removed = set(known_shas), 0
    for name in (INCOMING, RESTORE):
        base = root() / name
        if not base.exists():
            continue
        for item in base.iterdir():
            if now - item.stat().st_mtime > STALE_SECONDS:
                _remove(item)
                removed += 1
    for sha in stored_shas() - known:
        path = blob_path(sha)
        if now - path.stat().st_mtime > STALE_SECONDS:
            path.unlink(missing_ok=True)
            removed += 1
    return removed


def _remove(path: Path) -> None:
    if path.is_dir():
        import shutil

        shutil.rmtree(path, ignore_errors=True)
    else:
        path.unlink(missing_ok=True)


def detect_mime(name: str, head: bytes) -> str:
    """MIME theo phần mở rộng, nhưng ảnh/PDF phải khớp chữ ký đầu file (R8)."""
    extension = Path(name).suffix.lower()
    claimed = EXTENSION_MIME.get(extension, "application/octet-stream")
    if claimed in SAFE_PREVIEW_MIME:
        if claimed == "image/webp":
            return (
                claimed
                if head[:4] == b"RIFF" and head[8:12] == b"WEBP"
                else "application/octet-stream"
            )
        if claimed in ("image/heic", "image/heif"):
            return claimed if head[4:8] == b"ftyp" else "application/octet-stream"
        sniffed = next((mime for magic, mime in MAGIC if head.startswith(magic)), None)
        accepted = {claimed} | ({"image/jpeg"} if claimed == "image/jpeg" else set())
        return claimed if sniffed in accepted else "application/octet-stream"
    return claimed


def preview_kind(mime_type: str) -> str | None:
    return SAFE_PREVIEW_MIME.get(mime_type)


def is_executable(name: str, head: bytes) -> bool:
    if Path(name).suffix.lower() in EXECUTABLE_EXTENSIONS:
        return True
    return any(head.startswith(magic) for magic in EXECUTABLE_MAGIC) and not head.startswith(
        b"%PDF"
    )


_INVALID_NAME = re.compile(r"[\x00-\x1f\x7f/\\]")


def clean_display_name(name: str) -> str:
    """NFC, bỏ ký tự điều khiển và dấu gạch chéo, cắt còn 255 ký tự; rỗng → "file"."""
    text = _INVALID_NAME.sub("", unicodedata.normalize("NFC", name)).strip()
    return text[:255] or "file"


def unique_display_name(name: str, existing: Iterable[str]) -> str:
    """Thêm " (2)", " (3)"… trước phần mở rộng khi trùng tên (không phân biệt hoa thường)."""
    taken = {e.casefold() for e in existing}
    if name.casefold() not in taken:
        return name
    path = Path(name)
    stem, suffix = (path.stem, path.suffix) if path.suffix else (name, "")
    number = 2
    while f"{stem} ({number}){suffix}".casefold() in taken:
        number += 1
    return f"{stem} ({number}){suffix}"
