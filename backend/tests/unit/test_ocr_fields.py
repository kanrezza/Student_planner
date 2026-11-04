from datetime import time

from app.ocr.fields import (
    extract_fields,
    fix_code_token,
    fix_digit_letters,
    is_e_learning,
    parse_lecturer,
    parse_room,
    parse_time_line,
    split_class_label,
)
from tests.ocr_helpers import box


def lines(*texts: str):
    return [box(t, 10, 10 + 22 * i, conf=0.9) for i, t in enumerate(texts)]


def test_time_formats():
    assert parse_time_line("07:30 - 09:30")[:2] == (time(7, 30), time(9, 30))
    assert parse_time_line("7h30-9h30")[:2] == (time(7, 30), time(9, 30))
    assert parse_time_line("07g30–09g30")[:2] == (time(7, 30), time(9, 30))
    # OCR hay đổi ":" thành "." hoặc "-", và làm rơi dấu gạch giữa hai giờ
    assert parse_time_line("06.45 09.25 (Tlết 1-3)") == (time(6, 45), time(9, 25), (1, 3))
    assert parse_time_line("13-00 15.40 (Tiết 7-9)")[:2] == (time(13, 0), time(15, 40))


def test_shift_and_tiet():
    assert parse_time_line("Tiết 1-3")[2] == (1, 3)
    assert extract_fields(lines("Giải tích", "Ca 2", "A101"))["shift_number"][0] == 2


def test_rooms():
    assert parse_room("A101") == "A101"
    assert parse_room("P.B2-305") == "B2-305"
    assert parse_room("Phòng: C1.204") == "C1.204"
    assert parse_room("Có mặtA6-101.102 (PC)") == "A6-101.102 (PC)"
    assert parse_room("Phòng: Sân thể thao") == "Sân thể thao"
    assert parse_room("Đoàn Trung Sơn") is None


def test_lecturer_and_class_code():
    assert parse_lecturer("GV: Nguyễn Văn A") == "Nguyễn Văn A"
    assert parse_lecturer("Giảng viên: ThS. Lê B") == "ThS. Lê B"
    assert parse_lecturer("Đoàn Trung Sơn") == "Đoàn Trung Sơn"
    assert parse_lecturer("A6-103 (PC)") is None
    fields = extract_fields(lines("Lập trình", "07:30 - 09:30", "INT1234_01", "Phòng: A101"))
    assert fields["class_code"][0] == "INT1234_01"


def test_e_learning():
    for text in ("E-Learning", "Elearning", "online", "Phòng: E-Learning"):
        assert is_e_learning(text)
    assert not is_e_learning("Phòng A101")
    fields = extract_fields(lines("Triết học", "20:00 - 21:30", "E-Learning"))
    assert fields["e_learning"][0] is True and fields["room"][0] == "E-Learning"


def test_name_is_longest_remaining_line_without_time_line():
    fields = extract_fields(lines("Toán", "Giải tích nâng cao", "A101"))
    assert fields["name"][0] == "Giải tích nâng cao"


def test_portal_cell_with_class_suffix():
    cell = lines(
        "Đánh giá và kiểm định chất lượng phần mềm*",  # tiêu đề (có thể sai dấu)
        "15.45 - 18.25 (Tlết 10-12)",
        "Đánh giá và kiểm dịnh chất lượng phần",
        "mềm*-1-1-26(COURO1.LT2)",
        "Có mặtA6-101.102 (PC)",
        "Trịnh Thanh Bình",
    )
    fields = extract_fields(cell)
    assert fields["name"][0] == "Đánh giá và kiểm dịnh chất lượng phần mềm*"
    assert fields["class_code"][0] == "1-1-26(COUR01.LT2)"
    assert fields["room"][0] == "A6-101.102 (PC)"
    assert fields["lecturer"][0] == "Trịnh Thanh Bình"
    assert fields["start_time"][0] == time(15, 45) and fields["tiet"][0] == (10, 12)


def test_labelled_cell_name_from_header():
    cell = lines(
        "Giải tích 1", "06:45 - 09:25 (Tiết 1-3)", "MAT1101-1-1-26(N01)",
        "Phòng: A2-301", "GV: ThS. Nguyễn Văn", "An",
    )  # fmt: skip
    fields = extract_fields(cell)
    assert fields["name"][0] == "Giải tích 1"
    assert fields["class_code"][0] == "MAT1101-1-1-26(N01)"
    assert fields["lecturer"][0] == "ThS. Nguyễn Văn An"  # tên xuống dòng được ghép


def test_tiet_wrapped_onto_next_line():
    cell = lines("Tiếng Anh 2", "15.45 18.25 (Tiết", "10-12)", "ENG1002-1-1-26(N08)")
    fields = extract_fields(cell)
    assert fields["name"][0] == "Tiếng Anh 2" and fields["tiet"][0] == (10, 12)


def test_ocr_confusion_fixes():
    assert fix_digit_letters("NO1") == "N01"
    assert fix_digit_letters("COURO1") == "COUR01"
    assert fix_digit_letters("TONG") == "TONG"
    assert fix_code_token("MATI101") == "MAT1101"
    assert fix_code_token("ENG10O1") == "ENG1001"
    assert split_class_label("Tối ưu hóa-1-1-26(N01)") == ("Tối ưu hóa", "1-1-26(N01)")
    assert split_class_label("Không có hậu tố") == ("Không có hậu tố", None)
