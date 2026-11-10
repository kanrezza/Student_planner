from datetime import date, time
from types import SimpleNamespace

from app.ocr.preview import ExistingSession, build_preview, shift_from_tiet, week_dates
from tests.ocr_helpers import box, context, load_boxes, shifts

SIZE = (2000, 1000)
PITCH = 250


def grid(cells, days=(2, 3, 4, 5, 6, 7, 8), mini="Tháng 11/2026"):
    labels = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "CN"]
    boxes = [box(mini, 1950, 250, w=150)]
    for i, label in enumerate(labels):
        x = 200 + PITCH * i
        boxes += [box(f"{days[i]:02d}", x - 40, 200, w=30, h=26), box(label, x, 205, w=60)]
    for col, y, lines in cells:
        for k, text in enumerate(lines):
            boxes.append(box(text, 160 + PITCH * col, y + 22 * k, w=200))
    return boxes


MATH = (
    0,
    300,
    [
        "Giải tích 1",
        "06:45 - 09:25 (Tiết 1-3)",
        "MAT1101-1-1-26(N01)",
        "Phòng: A2-301",
        "GV: ThS. An",
    ],
)


def preview(cells, ctx=None, **kw):
    return build_preview(grid(cells, **kw), SIZE, ctx or context())


def test_row_fields_shift_and_dates():
    p = preview([MATH])
    assert p["kind"] == "week_schedule" and p["month_year"]["value"] == "2026-11"
    row = p["rows"][0]
    f = row["fields"]
    assert (f["name"]["value"], f["date"]["value"], f["weekday"]["value"]) == (
        "Giải tích 1",
        "2026-11-02",
        1,
    )
    assert (f["start_time"]["value"], f["end_time"]["value"]) == ("06:45", "09:25")
    assert row["shift"] == {"start_shift_id": 1, "end_shift_id": 1} and row["shift_note"] is None
    assert row["semester_id"] == 7
    assert row["repeat"] == {"mode": "weekly", "until": "2026-12-20"}
    assert row["selected"] is True and row["duplicate_of_session_id"] is None


def test_time_within_five_minutes_snaps_to_shift_and_custom_time_has_note():
    snapped = preview([(0, 300, ["Toán", "06:47 - 09:22", "A101"])])["rows"][0]
    assert (
        snapped["fields"]["start_time"]["value"] == "06:45"
        and snapped["shift"]["start_shift_id"] == 1
    )
    custom = preview([(0, 300, ["Toán", "20:00 - 21:30", "A101"])])["rows"][0]
    assert custom["shift"] is None and "không khớp ca nào" in custom["shift_note"]
    assert custom["fields"]["start_time"]["value"] == "20:00"


def test_range_of_shifts_from_tiet_when_time_unreadable():
    row = preview([(0, 300, ["Toán", "(Tiết 1-6)", "MAT1101-1-1-26(N01)"])])["rows"][0]
    assert row["shift"] == {"start_shift_id": 1, "end_shift_id": 2}
    assert row["fields"]["end_time"]["value"] == "12:10"
    assert row["fields"]["start_time"]["certain"] is False  # giờ lấy theo tiết → cần kiểm tra
    assert (
        shift_from_tiet((7, 9), shifts()) == (3, 3) and shift_from_tiet((16, 17), shifts()) is None
    )


def test_weekday_mismatch_is_flagged():
    wrong, certain = week_dates([2, 3, 4, 5, 6, 7, 8], [1, 2, 3, 4, 5, 6, 7], (2026, 11))
    assert certain and wrong[0] == date(2026, 11, 2)
    # Tháng gợi ý sai (10) → thử tháng khác cho khớp thứ, và không còn "chắc chắn"
    fixed, certain = week_dates([2, 3, 4, 5, 6, 7, 8], [1, 2, 3, 4, 5, 6, 7], (2026, 10))
    assert fixed[0] == date(2026, 11, 2) and certain is False


