"""File đính kèm đi theo Thùng rác, xoá môn/buổi thi/học kỳ, đổi lịch môn (feature 005, US6)."""

import os
import time as clock
from datetime import datetime, timedelta

import pytest
from sqlalchemy import func, select

from app.lib import timeutil
from app.lib.timeutil import TZ
from app.models import Attachment, AttachmentBlob, Semester, Task
from app.services import attachments as service
from app.services import attachments_store as store
from app.services import tasks as task_service
from tests.factories import make_semester, make_subject
from tests.integration.helpers import create_semester, create_subject, sessions_of
from tests.integration.test_attachments_api import one, owners, store_files, upload  # noqa: F401
from tests.integration.test_exams_api import make_exam
from tests.integration.test_task_status_api import create

NOW = datetime(2026, 11, 11, 10, 0, tzinfo=TZ)


@pytest.fixture(autouse=True)
def fixed_now(monkeypatch):
    monkeypatch.setattr(timeutil, "now", lambda: NOW)


def blobs(db_session):
    return db_session.scalar(select(func.count()).select_from(AttachmentBlob))


def listing(client, owner_type, owner_id):
    return client.get(f"/api/attachments?owner_type={owner_type}&owner_id={owner_id}")


def test_thung_rac_an_file_khoi_phuc_thi_hien_lai(client, owners, db_session):  # noqa: F811
    a = one(client, "task", owners["task"], "de-cuong.pdf")
    one(client, "task", owners["task"], "anh-nho.png")
    stats_before = client.get("/api/attachments/stats").get_json()
    client.delete(f"/api/tasks/{owners['task']}")
    assert client.get(f"/api/attachments/{a['id']}").status_code == 404
    assert listing(client, "task", owners["task"]).status_code == 400  # owner_not_found
    stats = client.get("/api/attachments/stats").get_json()
    assert stats["attachment_count"] == 0 and blobs(db_session) == 2  # blob vẫn được giữ
    assert stats_before["attachment_count"] == 2
    client.post(f"/api/tasks/{owners['task']}/restore")
    assert [x["display_name"] for x in listing(client, "task", owners["task"]).get_json()] == [
        "de-cuong.pdf",
        "anh-nho.png",
    ]
    assert client.get(f"/api/attachments/{a['id']}").status_code == 200


def test_xoa_han_task_don_blob_tru_noi_khac_dung(client, owners, db_session, attachments_dir):  # noqa: F811
    shared = upload(client, "task", owners["task"], ("x.pdf", b"chung")).get_json()["attachments"][
        0
    ]
    upload(client, "subject", owners["subject"], ("x.pdf", b"chung"))
    one(client, "task", owners["task"], "anh-nho.png")
    client.delete(f"/api/tasks/{owners['task']}")
    assert client.delete(f"/api/tasks/{owners['task']}?permanent=true").status_code == 204
    assert blobs(db_session) == 1  # chỉ còn nội dung "chung" (môn còn dùng)
    assert len(store_files(attachments_dir)) == 1
    assert db_session.get(Attachment, shared["id"]) is None


def test_don_thung_rac_va_het_han_30_ngay_don_file(client, db_session, attachments_dir):
    first, second = create(client, "A"), create(client, "B")
    one(client, "task", first["id"], "de-cuong.pdf")
    one(client, "task", second["id"], "anh-nho.png")
    client.delete(f"/api/tasks/{first['id']}")
    client.delete(f"/api/tasks/{second['id']}")
    db_session.get(Task, second["id"]).deleted_at = NOW - timedelta(days=31)
    db_session.commit()
    assert task_service.purge_expired_trash(NOW) == 1
    assert blobs(db_session) == 1  # task còn trong hạn 30 ngày giữ file
    assert client.delete("/api/trash").get_json() == {"deleted": 1}
    assert blobs(db_session) == 0 and store_files(attachments_dir) == []


def test_xoa_mon_can_xac_nhan_khi_co_file(client, owners, db_session, attachments_dir):  # noqa: F811
    one(client, "subject", owners["subject"], "de-cuong.pdf")
    one(client, "session", owners["session"], "anh-nho.png")
    response = client.delete(f"/api/subjects/{owners['subject']}")
    assert response.status_code == 409
    error = response.get_json()["error"]
    assert error["code"] == "confirm_required" and error["details"]["attachment_count"] == 2
    assert blobs(db_session) == 2
    assert client.delete(f"/api/subjects/{owners['subject']}?confirm=true").status_code == 204
    assert blobs(db_session) == 0 and store_files(attachments_dir) == []


