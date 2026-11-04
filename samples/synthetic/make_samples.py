"""Tạo ảnh thời khoá biểu GIẢ LẬP để chạy spike nhận diện ảnh (T010).

⚠️ ĐÂY LÀ ẢNH GIẢ LẬP, KHÔNG PHẢI ẢNH CHỤP THẬT. Bố cục mô phỏng trang "Lịch học" kiểu cổng
thông tin sinh viên (lịch tuần, mỗi cột một ngày có số ngày + Thứ, ô môn học nền xanh đậm, lịch
tháng thu nhỏ bên phải) đặt trong một ảnh chụp toàn màn hình macOS (thanh menu, trình duyệt,
Dock). Tên miền, tên môn, mã lớp, phòng, giảng viên đều là dữ liệu bịa. Kết quả spike trên các
ảnh này PHẢI được kiểm chứng lại bằng ảnh chụp thật.

Chạy: uv run --python 3.12 --with pillow samples/synthetic/make_samples.py
Đầu ra (cùng thư mục): sample-0N.png|jpg + sample-0N.expected.json
"""

from __future__ import annotations

import calendar
import json
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).parent

FONT_CANDIDATES = {
    "regular": [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ],
    "bold": [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
}

# Màu giao diện
MENU_BAR = (236, 236, 236)
CHROME = (222, 222, 226)
PAGE_BG = (245, 247, 250)
SIDEBAR = (24, 52, 99)
CELL_BLUE = (25, 55, 140)  # nền xanh đậm của ô môn học
GRID_LINE = (215, 220, 228)
TEXT_DARK = (33, 37, 41)
TEXT_MUTED = (120, 125, 135)
WHITE = (255, 255, 255)

WEEKDAY_LABELS = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "CN"]
GRID_START_HOUR = 6
GRID_END_HOUR = 22


@dataclass
class Session:
    name: str
    weekday: int  # 1 = Thứ 2 … 7 = Chủ nhật
    start: str  # "HH:MM"
    end: str
    tiet: str | None  # "1-3" hoặc None nếu giờ không theo tiết
    class_code: str
    room: str
    lecturer: str


@dataclass
class Sample:
    file_name: str
    week_monday: date
    scale: int  # 2 = màn hình Retina (ảnh 2880×1800), 1 = 1440×900
    menu_bar_text: str
    mini_calendar_month: tuple[int, int]  # (năm, tháng) hiển thị ở lịch thu nhỏ
    sessions: list[Session]
    jpeg_quality: int | None = None
    notes: str = ""


def load_font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES[kind]:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    raise FileNotFoundError(f"Không tìm thấy font {kind} hỗ trợ tiếng Việt")


def time_label(s: Session) -> str:
    text = f"{s.start} - {s.end}"
    return f"{text} (Tiết {s.tiet})" if s.tiet else text


def to_hours(hhmm: str) -> float:
    h, m = hhmm.split(":")
    return int(h) + int(m) / 60


def wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    words, lines, line = text.split(), [], ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def render(sample: Sample) -> Image.Image:
    S = sample.scale
    W, H = 1440 * S, 900 * S
    img = Image.new("RGB", (W, H), PAGE_BG)
    d = ImageDraw.Draw(img)
    f = lambda kind, size: load_font(kind, size * S)  # noqa: E731

    # --- Thanh menu macOS
    d.rectangle([0, 0, W, 24 * S], fill=MENU_BAR)
    d.text(
        (14 * S, 5 * S),
        "  Safari    Tệp    Sửa    Xem    Lịch sử    Dấu trang    Cửa sổ    Trợ giúp",
        font=f("regular", 13),
        fill=TEXT_DARK,
    )
    menu_font = f("regular", 13)
    d.text(
        (W - d.textlength(sample.menu_bar_text, font=menu_font) - 14 * S, 5 * S),
        sample.menu_bar_text,
        font=menu_font,
        fill=TEXT_DARK,
    )

    # --- Trình duyệt: thanh tab + thanh địa chỉ (tên miền giả)
    d.rectangle([0, 24 * S, W, 86 * S], fill=CHROME)
    d.rounded_rectangle([90 * S, 30 * S, 330 * S, 52 * S], radius=6 * S, fill=WHITE)
    d.text((104 * S, 34 * S), "Lịch học - Cổng sinh viên", font=f("regular", 12), fill=TEXT_DARK)
    d.rounded_rectangle([380 * S, 58 * S, 1060 * S, 80 * S], radius=6 * S, fill=WHITE)
    d.text(
        (395 * S, 61 * S),
        "sinhvien.example.edu.vn/lich-hoc",
        font=f("regular", 13),
        fill=TEXT_MUTED,
    )

    top = 86 * S

    # --- Sidebar trái
    d.rectangle([0, top, 190 * S, H], fill=SIDEBAR)
    d.text((20 * S, top + 18 * S), "CỔNG SINH VIÊN", font=f("bold", 14), fill=WHITE)
    for i, item in enumerate(["Trang chủ", "Lịch học", "Lịch thi", "Kết quả học tập", "Học phí"]):
        y = top + (60 + i * 36) * S
        if item == "Lịch học":
            d.rectangle([0, y - 8 * S, 190 * S, y + 24 * S], fill=(40, 80, 150))
        d.text((24 * S, y), item, font=f("regular", 14), fill=WHITE)

    # --- Tiêu đề trang + điều hướng tuần
    d.text((215 * S, top + 16 * S), "LỊCH HỌC", font=f("bold", 20), fill=TEXT_DARK)
    for i, label in enumerate(["‹ Tuần trước", "Hôm nay", "Tuần sau ›"]):
        x = (215 + 110 * i) * S
        d.rounded_rectangle(
            [x, top + 50 * S, x + 100 * S, top + 74 * S],
            radius=4 * S,
            outline=GRID_LINE,
            fill=WHITE,
        )
        d.text((x + 12 * S, top + 54 * S), label, font=f("regular", 12), fill=TEXT_DARK)

    # --- Lưới tuần
    grid_left, grid_right = 260 * S, 1150 * S
    header_top, header_h = top + 90 * S, 52 * S
    body_top, body_bottom = header_top + header_h, H - 90 * S
    col_w = (grid_right - grid_left) / 7
    hour_h = (body_bottom - body_top) / (GRID_END_HOUR - GRID_START_HOUR)

    d.rectangle([grid_left, header_top, grid_right, body_bottom], fill=WHITE, outline=GRID_LINE)
    for i in range(7):
        x0 = grid_left + i * col_w
        day = sample.week_monday + timedelta(days=i)
        d.line([x0, header_top, x0, body_bottom], fill=GRID_LINE, width=S)
        d.text(
            (x0 + 10 * S, header_top + 4 * S), f"{day.day:02d}", font=f("bold", 22), fill=TEXT_DARK
        )
        d.text(
            (x0 + 48 * S, header_top + 14 * S),
            WEEKDAY_LABELS[i],
            font=f("regular", 13),
            fill=TEXT_MUTED,
        )
    d.line([grid_left, body_top, grid_right, body_top], fill=GRID_LINE, width=S)
    for h in range(GRID_START_HOUR, GRID_END_HOUR + 1):
        y = body_top + (h - GRID_START_HOUR) * hour_h
        d.line([grid_left, y, grid_right, y], fill=(238, 240, 244), width=S)
        d.text(
            (grid_left - 44 * S, y - 7 * S), f"{h:02d}:00", font=f("regular", 11), fill=TEXT_MUTED
        )

    # --- Ô môn học
    name_font, line_font = f("bold", 11), f("regular", 10)
    for s in sample.sessions:
        x0 = grid_left + (s.weekday - 1) * col_w + 3 * S
        x1 = x0 + col_w - 6 * S
        y0 = body_top + (to_hours(s.start) - GRID_START_HOUR) * hour_h + 1 * S
        y1 = body_top + (to_hours(s.end) - GRID_START_HOUR) * hour_h - 1 * S
        d.rounded_rectangle([x0, y0, x1, y1], radius=4 * S, fill=CELL_BLUE)
        y = y0 + 4 * S
        for line in wrap(d, s.name, name_font, int(x1 - x0 - 10 * S)):
            d.text((x0 + 5 * S, y), line, font=name_font, fill=WHITE)
            y += 14 * S
        for line in [time_label(s), s.class_code, f"Phòng: {s.room}", f"GV: {s.lecturer}"]:
            for part in wrap(d, line, line_font, int(x1 - x0 - 10 * S)):
                d.text((x0 + 5 * S, y), part, font=line_font, fill=(225, 232, 255))
                y += 13 * S

    # --- Lịch tháng thu nhỏ bên phải
    year, month = sample.mini_calendar_month
    cx, cy = 1175 * S, header_top
    d.rounded_rectangle(
        [cx, cy, 1420 * S, cy + 230 * S], radius=6 * S, fill=WHITE, outline=GRID_LINE
    )
    d.text((cx + 14 * S, cy + 10 * S), f"Tháng {month}/{year}", font=f("bold", 14), fill=TEXT_DARK)
    cell = 33 * S
    for i, label in enumerate(["T2", "T3", "T4", "T5", "T6", "T7", "CN"]):
        d.text((cx + 12 * S + i * cell, cy + 40 * S), label, font=f("bold", 11), fill=TEXT_MUTED)
    week_days = {sample.week_monday + timedelta(days=i) for i in range(7)}
    for r, week in enumerate(calendar.Calendar(firstweekday=0).monthdatescalendar(year, month)):
        for c, day in enumerate(week):
            x, y = cx + 12 * S + c * cell, cy + (62 + r * 26) * S
            if day in week_days:
                d.rectangle([x - 4 * S, y - 3 * S, x + 24 * S, y + 17 * S], fill=(220, 230, 250))
            color = TEXT_DARK if day.month == month else (190, 195, 205)
            d.text((x, y), f"{day.day}", font=f("regular", 12), fill=color)

    # --- Ghi chú ảnh giả lập (góc dưới) + Dock
    d.text(
        (215 * S, H - 80 * S),
        "ẢNH GIẢ LẬP – dữ liệu không có thật, chỉ dùng để thử nhận diện",
        font=f("regular", 10),
        fill=(170, 170, 175),
    )
    d.rounded_rectangle(
        [420 * S, H - 62 * S, 1020 * S, H - 6 * S], radius=14 * S, fill=(210, 212, 218)
    )
    for i in range(10):
        x = (440 + i * 58) * S
        d.rounded_rectangle(
            [x, H - 54 * S, x + 42 * S, H - 14 * S],
            radius=9 * S,
            fill=(120 + i * 12, 140, 200 - i * 8),
        )
    return img


