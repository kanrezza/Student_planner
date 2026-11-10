import json
from datetime import time

from app.ocr.exam_table import format_duration, parse_exam_table
from app.ocr.layout import detect_layout, find_week_headers
from tests.ocr_helpers import box, load_boxes

COLS = {  # tên cột → x trái
    "stt": 40, "code": 120, "name": 280, "attempt": 720, "date": 790,
    "time": 940, "format": 1090, "room": 1350, "sbd": 1550, "student": 1670,
}  # fmt: skip
FAKE_NAME, FAKE_ID = "Nguyễn Văn Test", "21010999"


def header_boxes(accents=True):
    t = (lambda a, b: a) if accents else (lambda a, b: b)
    return [
        box("STT", COLS["stt"], 120, w=45),
        box(t("Mã học", "Ma hoc"), COLS["code"], 120, w=70), box("phần" if accents else "phan", COLS["code"], 142, w=50),
        box(t("Tên học phần", "Ten hoc phan"), COLS["name"], 130, w=150),
        box("Lần", COLS["attempt"], 120, w=36), box("thi", COLS["attempt"] + 2, 142, w=30),
        box(t("Ngày thi", "Ngay thi"), COLS["date"], 130, w=90),
        box(t("Thời gian", "Thoi gian"), COLS["time"], 120, w=100), box("thi", COLS["time"], 142, w=30),
        box(t("Hình thức", "Hinh thuc"), COLS["format"], 130, w=100),
        box(t("Phòng thi", "Phong thi"), COLS["room"], 130, w=100),
        box(t("Số báo", "So bao"), COLS["sbd"], 120, w=70), box("danh", COLS["sbd"] + 8, 142, w=50),
        box("Thông tin sinh viên ( Họ tên,", COLS["student"], 120, w=280), box("mã số)", COLS["student"], 142, w=80),
    ]  # fmt: skip


def row(y, n, code, name_lines, date, times, fmt_lines, room_lines, sbd):
    boxes = [
        box(str(n), COLS["stt"] + 14, y, w=12), box(code, COLS["code"], y, w=100),
        box("1", COLS["attempt"] + 8, y, w=10), box(date, COLS["date"], y, w=100),
        box(sbd, COLS["sbd"] + 10, y, w=30),
        box(f"{FAKE_NAME} - {FAKE_ID} -", COLS["student"], y, w=280),
    ]  # fmt: skip
    for i, line in enumerate(name_lines):
        boxes.append(box(line, COLS["name"], y - 10 + 22 * i, w=300))
    for i, line in enumerate(times):
        boxes.append(box(line, COLS["time"], y - 10 + 22 * i, w=70))
    for i, line in enumerate(fmt_lines):
        boxes.append(box(line, COLS["format"], y - 10 + 22 * i, w=200))
    for i, line in enumerate(room_lines):
        boxes.append(box(line, COLS["room"], y - 10 + 22 * i, w=120))
    return boxes


def table(accents=True):
    return (
        header_boxes(accents)
        + [box("Lịch thi cá nhân", 20, 50, w=200, h=30)]
        + row(220, 1, "CSE703057", ["Tối ưu hóa"], "30/11/2026", ["18.30 -", "20.00"],
              ["Trắc nghiệm trên máy", "90p"], ["A6-101.102", "(PC)"], "21")
        + row(330, 2, "CSE703010", ["Đánh giá và kiểm định chất lượng", "phần mềm*"], "14/11/2026",
              ["07:30"], ["Trắc nghiệm trên máy", "6Op"], [], "84")
        + row(440, 3, "CSE703014", ["Đồ án liên ngành"], "19/11/2026", ["08:00 - 17:00"], ["Bài tập lớn"], [], "72")
    )  # fmt: skip


def test_detect_exam_table_and_not_week_grid():
    assert detect_layout(table()) == "exam_table"
    assert find_week_headers(table()) == []


def test_headers_without_accents_still_recognized():
    assert detect_layout(table(accents=False)) == "exam_table"
    assert len(parse_exam_table(table(accents=False))) == 3


def test_multiline_cells_are_joined_per_row():
    rows = parse_exam_table(table())
    assert [r.course_code[0] for r in rows] == ["CSE703057", "CSE703010", "CSE703014"]
    assert rows[1].course_name[0] == "Đánh giá và kiểm định chất lượng phần mềm*"
    assert rows[0].room[0] == "A6-101.102 (PC)"
    assert rows[0].exam_format[0] == "Trắc nghiệm trên máy 90p"  # "9Op" … sửa ở test dưới
    assert rows[0].date[0].isoformat() == "2026-11-30"


def test_student_columns_never_leak():
    rows = parse_exam_table(table())
    blob = json.dumps([r.__dict__ for r in rows], default=str, ensure_ascii=False)
    assert FAKE_NAME not in blob and FAKE_ID not in blob
    assert rows[0].candidate_number[0] == "21"  # số báo danh vẫn được giữ


def test_times():
    rows = parse_exam_table(table())
    assert (rows[0].start_time[0], rows[0].end_time[0]) == (time(18, 30), time(20, 0))
    assert rows[0].end_time_source == "image"
    assert (rows[2].start_time[0], rows[2].end_time[0]) == (time(8, 0), time(17, 0))


def test_end_time_from_format_duration():
    row = parse_exam_table(table())[1]
    assert row.start_time[0] == time(7, 30) and row.end_time[0] == time(8, 30)
    assert row.end_time_source == "format_duration"  # "6Op" được hiểu là 60p


def test_no_duration_means_no_end_time():
    boxes = [b for b in table() if b.text != "6Op"]
    boxes.append(box("Tự luận", COLS["format"], 330 + 12, w=100))
    row = parse_exam_table(boxes)[1]
    assert row.end_time[0] is None and row.end_time_source is None


def test_empty_room_and_unknown_when_not_a_table():
    assert parse_exam_table(table())[1].room[0] is None
    assert parse_exam_table([box("không phải bảng", 10, 10)]) == []


def test_format_duration():
    assert format_duration("Trắc nghiệm trên máy 60p") == 60
    assert format_duration("Tự luận 90 phút") == 90
    assert format_duration("Trắc nghiệm trên máy 6Op") == 60
    assert format_duration("Bài tập lớn") is None


def test_real_exam_table():
    boxes, _ = load_boxes("real-exam-01")
    assert detect_layout(boxes) == "exam_table"
    rows = parse_exam_table(boxes)
    assert [r.course_code[0] for r in rows] == [
        "CSE703057", "CSE703004", "CSE703014", "CSE703010", "CSE702049",
    ]  # fmt: skip
    assert rows[3].course_name[0] == "Đánh giá và kiểm định chất lượng phần mềm*"
    assert rows[2].room[0] is None
    assert FAKE_ID not in json.dumps([r.__dict__ for r in rows], default=str)
