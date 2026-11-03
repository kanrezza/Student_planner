"""Vòng lặp chính của LichHocAgent (research R5, contracts/calendar-sync.md).

long-poll `changes` → lấy `feed` → `plan_changes` → ghi vào Lịch/Lời nhắc → `commit` →
báo trạng thái.
Backend không phản hồi thì thử lại sau 30 giây, tăng dần tới 5 phút; KHÔNG xoá mục đã ghi.

Chạy: LichHocAgent.app (do launchd khởi động). `--once`: đồng bộ một lần rồi thoát.
"""

import logging
import sys
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

import requests

from lichhoc_agent.backend_client import BackendClient
from lichhoc_agent.reconcile import plan_changes
from lichhoc_agent.state import State

LOG_PATH = Path.home() / "Library/Logs/LichHocAgent/agent.log"
LONG_POLL_SECONDS = 25
HEARTBEAT_SECONDS = 60  # backend coi agent "không chạy" nếu quá 2 phút không liên lạc
FULL_RESYNC_SECONDS = 6 * 3600  # ghi lại toàn bộ định kỳ để sửa mục bị chỉnh tay trong Lịch
RETRY_START, RETRY_MAX = 30, 300

log = logging.getLogger("lichhoc_agent")


def sync_once(backend, store, state: State, force: bool = False) -> int:
    """Đưa Lịch/Lời nhắc về khớp feed. Trả revision đã đồng bộ."""
    feed = backend.feed()
    revision = feed["revision"]

    if not feed["sync_enabled"]:
        if state.calendar_id or state.reminder_list_id:
            store.remove_containers(state)  # FR-054: tắt đồng bộ thì xoá lịch/danh sách của app
            store.commit()
            log.info("Đã tắt đồng bộ: xoá lịch và danh sách lời nhắc của app")
        state.clear()
        state.last_revision = revision
        state.save()
        backend.put_status(
            permission="unknown",
            icloud_source="unknown",
            last_synced_revision=revision,
            last_error=None,
        )
        return revision

    permission = store.request_access()
    if permission != "granted":
        backend.put_status(
            permission="denied",
            icloud_source="unknown",
            last_synced_revision=state.last_revision,
            last_error="Chưa được cấp quyền Lịch/Lời nhắc",
        )
        return state.last_revision

    current = store.list_items(state)
    plan = plan_changes(feed, current, state.fingerprints, force=force)
    if plan.recreate_containers:
        store.ensure_containers(state)
        state.fingerprints, state.item_keys = {}, {}
    for handle in plan.delete:
        store.delete(handle)
    for handle, kind, item in plan.update:
        store.update(handle, kind, item)
    for kind, item in plan.create:
        state.item_keys[store.create(kind, item, state)] = item["sync_key"]
    store.commit()

    wanted = {i["sync_key"]: i["fingerprint"] for i in feed["events"] + feed["reminders"]}
    state.fingerprints = wanted
    state.item_keys = {k: v for k, v in state.item_keys.items() if v in wanted}
    state.last_revision = revision
    state.save()
    backend.put_status(
        permission="granted",
        icloud_source=store.source_kind(),
        last_synced_revision=revision,
        last_error=None,
    )
    log.info(
        "Đồng bộ revision %s: +%d ~%d -%d",
        revision,
        len(plan.create),
        len(plan.update),
        len(plan.delete),
    )
    return revision


def _setup_logging() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(LOG_PATH, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(handler)
    log.setLevel(logging.INFO)


def run_forever(backend, store, state: State) -> None:
    retry = RETRY_START
    last_full = last_heartbeat = 0.0
    first = True
    while True:
        try:
            changes = backend.changes(
                after=state.last_revision, wait=0 if first else LONG_POLL_SECONDS
            )
            now = time.monotonic()
            force = now - last_full > FULL_RESYNC_SECONDS
            if first or force or changes["revision"] != state.last_revision:
                sync_once(backend, store, state, force=force and not first)
                last_heartbeat = now
                if force:
                    last_full = now
            elif changes["sync_enabled"] and now - last_heartbeat > HEARTBEAT_SECONDS:
                backend.put_status(
                    permission="granted",
                    icloud_source=store.source_kind(),
                    last_synced_revision=state.last_revision,
                    last_error=None,
                )
                last_heartbeat = now
            first, retry = False, RETRY_START
        except requests.RequestException as e:
            log.warning("Chưa kết nối được backend (%s); thử lại sau %ss", e, retry)
            time.sleep(retry)
            retry = min(retry * 2, RETRY_MAX)
        except Exception as e:  # noqa: BLE001 — agent chạy nền, không được dừng hẳn
            log.exception("Lỗi khi đồng bộ")
            try:
                backend.put_status(
                    permission="granted",
                    icloud_source=store.source_kind(),
                    last_synced_revision=state.last_revision,
                    last_error=str(e),
                )
            except requests.RequestException:
                pass
            time.sleep(retry)
            retry = min(retry * 2, RETRY_MAX)


def main() -> None:
    from lichhoc_agent.calendar_store import EventKitStore

    _setup_logging()
    backend, store, state = BackendClient(), EventKitStore(), State.load()
    log.info("LichHocAgent khởi động (state: %s)", state.path)
    if "--once" in sys.argv:
        sync_once(backend, store, state, force=True)
        return
    run_forever(backend, store, state)


if __name__ == "__main__":
    main()
