"""Migration 0012: cột Kanban, bảng đính kèm, cài đặt mới (feature 005, T007)."""

import pytest
import sqlalchemy as sa
from flask_migrate import downgrade, upgrade

from app.extensions import db


@pytest.fixture
def app_at_0011(isolated_app):
    with isolated_app.app_context():
        db.session.remove()
        db.engine.dispose()
        downgrade(revision="0011_periods_canonical_names")
        db.engine.dispose()
        run("DELETE FROM tasks")
    yield isolated_app
    with isolated_app.app_context():
        db.session.remove()
        db.engine.dispose()
        upgrade()
        db.session.remove()


def run(sql, **params):
    with db.engine.begin() as conn:
        return conn.execute(sa.text(sql), params)


def seed_tasks():
    lists = [r[0] for r in run("SELECT id FROM task_lists ORDER BY id LIMIT 2")]
    run(
        "INSERT INTO tasks (id, list_id, title, due_date, priority, completed_at, deleted_at) VALUES "
        "(1, :a, 'Muộn', '2026-12-30', 2, NULL, NULL), "
        "(2, :b, 'Sớm', '2026-11-20', 2, NULL, NULL), "
        "(3, :a, 'Không hạn', NULL, 1, NULL, NULL), "
        "(4, :a, 'Xong cũ', NULL, 2, '2026-11-01 10:00+07', NULL), "
        "(5, :b, 'Xong mới', NULL, 2, '2026-11-09 10:00+07', NULL), "
        "(6, :a, 'Thùng rác', '2026-11-01', 2, NULL, '2026-11-10 10:00+07')",
        a=lists[0],
        b=lists[-1],
    )


def test_upgrade_dat_thu_tu_va_giu_du_lieu(app_at_0011):
    with app_at_0011.app_context():
        seed_tasks()
        upgrade()
        db.engine.dispose()
        rows = run("SELECT id, in_progress, board_rank, subject_id FROM tasks ORDER BY id").all()
        ranks = {r.id: r.board_rank for r in rows}
        assert all(r.in_progress is False and r.subject_id is None for r in rows)
        # Chưa xong: hạn gần trước (2 < 1), task không hạn ở cuối; thùng rác (hạn 01/11) đứng đầu nhóm.
        todo = [i for i in sorted((1, 2, 3, 6), key=ranks.get)]
        assert todo == [6, 2, 1, 3]
        assert len({ranks[i] for i in (1, 2, 3, 6)}) == 4  # không trùng thứ tự
        # Đã xong: mới nhất trước.
        assert ranks[5] < ranks[4]
        settings = run("SELECT attachment_max_mb, backup_attachments_warn_mb FROM settings").one()
        assert tuple(settings) == (50, 1024)
        tables = {r[0] for r in run("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")}
        assert {"attachments", "attachment_blobs"} <= tables


def test_rang_buoc_va_downgrade(app_at_0011):
    with app_at_0011.app_context():
        upgrade()
        db.engine.dispose()
        with pytest.raises(sa.exc.IntegrityError):
            run("UPDATE settings SET attachment_max_mb = 501")
        with pytest.raises(sa.exc.IntegrityError):
            run("INSERT INTO attachment_blobs (sha256, size) VALUES ('ABC', 1)")
        run("INSERT INTO attachment_blobs (sha256, size) VALUES (repeat('a', 64), 3)")
        with pytest.raises(sa.exc.IntegrityError):  # không gắn vào nơi nào
            run("INSERT INTO attachments (blob_sha256, display_name) VALUES (repeat('a', 64), 'x')")
        downgrade(revision="0011_periods_canonical_names")
        db.engine.dispose()
        columns = {
            r[0]
            for r in run(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'tasks'"
            )
        }
        assert not {"in_progress", "board_rank", "subject_id"} & columns