def expected(sample: Sample) -> dict:
    rows = []
    for s in sorted(sample.sessions, key=lambda s: (s.weekday, s.start)):
        day = sample.week_monday + timedelta(days=s.weekday - 1)
        row = asdict(s)
        row.update(
            date=day.isoformat(),
            start_time=s.start,
            end_time=s.end,
            time_label=time_label(s),
            e_learning=s.room == "E-Learning",
        )
        del row["start"], row["end"]
        rows.append(row)
    return {
        "synthetic": True,
        "warning": (
            "Ảnh giả lập, không phải ảnh chụp thật. Kết quả spike cần kiểm chứng lại bằng ảnh thật."
        ),
        "image": sample.file_name,
        "screen": f"{1440 * sample.scale}x{900 * sample.scale}",
        "menu_bar_text": sample.menu_bar_text,
        "mini_calendar_title": "Tháng {1}/{0}".format(*sample.mini_calendar_month),
        "week": {
            "monday": sample.week_monday.isoformat(),
            "sunday": (sample.week_monday + timedelta(days=6)).isoformat(),
        },
        "notes": sample.notes,
        "rows": rows,
    }


SAMPLES = [
    Sample(
        file_name="sample-01.png",
        week_monday=date(2026, 11, 2),
        scale=2,
        menu_bar_text="Th 4 4 thg 11 14:05",
        mini_calendar_month=(2026, 11),
        notes="Retina 2880×1800, PNG. Mọi buổi theo tiết chuẩn. Tháng/năm lấy từ lịch thu nhỏ.",
        sessions=[
            Session(
                "Giải tích 1",
                1,
                "06:45",
                "09:25",
                "1-3",
                "MAT1101-1-1-26(N01)",
                "A2-301",
                "ThS. Nguyễn Văn An",
            ),
            Session(
                "Lập trình hướng đối tượng",
                1,
                "13:00",
                "15:40",
                "7-9",
                "CSE2203-1-1-26(N03)",
                "A5-402",
                "TS. Trần Thị Bình",
            ),
            Session(
                "Triết học Mác - Lênin",
                2,
                "09:35",
                "12:10",
                "4-6",
                "PHI1001-1-1-26(N12)",
                "B1-205",
                "TS. Lê Minh Châu",
            ),
            Session(
                "Cơ sở dữ liệu",
                3,
                "06:45",
                "09:25",
                "1-3",
                "CSE2301-1-1-26(N02)",
                "A5-310",
                "ThS. Phạm Quốc Dũng",
            ),
            Session(
                "Tiếng Anh 2",
                3,
                "15:45",
                "18:25",
                "10-12",
                "ENG1002-1-1-26(N08)",
                "C2-104",
                "ThS. Hoàng Thu Hà",
            ),
            Session(
                "Kiến trúc máy tính",
                4,
                "09:35",
                "12:10",
                "4-6",
                "CSE2105-1-1-26(N01)",
                "A2-508",
                "TS. Vũ Đức Huy",
            ),
            Session(
                "Xác suất thống kê",
                5,
                "13:00",
                "15:40",
                "7-9",
                "MAT1205-1-1-26(N05)",
                "A2-301",
                "ThS. Đặng Thị Lan",
            ),
            Session(
                "Lập trình hướng đối tượng",
                6,
                "06:45",
                "09:25",
                "1-3",
                "CSE2203-1-1-26(N03)",
                "A5-402",
                "TS. Trần Thị Bình",
            ),
            Session(
                "Giáo dục thể chất 2",
                7,
                "15:45",
                "18:25",
                "10-12",
                "PES1002-1-1-26(N20)",
                "Sân thể thao",
                "ThS. Bùi Văn Long",
            ),
        ],
    ),
    Sample(
        file_name="sample-02.png",
        week_monday=date(2026, 11, 9),
        scale=1,
        menu_bar_text="Th 2 9 thg 11 08:30",
        mini_calendar_month=(2026, 11),
        notes=(
            "Màn hình thường 1440×900 (chữ nhỏ hơn, khó hơn). "
            "Có môn E-Learning (phòng 'E-Learning'), "
            "một buổi tối 20:00–21:30 không theo tiết, một buổi 07:00–09:00 lệch ca."
        ),
        sessions=[
            Session(
                "Giải tích 1",
                1,
                "06:45",
                "09:25",
                "1-3",
                "MAT1101-1-1-26(N01)",
                "A2-301",
                "ThS. Nguyễn Văn An",
            ),
            Session(
                "Triết học Mác - Lênin",
                2,
                "20:00",
                "21:30",
                None,
                "PHI1001-1-1-26(N12)",
                "E-Learning",
                "TS. Lê Minh Châu",
            ),
            Session(
                "Cơ sở dữ liệu",
                3,
                "07:00",
                "09:00",
                None,
                "CSE2301-1-1-26(N02)",
                "A5-310",
                "ThS. Phạm Quốc Dũng",
            ),
            Session(
                "Kỹ năng mềm",
                4,
                "13:00",
                "15:40",
                "7-9",
                "SKL1001-1-1-26(N04)",
                "E-Learning",
                "ThS. Ngô Thanh Tâm",
            ),
            Session(
                "Kiến trúc máy tính",
                4,
                "09:35",
                "12:10",
                "4-6",
                "CSE2105-1-1-26(N01)",
                "A2-508",
                "TS. Vũ Đức Huy",
            ),
            Session(
                "Xác suất thống kê",
                5,
                "13:00",
                "15:40",
                "7-9",
                "MAT1205-1-1-26(N05)",
                "A2-301",
                "ThS. Đặng Thị Lan",
            ),
            Session(
                "Giáo dục thể chất 2",
                6,
                "15:45",
                "18:25",
                "10-12",
                "PES1002-1-1-26(N20)",
                "Sân thể thao",
                "ThS. Bùi Văn Long",
            ),
        ],
    ),
    Sample(
        file_name="sample-03.jpg",
        week_monday=date(2026, 12, 28),
        scale=2,
        menu_bar_text="Th 2 28 thg 12 09:12",
        mini_calendar_month=(2026, 12),
        jpeg_quality=70,
        notes=(
            "JPEG chất lượng 70. Tuần vắt qua năm mới (28/12/2026–03/01/2027): "
            "cột chỉ ghi số ngày, "
            "lịch thu nhỏ ghi 'Tháng 12/2026' nên ngày 01–03 phải suy ra là tháng 1/2027. "
            "Nghỉ Tết dương lịch 01/01."
        ),
        sessions=[
            Session(
                "Giải tích 1",
                1,
                "06:45",
                "09:25",
                "1-3",
                "MAT1101-1-1-26(N01)",
                "A2-301",
                "ThS. Nguyễn Văn An",
            ),
            Session(
                "Lập trình hướng đối tượng",
                1,
                "13:00",
                "15:40",
                "7-9",
                "CSE2203-1-1-26(N03)",
                "A5-402",
                "TS. Trần Thị Bình",
            ),
            Session(
                "Cơ sở dữ liệu",
                3,
                "06:45",
                "12:10",
                "1-6",
                "CSE2301-1-1-26(N02)",
                "A5-310",
                "ThS. Phạm Quốc Dũng",
            ),
            Session(
                "Tiếng Anh 2",
                3,
                "15:45",
                "18:25",
                "10-12",
                "ENG1002-1-1-26(N08)",
                "C2-104",
                "ThS. Hoàng Thu Hà",
            ),
            Session(
                "Xác suất thống kê",
                6,
                "13:00",
                "15:40",
                "7-9",
                "MAT1205-1-1-26(N05)",
                "A2-301",
                "ThS. Đặng Thị Lan",
            ),
            Session(
                "Đồ án cơ sở",
                7,
                "09:35",
                "12:10",
                "4-6",
                "CSE2999-1-1-26(N01)",
                "Phòng Lab 3",
                "TS. Vũ Đức Huy",
            ),
        ],
    ),
]


