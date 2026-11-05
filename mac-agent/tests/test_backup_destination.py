"""resolve_destination: thư mục đích có/không, iCloud Drive, quyền ghi (research R6)."""

import os
from pathlib import Path

import pytest

from lichhoc_agent.backup import DEFAULT_FOLDER_PARTS, resolve_destination

ICLOUD_PARTS = ("Library", "Mobile Documents", "com~apple~CloudDocs")


def fake_home(tmp_path: Path, icloud: bool) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    if icloud:
        home.joinpath(*ICLOUD_PARTS).mkdir(parents=True)
    return home


def test_mac_dinh_co_icloud_tu_tao_thu_muc(tmp_path):
    home = fake_home(tmp_path, icloud=True)
    dest = resolve_destination(None, home=home)
    expected = home.joinpath(*ICLOUD_PARTS, *DEFAULT_FOLDER_PARTS)
    assert dest.state == "ok"
    assert dest.path == expected and expected.is_dir()
    assert dest.message is None
    assert DEFAULT_FOLDER_PARTS == ("Lịch Học Cá Nhân", "Sao lưu")


def test_mac_dinh_khong_co_icloud(tmp_path):
    home = fake_home(tmp_path, icloud=False)
    dest = resolve_destination(None, home=home)
    assert dest.state == "icloud_off"
    assert dest.path is None
    assert dest.message == "iCloud Drive chưa bật. Bật iCloud Drive hoặc chọn thư mục khác."
    assert not home.joinpath("Library", "Mobile Documents").exists()  # không tự tạo gì


def test_thu_muc_tu_chon_khong_ton_tai_khong_duoc_tu_tao(tmp_path):
    home = fake_home(tmp_path, icloud=True)
    missing = tmp_path / "Volumes" / "SSD" / "Sao lưu"
    dest = resolve_destination(str(missing), home=home)
    assert dest.state == "missing"
    assert dest.message == (
        "Không tìm thấy thư mục sao lưu (ổ đĩa có thể đã được tháo). Sẽ thử lại khi ổ được cắm lại."
    )
    assert not missing.exists() and not missing.parent.exists()


def test_thu_muc_tu_chon_co_that(tmp_path):
    home = fake_home(tmp_path, icloud=False)
    folder = tmp_path / "SSD"
    folder.mkdir()
    dest = resolve_destination(str(folder), home=home)
    assert dest.state == "ok" and dest.path == folder
    assert list(folder.iterdir()) == []  # file thử ghi đã được dọn


@pytest.mark.skipif(os.geteuid() == 0, reason="root luôn ghi được")
def test_khong_co_quyen_ghi(tmp_path):
    home = fake_home(tmp_path, icloud=False)
    folder = tmp_path / "ChiDoc"
    folder.mkdir()
    folder.chmod(0o500)
    try:
        dest = resolve_destination(str(folder), home=home)
    finally:
        folder.chmod(0o700)
    assert dest.state == "no_permission"
    assert "Quyền riêng tư & Bảo mật" in dest.message
    assert "LichHocAgent" in dest.message


def test_duong_dan_la_file_khong_phai_thu_muc(tmp_path):
    home = fake_home(tmp_path, icloud=False)
    a_file = tmp_path / "file.txt"
    a_file.write_text("x")
    assert resolve_destination(str(a_file), home=home).state == "missing"
