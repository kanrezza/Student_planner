"""stale_notice_due: thông báo macOS khi quá 3 ngày chưa sao lưu (spec FR-008, research R10)."""

from datetime import datetime, timedelta

from lichhoc_agent.notify import stale_notice_due

ENABLED_SINCE = datetime(2026, 10, 20, 9, 0)
LAST_OK = datetime(2026, 11, 1, 21, 0)


def test_chua_du_3_ngay():
    now = LAST_OK + timedelta(days=3)
    assert not stale_notice_due(now, LAST_OK, ENABLED_SINCE, None)


def test_vua_qua_3_ngay_thi_gui():
    now = LAST_OK + timedelta(days=3, seconds=1)
    assert stale_notice_due(now, LAST_OK, ENABLED_SINCE, None)


def test_da_gui_cho_cung_moc_thi_khong_gui_lai():
    now = LAST_OK + timedelta(days=9)
    assert not stale_notice_due(now, LAST_OK, ENABLED_SINCE, LAST_OK.isoformat())


def test_co_ban_moi_roi_lai_qua_3_ngay_thi_gui_lai():
    new_ok = LAST_OK + timedelta(days=5)
    now = new_ok + timedelta(days=4)
    assert stale_notice_due(now, new_ok, ENABLED_SINCE, LAST_OK.isoformat())


def test_chua_tung_co_ban_tinh_tu_luc_bat():
    assert not stale_notice_due(ENABLED_SINCE + timedelta(days=2), None, ENABLED_SINCE, None)
    assert stale_notice_due(ENABLED_SINCE + timedelta(days=4), None, ENABLED_SINCE, None)


def test_tat_sao_luu_thi_khong_thong_bao():
    now = LAST_OK + timedelta(days=30)
    assert not stale_notice_due(now, LAST_OK, ENABLED_SINCE, None, enabled=False)