def test_week_spanning_two_months_picks_the_matching_option():
    dates, certain = week_dates([28, 29, 30, 1, 2, 3, 4], [1, 2, 3, 4, 5, 6, 7], (2026, 10))
    assert dates[0] == date(2026, 9, 28) and dates[3] == date(2026, 10, 1) and certain
    dates, _ = week_dates([28, 29, 30, 31, 1, 2, 3], [1, 2, 3, 4, 5, 6, 7], (2026, 12))
    assert dates[0] == date(2026, 12, 28) and dates[4] == date(2027, 1, 1)


def test_no_semester_means_once_and_none():
    ctx = context(semesters=[])
    row = preview([MATH], ctx)["rows"][0]
    assert row["semester_id"] is None and row["repeat"]["mode"] == "once"


def test_duplicate_with_database_and_between_rows():
    existing = ExistingSession(5, "giải tích 1", None, date(2026, 11, 2), time(6, 45))
    rows = preview([MATH], context(sessions=[existing]))["rows"]
    assert rows[0]["duplicate_of_session_id"] == 5 and rows[0]["selected"] is False
    twice = preview([MATH, (0, 600, MATH[2])])["rows"]
    assert [r["selected"] for r in twice] == [True, False]
    # cùng mã lớp cũng là trùng
    by_code = ExistingSession(6, "Tên khác", "MAT1101-1-1-26(N01)", date(2026, 11, 2), time(6, 45))
    assert preview([MATH], context(sessions=[by_code]))["rows"][0]["duplicate_of_session_id"] == 6


def test_low_confidence_marks_field_uncertain():
    boxes = grid([MATH])
    boxes = [
        b.__class__(b.text, b.x0, b.y0, b.x1, b.y1, 0.3) if b.text == "Giải tích 1" else b
        for b in boxes
    ]
    row = build_preview(boxes, SIZE, context())["rows"][0]
    assert row["fields"]["name"]["certain"] is False and row["fields"]["name"]["reason"]


def test_name_is_corrected_from_known_subjects():
    row = preview(
        [(0, 300, ["Giải tich 1", "06:45 - 09:25", "A101"])], context(subject_names=["Giải tích 1"])
    )["rows"][0]
    assert (
        row["fields"]["name"]["value"] == "Giải tích 1" and row["fields"]["name"]["certain"] is True
    )


def test_e_learning_tag_suggestion():
    row = preview([(1, 300, ["Triết học", "20:00 - 21:30", "E-Learning"])])["rows"][0]
    assert (
        row["suggested_tags"] == ["e_learning"] and row["fields"]["room"]["value"] == "E-Learning"
    )


def test_merge_group_for_same_name_weekday_time():
    cells = [MATH, (0, 600, ["Giải tích 1", "06:45 - 09:25 (Tiết 1-3)", "A101"])]
    rows = preview(cells)["rows"]
    # hai ô cùng thứ, cùng giờ trong một ảnh tuần → cùng nhóm gộp, mặc định chưa gộp
    assert rows[0]["merge_group"] == rows[1]["merge_group"] is not None
    assert rows[0]["merge_accepted"] is False


def test_unknown_when_image_has_no_table():
    assert build_preview([box("Ảnh bất kỳ", 10, 100)], SIZE, context()) == {"kind": "unknown"}


def test_real_week_grid_end_to_end():
    boxes, size = load_boxes("real-grid-01")
    p = build_preview(
        boxes,
        size,
        context(
            semesters=[
                SimpleNamespace(id=7, start_date=date(2026, 8, 17), end_date=date(2026, 10, 25))
            ]
        ),
    )
    assert p["month_year"]["value"] == "2026-10"
    good = {
        (r["fields"]["date"]["value"], r["fields"]["start_time"]["value"]): r for r in p["rows"]
    }
    row = good[("2026-10-02", "13:00")]
    assert (
        row["fields"]["room"]["value"] == "A6-103 (PC)"
        and row["fields"]["lecturer"]["value"] == "Lê Minh Khoa"
    )
    assert row["fields"]["class_code"]["value"] == "1-1-26(N01.TH2)"
    assert row["fields"]["weekday"]["certain"] is True and row["repeat"]["until"] == "2026-10-25"
    assert good[("2026-09-30", "06:45")]["fields"]["name"]["value"].startswith("An toàn và b")
