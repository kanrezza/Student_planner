from datetime import date

from lichhoc_agent.calendar_store import FakeCalendarStore
from lichhoc_agent.main import needs_full_sync, sync_once
from lichhoc_agent.state import State


class FakeBackend:
    def __init__(self, feed):
        self.feed_data = feed
        self.statuses = []

    def feed(self):
        return self.feed_data

    def put_status(self, **status):
        self.statuses.append(status)


DIGEST = {
    "sync_key": "digest:2026-11-16",
    "fingerprint": "d",
    "date": "2026-11-16",
    "title": "Hôm nay: Ca 1 Giải tích 1 A2-301",
    "notes": "Ca 1 (06:45): Giải tích 1 – A2-301",
    "alarm_at": "2026-11-16T05:00:00+07:00",
}


def make_feed(enabled=True, events=None, reminders=None, revision=3, digests=None):
    return {
        "digests": digests if digests is not None else [],
        "revision": revision,
        "sync_enabled": enabled,
        "calendar_name": "Lịch Học Cá Nhân",
        "reminder_list_name": "Lịch Học Cá Nhân",
        "events": events
        if events is not None
        else [
            {
                "sync_key": "session:1",
                "fingerprint": "a",
                "title": "Giải tích 1",
                "location": "A2-301",
                "start_at": "2026-11-16T06:45:00+07:00",
                "end_at": "2026-11-16T09:25:00+07:00",
                "alarms_minutes_before": [15],
            },
        ],
        "reminders": reminders
        if reminders is not None
        else [
            {
                "sync_key": "task:5",
                "fingerprint": "c",
                "title": "Nộp bài",
                "due_at": "2026-11-17T17:00:00+07:00",
                "due_has_time": True,
                "important": False,
                "alarms_at": ["2026-11-17T16:00:00+07:00"],
            },
        ],
    }


def test_first_sync_creates_containers_and_items(tmp_path):
    store, state = FakeCalendarStore(), State(path=tmp_path / "state.json")
    backend = FakeBackend(make_feed())
    assert sync_once(backend, store, state) == 3
    assert store.containers_exist(state)
    assert {i["sync_key"] for i in store.items.values()} == {"session:1", "task:5"}
    assert state.fingerprints == {"session:1": "a", "task:5": "c"}
    assert backend.statuses[-1]["permission"] == "granted"
    assert backend.statuses[-1]["last_synced_revision"] == 3
    assert State.load(tmp_path / "state.json").fingerprints == state.fingerprints


def test_update_delete_and_recreate_after_user_deleted_calendar(tmp_path):
    store, state = FakeCalendarStore(), State(path=tmp_path / "state.json")
    sync_once(FakeBackend(make_feed()), store, state)

    changed = make_feed(revision=4, reminders=[])
    changed["events"][0] = {**changed["events"][0], "location": "C1-204", "fingerprint": "a2"}
    sync_once(FakeBackend(changed), store, state)
    assert [i["location"] for i in store.items.values()] == ["C1-204"]

    store.user_deletes_containers()
    sync_once(FakeBackend(changed), store, state)
    assert [i["sync_key"] for i in store.items.values()] == ["session:1"]


def test_disable_sync_removes_containers(tmp_path):
    store, state = FakeCalendarStore(), State(path=tmp_path / "state.json")
    sync_once(FakeBackend(make_feed()), store, state)
    sync_once(FakeBackend(make_feed(enabled=False)), store, state)
    assert not store.containers_exist(state) and store.items == {}
    assert state.calendar_id is None and state.fingerprints == {}


def test_permission_denied_writes_nothing(tmp_path):
    store, state = FakeCalendarStore(permission="denied"), State(path=tmp_path / "state.json")
    backend = FakeBackend(make_feed())
    sync_once(backend, store, state)
    assert store.items == {} and backend.statuses[-1]["permission"] == "denied"


def test_digest_and_important_reminder_written(tmp_path):
    store, state = FakeCalendarStore(), State(path=tmp_path / "state.json")
    important = {
        "sync_key": "task:6",
        "fingerprint": "i",
        "title": "Ôn thi",
        "due_at": "2026-11-18T17:00:00+07:00",
        "due_has_time": True,
        "important": True,
        "alarms_at": ["2026-11-17T17:00:00+07:00", "2026-11-18T16:45:00+07:00"],
    }
    sync_once(FakeBackend(make_feed(reminders=[important], digests=[DIGEST])), store, state)
    by_key = {i["sync_key"]: i for i in store.items.values()}
    assert by_key["digest:2026-11-16"]["kind"] == "digest"
    assert by_key["digest:2026-11-16"]["notes"] == DIGEST["notes"]
    assert by_key["task:6"]["alarms_at"] == important["alarms_at"]
    assert by_key["task:6"]["important"] is True
    assert state.fingerprints["digest:2026-11-16"] == "d"

    # Ngày đã qua: bản tóm tắt không còn trong feed → bị xoá.
    sync_once(FakeBackend(make_feed(reminders=[important], revision=4)), store, state)
    assert "digest:2026-11-16" not in {i["sync_key"] for i in store.items.values()}


def test_needs_full_sync_on_new_day_or_after_interval():
    day = date(2026, 11, 16)
    assert needs_full_sync(now=100.0, last_full=0.0, today=day, last_day=day) is False
    assert needs_full_sync(now=100.0, last_full=0.0, today=date(2026, 11, 17), last_day=day)
    assert needs_full_sync(now=7 * 3600.0, last_full=0.0, today=day, last_day=day)
