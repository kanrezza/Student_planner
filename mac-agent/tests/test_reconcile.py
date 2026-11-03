from lichhoc_agent.reconcile import Item, plan_changes


def feed(enabled=True, events=(), reminders=()):
    return {
        "revision": 7,
        "sync_enabled": enabled,
        "events": [dict(e) for e in events],
        "reminders": [dict(r) for r in reminders],
    }


EV1 = {"sync_key": "session:1", "fingerprint": "a", "title": "Giải tích"}
EV2 = {"sync_key": "session:2", "fingerprint": "b", "title": "Triết học"}
TK1 = {"sync_key": "task:5", "fingerprint": "c", "title": "Nộp bài"}


def test_sync_disabled_removes_everything():
    plan = plan_changes(feed(enabled=False, events=[EV1]), [], {})
    assert plan.remove_all and not plan.create


def test_missing_containers_recreate_and_create_all():
    plan = plan_changes(feed(events=[EV1], reminders=[TK1]), None, {})
    assert plan.recreate_containers
    assert [(kind, item["sync_key"]) for kind, item in plan.create] == [
        ("event", "session:1"),
        ("reminder", "task:5"),
    ]


def test_create_update_delete_by_key_and_fingerprint():
    current = [
        Item(key="session:1", kind="event", handle="h1"),  # fingerprint khớp → giữ
        Item(key="session:2", kind="event", handle="h2"),  # fingerprint lệch → cập nhật
        Item(key="session:9", kind="event", handle="h9"),  # không còn trong feed → xoá
    ]
    saved = {"session:1": "a", "session:2": "OLD", "session:9": "z"}
    plan = plan_changes(feed(events=[EV1, EV2], reminders=[TK1]), current, saved)
    assert [(k, i["sync_key"]) for k, i in plan.create] == [("reminder", "task:5")]
    assert [(h, i["sync_key"]) for h, _, i in plan.update] == [("h2", "session:2")]
    assert plan.delete == ["h9"]
    assert not plan.remove_all and not plan.recreate_containers


def test_never_touches_items_without_our_url():
    current = [Item(key=None, kind="event", handle="user-added")]
    plan = plan_changes(feed(events=[EV1]), current, {})
    assert plan.delete == [] and plan.update == []
    assert [i["sync_key"] for _, i in plan.create] == ["session:1"]


def test_duplicate_items_for_same_key_are_cleaned():
    current = [
        Item(key="session:1", kind="event", handle="h1"),
        Item(key="session:1", kind="event", handle="h1-copy"),
    ]
    plan = plan_changes(feed(events=[EV1]), current, {"session:1": "a"})
    assert plan.delete == ["h1-copy"] and plan.create == [] and plan.update == []


def test_force_rewrites_all():
    current = [Item(key="session:1", kind="event", handle="h1")]
    plan = plan_changes(feed(events=[EV1]), current, {"session:1": "a"}, force=True)
    assert [h for h, _, _ in plan.update] == ["h1"]
