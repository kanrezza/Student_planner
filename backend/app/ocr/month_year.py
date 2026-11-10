"""Xác định tháng/năm của ảnh lịch học (FR-031, research R3 bước 6).

Thứ tự ưu tiên nguồn: ngày trong lưới → tiêu đề tuần → lịch tháng thu nhỏ → thanh menu macOS.
Các nguồn mâu thuẫn → chọn nguồn ưu tiên cao hơn nhưng `certain = False`.
"""

import re
from dataclasses import dataclass
from datetime import date

from app.ocr.geometry import find_dates, strip_accents
from app.ocr.layout import WeekdayHeader
from app.ocr.reader import TextBox

SOURCES = ("grid_dates", "week_header", "mini_calendar", "menu_bar")

_MINI_CAL_RE = re.compile(r"thang\s*(\d{1,2})\s*[-/,. ]\s*(\d{4})")
_MENU_RE = re.compile(r"(?:^|\s)(\d{1,2})\s*thg\s*(\d{1,2})(?:\s+(\d{1,2}:\d{2}))?")


@dataclass(frozen=True)
class MonthYear:
    value: str | None  # "2026-11"
    source: str | None
    certain: bool
    reason: str | None = None

    def as_dict(self) -> dict:
        data = {"value": self.value, "source": self.source, "certain": self.certain}
        if self.reason:
            data["reason"] = self.reason
        return data


def _valid(month: int, year: int) -> bool:
    return 1 <= month <= 12 and 2000 <= year <= 2100


def _from_headers(headers: list[WeekdayHeader]) -> list[tuple[int, int]]:
    return [(h.full_date.year, h.full_date.month) for h in headers if h.full_date]


def _from_week_text(boxes: list[TextBox]) -> list[tuple[int, int]]:
    """Tiêu đề tuần như "Tuần 10 (04/11/2026 - 10/11/2026)": lấy tháng của ngày đầu tiên."""
    found = []
    for box in boxes:
        text = strip_accents(box.text)
        if "tuan" in text and (dates := find_dates(box.text)):
            d, m, y = dates[0]
            found.append((y, m))
    return found


def _from_mini_calendar(boxes: list[TextBox]) -> list[tuple[int, int]]:
    found = []
    for box in boxes:
        if match := _MINI_CAL_RE.search(strip_accents(box.text)):
            month, year = int(match.group(1)), int(match.group(2))
            if _valid(month, year):
                found.append((year, month))
    return found


def _from_menu_bar(menu_boxes: list[TextBox], today: date) -> list[tuple[int, int]]:
    """Thanh menu chỉ có ngày và tháng ("Th 4 4 thg 11 14:05"); năm lấy theo năm hiện tại."""
    found = []
    for box in menu_boxes:
        if match := _MENU_RE.search(strip_accents(box.text)):
            month = int(match.group(2))
            if 1 <= month <= 12:
                found.append((today.year, month))
    return found


def infer_month_year(
    boxes: list[TextBox],
    headers: list[WeekdayHeader],
    menu_boxes: list[TextBox],
    today: date,
) -> MonthYear:
    """`boxes` là phần ảnh sau khi bỏ thanh menu; `menu_boxes` là thanh menu."""
    candidates = {
        "grid_dates": _from_headers(headers),
        "week_header": _from_week_text(boxes),
        # Ảnh cắt sát mép trên: tiêu đề lịch nhỏ ("Tháng 12-2026") có thể rơi vào vùng thanh menu.
        "mini_calendar": _from_mini_calendar(boxes + menu_boxes),
        "menu_bar": _from_menu_bar(menu_boxes, today),
    }
    chosen = next(((s, c[0]) for s in SOURCES if (c := candidates[s])), None)
    if chosen is None:
        return MonthYear(None, None, False, "Không tìm thấy tháng/năm trong ảnh")
    source, (year, month) = chosen
    others = {c[0] for s, c in candidates.items() if c and s != source}
    conflict = any(other != (year, month) for other in others)
    reason = "Các nguồn tháng/năm trong ảnh không khớp nhau" if conflict else None
    if source == "menu_bar":
        reason = "Năm lấy theo năm hiện tại vì thanh menu không ghi năm"
    return MonthYear(
        f"{year:04d}-{month:02d}", source, not (conflict or source == "menu_bar"), reason
    )
