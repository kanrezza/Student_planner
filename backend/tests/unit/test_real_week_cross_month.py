"""Ảnh thật tuần 30/11–06/12/2026 (vắt qua hai tháng, có ô "Lịch thi", ô bị cắt ở mép dưới).

Khối chữ trong `real-week-02.boxes.json` là kết quả OCR thật của ảnh (ảnh gốc không nằm trong git);
tên giảng viên trong đó đã được thay bằng tên giả vì repo công khai.
Đáp án dưới đây do người đọc ảnh viết tay.

Ngày, giờ, thứ, nhóm lớp và việc phân loại buổi học/buổi thi phải khớp hoàn toàn. Tên môn và phòng
là chữ nhỏ (~10 px) nên EasyOCR đọc sai vài ký tự ("Giao dlện nguòi máy"); đo trên ảnh gốc, tên
môn giống đáp án trung bình 86% (thấp nhất 74%). Ngưỡng bên dưới đặt sát số đo đó để bắt hồi quy;
người dùng sửa các chữ này ở bảng xem trước.
"""

from datetime import date

import pytest
from rapidfuzz import fuzz

from app.lib.text import ci_key
from app.ocr.preview import build_preview
from tests.ocr_helpers import context, load_boxes

# (ngày, giờ bắt đầu, giờ kết thúc, tên, phòng, giảng viên, nhóm lớp)
# Tiết 4–6 = Ca 2 = 09:30–12:10 (khớp cổng sinh viên).
SESSIONS = [
    ("2026-11-30", "06:45", "09:25", "Trực quan hoá dữ liệu", "A8-104", "Vũ Quốc Bảo", "2-2-26(N01)"),
    ("2026-11-30", "09:30", "12:10", "Bóng đá", "Sân bóng đá", "Phan Gia Huy", "2-2-26(N01)"),
    ("2026-11-30", "13:00", "15:40", "Tích hợp và phân tích dữ liệu lớn", "A6-301.302 (PC)", "Đỗ Thu Hà", None),
    ("2026-12-01", "13:00", "15:40", "Giao diện người máy", "A2-402.404", "Hồ Thanh Mai", "2-2-26(N02)"),
    ("2026-12-01", "21:05", "22:00", "Tích hợp và phân tích dữ liệu lớn", None, None, None),
    ("2026-12-04", "09:30", "12:10", "Xử lý ngôn ngữ tự nhiên", "A6-501 (PC)", "Mai Văn Lực", "2-2-26(N01)"),
    ("2026-12-05", "06:45", "09:25", "Giao diện người máy", "A6-101.102 (PC)", "Hồ Thanh Mai", None),
]  # fmt: skip


@pytest.fixture(scope="module")
def preview():
    boxes, size = load_boxes("real-week-02")
    return build_preview(boxes, size, context())


def close(got, want, floor=70):
    return fuzz.ratio(ci_key(str(got)), ci_key(want)) >= floor


def by_key(rows):
    return {(r["fields"]["date"]["value"], r["fields"]["start_time"]["value"]): r for r in rows}


def test_month_comes_from_mini_calendar_even_at_the_top_edge(preview):
    assert preview["kind"] == "week_schedule"
    assert preview["month_year"]["value"] == "2026-12"
    assert preview["month_year"]["source"] == "mini_calendar"


def test_week_crossing_two_months_gets_consecutive_dates(preview):
    # Cột "30 Thứ 2" là 30/11 dù lịch nhỏ ghi tháng 12; 01, 02… thuộc tháng 12
    dates = {r["fields"]["date"]["value"] for r in preview["rows"]}
    assert dates == {"2026-11-30", "2026-12-01", "2026-12-04", "2026-12-05"}
    for row in preview["rows"]:
        day = date.fromisoformat(row["fields"]["date"]["value"])
        assert day.isoweekday() == row["fields"]["weekday"]["value"]
        assert row["fields"]["weekday"]["certain"] and row["fields"]["date"]["certain"]


def test_every_session_is_read(preview):
    rows = by_key(preview["rows"])
    assert len(preview["rows"]) == len(SESSIONS)  # không thừa dòng từ phần "Lớp học phần"
    for day, start, end, name, room, lecturer, code in SESSIONS:
        fields = rows[(day, start)]["fields"]
        assert fields["end_time"]["value"] == end, (day, start)
        assert close(fields["name"]["value"], name), (day, start, fields["name"]["value"])
        if room:
            assert close(fields["room"]["value"], room, 85), (day, start, fields["room"]["value"])
        if lecturer:
            assert close(fields["lecturer"]["value"], lecturer), (day, start)
        if code:
            assert fields["class_code"]["value"] == code, (day, start)


def test_exam_cell_is_an_exam_not_a_subject(preview):
    assert not any(r["fields"]["start_time"]["value"] == "18:30" for r in preview["rows"])
    (exam,) = preview["exam_rows"]
    fields = exam["fields"]
    assert fields["date"]["value"] == "2026-11-30"
    assert (fields["start_time"]["value"], fields["end_time"]["value"]) == ("18:30", "20:00")
    assert fields["room"]["value"] == "A6-101.102 (PC)"
    assert close(fields["exam_format"]["value"], "Trắc nghiệm trên máy 90p", 70)
    assert exam["selected"] is True and exam["is_past"] is False
    assert fields["course_name"]["certain"] is False  # tiêu đề chữ trắng nhỏ, OCR đọc kém


def test_exam_name_is_corrected_from_known_subjects():
    boxes, size = load_boxes("real-week-02")
    preview = build_preview(boxes, size, context(subject_names=["Tối ưu hóa", "Bóng đá"]))
    (exam,) = preview["exam_rows"]
    assert exam["fields"]["course_name"]["value"] == "Tối ưu hóa"
    assert exam["fields"]["course_name"]["certain"] is False  # đoán theo tên có sẵn → xem lại


def test_cut_cell_keeps_title_fields_but_is_uncertain(preview):
    row = by_key(preview["rows"])[("2026-12-01", "21:05")]
    assert row["truncated"] is True
    for key in ("name", "start_time", "end_time"):
        assert row["fields"][key]["certain"] is False, key
        assert "mép dưới" in row["fields"][key]["reason"]
    assert row["fields"]["room"]["value"] is None
    # các ô đầy đủ không bị đánh dấu cắt
    assert [r["truncated"] for r in preview["rows"]].count(True) == 1


def test_cut_cell_name_is_matched_to_the_same_subject_in_the_image(preview):
    rows = by_key(preview["rows"])
    cut = rows[("2026-12-01", "21:05")]["fields"]["name"]["value"]
    full = rows[("2026-11-30", "13:00")]["fields"]["name"]["value"]
    assert cut == full
