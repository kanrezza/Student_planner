"""Ghép dòng bị ngắt trong ô và đọc nội dung ô của bảng thời khoá biểu (R4, R5)."""

import re
from dataclasses import dataclass
from datetime import date

from app.ocr.fields import split_class_label

_DATE_RE = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")
_DAY_CELL_RE = re.compile(r"^\s*(\d{1,2})\s*-\s*(\d{1,2})\s*(?:\((.*)\))?\s*$", re.DOTALL)
_SEMESTER_RE = re.compile(r"[Hh]ọc\s*kỳ\s*(\d+)\s*Năm\s*học\s*(\d{4})\s*-\s*(\d{4})")


def join_cell_lines(lines: list[str], kind: str) -> str:
    """Nối các dòng của một ô theo luật của loại cột.

    - `course_code`: nối liền, không dấu cách ("FFS7010" + "69" → "FFS701069").
    - `class_label`, `dates`: nối bằng dấu cách.
    - `day_cell`: không dấu cách khi dòng trước kết thúc bằng chữ số, "." hoặc "-", hoặc dòng
      sau bắt đầu bằng chữ số hay "."; ngược lại một dấu cách.
    """
    lines = [line.strip() for line in lines if line.strip()]
    if kind == "course_code":
        return "".join("".join(line.split()) for line in lines)
    if kind in ("class_label", "dates"):
        return " ".join(lines)
    if kind == "day_cell":
        out = ""
        for line in lines:
            if out and not (
                out[-1].isdigit() or out[-1] in ".-" or line[0].isdigit() or line[0] == "."
            ):
                out += " "
            out += line
        return out
    raise ValueError(f"Loại ô không biết: {kind}")


@dataclass(frozen=True)
class DayCell:
    period_from: int
    period_to: int
    room: str | None


def normalize_room(room: str) -> str | None:
    """ "A6-203(PC)" → "A6-203 (PC)"; rỗng → None."""
    room = re.sub(r"\s*\(\s*PC\s*\)", " (PC)", room.strip())
    room = re.sub(r"\s+", " ", room).strip()
    return room or None


def parse_day_cell(text: str) -> DayCell | None:
    """ "4 - 6 (A6-203 (PC))" → DayCell(4, 6, "A6-203 (PC)"); không đọc được tiết → None."""
    match = _DAY_CELL_RE.match(text)
    if not match:
        return None
    first, last = int(match.group(1)), int(match.group(2))
    if not 1 <= first <= last <= 30:
        return None
    return DayCell(first, last, normalize_room(match.group(3) or ""))


def parse_dates(text: str) -> list[date]:
    """Mọi ngày dd/mm/yyyy hợp lệ theo thứ tự xuất hiện."""
    found = []
    for d, m, y in _DATE_RE.findall(text):
        try:
            found.append(date(int(y), int(m), int(d)))
        except ValueError:
            continue
    return found


def parse_semester_name(line: str | None) -> str | None:
    """ "Học kỳ 2 Năm học 2026 - 2027 Đợt 2" → "HK2 2026–2027"."""
    match = _SEMESTER_RE.search(line or "")
    if not match:
        return None
    return f"HK{match.group(1)} {match.group(2)}–{match.group(3)}"


def parse_class_label(text: str) -> tuple[str, str | None]:
    return split_class_label(text)


def parse_credits(text: str) -> int | None:
    digits = re.sub(r"\D", "", text)
    return int(digits) if digits else None
