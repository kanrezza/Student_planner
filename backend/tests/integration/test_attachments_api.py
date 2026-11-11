"""API đính kèm file: gắn vào 4 loại nơi, gộp nội dung trùng, giới hạn, lỗi (feature 005, US4)."""

import io
import threading
import time as clock
from datetime import date, datetime

import pytest
from sqlalchemy import func, select

from app.lib import timeutil
from app.lib.timeutil import TZ
from app.models import Attachment, AttachmentBlob, ClassSession, Settings
from app.services import attachments as service
from app.services import attachments_store as store
from tests.factories import make_semester, make_subject
from tests.integration.test_exams_api import make_exam
from tests.integration.test_task_status_api import create
from tests.ocr_helpers import load_attachment

NOW = datetime(2026, 11, 11, 10, 0, tzinfo=TZ)


@pytest.fixture(autouse=True)
def fixed_now(monkeypatch):
    monkeypatch.setattr(timeutil, "now", lambda: NOW)


def upload(client, owner_type, owner_id, *files):
    data = {
        "owner_type": owner_type,
        "owner_id": str(owner_id),
        "file": [(io.BytesIO(content), name) for name, content in files],
    }
    return client.post("/api/attachments", data=data, content_type="multipart/form-data")


def one(client, owner_type, owner_id, name="de-cuong.pdf"):
    response = upload(client, owner_type, owner_id, (name, load_attachment(name)))
    assert response.status_code == 201, response.get_json()
    return response.get_json()["attachments"][0]


@pytest.fixture
def owners(client, db_session):
    semester = make_semester(db_session)
    subject = make_subject(db_session, semester)
    session = ClassSession(
        subject_id=subject.id,
        date=date(2026, 11, 12),
        start_at=datetime(2026, 11, 12, 7, 0, tzinfo=TZ),
        end_at=datetime(2026, 11, 12, 9, 0, tzinfo=TZ),
    )
    db_session.add(session)
    db_session.commit()
    return {
        "task": create(client)["id"],
        "subject": subject.id,
        "session": session.id,
        "exam": make_exam(client)["exam"]["id"],
    }


def store_files(root):
    return [p for p in root.rglob("*") if p.is_file() and ".incoming" not in p.parts]


def test_gan_vao_ca_bon_loai_noi(client, owners):
    for owner_type, owner_id in owners.items():
        attachment = one(client, owner_type, owner_id)
        assert attachment["owner"]["type"] == owner_type and attachment["owner"]["id"] == owner_id
        assert attachment["display_name"] == "de-cuong.pdf" and attachment["preview"] == "pdf"
        assert attachment["mime_type"] == "application/pdf" and not attachment["is_executable"]
        listed = client.get(f"/api/attachments?owner_type={owner_type}&owner_id={owner_id}")
        assert [a["id"] for a in listed.get_json()] == [attachment["id"]]
        content = client.get(attachment["content_url"])
        assert content.status_code == 200 and content.data == load_attachment("de-cuong.pdf")


def test_nhieu_file_mot_lan_va_ten_trung(client, owners):
    response = upload(
        client,
        "subject",
        owners["subject"],
        ("a.pdf", load_attachment("de-cuong.pdf")),
        ("a.pdf", load_attachment("anh-nho.png")),  # trùng tên, khác nội dung
        ("rong.txt", b""),
    )
    created = response.get_json()["attachments"]
    assert [a["display_name"] for a in created] == ["a.pdf", "a (2).pdf", "rong.txt"]
    assert created[2]["size"] == 0  # file 0 byte được chấp nhận


def test_cung_noi_dung_5_noi_chi_tinh_dung_luong_mot_lan(client, owners, attachments_dir):
    data = load_attachment("de-cuong.pdf")
    for owner_type, owner_id in owners.items():
        upload(client, owner_type, owner_id, ("a.pdf", data))
    upload(client, "task", owners["task"], ("b.pdf", data))
    stats = client.get("/api/attachments/stats").get_json()
    assert stats["blob_count"] == 1 and stats["attachment_count"] == 5
    assert stats["total_bytes"] == len(data)
    assert len(store_files(attachments_dir)) == 1


