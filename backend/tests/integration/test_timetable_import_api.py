"""API nhập thời khoá biểu PDF: xem trước không ghi gì, lỗi đúng mã, lưu trong một transaction."""

import io
from datetime import date, timedelta

from sqlalchemy import func, select

from app.models import ClassSession, Semester, Subject
from tests.ocr_helpers import load_pdf

PREVIEW = "/api/imports/timetable-pdf/preview"
COMMIT = "/api/imports/timetable-pdf/commit"


def upload(client, data: bytes, name="tkb.pdf", url=PREVIEW):
    return client.post(
        url, data={"file": (io.BytesIO(data), name)}, content_type="multipart/form-data"
    )


def preview(client, name="tkb-synthetic-01.pdf"):
    response = upload(client, load_pdf(name))
    assert response.status_code == 200, response.get_json()
    return response.get_json()


def payload(prev, *, only=None):
    """Commit payload từ bản xem trước (như giao diện gửi lại)."""
    subjects = prev["subjects"] if only is None else [prev["subjects"][i] for i in only]
    sem = prev["semester"]
    return {
        "semester": {
            "choice": "create",
            "name": sem["suggested_name"],
            "start_date": sem["start_date"],
            "end_date": sem["end_date"],
        },
        "subjects": [
            {
                "course_code": s["course_code"],
                "name": s["name"],
                "class_code": s["class_code"],
                "credits": s["credits"],
                "schedules": [
                    {
                        "weekdays": [r["weekday"]],
                        "start_date": r["start_date"],
                        "end_date": r["end_date"],
                        "shift": r["shift"],
                        "start_time": None if r["shift"] else r["start_time"],
                        "end_time": None if r["shift"] else r["end_time"],
                        "period_from": r["period_from"],
                        "period_to": r["period_to"],
                        "room": r["room"],
                    }
                    for r in s["schedules"]
                    if r["selected"]
                ],
            }
            for s in subjects
        ],
    }


def count(db_session, model):
    return db_session.scalar(select(func.count()).select_from(model))


def weekday_count(weekday: int, start: date, end: date) -> int:
    return sum(
        1 for n in range((end - start).days + 1) if (start + timedelta(n)).isoweekday() == weekday
    )


def test_preview_khong_ghi_gi(client, db_session):
    before = (
        count(db_session, Semester),
        count(db_session, Subject),
        count(db_session, ClassSession),
    )
    prev = preview(client)
    assert len(prev["subjects"]) == 8
    assert sum(len(s["schedules"]) for s in prev["subjects"]) == 17
    assert prev["semester"]["choice"] == "create"
    assert before == (
        count(db_session, Semester),
        count(db_session, Subject),
        count(db_session, ClassSession),
    )


def test_ma_loi(client):
    assert upload(client, b"%PDF-1.4 " + b"x" * 50 + b"\x00").status_code in (422,)
    r = upload(client, b"khong phai pdf")
    assert (r.status_code, r.get_json()["error"]["code"]) == (415, "unsupported_file")
    r = upload(client, load_pdf("tkb-encrypted.pdf"))
    assert (r.status_code, r.get_json()["error"]["code"]) == (422, "pdf_encrypted")
    r = upload(client, load_pdf("tkb-no-text.pdf"))
    assert (r.status_code, r.get_json()["error"]["code"]) == (422, "pdf_no_text")
    r = upload(client, load_pdf("tkb-not-timetable.pdf"))
    assert (r.status_code, r.get_json()["error"]["code"]) == (422, "pdf_not_timetable")
    r = upload(client, b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ngarbage")
    assert (r.status_code, r.get_json()["error"]["code"]) == (422, "pdf_unreadable")


def test_file_qua_lon(client, monkeypatch):
    monkeypatch.setattr("app.api.timetable_import.MAX_IMAGE_BYTES", 1000)
    r = upload(client, b"%PDF-" + b"0" * 2000)
    assert (r.status_code, r.get_json()["error"]["code"]) == (413, "file_too_large")


def test_commit_tao_hoc_ky_mon_va_buoi(client, db_session):
    prev = preview(client)
    response = client.post(COMMIT, json=payload(prev))
    assert response.status_code == 200, response.get_json()
    body = response.get_json()
    assert body["created_subjects"] == 8
    semester = db_session.get(Semester, body["semester_id"])
    assert (semester.name, semester.start_date, semester.end_date) == (
        "HK2 2026–2027",
        date(2026, 11, 30),
        date(2027, 2, 28),
    )
    expected = sum(
        weekday_count(
            r["weekday"], date.fromisoformat(r["start_date"]), date.fromisoformat(r["end_date"])
        )
        for s in prev["subjects"]
        for r in s["schedules"]
    )
    assert body["created_sessions"] == expected == count(db_session, ClassSession)
    gap = db_session.scalar(
        select(func.count())
        .select_from(ClassSession)
        .where(ClassSession.date.between(date(2027, 1, 25), date(2027, 2, 14)))
    )
    assert gap == 0


def test_chi_luu_phan_duoc_chon(client, db_session):
    prev = preview(client)
    body = payload(prev, only=[0, 1])
    body["subjects"][0]["schedules"] = body["subjects"][0]["schedules"][:1]
    response = client.post(COMMIT, json=body)
    assert response.status_code == 200
    assert count(db_session, Subject) == 2
    assert count(db_session, ClassSession) == response.get_json()["created_sessions"]


def test_loi_giua_chung_khong_luu_gi(client, db_session):
    prev = preview(client)
    body = payload(prev)
    body["subjects"][3]["schedules"][0]["end_date"] = "2026-01-01"  # ngoài học kỳ / ngược
    before = (
        count(db_session, Semester),
        count(db_session, Subject),
        count(db_session, ClassSession),
    )
    response = client.post(COMMIT, json=body)
    assert response.status_code == 400
    fields = response.get_json()["error"]["fields"]
    assert any(key.startswith("subjects[3].schedules[0].") for key in fields)
    assert before == (
        count(db_session, Semester),
        count(db_session, Subject),
        count(db_session, ClassSession),
    )


def test_hai_mon_trung_gio_co_canh_bao(client):
    prev = preview(client)
    body = payload(prev, only=[0])
    twin = {**body["subjects"][0], "name": "Môn trùng giờ", "class_code": "X", "course_code": "X1"}
    body["subjects"].append(twin)
    response = client.post(COMMIT, json=body)
    assert response.status_code == 200
    assert response.get_json()["warnings"]
