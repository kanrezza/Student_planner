"""SC-006: họ tên, mã sinh viên, lớp trong PDF không xuất hiện ở phản hồi, log hay CSDL."""

import json
import logging
import os
import tempfile

from sqlalchemy import text

from tests.integration.test_timetable_import_api import COMMIT, payload, upload
from tests.ocr_helpers import FIXTURES, load_pdf

SECRETS = json.loads((FIXTURES / "tkb-synthetic-01.expected.json").read_text("utf-8"))[
    "must_not_appear"
]


def _tmp_files() -> set[str]:
    return set(os.listdir(tempfile.gettempdir()))


def _db_text(db_session) -> str:
    """Mọi cột văn bản của mọi bảng trong schema public, gộp thành một chuỗi."""
    parts = []
    tables = db_session.execute(
        text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    ).scalars()
    for table in tables:
        rows = db_session.execute(text(f'SELECT t::text FROM "{table}" t')).scalars()
        parts.extend(rows)
    return "\n".join(parts)


def test_khong_ro_ri_thong_tin_ca_nhan(client, db_session, caplog):
    caplog.set_level(logging.DEBUG)
    files_before = _tmp_files()
    response = upload(client, load_pdf("tkb-synthetic-01.pdf"))
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    committed = client.post(COMMIT, json=payload(response.get_json()))
    assert committed.status_code == 200
    body += committed.get_data(as_text=True)
    database = _db_text(db_session)
    logs = caplog.text
    for secret in SECRETS:
        assert secret not in body
        assert secret not in logs
        assert secret not in database
    assert _tmp_files() == files_before
