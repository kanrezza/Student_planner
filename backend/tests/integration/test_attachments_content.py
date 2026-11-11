"""Nội dung, tải về, xoá file đính kèm: header an toàn, chỉ xem trước ảnh/PDF (feature 005, US5)."""

import pytest
from sqlalchemy import select

from app.models import Attachment, AttachmentBlob
from app.services import attachments_store as store
from tests.integration.test_attachments_api import one, owners, store_files, upload  # noqa: F401
from tests.ocr_helpers import load_attachment


def content(client, attachment):
    return client.get(attachment["content_url"])


def test_anh_va_pdf_xem_truc_tiep_voi_header_an_toan(client, owners):  # noqa: F811
    for name, mime in (("anh-nho.png", "image/png"), ("de-cuong.pdf", "application/pdf")):
        response = content(client, one(client, "task", owners["task"], name))
        assert response.status_code == 200
        assert response.headers["Content-Type"].startswith(mime)
        assert response.headers["Content-Disposition"].startswith("inline")
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert "sandbox" in response.headers["Content-Security-Policy"]
        assert response.data == load_attachment(name)


@pytest.mark.parametrize("name", ["ve.svg", "gia-mao.png", "bai-tap.docx", "chay-thu.command"])
def test_loai_khac_luon_tai_ve_khong_chay_trong_trang(client, owners, name):  # noqa: F811
    response = content(client, one(client, "subject", owners["subject"], name))
    assert response.headers["Content-Disposition"].startswith("attachment")
    assert response.headers["Content-Type"].startswith("application/octet-stream")


def test_co_thuc_thi(client, owners):  # noqa: F811
    assert one(client, "task", owners["task"], "chay-thu.command")["is_executable"] is True
    assert one(client, "task", owners["task"], "de-cuong.pdf")["is_executable"] is False


def test_etag_va_range(client, owners):  # noqa: F811
    attachment = one(client, "task", owners["task"])
    full = content(client, attachment)
    assert (
        full.headers["ETag"].strip('"') == full.headers["ETag"].strip('"') and full.headers["ETag"]
    )
    partial = client.get(attachment["content_url"], headers={"Range": "bytes=0-99"})
    assert partial.status_code == 206 and partial.data == load_attachment("de-cuong.pdf")[:100]
    cached = client.get(attachment["content_url"], headers={"If-None-Match": full.headers["ETag"]})
    assert cached.status_code == 304


def test_tai_ve_giu_ten_co_dau(client, owners):  # noqa: F811
    response = upload(client, "task", owners["task"], ("Đề cương NLP.pdf", b"%PDF-1.4"))
    attachment = response.get_json()["attachments"][0]
    download = client.get(attachment["download_url"])
    disposition = download.headers["Content-Disposition"]
    assert disposition.startswith("attachment") and "filename*=UTF-8''" in disposition
    assert "%C4%90%E1%BB%81%20c%C6%B0%C6%A1ng%20NLP.pdf" in disposition


def test_xoa_giu_blob_khi_noi_khac_dung_va_don_khi_het(client, owners, db_session, attachments_dir):  # noqa: F811
    data = load_attachment("de-cuong.pdf")
    first = upload(client, "task", owners["task"], ("a.pdf", data)).get_json()["attachments"][0]
    second = upload(client, "subject", owners["subject"], ("a.pdf", data)).get_json()[
        "attachments"
    ][0]
    sha = db_session.get(Attachment, first["id"]).blob_sha256
    assert client.delete(f"/api/attachments/{first['id']}").status_code == 204
    assert store.blob_path(sha).exists()  # nơi khác còn dùng
    assert client.get(second["content_url"]).data == data
    assert client.get("/api/attachments/stats").get_json()["total_bytes"] == len(data)
    assert client.delete(f"/api/attachments/{second['id']}").status_code == 204
    assert not store.blob_path(sha).exists()
    assert db_session.scalar(select(AttachmentBlob).where(AttachmentBlob.sha256 == sha)) is None
    assert client.get("/api/attachments/stats").get_json()["total_bytes"] == 0
    assert store_files(attachments_dir) == []
    assert client.delete(f"/api/attachments/{second['id']}").status_code == 404


def test_file_thieu_trong_kho_bao_loi_ro(client, owners):  # noqa: F811
    attachment = one(client, "task", owners["task"])
    for path in store_files(store.root()):
        path.unlink()
    response = content(client, attachment)
    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "attachment_missing"
