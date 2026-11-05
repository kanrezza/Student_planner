from lichhoc_agent import icloud


def test_nhan_dien_ban_chi_tren_icloud(tmp_path):
    real = tmp_path / "LichHoc-2026-11-05-2100-tu-dong.lhbackup"
    assert not icloud.is_cloud_only(real)
    icloud.placeholder_for(real).write_bytes(b"")
    assert icloud.is_cloud_only(real)
    real.write_bytes(b"x")
    assert not icloud.is_cloud_only(real)


def test_ensure_downloaded_cho_toi_khi_file_xuat_hien(tmp_path, monkeypatch):
    real = tmp_path / "a.lhbackup"
    monkeypatch.setattr(icloud, "_start_download", lambda path: None)
    ticks = []

    def fake_sleep(_seconds):
        ticks.append(1)
        if len(ticks) == 3:
            real.write_bytes(b"x")

    icloud.ensure_downloaded(real, timeout=60, sleep=fake_sleep)
    assert len(ticks) == 3


def test_ensure_downloaded_qua_han(tmp_path, monkeypatch):
    monkeypatch.setattr(icloud, "_start_download", lambda path: None)
    now = [0.0]

    def clock():
        return now[0]

    def sleep(seconds):
        now[0] += seconds

    try:
        icloud.ensure_downloaded(tmp_path / "a.lhbackup", timeout=10, sleep=sleep, clock=clock)
    except TimeoutError:
        pass
    else:
        raise AssertionError("phải báo quá hạn")
