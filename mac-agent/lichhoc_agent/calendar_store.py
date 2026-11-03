"""Nơi lưu sự kiện/lời nhắc: `EventKitStore` (Lịch và Lời nhắc thật của macOS, qua PyObjC) và
`FakeCalendarStore` (bộ nhớ, cho test). Cả hai có cùng giao diện `CalendarStore`.

Chỉ thao tác trên đúng lịch và danh sách lời nhắc do app tạo (ID lưu trong state.json) — FR-052.
"""

from __future__ import annotations

import itertools
import time
from datetime import datetime, timedelta
from typing import Any, Protocol

from lichhoc_agent.reconcile import Item
from lichhoc_agent.state import State

CONTAINER_NAME = "Lịch Học Cá Nhân"
URL_PREFIX = "lichhoc://"


def key_from_url(url: str | None) -> str | None:
    """ "lichhoc://session/12" → "session:12"."""
    if not url or not url.startswith(URL_PREFIX):
        return None
    kind, _, ident = url[len(URL_PREFIX) :].partition("/")
    return f"{kind}:{ident}" if kind and ident else None


def url_from_key(key: str) -> str:
    kind, _, ident = key.partition(":")
    return f"{URL_PREFIX}{kind}/{ident}"


class CalendarStore(Protocol):
    def request_access(self) -> str: ...  # "granted" | "denied"
    def source_kind(self) -> str: ...  # "icloud" | "local_only" | "unknown"
    def ensure_containers(self, state: State) -> None: ...
    def list_items(self, state: State) -> list[Item] | None: ...
    def create(self, kind: str, item: dict, state: State) -> str: ...  # trả identifier
    def update(self, handle: Any, kind: str, item: dict) -> None: ...
    def delete(self, handle: Any) -> None: ...
    def remove_containers(self, state: State) -> None: ...
    def commit(self) -> None: ...


# ---- Bản giả cho test -----------------------------------------------------------------------


class FakeCalendarStore:
    def __init__(self, permission: str = "granted"):
        self.permission = permission
        self.items: dict[str, dict] = {}  # identifier → item của feed (kèm "kind")
        self._containers: set[str] = set()
        self._ids = itertools.count(1)

    def request_access(self) -> str:
        return self.permission

    def source_kind(self) -> str:
        return "icloud"

    def containers_exist(self, state: State) -> bool:
        return {state.calendar_id, state.reminder_list_id} <= self._containers and bool(
            state.calendar_id
        )

    def ensure_containers(self, state: State) -> None:
        state.calendar_id, state.reminder_list_id = (
            f"cal-{next(self._ids)}",
            f"rem-{next(self._ids)}",
        )
        self._containers |= {state.calendar_id, state.reminder_list_id}

    def list_items(self, state: State) -> list[Item] | None:
        if not self.containers_exist(state):
            return None
        return [
            Item(key=item["sync_key"], kind=item["kind"], handle=ident)
            for ident, item in self.items.items()
        ]

    def create(self, kind: str, item: dict, state: State) -> str:
        ident = f"item-{next(self._ids)}"
        self.items[ident] = {**item, "kind": kind}
        return ident

    def update(self, handle: Any, kind: str, item: dict) -> None:
        self.items[handle] = {**item, "kind": kind}

    def delete(self, handle: Any) -> None:
        self.items.pop(handle, None)

    def remove_containers(self, state: State) -> None:
        self._containers.clear()
        self.items.clear()

    def commit(self) -> None:
        pass

    def user_deletes_containers(self) -> None:
        """Giả lập người dùng tự xoá lịch "Lịch Học Cá Nhân" trong ứng dụng Lịch."""
        self.remove_containers(State())


# ---- EventKit thật (macOS) --------------------------------------------------------------------


def _ns_date(iso: str):
    from Foundation import NSDate

    return NSDate.dateWithTimeIntervalSince1970_(datetime.fromisoformat(iso).timestamp())


