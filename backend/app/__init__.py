"""Lịch Học Cá Nhân — Flask REST API."""

import logging
from pathlib import Path

from flask import Flask

from app import config
from app.api.errors import register_error_handlers
from app.extensions import db, migrate

log = logging.getLogger(__name__)

MIGRATIONS_DIR = str(Path(__file__).resolve().parent.parent / "migrations")


def create_app(config_overrides: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(config.flask_config())
    if config_overrides:
        app.config.update(config_overrides)
    app.json.ensure_ascii = False  # trả tiếng Việt nguyên dạng, không \uXXXX

    from app import models  # noqa: F401  (đăng ký model với SQLAlchemy và Alembic)

    db.init_app(app)
    migrate.init_app(app, db, directory=MIGRATIONS_DIR)

    register_blueprints(app)
    from app import cli

    cli.register(app)
    register_error_handlers(app)
    purge_trash_on_startup(app)
    return app


def purge_trash_on_startup(app: Flask) -> None:
    """Xoá hẳn task ở Thùng rác quá 30 ngày khi backend khởi động (feature 002 research R6).

    Lỗi (ví dụ database chưa chạy migration khi gọi `flask db upgrade`) chỉ được ghi log.
    """
    if app.config.get("TESTING"):
        return
    from app.lib import timeutil
    from app.services.tasks import purge_expired_trash

    with app.app_context():
        try:
            purge_expired_trash(timeutil.now())
        except Exception as err:  # noqa: BLE001 — không được chặn việc khởi động
            log.warning("Bỏ qua dọn Thùng rác lúc khởi động: %s", err)
            db.session.rollback()
        finally:
            db.session.remove()


def register_blueprints(app: Flask) -> None:
    """Mọi API nằm dưới /api. Blueprint của từng user story được thêm vào danh sách này."""
    from app.api import (
        calendar,
        exams,
        health,
        imports,
        lists,
        semesters,
        sessions,
        settings,
        shifts,
        subjects,
        sync,
        tags,
        tasks,
        today,
    )

    modules = (health, settings, tasks, lists, semesters, subjects, today, sessions, calendar)
    for module in (*modules, exams, imports, shifts, tags, sync):
        app.register_blueprint(module.bp, url_prefix="/api")
