"""⌘F tìm theo tên file đính kèm (feature 005, US6, FR-027, SC-009)."""

import time as clock
import unicodedata

from sqlalchemy import func, insert, select

from app.models import Attachment, AttachmentBlob
from tests.integration.test_attachments_api import one, owners, upload  # noqa: F401
from tests.ocr_helpers import load_attachment


def search(client, q, **extra):
    query = "&".join(f"{k}={v}" for k, v in {"q": q, **extra}.items())
    response = client.get(f"/api/search?{query}")
    assert response.status_code == 200, response.get_json()
    return response.get_json()["groups"]["files"]


def test_tim_khong_dau_va_ra_dung_noi_gan(client, owners):  # noqa: F811
    subject_file = upload(
        client, "subject", owners["subject"], ("Đề cương NLP.pdf", load_attachment("de-cuong.pdf"))
    ).get_json()["attachments"][0]
    result = search(client, "de cuong")
    assert result["total"] == 1
    item = result["items"][0]
    assert item["attachment_id"] == subject_file["id"] and item["name"] == "Đề cương NLP.pdf"
    assert item["owner"]["type"] == "subject" and item["owner"]["id"] == owners["subject"]
    assert item["owner"]["title"]


def test_ten_dang_to_hop_cua_finder_van_khop(client, owners):  # noqa: F811
    nfd = unicodedata.normalize("NFD", "Đề thi 2025.pdf")
    upload(client, "exam", owners["exam"], (nfd, b"1"))
    assert search(client, "de thi")["total"] == 1
    assert search(client, "ĐỀ THI 2025")["total"] == 1


def test_ca_bon_loai_noi_gan(client, owners):  # noqa: F811
    for owner_type, owner_id in owners.items():
        upload(client, owner_type, owner_id, (f"tai-lieu-{owner_type}.pdf", b"x"))
    items = search(client, "tai lieu")["items"]
    assert {i["owner"]["type"] for i in items} == {"task", "subject", "session", "exam"}
    assert all(i["owner"]["title"] for i in items)


def test_file_task_thung_rac_khong_xuat_hien(client, owners):  # noqa: F811
    upload(client, "task", owners["task"], ("bi-mat.pdf", b"x"))
    assert search(client, "bi mat")["total"] == 1
    client.delete(f"/api/tasks/{owners['task']}")
    assert search(client, "bi mat")["total"] == 0


def test_loc_theo_nhom_files_va_khong_doc_noi_dung(client, owners):  # noqa: F811
    upload(client, "task", owners["task"], ("a.txt", b"tu-khoa-trong-noi-dung"))
    data = client.get("/api/search?q=tu-khoa-trong&group=files").get_json()
    assert data["groups"]["files"]["total"] == 0  # chỉ tìm theo tên, không theo nội dung
    only = client.get("/api/search?q=a.txt&group=files").get_json()["groups"]
    assert only["files"]["total"] == 1 and only["tasks"]["total"] == 0


def test_1000_file_duoi_1_giay(client, owners, db_session):  # noqa: F811
    blob = "a" * 64
    db_session.execute(insert(AttachmentBlob).values(sha256=blob, size=1))
    db_session.execute(
        insert(Attachment),
        [
            {"blob_sha256": blob, "task_id": owners["task"], "display_name": f"Tài liệu {i}.pdf"}
            for i in range(1000)
        ],
    )
    db_session.commit()
    assert db_session.scalar(select(func.count()).select_from(Attachment)) == 1000
    start = clock.perf_counter()
    result = search(client, "tai lieu 99", limit=50)
    elapsed = clock.perf_counter() - start
    assert result["total"] >= 11 and elapsed < 1.0, f"{elapsed:.2f} giây"
