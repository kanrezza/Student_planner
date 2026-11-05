"""Khung test: database test riêng (`lichhoc_test`), chạy migration một lần mỗi phiên test,
mỗi test chạy trong transaction rồi rollback (dữ liệu mặc định từ migration luôn còn nguyên)."""

import pytest
from flask_migrate import upgrade
from sqlalchemy import text
from sqlalchemy.orm import scoped_session, sessionmaker

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
        # Session thuần của SQLAlchemy gắn chặt vào `connection` (session của Flask-SQLAlchemy
        # tự chọn engine riêng và bỏ qua `bind`, làm dữ liệu test bị ghi thật).
        session = scoped_session(
            sessionmaker(bind=connection, join_transaction_mode="create_savepoint")
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


@pytest.fixture(scope="module")
def isolated_app(tmp_path_factory):
    """App chạy trên database riêng `lichhoc_restore_test`, KHÔNG bọc trong transaction của test.

    `pg_restore` cần khoá độc quyền nên không chạy được khi test đang giữ transaction mở
    (feature 003, khôi phục). Mỗi module test có một database mới, xoá khi xong.
    """
    import sqlalchemy as sa
    from sqlalchemy.engine import make_url

    name = "lichhoc_restore_test"
    base = make_url(TEST_DATABASE_URL)
    admin = sa.create_engine(base.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(sa.text(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)"))
        conn.execute(sa.text(f"CREATE DATABASE {name}"))
    flag = tmp_path_factory.mktemp("bao-tri") / "restoring"
    app = create_app(
        {
            "SQLALCHEMY_DATABASE_URI": base.set(database=name).render_as_string(hide_password=False),
            "TESTING": True,
            "RESTORE_FLAG_PATH": str(flag),
        }
    )
    with app.app_context():
        upgrade()
        db.session.remove()
    yield app
    with app.app_context():
        db.session.remove()
        db.engine.dispose()
    with admin.connect() as conn:
        conn.execute(sa.text(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)"))
    admin.dispose()
