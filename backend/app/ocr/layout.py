"""Nhận dạng bố cục ảnh và gom khối chữ thành ô buổi học (research R3 bước 2–4, R14).

Mọi hàm là hàm thuần trên danh sách `TextBox` (toạ độ px của ảnh gốc).
"""

import re
from dataclasses import dataclass, field
from datetime import date
from statistics import median

from app.ocr.geometry import cluster_by_y, find_dates, strip_accents, to_lines
from app.ocr.reader import TextBox

MENU_BAR_FRACTION = 0.028  # thanh menu macOS ≈ 2,7% chiều cao ảnh chụp toàn màn hình
DOCK_FRACTION = 0.93

_WEEKDAY_RE = re.compile(r"^thu\w?\s*([2-7])?$")
_SUNDAY_RE = re.compile(r"^(?:cn|chu\s*nhat|chu\s*nhut)$")
_HOUR_LABEL_RE = re.compile(r"^\d{1,2}\s*[:;.]\s*\w{1,2}$")
_DAY_RE = re.compile(r"^\d{1,2}$")
_DAY_MONTH_RE = re.compile(r"^(\d{1,2})\s*/\s*(\d{1,2})$")


def split_menu_bar(
    boxes: list[TextBox], size: tuple[int, int]
) -> tuple[list[TextBox], list[TextBox]]:
    """Tách (thanh menu macOS, phần còn lại). Thanh menu chỉ dùng để đọc ngày giờ hệ thống."""
    limit = MENU_BAR_FRACTION * size[1]
    menu = [b for b in boxes if b.y1 <= limit]
    return menu, [b for b in boxes if b.y1 > limit]


def filter_chrome(boxes: list[TextBox], size: tuple[int, int]) -> list[TextBox]:
    """Bỏ thanh menu macOS ở trên cùng và nhãn Dock ở dưới cùng."""
    _, rest = split_menu_bar(boxes, size)
    return [b for b in rest if b.y0 < DOCK_FRACTION * size[1]]


# ---- Lưới tuần ----------------------------------------------------------------------------------


@dataclass(frozen=True)
class WeekdayHeader:
    weekday: int  # 1 = Thứ Hai … 7 = Chủ Nhật
    box: TextBox
    day: int | None = None  # số ngày in phía trên/dưới tiêu đề (ví dụ "28")
    day_box: TextBox | None = None
    full_date: date | None = None  # dd/mm/yyyy nếu cột ghi đủ ngày


@dataclass(frozen=True)
class Column:
    weekday: int
    lo: float
    hi: float


@dataclass
class Cell:
    weekday: int
    lines: list[TextBox] = field(default_factory=list)

    @property
    def y0(self) -> float:
        return min(line.y0 for line in self.lines)


def _weekday_of(text: str) -> int | None | bool:
    """Số thứ (1–7) nếu là tiêu đề thứ; True nếu là "Thứ" thiếu số; None nếu không phải tiêu đề."""
    clean = strip_accents(text)
    if _SUNDAY_RE.match(clean):
        return 7
    if match := _WEEKDAY_RE.match(clean):
        return int(match.group(1)) - 1 if match.group(1) else True
    return None


def _assign_weekdays(
    candidates: list[tuple[TextBox, int | bool]],
) -> list[tuple[TextBox, int]] | None:
    """Điền số thứ còn thiếu theo vị trí (OCR hay làm rơi chữ số: "Thứ 7" → "Thứ")."""
    ordered = sorted(candidates, key=lambda c: c[0].x0)
    anchor = next((i for i, (_, w) in enumerate(ordered) if w is not True), None)
    if anchor is None:
        return None
    base = ordered[anchor][1] - anchor
    result = [(box, base + i) for i, (box, _) in enumerate(ordered)]
    explicit = all(w is True or w == num for (_, w), (_, num) in zip(ordered, result, strict=True))
    in_range = all(1 <= num <= 7 for _, num in result)
    return result if explicit and in_range else None


def find_week_headers(boxes: list[TextBox]) -> list[WeekdayHeader]:
    """Hàng tiêu đề "Thứ 2 … Chủ nhật" (≥ 5 tiêu đề cùng hàng); rỗng nếu không phải lưới tuần."""
    candidates = [(b, w) for b in boxes if (w := _weekday_of(b.text)) is not None]
    if len(candidates) < 5:
        return []
    height = median(b.h for b, _ in candidates)
    best: list[tuple[TextBox, int | bool]] = []
    for group in cluster_by_y([b for b, _ in candidates], 0.6 * height):
        if len(group) > len(best):
            best = [(b, dict((id(x), w) for x, w in candidates)[id(b)]) for b in group]
    if len(best) < 5:
        return []
    assigned = _assign_weekdays(best)
    if assigned is None:
        return []
    pitch = median(b.cx - a.cx for (a, _), (b, _) in zip(assigned, assigned[1:], strict=False))
    return [_with_dates(box, weekday, boxes, pitch) for box, weekday in assigned]


