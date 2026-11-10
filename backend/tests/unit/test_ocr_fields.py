from datetime import time

from app.ocr.fields import (
    extract_exam_fields,
    extract_fields,
    fix_code_token,
    fix_digit_letters,
    is_e_learning,
    is_exam_cell,
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
    assert parse_room("Lê Minh Khoa") is None


def test_lecturer_and_class_code():
    assert parse_lecturer("GV: Nguyễn Văn A") == "Nguyễn Văn A"
    assert parse_lecturer("Giảng viên: ThS. Lê B") == "ThS. Lê B"
    assert parse_lecturer("Lê Minh Khoa") == "Lê Minh Khoa"
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
        "Cao Bích Ngọc",
    )
    fields = extract_fields(cell)
    assert fields["name"][0] == "Đánh giá và kiểm dịnh chất lượng phần mềm*"
    assert fields["class_code"][0] == "1-1-26(COUR01.LT2)"
    assert fields["room"][0] == "A6-101.102 (PC)"
    assert fields["lecturer"][0] == "Cao Bích Ngọc"
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


def test_time_line_with_ocr_damage():
    # "09.80" (3 → 8), giờ kết thúc dính liền "1210", "Tiết 46" thiếu dấu gạch (ảnh thật 30/11)
    assert parse_time_line("09.80-1210 (Tlet 4 6)") == (time(9, 30), time(12, 10), (4, 6))
    assert parse_time_line("09.30- 1210 (Tlet 46)") == (time(9, 30), time(12, 10), (4, 6))
    assert parse_time_line("06*45-09,25 (Tlet 1 3)") == (time(6, 45), time(9, 25), (1, 3))
    assert parse_time_line("21.05 - 22.00 (Tiet 16-18)") == (time(21, 5), time(22, 0), (16, 18))


def test_class_suffix_with_dropped_dash():
    assert split_class_label("Giao diện người máy-2-2 26(N02 TH1)") == (
        "Giao diện người máy",
        "2-2-26(N02.TH1)",
    )
    # nhãn bị ngắt dòng ngay sau "-2-2" và dòng sau mất dấu gạch
    cell = extract_fields(
        lines(
            "Tích hợp",
            "13.00 - 15.40 (Tiết 7-9)",
            "Tích hợp và phân tích dữ liệu lớn-2-2",
            "26(COUR01.LT2)",
            "A6-301.302 (PC)",
            "Đỗ Thu Hà",
        )
    )
    assert cell["name"][0] == "Tích hợp và phân tích dữ liệu lớn"
    assert cell["class_code"][0] == "2-2-26(COUR01.LT2)"


def test_place_before_lecturer_is_the_room():
    cell = extract_fields(
        lines(
            "Bóng đá",
            "09:30 - 12:10 (Tiết 4-6)",
            "Bóng đá-2-2-26(N01)",
            "Sân bóng đá",
            "Phan Gia Huy",
        )
    )
    assert cell["room"][0] == "Sân bóng đá" and cell["lecturer"][0] == "Phan Gia Huy"


def test_exam_cell_inside_week_grid():
    exam = lines(
        "Lịch thi: Tối ưu hóa",
        "18:30 - 20:00 (Ca 5)",
        "Trắc nghiệm trên máy 90p",
        "A6-101.102 (PC)",
    )
    assert is_exam_cell(exam)
    fields = extract_exam_fields(exam)
    assert fields["name"][0] == "Tối ưu hóa"
    assert fields["start_time"][0] == time(18, 30) and fields["end_time"][0] == time(20, 0)
    assert fields["exam_format"][0] == "Trắc nghiệm trên máy 90p"
    assert fields["room"][0] == "A6-101.102 (PC)"
    # OCR đọc hỏng tiêu đề: vẫn nhận ra nhờ "(Ca n)" thay cho "(Tiết a-b)"
    assert is_exam_cell(lines("Llch thl: Tal uuhóa", "18.30 - 20.00 (Ca 5)", "A6-101.102 (PC)"))
    assert is_exam_cell(lines("Bất kỳ", "18:30 - 20:00 (Ca 5)"))


def test_normal_cells_are_not_exam_cells():
    assert not is_exam_cell(
        lines("Giải tích", "06:45 - 09:25 (Tiết 1-3)", "MAT1101-1-1-26(N01)", "A101")
    )
    assert not is_exam_cell(lines("Giải tích", "Ca 2", "A101"))
