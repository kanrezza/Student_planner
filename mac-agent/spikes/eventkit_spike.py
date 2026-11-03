"""SPIKE S2 (task T011, research R4): Python + PyObjC có ghi được vào Lịch/Lời nhắc qua EventKit không?

Chạy dưới dạng .app (py2app, có Info.plist khai báo quyền) bằng `open`, để macOS coi chính app là tiến
trình xin quyền (TCC). Các bước:
1. Xin quyền đầy đủ cho Lịch và Lời nhắc (macOS 14+: requestFullAccessTo…).
2. Tìm nguồn iCloud; tạo lịch và danh sách lời nhắc "Lịch Học Cá Nhân (spike)".
3. Tạo 1 sự kiện bắt đầu sau 10 phút (báo trước 5 phút) và 1 lời nhắc hạn sau 15 phút (báo lúc +10 phút),
   gắn URL lichhoc://spike/… như cách agent thật dùng sync_key.
4. Đọc lại theo URL để chắc việc đối chiếu (reconcile) khả thi.
5. Ghi kết quả vào ~/Library/Application Support/LichHocAgent/spike-result.json.

Dọn dẹp: open -a <đường dẫn app> --args --cleanup  (xoá lịch và danh sách "(spike)").
"""

from __future__ import annotations

import json
import sys
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path

import EventKit
from Foundation import NSURL, NSDate, NSDateComponents, NSRunLoop

SPIKE_NAME = "Lịch Học Cá Nhân (spike)"
RESULT_DIR = Path.home() / "Library/Application Support/LichHocAgent"
RESULT_FILE = RESULT_DIR / "spike-result.json"


def wait_for(flag: dict, timeout: float = 120.0) -> None:
    """Chạy run loop cho tới khi callback bất đồng bộ của EventKit trả về (người dùng bấm Cho phép)."""
    deadline = time.time() + timeout
    while not flag.get("done") and time.time() < deadline:
        NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.2))


def request_access(store, entity: str) -> tuple[bool, str | None]:
    flag: dict = {}

    def handler(granted, error):
        flag.update(done=True, granted=bool(granted), error=str(error) if error else None)

    if entity == "events":
        store.requestFullAccessToEventsWithCompletion_(handler)
    else:
        store.requestFullAccessToRemindersWithCompletion_(handler)
    wait_for(flag)
    return flag.get("granted", False), flag.get("error", "timeout chờ người dùng")


def ns_date(dt: datetime) -> NSDate:
    return NSDate.dateWithTimeIntervalSince1970_(dt.timestamp())


def find_icloud_source(store):
    for source in store.sources():
        if source.sourceType() == EventKit.EKSourceTypeCalDAV and source.title() == "iCloud":
            return source, "icloud"
    for source in store.sources():
        if source.sourceType() == EventKit.EKSourceTypeLocal:
            return source, "local_only"
    return None, "none"


def get_or_create_calendar(store, entity_type, source):
    for cal in store.calendarsForEntityType_(entity_type):
        if cal.title() == SPIKE_NAME:
            return cal
    cal = EventKit.EKCalendar.calendarForEntityType_eventStore_(entity_type, store)
    cal.setTitle_(SPIKE_NAME)
    cal.setSource_(source)
    ok, err = store.saveCalendar_commit_error_(cal, True, None)
    if not ok:
        raise RuntimeError(f"Không tạo được lịch: {err}")
    return cal


def cleanup(store) -> dict:
    removed = []
    for entity in (EventKit.EKEntityTypeEvent, EventKit.EKEntityTypeReminder):
        for cal in store.calendarsForEntityType_(entity):
            if cal.title() == SPIKE_NAME:
                ok, err = store.removeCalendar_commit_error_(cal, True, None)
                removed.append(
                    {"entity": int(entity), "ok": bool(ok), "error": str(err) if err else None}
                )
    return {"action": "cleanup", "removed": removed}


def arg_int(name: str, default: int) -> int:
    """Đọc tham số dạng `--start-in 15` (truyền qua `open … --args`)."""
    if name in sys.argv:
        return int(sys.argv[sys.argv.index(name) + 1])
    return default


def remove_old_items(store, event_cal, reminder_cal) -> dict:
    """Xoá sự kiện và lời nhắc thử cũ trong lịch "(spike)", giữ lại chính lịch đó."""
    now = datetime.now()
    predicate = store.predicateForEventsWithStartDate_endDate_calendars_(
        ns_date(now - timedelta(days=7)), ns_date(now + timedelta(days=7)), [event_cal]
    )
    events = list(store.eventsMatchingPredicate_(predicate) or [])
    for event in events:
        store.removeEvent_span_commit_error_(event, EventKit.EKSpanThisEvent, False, None)

    flag: dict = {}

    def on_reminders(reminders):
        flag.update(done=True, items=list(reminders or []))

    store.fetchRemindersMatchingPredicate_completion_(
        store.predicateForRemindersInCalendars_([reminder_cal]), on_reminders
    )
    wait_for(flag, timeout=20)
    for reminder in flag.get("items", []):
        store.removeReminder_commit_error_(reminder, False, None)
    store.commit_(None)
    return {"events": len(events), "reminders": len(flag.get("items", []))}


