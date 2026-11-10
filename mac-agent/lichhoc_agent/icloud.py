"""File sao lưu chỉ có trên iCloud (macOS "tối ưu dung lượng"): nhận diện, tải về (R6)."""

from __future__ import annotations

import time
from pathlib import Path

CHECK_EVERY_SECONDS = 2
DOWNLOAD_TIMEOUT_SECONDS = 300


def placeholder_for(path: Path) -> Path:
    """`/a/Tên.lhbackup` → `/a/.Tên.lhbackup.icloud` (chỗ giữ chỗ khi file chưa tải)."""
    return path.with_name(f".{path.name}.icloud")


def is_cloud_only(path: Path) -> bool:
    return not path.exists() and placeholder_for(path).exists()


def ensure_downloaded(
    path: Path,
    timeout: float = DOWNLOAD_TIMEOUT_SECONDS,
    sleep=time.sleep,
    clock=time.monotonic,
) -> None:
    """Yêu cầu macOS tải file về máy rồi chờ tới khi file thật xuất hiện; quá hạn → TimeoutError."""
    if path.exists():
        return
    _start_download(path)
    deadline = clock() + timeout
    while not path.exists():
        if clock() >= deadline:
            raise TimeoutError(f"Quá {int(timeout)} giây chưa tải xong {path.name}")
        sleep(CHECK_EVERY_SECONDS)


def _start_download(path: Path) -> None:
    from Foundation import NSURL, NSFileManager

    url = NSURL.fileURLWithPath_(str(path))
    ok, error = NSFileManager.defaultManager().startDownloadingUbiquitousItemAtURL_error_(url, None)
    if not ok:
        raise OSError(f"Không yêu cầu tải được từ iCloud: {error}")
