"""Kiểm tra nền tảng: migration khớp model, dữ liệu mặc định, ràng buộc database, định dạng lỗi."""

from datetime import date, time

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Settings, Shift, SyncState, Tag, TaskList
from tests.factories import make_semester, make_subject, make_tag, make_task


def test_migrations_match_models(db_session):
    """Không được có khác biệt giữa models và migration (tương đương `flask db check`)."""
    context = MigrationContext.configure(db_session.connection())
    assert compare_metadata(context, db.metadata) == []


def test_seed_data(db_session):
    shifts = db_session.scalars(select(Shift).order_by(Shift.position)).all()
    assert [(s.name, s.start_time, s.end_time) for s in shifts] == [
        ("Ca 1", time(6, 45), time(9, 25)),
        ("Ca 2", time(9, 30), time(12, 10)),
        ("Ca 3", time(13, 0), time(15, 40)),
        ("Ca 4", time(15, 45), time(18, 25)),
    ]
    lists = db_session.scalars(select(TaskList).order_by(TaskList.id)).all()
    assert [(tl.name, tl.color, tl.is_default_study) for tl in lists] == [
        ("Học tập", "c01", True),
        ("Cá nhân", "c02", False),
        ("Công việc", "c03", False),
    ]
    e_learning = db_session.scalars(select(Tag).where(Tag.system_key == "e_learning")).one()
    assert (e_learning.name, e_learning.color) == ("E-Learning", "c05")
    assert db_session.get(Settings, 1) is not None
    assert db_session.get(SyncState, 1).revision >= 0


def _violates(db_session, action) -> bool:
    nested = db_session.begin_nested()
    try:
        action()
        db_session.flush()
    except IntegrityError:
        nested.rollback()
        return True
    nested.rollback()
    return False


def test_semesters_cannot_overlap(db_session):
    make_semester(db_session, "HK1", date(2026, 9, 7), date(2026, 12, 20))
    assert _violates(
        db_session, lambda: make_semester(db_session, "HK2", date(2026, 12, 20), date(2027, 5, 1))
    )
    assert not _violates(
        db_session, lambda: make_semester(db_session, "HK2", date(2026, 12, 21), date(2027, 5, 1))
    )


@pytest.mark.parametrize(
    "fields",
    [
        {"weekdays": []},
        {"weekdays": [8]},
        {"start_time": time(9, 0), "end_time": time(9, 0)},
        {"start_shift_id": 1},  # thiếu end_shift_id
        {"reminder_minutes": -2},
        {"name": ""},
    ],
)
def test_subject_check_constraints(db_session, fields):
    semester = make_semester(db_session)
    assert _violates(db_session, lambda: make_subject(db_session, semester, **fields))


@pytest.mark.parametrize(
    "fields",
    [{"priority": 4}, {"due_time": time(17, 0)}, {"title": "   "}, {"title": "x" * 301}],
)
def test_task_check_constraints(db_session, fields):
    title = fields.pop("title", "Nộp bài")
    assert _violates(db_session, lambda: make_task(db_session, title, **fields))


def test_tag_and_list_names_unique_case_insensitive(db_session):
    make_tag(db_session, "Gấp")
    assert _violates(db_session, lambda: make_tag(db_session, "gấp"))
    assert _violates(db_session, lambda: db_session.add(TaskList(name="học tập", color="c04")))


def test_vietnamese_text_round_trip(db_session):
    task = make_task(db_session, "Ôn tập Triết học Mác - Lênin: chương 3 “Phép biện chứng”")
    db_session.expire_all()
    assert db_session.get(type(task), task.id).title.endswith("“Phép biện chứng”")


def test_unknown_route_returns_vietnamese_json_404(client):
    resp = client.get("/api/khong-ton-tai")
    assert resp.status_code == 404
    assert resp.get_json() == {
        "error": {"code": "not_found", "message": "Không tìm thấy đường dẫn này"}
    }
