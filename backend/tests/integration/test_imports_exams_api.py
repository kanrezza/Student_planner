import io
from datetime import datetime

import pytest
from sqlalchemy import func, select

from app.lib import timeutil
from app.lib.timeutil import TZ
from app.models import ClassSession, Exam, Semester, Subject
from tests.ocr_helpers import load_boxes, png_bytes

NOW = datetime(2026, 11, 5, 9, 0, tzinfo=TZ)
BOXES, SIZE = load_boxes(
    "real-exam-01"
)  # bảng lịch thi thật, họ tên và mã SV đã thay bằng giá trị bịa


@pytest.fixture(autouse=True)
def stub_ocr(monkeypatch):
    monkeypatch.setattr(timeutil, "now", lambda: NOW)
    monkeypatch.setattr("app.ocr.reader.read_boxes", lambda image: BOXES)


def recognize(client, query=""):
    return client.post(
        f"/api/imports/recognize{query}",
        data={"image": (io.BytesIO(png_bytes(SIZE)), "lich-thi.png")},
        content_type="multipart/form-data",
    )


def counts(db_session):
    return [
        db_session.scalar(select(func.count()).select_from(m))
        for m in (Subject, ClassSession, Semester, Exam)
    ]


def confirm(preview):
    rows = preview["exam_rows"]
    for row in rows:
        for field in row["fields"].values():
            field["certain"] = True
    return {"kind": "exam_table", "exam_rows": rows}


def test_recognize_exam_table_hides_student_info(client, db_session):
    before = counts(db_session)
    resp = recognize(client)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["kind"] == "exam_table" and len(body["exam_rows"]) == 5
    text = resp.get_data(as_text=True)
    assert "Nguyễn Văn Test" not in text and "21010999" not in text
    assert body["exam_rows"][0]["fields"]["course_name"]["value"] == "Tối ưu hóa"
    assert counts(db_session) == before


def test_force_kind_when_unknown(client, monkeypatch):
    monkeypatch.setattr("app.ocr.reader.read_boxes", lambda image: [])
    assert recognize(client).get_json() == {"kind": "unknown"}
    forced = recognize(client, "?kind=exam_table").get_json()
    assert forced["kind"] == "exam_table" and forced["exam_rows"] == []


def test_commit_creates_exams_and_skips_duplicates(client, db_session):
    body = confirm(recognize(client).get_json())
    resp = client.post("/api/imports/commit", json=body)
    assert resp.status_code == 200, resp.get_json()
    assert resp.get_json()["created_exams"] == 5
    exams = client.get("/api/exams").get_json()["exams"]
    assert len(exams) == 5 and exams[0]["course_name"] == "Quản trị dự án công nghệ thông tin"
    assert exams[0]["tags"][0]["system_key"] == "exam"

    again = client.post("/api/imports/commit", json=body).get_json()
    assert again["created_exams"] == 0 and again["skipped_duplicates"] == 5
    assert len(client.get("/api/exams").get_json()["exams"]) == 5
    assert not any(r["selected"] for r in recognize(client).get_json()["exam_rows"])


def test_missing_required_field_is_rejected(client, db_session):
    body = confirm(recognize(client).get_json())
    body["exam_rows"][2]["fields"]["course_name"]["value"] = ""
    before = counts(db_session)
    resp = client.post("/api/imports/commit", json=body)
    assert resp.status_code == 400
    assert "exam_rows[2].course_name" in resp.get_json()["error"]["fields"]
    assert counts(db_session) == before


def test_past_rows_default_to_unselected_but_can_be_forced(client):
    preview = recognize(client).get_json()
    flags = {r["fields"]["course_name"]["value"]: r["is_past"] for r in preview["exam_rows"]}
    assert not any(flags.values())  # NOW = 05/11: mọi buổi còn ở tương lai