def _with_dates(header: TextBox, weekday: int, boxes: list[TextBox], pitch: float) -> WeekdayHeader:
    """Số ngày (hoặc dd/mm/yyyy) nằm ngay trên/dưới tiêu đề cột."""
    day, full, day_box = None, None, None
    nearby = [
        b
        for b in boxes
        if b is not header
        and abs(b.cy - header.cy) <= 3.2 * header.h
        and abs(b.cx - header.cx) <= 0.5 * pitch
    ]
    for box in sorted(nearby, key=lambda b: abs(b.cy - header.cy)):
        text = box.text.strip()
        if dates := find_dates(text):
            d, m, y = dates[0]
            full = date(y, m, d)
            break
        if (
            day is None
            and _DAY_RE.match(text)
            and 1 <= int(text) <= 31
            and box.cy <= header.cy + 0.5 * header.h
        ):
            day, day_box = int(text), box
    return WeekdayHeader(weekday, header, day=day, day_box=day_box, full_date=full)


def _left_aligned(headers: list[WeekdayHeader]) -> bool:
    """Tiêu đề căn trái (số ngày và chữ "Thứ n" cùng mép trái) hay căn giữa cột."""
    # Chỉ xét số ngày nằm phía trên tiêu đề; số ngày đứng cạnh chữ "Thứ n" không cho biết căn lề.
    pairs = [
        (h.box, h.day_box)
        for h in headers
        if h.day_box is not None and h.day_box.cy < h.box.cy - 0.5 * h.box.h
    ]
    if not pairs:
        return False
    left = median(abs(b.x0 - d.x0) for b, d in pairs)
    center = median(abs(b.cx - d.cx) for b, d in pairs)
    return left < center


def columns_for_weekdays(headers: list[WeekdayHeader]) -> list[Column]:
    """Khoảng x của từng cột.

    Tiêu đề căn trái (cổng thông tin thật): cột bắt đầu ở mép trái tiêu đề, nên chữ của ô xuống dòng
    vẫn nằm đúng cột. Tiêu đề căn giữa: ranh giới là trung điểm giữa hai tâm tiêu đề kề nhau.
    """
    xs = [h.box.x0 for h in headers]
    centers = [h.box.cx for h in headers]
    ref = xs if _left_aligned(headers) else centers
    pitch = median(b - a for a, b in zip(ref, ref[1:], strict=False)) if len(ref) > 1 else 300
    left = _left_aligned(headers)
    tol = 0.05 * pitch
    columns = []
    for i, header in enumerate(headers):
        if left:
            lo = xs[i] - tol
            hi = xs[i + 1] - tol if i + 1 < len(xs) else xs[i] + pitch - tol
        else:
            lo = centers[0] - pitch / 2 if i == 0 else (centers[i - 1] + centers[i]) / 2
            hi = (
                centers[i] + 0.75 * pitch
                if i + 1 == len(centers)
                else (centers[i] + centers[i + 1]) / 2
            )
        columns.append(Column(header.weekday, lo, hi))
    return columns


def _is_hour_label(box: TextBox, first_header: TextBox) -> bool:
    """Nhãn giờ ở lề trái lưới ("8:00", "10:00") — nằm hẳn bên trái cột đầu."""
    return bool(_HOUR_LABEL_RE.match(box.text.strip())) and box.x1 < first_header.x0 - 3


def group_cells(boxes: list[TextBox], headers: list[WeekdayHeader]) -> list[Cell]:
    """Mỗi cột một thứ: gom các dòng gần nhau theo chiều dọc thành ô (gần = < 1,2 chiều cao dòng);
    một dòng giờ thứ hai trong cùng nhóm luôn mở ô mới."""
    from app.ocr.fields import is_time_line

    if not headers:
        return []
    below = max(h.box.y1 for h in headers)
    first = min(headers, key=lambda h: h.box.x0).box
    cells: list[Cell] = []
    for column in columns_for_weekdays(headers):
        members = [
            b
            for b in boxes
            if b.y0 >= below - 2 and column.lo <= b.x0 < column.hi and not _is_hour_label(b, first)
        ]
        lines = to_lines(members)
        if not lines:
            continue
        gap_limit = 1.2 * median(line.h for line in lines)
        current: Cell | None = None
        for line in lines:
            new_time = (
                current is not None
                and is_time_line(line.text)
                and any(is_time_line(existing.text) for existing in current.lines)
            )
            far = current is not None and line.y0 - max(x.y1 for x in current.lines) > gap_limit
            if current is None or far or new_time:
                current = Cell(column.weekday)
                cells.append(current)
            current.lines.append(line)
    return cells


# ---- Nhận dạng bố cục ---------------------------------------------------------------------------


def detect_layout(boxes: list[TextBox]) -> str:
    """ "week_grid" | "exam_table" | "list" | "unknown" (research R14).

    Đạt cả lưới tuần lẫn bảng lịch thi, hoặc không đạt cái nào → "unknown" (giao diện sẽ hỏi).
    """
    from app.ocr.table import EXAM_FIELDS, LIST_FIELDS, find_table_header

    is_grid = len(find_week_headers(boxes)) >= 5
    exam = find_table_header(boxes, EXAM_FIELDS, min_fields=3)
    has_dates = any(find_dates(b.text) for b in boxes)
    is_exam = exam is not None and has_dates
    if is_grid and is_exam:
        return "unknown"
    if is_grid:
        return "week_grid"
    if is_exam:
        return "exam_table"
    if find_table_header(boxes, LIST_FIELDS, min_fields=3) is not None:
        return "list"
    return "unknown"
