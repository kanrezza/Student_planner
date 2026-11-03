from lichhoc_agent.calendar_store import FakeCalendarStore
from lichhoc_agent.main import sync_once
from lichhoc_agent.state import State


class FakeBackend:
    def __init__(self, feed):
        self.feed_data = feed
        self.statuses = []

    def feed(self):
        return self.feed_data

    def put_status(self, **status):
        self.statuses.append(status)


def make_feed(enabled=True, events=None, reminders=None, revision=3):
    return {
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
                "alarm_at": "2026-11-17T16:00:00+07:00",
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
