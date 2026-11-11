"""Gộp hàng thành môn, đổi tiết sang giờ, chọn học kỳ (hàm thuần, không CSDL)."""

import json
from datetime import date, time
from types import SimpleNamespace

import pytest

from app.pdfimport.layout import parse_table
from app.pdfimport.preview import (
    PreviewContext,
    apply_existing,
    build_timetable_preview,
    choose_semester,
    diff_subject,
    is_e_learning_room,
    match_existing,
)
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


# ---- Nhận ra môn đã có khi nhập lại (US3, R9) ----------------------------------------------------


def _existing(i, name, class_code, course_code, rules, semester_id=1, credits=None):
    schedules = [
        SimpleNamespace(
            weekdays=[wd],
            start_date=date.fromisoformat(sd),
            end_date=date.fromisoformat(ed),
            start_time=time.fromisoformat(st),
            end_time=time.fromisoformat(et),
            room=room,
        )
        for wd, sd, ed, st, et, room in rules
    ]
    return SimpleNamespace(
        id=i,
        name=name,
        class_code=class_code,
        course_code=course_code,
        credits=credits,
        semester_id=semester_id,
        schedules=schedules,
    )


def _subject(name="Bóng đá", class_code="2-2-26(N01)", course_code="FFS701069", **over):
    base = {
        "name": name,
        "class_code": class_code,
        "course_code": course_code,
        "credits": 1,
        "status": "new",
        "existing_subject_id": None,
        "diff": [],
        "selected": True,
        "schedules": [
            {
                "weekday": 1,
                "start_date": "2026-11-30",
                "end_date": "2027-01-24",
                "start_time": "09:30",
                "end_time": "12:10",
                "room": "Sân bóng đá",
                "selected": True,
            }
        ],
    }
    return {**base, **over}


RULE = (1, "2026-11-30", "2027-01-24", "09:30", "12:10", "Sân bóng đá")


def test_khop_theo_ma_lop_va_ma_hoc_phan_hoac_ten():
    sub = _subject()
    by_code = _existing(1, "Tên khác hẳn", "2-2-26(N01)", "ffs701069", [RULE])
    assert match_existing(sub, [by_code]) is by_code
    by_name = _existing(2, "BONG DA", "2-2-26(n01)", None, [RULE])  # môn tạo từ ảnh: không có mã HP
    assert match_existing(sub, [by_name]) is by_name


def test_cung_ma_lop_khac_ten_khong_khop_nham():
    other = _existing(3, "Giải tích", "2-2-26(N01)", "MAT1101", [RULE])
    assert match_existing(_subject(), [other]) is None
    # N02 và N02.TH1 cùng tên vẫn là hai môn.
    th = _existing(4, "Bóng đá", "2-2-26(N01.TH1)", "FFS701069", [RULE])
    assert match_existing(_subject(), [th]) is None


def test_unchanged_mac_dinh_bo_chon():
    subject = _subject()
    existing = _existing(1, "Bóng đá", "2-2-26(N01)", "FFS701069", [RULE], credits=1)
    assert diff_subject(existing, subject) == []
    apply_existing([subject], [existing])
    assert subject["status"] == "unchanged" and subject["selected"] is False
    assert subject["existing_subject_id"] == 1
    assert subject["schedules"][0]["selected"] is False


def test_changed_liet_ke_khac_biet():
    existing = _existing(
        1, "Bóng đá", "2-2-26(N01)", None,
        [(1, "2026-11-30", "2027-01-24", "09:30", "12:10", "Sân A"), (3, "2026-11-30", "2027-01-24", "09:30", "12:10", None)],
    )  # fmt: skip
    subject = _subject()
    diff = diff_subject(existing, subject)
    fields = [d["field"] for d in diff]
    assert {"Mã học phần", "Số tín chỉ", "Phòng", "Lịch"} <= set(fields)
    room = next(d for d in diff if d["field"] == "Phòng")
    assert (room["before"], room["after"]) == ("Sân A", "Sân bóng đá")
    removed = next(d for d in diff if d["field"] == "Lịch")
    assert removed["before"].startswith("T4") and removed["after"] is None
    apply_existing([subject], [existing])
    assert subject["status"] == "changed" and subject["selected"] is True


def test_chi_nhan_ra_mon_cua_hoc_ky_dich():
    ctx = _ctx(semesters=[_sem(1, date(2026, 9, 1), date(2027, 6, 30), "HK")])
    ctx.existing_subjects = [
        _existing(9, "Bóng đá", "2-2-26(N01)", "FFS701069", [RULE], semester_id=2)
    ]
    table = parse_table(read_pdf(load_pdf("tkb-synthetic-01.pdf")))
    preview = build_timetable_preview(table.rows, table.semester_line, ctx)
    assert preview["semester"]["choice"] == "use"
    assert all(s["status"] == "new" for s in preview["subjects"])


@pytest.mark.parametrize(
    ("room", "expected"),
    [
        ("ONLINE-Elearning", True),
        ("Elearning", True),
        ("E-Learning", True),
        ("online", True),
        ("A6-103 (PC)", False),
        ("Sân bóng đá", False),
        (None, False),
    ],
)
def test_phong_truc_tuyen_de_xuat_nhan_e_learning(room, expected):
    assert is_e_learning_room(room) is expected
