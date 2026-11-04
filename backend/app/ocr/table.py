"""Phân tích bảng có hàng tiêu đề (bảng lịch thi, danh sách buổi học): cột, hàng, ô nhiều dòng.

Tiêu đề có thể xuống dòng ("Mã học" / "phần"); ánh xạ tiêu đề → trường dùng so khớp mờ để chịu lỗi
mất dấu của OCR (research R14).
"""

import re
from dataclasses import dataclass
from statistics import median

from rapidfuzz import fuzz

from app.ocr.geometry import find_dates, strip_accents, to_lines
from app.ocr.reader import TextBox

FUZZY_MIN = 85

# Tiêu đề đồng nghĩa (đã bỏ dấu, chữ thường) → trường.
EXAM_FIELDS: dict[str, tuple[str, ...]] = {
    "course_code": ("ma hoc phan", "ma hp", "ma mon hoc", "ma mon"),
    "course_name": ("ten hoc phan", "ten mon thi", "ten mon hoc", "mon thi", "ten hp"),
    "attempt": ("lan thi",),
    "date": ("ngay thi",),
    "time": ("thoi gian thi", "gio thi", "ca thi", "thoi gian"),
    "exam_format": ("hinh thuc thi", "hinh thuc"),
    "room": ("phong thi",),
    "candidate_number": ("so bao danh", "sbd"),
    "stt": ("stt",),
}
LIST_FIELDS: dict[str, tuple[str, ...]] = {
    "name": ("mon hoc", "ten mon", "ten lop", "ten hoc phan"),
    "weekday": ("thu",),
    "date": ("ngay hoc", "ngay"),
    "time": ("tiet", "gio hoc", "thoi gian", "gio"),
    "room": ("phong", "dia diem", "phong hoc"),
    "lecturer": ("giang vien", "gv"),
    "class_code": ("ma lop", "ma hoc phan", "ma mon"),
}
# Cột thông tin sinh viên: loại bỏ ngay sau khi xác định cột (FR-061).
STUDENT_KEYWORDS = (
    "ho ten",
    "ho va ten",
    "ma sv",
    "ma sinh vien",
    "sinh vien",
    "ngay sinh",
    "mssv",
    "ma so",
    "lop",
)


@dataclass(frozen=True)
class TableColumn:
    title: str
    field: str | None  # None = cột không dùng; "student" = cột thông tin sinh viên
    x0: float
    x1: float


@dataclass(frozen=True)
class TableHeader:
    columns: list[TableColumn]
    y0: float
    y1: float


def _is_student(title: str) -> bool:
    words = title.split()
    padded = f" {' '.join(words)} "
    if any(f" {k} " in padded for k in STUDENT_KEYWORDS):
        return True
    return any(fuzz.ratio(title, k) >= FUZZY_MIN for k in STUDENT_KEYWORDS if len(k) > 3)


def map_title(title: str, synonyms: dict[str, tuple[str, ...]]) -> str | None:
    """Trường ứng với tiêu đề cột (đã bỏ dấu); "student" cho cột sinh viên; None nếu lạ."""
    if _is_student(title):
        return "student"
    best, best_score = None, 0.0
    for field_name, names in synonyms.items():
        for name in names:
            score = 100.0 if title == name else fuzz.ratio(title, name)
            if title.startswith(name + " ") or title.endswith(" " + name):
                score = max(score, 90.0)
            if score > best_score:
                best, best_score = field_name, score
    return best if best_score >= FUZZY_MIN else None


def _keyword_box(box: TextBox, synonyms: dict[str, tuple[str, ...]]) -> bool:
    text = strip_accents(box.text)
    if len(text) < 3:
        return False
    names = [n for ns in synonyms.values() for n in ns] + list(STUDENT_KEYWORDS)
    return any(
        text in n or n in text or fuzz.ratio(text, n) >= FUZZY_MIN for n in names if len(n) > 2
    )


def _union_columns(header_boxes: list[TextBox], height: float) -> list[list[TextBox]]:
    """Gom các khối tiêu đề chồng/sát nhau theo trục x thành từng cột (liên kết đơn)."""
    groups: list[list[TextBox]] = []
    for box in sorted(header_boxes, key=lambda b: b.x0):
        hit = [
            g
            for g in groups
            if any(box.x0 <= m.x1 + 0.4 * height and box.x1 >= m.x0 - 0.4 * height for m in g)
        ]
        merged = [box] + [m for g in hit for m in g]
        groups = [g for g in groups if g not in hit] + [merged]
    return sorted(groups, key=lambda g: min(m.x0 for m in g))


