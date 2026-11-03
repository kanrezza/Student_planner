"""Đối chiếu feed của backend với các mục đang có trong Lịch/Lời nhắc.

Theo contracts/calendar-sync.md §4.

Hàm thuần, không đụng EventKit: dễ test bằng dữ liệu giả.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Item:
    """Một mục đang có trong lịch/danh sách của app. `key` = None nếu không có URL lichhoc://."""

    key: str | None
    kind: str  # "event" | "reminder"
    handle: Any


@dataclass
class Plan:
    create: list[tuple[str, dict]] = field(default_factory=list)  # (kind, item của feed)
    update: list[tuple[Any, str, dict]] = field(default_factory=list)  # (handle, kind, item)
    delete: list[Any] = field(default_factory=list)  # handle
    remove_all: bool = False
    recreate_containers: bool = False


def _wanted(feed: dict) -> dict[str, tuple[str, dict]]:
    wanted = {e["sync_key"]: ("event", e) for e in feed["events"]}
    wanted.update({r["sync_key"]: ("reminder", r) for r in feed["reminders"]})
    return wanted


def plan_changes(
    feed: dict, current: list[Item] | None, saved_fingerprints: dict[str, str], force: bool = False
) -> Plan:
    """
    - Đồng bộ tắt → xoá toàn bộ lịch và danh sách của app.
    - Lịch/danh sách không còn (`current is None`, ví dụ người dùng đã xoá) → tạo lại và ghi tất cả.
    - Mục thiếu → tạo; `fingerprint` khác lần ghi trước (hoặc `force`) → cập nhật; mục của app không
      còn trong feed → xoá. Mục không có URL lichhoc:// không bao giờ bị đụng tới.
    """
    if not feed["sync_enabled"]:
        return Plan(remove_all=True)
    wanted = _wanted(feed)
    if current is None:
        return Plan(create=list(wanted.values()), recreate_containers=True)

    plan = Plan()
    seen: set[str] = set()
    for item in current:
        if item.key is None:
            continue
        if item.key in seen or item.key not in wanted:
            plan.delete.append(item.handle)  # mục thừa hoặc bản trùng
            continue
        seen.add(item.key)
        kind, data = wanted[item.key]
        if force or saved_fingerprints.get(item.key) != data["fingerprint"]:
            plan.update.append((item.handle, kind, data))
    plan.create = [(kind, data) for key, (kind, data) in wanted.items() if key not in seen]
    return plan
