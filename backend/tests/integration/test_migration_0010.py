"""Migration 0010: môn cũ thành đúng một quy tắc lặp, buổi giữ nguyên ngoại lệ (feature 004, T007)."""

import pytest
import sqlalchemy as sa
from flask_migrate import downgrade, upgrade

from app.extensions import db


@pytest.fixture
def app_at_0009(isolated_app):
    with isolated_app.app_context():
        db.session.remove()
        db.engine.dispose()
        downgrade(revision="0009_ca2_default")
        db.engine.dispose()
        run(
            "DELETE FROM semesters"
        )  # xoá dữ liệu của test trước (database dùng chung trong module)
    yield isolated_app
    with isolated_app.app_context():
        db.session.remove()
        db.engine.dispose()
        upgrade()
        db.session.remove()


def run(sql, **params):
    with db.engine.begin() as conn:
        return conn.execute(sa.text(sql), params)


def seed_legacy_data():
    run(
        "INSERT INTO semesters (id, name, start_date, end_date) "
        "VALUES (1, 'HK1', '2026-09-07', '2026-12-20')"
    )
    shift = run("SELECT id FROM shifts WHERE name = 'Ca 2'").scalar_one()
    # Môn 1: hai thứ, gắn Ca 2, có phòng. Môn 2: giờ tuỳ chỉnh, không phòng.
    run(
        "INSERT INTO subjects (id, semester_id, name, class_code, color, weekdays, start_shift_id, "
        "end_shift_id, start_time, end_time, start_date, end_date, room) VALUES "
        "(1, 1, 'Giải tích', 'MAT1', 'c01', ARRAY[1,4]::smallint[], :s, :s, '09:30', '12:10', "
        "'2026-09-07', '2026-12-20', 'A101'), "
        "(2, 1, 'Triết', NULL, 'c02', ARRAY[3]::smallint[], NULL, NULL, '20:00', '21:30', "
        "'2026-10-01', '2026-11-30', NULL)",
        s=shift,
    )
    run(
        "INSERT INTO class_sessions (id, subject_id, date, start_at, end_at, room, is_cancelled, "
        "time_overridden, room_overridden) VALUES "
        "(1, 1, '2026-09-07', '2026-09-07 09:30+07', '2026-09-07 12:10+07', 'A101', false, false, false), "
        "(2, 1, '2026-09-10', '2026-09-10 09:30+07', '2026-09-10 12:10+07', 'A101', true, false, false), "
        "(3, 1, '2026-09-14', '2026-09-14 10:00+07', '2026-09-14 12:10+07', 'A101', false, true, false), "
        "(4, 1, '2026-09-17', '2026-09-17 09:30+07', '2026-09-17 12:10+07', 'B2', false, false, true), "
        "(5, 2, '2026-10-07', '2026-10-07 20:00+07', '2026-10-07 21:30+07', NULL, false, false, false)"
    )
    return shift


def test_upgrade_turns_each_subject_into_one_schedule(app_at_0009):
    with app_at_0009.app_context():
        shift = seed_legacy_data()
        upgrade()
        db.engine.dispose()

        rules = run(
            "SELECT subject_id, position, weekdays, start_date, end_date, start_shift_id, "
            "end_shift_id, to_char(start_time, 'HH24:MI'), to_char(end_time, 'HH24:MI'), room, "
            "period_from FROM subject_schedules ORDER BY subject_id"
        ).all()
        assert len(rules) == 2
        first, second = rules
        assert first[:3] == (1, 0, [1, 4])
        assert (str(first[3]), str(first[4])) == ("2026-09-07", "2026-12-20")
        assert (first[5], first[6], first[7], first[8], first[9]) == (
            shift,
            shift,
            "09:30",
            "12:10",
            "A101",
        )
        assert second[:3] == (2, 0, [3]) and second[5] is None and second[9] is None
        assert (second[7], second[8]) == ("20:00", "21:30")

        sessions = run(
            "SELECT cs.id, cs.schedule_id = ss.id, cs.is_cancelled, cs.time_overridden, "
            "cs.room_overridden, cs.room, cs.original_date FROM class_sessions cs "
            "JOIN subject_schedules ss ON ss.subject_id = cs.subject_id ORDER BY cs.id"
        ).all()
        assert [row[1] for row in sessions] == [True] * 5  # mọi buổi gắn quy tắc của môn
        assert [row[2:5] for row in sessions] == [
            (False, False, False),
            (True, False, False),
            (False, True, False),
            (False, False, True),
            (False, False, False),
        ]  # ngoại lệ giữ nguyên
        assert sessions[3][5] == "B2"

        columns = {
            row[0]
            for row in run(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'subjects'"
            )
        }
        assert {"weekdays", "start_date", "start_time", "room", "start_shift_id"}.isdisjoint(
            columns
        )
        assert {"course_code", "credits"} <= columns


def test_downgrade_restores_columns_from_first_schedule(app_at_0009):
    with app_at_0009.app_context():
        seed_legacy_data()
        upgrade()
        db.engine.dispose()
        # môn 1 có thêm quy tắc thứ hai: downgrade chỉ giữ quy tắc đầu tiên
        run(
            "INSERT INTO subject_schedules (subject_id, position, weekdays, start_date, end_date, "
            "start_time, end_time, room) VALUES (1, 1, ARRAY[2]::smallint[], '2026-10-05', "
            "'2026-10-20', '13:00', '15:40', 'C3')"
        )
        downgrade(revision="0009_ca2_default")
        db.engine.dispose()
        row = run(
            "SELECT weekdays, to_char(start_time, 'HH24:MI'), room FROM subjects WHERE id = 1"
        ).one()
        assert row == ([1, 4], "09:30", "A101")
        assert run("SELECT count(*) FROM class_sessions").scalar_one() == 5