def test_vuot_gioi_han_khong_de_lai_file(client, owners, db_session, attachments_dir):
    db_session.get(Settings, 1).attachment_max_mb = 1
    db_session.commit()
    big = b"x" * (1024 * 1024 + 1)
    response = upload(
        client,
        "task",
        owners["task"],
        ("lon.bin", big),
        ("nho.png", load_attachment("anh-nho.png")),
    )
    assert response.status_code == 201  # file nhỏ vẫn lưu
    body = response.get_json()
    assert [a["display_name"] for a in body["attachments"]] == ["nho.png"]
    assert body["errors"][0]["code"] == "file_too_large"
    assert "1 MB" in body["errors"][0]["message"] and "Cài đặt" in body["errors"][0]["message"]
    only_big = upload(client, "task", owners["task"], ("lon.bin", big))
    assert only_big.status_code == 413
    assert list((attachments_dir / ".incoming").iterdir()) == []


def test_noi_gan_khong_hop_le(client, owners):
    response = upload(client, "task", 999999, ("a.pdf", b"x"))
    assert response.status_code == 400 and response.get_json()["error"]["code"] == "owner_not_found"
    assert upload(client, "task", owners["task"]).status_code == 400  # thiếu file
    client.delete(f"/api/tasks/{owners['task']}")  # vào Thùng rác
    trashed = upload(client, "task", owners["task"], ("a.pdf", b"x"))
    assert trashed.get_json()["error"]["code"] == "owner_not_found"


def test_het_cho_tra_507(client, owners, monkeypatch):
    def full(*_args, **_kw):
        raise store.DiskFull

    monkeypatch.setattr(store, "store_stream", full)
    response = upload(client, "task", owners["task"], ("a.pdf", b"x"))
    assert response.status_code == 507
    assert response.get_json()["errors"][0] == {
        "name": "a.pdf",
        "code": "disk_full",
        "message": "Ổ đĩa không đủ chỗ",
    }


def test_doi_ten(client, owners):
    first = one(client, "task", owners["task"])
    other = one(client, "task", owners["task"], "anh-nho.png")
    patch = {"display_name": "Đề cương NLP.pdf"}
    renamed = client.patch(f"/api/attachments/{first['id']}", json=patch)
    assert renamed.get_json()["display_name"] == "Đề cương NLP.pdf"
    clash = client.patch(f"/api/attachments/{first['id']}", json={"display_name": "anh-nho.png"})
    assert clash.get_json()["display_name"] == "anh-nho (2).png" and other["id"] != first["id"]
    for bad in ("", "   "):
        response = client.patch(f"/api/attachments/{first['id']}", json={"display_name": bad})
        assert response.status_code == 400


def test_so_file_tren_task_mon_buoi_thi(client, owners):
    for owner_type, owner_id in owners.items():
        upload(client, owner_type, owner_id, ("a.pdf", b"1"), ("b.pdf", b"2"))
    task = client.get(f"/api/tasks/{owners['task']}").get_json()
    assert task["attachment_count"] == 2
    subjects = client.get("/api/subjects").get_json()
    assert next(s for s in subjects if s["id"] == owners["subject"])["attachment_count"] == 2
    exams = client.get("/api/exams?from=2026-11-01&to=2026-12-31").get_json()["exams"]
    assert next(e for e in exams if e["id"] == owners["exam"])["attachment_count"] == 2


def test_chay_chong_don_dep_va_upload_cung_noi_dung(client, owners, app):
    """Dọn blob đúng lúc upload cùng nội dung: mục đính kèm mới vẫn trỏ tới file còn trong kho."""
    data = load_attachment("de-cuong.pdf")
    first = one(client, "task", owners["task"])
    sha = service.db.session.get(Attachment, first["id"]).blob_sha256
    client.delete(f"/api/attachments/{first['id']}")  # blob đã bị dọn
    assert not store.blob_path(sha).exists()
    again = upload(client, "subject", owners["subject"], ("de-cuong.pdf", data))
    assert again.status_code == 201
    new = again.get_json()["attachments"][0]
    assert client.get(new["content_url"]).data == data

    errors = []

    def run_gc():
        try:
            with app.app_context():
                for _ in range(20):
                    service.collect_garbage([sha])
        except Exception as error:  # noqa: BLE001
            errors.append(error)

    thread = threading.Thread(target=run_gc)
    thread.start()
    thread.join()
    assert not errors
    assert client.get(new["content_url"]).data == data  # còn mục tham chiếu thì không bị dọn


def test_upload_50mb_duoi_5_giay(client, owners, db_session):
    start = clock.perf_counter()
    response = upload(client, "task", owners["task"], ("lon.bin", b"\x00" * (50 * 1024 * 1024)))
    elapsed = clock.perf_counter() - start
    assert response.status_code == 201, response.get_json()
    assert elapsed < 5.0, f"{elapsed:.2f} giây"
    assert db_session.scalar(select(func.count()).select_from(AttachmentBlob)) == 1
