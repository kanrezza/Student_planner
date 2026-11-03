"""Lịch Học Cá Nhân — Flask REST API."""

from pathlib import Path

from flask import Flask

from app import config
from app.api.errors import register_error_handlers
from app.extensions import db, migrate

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
    register_error_handlers(app)
    return app


def register_blueprints(app: Flask) -> None:
    """Mọi API nằm dưới /api. Blueprint của từng user story được thêm vào danh sách này."""
    from app.api.health import bp as health_bp
    from app.api.lists import bp as lists_bp
    from app.api.semesters import bp as semesters_bp
    from app.api.settings import bp as settings_bp
    from app.api.subjects import bp as subjects_bp
    from app.api.tasks import bp as tasks_bp
    from app.api.today import bp as today_bp

    for bp in (health_bp, settings_bp, tasks_bp, lists_bp, semesters_bp, subjects_bp, today_bp):
        app.register_blueprint(bp, url_prefix="/api")
