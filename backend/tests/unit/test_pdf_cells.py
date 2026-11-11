"""Luật ghép dòng và đọc ô của bảng thời khoá biểu PDF (contracts/timetable-pdf-format.md)."""

from datetime import date

import pytest

from app.pdfimport.cells import (
    DayCell,
    join_cell_lines,
    parse_class_label,
    parse_credits,
    parse_dates,
    parse_day_cell,
    parse_semester_name,
)


def test_ma_hoc_phan_noi_lien():
    assert join_cell_lines(["FFS7010", "69"], "course_code") == "FFS701069"
    assert join_cell_lines(["CSE703", "016"], "course_code") == "CSE703016"


def test_lop_hoc_phan_noi_bang_dau_cach_roi_tach_ten_va_ma_lop():
    text = join_cell_lines(
        ["Tích hợp và phân tích dữ", "liệu", "lớn-2-2-26(COUR01.LT2)"], "class_label"
    )
    assert text == "Tích hợp và phân tích dữ liệu lớn-2-2-26(COUR01.LT2)"
    assert parse_class_label(text) == ("Tích hợp và phân tích dữ liệu lớn", "2-2-26(COUR01.LT2)")


@pytest.mark.parametrize(
    ("lines", "expected"),
    [
        (["1 - 3", "(A6-1", "03", "(PC))"], DayCell(1, 3, "A6-103 (PC)")),
        (["4 - 6 (A6-203", "(PC))"], DayCell(4, 6, "A6-203 (PC)")),
        (["4 - 6 (A6-301.30", "2 (PC))"], DayCell(4, 6, "A6-301.302 (PC)")),
        (["4 - 6 (Sân", "bóng đá)"], DayCell(4, 6, "Sân bóng đá")),
        (["16 - 18", "(ONLINE-", "Elearning)"], DayCell(16, 18, "ONLINE-Elearning")),
        (["1 - 3"], DayCell(1, 3, None)),
        (["2 - 2 (A8-104)"], DayCell(2, 2, "A8-104")),
    ],
)
def test_o_thu(lines, expected):
    assert parse_day_cell(join_cell_lines(lines, "day_cell")) == expected


@pytest.mark.parametrize("text", ["", "abc", "6 - 4 (A1)", "0 - 3 (A1)", "31 - 32 (A1)", "A6-101"])
def test_o_thu_khong_doc_duoc_tiet(text):
    assert parse_day_cell(text) is None


def test_ngay():
    assert parse_dates("30/11/2026 24/01/2027") == [date(2026, 11, 30), date(2027, 1, 24)]
    assert parse_dates("30/11/2026") == [date(2026, 11, 30)]
    assert parse_dates("") == []
    assert parse_dates("31/02/2027 15/02/2027") == [date(2027, 2, 15)]


def test_ten_hoc_ky():
    assert parse_semester_name("Học kỳ 2 Năm học 2026 - 2027 Đợt 2") == "HK2 2026–2027"
    assert parse_semester_name("Học kỳ 1 Năm học 2026 - 2027") == "HK1 2026–2027"
    assert parse_semester_name("Thời khoá biểu") is None
    assert parse_semester_name(None) is None


def test_so_tin_chi():
    assert parse_credits("3") == 3
    assert parse_credits("") is None
