"""Gọi API đồng bộ của backend qua localhost (contracts/calendar-sync.md §1–§3)."""

import os
from pathlib import Path

import requests

from lichhoc_agent import __version__

DEFAULT_API = "http://127.0.0.1:8080/api"
TIMEOUT_SECONDS = 35  # long-poll của backend chờ tối đa 25 giây
DUMP_TIMEOUT_SECONDS = 600  # tạo và tải bản sao lưu/khôi phục có thể mất vài chục giây


class BackendClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or os.environ.get("LICHHOC_API", DEFAULT_API)).rstrip("/")
        self.http = requests.Session()

    def changes(self, after: int, wait: int) -> dict:
        resp = self.http.get(
            f"{self.base_url}/sync/changes",
            params={"after": after, "wait": wait},
            timeout=TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        return resp.json()

    def feed(self) -> dict:
        resp = self.http.get(f"{self.base_url}/sync/feed", timeout=TIMEOUT_SECONDS)
        resp.raise_for_status()
        return resp.json()

    def put_status(self, **status) -> None:
        payload = {"agent_version": __version__, **status}
        resp = self.http.put(
            f"{self.base_url}/sync/agent-status", json=payload, timeout=TIMEOUT_SECONDS
        )
        resp.raise_for_status()

    # ---- Sao lưu (feature 003, contracts/rest-api.md) ------------------------------------

    def backup_config(self) -> dict:
        resp = self.http.get(f"{self.base_url}/backup/config", timeout=TIMEOUT_SECONDS)
        resp.raise_for_status()
        return resp.json()

    def claim_job(self) -> dict | None:
        resp = self.http.post(f"{self.base_url}/backup/jobs/claim", timeout=TIMEOUT_SECONDS)
        if resp.status_code == 204:
            return None
        resp.raise_for_status()
        return resp.json()

    def update_job(self, job_id: int, **fields) -> None:
        resp = self.http.put(
            f"{self.base_url}/backup/jobs/{job_id}", json=fields, timeout=TIMEOUT_SECONDS
        )
        resp.raise_for_status()

    def put_backup_report(self, report: dict) -> None:
        resp = self.http.put(
            f"{self.base_url}/backup/agent-report", json=report, timeout=TIMEOUT_SECONDS
        )
        resp.raise_for_status()

    def upload_restore(self, path: Path) -> dict:
        """Gửi file `.lhbackup` lên để khôi phục (nhận thân là chính file, theo từng khối)."""
        with path.open("rb") as handle:
            resp = self.http.post(
                f"{self.base_url}/backup/restore",
                data=handle,
                headers={"Content-Type": "application/zip"},
                timeout=DUMP_TIMEOUT_SECONDS,
            )
        resp.raise_for_status()
        return resp.json()

    def download_backup(self, kind: str, dest: Path) -> tuple[str, str]:
        """Tải bản sao lưu mới tạo vào `dest` (theo khối 1 MB); trả (tên backend đặt, SHA-256)."""
        with self.http.get(
            f"{self.base_url}/backup/dump",
            params={"kind": kind},
            stream=True,
            timeout=DUMP_TIMEOUT_SECONDS,
        ) as resp:
            resp.raise_for_status()
            with dest.open("wb") as handle:
                for block in resp.iter_content(1 << 20):
                    handle.write(block)
            return resp.headers.get("X-Backup-Name", ""), resp.headers["X-Backup-Sha256"]
