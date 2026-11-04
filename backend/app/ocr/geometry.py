"""Hàm thuần dùng chung cho phân tích bố cục: chuẩn hoá chữ, ghép khối cùng dòng, tách cột."""

import re
import unicodedata
from statistics import median

from app.ocr.reader import TextBox


def strip_accents(text: str) -> str:
    """Chữ thường, bỏ dấu tiếng Việt (đ → d) để so khớp chịu lỗi mất dấu của OCR."""
    decomposed = unicodedata.normalize("NFD", text.replace("đ", "d").replace("Đ", "D"))
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn").lower().strip()


def median_height(boxes: list[TextBox]) -> float:
    return median(b.h for b in boxes) if boxes else 0.0


def merge_line(parts: list[TextBox]) -> TextBox:
    parts = sorted(parts, key=lambda b: b.x0)
    return TextBox(
        " ".join(p.text for p in parts),
        min(p.x0 for p in parts),
        min(p.y0 for p in parts),
        max(p.x1 for p in parts),
        max(p.y1 for p in parts),
        sum(p.conf for p in parts) / len(parts),
    )


def to_lines(boxes: list[TextBox], gap_factor: float = 2.5) -> list[TextBox]:
    """Ghép các khối cùng một dòng (cùng đường giữa theo chiều dọc, nằm sát nhau) thành một dòng.

    EasyOCR hay cắt một dòng thành nhiều khối ("13-00" + "15.40 (Tiết 7-9)"); ghép lại để regex
    của `fields` thấy nguyên dòng. Kết quả sắp từ trên xuống.
    """
    lines: list[list[TextBox]] = []
    for box in sorted(boxes, key=lambda b: (b.cy, b.x0)):
        for line in lines:
            last = max(line, key=lambda b: b.x1)
            first = min(line, key=lambda b: b.x0)
            height = min(box.h, last.h) or 1.0
            same_row = abs(box.cy - median(p.cy for p in line)) <= 0.55 * height
            gap = max(box.x0 - last.x1, first.x0 - box.x1)
            if same_row and gap <= gap_factor * height:
                line.append(box)
                break
        else:
            lines.append([box])
    return sorted((merge_line(line) for line in lines), key=lambda b: (b.y0, b.x0))


def cluster_by_y(boxes: list[TextBox], tolerance: float) -> list[list[TextBox]]:
    """Gom các khối có tâm dọc cách nhau ≤ `tolerance` (liên kết đơn)."""
    groups: list[list[TextBox]] = []
    for box in sorted(boxes, key=lambda b: b.cy):
        if groups and box.cy - groups[-1][-1].cy <= tolerance:
            groups[-1].append(box)
        else:
            groups.append([box])
    return groups


_DATE_RE = re.compile(r"(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})")
_TIME_RE = re.compile(r"(?<!\d)(\d{1,2})\s*[:.hg,;*\-]\s*(\d{2})(?!\d)")


def find_dates(text: str) -> list[tuple[int, int, int]]:
    """Mọi ngày dd/mm/yyyy trong chuỗi → [(ngày, tháng, năm)]; bỏ ngày không hợp lệ."""
    found = []
    for d, m, y in _DATE_RE.findall(text):
        d, m, y = int(d), int(m), int(y)
        if 1 <= d <= 31 and 1 <= m <= 12 and 1990 <= y <= 2100:
            found.append((d, m, y))
    return found


def find_times(text: str) -> list[tuple[int, int]]:
    """Mọi giờ trong chuỗi, chịu lỗi OCR ở dấu phân cách: 06.45, 13-00, 7h30, 07:30."""
    found = []
    for h, m in _TIME_RE.findall(text):
        h, m = int(h), int(m)
        if 0 <= h <= 23 and 0 <= m <= 59:
            found.append((h, m))
    return found
