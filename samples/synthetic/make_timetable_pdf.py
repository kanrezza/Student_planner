"""Tạo PDF "Thời khóa biểu chính thức" GIẢ LẬP cho test nhập học kỳ từ PDF (feature 004).

⚠️ ĐÂY LÀ FILE GIẢ LẬP. Họ tên, mã sinh viên, khoá/lớp là giá trị bịa; nội dung lịch mô phỏng bố cục của
cổng sinh viên (bảng có đường kẻ, chữ trong ô bị ngắt dòng giữa mã học phần, tên lớp học phần và phòng).
Không dùng dữ liệu thật; PDF thật của người dùng chỉ nằm trong samples/ (bị .gitignore chặn).

Chạy (trong container backend, cần reportlab và phông DejaVu):

  docker run --rm -v "$PWD:/repo" -w /repo --entrypoint sh lichhoc-backend:latest -c \
      "pip install -q reportlab && python samples/synthetic/make_timetable_pdf.py"

Đầu ra (mặc định backend/tests/fixtures/timetables/):
  tkb-synthetic-01.pdf         bảng 1 trang, 16 dòng, 8 môn, 17 quy tắc
  tkb-synthetic-01.answer.json  đáp án viết tay, độc lập với bộ đọc PDF
  tkb-synthetic-2pages.pdf     cùng nội dung, bảng tràn sang trang 2 (không lặp tiêu đề)
  tkb-no-text.pdf              chỉ có ảnh, không có chữ
  tkb-encrypted.pdf            có mật khẩu
  tkb-not-timetable.pdf        có chữ nhưng không phải thời khoá biểu
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

DEFAULT_OUT = Path(__file__).resolve().parents[2] / "backend" / "tests" / "fixtures" / "timetables"

FONT_DIRS = ["/usr/share/fonts/truetype/dejavu", "/System/Library/Fonts/Supplemental"]
FONT_FILES = {"DejaVu": "DejaVuSans.ttf", "DejaVu-Bold": "DejaVuSans-Bold.ttf"}

FAKE_NAME = "Nguyễn Văn Test"
FAKE_ID = "21010999"
FAKE_CLASS = "K99-TEST_1"
MUST_NOT_APPEAR = [FAKE_NAME, FAKE_ID, FAKE_CLASS]

# Cột: (tiêu đề, độ rộng pt). Các cột thứ nằm giữa "Số TC" và "Thời gian".
COLUMNS = [
    ("STT", 20),
    ("Mã HP", 38),
    ("Lớp học phần", 92),
    ("Số TC", 24),
    ("Thứ 2", 44),
    ("Thứ 3", 44),
    ("Thứ 4", 44),
    ("Thứ 5", 44),
    ("Thứ 6", 44),
    ("Thứ 7", 38),
    ("CN", 28),
    ("Thời gian", 56),
    ("Học phí", 38),
]
LEFT = 20
TOP_TABLE = 690
HEADER_H = 24
LINE_H = 8.6
PAD = 4
BODY_SIZE = 6.6

# Mỗi dòng của bảng: số thứ tự, mã HP và tên lớp học phần (kèm chỗ ngắt dòng như file thật), số tín chỉ,
# các ô thứ {thứ: (các dòng chữ trong ô, tiết đầu, tiết cuối, phòng ĐÃ GHÉP — đáp án)}, khoảng ngày.
ROWS = [
    dict(stt=1, code=["FFS7010", "69"], label=["Bóng đá-2-2-26(N01)"], tc=1,
         cells={0: (["4 - 6 (Sân", "bóng đá)"], 4, 6, "Sân bóng đá")},
         dates=("15/02/2027", "28/02/2027")),
    dict(stt=1, code=["FFS7010", "69"], label=["Bóng đá-2-2-26(N01)"], tc=1,
         cells={0: (["4 - 6 (Sân", "bóng đá)"], 4, 6, "Sân bóng đá")},
         dates=("30/11/2026", "24/01/2027")),
    dict(stt=2, code=["CSE703", "016"], label=["Giao diện người", "máy-2-2-26(N02.TH1)"], tc=3,
         cells={5: (["1 - 3", "(A6-1", "03", "(PC))"], 1, 3, "A6-103 (PC)")},
         dates=("15/02/2027", "28/02/2027")),
    dict(stt=2, code=["CSE703", "016"], label=["Giao diện người", "máy-2-2-26(N02.TH1)"], tc=3,
         cells={5: (["1 - 3", "(A6-1", "01.102", "(PC))"], 1, 3, "A6-101.102 (PC)")},
         dates=("30/11/2026", "24/01/2027")),
    dict(stt=3, code=["CSE703", "065"], label=["Xử lý ngôn ngữ tự", "nhiên-2-2-26(N01)"], tc=3,
         cells={1: (["4 - 6", "(A6-103", "(PC))"], 4, 6, "A6-103 (PC)")},
         dates=("15/02/2027", "28/02/2027")),
    dict(stt=3, code=["CSE703", "065"], label=["Xử lý ngôn ngữ tự", "nhiên-2-2-26(N01)"], tc=3,
         cells={1: (["4 - 6", "(A6-203", "(PC))"], 4, 6, "A6-203 (PC)"),
                4: (["4 - 6", "(A6-702", "(PC))"], 4, 6, "A6-702 (PC)")},
         dates=("21/12/2026", "24/01/2027")),
    dict(stt=3, code=["CSE703", "065"], label=["Xử lý ngôn ngữ tự", "nhiên-2-2-26(N01)"], tc=3,
         cells={4: (["4 - 6", "(A6-501", "(PC))"], 4, 6, "A6-501 (PC)")},
         dates=("30/11/2026", "20/12/2026")),
    dict(stt=4, code=["CSE703", "054"],
         label=["Tích hợp và phân tích dữ", "liệu", "lớn-2-2-26(COUR01.LT2)"], tc=3,
         cells={1: (["7 - 9", "(A6-103", "(PC))"], 7, 9, "A6-103 (PC)")},
         dates=("15/02/2027", "28/02/2027")),
    dict(stt=4, code=["CSE703", "054"],
         label=["Tích hợp và phân tích dữ", "liệu", "lớn-2-2-26(COUR01.LT2)"], tc=3,
         cells={1: (["7 - 9", "(A6-301.30", "2 (PC))"], 7, 9, "A6-301.302 (PC)")},
         dates=("30/11/2026", "24/01/2027")),
    dict(stt=5, code=["CSE702", "060"], label=["Trực quan hoá dữ", "liệu-2-2-26(N01.TH1)"], tc=2,
         cells={1: (["1 - 3", "(A6-103", "(PC))"], 1, 3, "A6-103 (PC)")},
         dates=("14/12/2026", "17/01/2027")),
    dict(stt=6, code=["CSE703", "016"], label=["Giao diện người", "máy-2-2-26(N02)"], tc=3,
         cells={1: (["7 - 9", "(A8-101)"], 7, 9, "A8-101")},
         dates=("15/02/2027", "28/02/2027")),
    dict(stt=6, code=["CSE703", "016"], label=["Giao diện người", "máy-2-2-26(N02)"], tc=3,
         cells={1: (["7 - 9", "(A2-402.40", "4)"], 7, 9, "A2-402.404")},
         dates=("30/11/2026", "24/01/2027")),
    dict(stt=7, code=["CSE702", "060"], label=["Trực quan hoá dữ", "liệu-2-2-26(N01)"], tc=2,
         cells={0: (["1 - 2", "(A8-104)"], 1, 2, "A8-104")},
         dates=("18/01/2027", "24/01/2027")),
    dict(stt=7, code=["CSE702", "060"], label=["Trực quan hoá dữ", "liệu-2-2-26(N01)"], tc=2,
         cells={0: (["1 - 3", "(A8-104)"], 1, 3, "A8-104")},
         dates=("30/11/2026", "17/01/2027")),
    dict(stt=8, code=["CSE703", "054"], label=["Tích hợp và phân tích dữ", "liệu lớn-2-2-26(COUR01)"],
         tc=3,
         cells={1: (["16 - 18", "(ONLINE-", "Elearning)"], 16, 18, "ONLINE-Elearning")},
         dates=("15/02/2027", "28/02/2027")),
    dict(stt=8, code=["CSE703", "054"], label=["Tích hợp và phân tích dữ", "liệu lớn-2-2-26(COUR01)"],
         tc=3,
         cells={1: (["16 - 18", "(ONLINE-", "Elearning)"], 16, 18, "ONLINE-Elearning")},
         dates=("30/11/2026", "24/01/2027")),
]
# Chỉ số cột thứ trong bảng: 0 = Thứ 2 … 5 = Thứ 7, 6 = CN. Trong đáp án `weekday` = chỉ số + 1
# (1 = Thứ Hai … 7 = Chủ Nhật, như isoweekday).

# Đáp án: nhãn lớp học phần → (tên môn, mã lớp), ghi tay thay vì tách bằng code của bộ đọc.
SUBJECTS_EXPECTED = {
    ("FFS701069", "2-2-26(N01)"): "Bóng đá",
    ("CSE703016", "2-2-26(N02.TH1)"): "Giao diện người máy",
    ("CSE703065", "2-2-26(N01)"): "Xử lý ngôn ngữ tự nhiên",
    ("CSE703054", "2-2-26(COUR01.LT2)"): "Tích hợp và phân tích dữ liệu lớn",
    ("CSE702060", "2-2-26(N01.TH1)"): "Trực quan hoá dữ liệu",
    ("CSE703016", "2-2-26(N02)"): "Giao diện người máy",
    ("CSE702060", "2-2-26(N01)"): "Trực quan hoá dữ liệu",
    ("CSE703054", "2-2-26(COUR01)"): "Tích hợp và phân tích dữ liệu lớn",
}
CREDITS = {
    ("FFS701069", "2-2-26(N01)"): 1,
    ("CSE703016", "2-2-26(N02.TH1)"): 3,
    ("CSE703065", "2-2-26(N01)"): 3,
    ("CSE703054", "2-2-26(COUR01.LT2)"): 3,
    ("CSE702060", "2-2-26(N01.TH1)"): 2,
    ("CSE703016", "2-2-26(N02)"): 3,
    ("CSE702060", "2-2-26(N01)"): 2,
    ("CSE703054", "2-2-26(COUR01)"): 3,
}


def register_fonts() -> None:
    for name, filename in FONT_FILES.items():
        for directory in FONT_DIRS:
            path = Path(directory) / filename
            if path.exists():
                pdfmetrics.registerFont(TTFont(name, str(path)))
                break
        else:
            sys.exit(f"Không tìm thấy phông {filename}; cài fonts-dejavu-core (xem docstring).")


def class_label_key(row: dict) -> tuple[str, str]:
    code = "".join(row["code"])
    label = " ".join(row["label"]).replace("- ", "-")
    # mã lớp nằm sau dấu "-" đầu tiên của dạng "-2-2-26(...)"
    class_code = label[label.index("-2-2-26") + 1 :]
    return code, class_code


def row_height(row: dict) -> float:
    lines = max(
        len(row["label"]),
        len(row["code"]),
        *(len(lines) for lines, *_ in row["cells"].values()),
        2,  # ô ngày luôn 2 dòng
    )
    return lines * LINE_H + 2 * PAD


def column_x() -> list[float]:
    xs = [LEFT]
    for _, width in COLUMNS:
        xs.append(xs[-1] + width)
    return xs


def draw_cell_lines(c: canvas.Canvas, x0: float, x1: float, top: float, lines: list[str], bold=True):
    c.setFont("DejaVu-Bold" if bold else "DejaVu", BODY_SIZE)
    y = top - PAD - BODY_SIZE
    for line in lines:
        c.drawCentredString((x0 + x1) / 2, y, line)
        y -= LINE_H


def draw_header(c: canvas.Canvas, xs: list[float], top: float) -> float:
    c.setFont("DejaVu-Bold", 7)
    for (title, _), x0, x1 in zip(COLUMNS, xs[:-1], xs[1:], strict=True):
        c.rect(x0, top - HEADER_H, x1 - x0, HEADER_H)
        if title == "Số TC":
            c.drawCentredString((x0 + x1) / 2, top - 10, "Số")
            c.drawCentredString((x0 + x1) / 2, top - 19, "TC")
        else:
            c.drawCentredString((x0 + x1) / 2, top - HEADER_H / 2 - 2.5, title)
    return top - HEADER_H


def draw_row(c: canvas.Canvas, xs: list[float], top: float, row: dict) -> float:
    height = row_height(row)
    for index, (x0, x1) in enumerate(zip(xs, xs[1:], strict=False)):
        c.rect(x0, top - height, x1 - x0, height)
    day_start = 4  # chỉ số cột "Thứ 2"
    draw_cell_lines(c, xs[0], xs[1], top, [str(row["stt"])])
    draw_cell_lines(c, xs[1], xs[2], top, row["code"])
    draw_cell_lines(c, xs[2], xs[3], top, row["label"])
    draw_cell_lines(c, xs[3], xs[4], top, [str(row["tc"])])
    for weekday_index, (lines, *_rest) in row["cells"].items():
        draw_cell_lines(c, xs[day_start + weekday_index], xs[day_start + weekday_index + 1], top, lines)
    draw_cell_lines(c, xs[11], xs[12], top, list(row["dates"]))
    return top - height


def draw_page_head(c: canvas.Canvas) -> None:
    width, height = A4
    c.setFont("DejaVu", 7)
    c.drawCentredString(95, height - 50, "ĐẠI HỌC PHENIKAA")
    c.setFont("DejaVu-Bold", 7)
    c.drawCentredString(95, height - 62, "PHÒNG ĐÀO TẠO")
    c.setFont("DejaVu-Bold", 12)
    c.drawCentredString(width / 2 + 40, height - 52, "THỜI KHÓA BIỂU CHÍNH THỨC")
    c.setFont("DejaVu-Bold", 7)
    c.drawCentredString(width / 2 + 40, height - 64, "Học kỳ 2 Năm học 2026 - 2027 Đợt 2")
    c.setFont("DejaVu", 7)
    c.drawString(80, height - 90, "Sinh viên :")
    c.drawString(80, height - 102, "Khóa, lớp :")
    c.setFont("DejaVu-Bold", 7)
    c.drawString(140, height - 90, FAKE_NAME)
    c.drawString(140, height - 102, FAKE_CLASS)
    c.setFont("DejaVu", 7)
    c.drawString(280, height - 90, "Mã sinh viên :")
    c.drawString(280, height - 102, "Ngành:")
    c.drawString(450, height - 90, "Số:")
    c.setFont("DejaVu-Bold", 7)
    c.drawString(340, height - 90, FAKE_ID)
    c.drawString(320, height - 102, "Công nghệ thông tin")


def draw_footer(c: canvas.Canvas, xs: list[float], top: float) -> None:
    c.setFont("DejaVu-Bold", 7)
    c.rect(xs[0], top - 11, xs[-1] - xs[0], 11)
    c.drawString(xs[0] + 2, top - 8, "Tổng cộng:")
    c.drawString(xs[0] + 2, top - 22, "Viết bằng chữ:")
    c.drawRightString(xs[-1], top - 22, "(................................................................đồng chẵn )")
    c.setFont("DejaVu", 6.5)
    c.drawRightString(xs[-1] - 20, top - 33, "Ngày 7 tháng 11 năm 2026")
    c.setFont("DejaVu-Bold", 7)
    c.drawString(xs[0] + 50, top - 48, "Họ tên và chữ ký của CVHT")
    c.drawRightString(xs[-1] - 8, top - 48, "Sinh viên (ký tên)")


def build_timetable(rows_per_page: list[int]) -> bytes:
    """PDF bảng thời khoá biểu; `rows_per_page` chia các dòng ra các trang (trang sau không lặp tiêu đề)."""
    register_fonts()
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    xs = column_x()
    remaining = list(ROWS)
    for page, count in enumerate(rows_per_page):
        top = TOP_TABLE
        if page == 0:
            draw_page_head(c)
            top = draw_header(c, xs, top)
        else:
            top = A4[1] - 60
        for row in remaining[:count]:
            top = draw_row(c, xs, top, row)
        remaining = remaining[count:]
        if page == len(rows_per_page) - 1:
            draw_footer(c, xs, top)
        c.showPage()
    c.save()
    return buffer.getvalue()


def build_no_text() -> bytes:
    """PDF chỉ có ảnh (như bản quét), không có ký tự nào."""
    image = Image.new("RGB", (600, 400), (235, 235, 235))
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.drawImage(ImageReader(image), 40, 400, width=500, height=330)
    c.save()
    return buffer.getvalue()


def build_encrypted() -> bytes:
    from reportlab.lib.pdfencrypt import StandardEncryption

    register_fonts()
    buffer = io.BytesIO()
    c = canvas.Canvas(
        buffer, pagesize=A4, encrypt=StandardEncryption("mat-khau-test", canPrint=1)
    )
    c.setFont("DejaVu", 10)
    c.drawString(60, 760, "THỜI KHÓA BIỂU CHÍNH THỨC")
    c.save()
    return buffer.getvalue()


def build_not_timetable() -> bytes:
    register_fonts()
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setFont("DejaVu-Bold", 12)
    c.drawString(60, 780, "Thông báo nghỉ lễ")
    c.setFont("DejaVu", 9)
    for i, line in enumerate(
        [
            "Nhà trường thông báo lịch nghỉ Tết Nguyên đán 2027 cho toàn thể sinh viên.",
            "Sinh viên theo dõi các thông báo tiếp theo trên cổng thông tin.",
        ]
    ):
        c.drawString(60, 755 - i * 14, line)
    c.save()
    return buffer.getvalue()


def expected_json() -> dict:
    """Đáp án máy đọc được: môn → các quy tắc (thứ 1–7, tiết, phòng, khoảng ngày theo dd/mm/yyyy → ISO)."""

    def iso(day: str) -> str:
        d, m, y = day.split("/")
        return f"{y}-{m}-{d}"

    subjects: dict[tuple[str, str], dict] = {}
    for row in ROWS:
        key = class_label_key(row)
        subject = subjects.setdefault(
            key,
            {
                "course_code": key[0],
                "class_code": key[1],
                "name": SUBJECTS_EXPECTED[key],
                "credits": CREDITS[key],
                "rules": [],
            },
        )
        for weekday_index, (_, first, last, room) in sorted(row["cells"].items()):
            subject["rules"].append(
                {
                    "weekday": weekday_index + 1,
                    "period_from": first,
                    "period_to": last,
                    "room": room,
                    "start_date": iso(row["dates"][0]),
                    "end_date": iso(row["dates"][1]),
                }
            )
    ordered = list(subjects.values())
    return {
        "semester_line": "Học kỳ 2 Năm học 2026 - 2027 Đợt 2",
        "semester_name": "HK2 2026–2027",
        "subject_count": len(ordered),
        "rule_count": sum(len(s["rules"]) for s in ordered),
        "must_not_appear": MUST_NOT_APPEAR,
        "subjects": ordered,
    }


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    out.mkdir(parents=True, exist_ok=True)
    files = {
        "tkb-synthetic-01.pdf": build_timetable([len(ROWS)]),
        "tkb-synthetic-2pages.pdf": build_timetable([10, len(ROWS) - 10]),
        "tkb-no-text.pdf": build_no_text(),
        "tkb-encrypted.pdf": build_encrypted(),
        "tkb-not-timetable.pdf": build_not_timetable(),
    }
    for name, data in files.items():
        (out / name).write_bytes(data)
        print(f"{name}: {len(data):,} byte")
    expected = expected_json()
    (out / "tkb-synthetic-01.answer.json").write_text(
        json.dumps(expected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"{expected['subject_count']} môn, {expected['rule_count']} quy tắc")


if __name__ == "__main__":
    main()
