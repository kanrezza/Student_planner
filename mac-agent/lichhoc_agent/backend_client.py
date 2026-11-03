"""Gọi API đồng bộ của backend qua localhost (contracts/calendar-sync.md §1–§3)."""

import os

import requests

from lichhoc_agent import __version__

DEFAULT_API = "http://127.0.0.1:8080/api"
TIMEOUT_SECONDS = 35  # long-poll của backend chờ tối đa 25 giây


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
