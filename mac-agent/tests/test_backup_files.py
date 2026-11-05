"""Tên file sao lưu, danh sách và dọn bản cũ (contracts/agent-backup.md, research R3/R6)."""

from datetime import datetime
from pathlib import Path

import pytest

from lichhoc_agent.backup import (
    BackupFile,
    list_backups,
    parse_backup_name,
    prune,
    unique_name,
)

WHEN = datetime(2026, 11, 5, 21, 0)


def make_file(day: int, kind="tu-dong", seq=None) -> BackupFile:
    suffix = f"-{seq}" if seq else ""
    name = f"LichHoc-2026-11-{day:02d}-2100-{kind}{suffix}.lhbackup"
    return BackupFile(
        name=name,
        path=f"/sao-luu/{name}",
        kind=kind,
        created_at=datetime(2026, 11, day, 21, 0),
        size=1000,
        location="local",
        seq=seq or 1,
    )


@pytest.mark.parametrize("kind", ["tu-dong", "thu-cong", "truoc-khoi-phuc"])
def test_parse_ba_loai(kind):
    parsed = parse_backup_name(f"LichHoc-2026-11-05-2100-{kind}.lhbackup")
    assert parsed is not None
    assert parsed.kind == kind
    assert parsed.created_at == WHEN
    assert parsed.seq == 1
    assert not parsed.cloud_only


def test_parse_hau_to_so_thu_tu():
    parsed = parse_backup_name("LichHoc-2026-11-05-2100-tu-dong-3.lhbackup")
    assert parsed is not None and parsed.seq == 3


def test_parse_file_la_bi_bo_qua():
    for name in [
        "ghi-chu.txt",
        "LichHoc-abc.lhbackup",
        "LichHoc-2026-11-05-2100-khac.lhbackup",
        "LichHoc-2026-13-05-2100-tu-dong.lhbackup",  # tháng 13
        "LichHoc-2026-11-05-2100-tu-dong.lhbackup.partial",
        ".LichHoc-2026-11-05-2100-tu-dong.lhbackup.partial",
        "LichHoc-2026-11-05-2100-tu-dong.zip",
    ]:
        assert parse_backup_name(name) is None, name


def test_parse_ban_chi_tren_icloud():
    parsed = parse_backup_name(".LichHoc-2026-11-05-2100-tu-dong.lhbackup.icloud")
    assert parsed is not None
    assert parsed.cloud_only
    assert parsed.name == "LichHoc-2026-11-05-2100-tu-dong.lhbackup"


def test_unique_name_khong_trung():
    assert unique_name(set(), WHEN, "tu-dong") == "LichHoc-2026-11-05-2100-tu-dong.lhbackup"


def test_unique_name_trung_phut_them_hau_to():
    base = "LichHoc-2026-11-05-2100-tu-dong.lhbackup"
    assert unique_name({base}, WHEN, "tu-dong").endswith("tu-dong-2.lhbackup")
    taken = {base, "LichHoc-2026-11-05-2100-tu-dong-2.lhbackup"}
    assert unique_name(taken, WHEN, "tu-dong").endswith("tu-dong-3.lhbackup")
    # Loại khác cùng phút không trùng.
    assert unique_name({base}, WHEN, "thu-cong") == "LichHoc-2026-11-05-2100-thu-cong.lhbackup"


def test_unique_name_tinh_ca_ban_chi_tren_icloud():
    placeholder = ".LichHoc-2026-11-05-2100-tu-dong.lhbackup.icloud"
    assert unique_name({placeholder}, WHEN, "tu-dong").endswith("tu-dong-2.lhbackup")


def test_prune_16_ban_giu_14():
    files = [make_file(d) for d in range(1, 17)]
    doomed = prune(files, keep=14)
    assert sorted(f.created_at.day for f in doomed) == [1, 2]


def test_prune_giam_xuong_7():
    files = [make_file(d) for d in range(1, 15)]
    assert len(prune(files, keep=7)) == 7


def test_prune_keep_lon_hon_so_ban_khong_xoa():
    assert prune([make_file(d) for d in range(1, 4)], keep=14) == []
    assert prune([], keep=1) == []


def test_prune_khong_bao_gio_xoa_ban_duoc_bao_ve():
    files = [make_file(d) for d in range(1, 16)]  # 15 bản, giữ 14 → bản ngày 1 là thừa
    oldest = files[0]
    assert prune(files, keep=14, protect=oldest.path) == []
    # Bảo vệ bản ngày 2 (không phải bản thừa) thì chỉ bản ngày 1 bị xoá.
    doomed = prune(files, keep=14, protect=files[1].path)
    assert [f.created_at.day for f in doomed] == [1]


def test_prune_cung_phut_xoa_so_thu_tu_nho_truoc():
    a, b = make_file(5, seq=None), make_file(5, seq=2)
    doomed = prune([b, a], keep=1)
    assert doomed == [a]


def test_list_backups_chi_liet_ke_file_cua_app(tmp_path: Path):
    (tmp_path / "LichHoc-2026-11-05-2100-tu-dong.lhbackup").write_bytes(b"x" * 10)
    (tmp_path / "LichHoc-2026-11-04-2100-thu-cong.lhbackup").write_bytes(b"x" * 5)
    (tmp_path / "ghi-chu.txt").write_text("của tôi")
    (tmp_path / ".LichHoc-2026-11-03-2100-tu-dong.lhbackup.partial").write_bytes(b"do")
    (tmp_path / ".LichHoc-2026-11-02-2100-tu-dong.lhbackup.icloud").write_bytes(b"")
    files = list_backups(tmp_path)
    assert [f.created_at.day for f in files] == [5, 4, 2]  # mới nhất trước
    assert files[0].size == 10 and files[0].location == "local"
    assert files[2].location == "icloud"
    assert files[2].path == str(tmp_path / "LichHoc-2026-11-02-2100-tu-dong.lhbackup")


def test_list_backups_thu_muc_khong_co(tmp_path: Path):
    assert list_backups(tmp_path / "khong-co") == []