class EventKitStore:
    """Ghi vào Lịch/Lời nhắc qua PyObjC (research R4).

    Phải chạy trong LichHocAgent.app (có Info.plist khai báo quyền).
    """

    ACCESS_TIMEOUT_SECONDS = 120  # chờ người dùng bấm "Cho phép"

    def __init__(self):
        import EventKit

        self.ek = EventKit
        self.store = EventKit.EKEventStore.alloc().init()
        self._source_kind = "unknown"

    # -- tiện ích chờ callback bất đồng bộ của EventKit
    def _wait(self, flag: dict, timeout: float) -> None:
        from Foundation import NSDate, NSRunLoop

        deadline = time.time() + timeout
        while not flag.get("done") and time.time() < deadline:
            NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.2))

    def _request(self, entity: str) -> bool:
        flag: dict = {}

        def handler(granted, _error):
            flag.update(done=True, granted=bool(granted))

        if entity == "events":
            self.store.requestFullAccessToEventsWithCompletion_(handler)
        else:
            self.store.requestFullAccessToRemindersWithCompletion_(handler)
        self._wait(flag, self.ACCESS_TIMEOUT_SECONDS)
        return flag.get("granted", False)

    def request_access(self) -> str:
        ek = self.ek
        full = getattr(ek, "EKAuthorizationStatusFullAccess", 3)
        statuses = [
            ek.EKEventStore.authorizationStatusForEntityType_(ek.EKEntityTypeEvent),
            ek.EKEventStore.authorizationStatusForEntityType_(ek.EKEntityTypeReminder),
        ]
        if all(s == full for s in statuses):
            return "granted"
        granted = self._request("events") and self._request("reminders")
        if granted:
            self.store = ek.EKEventStore.alloc().init()  # nạp lại nguồn sau khi được cấp quyền
        return "granted" if granted else "denied"

    def source_kind(self) -> str:
        return self._source_kind

    def _event_source(self):
        ek = self.ek
        for source in self.store.sources():
            if source.sourceType() == ek.EKSourceTypeCalDAV and source.title() == "iCloud":
                self._source_kind = "icloud"
                return source
        for source in self.store.sources():
            if source.sourceType() == ek.EKSourceTypeLocal:
                self._source_kind = "local_only"
                return source
        raise RuntimeError("Không tìm thấy nguồn lịch (iCloud hoặc Trên máy)")

    def _calendar(self, identifier: str | None):
        return self.store.calendarWithIdentifier_(identifier) if identifier else None

    def _new_container(self, entity_type, source):
        cal = self.ek.EKCalendar.calendarForEntityType_eventStore_(entity_type, self.store)
        cal.setTitle_(CONTAINER_NAME)
        cal.setSource_(source)
        ok, err = self.store.saveCalendar_commit_error_(cal, True, None)
        if not ok:
            raise RuntimeError(f"Không tạo được lịch/danh sách: {err}")
        return cal

    def ensure_containers(self, state: State) -> None:
        ek = self.ek
        if self._calendar(state.calendar_id) is None:
            cal = self._new_container(ek.EKEntityTypeEvent, self._event_source())
            state.calendar_id = str(cal.calendarIdentifier())
        else:
            self._event_source()
        if self._calendar(state.reminder_list_id) is None:
            # Lời nhắc iCloud không nằm ở nguồn CalDAV của Lịch (EKErrorDomain 24, research R4).
            default = self.store.defaultCalendarForNewReminders()
            source = default.source() if default else self._event_source()
            reminders = self._new_container(ek.EKEntityTypeReminder, source)
            state.reminder_list_id = str(reminders.calendarIdentifier())

    def list_items(self, state: State) -> list[Item] | None:
        cal, rem_list = self._calendar(state.calendar_id), self._calendar(state.reminder_list_id)
        if cal is None or rem_list is None:
            return None
        now = datetime.now()
        predicate = self.store.predicateForEventsWithStartDate_endDate_calendars_(
            _ns_date((now - timedelta(days=2)).astimezone().isoformat()),
            _ns_date((now + timedelta(days=500)).astimezone().isoformat()),
            [cal],
        )
        items = [
            Item(key=self._key(e, state), kind="event", handle=e)
            for e in (self.store.eventsMatchingPredicate_(predicate) or [])
        ]
        flag: dict = {}

        def got(reminders):
            flag.update(done=True, items=list(reminders or []))

        self.store.fetchRemindersMatchingPredicate_completion_(
            self.store.predicateForRemindersInCalendars_([rem_list]), got
        )
        self._wait(flag, 30)
        items += [
            Item(key=self._key(r, state), kind="reminder", handle=r) for r in flag.get("items", [])
        ]
        return items

    def _key(self, item, state: State) -> str | None:
        """Ưu tiên URL lichhoc://; nếu dịch vụ không giữ URL thì tra theo ID đã lưu lúc tạo."""
        url = item.URL()
        return key_from_url(str(url.absoluteString()) if url else None) or state.item_keys.get(
            str(item.calendarItemIdentifier())
        )

    def _fill_event(self, event, item: dict) -> None:
        from Foundation import NSURL

        event.setTitle_(item["title"])
        event.setLocation_(item.get("location"))
        event.setStartDate_(_ns_date(item["start_at"]))
        event.setEndDate_(_ns_date(item["end_at"]))
        event.setURL_(NSURL.URLWithString_(url_from_key(item["sync_key"])))
        event.setAlarms_(None)
        for minutes in item.get("alarms_minutes_before", []):
            event.addAlarm_(self.ek.EKAlarm.alarmWithRelativeOffset_(-60 * minutes))

    def _fill_reminder(self, reminder, item: dict) -> None:
        from Foundation import NSURL, NSDateComponents

        due = datetime.fromisoformat(item["due_at"])
        comps = NSDateComponents.alloc().init()
        comps.setYear_(due.year)
        comps.setMonth_(due.month)
        comps.setDay_(due.day)
        if item["due_has_time"]:
            comps.setHour_(due.hour)
            comps.setMinute_(due.minute)
        reminder.setTitle_(item["title"])
        reminder.setDueDateComponents_(comps)
        reminder.setURL_(NSURL.URLWithString_(url_from_key(item["sync_key"])))
        reminder.setAlarms_(None)
        if item.get("alarm_at"):
            reminder.addAlarm_(self.ek.EKAlarm.alarmWithAbsoluteDate_(_ns_date(item["alarm_at"])))

    def _save(self, kind: str, obj) -> None:
        if kind == "event":
            ok, err = self.store.saveEvent_span_commit_error_(
                obj, self.ek.EKSpanThisEvent, False, None
            )
        else:
            ok, err = self.store.saveReminder_commit_error_(obj, False, None)
        if not ok:
            raise RuntimeError(f"Không lưu được {kind}: {err}")

    def create(self, kind: str, item: dict, state: State) -> str:
        if kind == "event":
            obj = self.ek.EKEvent.eventWithEventStore_(self.store)
            obj.setCalendar_(self._calendar(state.calendar_id))
            self._fill_event(obj, item)
        else:
            obj = self.ek.EKReminder.reminderWithEventStore_(self.store)
            obj.setCalendar_(self._calendar(state.reminder_list_id))
            self._fill_reminder(obj, item)
        self._save(kind, obj)
        return str(obj.calendarItemIdentifier())

    def update(self, handle: Any, kind: str, item: dict) -> None:
        (self._fill_event if kind == "event" else self._fill_reminder)(handle, item)
        self._save(kind, handle)

    def delete(self, handle: Any) -> None:
        if isinstance(handle, self.ek.EKEvent):
            self.store.removeEvent_span_commit_error_(handle, self.ek.EKSpanThisEvent, False, None)
        else:
            self.store.removeReminder_commit_error_(handle, False, None)

    def remove_containers(self, state: State) -> None:
        for identifier in (state.calendar_id, state.reminder_list_id):
            cal = self._calendar(identifier)
            if cal is not None:
                self.store.removeCalendar_commit_error_(cal, False, None)

    def commit(self) -> None:
        ok, err = self.store.commit_(None)
        if not ok:
            raise RuntimeError(f"Không ghi được vào Lịch/Lời nhắc: {err}")
