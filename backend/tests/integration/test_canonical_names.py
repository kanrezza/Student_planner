"""Tên môn chuẩn từ PDF giúp sửa tên khi nhập ảnh (US5, SC-007)."""

import io
from datetime import datetime

import pytest
from sqlalchemy import select

from app.lib import timeutil
from app.lib.timeutil import TZ
from app.models import CanonicalSubjectName, Subject
from tests.integration.test_timetable_import_api import COMMIT, payload, preview
from tests.ocr_helpers import load_boxes, png_bytes

NOW = datetime(2026, 11, 10, 20, 30, tzinfo=TZ)
BOXES, SIZE = load_boxes("real-week-02")
CANONICAL = {
    "Xử lý ngôn ngữ tự nhiên",
    "Giao diện người máy",
    "Trực quan hoá dữ liệu",
    "Tích hợp và phân tích dữ liệu lớn",
    "Bóng đá",
}


@pytest.fixture(autouse=True)
def fixed_now(monkeypatch):
    monkeypatch.setattr(timeutil, "now", lambda: NOW)


def commit_pdf(client):
    prev = preview(client)
    response = client.post(COMMIT, json=payload(prev))
    assert response.status_code == 200, response.get_json()


def recognize(client, monkeypatch, boxes=BOXES):
    monkeypatch.setattr("app.ocr.reader.read_boxes", lambda image: boxes)
    return client.post(
        "/api/imports/recognize",
        data={"image": (io.BytesIO(png_bytes(SIZE)), "tuan.png")},
        content_type="multipart/form-data",
    ).get_json()


def test_commit_pdf_ghi_ten_chuan_khong_trung(client, db_session):
    commit_pdf(client)
    names = {n["name"] for n in client.get("/api/canonical-names").get_json()}
    assert names == CANONICAL
    assert db_session.scalars(select(CanonicalSubjectName)).all().__len__() == 5
    # Nhập lại không ghi trùng theo lower(name).
    client.post(
        COMMIT,
        json={
            **payload(preview(client)),
            "semester": {
                "choice": "use",
                "semester_id": db_session.scalars(select(Subject)).first().semester_id,
            },
        },
    )
    assert len(client.get("/api/canonical-names").get_json()) == 5


def test_ten_chuan_con_khi_mon_bi_xoa_va_xoa_het(client, db_session):
    commit_pdf(client)
    for subject in db_session.scalars(select(Subject)).all():
        assert client.delete(f"/api/subjects/{subject.id}").status_code == 204
    assert len(client.get("/api/canonical-names").get_json()) == 5
    assert client.delete("/api/canonical-names").status_code == 204
    assert client.get("/api/canonical-names").get_json() == []


def test_nhap_anh_sua_ten_theo_ten_chuan(client, monkeypatch):
    before = recognize(client, monkeypatch)
    commit_pdf(client)
    after = recognize(client, monkeypatch)
    names = [r["fields"]["name"]["value"] for r in after["rows"]]
    assert len(names) == 7
    assert all(n in CANONICAL for n in names), names
    fixed = [
        r
        for r in after["rows"]
        if r["fields"]["name"].get("reason") == "Đã sửa theo thời khoá biểu"
    ]
    assert fixed  # có tên được sửa so với khi chưa có tên chuẩn
    assert [r["fields"]["name"]["value"] for r in before["rows"]] != names


def test_ten_khong_du_giong_giu_nguyen(client, monkeypatch):
    commit_pdf(client)
    from app.ocr.preview import _fix_weak_name

    assert _fix_weak_name("Hoá học đại cương", sorted(CANONICAL)) == ("Hoá học đại cương", False)
