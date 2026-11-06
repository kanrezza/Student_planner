"""Hàm thuần của quy tắc lặp task (feature 003 T079)."""

from datetime import date, datetime, time

from app.lib.timeutil import TZ
from app.services import task_recurrence as rec

D = date


def rule(freq, **kw):
    kw.setdefault("anchor_date", D(2026, 11, 5))
    return rec.Rule(freq=freq, **kw)


def now(day=None, hour=10):
    day = day or D(2026, 11, 5)
    return datetime(day.year, day.month, day.day, hour, 0, tzinfo=TZ)


def test_hang_ngay_va_moi_n_ngay():
    daily = rule("daily")
    assert rec.occurrences(daily, D(2026, 11, 5), D(2026, 11, 8)) == [
        D(2026, 11, 5),
        D(2026, 11, 6),
        D(2026, 11, 7),
        D(2026, 11, 8),
    ]
    every3 = rule("every_n_days", interval_days=3)
    assert rec.occurrences(every3, D(2026, 11, 1), D(2026, 11, 16)) == [
        D(2026, 11, 5),
        D(2026, 11, 8),
        D(2026, 11, 11),
        D(2026, 11, 14),
    ]


def test_hang_tuan_nhieu_thu():
    weekly = rule("weekly", weekdays=(1, 4))  # T2, T5
    assert rec.occurrences(weekly, D(2026, 11, 2), D(2026, 11, 12)) == [
        D(2026, 11, 2),
        D(2026, 11, 5),
        D(2026, 11, 9),
        D(2026, 11, 12),
    ]


def test_hang_thang_ngay_31_roi_vao_cuoi_thang():
    monthly = rule("monthly", month_day=31)
    found = rec.occurrences(monthly, D(2026, 11, 1), D(2028, 3, 31))
    assert D(2026, 11, 30) in found and D(2026, 12, 31) in found and D(2027, 1, 31) in found
    assert D(2027, 2, 28) in found and D(2028, 2, 29) in found
    assert len(found) == 17  # 17 tháng liên tiếp, mỗi tháng đúng một ngày


def test_12_thang_lien_tiep_deu_dung():
    monthly = rule("monthly", month_day=15)
    found = rec.occurrences(monthly, D(2026, 11, 1), D(2027, 10, 31))
    assert [d.day for d in found] == [15] * 12


def test_next_due_khong_som_hon_hom_nay_va_khong_sinh_lan_da_lo():
    daily = rule("daily")
    # Hạn cũ 02/11, hôm nay 05/11 10:00. Giờ hạn 18:00 chưa qua → 05/11; 08:00 đã qua → 06/11.
    assert rec.next_due(daily, D(2026, 11, 2), now(), time(18, 0), 1) == D(2026, 11, 5)
    assert rec.next_due(daily, D(2026, 11, 2), now(), time(8, 0), 1) == D(2026, 11, 6)
    # Không có giờ: hạn cả ngày, hôm nay vẫn còn.
    assert rec.next_due(daily, D(2026, 11, 2), now(), None, 1) == D(2026, 11, 5)
    # Hạn chưa tới: tính từ ngày sau hạn.
    assert rec.next_due(daily, D(2026, 11, 9), now(), None, 1) == D(2026, 11, 10)


def test_ket_thuc_vao_ngay_va_sau_n_lan():
    on_date = rule("daily", end_kind="on_date", end_date=D(2026, 11, 6))
    assert rec.next_due(on_date, D(2026, 11, 5), now(), None, 1) == D(2026, 11, 6)
    assert rec.next_due(on_date, D(2026, 11, 6), now(), None, 2) is None
    assert rec.occurrences(on_date, D(2026, 11, 5), D(2026, 11, 20)) == [
        D(2026, 11, 5),
        D(2026, 11, 6),
    ]
    count = rule("daily", end_kind="after_count", end_count=3)
    assert rec.next_due(count, D(2026, 11, 5), now(), None, 2) == D(2026, 11, 6)
    assert rec.next_due(count, D(2026, 11, 6), now(), None, 3) is None
    assert rec.is_finished(count, 3) and not rec.is_finished(count, 2)


def test_shift_rule_hang_ngay_va_moi_n_ngay_dem_lai_tu_ngay_moi():
    new = rec.shift_rule(rule("every_n_days", interval_days=3), D(2026, 11, 5), D(2026, 11, 7))
    assert new.anchor_date == D(2026, 11, 7)
    assert rec.matches(new, D(2026, 11, 10)) and not rec.matches(new, D(2026, 11, 8))


def test_shift_rule_hang_tuan():
    t2_t5 = rule("weekly", weekdays=(1, 4))
    # Dời lần Thứ Hai sang Thứ Ba → T3 + T5.
    assert rec.shift_rule(t2_t5, D(2026, 11, 2), D(2026, 11, 3)).weekdays == (2, 4)
    # Dời sang Thứ Năm (đã có) → chỉ T5.
    assert rec.shift_rule(t2_t5, D(2026, 11, 2), D(2026, 11, 5)).weekdays == (4,)


def test_shift_rule_hang_thang_doi_ngay_d():
    assert (
        rec.shift_rule(rule("monthly", month_day=5), D(2026, 11, 5), D(2026, 11, 12)).month_day
        == 12
    )


def test_validate():
    assert rec.validate(rule("weekly", weekdays=())) == {"weekdays": "Chọn ít nhất một thứ"}
    assert "interval_days" in rec.validate(rule("every_n_days", interval_days=1))
    assert "interval_days" in rec.validate(rule("every_n_days", interval_days=366))
    assert "month_day" in rec.validate(rule("monthly", month_day=32))
    assert "end" in rec.validate(rule("daily", end_kind="after_count", end_count=0))
    assert "end" in rec.validate(rule("daily", end_kind="on_date"))
    assert rec.validate(rule("weekly", weekdays=(1,), end_kind="after_count", end_count=999)) == {}
