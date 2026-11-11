"""Bố cục bảng: cột thứ theo toạ độ chữ tiêu đề, hàng theo đường kẻ, bỏ phần đầu và cuối trang."""

import pytest

from app.pdfimport.layout import find_header, parse_table
from app.pdfimport.reader import PdfImportError, read_pdf
from tests.ocr_helpers import load_pdf

SECRETS = ["Nguyễn", "21010999", "K99-TEST_1", "Test"]


def _all_text(table) -> str:
    return " ".join(line for row in table.rows for lines in row.cells.values() for line in lines)


@pytest.mark.parametrize("name", ["tkb-synthetic-01", "tkb-synthetic-2pages"])
def test_16_hang_va_khong_ro_ri_phan_dau(name):
    table = parse_table(read_pdf(load_pdf(f"{name}.pdf")))
    assert len(table.rows) == 16
    assert table.semester_line == "Học kỳ 2 Năm học 2026 - 2027"
    text = _all_text(table)
    for secret in SECRETS:
        assert secret not in text
    assert "Tổng" not in text


def test_tieu_de_co_du_bay_cot_thu():
    page = read_pdf(load_pdf("tkb-synthetic-01.pdf"))[0]
    header = find_header(page)
    keys = [c.key for c in header.columns]
    for key in ("course", "class", "d1", "d2", "d3", "d4", "d5", "d6", "d7", "dates"):
        assert key in keys
    lefts = [c.left for c in header.columns]
    assert lefts == sorted(lefts)


def test_ban_hai_trang_du_hang():
    pages = read_pdf(load_pdf("tkb-synthetic-2pages.pdf"))
    assert len(pages) == 2
    assert len(parse_table(pages).rows) == 16


def test_khong_phai_thoi_khoa_bieu():
    with pytest.raises(PdfImportError) as err:
        parse_table(read_pdf(load_pdf("tkb-not-timetable.pdf")))
    assert err.value.code == "pdf_not_timetable"
