"""Khung test: database test riêng (`lichhoc_test`), chạy migration một lần mỗi phiên test,
mỗi test chạy trong transaction rồi rollback (dữ liệu mặc định từ migration luôn còn nguyên)."""

import pytest
from flask_migrate import upgrade
from sqlalchemy import text

from app import create_app
from app.config import TEST_DATABASE_URL
from app.extensions import db


@pytest.fixture(scope="session")
def app():
    app = create_app({"SQLALCHEMY_DATABASE_URI": TEST_DATABASE_URL, "TESTING": True})
    with app.app_context():
        # Bắt đầu từ schema trống rồi chạy đúng các migration như môi trường thật.
        db.session.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        db.session.execute(text("CREATE SCHEMA public"))
        db.session.commit()
        upgrade()
        db.session.remove()
    yield app


@pytest.fixture
def db_session(app):
    """Session gắn với một transaction ngoài; `commit()` trong code chỉ giải phóng savepoint."""
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()
        session = db._make_scoped_session(
            {"bind": connection, "join_transaction_mode": "create_savepoint"}
        )
        original_session = db.session
        db.session = session
        try:
            yield session
        finally:
            session.remove()
            transaction.rollback()
            connection.close()
            db.session = original_session


@pytest.fixture
def client(app, db_session):
    return app.test_client()
