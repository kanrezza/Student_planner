"""Hàm SQL vn_fold phải gập chữ giống hệt foldVi ở frontend (feature 003, research R15)."""

import json
from pathlib import Path

import pytest
from sqlalchemy import text

FIXTURE_NAME = "vi-fold-pairs.json"
# Trong container, scripts/test.sh mount frontend/tests/fixtures vào /frontend-fixtures.
FIXTURE_DIRS = [
    Path("/frontend-fixtures"),
    Path(__file__).resolve().parents[3] / "frontend/tests/fixtures",
]


def load_pairs() -> list[list[str]]:
    for directory in FIXTURE_DIRS:
        if (directory / FIXTURE_NAME).exists():
            return json.loads((directory / FIXTURE_NAME).read_text(encoding="utf-8"))
    pytest.skip("Không thấy frontend/tests/fixtures/vi-fold-pairs.json")


def test_vn_fold_khop_foldVi_voi_moi_chu_co_dau(db_session):
    pairs = load_pairs()
    assert len(pairs) >= 134
    for original, expected in pairs:
        got = db_session.execute(text("SELECT vn_fold(:s)"), {"s": original}).scalar()
        assert got == expected, original


def test_vn_fold_cau_day_du_va_null(db_session):
    fold = lambda s: db_session.execute(text("SELECT vn_fold(:s)"), {"s": s}).scalar()  # noqa: E731
    assert fold("Nộp bài QTDA - ĐỒ ÁN") == "nop bai qtda - do an"
    assert db_session.execute(text("SELECT vn_fold(NULL)")).scalar() == ""