# ---------------------------------------------------------------------------------------------------
# Ảnh bảng "Lịch thi cá nhân" GIẢ LẬP (feature 001 T109, US11). Họ tên và mã SV là giá trị BỊA, dùng để
# kiểm tra các giá trị này không bao giờ lọt vào kết quả nhận diện (FR-061, SC-020).
# ---------------------------------------------------------------------------------------------------
FAKE_STUDENT = "Nguyễn Văn Test - 21010999 -"
EXAM_HEADERS = [
    ("STT", 0.04),
    ("Mã học phần", 0.11),
    ("Tên học phần", 0.22),
    ("Lần thi", 0.06),
    ("Ngày thi", 0.10),
    ("Thời gian thi", 0.09),
    ("Hình thức", 0.14),
    ("Phòng thi", 0.09),
    ("Số báo danh", 0.07),
    ("Thông tin sinh viên ( Họ tên, mã số)", 0.20),
]
# (mã, tên, lần, ngày, giờ ghi trên ảnh, hình thức, phòng, SBD, ghi chú)
EXAM_ROWS = [
    ("MAT1101", "Giải tích 1", 1, date(2026, 10, 12), "07:30 - 09:00", "Tự luận 90 phút", "A2-301", "101", "đã qua"),
    ("PHI1001", "Triết học Mác - Lênin", 1, date(2026, 10, 20), "13:00 - 14:30", "Trắc nghiệm trên máy 90p", "A5-310", "102", "đã qua"),
    ("CSE2301", "Cơ sở dữ liệu", 1, date(2026, 12, 15), "07:30", "Trắc nghiệm trên máy 60p", "A5-310", "103", "chỉ giờ bắt đầu"),
    ("CSE2302", "Lập trình hướng đối tượng", 2, date(2026, 12, 18), "09:35 - 11:05", "Thực hành trên máy", "A8-101", "104", "lần thi 2"),
    ("INT1306", "Cấu trúc dữ liệu và giải thuật nâng cao", 1, date(2026, 12, 22), "13:00 - 15:00", "Tự luận 120 phút", "", "105", "phòng trống"),
    ("ENG1001", "Tiếng Anh chuyên ngành", 1, date(2026, 12, 29), "15:45 - 17:15", "Vấn đáp", "B1-204", "106", ""),
]


