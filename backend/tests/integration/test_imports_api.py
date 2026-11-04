import io
from datetime import datetime

import pytest
from sqlalchemy import func, select

from app.lib import timeutil
from app.lib.timeutil import TZ
from app.models import ClassSession, Exam, Semester, Subject
from tests.integration.helpers import create_semester
from tests.ocr_helpers import box, png_bytes

NOW = datetime(2026, 11, 3, 9, 0, tzinfo=TZ)
SIZE = (2000, 1000)


def grid_boxes():
    labels = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "CN"]
    boxes = [box("Tháng 11/2026", 1950, 250, w=150)]
    for i, label in enumerate(labels):
        x = 200 + 250 * i
        boxes += [box(f"{2 + i:02d}", x - 40, 200, w=30, h=26), box(label, x, 205, w=60)]
    cells = [
        (0, 300, ["Giải tích 1", "06:45 - 09:25 (Tiết 1-3)", "MAT1101-1-1-26(N01)", "Phòng: A2-301", "GV: ThS. An"]),
        (1, 300, ["Triết học", "20:00 - 21:30", "E-Learning"]),
        (3, 300, ["Vật lý", "13:00 - 15:40", "Phòng: B1-101"]),
    ]  # fmt: skip
    for col, y, lines in cells:
        boxes += [box(t, 160 + 250 * col, y + 22 * k, w=200) for k, t in enumerate(lines)]
    return boxes


@pytest.fixture(autouse=True)
def stub_ocr(monkeypatch):
    monkeypatch.setattr(timeutil, "now", lambda: NOW)
    monkeypatch.setattr("app.ocr.reader.read_boxes", lambda image: grid_boxes())


def recognize(client, data=None, name="a.png", query=""):
    data = png_bytes(SIZE) if data is None else data
    return client.post(
        f"/api/imports/recognize{query}",
        data={"image": (io.BytesIO(data), name)},
        content_type="multipart/form-data",
    )


def counts(db_session):
    return {
        model.__name__: db_session.scalar(select(func.count()).select_from(model))
        for model in (Subject, ClassSession, Semester, Exam)
    }


def commit_body(preview, **extra):
    rows = []
    for row in preview["rows"]:
        for field in row["fields"].values():
            field["certain"] = True
        rows.append({**row, "tag_ids": [], **extra})
    return {"kind": "week_schedule", "rows": rows}


def test_recognize_returns_preview_and_writes_nothing(client, db_session):
    create_semester(client, "2026-09-07", "2026-12-20")
    before = counts(db_session)
    resp = recognize(client)
    assert resp.status_code == 200
    preview = resp.get_json()
    assert preview["kind"] == "week_schedule" and len(preview["rows"]) == 3
    assert preview["rows"][0]["semester_id"] is not None
    assert counts(db_session) == before


def test_image_validation(client):
    assert recognize(client, b"khong phai anh", "x.txt").status_code == 415
    big = b"0" * (20 * 1024 * 1024 + 10)
    assert recognize(client, big).status_code == 413
    assert client.post("/api/imports/recognize").status_code == 400
    assert recognize(client, query="?kind=sai").status_code == 400


def test_commit_creates_weekly_and_once_subjects(client, db_session):
    create_semester(client, "2026-09-07", "2026-12-20")
    preview = recognize(client).get_json()
    body = commit_body(preview)
    body["rows"][1]["repeat"] = {"mode": "once", "until": None}
    resp = client.post("/api/imports/commit", json=body)
    assert resp.status_code == 200, resp.get_json()
    result = resp.get_json()
    assert result["created_subjects"] == 3 and result["skipped_duplicates"] == 0
    weekly = db_session.scalars(select(Subject).where(Subject.name == "Giải tích 1")).one()
    assert weekly.weekdays == [1] and weekly.class_code == "MAT1101-1-1-26(N01)"
    assert len(weekly.sessions) == 7  # các Thứ Hai từ 02/11 tới hết học kỳ 20/12
    once = db_session.scalars(select(Subject).where(Subject.name == "Triết học")).one()
    assert len(once.sessions) == 1


def test_recommit_creates_nothing_new(client, db_session):
    create_semester(client, "2026-09-07", "2026-12-20")
    preview = recognize(client).get_json()
    first = client.post("/api/imports/commit", json=commit_body(preview)).get_json()
    after_first = counts(db_session)
    second = client.post("/api/imports/commit", json=commit_body(preview)).get_json()
    assert (
        second["created_subjects"] == 0
        and second["skipped_duplicates"] == first["created_subjects"]
    )
    assert counts(db_session) == after_first
    # nhận diện lại: các dòng đã có đều bị bỏ chọn
    assert not any(r["selected"] for r in recognize(client).get_json()["rows"])


def test_uncertain_required_field_rejects_whole_commit(client, db_session):
    create_semester(client, "2026-09-07", "2026-12-20")
    body = commit_body(recognize(client).get_json())
    body["rows"][1]["fields"]["name"]["certain"] = False
    before = counts(db_session)
    resp = client.post("/api/imports/commit", json=body)
    assert resp.status_code == 400
    assert "rows[1].name" in resp.get_json()["error"]["fields"]
    assert counts(db_session) == before  # không lưu gì


def test_row_without_semester_is_rejected(client):
    body = commit_body(recognize(client).get_json())  # chưa có học kỳ nào
    resp = client.post("/api/imports/commit", json=body)
    assert resp.status_code == 400 and "rows[0].semester_id" in resp.get_json()["error"]["fields"]


def test_unselected_rows_are_ignored(client, db_session):
    create_semester(client, "2026-09-07", "2026-12-20")
    body = commit_body(recognize(client).get_json())
    for row in body["rows"][1:]:
        row["selected"] = False
    assert client.post("/api/imports/commit", json=body).get_json()["created_subjects"] == 1


@pytest.mark.parametrize("accepted, subjects", [(True, 1), (False, 3)])
def test_merge_group(client, db_session, accepted, subjects):
    create_semester(client, "2026-09-07", "2026-12-20")
    preview = recognize(client).get_json()
    base = preview["rows"][0]
    rows = []
    for day in ("2026-11-02", "2026-11-09", "2026-11-16"):
        row = {**base, "fields": {k: dict(v) for k, v in base["fields"].items()}}
        row["fields"]["date"]["value"] = day
        row.update(merge_group="g1", merge_accepted=accepted, tag_ids=[])
        for f in row["fields"].values():
            f["certain"] = True
        rows.append(row)
    result = client.post(
        "/api/imports/commit", json={"kind": "week_schedule", "rows": rows}
    ).get_json()
    assert result["created_subjects"] == subjects
