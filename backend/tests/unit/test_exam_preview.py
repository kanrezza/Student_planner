from datetime import date, datetime, time

from app.lib.timeutil import TZ
from app.ocr.preview import build_preview
from app.services.exams import duplicate_key
from tests.ocr_helpers import context, load_boxes


def exam_rows(**ctx):
    boxes, size = load_boxes("real-exam-01")
    return build_preview(boxes, size, context(**ctx))["exam_rows"]


def test_kind_and_field_values():
    preview = build_preview(*load_boxes("real-exam-01"), context())
    assert preview["kind"] == "exam_table"
    first = preview["exam_rows"][0]["fields"]
    assert first["course_name"]["value"] == "Tối ưu hóa"
    assert first["date"]["value"] == "2026-11-30"
    assert (first["start_time"]["value"], first["end_time"]["value"]) == ("18:30", "20:00")
    assert first["exam_format"]["value"] == "Trắc nghiệm trên máy 90p"  # "9Op" đã sửa
    assert first["attempt"]["value"] == 1
    assert "Nguyễn Văn Test" not in str(preview) and "21010999" not in str(preview)


def test_past_exams_are_deselected():
    rows = exam_rows(now=datetime(2026, 11, 20, 12, 0, tzinfo=TZ))
    past = {r["fields"]["course_name"]["value"]: r["is_past"] for r in rows}
    assert past["Đồ án liên ngành"] is True  # 19/11 đã qua
    assert past["Tối ưu hóa"] is False
    assert all(r["selected"] is (not r["is_past"]) for r in rows)


def test_duplicate_of_existing_exam_is_deselected():
    key = duplicate_key("CSE703057", "Tối ưu hóa", date(2026, 11, 30), time(18, 30), 1)
    rows = exam_rows(exams=[(key, 42)])
    assert rows[0]["duplicate_of_exam_id"] == 42 and rows[0]["selected"] is False
    assert rows[1]["duplicate_of_exam_id"] is None


def test_second_attempt_is_not_a_duplicate_of_first():
    key = duplicate_key("CSE703057", "Tối ưu hóa", date(2026, 11, 30), time(18, 30), 2)
    assert exam_rows(exams=[(key, 42)])[0]["duplicate_of_exam_id"] is None


def test_duplicates_inside_the_image():
    boxes, size = load_boxes("real-exam-01")
    doubled = boxes + [
        b.__class__(b.text, b.x0, b.y0 + 701, b.x1, b.y1 + 701, b.conf)
        for b in boxes
        if 230 < b.y0 < 345
    ]
    rows = build_preview(doubled, (size[0], size[1] + 702), context())["exam_rows"]
    assert len(rows) == 6 and rows[5]["selected"] is False and rows[5]["duplicate_in_image"]


def test_missing_end_time_is_uncertain():
    boxes, size = load_boxes("real-exam-01")
    rows = build_preview([b for b in boxes if b.text != "17.00"], size, context())["exam_rows"]
    end = rows[2]["fields"]["end_time"]  # "Bài tập lớn": không có thời lượng để suy ra
    assert end["certain"] is False and end["value"] is None
    assert rows[0]["fields"]["end_time"]["certain"] is True
