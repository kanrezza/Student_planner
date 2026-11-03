from datetime import date, datetime, time
from types import SimpleNamespace

from app.lib.timeutil import TZ, combine
from app.services.digest import DigestSession, DigestTask, build_digest, classify_tasks

DAY = date(2026, 11, 16)
SETTINGS = SimpleNamespace(
    daily_digest_enabled=True, daily_digest_time=time(5, 0), daily_digest_overdue_only=True
)


def at(hh, mm, day=DAY):
    return combine(day, time(hh, mm))


def sess(name, start, label=None, room="A101", important=False):
    return DigestSession(start_at=start, label=label, name=name, room=room, is_important=important)


def due(title, when, has_time=True, important=False):
    return DigestTask(title=title, due_at=when, has_time=has_time, is_important=important)


def test_full_day_order_and_task_limit():
    d = build_digest(
        DAY,
        exams=[],
        sessions=[sess("Vật lý", at(14, 0)), sess("Giải tích", at(13, 0), label="Ca 3", room=None)],
        due_today=[due("Đọc chương 3", at(23, 59), has_time=False), due("Nộp bài Toán", at(17, 0))],
        overdue=[
            due("Báo cáo B", at(9, 0, date(2026, 11, 12))),
            due("Báo cáo A", at(9, 0, date(2026, 11, 10))),
            due("Báo cáo C", at(9, 0, date(2026, 11, 14))),
        ],
        settings=SETTINGS,
    )
    assert d.fire_at == at(5, 0)
    assert d.lines == [
        "Ca 3 (13:00): Giải tích – chưa có phòng",
        "14:00: Vật lý – A101",
        "Nộp bài Toán – hạn 17:00",
        "Đọc chương 3 – cả ngày",
        "Báo cáo A – quá hạn từ 10/11",
        "+2 việc khác",
    ]
    assert d.title == (
        "Hôm nay: Ca 3 Giải tích · 14:00 Vật lý A101 · "
        "Việc: Nộp bài Toán, Đọc chương 3, Báo cáo A (quá hạn) +2 việc khác"
    )
    assert not d.is_important


def test_no_extra_line_when_three_or_fewer_tasks():
    d = build_digest(DAY, [], [], [due("A", at(8, 0)), due("B", at(9, 0))], [], SETTINGS)
    assert d.lines == ["A – hạn 08:00", "B – hạn 09:00"]
    assert "việc khác" not in d.title


def test_four_due_tasks_show_first_three_and_no_overdue_title():
    tasks = [due(f"T{i}", at(8 + i, 0)) for i in range(4)]
    d = build_digest(DAY, [], [], tasks, [due("Cũ", at(9, 0, date(2026, 11, 1)))], SETTINGS)
    assert d.lines == ["T0 – hạn 08:00", "T1 – hạn 09:00", "T2 – hạn 10:00", "+2 việc khác"]


def test_empty_day_has_no_digest():
    assert build_digest(DAY, [], [], [], [], SETTINGS) is None


def test_overdue_only_day_respects_option():
    overdue = [due("Cũ", at(9, 0, date(2026, 11, 1)))]
    assert build_digest(DAY, [], [], [], overdue, SETTINGS).lines == ["Cũ – quá hạn từ 01/11"]
    off = SimpleNamespace(**{**vars(SETTINGS), "daily_digest_overdue_only": False})
    assert build_digest(DAY, [], [], [], overdue, off) is None


def test_disabled_digest():
    off = SimpleNamespace(**{**vars(SETTINGS), "daily_digest_enabled": False})
    assert build_digest(DAY, [], [sess("Giải tích", at(7, 0))], [], [], off) is None


def test_important_item_adds_star():
    d = build_digest(DAY, [], [sess("Giải tích", at(7, 0), important=True)], [], [], SETTINGS)
    assert d.is_important
    assert d.title.startswith("★ Hôm nay: ")


def test_classify_tasks_by_day():
    def t(due_date, due_time=None, done=False):
        return SimpleNamespace(
            title="x",
            due_date=due_date,
            due_time=due_time,
            is_important=False,
            completed_at=datetime(2026, 11, 1, tzinfo=TZ) if done else None,
        )

    tasks = [
        t(DAY),
        t(DAY, time(7, 0)),
        t(date(2026, 11, 15), time(23, 0)),  # quá hạn từ hôm trước
        t(date(2026, 11, 17)),  # tương lai
        t(DAY, done=True),
        t(None),
    ]
    due_today, overdue = classify_tasks(DAY, tasks)
    assert len(due_today) == 2
    assert len(overdue) == 1