def run_spike(store) -> dict:
    result: dict = {"action": "spike", "started_at": datetime.now().isoformat(timespec="seconds")}

    granted_events, err_e = request_access(store, "events")
    granted_rem, err_r = request_access(store, "reminders")
    result["permission"] = {
        "events": granted_events,
        "events_error": err_e,
        "reminders": granted_rem,
        "reminders_error": err_r,
    }
    if not (granted_events and granted_rem):
        return result

    store.reset()  # nạp lại nguồn sau khi được cấp quyền
    source, source_kind = find_icloud_source(store)
    result["source"] = source_kind
    result["event_source"] = {"title": str(source.title()), "type": int(source.sourceType())}
    if source is None:
        return result

    event_cal = get_or_create_calendar(store, EventKit.EKEntityTypeEvent, source)
    # Lời nhắc iCloud (bản đã nâng cấp) KHÔNG nằm ở nguồn CalDAV của Lịch (EKErrorDomain 24 "That
    # account does not support reminders") → dùng nguồn của danh sách lời nhắc mặc định.
    default_list = store.defaultCalendarForNewReminders()
    reminder_source = default_list.source() if default_list else source
    result["reminder_source"] = {
        "title": str(reminder_source.title()),
        "type": int(reminder_source.sourceType()),
    }
    reminder_cal = get_or_create_calendar(store, EventKit.EKEntityTypeReminder, reminder_source)

    start_in = arg_int("--start-in", 10)  # phút tới giờ bắt đầu / hạn chót
    alarm_before = arg_int("--alarm-before", 5)  # báo trước bao nhiêu phút
    result["removed_old_items"] = remove_old_items(store, event_cal, reminder_cal)

    # Làm tròn lên phút kế tiếp để "sau N phút" không bị hụt vài chục giây.
    now = datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=1)
    event_start = now + timedelta(minutes=start_in)
    alarm_at = event_start - timedelta(minutes=alarm_before)
    label = event_start.strftime("%H:%M")

    event = EventKit.EKEvent.eventWithEventStore_(store)
    event.setCalendar_(event_cal)
    event.setTitle_(f"Thử nhắc buổi học {label} (spike)")
    event.setLocation_("A2-301")
    event.setStartDate_(ns_date(event_start))
    event.setEndDate_(ns_date(event_start + timedelta(minutes=30)))
    event.setURL_(NSURL.URLWithString_("lichhoc://spike/session/1"))
    event.addAlarm_(EventKit.EKAlarm.alarmWithRelativeOffset_(-alarm_before * 60))
    ok_e, err_e = store.saveEvent_span_commit_error_(event, EventKit.EKSpanThisEvent, False, None)

    due = event_start
    reminder = EventKit.EKReminder.reminderWithEventStore_(store)
    reminder.setCalendar_(reminder_cal)
    reminder.setTitle_(f"Thử nhắc hạn chót {label} (spike)")
    comps = NSDateComponents.alloc().init()
    for setter, value in [
        ("setYear_", due.year),
        ("setMonth_", due.month),
        ("setDay_", due.day),
        ("setHour_", due.hour),
        ("setMinute_", due.minute),
    ]:
        getattr(comps, setter)(value)
    reminder.setDueDateComponents_(comps)
    reminder.setURL_(NSURL.URLWithString_("lichhoc://spike/task/1"))
    reminder.addAlarm_(EventKit.EKAlarm.alarmWithAbsoluteDate_(ns_date(alarm_at)))
    ok_r, err_r = store.saveReminder_commit_error_(reminder, False, None)

    ok_c, err_c = store.commit_(None)
    result["write"] = {
        "event_saved": bool(ok_e),
        "event_error": str(err_e) if err_e else None,
        "reminder_saved": bool(ok_r),
        "reminder_error": str(err_r) if err_r else None,
        "commit": bool(ok_c),
        "commit_error": str(err_c) if err_c else None,
        "event_title": str(event.title()),
        "event_start": event_start.isoformat(timespec="minutes"),
        "event_alarm_at": alarm_at.isoformat(timespec="minutes"),
        "reminder_title": str(reminder.title()),
        "reminder_due": due.isoformat(timespec="minutes"),
        "reminder_alarm_at": alarm_at.isoformat(timespec="minutes"),
        "event_alarms_saved": len(event.alarms() or []),
        "reminder_alarms_saved": len(reminder.alarms() or []),
    }

    # Đọc lại theo URL — cơ sở cho việc đối chiếu sync_key của agent thật.
    predicate = store.predicateForEventsWithStartDate_endDate_calendars_(
        ns_date(now), ns_date(now + timedelta(hours=2)), [event_cal]
    )
    urls = [str(e.URL()) for e in store.eventsMatchingPredicate_(predicate) if e.URL()]
    result["read_back_event_urls"] = urls
    result["calendar_identifier"] = str(event_cal.calendarIdentifier())
    return result


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    store = EventKit.EKEventStore.alloc().init()
    try:
        result = cleanup(store) if "--cleanup" in sys.argv else run_spike(store)
    except Exception:  # noqa: BLE001 — spike: ghi mọi lỗi ra file kết quả
        result = {"error": traceback.format_exc()}
    result["finished_at"] = datetime.now().isoformat(timespec="seconds")
    result["python"] = sys.version.split()[0]
    RESULT_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
