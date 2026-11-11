"""Nhập lại PDF: nhận ra môn đã có, không tạo trùng, chỉ cập nhật phần tương lai (US3, SC-005)."""

from datetime import date, datetime, time

import pytest
from sqlalchemy import func, select

from app.lib import timeutil
from app.lib.timeutil import TZ
from app.models import ClassSession, Subject
from tests.factories import make_semester, make_subject
from tests.integration.test_timetable_import_api import COMMIT, count, payload, preview

NOW = datetime(2026, 12, 15, 10, 0, tzinfo=TZ)  # giữa học kỳ; thứ Hai 14/12 đã qua, 21/12 chưa tới


@pytest.fixture(autouse=True)
def fixed_now(monkeypatch):
    monkeypatch.setattr(timeutil, "now", lambda: NOW)


def first_import(client):
    prev = preview(client)
    body = payload(prev)
    result = client.post(COMMIT, json=body).get_json()
    return prev, body, result


def football(db_session) -> Subject:
    return db_session.scalars(select(Subject).where(Subject.name == "Bóng đá")).one()


def reimport_body(body, semester_id):
    return {**body, "semester": {"choice": "use", "semester_id": semester_id}}


def test_nhap_lai_cung_file_khong_tao_trung(client, db_session):
    _, body, first = first_import(client)
    subjects, sessions = count(db_session, Subject), count(db_session, ClassSession)
    prev2 = preview(client)
    assert prev2["semester"]["choice"] == "use"
    assert {s["status"] for s in prev2["subjects"]} == {"unchanged"}
    assert not any(s["selected"] for s in prev2["subjects"])
    response = client.post(COMMIT, json=reimport_body(body, first["semester_id"]))
    assert response.status_code == 200, response.get_json()
    result = response.get_json()
    assert result["created_subjects"] == 0 and result["created_sessions"] == 0
    assert result["updated_sessions"] == 0 and result["skipped_sessions"] > 0
    assert (count(db_session, Subject), count(db_session, ClassSession)) == (subjects, sessions)


def test_doi_phong_chi_ap_dung_buoi_tuong_lai(client, db_session):
    _, body, first = first_import(client)
    # Một buổi tương lai sửa phòng riêng và một buổi tương lai đã huỷ: phải giữ nguyên.
    sessions = {s.date: s for s in football(db_session).sessions}
    sessions[date(2026, 12, 28)].room = "Phòng riêng"
    sessions[date(2026, 12, 28)].room_overridden = True
    sessions[date(2027, 1, 4)].is_cancelled = True
    db_session.flush()
    football_in = next(s for s in body["subjects"] if s["name"] == "Bóng đá")
    for rule in football_in["schedules"]:
        rule["room"] = "Sân mới"
    result = client.post(COMMIT, json=reimport_body(body, first["semester_id"])).get_json()
    assert result["updated_subjects"] == 8 and result["created_subjects"] == 0
    assert result["updated_sessions"] > 0
    db_session.expire_all()
    rooms = {s.date: s.room for s in football(db_session).sessions}
    assert rooms[date(2026, 11, 30)] == "Sân bóng đá"  # đã qua
    assert rooms[date(2026, 12, 14)] == "Sân bóng đá"  # đã qua (hôm qua)
    assert rooms[date(2026, 12, 21)] == "Sân mới"  # tương lai
    assert rooms[date(2027, 2, 15)] == "Sân mới"
    assert rooms[date(2026, 12, 28)] == "Phòng riêng"  # sửa riêng giữ nguyên
    cancelled = next(s for s in football(db_session).sessions if s.date == date(2027, 1, 4))
    assert cancelled.is_cancelled  # buổi đã huỷ giữ như cũ


def test_buoi_ngoai_le_ngoai_lich_moi_duoc_giu(client, db_session):
    _, body, first = first_import(client)
    sessions = {s.date: s for s in football(db_session).sessions}
    sessions[date(2027, 1, 18)].is_cancelled = True
    db_session.flush()
    football_in = next(s for s in body["subjects"] if s["name"] == "Bóng đá")
    first_rule = next(r for r in football_in["schedules"] if r["start_date"] == "2026-11-30")
    first_rule["end_date"] = "2027-01-10"  # lịch mới kết thúc sớm hơn
    response = client.post(COMMIT, json=reimport_body(body, first["semester_id"]))
    assert response.status_code == 200, response.get_json()
    result = response.get_json()
    assert result["kept_exception_sessions"] == 1
    assert any(
        w["code"] == "kept_exception_sessions" and "18/01" in w["message"]
        for w in result["warnings"]
    )
    db_session.expire_all()
    kept = next(s for s in football(db_session).sessions if s.date == date(2027, 1, 18))
    assert kept.is_cancelled and kept.schedule_id is None
    assert date(2027, 1, 25) not in {s.date for s in football(db_session).sessions}
    assert date(2027, 1, 11) not in {s.date for s in football(db_session).sessions}


def test_mon_tao_tu_anh_duoc_khop_va_bo_sung(client, db_session):
    semester = make_semester(db_session, "HK2 2026–2027", date(2026, 11, 30), date(2027, 2, 28))
    existing = make_subject(
        db_session, semester, name="Bong da", class_code="2-2-26(n01)",
        weekdays=[1], start_time=time(9, 30), end_time=time(12, 10),
        start_date=date(2026, 11, 30), end_date=date(2027, 1, 24), room="Sân bóng đá",
    )  # fmt: skip
    prev = preview(client)
    assert prev["semester"]["choice"] == "use"
    match = next(s for s in prev["subjects"] if s["name"] == "Bóng đá")
    assert match["status"] == "changed" and match["existing_subject_id"] == existing.id
    assert {d["field"] for d in match["diff"]} >= {"Tên", "Mã học phần", "Số tín chỉ"}
    body = payload(prev, only=[prev["subjects"].index(match)])
    body["semester"] = {"choice": "use", "semester_id": semester.id}
    body["subjects"][0]["existing_subject_id"] = existing.id
    result = client.post(COMMIT, json=body).get_json()
    assert (result["created_subjects"], result["updated_subjects"]) == (0, 1)
    assert count(db_session, Subject) == 1
    db_session.expire_all()
    updated = db_session.get(Subject, existing.id)
    assert (updated.name, updated.course_code, updated.credits) == ("Bóng đá", "FFS701069", 1)
    assert len(updated.schedules) == 2


def test_mon_khong_co_trong_pdf_giu_nguyen(client, db_session):
    _, body, first = first_import(client)
    other = make_subject(
        db_session,
        db_session.get(Subject, football(db_session).id).semester,
        name="Môn khác",
        class_code="K1",
    )
    only = {
        **body,
        "subjects": [body["subjects"][0]],
        "semester": {"choice": "use", "semester_id": first["semester_id"]},
    }
    assert client.post(COMMIT, json=only).status_code == 200
    db_session.expire_all()
    assert db_session.get(Subject, other.id) is not None
    assert count(db_session, Subject) == 9


def test_existing_subject_id_sai_khoa(client, db_session):
    _, body, first = first_import(client)
    other = make_subject(
        db_session, football(db_session).semester, name="Môn khác", class_code="K1"
    )
    db_session.commit()
    bad = reimport_body(body, first["semester_id"])
    bad["subjects"][0]["existing_subject_id"] = other.id
    response = client.post(COMMIT, json=bad)
    assert response.status_code == 400
    assert "subjects[0].existing_subject_id" in response.get_json()["error"]["fields"]
    assert db_session.scalar(select(func.count()).select_from(Subject)) == 9
