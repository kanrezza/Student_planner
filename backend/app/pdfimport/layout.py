"""Xác định cột thứ và hàng của bảng thời khoá biểu từ toạ độ chữ (R3, R6).

Cột theo chữ tiêu đề (rồi khớp vào đường kẻ dọc gần nhất nếu có); hàng theo đường kẻ ngang, hoặc
theo cặp ngày của cột "Thời gian" khi file không có đường kẻ. Mọi từ ở phần đầu trang (tên trường,
họ tên, mã sinh viên, lớp…) bị bỏ ngay: chỉ dòng "Học kỳ … Năm học …" được giữ lại.
"""

import re
import unicodedata
from dataclasses import dataclass

from app.pdfimport.reader import PageData, PdfImportError, Word

# Khoá cột được giữ (STT và Học phí bị bỏ).
KEEP = ("course", "class", "credits", "d1", "d2", "d3", "d4", "d5", "d6", "d7", "dates")
DAY_KEYS = ("d1", "d2", "d3", "d4", "d5", "d6", "d7")
LINE_TOLERANCE = 3.0
HEADER_ABOVE, HEADER_BELOW = 16.0, 14.0
_DATE_RE = re.compile(r"\d{1,2}/\d{1,2}/\d{4}")
_SEMESTER_RE = re.compile(r"hoc\s*ky\s*(\d+)\s*nam\s*hoc\s*(\d{4})\s*-\s*(\d{4})")

NOT_TIMETABLE = PdfImportError(
    422,
    "pdf_not_timetable",
    "Không tìm thấy bảng thời khoá biểu (cần các cột Mã HP, Lớp học phần, Thứ 2…CN, Thời gian).",
)


def fold(text: str) -> str:
    """Bỏ dấu, chữ thường: "Thời" → "thoi"."""
    text = unicodedata.normalize("NFD", text.replace("đ", "d").replace("Đ", "D"))
    return "".join(c for c in text if unicodedata.category(c) != "Mn").lower()


@dataclass
class Column:
    key: str
    left: float
    right: float = float("inf")


@dataclass
class Header:
    top: float  # mép trên của chữ tiêu đề
    bottom: float  # hàng dữ liệu bắt đầu dưới mức này
    columns: list[Column]


@dataclass
class RawRow:
    """Một hàng bảng: các dòng chữ của từng ô, đã sắp theo dòng rồi theo x."""

    cells: dict[str, list[str]]


@dataclass
class ParsedTable:
    semester_line: str | None
    rows: list[RawRow]


def _same_line(a: Word, b: Word) -> bool:
    return abs(a.yc - b.yc) <= LINE_TOLERANCE + 2


def _day_label_words(words: list[Word]) -> dict[int, Word]:
    """Từ "Thứ" (kèm số 2..7 ngay sau) và "CN" của dòng tiêu đề → {thứ: từ cuối nhãn}."""
    found: dict[int, tuple[Word, Word]] = {}
    ordered = sorted(words, key=lambda w: (round(w.yc), w.x0))
    for i, word in enumerate(ordered):
        f = fold(word.text)
        match = re.fullmatch(r"thu\s*([2-7])", f)
        if match:
            found.setdefault(int(match.group(1)), (word, word))
        elif f == "thu" and i + 1 < len(ordered):
            nxt = ordered[i + 1]
            if re.fullmatch(r"[2-7]", fold(nxt.text)) and _same_line(word, nxt):
                found.setdefault(int(fold(nxt.text)), (word, nxt))
        elif f == "cn":
            found.setdefault(8, (word, word))
    return {k: v[0] for k, v in found.items()} | {-k: v[1] for k, v in found.items()}


def find_header(page: PageData) -> Header | None:
    """Hàng tiêu đề: đủ Thứ 2…7, CN, Thời gian, Mã HP và Lớp học phần trong một dải dọc."""
    days = _day_label_words(page.words)
    if not all(k in days for k in range(2, 9)):
        return None
    anchor = days[2]
    band = [
        w for w in page.words if anchor.top - HEADER_ABOVE <= w.top <= anchor.top + HEADER_BELOW
    ]
    if page.row_bands:
        for top, bottom in page.row_bands:
            if top - 1 <= anchor.yc <= bottom + 1:
                band = [w for w in band if w.top >= top - HEADER_ABOVE / 2]
                header_bottom = bottom
                break
        else:
            header_bottom = max(w.bottom for w in band)
    else:
        header_bottom = max(w.bottom for w in band)
    labels: dict[str, tuple[float, float]] = {}  # khoá cột → (x0 đầu nhãn, x1 cuối nhãn)

    def put(key: str, first: Word, last: Word | None = None):
        labels.setdefault(key, (first.x0, (last or first).x1))

    for key_num in range(2, 8):
        put(f"d{key_num - 1}", days[key_num], days[-key_num])
    put("d7", days[8], days[-8])
    # Các nhãn còn lại, lấy từ đầu tiên khớp theo thứ tự x.
    for word in sorted(band, key=lambda w: w.x0):
        f = fold(word.text)
        if f == "stt":
            put("stt", word)
        elif f == "ma" and "course" not in labels:
            put("course", word)
        elif f == "lop" and "class" not in labels:
            put("class", word)
        elif f == "so" and "credits" not in labels and word.x0 < days[2].x0:
            put("credits", word)
        elif f == "thoi" and "dates" not in labels and word.x0 > days[8].x0:
            put("dates", word)
        elif f == "hoc" and "fee" not in labels and word.x0 > days[8].x0 + 1:
            nxt = [w for w in band if w.x0 > word.x1 - 0.5 and fold(w.text) == "phi"]
            if nxt and word.x0 > labels.get("dates", (0, 0))[1]:
                put("fee", word)
    if not all(k in labels for k in ("course", "class", "dates")):
        return None
    ordered = sorted(labels.items(), key=lambda kv: kv[1][0])
    columns: list[Column] = []
    edges = page.vertical_edges
    for index, (key, (x0, _x1)) in enumerate(ordered):
        if edges:
            left = max((e for e in edges if e <= x0 + 1), default=x0 - 2)
        elif index == 0:
            left = x0 - 20
        else:
            prev_x1 = ordered[index - 1][1][1]
            left = (prev_x1 + x0) / 2
        columns.append(Column(key, left))
    for a, b in zip(columns, columns[1:], strict=False):
        a.right = b.left
    return Header(anchor.top, header_bottom, columns)


