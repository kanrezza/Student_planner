"""Lọc bảng Kanban theo danh sách, nhãn, môn (kể cả deadline tự tạo) — feature 005, US2."""

import time as clock
from datetime import date, datetime

import pytest

from app.lib import timeutil
from app.lib.timeutil import TZ
from app.models import ClassSession, Task
from tests.factories import make_semester, make_subject, make_tag
from tests.integration.test_board_api import board, ids
from tests.integration.test_task_status_api import create

NOW = datetime(2026, 11, 11, 10, 0, tzinfo=TZ)


@pytest.fixture(autouse=True)
def fixed_now(monkeypatch):
    monkeypatch.setattr(timeutil, "now", lambda: NOW)


def second_list(client):
    return client.post("/api/lists", json={"name": "Việc nhà", "color": "c03"}).get_json()


def test_loc_nhieu_danh_sach(client):
    other = second_list(client)
    study = create(client, "Học")
    home = create(client, "Nhà", list_id=other["id"])
    assert set(ids(board(client, f"?list_ids={other['id']}")["columns"]["todo"])) == {home["id"]}
    both = board(client, f"?list_ids={other['id']},{study['list_id']}")
    assert set(ids(both["columns"]["todo"])) == {home["id"], study["id"]}


def test_loc_nhan_khop_bat_ky_va_ket_hop_va(client, db_session):
    gap, nhom = make_tag(db_session, "Gấp"), make_tag(db_session, "Nhóm", "c02")
    a = create(client, "A", tag_ids=[gap.id])
    b = create(client, "B", tag_ids=[nhom.id])
    c = create(client, "C", tag_ids=[gap.id, nhom.id])
    create(client, "D")
    either = board(client, f"?tag_ids={gap.id},{nhom.id}")["columns"]["todo"]
    assert set(ids(either)) == {a["id"], b["id"], c["id"]}
    other = second_list(client)
    in_other = create(client, "E", list_id=other["id"], tag_ids=[gap.id])
    both = board(client, f"?tag_ids={gap.id}&list_ids={other['id']}")["columns"]["todo"]
    assert ids(both) == [in_other["id"]]  # "và" giữa các loại lọc


def test_loc_theo_mon_ca_deadline_tu_tao(client, db_session):
    semester = make_semester(db_session)
    subject = make_subject(db_session, semester)
    other_subject = make_subject(db_session, semester, name="Vật lý")
    session = ClassSession(
        subject_id=subject.id,
        date=date(2026, 11, 12),
        start_at=datetime(2026, 11, 12, 20, 0, tzinfo=TZ),
        end_at=datetime(2026, 11, 12, 21, 30, tzinfo=TZ),
    )
    db_session.add(session)
    db_session.flush()
    hand = create(client, "Gắn tay", subject_id=subject.id)
    create(client, "Môn khác", subject_id=other_subject.id)
    create(client, "Không môn")
    list_id = hand["list_id"]
    auto = Task(list_id=list_id, title="Bài tập tự tạo", source_session_id=session.id, is_auto=True)
    db_session.add(auto)
    db_session.commit()
    found = board(client, f"?subject_ids={subject.id}")["columns"]["todo"]
    assert set(ids(found)) == {hand["id"], auto.id}
    assert all(t["effective_subject_id"] == subject.id for t in found)


def test_dem_an_cot_xong_sau_khi_loc(client, db_session):
    other = second_list(client)
    a, b = create(client, "A"), create(client, "B", list_id=other["id"])
    for task in (a, b):
        client.post(f"/api/tasks/{task['id']}/complete")
        db_session.get(Task, task["id"]).completed_at = datetime(2026, 10, 1, tzinfo=TZ)
    db_session.flush()
    data = board(client, f"?list_ids={other['id']}")
    assert data["columns"]["done"] == [] and data["done_hidden_count"] == 1


def test_tham_so_loc_sai(client):
    response = client.get("/api/tasks/board?list_ids=a,b")
    assert response.status_code == 400 and "list_ids" in response.get_json()["error"]["fields"]


def test_xoa_mon_bo_gan_mon_cua_task(client, db_session):
    subject = make_subject(db_session, make_semester(db_session))
    task = create(client, "T", subject_id=subject.id)
    db_session.commit()
    assert client.delete(f"/api/subjects/{subject.id}").status_code in (200, 204)
    db_session.expire_all()
    assert db_session.get(Task, task["id"]).subject_id is None


def test_300_task_loc_duoi_1_giay(client, db_session):
    other = second_list(client)
    study_list = create(client, "x")["list_id"]
    db_session.add_all(
        Task(
            title=f"T{i}",
            list_id=other["id"] if i % 2 else study_list,
            in_progress=i % 5 == 0,
            board_rank=float(i),
        )
        for i in range(300)
    )
    db_session.commit()
    start = clock.perf_counter()
    data = board(client, f"?list_ids={other['id']}")
    elapsed = clock.perf_counter() - start
    assert len(data["columns"]["todo"]) + len(data["columns"]["doing"]) == 150
    assert elapsed < 1.0, f"{elapsed:.2f} giây"
