"""Vòng lặp chính của LichHocAgent (research R5, contracts/calendar-sync.md).

long-poll `changes` → lấy `feed` → `plan_changes` → ghi vào Lịch/Lời nhắc → `commit` →
báo trạng thái.
Backend không phản hồi thì thử lại sau 30 giây, tăng dần tới 5 phút; KHÔNG xoá mục đã ghi.

Từ feature 003 agent còn sao lưu dữ liệu hằng ngày (backup.py) và gửi thông báo macOS (notify.py).
Luồng chính chạy vòng lặp sự kiện Cocoa (để nhận click thông báo); vòng lặp đồng bộ + sao lưu chạy ở
luồng nền (research R10).

Chạy: LichHocAgent.app (do launchd khởi động). `--once`: đồng bộ một lần rồi thoát.
"""

import logging
import sys
import threading
import time
from datetime import date
from logging.handlers import RotatingFileHandler
from pathlib import Path

import requests

from lichhoc_agent import __version__, notify
from lichhoc_agent.backend_client import BackendClient
from lichhoc_agent.backup import BackupService
from lichhoc_agent.reconcile import plan_changes
from lichhoc_agent.state import State

LOG_PATH = Path.home() / "Library/Logs/LichHocAgent/agent.log"
LONG_POLL_SECONDS = 25
HEARTBEAT_SECONDS = 60  # backend coi agent "không chạy" nếu quá 2 phút không liên lạc
FULL_RESYNC_SECONDS = 6 * 3600  # ghi lại toàn bộ định kỳ để sửa mục bị chỉnh tay trong Lịch
RETRY_START, RETRY_MAX = 30, 120  # tối đa 2 phút để sao lưu bù kịp trong 5 phút (spec SC-001)

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

    all_items = feed["events"] + feed["reminders"] + feed.get("digests", [])
    wanted = {i["sync_key"]: i["fingerprint"] for i in all_items}
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


def needs_full_sync(now: float, last_full: float, today: date, last_day: date | None) -> bool:
    """Đồng bộ toàn phần định kỳ, và khi sang ngày mới để cửa sổ bản tóm tắt trượt theo
    (contracts/calendar-sync.md §4)."""
    return today != last_day or now - last_full > FULL_RESYNC_SECONDS


def _setup_logging() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(LOG_PATH, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(handler)
    log.setLevel(logging.INFO)


def run_backup_tick(service: BackupService, changes: dict | None) -> None:
    """Lỗi sao lưu không được làm dừng đồng bộ Lịch; chỉ lỗi kết nối backend được chuyển lên."""
    try:
        service.tick(changes)
    except requests.RequestException:
        raise
    except Exception:  # noqa: BLE001 — agent chạy nền, không được dừng hẳn
        log.exception("Lỗi khi sao lưu")


def run_forever(backend, store, state: State, backup: BackupService | None = None) -> None:
    retry = RETRY_START
    last_full = last_heartbeat = 0.0
    last_day: date | None = None
    first = True
    while True:
        try:
            changes = backend.changes(
                after=state.last_revision, wait=0 if first else LONG_POLL_SECONDS
            )
            now, today = time.monotonic(), date.today()
            force = needs_full_sync(now, last_full, today, last_day)
            if first or force or changes["revision"] != state.last_revision:
                sync_once(backend, store, state, force=force and not first)
                last_heartbeat = now
                if force:
                    last_full, last_day = now, today
            elif changes["sync_enabled"] and now - last_heartbeat > HEARTBEAT_SECONDS:
                backend.put_status(
                    permission="granted",
                    icloud_source=store.source_kind(),
                    last_synced_revision=state.last_revision,
                    last_error=None,
                )
                last_heartbeat = now
            if backup is not None:
                run_backup_tick(backup, None if first else changes)
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


def _run_worker(backend, state: State) -> None:
    from lichhoc_agent.calendar_store import EventKitStore

    run_forever(backend, EventKitStore(), state, BackupService(backend, state))


def _run_cocoa_loop() -> None:
    """Vòng lặp sự kiện ở luồng chính: cần để nhận click vào thông báo macOS."""
    try:
        from PyObjCTools import AppHelper

        AppHelper.runConsoleEventLoop(installInterrupt=True)
    except ImportError:  # chạy ngoài môi trường macOS/PyObjC: chỉ cần giữ tiến trình sống
        while True:
            time.sleep(3600)


def main() -> None:
    _setup_logging()
    backend, state = BackendClient(), State.load()
    log.info("LichHocAgent %s khởi động (state: %s)", __version__, state.path)
    if "--once" in sys.argv:
        from lichhoc_agent.calendar_store import EventKitStore

        sync_once(backend, EventKitStore(), state, force=True)
        return
    notify.install_delegate()
    threading.Thread(target=_run_worker, args=(backend, state), name="dong-bo", daemon=True).start()
    _run_cocoa_loop()


if __name__ == "__main__":
    main()