def test_xoa_mon_khong_co_file_khong_can_xac_nhan(client, db_session):
    subject = make_subject(db_session, make_semester(db_session))
    db_session.commit()
    assert client.delete(f"/api/subjects/{subject.id}").status_code == 204


def test_xoa_buoi_thi_can_xac_nhan(client, owners, db_session):  # noqa: F811
    one(client, "exam", owners["exam"], "de-cuong.pdf")
    one(client, "exam", owners["exam"], "anh-nho.png")
    response = client.delete(f"/api/exams/{owners['exam']}")
    assert response.status_code == 409
    assert response.get_json()["error"]["details"]["attachment_count"] == 2
    assert client.delete(f"/api/exams/{owners['exam']}?confirm=true").status_code == 204
    assert blobs(db_session) == 0
    bare = make_exam(client)["exam"]["id"]
    assert client.delete(f"/api/exams/{bare}").status_code == 204


def test_xoa_hoc_ky_can_xac_nhan_nhu_cu_va_nem_so_file(client, owners, db_session):  # noqa: F811
    one(client, "subject", owners["subject"], "de-cuong.pdf")
    semester = db_session.scalars(select(Semester)).first()
    response = client.delete(f"/api/semesters/{semester.id}")
    assert response.status_code == 409
    details = response.get_json()["error"]["details"]
    assert details["subject_count"] == 1 and details["attachment_count"] == 1
    assert client.delete(f"/api/semesters/{semester.id}?confirm=true").status_code == 204
    assert blobs(db_session) == 0


def test_thu_hep_hoc_ky_lam_mat_mon_bao_so_file(client, owners, db_session):  # noqa: F811
    one(client, "subject", owners["subject"], "de-cuong.pdf")
    semester = db_session.scalars(select(Semester)).first()
    shrink = {"start_date": "2027-01-01", "end_date": "2027-01-31"}
    first = client.patch(f"/api/semesters/{semester.id}", json=shrink)
    assert first.status_code == 409
    assert first.get_json()["error"]["details"]["attachment_count"] == 1
    done = client.patch(f"/api/semesters/{semester.id}?clamp_subjects=true", json=shrink)
    assert done.status_code == 200 and blobs(db_session) == 0


def test_doi_lich_mon_lam_mat_buoi_co_file_chuyen_file_sang_mon(client):
    semester_id = create_semester(client, "2026-11-02", "2026-11-29", "HK")
    subject = create_subject(client, semester_id, weekdays=[1])  # thứ Hai
    session = sessions_of(client, subject["id"])[0]
    attached = one(client, "session", session["id"], "de-cuong.pdf")
    response = client.patch(f"/api/subjects/{subject['id']}", json={"weekdays": [3]})  # sang thứ Tư
    assert response.status_code == 200, response.get_json()
    warnings = response.get_json()["warnings"]
    assert any(w["code"] == "attachments_moved" and "1 file" in w["message"] for w in warnings)
    moved = client.get(f"/api/attachments/{attached['id']}").get_json()
    assert moved["owner"]["type"] == "subject" and moved["owner"]["id"] == subject["id"]
    assert client.get(moved["content_url"]).status_code == 200


def test_quet_don_file_la_va_tam_cu(client, owners, db_session, attachments_dir):  # noqa: F811
    keep = one(client, "task", owners["task"], "de-cuong.pdf")
    del keep
    stray = attachments_dir / "ab" / ("ab" + "1" * 62)
    stray.parent.mkdir(parents=True, exist_ok=True)
    stray.write_bytes(b"la")
    fresh = attachments_dir / "cd" / ("cd" + "2" * 62)
    fresh.parent.mkdir(parents=True, exist_ok=True)
    fresh.write_bytes(b"moi")
    old = clock.time() - 7200
    os.utime(stray, (old, old))
    leftover = attachments_dir / ".incoming" / "cu"
    leftover.parent.mkdir(exist_ok=True)
    leftover.write_bytes(b"x")
    os.utime(leftover, (old, old))
    assert service.sweep_orphans() == 2
    assert not stray.exists() and not leftover.exists()
    assert fresh.exists()  # file mới (có thể đang chờ ghi CSDL) được giữ
    assert len(store.stored_shas()) == 2