def render_exam_table(scale: int) -> Image.Image:
    W, H = 1440 * scale, 900 * scale
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 24 * scale], fill=MENU_BAR)
    d.text((16 * scale, 5 * scale), "Safari   Tệp   Sửa   Xem", font=load_font("regular", 13 * scale), fill=TEXT_DARK)
    d.text((W - 150 * scale, 5 * scale), "Th 4 4 thg 11 14:05", font=load_font("regular", 13 * scale), fill=TEXT_DARK)
    left, right = 40 * scale, W - 40 * scale
    d.text((left, 70 * scale), "Lịch thi cá nhân", font=load_font("bold", 22 * scale), fill=TEXT_DARK)
    font, bold = load_font("regular", 14 * scale), load_font("bold", 14 * scale)

    xs, x = [], left
    for _, share in EXAM_HEADERS:
        xs.append(x)
        x += int((right - left) * share)
    xs.append(right)
    top = 120 * scale
    d.rectangle([left, top, right, top + 54 * scale], fill=(238, 244, 252))
    for i, (title, _) in enumerate(EXAM_HEADERS):
        for j, line in enumerate(wrap(d, title, bold, xs[i + 1] - xs[i] - 12 * scale)):
            d.text((xs[i] + 6 * scale, top + (8 + 18 * j) * scale), line, font=bold, fill=(90, 100, 115))
    y = top + 54 * scale
    row_h = 64 * scale
    for n, (code, name, attempt, day, hours, fmt, room, sbd, _note) in enumerate(EXAM_ROWS, start=1):
        if n % 2 == 0:
            d.rectangle([left, y, right, y + row_h], fill=(247, 247, 247))
        cells = [str(n), code, name, str(attempt), day.strftime("%d/%m/%Y"), hours, fmt, room, sbd, FAKE_STUDENT]
        for i, text in enumerate(cells):
            lines = wrap(d, text, font, xs[i + 1] - xs[i] - 12 * scale) or [""]
            start = y + (row_h - 18 * scale * len(lines)) // 2
            for j, line in enumerate(lines):
                d.text((xs[i] + 6 * scale, start + 18 * scale * j), line, font=font, fill=TEXT_DARK)
        d.line([left, y + row_h, right, y + row_h], fill=GRID_LINE, width=scale)
        y += row_h
    d.text((W - 150 * scale, H - 22 * scale), "ẢNH GIẢ LẬP", font=load_font("regular", 11 * scale), fill=TEXT_MUTED)
    return img