def _semester_line(words: list[Word], header_top: float) -> str | None:
    """Dòng "Học kỳ n Năm học yyyy - yyyy" phía trên bảng; không giữ gì khác (R6)."""
    above = sorted((w for w in words if w.bottom <= header_top + 1), key=lambda w: (w.yc, w.x0))
    lines: list[list[Word]] = []
    for word in above:
        if lines and abs(lines[-1][0].yc - word.yc) <= LINE_TOLERANCE:
            lines[-1].append(word)
        else:
            lines.append([word])
    for line in lines:
        text = " ".join(w.text for w in sorted(line, key=lambda w: w.x0))
        match = _SEMESTER_RE.search(fold(text))
        if match:
            return f"Học kỳ {match.group(1)} Năm học {match.group(2)} - {match.group(3)}"
    return None


def _total_top(words: list[Word], after: float) -> float | None:
    ordered = sorted((w for w in words if w.top >= after), key=lambda w: (w.yc, w.x0))
    for word, nxt in zip(ordered, ordered[1:], strict=False):
        if (
            fold(word.text) == "tong"
            and fold(nxt.text).rstrip(":.") == "cong"
            and _same_line(word, nxt)
        ):
            # Chữ có dấu có thể nhô cao hơn chữ liền kề vài pt: lùi một đoạn để không sót "cộng".
            return min(word.top, nxt.top) - 3
    return None


def _column_of(columns: list[Column], word: Word) -> Column | None:
    for column in columns:
        if column.left <= word.xc < column.right:
            return column
    return None


def _band_rows(
    page: PageData, columns: list[Column], start: float, stop: float | None
) -> list[tuple[float, float]]:
    """Dải dọc từng hàng dữ liệu: theo đường kẻ ngang, không có thì theo cặp ngày cột Thời gian."""
    limit = stop if stop is not None else float("inf")
    if page.row_bands:
        return [(t, b) for t, b in page.row_bands if t >= start - 1 and t < limit - 1]
    dates_col = next(c for c in columns if c.key == "dates")
    dated = sorted(
        (
            w
            for w in page.words
            if start <= w.top < limit
            and dates_col.left <= w.xc < dates_col.right
            and _DATE_RE.fullmatch(w.text)
        ),
        key=lambda w: w.yc,
    )
    groups: list[list[Word]] = []
    for word in dated:
        if groups and len(groups[-1]) < 2:
            groups[-1].append(word)
        else:
            groups.append([word])
    bands = []
    for i, group in enumerate(groups):
        top = start if i == 0 else (groups[i - 1][-1].bottom + group[0].top) / 2
        nxt = groups[i + 1][0].top if i + 1 < len(groups) else None
        bottom = (group[-1].bottom + nxt) / 2 if nxt is not None else min(limit, page.height)
        bands.append((top, bottom))
    return bands


def _cell_lines(words: list[Word]) -> list[str]:
    lines: list[list[Word]] = []
    for word in sorted(words, key=lambda w: (w.yc, w.x0)):
        if lines and abs(lines[-1][0].yc - word.yc) <= LINE_TOLERANCE:
            lines[-1].append(word)
        else:
            lines.append([word])
    return [" ".join(w.text for w in sorted(line, key=lambda w: w.x0)) for line in lines]


def parse_table(pages: list[PageData]) -> ParsedTable:
    """Tìm tiêu đề rồi đọc mọi hàng dữ liệu (kể cả các trang sau) tới trước "Tổng cộng"."""
    header: Header | None = None
    semester_line: str | None = None
    rows: list[RawRow] = []
    for page in pages:
        found = find_header(page)
        if found is not None and header is None:
            header = found
            semester_line = _semester_line(page.words, found.top)
            start = found.bottom
        elif found is not None:
            start = found.bottom  # tiêu đề lặp lại ở trang sau
        elif header is None:
            continue
        else:
            start = 0.0
        stop = _total_top(page.words, start)
        columns = header.columns if header else []
        for top, bottom in _band_rows(page, columns, start, stop):
            cells: dict[str, list[str]] = {}
            for key in KEEP:
                cells[key] = []
            words_by_col: dict[str, list[Word]] = {key: [] for key in KEEP}
            for word in page.words:
                if not top - 1 <= word.yc <= bottom + 1 or (stop is not None and word.top >= stop):
                    continue
                column = _column_of(columns, word)
                if column is not None and column.key in words_by_col:
                    words_by_col[column.key].append(word)
            for key, words in words_by_col.items():
                cells[key] = _cell_lines(words)
            if cells["class"] or cells["course"]:
                rows.append(RawRow(cells))
        if stop is not None:
            break
    if header is None:
        raise NOT_TIMETABLE
    return ParsedTable(semester_line, rows)
