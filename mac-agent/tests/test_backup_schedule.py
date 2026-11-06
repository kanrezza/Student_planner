"""backup_due: khi nào agent phải sao lưu (contracts/agent-backup.md, spec FR-001/FR-003)."""

from datetime import datetime, time, timedelta

from lichhoc_agent.backup import RETRY_AFTER, backup_due

SCHEDULE = time(21, 0)


def due(now, last_success=None, last_attempt=None, schedule=SCHEDULE, enabled=True):
    return backup_due(now, schedule, enabled, last_success, last_attempt)


def test_chua_den_gio_va_da_co_ban_hom_qua():
    now = datetime(2026, 11, 5, 20, 59)
    assert not due(now, last_success=datetime(2026, 11, 4, 21, 0, 5))


def test_dung_gio_21h_thi_den_han():
    now = datetime(2026, 11, 5, 21, 0)
    assert due(now, last_success=datetime(2026, 11, 4, 21, 0, 5))


def test_da_sao_luu_sau_moc_hom_nay_thi_khong_lam_lai():
    now = datetime(2026, 11, 5, 22, 30)
    assert not due(now, last_success=datetime(2026, 11, 5, 21, 0, 40))


def test_mac_ngu_tu_18h_den_7h30_sang_hom_sau_thi_bu_mot_lan():
    # Lần thành công cuối là 21:00 ngày 4; Mac ngủ qua mốc 21:00 ngày 5, thức dậy 07:30 ngày 6.
    last = datetime(2026, 11, 4, 21, 0, 5)
    assert due(datetime(2026, 11, 6, 7, 30), last_success=last)
    # Sau khi bù xong (07:31) thì không sao lưu nữa cho tới 21:00 ngày 6.
    assert not due(datetime(2026, 11, 6, 7, 40), last_success=datetime(2026, 11, 6, 7, 31))
    assert due(datetime(2026, 11, 6, 21, 0), last_success=datetime(2026, 11, 6, 7, 31))


def test_tat_may_3_ngay_chi_mot_ban_bu():
    last = datetime(2026, 11, 1, 21, 0, 5)
    now = datetime(2026, 11, 4, 9, 0)
    assert due(now, last_success=last)
    assert not due(now + timedelta(minutes=1), last_success=now)  # bản bù vừa xong


def test_doi_gio_sang_22h():
    last = datetime(2026, 11, 4, 21, 0, 5)
    now = datetime(2026, 11, 5, 21, 30)
    assert due(now, last_success=last, schedule=time(21, 0))
    # Đã đổi sang 22:00: lần thành công cuối 22:00 hôm qua → 21:30 hôm nay chưa tới mốc mới.
    after_22 = datetime(2026, 11, 4, 22, 0, 5)
    assert not due(now, last_success=after_22, schedule=time(22, 0))
    assert due(datetime(2026, 11, 5, 22, 0), last_success=after_22, schedule=time(22, 0))


def test_vua_that_bai_chua_thu_lai_truoc_4_phut():
    last = datetime(2026, 11, 4, 21, 0, 5)
    attempt = datetime(2026, 11, 5, 21, 0, 10)
    assert not due(attempt + timedelta(minutes=3, seconds=59), last, attempt)
    assert due(attempt + RETRY_AFTER, last, attempt)
    assert RETRY_AFTER == timedelta(minutes=4)


def test_tat_sao_luu_tu_dong():
    assert not due(datetime(2026, 11, 5, 21, 0), enabled=False)


def test_chua_tung_sao_luu_thi_sao_luu_ngay():
    assert due(datetime(2026, 11, 5, 10, 0))


def test_dong_ho_lui_khong_sao_luu_lien_tuc():
    # Lần thành công "ở tương lai" (đồng hồ chỉnh lùi) → coi như đã có bản, không lặp vô hạn.
    now = datetime(2026, 11, 5, 21, 30)
    assert not due(now, last_success=datetime(2026, 11, 5, 23, 0))


def test_lan_thu_o_tuong_lai_khong_chan_mai_mai():
    last = datetime(2026, 11, 4, 21, 0, 5)
    now = datetime(2026, 11, 5, 21, 30)
    assert due(now, last, last_attempt=datetime(2026, 11, 6, 8, 0))
