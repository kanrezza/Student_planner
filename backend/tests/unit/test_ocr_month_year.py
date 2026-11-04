from datetime import date

from app.ocr.layout import WeekdayHeader
from app.ocr.month_year import infer_month_year
from tests.ocr_helpers import box

TODAY = date(2026, 11, 5)


def header(weekday=1, full=None):
    return WeekdayHeader(weekday, box(f"Thứ {weekday + 1}", 100, 100), full_date=full)


def test_grid_dates_win_over_everything():
    result = infer_month_year(
        [box("Tháng 11 2026", 0, 0)], [header(full=date(2026, 12, 7))], [], TODAY
    )
    assert (result.value, result.source) == ("2026-12", "grid_dates")
    assert result.certain is False  # mâu thuẫn với lịch thu nhỏ


def test_week_header_then_mini_calendar():
    week = [box("Tuần 10 (04/11/2026 - 10/11/2026)", 0, 0)]
    assert infer_month_year(week, [], [], TODAY).source == "week_header"
    mini = infer_month_year([box("Tháng 10-2026", 0, 0)], [], [], TODAY)
    assert (mini.value, mini.source, mini.certain) == ("2026-10", "mini_calendar", True)
    for text in ("Tháng 11 2026", "Tháng 11/2026", "Thang 11, 2026"):
        assert infer_month_year([box(text, 0, 0)], [], [], TODAY).value == "2026-11"


def test_conflict_chooses_higher_priority_but_uncertain():
    boxes = [box("Tuần 10 (04/11/2026 - 10/11/2026)", 0, 0), box("Tháng 10 2026", 0, 40)]
    result = infer_month_year(boxes, [], [], TODAY)
    assert result.value == "2026-11" and result.certain is False


def test_menu_bar_uses_current_year():
    menu = [box("Th 4 4 thg 11 14:05", 0, 0)]
    result = infer_month_year([], [], menu, TODAY)
    assert (result.value, result.source) == ("2026-11", "menu_bar")


def test_no_source():
    result = infer_month_year([box("Không có gì", 0, 0)], [], [], TODAY)
    assert result.value is None and result.certain is False
