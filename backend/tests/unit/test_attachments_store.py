"""Kho file đính kèm trên đĩa (feature 005)."""

import hashlib
import io
import os
import time
import unicodedata
from pathlib import Path

import pytest
from flask import Flask

from app.services import attachments_store as store
from tests.ocr_helpers import load_attachment


@pytest.fixture(autouse=True)
def app_ctx(tmp_path):
    app = Flask(__name__)
    app.config["ATTACHMENTS_DIR"] = str(tmp_path / "kho")
    with app.app_context():
        yield tmp_path / "kho"


def test_duong_dan_blob(app_ctx):
    sha = "ab" + "0" * 62
    assert store.blob_path(sha) == app_ctx / "ab" / sha
    with pytest.raises(ValueError):
        store.blob_path("../etc/passwd")


def test_luu_luong_ten_theo_hash(app_ctx):
    data = b"noi dung " * 1000
    sha, size, head = store.store_stream(io.BytesIO(data), 10**6)
    assert sha == hashlib.sha256(data).hexdigest() and size == len(data) and head == data[:4096]
    assert store.blob_path(sha).read_bytes() == data
    assert list((app_ctx / ".incoming").iterdir()) == []


def test_noi_dung_trung_khong_tao_file_thu_hai(app_ctx):
    a = store.store_stream(io.BytesIO(b"abc"), 100)[0]
    b = store.store_stream(io.BytesIO(b"abc"), 100)[0]
    assert a == b and len(store.stored_shas()) == 1


def test_file_rong_duoc_luu(app_ctx):
    sha, size, _ = store.store_stream(io.BytesIO(b""), 100)
    assert size == 0 and store.blob_path(sha).read_bytes() == b""


def test_vuot_gioi_han_khong_de_lai_file(app_ctx):
    with pytest.raises(store.FileTooLarge):
        store.store_stream(io.BytesIO(b"x" * 100), 50)
    assert list((app_ctx / ".incoming").iterdir()) == [] and store.stored_shas() == set()


def test_loi_doc_giua_chung_khong_de_lai_file(app_ctx):
    class Broken(io.RawIOBase):
        calls = 0

        def read(self, size=-1):
            self.calls += 1
            if self.calls == 1:
                return b"x" * 10
            raise OSError("đĩa lỗi")

    with pytest.raises(OSError, match="đĩa lỗi"):
        store.store_stream(Broken(), 100)
    assert list((app_ctx / ".incoming").iterdir()) == [] and store.stored_shas() == set()


def test_het_cho_bao_disk_full(app_ctx, monkeypatch):
    def full(*_args):
        raise OSError(28, "No space left")

    monkeypatch.setattr(os, "fsync", full)
    with pytest.raises(store.DiskFull):
        store.store_stream(io.BytesIO(b"abc"), 100)
    assert list((app_ctx / ".incoming").iterdir()) == []


def test_xoa_blob_va_quet(app_ctx):
    keep = store.store_stream(io.BytesIO(b"giu"), 100)[0]
    stray = store.store_stream(io.BytesIO(b"la"), 100)[0]
    fresh = store.store_stream(io.BytesIO(b"moi"), 100)[0]
    old = time.time() - 2 * 3600
    for sha in (keep, stray):
        os.utime(store.blob_path(sha), (old, old))
    leftover = app_ctx / ".incoming" / "cu"
    leftover.write_bytes(b"x")
    os.utime(leftover, (old, old))
    assert store.sweep({keep}) == 2  # file lạ cũ + file tạm cũ
    assert store.stored_shas() == {keep, fresh}  # file lạ nhưng mới (chưa kịp ghi CSDL) được giữ
    store.delete_blob(keep)
    store.delete_blob(keep)  # xoá lần hai không lỗi
    assert store.stored_shas() == {fresh}


@pytest.mark.parametrize(
    ("name", "mime"),
    [
        ("anh-nho.png", "image/png"),
        ("de-cuong.pdf", "application/pdf"),
        ("gia-mao.png", "application/octet-stream"),  # đuôi .png nhưng là HTML
        ("ve.svg", "image/svg+xml"),
        ("bai-tap.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ("rong.txt", "text/plain"),
    ],
)
def test_nhan_dang_mime(name, mime):
    assert store.detect_mime(name, load_attachment(name)[:4096]) == mime


def test_chi_xem_truoc_anh_va_pdf():
    assert store.preview_kind("image/png") == "image"
    assert store.preview_kind("application/pdf") == "pdf"
    assert store.preview_kind("image/svg+xml") is None
    assert store.preview_kind("text/html") is None


@pytest.mark.parametrize(
    ("name", "head", "expected"),
    [
        ("chay-thu.command", b"#!/bin/sh", True),
        ("x.APP", b"", True),
        ("a.pkg", b"", True),
        ("lạ.bin", b"\xcf\xfa\xed\xfe....", True),  # Mach-O
        ("lạ.bin", b"\x7fELF....", True),
        ("de-cuong.pdf", b"%PDF-1.4", False),
        ("anh.png", b"\x89PNG", False),
    ],
)
def test_file_thuc_thi(name, head, expected):
    assert store.is_executable(name, head) is expected


def test_ten_hien_thi_khong_trung():
    assert store.unique_display_name("a.pdf", []) == "a.pdf"
    assert store.unique_display_name("a.pdf", ["A.pdf"]) == "a (2).pdf"
    assert store.unique_display_name("a.pdf", ["a.pdf", "a (2).pdf"]) == "a (3).pdf"
    assert store.unique_display_name("ghi chu", ["ghi chu"]) == "ghi chu (2)"


def test_lam_sach_ten():
    assert store.clean_display_name("a/b\\c\x00.pdf") == "abc.pdf"
    assert store.clean_display_name("   ") == "file"
    assert len(store.clean_display_name("x" * 400)) == 255
    nfd = unicodedata.normalize("NFD", "Đề cương.pdf")  # Finder đưa tên dạng tổ hợp
    assert store.clean_display_name(nfd) == unicodedata.normalize("NFC", "Đề cương.pdf")


def test_dat_lai_blob_thieu(app_ctx, tmp_path):
    sha = hashlib.sha256(b"abc").hexdigest()
    source = tmp_path / "tam"
    source.write_bytes(b"abc")
    store.ensure_blob_from(Path(source), sha)
    assert store.blob_path(sha).read_bytes() == b"abc"
