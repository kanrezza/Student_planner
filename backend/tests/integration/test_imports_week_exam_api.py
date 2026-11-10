"""Ảnh tuần có ô "Lịch thi: …" (ảnh thật 30/11–06/12): buổi thi lưu thành Exam, không thành môn học."""

import io
from datetime import datetime

import pytest
from sqlalchemy import func, select

from app.lib import timeutil
from app.lib.timeutil import TZ
from app.models import Exam, Subject
from tests.integration.helpers import create_semester
from tests.ocr_helpers import load_boxes, png_bytes

NOW = datetime(2026, 11, 10, 20, 30, tzinfo=TZ)
BOXES, SIZE = load_boxes("real-week-02")


@pytest.fixture(autouse=True)
def stub_ocr(monkeypatch):
    monkeypatch.setattr(timeutil, "now", lambda: NOW)
    monkeypatch.setattr("app.ocr.reader.read_boxes", lambda image: BOXES)


def recognize(client):
    return client.post(
        "/api/imports/recognize",
        data={"image": (io.BytesIO(png_bytes(SIZE)), "tuan.png")},
        content_type="multipart/form-data",
    )


def confirmed(rows):
    for row in rows:
        for field in row["fields"].values():
            field["certain"] = True
    return rows


def test_week_image_returns_sessions_and_exam_separately(client):
    create_semester(client, "2026-08-17", "2026-12-20")
    preview = recognize(client).get_json()
    assert preview["kind"] == "week_schedule" and preview["month_year"]["value"] == "2026-12"
    assert len(preview["rows"]) == 7 and len(preview["exam_rows"]) == 1
    assert preview["exam_rows"][0]["fields"]["date"]["value"] == "2026-11-30"


def test_commit_saves_exam_with_the_week(client, db_session):
    create_semester(client, "2026-08-17", "2026-12-20")
    preview = recognize(client).get_json()
    rows = [{**r, "tag_ids": []} for r in confirmed(preview["rows"])]
    body = {
        "kind": "week_schedule",
        "rows": rows,
        "exam_rows": [{**r, "tag_ids": []} for r in confirmed(preview["exam_rows"])],
    }
    resp = client.post("/api/imports/commit", json=body)
    assert resp.status_code == 200, resp.get_json()
    result = resp.get_json()
    assert result["created_exams"] == 1
    exam = db_session.scalars(select(Exam)).one()
    assert (exam.date.isoformat(), exam.room) == ("2026-11-30", "A6-101.102 (PC)")
    # buổi thi không biến thành môn học
    assert (
        db_session.scalar(select(func.count()).select_from(Subject)) == result["created_subjects"]
    )
    assert not any("thi" in s.name.lower().split()[:1] for s in db_session.scalars(select(Subject)))


def test_invalid_exam_blocks_the_whole_commit(client, db_session):
    create_semester(client, "2026-08-17", "2026-12-20")
    preview = recognize(client).get_json()
    exams = confirmed(preview["exam_rows"])
    exams[0]["fields"]["end_time"]["value"] = "18:00"  # trước giờ bắt đầu 18:30
    body = {
        "kind": "week_schedule",
        "rows": [{**r, "tag_ids": []} for r in confirmed(preview["rows"])],
        "exam_rows": exams,
    }
    assert client.post("/api/imports/commit", json=body).status_code == 400
    assert db_session.scalar(select(func.count()).select_from(Subject)) == 0  # chưa ghi gì