def exam_expected(file_name: str, scale: int) -> dict:
    from datetime import datetime

    rows = []
    for code, name, attempt, day, hours, fmt, room, sbd, note in EXAM_ROWS:
        start = hours.split(" - ")[0]
        end = hours.split(" - ")[1] if " - " in hours else None
        if end is None:  # chỉ ghi giờ bắt đầu: kết thúc = bắt đầu + thời lượng trong hình thức thi
            minutes = int(fmt.split()[-1].rstrip("p"))
            begin = datetime.strptime(start, "%H:%M")
            end = (begin + timedelta(minutes=minutes)).strftime("%H:%M")
        rows.append(
            {
                "course_code": code,
                "course_name": name,
                "attempt": attempt,
                "date": day.isoformat(),
                "start_time": start,
                "end_time": end,
                "end_time_source": "image" if " - " in hours else "format_duration",
                "exam_format": fmt,
                "room": room or None,
                "candidate_number": sbd,
                "note": note,
            }
        )
    return {
        "synthetic": True,
        "warning": "Ảnh giả lập, không phải ảnh chụp thật. Kết quả phải kiểm chứng lại bằng ảnh thật.",
        "image": file_name,
        "kind": "exam_table",
        "screen": f"{1440 * scale}x{900 * scale}",
        "rows": rows,
        "student_values_must_not_appear": ["Nguyễn Văn Test", "21010999"],
    }


def main() -> None:
    for sample in SAMPLES:
        img = render(sample)
        path = OUT_DIR / sample.file_name
        if sample.jpeg_quality:
            img.save(path, "JPEG", quality=sample.jpeg_quality)
        else:
            img.save(path, "PNG")
        exp_path = path.with_name(path.stem + ".expected.json")
        exp_path.write_text(
            json.dumps(expected(sample), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(
            f"{path.name}: {img.size[0]}x{img.size[1]}, "
            f"{len(sample.sessions)} buổi → {exp_path.name}"
        )
    for number, scale in ((1, 2), (2, 1)):  # exam-01: Retina 2880×1800; exam-02: 1440×900
        name = f"exam-0{number}.png"
        render_exam_table(scale).save(OUT_DIR / name, "PNG")
        (OUT_DIR / f"exam-0{number}.expected.json").write_text(
            json.dumps(exam_expected(name, scale), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"{name}: {1440 * scale}x{900 * scale}, {len(EXAM_ROWS)} buổi thi")


if __name__ == "__main__":
    main()
