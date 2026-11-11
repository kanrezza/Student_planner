"""Gộp hàng thành môn, đổi tiết sang giờ, chọn học kỳ (hàm thuần, không CSDL)."""

import json
from datetime import date
from types import SimpleNamespace

from app.pdfimport.layout import parse_table
from app.pdfimport.preview import PreviewContext, build_timetable_preview, choose_semester
from app.pdfimport.reader import read_pdf
from app.services.periods import default_periods
from tests.ocr_helpers import FIXTURES, load_pdf, shifts


def _ctx(semesters=()):
    ca = shifts()
    return PreviewContext(shifts=ca, periods=default_periods(ca), semesters=list(semesters))


def _preview():
    table = parse_table(read_pdf(load_pdf("tkb-synthetic-01.pdf")))
    return build_timetable_preview(table.rows, table.semester_line, _ctx())


def test_khop_dap_an():
    expected = json.loads((FIXTURES / "tkb-synthetic-01.expected.json").read_text("utf-8"))
    preview = _preview()
    assert preview["semester"]["suggested_name"] == expected["semester_name"]
    assert len(preview["subjects"]) == expected["subject_count"]
    assert sum(len(s["schedules"]) for s in preview["subjects"]) == expected["rule_count"]
    by_key = {(s["course_code"], s["class_code"]): s for s in preview["subjects"]}
    for want in expected["subjects"]:
        got = by_key[(want["course_code"], want["class_code"])]
        assert (got["name"], got["credits"]) == (want["name"], want["credits"])
        rule = lambda r: (  # noqa: E731
            r["weekday"],
            r["period_from"],
            r["period_to"],
            r["room"],
            r["start_date"],
            r["end_date"],
        )
        assert sorted(map(rule, got["schedules"])) == sorted(map(rule, want["rules"]))


def test_n02_va_n02_th1_la_hai_mon():
    codes = [s["class_code"] for s in _preview()["subjects"] if "N02" in (s["class_code"] or "")]
    assert sorted(codes) == ["2-2-26(N02)", "2-2-26(N02.TH1)"]


def test_tiet_doi_sang_ca_va_gio():
    preview = _preview()
    football = next(s for s in preview["subjects"] if s["name"] == "Bóng đá")
    rule = football["schedules"][0]
    assert rule["shift"] == {"start_shift_id": 2, "end_shift_id": 2}
    assert (rule["start_time"], rule["end_time"]) == ("09:30", "12:10")
    odd = next(
        r
        for s in preview["subjects"]
        for r in s["schedules"]
        if (r["period_from"], r["period_to"]) == (1, 2)
    )
    assert odd["shift"] is None and (odd["start_time"], odd["end_time"]) == ("06:45", "08:30")
    evening = next(r for s in preview["subjects"] for r in s["schedules"] if r["period_from"] == 16)
    assert (evening["start_time"], evening["end_time"]) == ("21:05", "22:00")


def test_so_buoi_va_nhan_elearning():
    preview = _preview()
    football = next(s for s in preview["subjects"] if s["name"] == "Bóng đá")
    # 30/11/2026–24/01/2027 có 8 thứ Hai; 15/02–28/02/2027 có 2 thứ Hai.
    assert sorted(r["session_count"] for r in football["schedules"]) == [2, 8]
    online = next(s for s in preview["subjects"] if s["class_code"] == "2-2-26(COUR01)")
    assert online["suggested_tags"] == ["e_learning"]
    assert football["suggested_tags"] == []


def test_hoc_ky_tao_moi_voi_khoang_ngay_cua_quy_tac():
    semester = _preview()["semester"]
    assert semester["choice"] == "create"
    assert (semester["start_date"], semester["end_date"]) == ("2026-11-30", "2027-02-28")


def _sem(i, start, end, name="HK"):
    return SimpleNamespace(id=i, name=name, start_date=start, end_date=end)


def test_choose_semester():
    a, b = date(2026, 11, 30), date(2027, 2, 28)
    wide = _sem(1, date(2026, 9, 1), date(2027, 6, 30))
    narrow = _sem(2, date(2026, 11, 1), date(2027, 3, 15))
    assert choose_semester(a, b, [wide, narrow], "X")["semester_id"] == 2  # ngắn nhất
    assert (
        choose_semester(a, b, [_sem(3, date(2025, 1, 1), date(2025, 6, 1))], "X")["choice"]
        == "create"
    )
    part = choose_semester(a, b, [_sem(4, date(2026, 9, 1), date(2027, 1, 31))], "X")
    assert (part["choice"], part["semester_id"], part["end_date"]) == ("extend", 4, "2027-02-28")
    two = choose_semester(
        a,
        b,
        [
            _sem(5, date(2026, 9, 1), date(2026, 12, 31)),
            _sem(6, date(2027, 2, 1), date(2027, 6, 1)),
        ],
        "X",
    )
    assert two["choice"] == "conflict" and len(two["conflicts"]) == 2


def test_tiet_chua_co_gio_la_loi():
    ctx = _ctx()
    table = parse_table(read_pdf(load_pdf("tkb-synthetic-01.pdf")))
    ctx.periods = {k: v for k, v in ctx.periods.items() if k < 16}
    preview = build_timetable_preview(table.rows, table.semester_line, ctx)
    online = next(s for s in preview["subjects"] if s["class_code"] == "2-2-26(COUR01)")
    problems = online["schedules"][0]["problems"]
    assert any(
        p["level"] == "error" and "Chưa có giờ cho tiết 16–18" in p["message"] for p in problems
    )