def find_table_header(
    boxes: list[TextBox], synonyms: dict[str, tuple[str, ...]], min_fields: int = 3
) -> TableHeader | None:
    """Hàng tiêu đề: cụm khối chữ gần nhau theo chiều dọc có ≥ `min_fields` trường khác nhau."""
    candidates = [b for b in boxes if _keyword_box(b, synonyms)]
    if len(candidates) < min_fields:
        return None
    height = median(b.h for b in candidates)
    best: TableHeader | None = None
    best_count = 0
    for seed in candidates:
        band = [c for c in candidates if abs(c.cy - seed.cy) <= 1.6 * height]
        y0, y1 = min(b.y0 for b in band) - 0.3 * height, max(b.y1 for b in band) + 0.3 * height
        header_boxes = [b for b in boxes if y0 <= b.cy <= y1]
        columns = []
        for group in _union_columns(header_boxes, height):
            title = strip_accents(" ".join(line.text for line in to_lines(group)))
            columns.append(
                TableColumn(
                    title,
                    map_title(title, synonyms),
                    min(m.x0 for m in group),
                    max(m.x1 for m in group),
                )
            )
        fields = {c.field for c in columns if c.field not in (None, "student", "stt")}
        if len(fields) >= min_fields and len(fields) > best_count:
            best, best_count = TableHeader(columns, y0, y1), len(fields)
    return best


def column_of(box: TextBox, columns: list[TableColumn]) -> int:
    """Cột của khối chữ: cột có khoảng x chứa mép trái khối; nếu không, cột gần tâm nhất."""
    inside = [i for i, c in enumerate(columns) if c.x0 - 3 <= box.x0 <= c.x1]
    pool = inside or list(range(len(columns)))

    def distance(i: int) -> float:
        c = columns[i]
        return 0.0 if c.x0 <= box.cx <= c.x1 else min(abs(box.cx - c.x0), abs(box.cx - c.x1))

    return min(pool, key=lambda i: (distance(i), abs(box.cx - (columns[i].x0 + columns[i].x1) / 2)))


_ANCHORS = {
    "date": lambda text: bool(find_dates(text)),
    "course_code": lambda text: bool(re.match(r"^[A-Z]{2,5}\d{3,}", text.strip())),
    "stt": lambda text: bool(re.match(r"^\d{1,3}$", text.strip())),
}


def table_rows(
    boxes: list[TextBox],
    header: TableHeader,
    anchor_fields: tuple[str, ...] = ("date", "course_code", "stt"),
) -> list[dict[str, tuple[str, float]]]:
    """Các hàng của bảng: {trường: (nội dung, độ tin cậy)}. Cột sinh viên bị bỏ trước khi tạo ô.

    Hàng được xác định bằng cột "mốc" có đúng một giá trị mỗi hàng (ngày, mã học phần hoặc STT);
    mỗi hàng trải từ trung điểm với mốc trước tới trung điểm với mốc sau, nên ô nhiều dòng
    (tên học phần xuống dòng) được ghép đúng.
    """
    columns = header.columns
    body = [b for b in boxes if b.y0 >= header.y1 - 1]
    assigned = [(b, column_of(b, columns)) for b in body]
    # FR-061: bỏ khối thuộc cột sinh viên ngay tại đây.
    kept = [(b, i) for b, i in assigned if columns[i].field != "student"]

    anchors: list[TextBox] = []
    for name in anchor_fields:
        matched = [b for b, i in kept if columns[i].field == name and _ANCHORS[name](b.text)]
        if len(matched) > len(anchors):
            anchors = matched
    anchors = sorted(anchors, key=lambda b: b.cy)
    if not anchors:
        return []
    bounds = [(anchors[i - 1].cy + a.cy) / 2 if i else header.y1 for i, a in enumerate(anchors)]
    bounds.append(float("inf"))

    rows = []
    for r in range(len(anchors)):
        cells: dict[str, list[TextBox]] = {}
        for box, i in kept:
            field_name = columns[i].field
            if field_name and bounds[r] <= box.cy < bounds[r + 1]:
                cells.setdefault(field_name, []).append(box)
        row = {}
        for field_name, parts in cells.items():
            lines = to_lines(parts)
            text = " ".join(line.text for line in lines)
            row[field_name] = (text, sum(p.conf for p in parts) / len(parts))
        rows.append(row)
    return rows
