"""Bảng "Lịch thi cá nhân" → các dòng buổi thi (research R14, FR-059 đến FR-062).

Cột thông tin sinh viên (họ tên, mã SV…) bị loại ở `table.table_rows`, trước khi tạo bất kỳ trường
nào; nội dung của chúng không được ghi log và không có trong kết quả.
"""

import re
from dataclasses import dataclass
from datetime import date, time

from app.lib.text import nfc
from app.ocr.fields import fix_code_token, parse_time_line
from app.ocr.geometry import find_dates
from app.ocr.reader import TextBox
from app.ocr.table import EXAM_FIELDS, find_table_header, table_rows

_DURATION_RE = re.compile(r"(\d{1,3})\s*(?:p\b|phút|phut)", re.IGNORECASE)


def format_duration(exam_format: str | None) -> int | None:
    """ "Trắc nghiệm trên máy 60p" → 60. OCR hay đọc "60p" thành "6Op" nên sửa O↔0 trước."""
    if not exam_format:
        return None
    fixed = re.sub(r"(?<=\d)[Oo](?=\s*(?:p\b|\d))", "0", exam_format)
    match = _DURATION_RE.search(fixed)
    return int(match.group(1)) if match else None


@dataclass
class ExamRowData:
    """Một dòng thô của bảng lịch thi; mỗi trường là (giá trị | None, độ tin cậy)."""

    course_code: tuple[str | None, float]
    course_name: tuple[str | None, float]
    attempt: tuple[int, float, bool]  # (giá trị, độ tin cậy, chắc chắn)
    date: tuple[date | None, float]
    start_time: tuple[time | None, float]
    end_time: tuple[time | None, float]
    end_time_source: str | None  # "image" | "format_duration" | None
    exam_format: tuple[str | None, float]
    room: tuple[str | None, float]
    candidate_number: tuple[str | None, float]


def _text(row: dict, key: str) -> tuple[str | None, float]:
    value, conf = row.get(key, (None, 1.0))
    value = nfc(value) if value else None
    return value or None, conf


def parse_exam_table(boxes: list[TextBox]) -> list[ExamRowData]:
    header = find_table_header(boxes, EXAM_FIELDS, min_fields=3)
    if header is None:
        return []
    result = []
    for row in table_rows(boxes, header):
        code, name = _text(row, "course_code"), _text(row, "course_name")
        code = (fix_code_token(code[0]) if code[0] else None, code[1])
        fmt = _text(row, "exam_format")
        fmt = (re.sub(r"(?<=\d)[Oo](?=p\b)", "0", fmt[0]) if fmt[0] else None, fmt[1])
        day_text, day_conf = _text(row, "date")
        dates = find_dates(day_text or "")
        day = date(dates[0][2], dates[0][1], dates[0][0]) if dates else None
        start, end, _ = parse_time_line(_text(row, "time")[0] or "")
        end_source = "image" if end else None
        if start and not end and (minutes := format_duration(fmt[0])):
            total = start.hour * 60 + start.minute + minutes
            if total < 24 * 60:
                end, end_source = time(total // 60, total % 60), "format_duration"
        time_conf = row.get("time", (None, 1.0))[1]
        attempt_text, attempt_conf = _text(row, "attempt")
        digits = re.search(r"\d+", attempt_text or "")
        attempt = (
            (int(digits.group()), attempt_conf, True)
            if digits
            else (1, attempt_conf, attempt_text is None)
        )
        result.append(
            ExamRowData(
                code,
                name,
                attempt,
                (day, day_conf),
                (start, time_conf),
                (end, time_conf),
                end_source,
                fmt,
                _text(row, "room"),
                _text(row, "candidate_number"),
            )
        )
    return result
